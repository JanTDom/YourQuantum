"""
YourQuantum — Unified Asynchronous LLM Gateway
Consolidates all Gemini API communications across cognitive reasoning,
advisors, and web evidence extraction.
Enforces real token budgeting, exponential backoff, usage telemetry, and explicit offline state.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
import httpx

from backend.domain.cognitive.workspace import EnergyBudget

logger = logging.getLogger(__name__)

GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


class LLMCallTelemetry(BaseModel):
    model: str
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    total_tokens: int = 0
    latency_seconds: float = 0.0
    purpose: str = "general"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LLMResponse(BaseModel):
    text: str = ""
    parsed_json: dict[str, Any] | None = None
    telemetry: LLMCallTelemetry
    is_offline: bool = False
    error: str | None = None


_DEFAULT_KEY = object()


class LLMGateway:
    """
    Unified async gateway for LLM calls with token budgeting and automatic retries.
    """

    def __init__(
        self,
        api_key: str | None | object = _DEFAULT_KEY,
        model: str | None = None,
        timeout: float = 20.0,
        max_retries: int = 3,
        session_token_limit: int = 50000,
    ) -> None:
        if api_key is _DEFAULT_KEY:
            self.api_key = os.getenv("GEMINI_API_KEY")
        else:
            self.api_key = api_key if isinstance(api_key, str) else None
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.timeout = timeout
        self.max_retries = max_retries
        self.session_token_limit = session_token_limit
        self.session_tokens_used = 0
        self.call_history: list[LLMCallTelemetry] = []

    @property
    def is_available(self) -> bool:
        """True if API key is configured and session token budget is not exhausted."""
        return bool(self.api_key) and self.session_tokens_used < self.session_token_limit

    async def generate(
        self,
        system_instruction: str,
        user_content: str,
        purpose: str = "formalization",
        response_schema: dict[str, Any] | None = None,
        few_shots: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        energy_budget: EnergyBudget | None = None,
    ) -> LLMResponse:
        """
        Execute an async call to Gemini API with exponential backoff and usage telemetry.
        """
        if not self.api_key:
            logger.info("LLMGateway: No API key configured. Utilizing offline deterministic mode.")
            telemetry = LLMCallTelemetry(model=self.model, purpose=purpose)
            return LLMResponse(
                text="",
                parsed_json=None,
                telemetry=telemetry,
                is_offline=True,
                error="GEMINI_API_KEY is not configured.",
            )

        if self.session_tokens_used >= self.session_token_limit:
            logger.warning("LLMGateway: Session token limit reached (%d/%d).", self.session_tokens_used, self.session_token_limit)
            telemetry = LLMCallTelemetry(model=self.model, purpose=purpose)
            return LLMResponse(
                text="",
                parsed_json=None,
                telemetry=telemetry,
                is_offline=True,
                error="Session token budget exhausted.",
            )

        # Build payload
        contents: list[dict[str, Any]] = []
        if few_shots:
            contents.extend(few_shots)
        contents.append({
            "role": "user",
            "parts": [{"text": user_content}],
        })

        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "responseMimeType": "application/json",
        }
        if response_schema:
            generation_config["responseSchema"] = response_schema

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}],
            },
            "contents": contents,
            "generationConfig": generation_config,
        }

        url = GEMINI_API_URL_TEMPLATE.format(model=self.model, key=self.api_key)
        start_time = time.monotonic()
        attempt = 0
        last_exception: Exception | None = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload)

                if resp.status_code == 429:
                    wait_time = (2 ** attempt) * 0.5
                    logger.warning("LLMGateway 429 Rate Limit (attempt %d/%d), sleeping %.1fs...", attempt, self.max_retries, wait_time)
                    await asyncio.sleep(wait_time)
                    continue

                resp.raise_for_status()
                data = resp.json()

                # Extract usage metadata
                usage = data.get("usageMetadata", {})
                prompt_tokens = int(usage.get("promptTokenCount", 0))
                candidate_tokens = int(usage.get("candidatesTokenCount", 0))
                total_tokens = int(usage.get("totalTokenCount", prompt_tokens + candidate_tokens))

                # Track session consumption
                self.session_tokens_used += total_tokens
                if energy_budget:
                    energy_budget.consume(total_tokens)

                latency = time.monotonic() - start_time
                telemetry = LLMCallTelemetry(
                    model=self.model,
                    prompt_tokens=prompt_tokens,
                    candidates_tokens=candidate_tokens,
                    total_tokens=total_tokens,
                    latency_seconds=round(latency, 3),
                    purpose=purpose,
                )
                self.call_history.append(telemetry)

                candidates = data.get("candidates", [])
                if not candidates:
                    raise ValueError("Gemini returned empty candidate list.")

                raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                parsed_json = None
                try:
                    parsed_json = json.loads(raw_text)
                except Exception:
                    pass

                return LLMResponse(
                    text=raw_text,
                    parsed_json=parsed_json,
                    telemetry=telemetry,
                    is_offline=False,
                )

            except Exception as e:
                last_exception = e
                wait_time = (2 ** attempt) * 0.3
                logger.warning("LLMGateway call failed (attempt %d/%d): %s", attempt, self.max_retries, e)
                if attempt < self.max_retries:
                    await asyncio.sleep(wait_time)

        latency = time.monotonic() - start_time
        telemetry = LLMCallTelemetry(
            model=self.model,
            latency_seconds=round(latency, 3),
            purpose=purpose,
        )
        return LLMResponse(
            text="",
            parsed_json=None,
            telemetry=telemetry,
            is_offline=True,
            error=str(last_exception),
        )


# Global singleton instance for easy import across modules
_gateway_instance: LLMGateway | None = None


def get_llm_gateway() -> LLMGateway:
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = LLMGateway()
    return _gateway_instance
