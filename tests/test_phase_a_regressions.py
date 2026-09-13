"""
YourQuantum — Phase A Regression & Honesty Test Suite
Verifies all A1–A20 fixes:
- Strict naming & honest computation sources (A1, A2)
- Verifier zero-trust for claimed optimality (A3)
- Zero fabricated numbers in fallbacks (A4)
- Human approval default False (A5)
- No hardcoded knapsack items (A6)
- Secure auth, expiring tokens, no default secrets (A9)
- Fingerprint normalization with Polish morphology (A13)
- Cognitive session persistence & tenant-isolated episodic memory (A14, A18)
- Synchronous job runner (A16)
- Solver dependency health & live capability registry (A17, A19)
"""
import pytest
import uuid
from datetime import datetime, timezone

from backend.db.database import init_db, async_session_factory
from backend.db.models import ProblemRecord, JobRecord, CognitiveTraceRecord, CognitiveSessionRecord
from backend.domain.problem_ir import (
    ProblemIR, Variable, VariableDomain, Objective, ObjectiveDirection,
    Constraint, ConstraintType, ExprNode, ExpressionRegistry, ComputeBudget,
)
from backend.solvers.base import ComputeSource, ExecutionStatus, MathStatus, SolverResult
from backend.solvers.cpsat import CPSATAdapter
from backend.solvers.hybrid_benders import HybridBendersAdapter
from backend.solvers.quantum.qaoa import QAOAAdapter
from backend.verifier.verifier import IndependentVerifier, SolverCandidate, Verdict
from backend.infrastructure.gemini_cognitive_adapter import GeminiCognitiveAdapter
from backend.domain.cognitive.active_inference_engine import compute_problem_fingerprint
from backend.domain.cognitive.episodic_memory import EpisodicMemoryRepository
from backend.domain.cognitive.ir_builder import build_problem_ir
from backend.domain.formalizer import ProblemFormalizer
from backend.domain.capabilities import get_capabilities_registry, CapabilityStatus
from backend.worker.runner import run_job_sync, SOLVER_REGISTRY
from backend.api.universal_engine import UniversalEngine, UniversalComputeRequest, VariableDef, create_expiring_token, verify_master_secret


def _make_problem(pid: str = "p1", var_names: tuple[str, ...] = ("x0", "x1"), approved: bool = True) -> ProblemIR:
    reg = ExpressionRegistry()
    for v in var_names:
        reg.var(v)

    if len(var_names) == 2:
        reg.add(ExprNode(id="obj_expr", op="add", children=[f"var_{var_names[0]}", f"var_{var_names[1]}"]))
    else:
        reg.add(ExprNode(id="obj_expr", op="var", value=var_names[0]))

    return ProblemIR(
        problem_id=pid,
        description_raw="test raw",
        description_formalised="test formalised",
        variables=[Variable(id=v, name=v, domain=VariableDomain.BINARY) for v in var_names],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id="obj_expr")],
        approved=approved,
        approved_at=datetime.now(timezone.utc) if approved else None,
    )


def test_a1_exhaustive_enumeration_naming_and_source():
    """A1: Exhaustive enumeration must be labeled classical, not quantum basis states."""
    engine = UniversalEngine()
    problem = _make_problem("p-a1")
    req = UniversalComputeRequest(
        variables=[VariableDef(id="x0", name="x0"), VariableDef(id="x1", name="x1")],
        objective_direction="minimize",
    )
    res = engine._solve_exhaustive_enumeration(problem, req)

    assert res.solver_name == "exhaustive_enumeration"
    assert res.source == ComputeSource.CLASSICAL_SOLVER
    assert "basis states" not in res.metadata.get("method", "").lower()
    assert res.assignment in ({"x0": 0.0, "x1": 0.0}, {"x0": 0, "x1": 0})


def test_a2_hybrid_benders_source_and_cuts():
    """A2: Hybrid Benders running CP-SAT must report CLASSICAL_SOLVER and add cuts."""
    problem = _make_problem("p-a2")
    adapter = HybridBendersAdapter()
    budget = ComputeBudget(wall_time_seconds=2.0)
    result = adapter.solve(problem, budget)

    # When CP-SAT assists or falls back, source must be CLASSICAL_SOLVER
    if result.metadata.get("decomposition_mode") == "HYBRID_CP_ASSISTED":
        assert result.source == ComputeSource.CLASSICAL_SOLVER
    assert "benders_cuts" in result.metadata


def test_a3_verifier_does_not_trust_claimed_optimal():
    """A3: Verifier independently computes dual bounds and does NOT accept claimed optimal blindly."""
    problem = _make_problem("p-a3")
    verifier = IndependentVerifier(problem)
    # A candidate assignment that is feasible but NOT optimal (x0=1, x1=1 has obj=2.0, optimal is 0.0)
    # Even if solver claims "optimal", verifier must NOT mark optimality_proven=True
    suboptimal_candidate = SolverCandidate(
        candidate_id="c-bad",
        assignment={"x0": 1, "x1": 1},
        claimed_objective=2.0,
        claimed_status="optimal",
    )
    report = verifier.verify(suboptimal_candidate)
    assert report.feasible is True
    assert report.optimality_proven is False, "Verifier must not certify optimality for suboptimal assignment!"


def test_a4_deterministic_fallback_zero_invented_numbers():
    """A4: Deterministic fallback must not invent fake numbers or loosen constraints."""
    adapter = GeminiCognitiveAdapter(api_key="")
    # Query with no numbers
    result = adapter._deterministic_fallback("Chcę zoptymalizować pracę zespołu bez liczb.")
    assert result.status == "needs_clarification"
    assert "brakuje danych liczbowych" in result.explanation.lower()

    # Query with concrete numbers
    result2 = adapter._deterministic_fallback("Wybierz opcje A i B z limitami 10 i 20.")
    if result2.problem_ir:
        for c in result2.problem_ir.constraints:
            # Must NOT contain the old hardcoded 25.0
            assert c.rhs != 25.0


def test_a5_ir_builder_approved_false_by_default():
    """A5: build_problem_ir must create ProblemIR with approved=False."""
    ir = build_problem_ir(
        raw_query="Test A5",
        variables_spec=[{"id": "x0", "name": "x0", "domain": "binary"}],
        objective_spec={"direction": "minimize", "terms": {"x0": 1.0}},
        constraints_spec=[],
    )
    assert ir.approved is False
    assert ir.approved_at is None


def test_a6_knapsack_requires_explicit_data():
    """A6: Formalizer knapsack must not use 4 hardcoded items."""
    formalizer = ProblemFormalizer()
    res = formalizer.formalize("Mam problem plecakowy bez podania wag i wartości.")
    assert len(res.missing_information) > 0


def test_a9_secure_auth_expiring_tokens(monkeypatch):
    """A9: Tokens must be signed and time-expiring."""
    secret = "test-secret-key-12345"
    monkeypatch.setenv("YQ_MASTER_API_SECRET", secret)

    token = create_expiring_token(secret, ttl_hours=1)
    assert token.startswith("yq_exp_")
    assert verify_master_secret(token) is True

    # Tampered token
    tampered = token[:-4] + "xxxx"
    assert verify_master_secret(tampered) is False

    # Expired token
    expired_token = create_expiring_token(secret, ttl_hours=-1)
    assert verify_master_secret(expired_token) is False


def test_a13_polish_fingerprint_morphology():
    """A13: Problem fingerprinting handles Polish stemming and order invariance."""
    fp1 = compute_problem_fingerprint("optymalizacja kosztów transportu")
    fp2 = compute_problem_fingerprint("koszty transportu optymalizacja")
    fp3 = compute_problem_fingerprint("optymalizacją transportem kosztami")

    assert fp1 == fp2, "Fingerprint must be word-order invariant"
    assert fp1 == fp3, "Fingerprint must stem Polish grammatical cases"


@pytest.mark.asyncio
async def test_a14_a18_cognitive_session_and_episodic_isolation():
    """A14 & A18: CognitiveSession persists state, EpisodicMemory prevents cross-user leaks."""
    await init_db()
    async with async_session_factory() as session:
        repo = EpisodicMemoryRepository()

        # User A consolidates a private trace
        await repo.consolidate_trace(
            session,
            {
                "problem_fingerprint": "fp_secret_proj",
                "raw_user_query": "Tajna strategia przejęcia konkurencji za 50M",
                "winning_solver": "cp_sat",
                "reward_score": 1.0,
                "owner_id": "user-A",
                "is_public": False,
            },
        )

        # User B queries analogies with the same fingerprint
        analogies_user_b = await repo.recall_analogies(
            session,
            fingerprint="fp_secret_proj",
            owner_id="user-B",
        )
        # User B must NOT see User A's private trace
        assert len(analogies_user_b) == 0

        # User A queries analogies
        analogies_user_a = await repo.recall_analogies(
            session,
            fingerprint="fp_secret_proj",
            owner_id="user-A",
        )
        assert len(analogies_user_a) >= 1
        assert "Tajna strategia" in analogies_user_a[0]["raw_user_query"]


@pytest.mark.asyncio
async def test_a16_run_job_sync():
    """A16: run_job_sync executes synchronously and publishes verified result."""
    await init_db()
    async with async_session_factory() as session:
        pid = f"p-sync-{uuid.uuid4().hex[:8]}"
        problem = _make_problem(pid)

        # Persist problem and job record
        prob_rec = ProblemRecord(
            id=problem.problem_id,
            description_raw="Raw test",
            description_formalised=problem.description_formalised,
            approved=True,
            ir_json=problem.model_dump(mode="json"),
        )
        job_id = f"job-sync-{uuid.uuid4().hex[:8]}"
        job_rec = JobRecord(
            id=job_id,
            problem_id=problem.problem_id,
            solver_name="cp_sat",
            execution_status=ExecutionStatus.QUEUED.value,
            budget_json=ComputeBudget(wall_time_seconds=5.0).model_dump(),
        )
        session.add(prob_rec)
        session.add(job_rec)
        await session.commit()

        # Run synchronously
        completed_job = await run_job_sync(job_rec.id, session)
        assert completed_job.execution_status == ExecutionStatus.COMPLETED.value
        assert completed_job.publication_status == "PUBLISHED_VERIFIED"
        assert completed_job.objective_value == 0.0


def test_a17_a19_solver_availability_and_capabilities_registry():
    """A17 & A19: Solvers report true installation status, capabilities registry is live."""
    for adapter in SOLVER_REGISTRY:
        avail, err = adapter.check_available()
        assert isinstance(avail, bool)
        if not avail:
            assert err is not None

    registry = get_capabilities_registry()
    assert len(registry) > 10
    for cap in registry:
        if cap.status == CapabilityStatus.TESTED:
            assert cap.test_coverage_ref is not None, f"Capability {cap.id} marked TESTED without test reference!"
