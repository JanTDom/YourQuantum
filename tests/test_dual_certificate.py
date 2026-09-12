from datetime import datetime, timezone
import pytest

from backend.domain.problem_ir import (
    Constraint, ConstraintType, ExprNode, ExpressionRegistry,
    Objective, ObjectiveDirection, ProblemIR, Variable, VariableDomain,
)
from backend.verifier.verifier import IndependentVerifier, SolverCandidate


def test_independent_verifier_dual_bound_and_sha256():
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="v1", op="var", value="x1"))
    reg.add(ExprNode(id="v2", op="var", value="x2"))
    reg.add(ExprNode(id="c1", op="const", value=3.0))
    reg.add(ExprNode(id="c2", op="const", value=4.0))
    reg.add(ExprNode(id="m1", op="mul", children=["c1", "v1"]))
    reg.add(ExprNode(id="m2", op="mul", children=["c2", "v2"]))
    reg.add(ExprNode(id="obj", op="sum", children=["m1", "m2"]))

    # Constraint: x1 + x2 >= 1
    reg.add(ExprNode(id="lhs_sum", op="sum", children=["v1", "v2"]))
    reg.add(ExprNode(id="rhs_1", op="const", value=1.0))

    ir = ProblemIR(
        description_raw="min 3*x1 + 4*x2 s.t. x1 + x2 >= 1",
        description_formalised="min 3*x1 + 4*x2 s.t. x1 + x2 >= 1",
        variables=[
            Variable(id="x1", name="x1", domain=VariableDomain.BINARY),
            Variable(id="x2", name="x2", domain=VariableDomain.BINARY),
        ],
        expressions=reg,
        objectives=[Objective(id="o", direction=ObjectiveDirection.MINIMIZE, expression_id="obj")],
        constraints=[
            Constraint(
                id="c1",
                lhs_expression_id="lhs_sum",
                rhs_expression_id="rhs_1",
                type=ConstraintType.INEQUALITY_GE,
                hard=True,
            )
        ],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )

    verifier = IndependentVerifier(ir)
    candidate = SolverCandidate(
        candidate_id="cand_opt",
        assignment={"x1": 1.0, "x2": 0.0},
        claimed_objective=3.0,
        claimed_status="optimal",
    )

    report = verifier.verify(candidate)
    assert report.verdict.value == "PASS"
    assert report.feasible is True
    assert report.objective_value == 3.0
    assert report.optimality_proven is True
    assert report.dual_bound is not None
    assert report.optimality_gap_percent is not None
    assert report.optimality_gap_percent <= 0.01
    assert len(report.sha256_hash) == 64
