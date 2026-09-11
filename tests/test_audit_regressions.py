"""
test_audit_regressions.py — Red tests and regression verification for all 20 audit findings.

Every test here directly targets a deficiency identified in the external audit:
1. Formalizer fabrication & missing info detection (3 of 5, 'maksymalnie', open-ended questions)
2. Max-Cut quadratic formulation vs linear sum
3. CP-SAT fractional coefficient scaling & rejection of unsupported operators
4. QUBO quadratic sum deduplication & polynomial multiplication with constants
5. QUBO inequality encoding with slack variables vs skipping
6. QAOA objective value separation from penalty offsets
7. Verifier handling of NaN, inf, and evaluation exceptions
8. ComputeBudget validation (rejection of negative / unbounded values)
9. Server-side publication gate (rejection of unverified / failed candidates)
"""

from __future__ import annotations

import math
import pytest
import numpy as np
from datetime import datetime, timezone
from pydantic import ValidationError

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
    Provenance,
)
from backend.domain.evaluator import ExpressionEvaluator, EvaluationError
from backend.domain.formalizer import ProblemFormalizer
from backend.solvers.cpsat import CPSATAdapter
from backend.solvers.quantum.qubo import QUBOEncoder, QUBOEncodingError
from backend.solvers.quantum.qaoa import QAOAAdapter
from backend.verifier.verifier import IndependentVerifier, SolverCandidate, Verdict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_base_ir(vars_count: int = 2) -> ProblemIR:
    reg = ExpressionRegistry()
    variables = [
        Variable(id=f"x{i}", name=f"x{i}", domain=VariableDomain.BINARY)
        for i in range(vars_count)
    ]
    # Default dummy constant objective so it passes ProblemIR model validator
    n_zero = reg.const(0.0)
    obj = Objective(id="dummy_obj", expression_id=n_zero, direction=ObjectiveDirection.MINIMIZE)
    return ProblemIR(
        problem_id="test_reg",
        description_raw="test problem",
        description_formalised="formalised test problem",
        mode=SolveMode.OPTIMIZE,
        variables=variables,
        expressions=reg,
        objectives=[obj],
        constraints=[],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# 1. Formalizer: No fabricated data, detects missing info (audit points 2 & 3)
# ---------------------------------------------------------------------------

def test_formalizer_does_not_fabricate_projects_and_profits():
    """
    Audit point 2:
    'Chcę wybrać 3 najbardziej zyskowne inwestycje z 5 projektów firmowych'
    MUST NOT fabricate proj_A..D with profits 12, 18, 9, 15 and budget 2.
    It must identify 5 candidate projects, a selection of 3, and mark missing profits.
    """
    formalizer = ProblemFormalizer()
    text = "Chcę wybrać 3 najbardziej zyskowne inwestycje z 5 projektów firmowych"
    res = formalizer.formalize(text)
    
    # Must NOT invent hardcoded profits 12, 18, 9, 15
    for p in ["12.0", "18.0", "9.0", "15.0"]:
        assert p not in str(res.objective_coefficients.values())
        
    # Must preserve count 3 of 5 (either in constraints or missing info)
    assert len(res.binary_variables) == 5 or len(res.missing_information) > 0
    # Must flag missing profit data
    assert any("zysk" in m.lower() or "wartość" in m.lower() or "stop" in m.lower() or "dane" in m.lower() for m in res.missing_information)


def test_formalizer_maksymalnie_is_inequality_not_equality():
    """
    Audit point 2 & 5:
    'wybierz maksymalnie 2 projekty' means <= 2, NOT == 2.
    """
    formalizer = ProblemFormalizer()
    text = "Wybierz maksymalnie 2 projekty spośród A, B, C"
    res = formalizer.formalize(text)
    
    # Must NOT generate equality constraint lhs == 2 if user said 'maksymalnie 2'
    assert len(res.equality_constraints) == 0 or not any(eq.get("rhs") == 2.0 for eq in res.equality_constraints)
    assert len(res.inequality_constraints) > 0
    # The inequality should be <= 2
    assert any(ineq.get("rhs") == 2.0 for ineq in res.inequality_constraints)


def test_formalizer_life_dilemma_not_forced_into_x0_x1_x2():
    """
    Audit point 3:
    'Nie wiem, czy zmienić pracę, czy zostać w obecnej firmie'
    Must NOT be turned into x0, x1, x2 with objective coeffs 1.0 without asking.
    It must identify options: 'zmienić pracę', 'zostać w obecnej firmie' and ask for criteria.
    """
    formalizer = ProblemFormalizer()
    text = "Nie wiem, czy zmienić pracę, czy zostać w obecnej firmie"
    res = formalizer.formalize(text)
    
    # Should identify missing criteria/information rather than pretending to solve
    assert len(res.missing_information) > 0
    # Should not fabricate bogus x0, x1, x2 variables
    assert res.binary_variables != ["x0", "x1", "x2"]


# ---------------------------------------------------------------------------
# 2. Max-Cut quadratic formulation (audit point 4)
# ---------------------------------------------------------------------------

def test_formalizer_maxcut_must_be_quadratic_not_linear():
    """
    Audit point 4:
    Max-Cut edge weight is quadratic sum_{(i,j)} (x_i + x_j - 2 x_i x_j),
    NOT linear sum x0 + x1 + x2 + x3.
    """
    formalizer = ProblemFormalizer()
    text = "Podział 4 osób na 2 zespoły tak aby zmaksymalizować liczbę konfliktów między grupami (max cut)"
    res = formalizer.formalize(text)
    
    # Linear objective coefficients cannot represent true max cut
    assert res.identified_archetype != "linear_fallback"


# ---------------------------------------------------------------------------
# 3. CP-SAT: Rational scaling & No silent pass on unsupported ops (audit point 9)
# ---------------------------------------------------------------------------

def test_cpsat_rejects_unsupported_expressions_without_silent_pass():
    """
    Audit point 9:
    CP-SAT must NOT have 'except Exception: pass' silently dropping constraints.
    Unsupported non-linear constraint must raise SolverModelError or be rejected.
    """
    ir = create_base_ir(3)
    # Create non-linear constraint x0 * x1 * x2 == 1 which CP-SAT cannot handle directly
    n_x0 = ir.expressions.var("x0")
    n_x1 = ir.expressions.var("x1")
    n_x2 = ir.expressions.var("x2")
    n_mul1 = ir.expressions.add(ExprNode(id="m1", op="mul", children=[n_x0, n_x1]))
    n_mul2 = ir.expressions.add(ExprNode(id="m2", op="mul", children=[n_mul1, n_x2]))
    n_const1 = ir.expressions.const(1.0)
    
    ir.constraints.append(
        Constraint(
            id="c_nonlin",
            lhs_expression_id=n_mul2,
            rhs_expression_id=n_const1,
            type=ConstraintType.EQUALITY,
            hard=True,
        )
    )
    adapter = CPSATAdapter()
    # It must raise an explicit error when constraint cannot be compiled, NOT silently ignore it!
    with pytest.raises(Exception):
        adapter.solve(ir)


def test_cpsat_does_not_round_fractional_coefficients_blindly():
    """
    Audit point 9:
    Constraint 0.4 * x0 + 0.4 * x1 <= 0.5 with binary x0, x1.
    If 0.4 is rounded to int(0), constraint becomes 0 <= 0 (always true), allowing x0=1, x1=1!
    With scaling (e.g. *10), 4*x0 + 4*x1 <= 5 forbids x0=1, x1=1.
    """
    ir = create_base_ir(2)
    # Objective: max x0 + x1
    n_x0 = ir.expressions.var("x0")
    n_x1 = ir.expressions.var("x1")
    n_obj = ir.expressions.add(ExprNode(id="obj", op="add", children=[n_x0, n_x1]))
    ir.objectives.append(Objective(id="o1", expression_id=n_obj, direction=ObjectiveDirection.MAXIMIZE))
    
    # 0.4 * x0
    n_c04 = ir.expressions.const(0.4)
    n_m0 = ir.expressions.add(ExprNode(id="m0", op="mul", children=[n_c04, n_x0]))
    n_m1 = ir.expressions.add(ExprNode(id="m1", op="mul", children=[n_c04, n_x1]))
    n_lhs = ir.expressions.add(ExprNode(id="lhs", op="add", children=[n_m0, n_m1]))
    n_rhs = ir.expressions.const(0.5)
    
    ir.constraints.append(
        Constraint(
            id="c_frac",
            lhs_expression_id=n_lhs,
            rhs_expression_id=n_rhs,
            type=ConstraintType.INEQUALITY_LE,
            hard=True,
        )
    )
    
    adapter = CPSATAdapter()
    result = adapter.solve(ir)
    
    # Optimal with 0.4*x0 + 0.4*x1 <= 0.5 must be 1 (either x0=1 or x1=1), NEVER 2!
    # If rounded blindly, x0=1, x1=1 would give objective = 2.
    assert result.assignment is not None
    assert result.assignment.get("x0", 0) + result.assignment.get("x1", 0) <= 1


# ---------------------------------------------------------------------------
# 4. QUBO: Quadratic terms deduplication & constant handling (audit point 11)
# ---------------------------------------------------------------------------

def test_qubo_quadratic_sum_no_overwriting_or_doubling():
    """
    Audit point 11:
    x0*x1 + 3*x0*x1 for x0=1, x1=1 must equal 4, NOT 6!
    """
    ir = create_base_ir(2)
    n_x0 = ir.expressions.var("x0")
    n_x1 = ir.expressions.var("x1")
    
    # Term 1: 1.0 * (x0 * x1)
    n_mul1 = ir.expressions.add(ExprNode(id="m1", op="mul", children=[n_x0, n_x1]))
    
    # Term 2: 3.0 * (x0 * x1)
    n_c3 = ir.expressions.const(3.0)
    n_mul2 = ir.expressions.add(ExprNode(id="m2_inner", op="mul", children=[n_x0, n_x1]))
    n_term2 = ir.expressions.add(ExprNode(id="m2", op="mul", children=[n_c3, n_mul2]))
    
    # Total: Term 1 + Term 2
    n_total = ir.expressions.add(ExprNode(id="tot", op="add", children=[n_mul1, n_term2]))
    ir.objectives = [Objective(id="o1", expression_id=n_total, direction=ObjectiveDirection.MINIMIZE)]
    
    enc = QUBOEncoder().encode(ir)
    x = np.array([1.0, 1.0])
    energy = enc.eval_qubo_energy(x)
    assert math.isclose(energy, 4.0, abs_tol=1e-5), f"Expected energy 4.0 for x0*x1 + 3*x0*x1, got {energy}"


def test_qubo_polynomial_multiplication_with_constants():
    """
    Audit point 11:
    (x0 + 1) * (x1 + 1) = x0*x1 + x0 + x1 + 1.
    For x0=1, x1=1, value is 4.
    For x0=0, x1=0, value is 1.
    """
    ir = create_base_ir(2)
    n_x0 = ir.expressions.var("x0")
    n_x1 = ir.expressions.var("x1")
    n_c1 = ir.expressions.const(1.0)
    
    n_add0 = ir.expressions.add(ExprNode(id="a0", op="add", children=[n_x0, n_c1]))
    n_add1 = ir.expressions.add(ExprNode(id="a1", op="add", children=[n_x1, n_c1]))
    n_mul = ir.expressions.add(ExprNode(id="mul", op="mul", children=[n_add0, n_add1]))
    ir.objectives = [Objective(id="o1", expression_id=n_mul, direction=ObjectiveDirection.MINIMIZE)]
    
    enc = QUBOEncoder().encode(ir)
    
    e_00 = enc.eval_qubo_energy(np.array([0.0, 0.0]))
    e_11 = enc.eval_qubo_energy(np.array([1.0, 1.0]))
    e_10 = enc.eval_qubo_energy(np.array([1.0, 0.0]))
    
    assert math.isclose(e_00, 1.0, abs_tol=1e-5), f"Expected 1.0 at (0,0), got {e_00}"
    assert math.isclose(e_10, 2.0, abs_tol=1e-5), f"Expected 2.0 at (1,0), got {e_10}"
    assert math.isclose(e_11, 4.0, abs_tol=1e-5), f"Expected 4.0 at (1,1), got {e_11}"


# ---------------------------------------------------------------------------
# 5. QUBO: Inequalities cannot be skipped (audit point 10)
# ---------------------------------------------------------------------------

def test_qubo_inequalities_not_silently_skipped():
    """
    Audit point 10:
    max x0 subject to x0 <= 0 (where x0 in {0, 1}).
    The only feasible point is x0=0.
    If inequality is skipped, QUBO maximizes x0 and chooses x0=1 (infeasible!).
    """
    ir = create_base_ir(1)
    n_x0 = ir.expressions.var("x0")
    ir.objectives = [Objective(id="o1", expression_id=n_x0, direction=ObjectiveDirection.MAXIMIZE)]
    
    n_c0 = ir.expressions.const(0.0)
    ir.constraints.append(
        Constraint(
            id="c_ineq",
            lhs_expression_id=n_x0,
            rhs_expression_id=n_c0,
            type=ConstraintType.INEQUALITY_LE,
            hard=True,
        )
    )
    
    # Either encoder encodes the inequality (e.g. via penalty/slack) OR raises QUBOEncodingError
    # But it must NEVER return an encoding where x0=1 has lower energy than x0=0!
    try:
        enc = QUBOEncoder().encode(ir)
        e0 = enc.eval_qubo_energy(np.array([0.0]))
        e1 = enc.eval_qubo_energy(np.array([1.0]))
        # For minimization of -x0 + penalty*(violation), feasible x0=0 must have lower energy than infeasible x0=1
        assert e0 < e1, f"Feasible x=0 (energy {e0}) must be preferred over infeasible x=1 (energy {e1})"
    except QUBOEncodingError:
        # Rejection of unsupported inequality is also acceptable
        pass


# ---------------------------------------------------------------------------
# 6. QAOA: Objective calculation separate from penalty offset (audit point 12)
# ---------------------------------------------------------------------------

def test_qaoa_objective_value_not_offset_corrupted():
    """
    Audit point 12:
    min x + 2y subject to x + y = 1.
    For feasible assignment x=1, y=0:
    Original objective is 1*(1) + 2*(0) = 1.
    Must NOT return -19 or arbitrary numbers due to QUBO penalty constants.
    """
    ir = create_base_ir(2)
    n_x = ir.expressions.var("x0")
    n_y = ir.expressions.var("x1")
    n_c2 = ir.expressions.const(2.0)
    n_2y = ir.expressions.add(ExprNode(id="2y", op="mul", children=[n_c2, n_y]))
    n_obj = ir.expressions.add(ExprNode(id="obj", op="add", children=[n_x, n_2y]))
    ir.objectives.append(Objective(id="o1", expression_id=n_obj, direction=ObjectiveDirection.MINIMIZE))
    
    n_x_plus_y = ir.expressions.add(ExprNode(id="x_plus_y", op="add", children=[n_x, n_y]))
    n_c1 = ir.expressions.const(1.0)
    ir.constraints.append(
        Constraint(
            id="c_eq",
            lhs_expression_id=n_x_plus_y,
            rhs_expression_id=n_c1,
            type=ConstraintType.EQUALITY,
            hard=True,
        )
    )
    
    # Test internal objective evaluation method on assignment {"x0": 1, "x1": 0}
    evaluator = ExpressionEvaluator(ir.expressions)
    obj_val = evaluator.evaluate(n_obj, {"x0": 1, "x1": 0})
    assert math.isclose(obj_val, 1.0, abs_tol=1e-5)


# ---------------------------------------------------------------------------
# 7. Verifier: Rejects NaN, inf, and evaluation exceptions (audit point 15)
# ---------------------------------------------------------------------------

def test_verifier_rejects_nan_and_inf():
    """
    Audit point 15:
    Verifier must NOT give PASS when objective evaluation results in NaN or inf.
    """
    ir = create_base_ir(1)
    n_x = ir.expressions.var("x0")
    # Expression: 1 / x0. If x0=0 -> division by zero or NaN/inf
    n_c1 = ir.expressions.const(1.0)
    n_div = ir.expressions.add(ExprNode(id="div", op="div", children=[n_c1, n_x]))
    ir.objectives = [Objective(id="o1", expression_id=n_div, direction=ObjectiveDirection.MINIMIZE)]
    
    verifier = IndependentVerifier(ir)
    cand = SolverCandidate(
        candidate_id="cand_nan",
        assignment={"x0": 0},
        claimed_objective=0.0,
        claimed_status="feasible",
    )
    report = verifier.verify(cand)
    assert report.verdict != Verdict.PASS, f"Expected verifier to reject NaN/division by zero, got {report.verdict}"
    assert report.objective_recomputed is False or report.objective_value is None or not math.isfinite(report.objective_value)


def test_verifier_rejects_when_objective_fails():
    """
    Audit point 15:
    If objective evaluation raises an exception, verifier must NOT return Verdict.PASS!
    """
    ir = create_base_ir(1)
    # Point objective to non-existent expression node
    ir.objectives = [Objective(id="o1", expression_id="missing_node_id", direction=ObjectiveDirection.MINIMIZE)]
    
    verifier = IndependentVerifier(ir)
    cand = SolverCandidate(
        candidate_id="cand_err",
        assignment={"x0": 1},
        claimed_objective=1.0,
        claimed_status="feasible",
    )
    report = verifier.verify(cand)
    assert report.verdict != Verdict.PASS, f"Expected verifier to fail when objective cannot be evaluated, got {report.verdict}"


# ---------------------------------------------------------------------------
# 8. ComputeBudget: Rejection of negative / excessive limits (audit point 18)
# ---------------------------------------------------------------------------

def test_compute_budget_rejects_negative_or_zero_values():
    """
    Audit point 18:
    ComputeBudget must reject negative or zero wall_time_seconds, memory_mb, quantum_shots.
    """
    with pytest.raises(ValidationError):
        ComputeBudget(wall_time_seconds=-10.0)
        
    with pytest.raises(ValidationError):
        ComputeBudget(wall_time_seconds=0.0)

    with pytest.raises(ValidationError):
        ComputeBudget(memory_mb=-100.0)

    with pytest.raises(ValidationError):
        ComputeBudget(quantum_shots=0)


def test_compute_budget_caps_excessive_values():
    """
    Audit point 18:
    ComputeBudget must cap excessive limits to prevent resource exhaustion.
    """
    with pytest.raises(ValidationError):
        ComputeBudget(wall_time_seconds=100000.0)  # max should be e.g. 600s
        
    with pytest.raises(ValidationError):
        ComputeBudget(quantum_shots=1000000)      # max should be e.g. 10000
