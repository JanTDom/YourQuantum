"""
Unit tests for Gemini Cognitive Adapter and Deterministic Fallback.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from backend.infrastructure.gemini_cognitive_adapter import GeminiCognitiveAdapter


@pytest.mark.asyncio
async def test_gemini_adapter_success():
    adapter = GeminiCognitiveAdapter(api_key="fake-test-key-123")

    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "status": "ready_for_review",
                                "explanation": "Optymalizacja wyboru projektów R&D",
                                "variables": [
                                    {"id": "p1", "name": "Projekt Alfa", "domain": "binary"},
                                    {"id": "p2", "name": "Projekt Beta", "domain": "binary"},
                                ],
                                "objective": {
                                    "direction": "maximize",
                                    "coefficients": {"p1": 50.0, "p2": 80.0},
                                },
                                "constraints": [
                                    {
                                        "id": "c_budget",
                                        "type": "inequality_le",
                                        "lhs_terms": {"p1": 20.0, "p2": 40.0},
                                        "rhs": 50.0,
                                        "description": "Limit budzetu 50k",
                                    }
                                ],
                                "penalty_multipliers": {"c_budget": 100.0},
                            })
                        }
                    ]
                }
            }
        ]
    }

    mock_response = httpx.Response(
        status_code=200,
        json=mock_gemini_response,
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        res = await adapter.formalize_query("Wybierz optymalne projekty A i B do budżetu 50k")

        assert res.status == "ready_for_review"
        assert res.problem_ir is not None
        assert len(res.problem_ir.variables) == 2
        assert len(res.problem_ir.constraints) == 1
        assert res.confidence >= 0.9
        assert "c_budget" in res.penalty_multipliers


@pytest.mark.asyncio
async def test_gemini_adapter_429_rate_limit_fallback():
    adapter = GeminiCognitiveAdapter(api_key="fake-test-key-123")

    mock_response = httpx.Response(
        status_code=429,
        text="Rate limit exceeded. Resource exhausted.",
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        # Should fall back cleanly without raising exception
        res = await adapter.formalize_query("Projekty A, B, C o budżecie 30. Koszty: 10, 8, 12. Zyski: 15, 12, 20")

        assert res.status == "ready_for_review"
        assert res.problem_ir is not None
        assert len(res.problem_ir.variables) >= 2
        assert "deterministycznym" in res.explanation.lower() or "offline" in res.fingerprint.lower()


@pytest.mark.asyncio
async def test_gemini_adapter_missing_api_key_deterministic_fallback():
    # Adapter with no key
    adapter = GeminiCognitiveAdapter(api_key=None)
    res = await adapter.formalize_query("Projekty A, B, C o budżecie 25. Koszty: 10, 8, 12. Zyski: 15, 12, 20")

    assert res.status == "ready_for_review"
    assert res.problem_ir is not None
    assert len(res.problem_ir.variables) == 3
    assert len(res.problem_ir.constraints) >= 1


@pytest.mark.asyncio
async def test_gemini_adapter_vague_input_needs_clarification():
    adapter = GeminiCognitiveAdapter(api_key=None)
    res = await adapter.formalize_query("hej")

    assert res.status == "needs_clarification"
    assert res.problem_ir is None
    assert len(res.questions) >= 1
