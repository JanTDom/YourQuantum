"""
Integration tests for Active Inference & Episodic Consolidation Flow.
Simulates: Perception -> Hypothesis -> Verifier FAIL -> Active Inference Reflexion
-> Hypothesis Revision -> Verifier PASS -> Episodic Memory Consolidation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.models import Base, CognitiveTraceRecord
from backend.domain.cognitive.active_inference_engine import ActiveInferenceOrchestrator
from backend.domain.cognitive.episodic_memory import EpisodicMemoryRepository
from backend.domain.cognitive.workspace import EnergyBudget
from backend.infrastructure.gemini_cognitive_adapter import GeminiCognitiveAdapter
from backend.verifier.verifier import ConstraintResult, Verdict, VerificationReport


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
async def test_full_active_inference_cycle(async_test_session: AsyncSession):
    # 1. Setup Cognitive Engine with offline deterministic reasoning port
    episodic_repo = EpisodicMemoryRepository()
    adapter = GeminiCognitiveAdapter(api_key=None)  # deterministic fallback
    budget = EnergyBudget(max_tokens=2000, max_cycles=3)
    orchestrator = ActiveInferenceOrchestrator(
        reasoning_port=adapter,
        episodic_repo=episodic_repo,
        budget=budget,
    )

    query = "Wybór projektów A, B, C przy budżecie 20. Koszty: 5, 8, 10. Zyski: 10, 15, 18"

    # 2. Perception & Intake (Hypothesis Formulation)
    formalization, workspace = await orchestrator.run_intake(
        session=async_test_session,
        query=query,
    )
    assert formalization.status == "ready_for_review"
    assert formalization.problem_ir is not None
    assert workspace.memory.active_hypothesis is not None
    assert len(workspace.memory.focus_variables) == 3
    assert workspace.energy_budget.current_cycle == 0
    assert workspace.energy_budget.tokens_used > 0

    # 3. Simulate Independent Verifier Failure (Verdict.FAIL)
    fail_report = VerificationReport(
        problem_id=formalization.problem_ir.problem_id,
        candidate_id="cand_fail_1",
        verified_at=datetime.now(timezone.utc),
        feasible=False,
        objective_value=None,
        objective_recomputed=False,
        solver_claimed_objective=None,
        constraint_results=[
            ConstraintResult(
                constraint_id="c_budget",
                satisfied=False,
                hard=True,
                violation_magnitude=5.0,
                note="Przekroczono limit budzetu o 5.0",
            )
        ],
        domain_violations=[],
        numerical_residual=5.0,
        verdict=Verdict.FAIL,
        verdict_reason="Constraint violation: c_budget exceeded.",
        limitations=["Infeasible solution"],
    )

    # Process failure signal: triggers Active Inference Reflexion Loop
    fail_outcome = await orchestrator.process_verification_feedback(
        session=async_test_session,
        workspace=workspace,
        verifier_report=fail_report,
        raw_query=query,
        winning_solver="cpsat",
    )

    assert fail_outcome.status == "FAIL"
    assert workspace.energy_budget.current_cycle == 1
    assert len(workspace.memory.prediction_errors) > 0
    assert any("c_budget" in err for err in workspace.memory.prediction_errors)
    assert fail_outcome.active_problem_ir is not None

    # 4. Simulate Independent Verifier Success (Verdict.PASS) on revised model
    pass_report = VerificationReport(
        problem_id=fail_outcome.active_problem_ir.problem_id,
        candidate_id="cand_pass_2",
        verified_at=datetime.now(timezone.utc),
        feasible=True,
        objective_value=40.0,
        objective_recomputed=True,
        solver_claimed_objective=40.0,
        constraint_results=[
            ConstraintResult(
                constraint_id="c_budget",
                satisfied=True,
                hard=True,
                violation_magnitude=0.0,
                note="Spełnione",
            )
        ],
        domain_violations=[],
        numerical_residual=0.0,
        verdict=Verdict.PASS,
        verdict_reason="All constraints satisfied.",
        limitations=["Independent audit confirmed feasibility"],
    )

    pass_outcome = await orchestrator.process_verification_feedback(
        session=async_test_session,
        workspace=workspace,
        verifier_report=pass_report,
        raw_query=query,
        winning_solver="cpsat",
    )

    assert pass_outcome.status == "PASS"
    assert pass_outcome.trace_id is not None
    assert pass_outcome.reward_score == 0.85  # Decayed from 1.0 due to cycle 1

    # 5. Verify episodic memory trace in SQLite database
    stmt = select(CognitiveTraceRecord).where(CognitiveTraceRecord.id == pass_outcome.trace_id)
    res = await async_test_session.execute(stmt)
    trace_rec = res.scalar_one_or_none()

    assert trace_rec is not None
    assert trace_rec.raw_user_query == query
    assert trace_rec.winning_solver == "cpsat"
    assert trace_rec.reward_score == 0.85
    assert "Zbieżność osiągnięta w cyklu 1" in trace_rec.lessons_learned
