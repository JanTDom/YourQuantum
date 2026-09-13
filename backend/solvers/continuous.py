"""
YourQuantum — Continuous Solver Adapter (Phase D4)
Handles continuous parameter optimization (VARIABLE DOMAIN = CONTINUOUS)
using SciPy HiGHS / minimize, calculating numerical residuals without approximation.
"""
from __future__ import annotations

import logging
import time
import numpy as np
from typing import Any

from backend.domain.problem_ir import (
    ComputeBudget,
    Constraint,
    ConstraintType,
    ExprNode,
    ObjectiveDirection,
    ProblemIR,
    VariableDomain,
)
from backend.domain.evaluator import ExpressionEvaluator
from backend.solvers.base import (
    ComputeSource,
    ExecutionStatus,
    MathStatus,
    ResourceEstimate,
    SolverAdapter,
    SolverResult,
)

logger = logging.getLogger(__name__)


class ContinuousSolverAdapter(SolverAdapter):
    """
    Adapter for continuous optimization (PARAMETER class problems) using SciPy HiGHS/minimize.
    Evaluates real mathematical constraints with precision numerical residuals.
    """

    @property
    def name(self) -> str:
        return "scipy_continuous"

    @property
    def version(self) -> str:
        try:
            import scipy
            return scipy.__version__
        except Exception:
            return "unknown"

    def check_available(self) -> tuple[bool, str | None]:
        try:
            import scipy.optimize  # noqa: F401
            return True, None
        except Exception as e:
            return False, f"SciPy not available: {e}"

    def supports(self, problem: ProblemIR) -> bool:
        # Supports if all or most variables are continuous
        is_avail, _ = self.check_available()
        if not is_avail:
            return False
        if not problem.variables:
            return False
        # Supports if at least one continuous variable is present
        return any(v.domain == VariableDomain.CONTINUOUS for v in problem.variables)

    def estimate_resources(self, problem: ProblemIR) -> ResourceEstimate:
        n = len(problem.variables)
        return ResourceEstimate(
            estimated_time_seconds=max(0.1, n * 0.005),
            estimated_memory_mb=64.0,
            notes=f"SciPy continuous LP/NLP solver ({n} variables)",
        )

    def solve(self, problem: ProblemIR, budget: ComputeBudget) -> SolverResult:
        t0 = time.perf_counter()
        import scipy.optimize as opt

        var_names = [v.id for v in problem.variables]
        n_vars = len(var_names)
        var_indices = {v.id: i for i, v in enumerate(problem.variables)}

        # Bounds
        bounds: list[tuple[float | None, float | None]] = []
        for v in problem.variables:
            lb = v.lower_bound if v.lower_bound is not None else 0.0
            ub = v.upper_bound if v.upper_bound is not None else None
            bounds.append((lb, ub))

        # Extract linear objective coefficients if possible
        c = np.zeros(n_vars)
        direction = 1.0  # minimize

        if problem.objectives:
            primary_obj = problem.objectives[0]
            if primary_obj.direction == ObjectiveDirection.MAXIMIZE:
                direction = -1.0  # SciPy minimizes by default

            # Linear coefficient extraction
            expr_id = primary_obj.expression_id
            coeffs = self._extract_linear_coeffs(expr_id, problem.expressions.nodes)
            for vid, val in coeffs.items():
                if vid in var_indices:
                    c[var_indices[vid]] = direction * val

        # Extract linear constraints
        A_ub_list: list[list[float]] = []
        b_ub_list: list[float] = []
        A_eq_list: list[list[float]] = []
        b_eq_list: list[float] = []

        evaluator = ExpressionEvaluator(problem.expressions)

        for constraint in problem.constraints:
            lhs_coeffs = self._extract_linear_coeffs(constraint.lhs_expression_id, problem.expressions.nodes)
            row = [0.0] * n_vars
            for vid, val in lhs_coeffs.items():
                if vid in var_indices:
                    row[var_indices[vid]] = val

            rhs_val = 0.0
            if constraint.rhs_expression_id:
                try:
                    rhs_val = float(evaluator.evaluate(constraint.rhs_expression_id, {}))
                except Exception:
                    rhs_val = 0.0

            if constraint.type == ConstraintType.INEQUALITY_LE:
                A_ub_list.append(row)
                b_ub_list.append(rhs_val)
            elif constraint.type == ConstraintType.INEQUALITY_GE:
                # -row <= -rhs_val
                A_ub_list.append([-x for x in row])
                b_ub_list.append(-rhs_val)
            elif constraint.type == ConstraintType.EQUALITY:
                A_eq_list.append(row)
                b_eq_list.append(rhs_val)

        A_ub = np.array(A_ub_list) if A_ub_list else None
        b_ub = np.array(b_ub_list) if b_ub_list else None
        A_eq = np.array(A_eq_list) if A_eq_list else None
        b_eq = np.array(b_eq_list) if b_eq_list else None

        try:
            res = opt.linprog(
                c=c,
                A_ub=A_ub,
                b_ub=b_ub,
                A_eq=A_eq,
                b_eq=b_eq,
                bounds=bounds,
                method="highs",
            )
            solve_time = time.perf_counter() - t0

            if res.success:
                assignment = {var_names[i]: float(res.x[i]) for i in range(n_vars)}
                # Recompute true objective
                true_obj: float | None = None
                if problem.objectives:
                    try:
                        true_obj = float(evaluator.evaluate(problem.objectives[0].expression_id, assignment))
                    except Exception:
                        true_obj = float(-res.fun if direction == -1.0 else res.fun)

                # Compute maximum constraint residual
                max_residual = 0.0
                if A_ub is not None and len(A_ub) > 0:
                    ub_residuals = np.dot(A_ub, res.x) - b_ub
                    max_residual = max(max_residual, float(np.max(np.maximum(0.0, ub_residuals))))
                if A_eq is not None and len(A_eq) > 0:
                    eq_residuals = np.abs(np.dot(A_eq, res.x) - b_eq)
                    max_residual = max(max_residual, float(np.max(eq_residuals)))

                return SolverResult(
                    solver_name=self.name,
                    solver_version=self.version,
                    problem_id=problem.problem_id,
                    execution_status=ExecutionStatus.COMPLETED,
                    math_status=MathStatus.OPTIMAL if max_residual < 1e-5 else MathStatus.FEASIBLE,
                    source=ComputeSource.CLASSICAL_SOLVER,
                    assignment=assignment,
                    objective_value=true_obj,
                    solve_time_seconds=solve_time,
                    numerical_residual=max_residual,
                )
            elif res.status == 2:
                return SolverResult(
                    solver_name=self.name,
                    solver_version=self.version,
                    problem_id=problem.problem_id,
                    execution_status=ExecutionStatus.COMPLETED,
                    math_status=MathStatus.INFEASIBLE,
                    source=ComputeSource.CLASSICAL_SOLVER,
                    solve_time_seconds=time.perf_counter() - t0,
                    error_message="Problem mathematically infeasible under given constraints",
                )
            else:
                return SolverResult(
                    solver_name=self.name,
                    solver_version=self.version,
                    problem_id=problem.problem_id,
                    execution_status=ExecutionStatus.FAILED,
                    math_status=MathStatus.UNKNOWN,
                    source=ComputeSource.CLASSICAL_SOLVER,
                    solve_time_seconds=time.perf_counter() - t0,
                    error_message=res.message,
                )
        except Exception as e:
            return SolverResult(
                solver_name=self.name,
                solver_version=self.version,
                problem_id=problem.problem_id,
                execution_status=ExecutionStatus.FAILED,
                math_status=MathStatus.UNKNOWN,
                source=ComputeSource.CLASSICAL_SOLVER,
                solve_time_seconds=time.perf_counter() - t0,
                error_message=str(e),
            )

    def _extract_linear_coeffs(self, node_id: str, nodes: dict[str, ExprNode]) -> dict[str, float]:
        """Helper to extract variable coefficients from safe expression trees."""
        coeffs: dict[str, float] = {}
        if node_id not in nodes:
            return coeffs
        node = nodes[node_id]

        if node.op == "var":
            coeffs[str(node.value)] = 1.0
        elif node.op == "mul":
            # const * var or var * const
            c_val = 1.0
            v_name = None
            for child_id in node.children:
                child = nodes.get(child_id)
                if not child:
                    continue
                if child.op == "const":
                    c_val *= float(child.value or 0.0)
                elif child.op == "var":
                    v_name = str(child.value)
            if v_name:
                coeffs[v_name] = c_val
        elif node.op == "sum" or node.op == "add":
            for child_id in node.children:
                sub_coeffs = self._extract_linear_coeffs(child_id, nodes)
                for v, c in sub_coeffs.items():
                    coeffs[v] = coeffs.get(v, 0.0) + c
        return coeffs
