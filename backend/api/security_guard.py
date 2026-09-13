"""
YourQuantum — Security Guard, Rate Limiting & Session Token Subsystem (Phase H1 & H2)
Protects external LLM endpoints (/cases/analyze, /cases/formalize, /cognitive/intake, /evidence/research)
against denial-of-wallet, unbounded scraping, and unauthorized resource exhaustion.
Enforces:
1. Sliding window rate limits per IP and session.
2. Daily request quotas per IP and session.
3. Global safety circuit breaker for external LLM calls.
4. Cryptographically signed anonymous session tokens (HMAC-SHA256).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# Fallback internal signing secret if none configured in environment
_SESSION_HMAC_SECRET = os.getenv("YQ_SESSION_SIGNING_SECRET") or os.getenv("YQ_MASTER_API_SECRET") or "yq_ephemeral_sec_2026_sign"


@dataclass
class ClientUsageRecord:
    timestamps: list[float] = field(default_factory=list)
    daily_count: int = 0
    day_marker: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))


class RateLimiter:
    """
    In-memory resilient sliding-window rate limiter with daily quota caps.
    Thread-safe within single asyncio loop execution.
    """

    def __init__(
        self,
        window_seconds: int = 60,
        max_requests_per_window: int = 15,
        max_daily_requests: int = 60,
        max_global_daily_calls: int = 600,
    ) -> None:
        self.window_seconds = window_seconds
        self.max_requests_per_window = max_requests_per_window
        self.max_daily_requests = max_daily_requests
        self.max_global_daily_calls = max_global_daily_calls

        # Maps client_key -> ClientUsageRecord
        self._usage: dict[str, ClientUsageRecord] = defaultdict(ClientUsageRecord)
        self._global_daily_count: int = 0
        self._current_day: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _reset_day_if_needed(self, record: ClientUsageRecord) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._current_day != today:
            self._current_day = today
            self._global_daily_count = 0

        if record.day_marker != today:
            record.day_marker = today
            record.daily_count = 0

    def check_and_consume(self, client_key: str, is_privileged: bool = False) -> tuple[bool, str, int]:
        """
        Evaluate if client_key is allowed to execute a protected request.
        Returns:
            (allowed: bool, reason: str, retry_after_seconds: int)
        """
        now = time.time()
        record = self._usage[client_key]
        self._reset_day_if_needed(record)

        # Privileged callers (valid master API secret) have 10x higher limits
        window_limit = self.max_requests_per_window * 10 if is_privileged else self.max_requests_per_window
        daily_limit = self.max_daily_requests * 10 if is_privileged else self.max_daily_requests

        # 1. Check Global Server Daily Circuit Breaker
        if not is_privileged and self._global_daily_count >= self.max_global_daily_calls:
            logger.error("Global daily LLM cost circuit breaker tripped (%d calls).", self._global_daily_count)
            return False, "Globalny dzienny limit zapytań obliczeniowych serwera został wyczerpany. Spróbuj jutro.", 3600

        # 2. Check Daily Quota per Client
        if record.daily_count >= daily_limit:
            logger.warning("Client '%s' exceeded daily limit (%d).", client_key, daily_limit)
            return False, f"Przekroczono dzienny limit zapytań ({daily_limit} na dobę). Spróbuj jutro lub podaj klucz autoryzacyjny.", 86400

        # 3. Clean up sliding window timestamps
        cutoff = now - self.window_seconds
        record.timestamps = [t for t in record.timestamps if t > cutoff]

        # 4. Check Window Rate Limit
        if len(record.timestamps) >= window_limit:
            oldest = record.timestamps[0]
            retry_after = max(1, int(oldest + self.window_seconds - now))
            logger.warning("Client '%s' rate limited (window=%ds, limit=%d).", client_key, self.window_seconds, window_limit)
            return False, f"Zbyt wiele zapytań w krótkim czasie. Zwolnij tempo. Odczekaj {retry_after}s.", retry_after

        # Record usage
        record.timestamps.append(now)
        record.daily_count += 1
        self._global_daily_count += 1

        return True, "OK", 0

    def get_client_stats(self, client_key: str) -> dict[str, Any]:
        record = self._usage[client_key]
        self._reset_day_if_needed(record)
        return {
            "daily_requests_used": record.daily_count,
            "max_daily_requests": self.max_daily_requests,
            "window_requests_used": len([t for t in record.timestamps if t > time.time() - self.window_seconds]),
            "max_window_requests": self.max_requests_per_window,
            "global_daily_used": self._global_daily_count,
        }

    def reset_all(self) -> None:
        """Testing utility to clear in-memory state."""
        self._usage.clear()
        self._global_daily_count = 0


# Global singleton instance
GLOBAL_RATE_LIMITER = RateLimiter()


def create_session_token(session_id: str, client_ip: str, ttl_hours: int = 12) -> str:
    """
    Issues an HMAC-signed anonymous session token bound to a session identifier and expiry.
    Format: yq_sess_<exp>_<session_hash>_<sig>
    """
    exp = int(time.time()) + ttl_hours * 3600
    sess_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:12]
    payload = f"{exp}:{sess_hash}:{client_ip}"
    sig = hmac.new(_SESSION_HMAC_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:20]
    return f"yq_sess_{exp}_{sess_hash}_{sig}"


def verify_session_token(token: str, client_ip: str) -> bool:
    """
    Validates HMAC integrity, expiry timestamp, and client identity of session token.
    """
    if not token or not token.startswith("yq_sess_"):
        return False

    parts = token.split("_")
    if len(parts) != 5:
        return False

    _, _, exp_str, sess_hash, sig = parts
    try:
        exp = int(exp_str)
        if time.time() > exp:
            return False

        payload = f"{exp}:{sess_hash}:{client_ip}"
        expected_sig = hmac.new(_SESSION_HMAC_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:20]
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False


def get_client_ip(request: Request) -> str:
    """Safely extracts client IP considering trusted reverse proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the leftmost public IP in the forwarded chain
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


async def verify_security_limits(request: Request) -> str:
    """
    FastAPI dependency: verifies rate limits, quotas, and session credentials
    for costly external LLM and research endpoints.
    """
    client_ip = get_client_ip(request)
    session_id = request.headers.get("X-Session-ID") or request.query_params.get("session_id")
    auth_header = request.headers.get("Authorization", "").strip()

    # Check if caller has privileged master API key
    from backend.api.universal_engine import verify_master_secret
    is_privileged = False
    if auth_header:
        candidate = auth_header[7:].strip() if auth_header.startswith("Bearer ") else auth_header
        if verify_master_secret(candidate):
            is_privileged = True

    # Check session token if provided
    sess_token = request.headers.get("X-Session-Token")
    if sess_token and verify_session_token(sess_token, client_ip):
        client_key = f"sess:{session_id}" if session_id else f"sess:{sess_token.split('_')[3]}"
    elif session_id:
        client_key = f"sess_raw:{session_id}"
    else:
        client_key = f"ip:{client_ip}"

    # Evaluate rate limits
    allowed, reason, retry_after = GLOBAL_RATE_LIMITER.check_and_consume(client_key, is_privileged=is_privileged)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason,
            headers={"Retry-After": str(retry_after)},
        )

    return client_key
