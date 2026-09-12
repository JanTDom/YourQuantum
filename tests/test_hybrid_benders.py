from datetime import datetime, timezone
import pytest

from backend.domain.problem_ir import (
    ComputeBudget, Constraint, ConstraintType, ExprNode, ExpressionRegistry,
    Objective, ObjectiveDirection, ProblemIR, Variable, VariableDomain,
)
from backend.solvers.hybrid_benders import HybridBendersAdapter


def test_hybrid_benders_adapter_solve():
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="v1", op="var", value="x1"))
    reg.add(ExprNode(id="v2", op="var", value="x2"))
    reg.add(ExprNode(id="c1", op="const", value=1.0))
    reg.add(ExprNode(id="c2", op="const", value=2.0))
    reg.add(ExprNode(id="m1", op="mul", children=["c1", "v1"]))
    reg.add(ExprNode(id="m2", op="mul", children=["c2", "v2"]))
    reg.add(ExprNode(id="obj", op="sum", children=["m1", "m2"]))

    # Constraint: x1 + x2 == 1 (exact choice of one)
    reg.add(ExprNode(id="lhs_sum", op="sum", children=["v1", "v2"]))
    reg.add(ExprNode(id="rhs_1", op="const", value=1.0))

    ir = ProblemIR(
        description_raw="test hybrid benders",
        description_formalised="min x1 + 2*x2 s.t. x1 + x2 == 1",
        variables=[
            Variable(id="x1", name="x1", domain=VariableDomain.BINARY),
            Variable(id="x2", name="x2", domain=VariableDomain.BINARY),
        ],
        expressions=reg,
        objectives=[Objective(id="o", direction=ObjectiveDirection.MINIMIZE, expression_id="obj")],
        constraints=[
            Constraint(
                id="eq_choice",
                lhs_expression_id="lhs_sum",
                rhs_expression_id="rhs_1",
                type=ConstraintType.EQUALITY,
                hard=True,
            )
        ],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )

    adapter = HybridBendersAdapter()
    assert adapter.supports(ir) is True
    assert adapter.name == "hybrid_benders"

    budget = ComputeBudget(wall_time_seconds=5.0, quantum_shots=512)
    res = adapter.solve(ir, budget)

    assert res.execution_status.value == "COMPLETED"
    assert res.math_status.value in ("FEASIBLE", "OPTIMAL")
    assert res.assignment.get("x1") == 1
    assert res.assignment.get("x2") == 0
    assert res.objective_value == 1.0
    assert "benders_iterations" in res.metadata
