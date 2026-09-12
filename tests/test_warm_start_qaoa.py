import pytest
import numpy as np
from datetime import datetime, timezone

from backend.domain.problem_ir import (
    ComputeBudget, ExprNode, ExpressionRegistry,
    Objective, ObjectiveDirection, ProblemIR, Variable, VariableDomain,
)
from backend.solvers.quantum.qaoa import QAOAAdapter, QISKIT_AVAILABLE
from backend.solvers.quantum.qubo import QUBOEncoder


@pytest.mark.skipif(not QISKIT_AVAILABLE, reason="Qiskit not installed")
def test_qaoa_warm_start_relaxation():
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="v1", op="var", value="x1"))
    reg.add(ExprNode(id="v2", op="var", value="x2"))
    reg.add(ExprNode(id="c1", op="const", value=2.0))
    reg.add(ExprNode(id="c2", op="const", value=5.0))
    reg.add(ExprNode(id="m1", op="mul", children=["c1", "v1"]))
    reg.add(ExprNode(id="m2", op="mul", children=["c2", "v2"]))
    reg.add(ExprNode(id="obj", op="sum", children=["m1", "m2"]))

    ir = ProblemIR(
        description_raw="min 2*x1 + 5*x2",
        description_formalised="min 2*x1 + 5*x2",
        variables=[
            Variable(id="x1", name="x1", domain=VariableDomain.BINARY),
            Variable(id="x2", name="x2", domain=VariableDomain.BINARY),
        ],
        expressions=reg,
        objectives=[Objective(id="o", direction=ObjectiveDirection.MINIMIZE, expression_id="obj")],
        constraints=[],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )

    adapter = QAOAAdapter()
    encoding = QUBOEncoder().encode(ir)
    x_star, rel_energy = adapter._compute_continuous_relaxation(encoding)

    assert len(x_star) == 2
    assert all(0.0 <= x <= 1.0 for x in x_star)
    # For min 2*x1 + 5*x2, continuous relaxation should drive x towards 0.0 (clipped to 0.05)
    assert x_star[0] <= 0.2
    assert x_star[1] <= 0.2

    budget = ComputeBudget(wall_time_seconds=5.0, quantum_shots=256)
    res = adapter.solve(ir, budget)

    assert res.execution_status.value == "COMPLETED"
    assert res.metadata.get("warm_started") is True
    assert "relaxation_energy" in res.metadata
    assert res.assignment.get("x1") == 0
    assert res.assignment.get("x2") == 0
