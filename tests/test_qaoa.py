"""
Tests for QAOA Quantum Solver Adapter.
Verifies real circuit building, Aer statevector simulation, and audit record.
"""
from datetime import datetime, timezone
import pytest

from backend.domain.problem_ir import (
    ComputeBudget, Constraint, ConstraintType, ExprNode, ExpressionRegistry,
    Objective, ObjectiveDirection, ProblemIR, Variable, VariableDomain,
)
from backend.solvers.base import ComputeSource, ExecutionStatus, MathStatus
from backend.solvers.quantum.qaoa import QAOAAdapter, QISKIT_AVAILABLE


@pytest.mark.skipif(not QISKIT_AVAILABLE, reason="Qiskit Aer not installed")
def test_qaoa_supports_binary_problems():
    adapter = QAOAAdapter()
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="vx", op="var", value="x"))
    reg.add(ExprNode(id="obj", op="var", value="x"))

    # Binary problem -> supported
    ir_binary = ProblemIR(
        description_raw="test",
        description_formalised="test",
        variables=[Variable(id="x", name="x", domain=VariableDomain.BINARY)],
        expressions=reg,
        objectives=[Objective(id="o1", direction=ObjectiveDirection.MINIMIZE, expression_id="obj")],
        constraints=[],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    assert adapter.supports(ir_binary) is True

    # Integer problem -> not supported
    ir_int = ProblemIR(
        description_raw="test",
        description_formalised="test",
        variables=[Variable(id="x", name="x", domain=VariableDomain.INTEGER)],
        expressions=reg,
        objectives=[Objective(id="o1", direction=ObjectiveDirection.MINIMIZE, expression_id="obj")],
        constraints=[],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    assert adapter.supports(ir_int) is False


@pytest.mark.skipif(not QISKIT_AVAILABLE, reason="Qiskit Aer not installed")
def test_qaoa_solves_small_instance():
    """Solve a 2-qubit minimization problem with QAOA on Qiskit Aer."""
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="vx0", op="var", value="x0"))
    reg.add(ExprNode(id="vx1", op="var", value="x1"))
    reg.add(ExprNode(id="c2", op="const", value=2.0))
    reg.add(ExprNode(id="mul_x1", op="mul", children=["c2", "vx1"]))
    reg.add(ExprNode(id="sum_obj", op="sum", children=["vx0", "mul_x1"]))

    ir = ProblemIR(
        description_raw="min x0 + 2*x1",
        description_formalised="min x0 + 2*x1",
        variables=[
            Variable(id="x0", name="x0", domain=VariableDomain.BINARY),
            Variable(id="x1", name="x1", domain=VariableDomain.BINARY),
        ],
        expressions=reg,
        objectives=[Objective(id="o1", direction=ObjectiveDirection.MINIMIZE, expression_id="sum_obj")],
        constraints=[],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )

    adapter = QAOAAdapter()
    budget = ComputeBudget(wall_time_seconds=10.0, quantum_shots=512)
    result = adapter.solve(ir, budget)

    assert result.execution_status == ExecutionStatus.COMPLETED
    assert result.source == ComputeSource.QUANTUM_CIRCUIT_SIMULATION
    assert result.assignment is not None
    assert "x0" in result.assignment
    assert "x1" in result.assignment
    assert "qaoa_run_record" in result.metadata

    record = result.metadata["qaoa_run_record"]
    assert record["n_qubits"] == 2
    assert record["p_layers"] == 1
    assert record["circuit_depth"] is not None
    assert record["circuit_depth"] > 0
    assert len(record["sample_distribution"]) > 0
    assert len(result.limitations) > 0
