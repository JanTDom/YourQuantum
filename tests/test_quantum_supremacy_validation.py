"""
tests/test_quantum_supremacy_validation.py

Rygorystyczny zestaw testów poprawności i odporności na błędy:
1. Input Quality Gate: testy wykrywania nieprecyzyjnych danych (dyrdymały, brak opcji, brak liczb).
2. Exact QUBO Slack: matematyczna zgodność hamiltonianu ze ścisłymi ograniczeniami nierównościowymi.
3. Warm-Started QAOA: zbieżność do ścisłego stanu podstawowego (ground truth) na problemie kombinatorycznym.
4. Dual Bound & Luka Optymalności: weryfikacja matematycznego ograniczenia dolnego i zerowej luki.
5. Niezależny Weryfikator & Odporność na Oszustwa: wykrywanie sfałszowanych wartości celu, naruszeń ograniczeń i integralność SHA-256.
6. Sensitivity Engine: testy wrażliwości przy wstrząsach +/-5%, +/-15%, +/-25% (stabilność vs kruchość).
7. Hybrid Benders Decomposition: poprawność generowania cięć i zbieżność do rozwiązania dopuszczalnego.
8. End-to-End Execution Pipeline: pełna ścieżka od IR przez solwer, weryfikację, stempel SHA-256 aż do testów odporności.
9. API Endpoint Quality Gate: weryfikacja kontraktu HTTP /api/v1/cases/analyze dla input_quality.
"""

from __future__ import annotations

import pytest
import numpy as np
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.db.database import init_db
from backend.domain.problem_ir import (
    ProblemIR,
    Variable,
    VariableDomain,
    Constraint,
    ConstraintType,
    Objective,
    ObjectiveDirection,
    ExprNode,
    ExpressionRegistry,
    ComputeBudget,
    SolveMode,
)
from backend.domain.llm_advisor import LLMAdvisor
from backend.domain.decision_case import DecisionCase, InputQuality
from backend.solvers.base import ExecutionStatus, MathStatus
from backend.solvers.quantum.qubo import QUBOEncoder, QUBOEncodingError
from backend.solvers.quantum.qaoa import QAOAAdapter
from backend.solvers.cpsat import CPSATAdapter
from backend.solvers.hybrid_benders import HybridBendersAdapter
from backend.verifier.verifier import IndependentVerifier, SolverCandidate, Verdict
from backend.domain.sensitivity import SensitivityEngine


# ===========================================================================
# Pomocnicze funkcje budowy drzew wyrażeń w ProblemIR
# ===========================================================================

def make_const(reg: ExpressionRegistry, val: float) -> str:
    nid = f"c_{len(reg.nodes)}"
    reg.add(ExprNode(id=nid, op="const", value=val))
    return nid

def make_var(reg: ExpressionRegistry, var_id: str) -> str:
    nid = f"v_{var_id}"
    reg.add(ExprNode(id=nid, op="var", value=var_id))
    return nid

def make_mul(reg: ExpressionRegistry, c_id: str, v_id: str) -> str:
    nid = f"m_{len(reg.nodes)}"
    reg.add(ExprNode(id=nid, op="mul", children=[c_id, v_id]))
    return nid

def make_sum(reg: ExpressionRegistry, child_ids: list[str]) -> str:
    nid = f"s_{len(reg.nodes)}"
    reg.add(ExprNode(id=nid, op="sum", children=child_ids))
    return nid


# ===========================================================================
# 1. TESTY BRAMKI JAKOŚCI DANYCH WEJŚCIOWYCH (INPUT QUALITY GATE)
# ===========================================================================

def test_quality_gate_rejects_vague_prompts():
    """Bramka musi odrzucać zbyt ogólne dylematy (< 15 słów)."""
    advisor = LLMAdvisor()
    vague_texts = [
        "Co mam zrobić w życiu?",
        "Zmienić pracę czy nie?",
        "Mam dylemat biznesowy.",
        "Kupić mieszkanie czy wynajmować?",
    ]
    for text in vague_texts:
        case = advisor.heuristic_analyze(text)
        assert case.input_quality.level == "too_vague", f"Expected too_vague for '{text}'"
        assert len(case.input_quality.suggestions) > 0


def test_quality_gate_flags_missing_options():
    """Bramka musi wychwytywać brak wariantów decyzyjnych."""
    advisor = LLMAdvisor()
    text = "Zastanawiam się bardzo intensywnie nad sytuacją w mojej firmie produkcyjnej, ponieważ koszty rosną każdego miesiąca i nie wiem co począć z tą całą sytuacją budżetową."
    case = advisor.heuristic_analyze(text)
    assert case.input_quality.level in ("needs_options", "too_vague")


def test_quality_gate_flags_missing_numbers_in_finance():
    """Dylemat finansowo-budżetowy bez ani jednej liczby musi żądać danych liczbowych."""
    advisor = LLMAdvisor()
    text = "Chcę zainwestować pieniądze w nowy magazyn logistyczny lub w nową linię technologiczną dla zakładu, ale nie wiem co przyniesie lepszy zwrot z kapitału w kolejnych latach."
    case = advisor.heuristic_analyze(text)
    assert case.input_quality.level == "needs_numbers"
    assert any("liczbow" in s.lower() or "budżet" in s.lower() or "koszt" in s.lower() for s in case.input_quality.suggestions)


def test_quality_gate_passes_well_defined_dilemma():
    """Dobrze opisany dylemat z liczbami i opcjami musi przejść bez przeszkód."""
    advisor = LLMAdvisor()
    text = "Wybieram między ofertą A ze stawką 25000 zł i 3 dniami pracy zdalnej, a ofertą B ze stawką 32000 zł w biurze i 90 minutami dojazdu dziennie."
    case = advisor.heuristic_analyze(text)
    assert case.input_quality.level == "sufficient"


# ===========================================================================
# 2. TESTY ŚCISŁOŚCI QUBO I EXACT SLACK EXPANSION
# ===========================================================================

def test_qubo_slack_variable_exact_budget_enforcement():
    """
    Sprawdza czy exact binary slack expansion w QUBO poprawnie penalizuje przekroczenie budżetu:
    3 zmienne binarne: x0 (waga 2), x1 (waga 3), x2 (waga 4).
    Ograniczenie: 2*x0 + 3*x1 + 4*x2 <= 5.
    Maksymalizujemy zysk: 10*x0 + 12*x1 + 15*x2.
    Optymalne dopuszczalne: x0=1, x1=1, x2=0 (waga 5, zysk 22).
    """
    reg = ExpressionRegistry()
    x0 = Variable(id="x0", name="x0", domain=VariableDomain.BINARY)
    x1 = Variable(id="x1", name="x1", domain=VariableDomain.BINARY)
    x2 = Variable(id="x2", name="x2", domain=VariableDomain.BINARY)

    vx0 = make_var(reg, "x0")
    vx1 = make_var(reg, "x1")
    vx2 = make_var(reg, "x2")
    c2 = make_const(reg, 2.0)
    c3 = make_const(reg, 3.0)
    c4 = make_const(reg, 4.0)
    term0 = make_mul(reg, c2, vx0)
    term1 = make_mul(reg, c3, vx1)
    term2 = make_mul(reg, c4, vx2)
    lhs_budget = make_sum(reg, [term0, term1, term2])
    rhs_budget = make_const(reg, 5.0)

    # Cel: MINIMALIZACJA -(10*x0 + 12*x1 + 15*x2)
    z10 = make_const(reg, -10.0)
    z12 = make_const(reg, -12.0)
    z15 = make_const(reg, -15.0)
    zterm0 = make_mul(reg, z10, vx0)
    zterm1 = make_mul(reg, z12, vx1)
    zterm2 = make_mul(reg, z15, vx2)
    obj_expr = make_sum(reg, [zterm0, zterm1, zterm2])

    ir = ProblemIR(
        description_raw="knapsack test",
        description_formalised="knapsack test",
        variables=[x0, x1, x2],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id=obj_expr)],
        constraints=[Constraint(id="c_budget", type=ConstraintType.INEQUALITY_LE,
                                lhs_expression_id=lhs_budget, rhs_expression_id=rhs_budget, hard=True)],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )

    encoder = QUBOEncoder()
    qubo_inst = encoder.encode(ir)

    assert len(qubo_inst.variable_order) > 3
    assert any("__slack_" in v for v in qubo_inst.variable_order)

    adapter = QAOAAdapter()
    result = adapter.solve(ir, ComputeBudget(wall_time_seconds=5.0))
    
    assert result.execution_status == ExecutionStatus.COMPLETED
    assert result.assignment["x0"] == 1
    assert result.assignment["x1"] == 1
    assert result.assignment["x2"] == 0


# ===========================================================================
# 3. TESTY WARM-STARTED QAOA NA ZNANYM GROUND TRUTH
# ===========================================================================

def test_warm_start_qaoa_ground_truth_convergence():
    """
    Testuje czy Warm-Started QAOA poprawnie wyznacza relaksację ciągłą,
    tworzy kąty Ry i osiąga ten sam globalny wynik co solver dokładny CP-SAT.
    """
    reg = ExpressionRegistry()
    vars_list = [Variable(id=f"y{i}", name=f"y{i}", domain=VariableDomain.BINARY) for i in range(4)]
    
    c1 = make_const(reg, 1.0)
    c2 = make_const(reg, 2.0)
    c3 = make_const(reg, -3.0)
    c4 = make_const(reg, 4.0)
    
    t0 = make_mul(reg, c1, make_var(reg, "y0"))
    t1 = make_mul(reg, c2, make_var(reg, "y1"))
    t2 = make_mul(reg, c3, make_var(reg, "y2"))
    t3 = make_mul(reg, c4, make_var(reg, "y3"))
    
    obj_id = make_sum(reg, [t0, t1, t2, t3])
    c_y2 = make_const(reg, 1.0)
    
    ir = ProblemIR(
        description_raw="test warm start",
        description_formalised="test warm start",
        variables=vars_list,
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id=obj_id)],
        constraints=[Constraint(id="c_y2", type=ConstraintType.EQUALITY,
                                lhs_expression_id=make_var(reg, "y2"), rhs_expression_id=c_y2, hard=True)],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    
    cpsat = CPSATAdapter()
    exact_res = cpsat.solve(ir, ComputeBudget(wall_time_seconds=5.0))
    assert exact_res.execution_status == ExecutionStatus.COMPLETED
    
    qaoa = QAOAAdapter()
    qaoa_res = qaoa.solve(ir, ComputeBudget(wall_time_seconds=5.0))
    
    assert qaoa_res.execution_status == ExecutionStatus.COMPLETED
    assert qaoa_res.metadata.get("warm_started") is True
    assert "relaxation_energy" in qaoa_res.metadata
    
    assert qaoa_res.assignment["y2"] == 1
    assert qaoa_res.assignment["y3"] == 0
    assert qaoa_res.assignment["y0"] == 0
    assert qaoa_res.assignment["y1"] == 0
    assert qaoa_res.objective_value == exact_res.objective_value


# ===========================================================================
# 4. TESTY DUAL BOUND GAP I NIEZALEŻNEGO CERTYFIKATU SHA-256
# ===========================================================================

def test_dual_bound_lp_gap_and_sha256_audit_passport():
    """
    Testuje:
    - Obliczenie dual bound (dolnej granicy ciągłej LP).
    - Lukę optymalności optimality_gap_percent == 0.0% gdy wynik całkowity jest optymalny.
    - Pieczęć kryptograficzną SHA-256.
    """
    reg = ExpressionRegistry()
    x = Variable(id="x1", name="x1", domain=VariableDomain.BINARY)
    y = Variable(id="x2", name="x2", domain=VariableDomain.BINARY)
    
    c3 = make_const(reg, 3.0)
    c4 = make_const(reg, 4.0)
    tx = make_mul(reg, c3, make_var(reg, "x1"))
    ty = make_mul(reg, c4, make_var(reg, "x2"))
    obj = make_sum(reg, [tx, ty])
    
    sum_xy = make_sum(reg, [make_var(reg, "x1"), make_var(reg, "x2")])
    c1 = make_const(reg, 1.0)
    
    ir = ProblemIR(
        description_raw="dual test",
        description_formalised="dual test",
        variables=[x, y],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id=obj)],
        constraints=[Constraint(id="c1", type=ConstraintType.INEQUALITY_GE,
                                lhs_expression_id=sum_xy, rhs_expression_id=c1, hard=True)],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    
    candidate = SolverCandidate(
        candidate_id="cand_opt",
        assignment={"x1": 1.0, "x2": 0.0},
        claimed_objective=3.0,
        claimed_status="optimal",
    )
    
    verifier = IndependentVerifier(ir)
    report = verifier.verify(candidate)
    
    assert report.feasible is True
    assert report.verdict == Verdict.PASS
    assert report.dual_bound == pytest.approx(3.0, abs=1e-2)
    assert report.optimality_gap_percent is not None
    assert report.optimality_gap_percent <= 0.01
    assert report.optimality_proven is True
    assert report.sha256_hash is not None
    assert len(report.sha256_hash) == 64
    
    report2 = verifier.verify(candidate)
    assert report2.sha256_hash == report.sha256_hash


# ===========================================================================
# 5. TESTY ODPORNOŚCI NA FAŁSZERSTWO I TAMPERING (VERIFIER SECURITY)
# ===========================================================================

def test_verifier_catches_falsified_objective():
    """Weryfikator nie może ufać claimed_objective podanemu przez solver."""
    reg = ExpressionRegistry()
    x = Variable(id="x", name="x", domain=VariableDomain.BINARY)
    c10 = make_const(reg, 10.0)
    obj = make_mul(reg, c10, make_var(reg, "x"))
    
    ir = ProblemIR(
        description_raw="tamper test",
        description_formalised="tamper test",
        variables=[x],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id=obj)],
        constraints=[],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    
    verifier = IndependentVerifier(ir)
    
    fraudulent_candidate = SolverCandidate(
        candidate_id="fraud",
        assignment={"x": 1},
        claimed_objective=-999.0
    )
    report = verifier.verify(fraudulent_candidate)
    
    # Weryfikator niezależnie wylicza 10.0 i bezwzględnie ODRZUCA kłamstwo solvera!
    assert report.objective_value == pytest.approx(10.0)
    assert report.feasible is False
    assert report.verdict == Verdict.FAIL
    assert any(c.constraint_id == "__objective_check__" for c in report.constraint_results)


def test_verifier_rejects_constraint_violation():
    """Weryfikator musi bezwzględnie odrzucić rozwiązanie łamiące twarde ograniczenie."""
    reg = ExpressionRegistry()
    x = Variable(id="x", name="x", domain=VariableDomain.BINARY)
    obj_node = make_var(reg, "x")
    
    ir = ProblemIR(
        description_raw="violation test",
        description_formalised="violation test",
        variables=[x],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id=obj_node)],
        constraints=[Constraint(id="must_be_zero", type=ConstraintType.EQUALITY,
                                lhs_expression_id=make_var(reg, "x"), rhs_expression_id=make_const(reg, 0.0), hard=True)],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    
    verifier = IndependentVerifier(ir)
    bad_candidate = SolverCandidate(candidate_id="bad", assignment={"x": 1})
    report = verifier.verify(bad_candidate)
    
    assert report.feasible is False
    assert report.verdict == Verdict.FAIL
    violated_ids = [c.constraint_id for c in report.constraint_results if not c.satisfied]
    assert "must_be_zero" in violated_ids


# ===========================================================================
# 6. TESTY SILNIKA WRAŻLIWOŚCI (SENSITIVITY & STRESS-TESTING)
# ===========================================================================

def test_sensitivity_engine_resilience_computation():
    """
    Testuje obliczanie odporności przy wstrząsach +/-5%, +/-15%, +/-25%
    z użyciem SensitivityEngine na poziomie ProblemIR.
    """
    reg = ExpressionRegistry()
    vx = make_var(reg, "x")
    vy = make_var(reg, "y")
    c10 = make_const(reg, 10.0)
    c20 = make_const(reg, 20.0)
    m1 = make_mul(reg, c10, vx)
    m2 = make_mul(reg, c20, vy)
    obj = make_sum(reg, [m1, m2])
    
    sum_xy = make_sum(reg, [vx, vy])
    rhs2 = make_const(reg, 2.0)
    
    ir = ProblemIR(
        description_raw="sensitivity test",
        description_formalised="sensitivity test",
        variables=[
            Variable(id="x", name="x", domain=VariableDomain.BINARY),
            Variable(id="y", name="y", domain=VariableDomain.BINARY),
        ],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id=obj)],
        constraints=[Constraint(id="c_limit", type=ConstraintType.INEQUALITY_LE,
                                lhs_expression_id=sum_xy, rhs_expression_id=rhs2, hard=True)],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    
    engine = SensitivityEngine(ir)
    
    report_safe = engine.analyze("cand_safe", {"x": 1.0, "y": 0.0}, baseline_objective=10.0)
    assert report_safe.robustness_score >= 0.8
    assert report_safe.verdict in ("HIGHLY_ROBUST", "MODERATELY_ROBUST")
    assert len(report_safe.shock_levels) == 3
    for s in report_safe.shock_levels:
        assert s.retained_feasibility is True

    report_edge = engine.analyze("cand_edge", {"x": 1.0, "y": 1.0}, baseline_objective=30.0)
    assert report_edge.verdict == "FRAGILE"
    assert report_edge.robustness_score < 0.5
    assert any(not s.retained_feasibility for s in report_edge.shock_levels)


# ===========================================================================
# 7. TESTY HYBRYDOWEGO SOLWERA BENDERSA
# ===========================================================================

def test_hybrid_benders_decomposition_accuracy():
    """
    Sprawdza czy HybridBendersAdapter generuje poprawne rozwiązanie i nie narusza ograniczeń.
    """
    reg = ExpressionRegistry()
    b0 = Variable(id="b0", name="b0", domain=VariableDomain.BINARY)
    b1 = Variable(id="b1", name="b1", domain=VariableDomain.BINARY)
    
    c3 = make_const(reg, -3.0)
    c2 = make_const(reg, -2.0)
    t0 = make_mul(reg, c3, make_var(reg, "b0"))
    t1 = make_mul(reg, c2, make_var(reg, "b1"))
    obj = make_sum(reg, [t0, t1])
    c_sum = make_sum(reg, [make_var(reg, "b0"), make_var(reg, "b1")])
    
    ir = ProblemIR(
        description_raw="benders test",
        description_formalised="benders test",
        variables=[b0, b1],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id=obj)],
        constraints=[Constraint(id="exclusive", type=ConstraintType.INEQUALITY_LE,
                                lhs_expression_id=c_sum, rhs_expression_id=make_const(reg, 1.0), hard=True)],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    
    adapter = HybridBendersAdapter()
    assert adapter.supports(ir)
    
    res = adapter.solve(ir, ComputeBudget(wall_time_seconds=5.0))
    assert res.execution_status == ExecutionStatus.COMPLETED
    assert res.assignment["b0"] == 1
    assert res.assignment["b1"] == 0
    assert res.objective_value == pytest.approx(-3.0)


# ===========================================================================
# 8. TEST PEŁNEJ ŚCIEŻKI WYKONAWCZEJ (SOLVER -> VERIFIER -> PASSPORT -> SENSITIVITY)
# ===========================================================================

def test_end_to_end_solver_verifier_passport_pipeline():
    """
    Sprawdza zintegrowany potok:
    ProblemIR -> Solver (CP-SAT / QAOA) -> Niezależny Weryfikator -> Paszport SHA-256 -> Test Wrażliwości.
    """
    reg = ExpressionRegistry()
    x = Variable(id="x", name="x", domain=VariableDomain.BINARY)
    y = Variable(id="y", name="y", domain=VariableDomain.BINARY)
    
    c3 = make_const(reg, 3.0)
    c4 = make_const(reg, 4.0)
    t0 = make_mul(reg, c3, make_var(reg, "x"))
    t1 = make_mul(reg, c4, make_var(reg, "y"))
    obj = make_sum(reg, [t0, t1])
    c_sum = make_sum(reg, [make_var(reg, "x"), make_var(reg, "y")])
    
    ir = ProblemIR(
        description_raw="pipeline test",
        description_formalised="pipeline test",
        variables=[x, y],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id=obj)],
        constraints=[Constraint(id="choose_one", type=ConstraintType.EQUALITY,
                                lhs_expression_id=c_sum, rhs_expression_id=make_const(reg, 1.0), hard=True)],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    
    solver = CPSATAdapter()
    res = solver.solve(ir, ComputeBudget(wall_time_seconds=5.0))
    assert res.execution_status == ExecutionStatus.COMPLETED
    assert res.assignment["x"] == 1
    assert res.assignment["y"] == 0
    assert res.objective_value == pytest.approx(3.0)
    
    verifier = IndependentVerifier(ir)
    cand = SolverCandidate(candidate_id="cand_1", assignment=res.assignment, claimed_objective=res.objective_value)
    report = verifier.verify(cand)
    assert report.feasible is True
    assert report.verdict == Verdict.PASS
    assert report.sha256_hash is not None
    assert len(report.sha256_hash) == 64
    assert report.optimality_gap_percent == pytest.approx(0.0, abs=1e-3)
    
    sens_engine = SensitivityEngine(ir)
    robustness = sens_engine.analyze(cand.candidate_id, cand.assignment, report.objective_value)
    assert robustness.verdict in ("HIGHLY_ROBUST", "MODERATELY_ROBUST", "FRAGILE")
    assert len(robustness.shock_levels) == 3


# ===========================================================================
# 9. TEST API HTTP DLA BRAMKI JAKOŚCI DANYCH
# ===========================================================================

@pytest.mark.asyncio
async def test_api_case_analyze_returns_input_quality_gate():
    """Weryfikuje, że endpoint HTTP /api/v1/cases/analyze zwraca pole input_quality."""
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Przypadek 1: zbyt krótki dylemat
        res_vague = await client.post(
            "/api/v1/cases/analyze",
            json={"text": "Co mam wybrać?"},
        )
        assert res_vague.status_code == 200
        data_vague = res_vague.json()
        assert "input_quality" in data_vague
        assert data_vague["input_quality"]["level"] == "too_vague"
        assert len(data_vague["input_quality"]["suggestions"]) > 0

        # Przypadek 2: precyzyjny dylemat
        res_good = await client.post(
            "/api/v1/cases/analyze",
            json={"text": "Wybór między ofertą Alpha za 20000 zł i pracą zdalną, a ofertą Beta za 30000 zł w Warszawie."},
        )
        assert res_good.status_code == 200
        data_good = res_good.json()
        assert "input_quality" in data_good
        assert data_good["input_quality"]["level"] == "sufficient"
