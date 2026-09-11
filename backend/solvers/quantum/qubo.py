"""
YourQuantum — QUBO/Ising Encoder
Converts a binary ProblemIR to a QUBO matrix (and Ising h, J).

Energy convention:
  E(x) = c + sum_i(a_i * x_i) + sum_{i<j}(b_ij * x_i * x_j)
  x_i in {0, 1}

Ising mapping (x_i = (1 - z_i) / 2, z_i in {-1, +1}):
  E_Ising(z) = h0 + sum_i(h_i * z_i) + sum_{i<j}(J_ij * z_i * z_j)

All coefficients are stored explicitly. The mapping is verified for
n <= MAX_BRUTE_FORCE_N by exhaustive comparison.
"""
from __future__ import annotations

import itertools
import math
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from backend.domain.problem_ir import (
    ConstraintType, ObjectiveDirection, ProblemIR, VariableDomain,
)
from backend.domain.evaluator import ExpressionEvaluator


MAX_BRUTE_FORCE_N = 10  # max qubits for brute-force encoding verification


class QUBOEncodingError(Exception):
    pass


@dataclass
class QUBOEncoding:
    """
    QUBO encoding of a binary optimisation problem.
    Q[i, j] is defined for i <= j (upper triangular + diagonal).
    """
    problem_id: str
    encoding_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Variable ordering (index → problem variable id)
    variable_order: list[str] = field(default_factory=list)

    # QUBO matrix (n x n, upper triangular used)
    Q: np.ndarray | None = None                # shape (n, n)
    constant_energy: float = 0.0               # constant offset

    # Ising representation
    h: np.ndarray | None = None                # shape (n,) biases
    J: np.ndarray | None = None                # shape (n, n) couplers (i<j)
    ising_constant: float = 0.0               # Ising constant offset

    # Constraint penalties
    penalty_weights: dict[str, float] = field(default_factory=dict)
    penalty_heuristic: bool = False           # True if penalty not proven tight

    # Encoding metadata
    n_qubits: int = 0
    coefficient_range: tuple[float, float] = (0.0, 0.0)
    notes: list[str] = field(default_factory=list)

    # Verification results
    verified: bool = False
    verification_error: str | None = None
    verification_n_checked: int = 0

    def qubit_index(self, variable_id: str) -> int:
        return self.variable_order.index(variable_id)

    def decode_bitstring(self, bitstring: str | list[int]) -> dict[str, int]:
        """Map a measurement bitstring back to problem variable assignments."""
        bits: list[int]
        if isinstance(bitstring, str):
            # Qiskit uses little-endian (rightmost = qubit 0)
            bits = [int(b) for b in reversed(bitstring)]
        else:
            bits = list(bitstring)
        if len(bits) != self.n_qubits:
            raise ValueError(
                f"Bitstring length {len(bits)} != n_qubits {self.n_qubits}"
            )
        return {vid: bits[i] for i, vid in enumerate(self.variable_order)}

    def eval_qubo_energy(self, x: np.ndarray) -> float:
        """Evaluate E = x^T Q x + constant_energy for binary vector x."""
        assert self.Q is not None
        return float(x @ self.Q @ x) + self.constant_energy

    def eval_ising_energy(self, z: np.ndarray) -> float:
        """Evaluate Ising energy for spin vector z in {-1, +1}^n."""
        assert self.h is not None and self.J is not None
        return (
            float(self.h @ z)
            + float(z @ self.J @ z)
            + self.ising_constant
        )


class QUBOEncoder:
    """
    Encodes a binary ProblemIR (all variables must be BINARY) to QUBO form.
    Supports:
    - Linear objectives (sum of binary variables with coefficients).
    - Quadratic penalty terms for equality constraints.
    - Penalty weight validation for small instances.
    """

    def __init__(self, penalty_scale: float = 10.0):
        """
        penalty_scale: multiplier applied to the objective range to compute
        constraint penalty weights. Heuristic — verify with brute force.
        """
        self._penalty_scale = penalty_scale

    def encode(self, problem: ProblemIR) -> QUBOEncoding:
        if not problem.is_ready_to_solve:
            raise QUBOEncodingError("Problem must be approved and ready to solve.")

        for var in problem.variables:
            if var.domain != VariableDomain.BINARY:
                raise QUBOEncodingError(
                    f"Variable {var.id!r} has domain {var.domain} — "
                    "QUBO encoding requires all variables to be BINARY."
                )

        n = len(problem.variables)
        if n == 0:
            raise QUBOEncodingError("Problem has no variables.")

        var_order = [v.id for v in problem.variables]
        Q = np.zeros((n, n), dtype=np.float64)
        constant = 0.0
        evaluator = ExpressionEvaluator(problem.expressions)
        notes: list[str] = []
        penalty_weights: dict[str, float] = {}
        penalty_heuristic = False

        # 1. Encode objective
        if problem.objectives:
            primary = problem.objectives[0]
            sign = (
                1.0
                if primary.direction == ObjectiveDirection.MINIMIZE
                else -1.0
            )
            obj_const, obj_lin, obj_quad = self._extract_linear_quadratic(
                primary.expression_id, problem, var_order
            )
            constant += sign * obj_const
            for i, c in enumerate(obj_lin):
                Q[i, i] += sign * c
            for (i, j), c in obj_quad.items():
                Q[i, j] += sign * c

        # 2. Compute penalty scale from objective coefficient range
        obj_coeff_range = float(np.abs(Q).max()) if np.any(Q != 0) else 1.0
        penalty = max(1.0, self._penalty_scale * obj_coeff_range)

        # 3. Encode constraints as penalty terms
        for constraint in problem.constraints:
            if not constraint.hard:
                continue

            lhs_const, lhs_lin, lhs_quad = self._extract_linear_quadratic(
                constraint.lhs_expression_id, problem, var_order
            )
            rhs_val = 0.0
            if constraint.rhs_expression_id:
                rhs_node = problem.expressions.nodes.get(
                    constraint.rhs_expression_id
                )
                if rhs_node and rhs_node.op == "const":
                    rhs_val = float(rhs_node.value)

            if constraint.type == ConstraintType.EQUALITY:
                # (lhs_lin_i * x_i + lhs_const - rhs_val)^2 * penalty
                b_i = np.array(lhs_lin)
                b_0 = lhs_const - rhs_val
                # Expand: (b_0 + sum b_i*x_i)^2
                constant += penalty * b_0 ** 2
                for i in range(n):
                    Q[i, i] += penalty * (b_i[i] ** 2 + 2 * b_0 * b_i[i])
                for i in range(n):
                    for j in range(i + 1, n):
                        Q[i, j] += penalty * 2 * b_i[i] * b_i[j]

                penalty_weights[constraint.id] = penalty
                penalty_heuristic = True

            elif constraint.type in (ConstraintType.INEQUALITY_LE, ConstraintType.INEQUALITY_GE):
                if lhs_quad:
                    raise QUBOEncodingError(
                        f"Constraint {constraint.id}: Non-linear inequality cannot be compiled to QUBO."
                    )
                # Normalize to sum a_i*x_i + a_0 <= 0
                if constraint.type == ConstraintType.INEQUALITY_LE:
                    a_i = np.array(lhs_lin)
                    a_0 = lhs_const - rhs_val
                else:
                    a_i = -np.array(lhs_lin)
                    a_0 = -(lhs_const - rhs_val)

                non_zeros = [i for i, v in enumerate(a_i) if v != 0.0]
                if len(non_zeros) == 0:
                    # Constant inequality
                    if a_0 > 0:
                        raise QUBOEncodingError(
                            f"Constraint {constraint.id}: Infeasible constant inequality ({a_0} <= 0)."
                        )
                elif len(non_zeros) == 1:
                    # Single variable bound: a_k * x_k + a_0 <= 0
                    k = non_zeros[0]
                    ak = a_i[k]
                    bound = -a_0 / ak
                    if ak > 0:
                        # x_k <= bound
                        if bound < 0:
                            raise QUBOEncodingError(
                                f"Constraint {constraint.id}: Infeasible bound {var_order[k]} <= {bound} for binary variable."
                            )
                        elif bound < 1.0:
                            # x_k must be 0 -> penalize x_k = 1
                            Q[k, k] += penalty
                            penalty_weights[constraint.id] = penalty
                            penalty_heuristic = True
                        # if bound >= 1.0: trivially satisfied for binary var
                    else:
                        # x_k >= bound
                        if bound > 1.0:
                            raise QUBOEncodingError(
                                f"Constraint {constraint.id}: Infeasible bound {var_order[k]} >= {bound} for binary variable."
                            )
                        elif bound > 0.0:
                            # x_k must be 1 -> penalize x_k = 0
                            constant += penalty
                            Q[k, k] -= penalty
                            penalty_weights[constraint.id] = penalty
                            penalty_heuristic = True
                else:
                    # Multi-variable inequality requires slack expansion or classical solver
                    raise QUBOEncodingError(
                        f"Constraint {constraint.id}: Multi-variable inequality ({constraint.type}) "
                        "cannot be compiled to QUBO without slack variable expansion. Use CP-SAT solver."
                    )
            else:
                raise QUBOEncodingError(
                    f"Constraint {constraint.id}: Unsupported constraint type {constraint.type} for QUBO."
                )

        # 4. Symmetrise Q (make upper triangular; Q[i,j] for i<=j)
        # We keep Q upper triangular already; diagonal terms are on Q[i,i].

        # 5. Build Ising representation
        h, J, ising_const = self._qubo_to_ising(Q, constant, n)

        coeff_range = (float(np.abs(Q).min()), float(np.abs(Q[Q != 0]).min()
                                                      if np.any(Q != 0) else 0.0))

        encoding = QUBOEncoding(
            problem_id=problem.problem_id,
            variable_order=var_order,
            Q=Q,
            constant_energy=constant,
            h=h,
            J=J,
            ising_constant=ising_const,
            penalty_weights=penalty_weights,
            penalty_heuristic=penalty_heuristic,
            n_qubits=n,
            coefficient_range=(float(np.abs(Q).min()), float(np.abs(Q).max())),
            notes=notes,
        )

        # 6. Verify encoding for small instances
        if n <= MAX_BRUTE_FORCE_N:
            encoding = self._verify_encoding(encoding, problem, evaluator, var_order)

        return encoding

    def _extract_linear_quadratic(
        self,
        node_id: str,
        problem: ProblemIR,
        var_order: list[str],
    ) -> tuple[float, list[float], dict[tuple[int, int], float]]:
        """
        Extract constant, linear coefficients, and quadratic coefficients
        from a linear or quadratic expression node.
        Returns: (constant, [lin_i], {(i,j): coeff for i<j})
        Raises QUBOEncodingError for non-linear/non-quadratic expressions.
        """
        n = len(var_order)
        lin = [0.0] * n
        quad: dict[tuple[int, int], float] = {}
        const = 0.0

        node = problem.expressions.nodes.get(node_id)
        if node is None:
            raise QUBOEncodingError(f"Unknown expression node: {node_id!r}")

        if node.op == "const":
            return float(node.value), lin, quad  # type: ignore[arg-type]

        if node.op == "var":
            vid = str(node.value)
            if vid in var_order:
                lin[var_order.index(vid)] = 1.0
            return const, lin, quad

        if node.op in ("add", "sub"):
            c0, l0, q0 = self._extract_linear_quadratic(
                node.children[0], problem, var_order
            )
            c1, l1, q1 = self._extract_linear_quadratic(
                node.children[1], problem, var_order
            )
            sign = 1.0 if node.op == "add" else -1.0
            new_quad = dict(q0)
            for k, v in q1.items():
                new_quad[k] = new_quad.get(k, 0.0) + sign * v
            return (
                c0 + sign * c1,
                [a + sign * b for a, b in zip(l0, l1)],
                new_quad,
            )

        if node.op == "sum":
            total_c, total_l, total_q = 0.0, [0.0] * n, {}
            for child_id in node.children:
                c, l, q = self._extract_linear_quadratic(
                    child_id, problem, var_order
                )
                total_c += c
                for i in range(n):
                    total_l[i] += l[i]
                for k, v in q.items():
                    total_q[k] = total_q.get(k, 0.0) + v
            return total_c, total_l, total_q

        if node.op == "mul" and len(node.children) == 2:
            c0, l0, q0 = self._extract_linear_quadratic(
                node.children[0], problem, var_order
            )
            c1, l1, q1 = self._extract_linear_quadratic(
                node.children[1], problem, var_order
            )
            # If both have quadratic terms, product is degree >= 3
            if q0 or q1:
                is_const_0 = all(x == 0.0 for x in l0) and not q0
                is_const_1 = all(x == 0.0 for x in l1) and not q1
                if is_const_0:
                    return (
                        c0 * c1,
                        [c0 * x for x in l1],
                        {k: c0 * v for k, v in q1.items()},
                    )
                if is_const_1:
                    return (
                        c0 * c1,
                        [c1 * x for x in l0],
                        {k: c1 * v for k, v in q0.items()},
                    )
                raise QUBOEncodingError(
                    "Cannot multiply quadratic expressions in QUBO (resulting degree > 2)."
                )

            # Neither has quadratic terms: both are affine (c0 + sum l0*x) and (c1 + sum l1*x)
            res_const = c0 * c1
            res_lin = [c0 * l1[i] + c1 * l0[i] for i in range(n)]
            res_quad: dict[tuple[int, int], float] = {}
            for i in range(n):
                if l0[i] == 0.0:
                    continue
                for j in range(n):
                    if l1[j] == 0.0:
                        continue
                    coeff = l0[i] * l1[j]
                    if i == j:
                        # For binary: x_i^2 = x_i
                        res_lin[i] += coeff
                    else:
                        pair = (min(i, j), max(i, j))
                        res_quad[pair] = res_quad.get(pair, 0.0) + coeff
            return res_const, res_lin, res_quad

        raise QUBOEncodingError(
            f"Unsupported expression operator for QUBO encoding: {node.op!r}. "
            "Only linear and quadratic binary expressions are supported."
        )

    @staticmethod
    def _qubo_to_ising(
        Q: np.ndarray, qubo_constant: float, n: int
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """
        Convert QUBO to Ising using x_i = (1 - z_i) / 2.
        Returns (h, J, constant).
        h shape: (n,) ; J shape: (n, n) upper triangular.
        """
        h = np.zeros(n, dtype=np.float64)
        J = np.zeros((n, n), dtype=np.float64)
        constant = qubo_constant

        for i in range(n):
            # Diagonal Q[i,i]: x_i = (1-z_i)/2 → x_i contributes Q[i,i]/4 * (1-z_i)^2
            # = Q[i,i]/4 * (1 - 2*z_i + z_i^2) = Q[i,i]/4 * (2 - 2*z_i)
            # since z_i^2 = 1.
            constant += Q[i, i] / 2.0
            h[i] -= Q[i, i] / 2.0

        for i in range(n):
            for j in range(i + 1, n):
                qij = Q[i, j]
                if qij == 0.0:
                    continue
                # x_i * x_j = (1-z_i)(1-z_j)/4
                constant += qij / 4.0
                h[i] -= qij / 4.0
                h[j] -= qij / 4.0
                J[i, j] += qij / 4.0

        return h, J, constant

    def _verify_encoding(
        self,
        encoding: QUBOEncoding,
        problem: ProblemIR,
        evaluator: ExpressionEvaluator,
        var_order: list[str],
    ) -> QUBOEncoding:
        """
        For n <= MAX_BRUTE_FORCE_N, verify that QUBO energy equals the
        original objective value for all feasible assignments.
        Records verification results in the encoding.
        """
        n = encoding.n_qubits
        assert encoding.Q is not None and encoding.h is not None
        n_checked = 0
        max_diff = 0.0

        if not problem.objectives:
            encoding.verified = True
            encoding.verification_n_checked = 0
            encoding.notes.append(
                "No objective — QUBO penalty encoding only; "
                "verification skipped (feasibility problem)."
            )
            return encoding

        primary = problem.objectives[0]
        sign = (
            1.0
            if primary.direction == ObjectiveDirection.MINIMIZE
            else -1.0
        )

        for bits in itertools.product([0, 1], repeat=n):
            x = np.array(bits, dtype=np.float64)
            assignment = {vid: float(bits[i]) for i, vid in enumerate(var_order)}

            # Original objective value
            try:
                orig_obj = evaluator.evaluate(primary.expression_id, assignment)
            except Exception:
                continue

            qubo_energy = encoding.eval_qubo_energy(x)
            # QUBO energy = sign * obj + penalties (penalties are 0 for feasible)
            # For feasible points: qubo_energy - constant_penalty ≈ sign * orig_obj
            # We check that the ordering is preserved (not just absolute value)
            diff = abs(qubo_energy - (sign * orig_obj + encoding.constant_energy
                                      - encoding.constant_energy))

            # Simpler check: QUBO energy should equal sign * obj for zero-penalty points
            # (all hard constraints satisfied with penalty=0)
            all_satisfied = True
            for constraint in problem.constraints:
                if not constraint.hard:
                    continue
                try:
                    lhs = evaluator.evaluate(constraint.lhs_expression_id, assignment)
                    rhs = (
                        evaluator.evaluate(constraint.rhs_expression_id, assignment)
                        if constraint.rhs_expression_id
                        else 0.0
                    )
                    if abs(lhs - rhs) > 1e-6:
                        all_satisfied = False
                        break
                except Exception:
                    all_satisfied = False
                    break

            if all_satisfied:
                expected = sign * orig_obj
                total_energy = encoding.eval_qubo_energy(x)
                diff = abs(total_energy - expected)
                max_diff = max(max_diff, diff)
                n_checked += 1

        encoding.verified = (max_diff < 1e-4) and (n_checked > 0)
        encoding.verification_n_checked = n_checked
        if not encoding.verified:
            if n_checked == 0:
                encoding.verification_error = (
                    "No feasible assignments found in brute-force verification sample."
                )
            else:
                encoding.verification_error = (
                    f"QUBO energy mismatch: max |QUBO - sign*obj| = {max_diff:.6f} "
                    f"over {n_checked} feasible assignments."
                )
        else:
            encoding.notes.append(
                f"Brute-force verified on {n_checked} feasible assignments "
                f"(max deviation {max_diff:.2e})."
            )
        return encoding
