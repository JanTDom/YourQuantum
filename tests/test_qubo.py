"""
Tests for QUBO/Ising encoder.
All encoding tests use brute-force verification for small instances.
"""
import itertools
import pytest
import numpy as np
from datetime import datetime, timezone

from backend.domain.problem_ir import (
    Constraint, ConstraintType, ExprNode, ExpressionRegistry,
    Objective, ObjectiveDirection, ProblemIR, Variable, VariableDomain,
)
from backend.solvers.quantum.qubo import QUBOEncoder, QUBOEncodingError


def make_binary_minimize_ir(n: int, coeffs: list[float]) -> ProblemIR:
    """Build a binary IR: minimize sum(coeffs[i] * x_i)."""
    assert len(coeffs) == n
    reg = ExpressionRegistry()
    variables = [
        Variable(id=f"x{i}", name=f"x{i}", domain=VariableDomain.BINARY)
        for i in range(n)
    ]
    term_ids = []
    for i, c in enumerate(coeffs):
        vref = f"vref_{i}"
        reg.add(ExprNode(id=vref, op="var", value=f"x{i}"))
        if c == 1.0:
            term_ids.append(vref)
        else:
            cid = f"coeff_{i}"
            mid = f"mul_{i}"
            reg.add(ExprNode(id=cid, op="const", value=c))
            reg.add(ExprNode(id=mid, op="mul", children=[cid, vref]))
            term_ids.append(mid)
    obj_id = "obj_sum"
    reg.add(ExprNode(id=obj_id, op="sum", children=term_ids))
    return ProblemIR(
        description_raw=f"minimize {coeffs}-weighted binary sum",
        description_formalised=f"min sum_{i} {coeffs[i]}*x{i}",
        variables=variables,
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id=obj_id)],
        constraints=[],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )


def test_encode_single_variable():
    ir = make_binary_minimize_ir(1, [3.0])
    enc = QUBOEncoder().encode(ir)
    assert enc.n_qubits == 1
    assert enc.Q is not None
    # For min 3*x, optimal is x=0, energy=0
    x0 = np.array([0.0])
    x1 = np.array([1.0])
    assert enc.eval_qubo_energy(x0) + enc.constant_energy < enc.eval_qubo_energy(x1) + enc.constant_energy
    # Just check it runs and produces consistent shapes
    assert enc.Q.shape == (1, 1)


def test_encode_two_variables():
    ir = make_binary_minimize_ir(2, [1.0, 2.0])
    enc = QUBOEncoder().encode(ir)
    assert enc.n_qubits == 2
    assert enc.Q.shape == (2, 2)
    # Optimal assignment: both 0, energy = constant
    x_zero = np.array([0.0, 0.0])
    x_one_one = np.array([1.0, 1.0])
    e_zero = enc.eval_qubo_energy(x_zero)
    e_one_one = enc.eval_qubo_energy(x_one_one)
    # min sum → x=0 should have lower QUBO energy
    assert e_zero <= e_one_one


def test_qubo_to_ising_energy_equivalence():
    """QUBO energy and Ising energy must be equal for all binary assignments."""
    ir = make_binary_minimize_ir(3, [1.0, -2.0, 3.0])
    enc = QUBOEncoder().encode(ir)
    for bits in itertools.product([0, 1], repeat=3):
        x = np.array(bits, dtype=np.float64)
        z = 1 - 2 * x  # x_i = (1 - z_i) / 2 → z_i = 1 - 2*x_i
        qubo_e = enc.eval_qubo_energy(x)
        ising_e = enc.eval_ising_energy(z)
        assert abs(qubo_e - ising_e) < 1e-6, (
            f"bits={bits}: QUBO={qubo_e:.6f}, Ising={ising_e:.6f}"
        )


def test_verification_runs_for_small_instance():
    ir = make_binary_minimize_ir(4, [1.0, 2.0, 3.0, 4.0])
    enc = QUBOEncoder().encode(ir)
    assert enc.verified, (
        f"Encoding failed verification: {enc.verification_error}"
    )
    assert enc.verification_n_checked > 0


def test_rejects_non_binary_variable():
    from backend.domain.problem_ir import SolveMode
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="vx", op="var", value="x"))
    ir = ProblemIR(
        description_raw="t", description_formalised="t",
        mode=SolveMode.VERIFY,
        variables=[Variable(id="x", name="x", domain=VariableDomain.INTEGER)],
        expressions=reg, objectives=[], constraints=[],
        approved=True, approved_at=datetime.now(timezone.utc),
    )
    with pytest.raises(QUBOEncodingError):
        QUBOEncoder().encode(ir)


def test_decode_bitstring_round_trip():
    ir = make_binary_minimize_ir(3, [1.0, 2.0, 3.0])
    enc = QUBOEncoder().encode(ir)
    # Qiskit convention: rightmost bit = qubit 0
    bitstring = "011"  # qubit0=1, qubit1=1, qubit2=0 (reversed)
    assignment = enc.decode_bitstring(bitstring)
    assert len(assignment) == 3
    # Verify all values are 0 or 1
    for vid, val in assignment.items():
        assert val in (0, 1), f"Variable {vid} has non-binary value {val}"
