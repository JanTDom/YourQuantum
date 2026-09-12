from datetime import datetime, timezone
import pytest

from backend.domain.problem_ir import (
    Constraint, ConstraintType, ExprNode, ExpressionRegistry,
    Objective, ObjectiveDirection, ProblemIR, Variable, VariableDomain,
)
from backend.domain.sensitivity import SensitivityEngine


def test_sensitivity_engine_resilience():
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="vx", op="var", value="x"))
    reg.add(ExprNode(id="vy", op="var", value="y"))
    reg.add(ExprNode(id="c1", op="const", value=10.0))
    reg.add(ExprNode(id="c2", op="const", value=20.0))
    reg.add(ExprNode(id="m1", op="mul", children=["c1", "vx"]))
    reg.add(ExprNode(id="m2", op="mul", children=["c2", "vy"]))
    reg.add(ExprNode(id="obj", op="sum", children=["m1", "m2"]))

    # Constraint: x + y <= 1 (budget/cardinality)
    reg.add(ExprNode(id="lhs_sum", op="sum", children=["vx", "vy"]))
    reg.add(ExprNode(id="rhs_limit", op="const", value=2.0))

    ir = ProblemIR(
        description_raw="test sensitivity",
        description_formalised="min 10*x + 20*y s.t. x+y <= 2",
        variables=[
            Variable(id="x", name="x", domain=VariableDomain.BINARY),
            Variable(id="y", name="y", domain=VariableDomain.BINARY),
        ],
        expressions=reg,
        objectives=[Objective(id="o", direction=ObjectiveDirection.MINIMIZE, expression_id="obj")],
        constraints=[
            Constraint(
                id="c_limit",
                lhs_expression_id="lhs_sum",
                rhs_expression_id="rhs_limit",
                type=ConstraintType.INEQUALITY_LE,
                hard=True,
            )
        ],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )

    engine = SensitivityEngine(ir)
    assignment = {"x": 1.0, "y": 0.0}
    report = engine.analyze("cand_1", assignment, baseline_objective=10.0)

    assert report.candidate_id == "cand_1"
    assert report.robustness_score >= 0.0
    assert report.robustness_score <= 1.0
    assert report.verdict in ("HIGHLY_ROBUST", "MODERATELY_ROBUST", "FRAGILE")
    assert len(report.shock_levels) == 3
    assert len(report.summary_pl) > 20
