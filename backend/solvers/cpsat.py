"""
YourQuantum — OR-Tools CP-SAT Adapter
Handles discrete constraint satisfaction and optimisation.
"""
from __future__ import annotations

import time
import traceback
from typing import Any

from backend.domain.problem_ir import (
    ComputeBudget, Constraint, ConstraintType, ExprNode,
    ObjectiveDirection, ProblemIR, Variable, VariableDomain,
)
from backend.domain.evaluator import ExpressionEvaluator
from backend.solvers.base import (
    ComputeSource, ExecutionStatus, MathStatus,
    ResourceEstimate, SolverAdapter, SolverResult,
)


class SolverModelError(Exception):
    """Raised when problem constraints or expressions cannot be represented in CP-SAT."""
    pass


class CPSATAdapter(SolverAdapter):
    """
    CP-SAT adapter for binary, integer, and mixed-integer problems.
    Uses google.protobuf CP-SAT solver from OR-Tools.
    Limitations:
    - Continuous variables are not natively supported (will be scaled).
    - Non-linear terms require linearisation or are unsupported.
    """

    @property
    def name(self) -> str:
        return "cp_sat"

    @property
    def version(self) -> str:
        try:
            from ortools.sat.python.cp_model import CpModel  # noqa: F401
            import ortools
            return ortools.__version__
        except Exception:
            return "unknown"

    def check_available(self) -> tuple[bool, str | None]:
        try:
            from ortools.sat.python import cp_model  # noqa: F401
            return True, None
        except Exception as e:
            return False, f"OR-Tools CP-SAT not available: {e}"

    def supports(self, problem: ProblemIR) -> bool:
        try:
            from ortools.sat.python import cp_model  # noqa: F401
        except ImportError:
            return False
        if not problem.is_ready_to_solve:
            return False
        # Check if variables are discrete
        for v in problem.variables:
            if v.domain not in (VariableDomain.BINARY, VariableDomain.INTEGER):
                return False
        return True

    def estimate_resources(
        self, problem: ProblemIR, budget: ComputeBudget
    ) -> ResourceEstimate:
        n_vars = len(problem.variables)
        n_constrs = len(problem.constraints)
        wall = min(budget.wall_time_seconds, 1.0 + 0.05 * (n_vars + n_constrs))
        mem = 64.0 + 0.5 * (n_vars + n_constrs)
        return ResourceEstimate(
            estimated_wall_time_seconds=wall,
            estimated_memory_mb=mem,
            source=ComputeSource.CLASSICAL,
            confidence="high" if n_vars < 100 else "medium",
            notes=["Estimate based on CP-SAT linear complexity heuristics."],
        )

    def solve(
        self, problem: ProblemIR, budget: ComputeBudget | None = None
    ) -> SolverResult:
        t0 = time.monotonic()
        budget = budget or problem.budget

        result = SolverResult(
            solver_name=self.name,
            solver_version=self.version,
            source=ComputeSource.CLASSICAL_SOLVER,
            execution_status=ExecutionStatus.RUNNING,
            math_status=MathStatus.UNKNOWN,
        )

        try:
            from ortools.sat.python import cp_model
        except ImportError:
            result.execution_status = ExecutionStatus.FAILED
            result.math_status = MathStatus.UNSUPPORTED
            result.error_message = "ortools is not installed in this environment."
            return result

        model = cp_model.CpModel()
        var_map: dict[str, Any] = {}

        # Build CP-SAT variables
        for var in problem.variables:
            if var.domain == VariableDomain.BINARY:
                var_map[var.id] = model.new_bool_var(var.name)
            elif var.domain == VariableDomain.INTEGER:
                lb = int(var.lower_bound) if var.lower_bound is not None else -10_000
                ub = int(var.upper_bound) if var.upper_bound is not None else 10_000
                var_map[var.id] = model.new_int_var(lb, ub, var.name)

        # Build constraints
        evaluator = ExpressionEvaluator(problem.expressions)
        try:
            for constraint in problem.constraints:
                self._add_constraint(model, constraint, var_map, problem)
        except Exception as e:
            result.execution_status = ExecutionStatus.FAILED
            result.math_status = MathStatus.MODEL_INVALID
            result.error_message = f"Constraint compilation error: {e}"
            raise SolverModelError(str(e)) from e

        # Build objective
        if problem.objectives:
            primary = problem.objectives[0]
            obj_affine = self._extract_affine(primary.expression_id, problem)
            if obj_affine is None:
                raise SolverModelError("Objective contains non-linear terms unsupported by CP-SAT.")
            
            coeffs, const = obj_affine
            scale = self._compute_scale_factor([const] + list(coeffs.values()))
            obj_expr = sum(
                int(round(c * scale)) * var_map[v]
                for v, c in coeffs.items()
                if abs(c) > 1e-9 and v in var_map
            )
            if primary.direction == ObjectiveDirection.MINIMIZE:
                model.minimize(obj_expr)
            else:
                model.maximize(obj_expr)

        # Solve with time limit
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = budget.wall_time_seconds
        solver.parameters.log_search_progress = False

        status_code = solver.solve(model)
        status_map = {
            cp_model.OPTIMAL: (ExecutionStatus.COMPLETED, MathStatus.OPTIMAL),
            cp_model.FEASIBLE: (ExecutionStatus.COMPLETED, MathStatus.FEASIBLE),
            cp_model.INFEASIBLE: (ExecutionStatus.COMPLETED, MathStatus.INFEASIBLE),
            cp_model.MODEL_INVALID: (ExecutionStatus.FAILED, MathStatus.MODEL_INVALID),
            cp_model.UNKNOWN: (ExecutionStatus.TIMED_OUT, MathStatus.UNKNOWN),
        }
        exec_st, math_st = status_map.get(
            status_code, (ExecutionStatus.FAILED, MathStatus.UNKNOWN)
        )
        result.execution_status = exec_st
        result.math_status = math_st
        result.solver_backend_status = solver.status_name(status_code)
        result.solve_time_seconds = time.monotonic() - t0

        if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            assignment: dict[str, Any] = {}
            for var in problem.variables:
                cp_var = var_map.get(var.id)
                if cp_var is not None:
                    assignment[var.id] = solver.value(cp_var)
            result.assignment = assignment

            # Re-evaluate exact objective from original ProblemIR
            if problem.objectives:
                try:
                    result.objective_value = evaluator.evaluate(
                        problem.objectives[0].expression_id, assignment
                    )
                except Exception:
                    result.objective_value = solver.objective_value
            else:
                result.objective_value = None

            if status_code == cp_model.OPTIMAL:
                result.lower_bound = solver.best_objective_bound
                result.optimality_gap = 0.0

        return result

    def _add_constraint(
        self,
        model: Any,
        constraint: Constraint,
        var_map: dict[str, Any],
        problem: ProblemIR,
    ) -> None:
        """Add a single constraint to the CP-SAT model with rational scaling."""
        lhs_affine = self._extract_affine(constraint.lhs_expression_id, problem)
        if lhs_affine is None:
            raise SolverModelError(
                f"Constraint {constraint.id}: LHS contains non-linear or unsupported expression."
            )
        
        rhs_affine = (
            self._extract_affine(constraint.rhs_expression_id, problem)
            if constraint.rhs_expression_id
            else ({}, 0.0)
        )
        if rhs_affine is None:
            raise SolverModelError(
                f"Constraint {constraint.id}: RHS contains non-linear or unsupported expression."
            )

        lhs_coeffs, lhs_const = lhs_affine
        rhs_coeffs, rhs_const = rhs_affine

        # Normalize to: sum net_coeffs * x + net_const (op) 0
        net_coeffs: dict[str, float] = dict(lhs_coeffs)
        for v, c in rhs_coeffs.items():
            net_coeffs[v] = net_coeffs.get(v, 0.0) - c
        net_const = lhs_const - rhs_const

        all_nums = [net_const] + list(net_coeffs.values())
        scale = self._compute_scale_factor(all_nums)

        scaled_coeffs = {
            v: int(round(c * scale))
            for v, c in net_coeffs.items()
            if abs(c) > 1e-9
        }
        scaled_const = int(round(net_const * scale))

        expr = sum(
            scaled_coeffs[v] * var_map[v]
            for v in scaled_coeffs
            if v in var_map
        )

        ctype = constraint.type
        if ctype == ConstraintType.EQUALITY:
            model.add(expr + scaled_const == 0)
        elif ctype == ConstraintType.INEQUALITY_LE:
            model.add(expr + scaled_const <= 0)
        elif ctype == ConstraintType.INEQUALITY_GE:
            model.add(expr + scaled_const >= 0)
        else:
            raise SolverModelError(
                f"Constraint {constraint.id}: Constraint type {ctype} not supported by CP-SAT."
            )

    def _extract_affine(
        self,
        node_id: str,
        problem: ProblemIR,
    ) -> tuple[dict[str, float], float] | None:
        """Recursively extract (coefficients_dict, constant) from affine expression node."""
        node = problem.expressions.nodes.get(node_id)
        if node is None:
            return None

        if node.op == "const":
            return ({}, float(node.value or 0.0))

        if node.op == "var":
            return ({str(node.value): 1.0}, 0.0)

        if node.op in ("add", "sub") and len(node.children) == 2:
            a = self._extract_affine(node.children[0], problem)
            b = self._extract_affine(node.children[1], problem)
            if a is None or b is None:
                return None
            sign = 1.0 if node.op == "add" else -1.0
            coeffs = dict(a[0])
            for v, c in b[0].items():
                coeffs[v] = coeffs.get(v, 0.0) + sign * c
            return (coeffs, a[1] + sign * b[1])

        if node.op == "sum":
            total_coeffs: dict[str, float] = {}
            total_const = 0.0
            for c_id in node.children:
                aff = self._extract_affine(c_id, problem)
                if aff is None:
                    return None
                for v, c in aff[0].items():
                    total_coeffs[v] = total_coeffs.get(v, 0.0) + c
                total_const += aff[1]
            return (total_coeffs, total_const)

        if node.op == "neg" and len(node.children) == 1:
            a = self._extract_affine(node.children[0], problem)
            if a is None:
                return None
            return ({v: -c for v, c in a[0].items()}, -a[1])

        if node.op == "mul" and len(node.children) == 2:
            a = self._extract_affine(node.children[0], problem)
            b = self._extract_affine(node.children[1], problem)
            if a is None or b is None:
                return None
            # At least one must be a pure constant
            is_const_a = len(a[0]) == 0
            is_const_b = len(b[0]) == 0
            if is_const_a:
                const_val = a[1]
                return ({v: c * const_val for v, c in b[0].items()}, b[1] * const_val)
            if is_const_b:
                const_val = b[1]
                return ({v: c * const_val for v, c in a[0].items()}, a[1] * const_val)
            # Both have variables -> non-linear!
            return None

        return None

    def _compute_scale_factor(self, numbers: list[float]) -> float:
        """Find integer scaling factor up to 10^4 for floating point values."""
        max_decimals = 0
        for num in numbers:
            if abs(num) < 1e-9:
                continue
            # Count decimals
            s = f"{abs(num):.6f}".rstrip("0")
            if "." in s:
                decimals = len(s.split(".")[1])
                max_decimals = max(max_decimals, min(decimals, 4))
        return 10.0 ** max_decimals

    def _base_limitations(self, math_status: MathStatus) -> list[str]:
        return [
            "Global optimality claimed by solver; no independent certificate validated.",
            "Model-optimal result does not guarantee real-world validity.",
        ]
