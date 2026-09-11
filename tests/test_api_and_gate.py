"""
Tests for API endpoints, Explicit Approval Flow, Publication Gate, and DecisionCase.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.db.database import init_db


@pytest.mark.asyncio
async def test_problem_explicit_approval_and_job_gate():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create problem with approved=False (default)
        create_res = await client.post(
            "/api/v1/problems",
            json={
                "description": "Wybór inwestycji: 2 projekty",
                "binary_variables": ["p0", "p1"],
                "objective_coefficients": {"p0": 1.0, "p1": 2.0},
                "objective_direction": "maximize",
                "equality_constraints": [{"lhs": {"p0": 1.0, "p1": 1.0}, "rhs": 1.0}],
            },
        )
        assert create_res.status_code == 201
        data = create_res.json()
        problem_id = data["problem_id"]
        assert data["approved"] is False

        # 2. Attempt to create job for unapproved problem -> MUST fail with 422
        job_res = await client.post(
            "/api/v1/jobs",
            json={"problem_id": problem_id, "solver": "cp_sat"},
        )
        assert job_res.status_code == 422
        assert "approved" in job_res.json()["detail"].lower()

        # 3. Explicitly approve problem
        appr_res = await client.post(f"/api/v1/problems/{problem_id}/approve")
        assert appr_res.status_code == 200
        assert appr_res.json()["approved"] is True

        # 4. Now create job -> MUST succeed (202 Accepted)
        job_res2 = await client.post(
            "/api/v1/jobs",
            json={"problem_id": problem_id, "solver": "cp_sat"},
        )
        assert job_res2.status_code == 202
        job_id = job_res2.json()["job_id"]

        # 5. Check status
        status_res = await client.get(f"/api/v1/jobs/{job_id}")
        assert status_res.status_code == 200
        assert "publication_status" in status_res.json()


@pytest.mark.asyncio
async def test_case_analyze_endpoint():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/cases/analyze",
            json={"text": "Nie wiem czy zmienić pracę czy zostać w korporacji"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["options"]) >= 2
        assert len(data["unknowns"]) >= 1
        assert "status" in data
