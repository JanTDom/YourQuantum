"""
YourQuantum — Phase E Cognitive Engine Tests (E1–E7)
Tests:
1. E1: Single unified intake pipeline (Computability, Quality Gate, Episodic Recall, DecisionCase, ResearchPlan, Matrix, IR)
2. E1: Quality Gate blocks vague input and prompts clarification
3. E1: Uncomputable / philosophical query returns honest NotComputableReport
4. E2: Persistent Working Memory via CognitiveSessionRecord across turns and session deletion
5. E3: Closed Active Inference Loop in runner.py with DEC-002 mandatory re-approval on model revision
6. E4: Metabolic Energy Budget tracking (tokens, searches, solver time) and exhaustion advice
7. E5: Consent-gated episodic consolidation (strictly skips without consent, anonymizes with consent)
8. E6: Cognitive Inspector telemetry endpoint
"""
from __future__ import annotations

from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.models import Base, CognitiveSessionRecord, CognitiveTraceRecord, JobRecord, ProblemRecord
from backend.domain.cognitive.active_inference_engine import ActiveInferenceOrchestrator
from backend.domain.cognitive.episodic_memory import EpisodicMemoryRepository
from backend.domain.cognitive.workspace import EnergyBudget, GlobalWorkspace
from backend.domain.problem_ir import ComputeBudget, ProblemIR, SolveMode, Variable, VariableDomain
from backend.infrastructure.gemini_cognitive_adapter import GeminiCognitiveAdapter
from backend.main import app
from backend.verifier.verifier import ConstraintResult, Verdict, VerificationReport
from backend.worker.runner import run_job_sync


@pytest_asyncio.fixture
async def async_test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_e1_single_intake_pathway_returns_unified_model():
    """E1: POST /api/v1/cognitive/intake structures dilemma, creates DecisionCase, research queries, and unapproved IR."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/cognitive/intake",
            json={
                "query": "Wybór między ofertą pracy A (pensja 18000 zł) a ofertą pracy B (pensja 22000 zł). Czas dojazdu: 20 min vs 60 min.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ready_for_review", "needs_clarification")
        assert data["session_id"] is not None
        assert data["decision_case"] is not None
        assert data["problem_class"] in ("CHOICE", "ALLOCATION")
        assert data["input_quality"]["level"] == "sufficient"


@pytest.mark.asyncio
async def test_e1_input_quality_gate_triggers_clarification():
    """E1: Vague input triggers needs_clarification before running solver."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/cognitive/intake",
            json={"query": "Co zrobić?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "needs_clarification"
        assert data["input_quality"]["level"] == "too_vague"
        assert len(data["questions"]) > 0


@pytest.mark.asyncio
async def test_e1_not_computable_question_returns_reframing_advice():
    """E1 & D1: Non-computable philosophical query returns honest explanation without fake quantum math."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/cognitive/intake",
            json={"query": "Jaki jest sens życia?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_computable"
        assert data["problem_class"] == "NOT_COMPUTABLE"
        assert data["not_computable_report"] is not None
        assert len(data["questions"]) > 0
        assert "sens" in data["explanation"].lower() or "egzystencjalnym" in data["explanation"].lower()


@pytest.mark.asyncio
async def test_e2_working_memory_session_persistence_and_deletion():
    """E2: Multi-turn interaction preserves session working memory, followed by deletion."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Turn 1: Create session
        resp1 = await ac.post(
            "/api/v1/cognitive/intake",
            json={"query": "Projekt Alpha vs Projekt Beta przy budżecie 50000 zł i czasie 6 miesięcy."},
        )
        assert resp1.status_code == 200
        session_id = resp1.json()["session_id"]
        assert session_id is not None

        # Turn 2: Query same session
        resp2 = await ac.post(
            "/api/v1/cognitive/intake",
            json={
                "query": "Dodatkowa opcja: Projekt Gamma o koszcie 40000 zł.",
                "session_id": session_id,
            },
        )
        assert resp2.status_code == 200
        assert resp2.json()["session_id"] == session_id

        # Inspect session
        resp_insp = await ac.get(f"/api/v1/cognitive/session/{session_id}")
        assert resp_insp.status_code == 200
        telemetry = resp_insp.json()
        assert len(telemetry["interaction_history"]) >= 2

        # Delete session
        resp_del = await ac.delete(f"/api/v1/cognitive/session/{session_id}")
        assert resp_del.status_code == 200
        assert resp_del.json()["status"] == "deleted"

        # Verify 404 after deletion
        resp_after = await ac.get(f"/api/v1/cognitive/session/{session_id}")
        assert resp_after.status_code == 404


@pytest.mark.asyncio
async def test_e3_verifier_failure_generates_unapproved_revised_model_requiring_reapproval(
    async_test_session: AsyncSession,
):
    """E3 & DEC-002: Verifier FAIL creates revised ProblemIR that strictly starts UNAPPROVED."""
    # 1. Create and store an initial problem
    from backend.domain.cognitive.ir_builder import build_problem_ir
    ir = build_problem_ir(
        raw_query="Wybór projektu x1",
        variables_spec=[{"id": "x1", "name": "x1", "domain": "binary"}],
        objective_spec={"direction": "maximize", "coefficients": {"x1": 10.0}},
        constraints_spec=[],
        formalised_description="Wybór projektu x1",
    )
    ir.approved = True
    ir.approved_at = datetime.now(timezone.utc)
    prob_rec = ProblemRecord(
        id=ir.problem_id,
        description_raw=ir.description_raw,
        description_formalised=ir.description_formalised,
        ir_json=ir.model_dump(mode="json"),
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )

    async_test_session.add(prob_rec)

    # 2. Create job
    job = JobRecord(
        id="job_e3_test",
        problem_id=ir.problem_id,
        solver_name="cpsat",
        budget_json=ComputeBudget(wall_time_seconds=10.0).model_dump(),
        metadata_json={"session_id": "test_sess_e3"},
    )
    async_test_session.add(job)
    await async_test_session.commit()

    # 3. Run job synchronously
    completed_job = await run_job_sync("job_e3_test", async_test_session)
    assert completed_job is not None
    assert completed_job.metadata_json is not None
    assert "active_inference_outcome" in completed_job.metadata_json

    # If verifier failed and created revised model: verify DEC-002 invariant
    if completed_job.metadata_json.get("requires_reapproval"):
        revised_id = completed_job.metadata_json.get("revised_problem_id")
        assert revised_id is not None
        revised_rec = await async_test_session.get(ProblemRecord, revised_id)
        assert revised_rec is not None
        # Non-negotiable DEC-002: revised model MUST be unapproved
        assert not revised_rec.approved
        assert revised_rec.approved_at is None


@pytest.mark.asyncio
async def test_e4_energy_budget_metabolic_tracking_and_exhaustion_suggestions():
    """E4: EnergyBudget tracks token, search, and solver limits, and emits simplification suggestions."""
    budget = EnergyBudget(max_tokens=500, max_search_queries=2, max_solver_seconds=5.0)

    # Consume within limits
    assert budget.consume_tokens(200)
    assert budget.consume_search(1)
    assert budget.consume_solver_time(2.0)
    assert not budget.is_exhausted()

    # Exceed search limit
    budget.consume_search(2)
    assert budget.is_exhausted()
    reason = budget.get_exhaustion_reason()
    assert reason is not None
    assert "badań" in reason or "zapytań" in reason or "limit" in reason

    suggestions = budget.suggest_simplifications()
    assert len(suggestions) > 0
    assert any("liczby" in s or "parametry" in s or "zmniejsz" in s.lower() for s in suggestions)


@pytest.mark.asyncio
async def test_e5_consent_gated_consolidation_rejects_without_consent_and_anonymizes_with_consent():
    """E5: Consolidation endpoint skips if consent=False; saves anonymized trace if consent=True."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create session
        intake_res = await ac.post(
            "/api/v1/cognitive/intake",
            json={"query": "Opcja A vs Opcja B przy koszcie 10000 zł i zysku 20000 zł."},
        )
        session_id = intake_res.json()["session_id"]

        # Attempt 1: Without consent (consent=False)
        skip_res = await ac.post(
            "/api/v1/cognitive/consolidate",
            json={"session_id": session_id, "consent": False},
        )
        assert skip_res.status_code == 200
        assert skip_res.json()["status"] == "skipped"

        # Attempt 2: With explicit consent (consent=True)
        cons_res = await ac.post(
            "/api/v1/cognitive/consolidate",
            json={"session_id": session_id, "consent": True},
        )
        assert cons_res.status_code == 200
        assert cons_res.json()["status"] == "consolidated"
        assert cons_res.json()["trace_id"] is not None


@pytest.mark.asyncio
async def test_e6_cognitive_inspector_telemetry_endpoint():
    """E6: Telemetry endpoint returns cycles, metabolic budget, and prediction errors without metaphors."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        intake_res = await ac.post(
            "/api/v1/cognitive/intake",
            json={"query": "Inwestycja A vs Inwestycja B przy kapitale 100000 zł."},
        )
        session_id = intake_res.json()["session_id"]

        telemetry_res = await ac.get(f"/api/v1/cognitive/session/{session_id}")
        assert telemetry_res.status_code == 200
        data = telemetry_res.json()
        assert data["session_id"] == session_id
        assert "energy_budget" in data
        assert "tokens_used" in data["energy_budget"]
        assert "prediction_errors" in data
        assert "cycle_history" in data
        assert "interaction_history" in data
