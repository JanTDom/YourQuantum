"""
Integration tests for Cognitive Intake FastAPI Endpoint (/api/cognitive/intake).
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.db.database import init_db
from backend.main import app


@pytest_asyncio.fixture
async def api_client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_cognitive_intake_endpoint_success(api_client: AsyncClient):
    payload = {
        "query": "Wybór projektów A, B, C przy maksymalnym budżecie 50. Koszty: 20, 15, 25. Zyski: 30, 25, 40",
        "session_id": "session_test_123",
    }

    # Test /api/cognitive/intake
    resp = await api_client.post("/api/cognitive/intake", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "ready_for_review"
    assert data["problem_ir"] is not None
    assert len(data["problem_ir"]["variables"]) >= 2
    assert data["confidence"] > 0.0

    # Also verify /api/v1/cognitive/intake alias
    resp_v1 = await api_client.post("/api/v1/cognitive/intake", json=payload)
    assert resp_v1.status_code == 200
    data_v1 = resp_v1.json()
    assert data_v1["status"] == "ready_for_review"


@pytest.mark.asyncio
async def test_cognitive_intake_endpoint_vague(api_client: AsyncClient):
    payload = {
        "query": "hej",
    }
    resp = await api_client.post("/api/cognitive/intake", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "needs_clarification"
    assert len(data["questions"]) > 0
