"""Tests for the IndependentVerifier."""
import pytest
from datetime import datetime, timezone
from backend.domain.problem_ir import (
    Constraint, ConstraintType, ExprNode, ExpressionRegistry,
    Objective, ObjectiveDirection, ProblemIR, Variable, VariableDomain,
)
from backend.verifier.verifier import (
    IndependentVerifier, SolverCandidate, Verdict,
)


def build_ir_with_constraint(
    lhs_val: float, rhs_val: float, ctype: ConstraintType
) -> ProblemIR:
    """Build IR with one binary var and one constraint: lhs op rhs."""
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="vx", op="var", value="x"))
    reg.add(ExprNode(id="lhs", op="const", value=lhs_val))
    reg.add(ExprNode(id="rhs", op="const", value=rhs_val))
    reg.add(ExprNode(id="obj_vx", op="var", value="x"))
    return ProblemIR(
        description_raw="test",
        description_formalised="test",
        variables=[Variable(id="x", name="x", domain=VariableDomain.BINARY)],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id="obj_vx")],
        constraints=[Constraint(id="c0", type=ctype,
                                lhs_expression_id="lhs",
                                rhs_expression_id="rhs", hard=True)],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )


def test_verifier_requires_approved_ir():
    reg = ExpressionRegistry()
    ir = ProblemIR(
        description_raw="t", description_formalised="t",
        variables=[], expressions=reg,
        approved=False,
    )
    with pytest.raises(ValueError):
        IndependentVerifier(ir)


def test_pass_when_equality_satisfied():
    ir = build_ir_with_constraint(1.0, 1.0, ConstraintType.EQUALITY)
    v = IndependentVerifier(ir)
    report = v.verify(SolverCandidate(
        candidate_id="cand1", assignment={"x": 1}, claimed_objective=1.0
    ))
    assert report.feasible
    assert report.verdict == Verdict.PASS


def test_fail_when_equality_violated():
    ir = build_ir_with_constraint(1.0, 2.0, ConstraintType.EQUALITY)
    v = IndependentVerifier(ir)
    report = v.verify(SolverCandidate(
        candidate_id="cand2", assignment={"x": 1}
    ))
    assert not report.feasible
    assert report.verdict == Verdict.FAIL


def test_pass_inequality_le():
    ir = build_ir_with_constraint(1.0, 2.0, ConstraintType.INEQUALITY_LE)
    v = IndependentVerifier(ir)
    report = v.verify(SolverCandidate(candidate_id="c3", assignment={"x": 0}))
    assert report.feasible


def test_fail_inequality_le_violated():
    ir = build_ir_with_constraint(5.0, 2.0, ConstraintType.INEQUALITY_LE)
    v = IndependentVerifier(ir)
    report = v.verify(SolverCandidate(candidate_id="c4", assignment={"x": 0}))
    # lhs=5, rhs=2, 5 <= 2 is False
    assert not report.feasible
    assert report.verdict == Verdict.FAIL


def test_domain_violation_binary():
    from backend.domain.problem_ir import SolveMode
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="vx", op="var", value="x"))
    ir = ProblemIR(
        description_raw="t", description_formalised="t",
        mode=SolveMode.VERIFY,
        variables=[Variable(id="x", name="x", domain=VariableDomain.BINARY)],
        expressions=reg, objectives=[], constraints=[],
        approved=True, approved_at=datetime.now(timezone.utc),
    )
    v = IndependentVerifier(ir)
    # Assigning 0.5 to a binary variable is a domain violation
    report = v.verify(SolverCandidate(candidate_id="c5", assignment={"x": 0.5}))
    assert "x" in report.domain_violations
    assert not report.feasible


def test_objective_recomputed_correctly():
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="vx", op="var", value="x"))
    reg.add(ExprNode(id="vy", op="var", value="y"))
    reg.add(ExprNode(id="sum", op="sum", children=["vx", "vy"]))
    ir = ProblemIR(
        description_raw="t", description_formalised="t",
        variables=[
            Variable(id="x", name="x", domain=VariableDomain.BINARY),
            Variable(id="y", name="y", domain=VariableDomain.BINARY),
        ],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id="sum")],
        constraints=[],
        approved=True, approved_at=datetime.now(timezone.utc),
    )
    v = IndependentVerifier(ir)
    report = v.verify(SolverCandidate(
        candidate_id="c6", assignment={"x": 1, "y": 0}, claimed_objective=1.0
    ))
    assert report.objective_value == pytest.approx(1.0)
    assert report.objective_recomputed
    assert report.verdict == Verdict.PASS


def test_limitations_always_present():
    from backend.domain.problem_ir import SolveMode
    reg = ExpressionRegistry()
    ir = ProblemIR(
        description_raw="t", description_formalised="t",
        mode=SolveMode.VERIFY,
        variables=[], expressions=reg, objectives=[], constraints=[],
        approved=True, approved_at=datetime.now(timezone.utc),
    )
    v = IndependentVerifier(ir)
    report = v.verify(SolverCandidate(candidate_id="c7", assignment={}))
    assert len(report.limitations) > 0
