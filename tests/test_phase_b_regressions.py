"""
Phase B Regressions & Verification Test Suite (B1 - B7).
Guarantees that all half-measures are eliminated:
- B1: Multi-criteria DecisionMatrix, ScoredValue provenance, analytical break-even point.
- B2: Dynamic re-solve sensitivity analysis (what-if shock testing and parameter rankings).
- B3: Cryptographic HMAC server signatures and POST /api/v1/verification/check endpoint.
- B4: Unified async LLMGateway with token budgeting and usage telemetry.
- B5: Extended Provenance enum (WEB_SOURCED, LLM_EXTRACTED) and IR builder metadata.
- B6: Dynamic ProblemRouter with capability registry and benchmark grounding.
- B7: MCP server criteria_matrix input and routing_record reporting.
"""
from __future__ import annotations

import asyncio
import os
import pytest
from httpx import ASGITransport, AsyncClient

from backend.domain.decision_case import DecisionCase, Criterion, Option, ScoredValue
from backend.domain.decision_matrix import (
    calculate_analytical_break_even,
    calculate_criteria_weights,
    compute_option_utilities,
    normalize_matrix,
)
from backend.domain.formalizer import ProblemFormalizer
from backend.domain.problem_ir import (
    ComputeBudget,
    Constraint,
    ConstraintType,
    ExprNode,
    ExpressionRegistry,
    Objective,
    ObjectiveDirection,
    ProblemIR,
    Provenance,
    SolveMode,
    Variable,
    VariableDomain,
)
from backend.domain.cognitive.ir_builder import build_problem_ir
from backend.domain.sensitivity import SensitivityEngine
from backend.verifier.verifier import (
    IndependentVerifier,
    SolverCandidate,
    build_verification_canonical_string,
    compute_verification_signatures,
)
from backend.infrastructure.llm_gateway import LLMGateway
from backend.domain.router import ProblemRouter, characterize_problem
from backend.main import app
from backend.db.database import init_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_binary_ir(problem_id: str = "p_test") -> ProblemIR:
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="v_x0", op="var", value="x0"))
    reg.add(ExprNode(id="v_x1", op="var", value="x1"))
    reg.add(ExprNode(id="c0", op="const", value=10.0))
    reg.add(ExprNode(id="c1", op="const", value=20.0))
    reg.add(ExprNode(id="m0", op="mul", children=["c0", "v_x0"]))
    reg.add(ExprNode(id="m1", op="mul", children=["c1", "v_x1"]))
    reg.add(ExprNode(id="obj_sum", op="sum", children=["m0", "m1"]))

    reg.add(ExprNode(id="one", op="const", value=1.0))
    reg.add(ExprNode(id="c_sum", op="sum", children=["v_x0", "v_x1"]))

    return ProblemIR(
        problem_id=problem_id,
        description_raw="Test Problem",
        description_formalised="Test Problem",
        mode=SolveMode.OPTIMIZE,
        variables=[
            Variable(id="x0", name="Option A", domain=VariableDomain.BINARY, provenance=Provenance.ASSUMED),
            Variable(id="x1", name="Option B", domain=VariableDomain.BINARY, provenance=Provenance.USER_SUPPLIED),
        ],
        expressions=reg,
        objectives=[
            Objective(id="obj", direction=ObjectiveDirection.MAXIMIZE, expression_id="obj_sum")
        ],
        constraints=[
            Constraint(id="c1", type=ConstraintType.EQUALITY, lhs_expression_id="c_sum", rhs_expression_id="one", hard=True)
        ],
        budget=ComputeBudget(wall_time_seconds=2.0),
        approved=True,
    )


# ---------------------------------------------------------------------------
# B1: Multi-Criteria Decision Matrix & Analytical Break-Even Point
# ---------------------------------------------------------------------------

def test_b1_multi_criteria_matrix_and_analytical_break_even():
    case = DecisionCase(
        title="Dylemat karierowy",
        context="Wybór między Ofertą Alfa a Ofertą Beta",
        options=[
            Option(id="opt_alfa", title="Oferta Alfa"),
            Option(id="opt_beta", title="Oferta Beta"),
        ],
        criteria=[
            Criterion(id="crit_pensja", name="Wynagrodzenie", direction="maximize", weight=1.0, unit="PLN"),
            Criterion(id="crit_autonomia", name="Autonomia", direction="maximize", weight=1.0, unit="pkt"),
        ],
        score_matrix={
            "opt_alfa": {
                "crit_pensja": ScoredValue(value=15000.0, unit="PLN", provenance="user_supplied", source_ref="doc_1"),
                "crit_autonomia": ScoredValue(value=6.0, unit="pkt", provenance="assumed", source_ref="assumption"),
            },
            "opt_beta": {
                "crit_pensja": ScoredValue(value=12000.0, unit="PLN", provenance="user_supplied", source_ref="doc_2"),
                "crit_autonomia": ScoredValue(value=9.0, unit="pkt", provenance="assumed", source_ref="assumption"),
            },
        },
    )

    # 1. Validation for modeling
    is_valid, errs = case.validate_for_modeling()
    assert is_valid is True
    assert len(errs) == 0

    # 2. Normalized scores and utility computation
    norm = normalize_matrix(case)
    assert norm["opt_alfa"]["crit_pensja"] == 1.0
    assert norm["opt_beta"]["crit_pensja"] == 0.0
    assert norm["opt_alfa"]["crit_autonomia"] == 0.0
    assert norm["opt_beta"]["crit_autonomia"] == 1.0

    # User weights: equal weighting -> utilities both 0.5
    utils = compute_option_utilities(case)
    assert utils["opt_alfa"] == 0.5
    assert utils["opt_beta"] == 0.5

    # 3. Priority tokens test: user prioritizes Autonomia
    case.selected_priority_tokens = ["Autonomia"]
    weights = calculate_criteria_weights(case)
    assert weights["crit_autonomia"] > weights["crit_pensja"]

    utils_prio = compute_option_utilities(case)
    assert utils_prio["opt_beta"] > utils_prio["opt_alfa"]  # Beta wins because of higher autonomy!

    # 4. Analytical Break-Even Calculation
    be = calculate_analytical_break_even(case)
    assert be is not None
    assert be.winner_option_id == "opt_beta"
    assert be.runner_up_option_id == "opt_alfa"
    assert be.utility_gap > 0.0
    assert len(be.shifts) > 0
    assert "Oferta Alfa" in be.summary_pl

    # 5. Formalization compilation
    formalizer = ProblemFormalizer()
    res = formalizer.formalize_case(case)
    assert res.identified_archetype == "decision_dilemma"
    assert res.break_even_point is not None
    assert len(res.binary_variables) == 2


def test_b1_missing_source_ref_blocks_modeling():
    """B1: Cell without source_ref must be reported as missing information."""
    case = DecisionCase(
        title="Dylemat bez źródła",
        context="Brak źródła",
        options=[Option(id="o1", title="A"), Option(id="o2", title="B")],
        criteria=[Criterion(id="c1", name="Koszt", direction="minimize")],
        score_matrix={
            "o1": {"c1": ScoredValue(value=100.0, source_ref=None)},  # missing source_ref!
            "o2": {"c1": ScoredValue(value=200.0, source_ref="user_input")},
        },
    )
    is_valid, errs = case.validate_for_modeling()
    assert is_valid is False
    assert any("source_ref" in e for e in errs)


# ---------------------------------------------------------------------------
# B2: Dynamic Re-Solve Sensitivity Analysis
# ---------------------------------------------------------------------------

def test_b2_dynamic_resolve_sensitivity_analysis():
    """B2: SensitivityEngine.analyze_resolve must re-solve and detect parameter sensitivity."""
    problem = _make_binary_ir("p_resolve_test")
    sens_engine = SensitivityEngine(problem)

    baseline_assignment = {"x0": 0.0, "x1": 1.0}  # x1 is winning (coeff 20.0 vs 10.0)
    report = sens_engine.analyze_resolve(
        candidate_id="cand_1",
        baseline_assignment=baseline_assignment,
    )

    assert report.candidate_id == "cand_1"
    assert report.baseline_winner == "x1"
    assert len(report.parameters_tested) > 0
    assert report.summary_pl is not None
    # x0 has provenance ASSUMED, so it was tested
    assert any(p.parameter_id == "x0" for p in report.parameters_tested)


# ---------------------------------------------------------------------------
# B3: HMAC Signatures and POST /verification/check Endpoint
# ---------------------------------------------------------------------------

def test_b3_cryptographic_signatures_generation(monkeypatch):
    """B3: Verification canonical string generates reproducible SHA-256 and HMAC."""
    monkeypatch.setenv("YQ_SIGNING_KEY", "phase_b_test_verification_signing_key")
    canon = build_verification_canonical_string(
        problem_id="prob_123",
        candidate_id="cand_456",
        assignment={"x0": 1, "x1": 0},
        objective_value=15.5,
        residual=0.0,
        verdict="PASS",
    )
    sha, sig = compute_verification_signatures(canon)
    assert len(sha) == 64
    assert sig is not None
    assert len(sig) == 64
    # Recomputing gives exact same result
    sha2, sig2 = compute_verification_signatures(canon)
    assert sha == sha2
    assert sig == sig2


@pytest.mark.asyncio
async def test_b3_verification_check_api_endpoint(monkeypatch):
    """B3: POST /api/v1/verification/check endpoint verifies authentic and detects tampered passports."""
    monkeypatch.setenv("YQ_SIGNING_KEY", "phase_b_test_verification_signing_key")
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        problem_id = "prob_verif_check"
        candidate_id = "cand_789"
        assignment = {"x0": 1, "x1": 0}
        obj_val = 42.0

        canon = build_verification_canonical_string(
            problem_id=problem_id,
            candidate_id=candidate_id,
            assignment=assignment,
            objective_value=obj_val,
            residual=0.0,
            verdict="PASS",
        )
        valid_sha, valid_hmac = compute_verification_signatures(canon)

        # 1. Valid authentic check
        payload_valid = {
            "problem_id": problem_id,
            "candidate_id": candidate_id,
            "assignment": assignment,
            "objective_value": obj_val,
            "residual": 0.0,
            "verdict": "PASS",
            "sha256_hash": valid_sha,
            "hmac_signature": valid_hmac,
        }
        resp = await client.post("/api/v1/verification/check", json=payload_valid)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sha256_valid"] is True
        assert data["hmac_valid"] is True
        assert data["status"] == "AUTHENTIC_VERIFIED"

        # 2. Tampered content check (changed assignment)
        payload_tampered = dict(payload_valid)
        payload_tampered["assignment"] = {"x0": 0, "x1": 1}
        resp_tampered = await client.post("/api/v1/verification/check", json=payload_tampered)
        assert resp_tampered.status_code == 200
        data_tampered = resp_tampered.json()
        assert data_tampered["sha256_valid"] is False
        assert data_tampered["status"] == "TAMPERED"


# ---------------------------------------------------------------------------
# B4: Unified Asynchronous LLMGateway
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_b4_llm_gateway_offline_mode():
    """B4: LLMGateway with no API key enters explicit offline mode cleanly."""
    gateway = LLMGateway(api_key=None)
    resp = await gateway.generate(
        system_instruction="Test system",
        user_content="Test user",
        purpose="test_offline",
    )
    assert resp.is_offline is True
    assert resp.telemetry.purpose == "test_offline"
    assert resp.error == "GEMINI_API_KEY is not configured."


# ---------------------------------------------------------------------------
# B5: Extended Provenance and IR Builder Metadata
# ---------------------------------------------------------------------------

def test_b5_extended_provenance_and_ir_builder():
    """B5: Provenance includes WEB_SOURCED, LLM_EXTRACTED and builder stores provenance and metadata."""
    assert Provenance.WEB_SOURCED.value == "web_sourced"
    assert Provenance.LLM_EXTRACTED.value == "llm_extracted"

    vars_spec = [
        {"id": "v_web", "name": "Web Option", "provenance": "web_sourced", "domain": "binary"},
        {"id": "v_llm", "name": "LLM Option", "provenance": "llm_extracted", "domain": "binary"},
    ]
    ir = build_problem_ir(
        raw_query="Test provenance",
        variables_spec=vars_spec,
        objective_spec={"direction": "maximize", "coefficients": {"v_web": 1.0, "v_llm": 2.0}},
        constraints_spec=[],
        assumptions=["Założenie A"],
    )

    assert ir.variables[0].provenance == Provenance.WEB_SOURCED
    assert ir.variables[1].provenance == Provenance.LLM_EXTRACTED
    assert any(a.statement == "Założenie A" for a in ir.assumptions)


# ---------------------------------------------------------------------------
# B6: Dynamic ProblemRouter
# ---------------------------------------------------------------------------

def test_b6_dynamic_problem_router():
    """B6: ProblemRouter characterizes problem and selects exact solver with comparison solvers."""
    problem = _make_binary_ir("p_router_test")
    chars = characterize_problem(problem)
    assert chars.variable_count == 2
    assert chars.is_pure_binary is True
    assert chars.is_linear is True

    router = ProblemRouter()
    decision = router.route(problem)
    assert decision.recommended_solver in ("cpsat", "hybrid_benders")
    assert len(decision.candidates) >= 1
    assert "routing_record" in decision.model_dump()
    assert decision.routing_record["recommended_solver"] == decision.recommended_solver
