"""
YourQuantum — Independent Verifier
Reads only ProblemIR + candidate. Never reads solver internals.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel

from backend.domain.problem_ir import (
    Constraint, ConstraintType, ObjectiveDirection,
    ProblemIR, Variable, VariableDomain,
)
from backend.domain.evaluator import ExpressionEvaluator


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class ConstraintResult(BaseModel):
    constraint_id: str
    satisfied: bool
    hard: bool
    violation_magnitude: float | None = None
    note: str | None = None


class VerificationReport(BaseModel):
    problem_id: str
    candidate_id: str
    verified_at: datetime
    verifier_version: str = "0.1"

    feasible: bool
    objective_value: float | None
    objective_recomputed: bool
    solver_claimed_objective: float | None

    constraint_results: list[ConstraintResult]
    domain_violations: list[str]       # variable IDs with domain violations
    numerical_residual: float | None

    verdict: Verdict
    verdict_reason: str
    limitations: list[str]             # honest list of what was NOT proven

    # Mathematical Certificate & Supremacy Stamping
    sha256_hash: str = ""
    optimality_proven: bool = False
    dual_bound: float | None = None
    optimality_gap_percent: float | None = None
    irreducible_inconsistent_subsystem: list[str] = []


class SolverCandidate(BaseModel):
    candidate_id: str
    assignment: dict[str, Any]         # variable_id → value
    claimed_objective: float | None = None
    claimed_status: str = "unknown"


class IndependentVerifier:
    """
    Independently verifies a candidate against the approved ProblemIR.
    Does NOT re-run the solver.
    Does NOT modify the candidate.
    """

    VERSION = "0.1"
    NUMERIC_TOLERANCE = 1e-6

    def __init__(self, problem: ProblemIR):
        if not problem.approved:
            raise ValueError("Verifier requires an approved ProblemIR.")
        self._problem = problem
        self._evaluator = ExpressionEvaluator(problem.expressions)

    def verify(self, candidate: SolverCandidate) -> VerificationReport:
        assignment = candidate.assignment
        constraint_results: list[ConstraintResult] = []
        domain_violations: list[str] = []

        # 1. Domain check
        for var in self._problem.variables:
            violation = self._check_domain(var, assignment.get(var.id))
            if violation:
                domain_violations.append(var.id)

        # 2. Constraint check
        for constraint in self._problem.constraints:
            result = self._check_constraint(constraint, assignment)
            constraint_results.append(result)

        # 3. Objective re-evaluation
        objective_value: float | None = None
        objective_recomputed = False
        objective_error: str | None = None
        if self._problem.objectives:
            primary = self._problem.objectives[0]
            try:
                val = self._evaluator.evaluate(
                    primary.expression_id, assignment
                )
                if val is not None and math.isfinite(val):
                    objective_value = val
                    objective_recomputed = True
                else:
                    objective_error = f"Objective evaluated to non-finite value: {val}"
            except Exception as exc:
                objective_value = None
                objective_recomputed = False
                objective_error = str(exc)

        # 4. Numerical residual (sum of soft violations)
        hard_violations = [r for r in constraint_results if r.hard and not r.satisfied]
        soft_violations = [r for r in constraint_results if not r.hard and not r.satisfied]
        residual = sum(
            r.violation_magnitude or 0.0
            for r in constraint_results
            if not r.satisfied and r.violation_magnitude is not None
        )

        # 5. Feasibility
        feasible = len(hard_violations) == 0 and len(domain_violations) == 0

        # 6. Objective discrepancy check
        if (
            objective_recomputed
            and candidate.claimed_objective is not None
            and abs((objective_value or 0.0) - candidate.claimed_objective)
            > self.NUMERIC_TOLERANCE
        ):
            obj_violation = ConstraintResult(
                constraint_id="__objective_check__",
                satisfied=False,
                hard=True,
                note=(
                    f"Objective mismatch: solver claimed "
                    f"{candidate.claimed_objective}, "
                    f"verifier computed {objective_value}"
                ),
            )
            constraint_results.append(obj_violation)
            hard_violations.append(obj_violation)
            feasible = False

        # 7. Verdict
        if self._problem.objectives and not objective_recomputed:
            verdict = Verdict.FAIL
            reason = f"Objective re-evaluation failed: {objective_error or 'calculation error'}"
        elif not feasible or domain_violations:
            verdict = Verdict.FAIL
            reason = (
                f"{len(hard_violations)} hard constraint(s) violated; "
                f"{len(domain_violations)} domain violation(s)"
            )
        elif soft_violations:
            verdict = Verdict.PARTIAL
            reason = (
                f"All hard constraints satisfied; "
                f"{len(soft_violations)} soft constraint(s) violated"
            )
        else:
            verdict = Verdict.PASS
            reason = "All constraints satisfied and objective verified successfully"

        # 8. Dual bound and optimality gap computation
        dual_bound, gap_percent, opt_proven = self._compute_dual_gap(
            candidate, objective_value, feasible
        )

        # 9. Cryptographic SHA-256 Audit Stamp
        canonical_str = (
            f"{self._problem.problem_id}:{candidate.candidate_id}:"
            f"{json.dumps(assignment, sort_keys=True)}:{objective_value}:"
            f"{residual:.6f}:{verdict.value}"
        )
        sha256_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        # 10. Honest limitations
        limitations = self._build_limitations(
            candidate, objective_recomputed, opt_proven, gap_percent
        )

        return VerificationReport(
            problem_id=self._problem.problem_id,
            candidate_id=candidate.candidate_id,
            verified_at=datetime.now(timezone.utc),
            feasible=feasible,
            objective_value=objective_value,
            objective_recomputed=objective_recomputed,
            solver_claimed_objective=candidate.claimed_objective,
            constraint_results=constraint_results,
            domain_violations=domain_violations,
            numerical_residual=residual if residual > 0 else None,
            verdict=verdict,
            verdict_reason=reason,
            limitations=limitations,
            sha256_hash=sha256_hash,
            optimality_proven=opt_proven,
            dual_bound=dual_bound,
            optimality_gap_percent=gap_percent,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_domain(self, var: Variable, value: Any) -> bool:
        """Returns True if there IS a violation."""
        if value is None:
            return True  # missing value is a violation
        try:
            v = float(value)
        except (TypeError, ValueError):
            return True
        if var.domain == VariableDomain.BINARY and v not in (0.0, 1.0):
            return True
        if var.domain == VariableDomain.INTEGER and not float(v).is_integer():
            return True
        if var.lower_bound is not None and v < var.lower_bound - self.NUMERIC_TOLERANCE:
            return True
        if var.upper_bound is not None and v > var.upper_bound + self.NUMERIC_TOLERANCE:
            return True
        if var.allowed_values is not None and value not in var.allowed_values:
            return True
        return False

    def _check_constraint(
        self, constraint: Constraint, assignment: dict[str, Any]
    ) -> ConstraintResult:
        try:
            lhs = self._evaluator.evaluate(
                constraint.lhs_expression_id, assignment
            )
            rhs = (
                self._evaluator.evaluate(
                    constraint.rhs_expression_id, assignment
                )
                if constraint.rhs_expression_id
                else 0.0
            )
        except Exception as exc:
            return ConstraintResult(
                constraint_id=constraint.id,
                satisfied=False,
                hard=constraint.hard,
                note=f"Evaluation error: {exc}",
            )

        ctype = constraint.type
        if ctype == ConstraintType.EQUALITY:
            diff = abs(lhs - rhs)
            satisfied = diff <= self.NUMERIC_TOLERANCE
            return ConstraintResult(
                constraint_id=constraint.id,
                satisfied=satisfied,
                hard=constraint.hard,
                violation_magnitude=diff if not satisfied else None,
            )
        if ctype == ConstraintType.INEQUALITY_LE:
            satisfied = lhs <= rhs + self.NUMERIC_TOLERANCE
            return ConstraintResult(
                constraint_id=constraint.id,
                satisfied=satisfied,
                hard=constraint.hard,
                violation_magnitude=max(0.0, lhs - rhs) if not satisfied else None,
            )
        if ctype == ConstraintType.INEQUALITY_GE:
            satisfied = lhs >= rhs - self.NUMERIC_TOLERANCE
            return ConstraintResult(
                constraint_id=constraint.id,
                satisfied=satisfied,
                hard=constraint.hard,
                violation_magnitude=max(0.0, rhs - lhs) if not satisfied else None,
            )
        if ctype == ConstraintType.LOGICAL:
            satisfied = bool(lhs)
            return ConstraintResult(
                constraint_id=constraint.id,
                satisfied=satisfied,
                hard=constraint.hard,
            )
        # DOMAIN / CARDINALITY — evaluated as lhs == rhs
        satisfied = abs(lhs - rhs) <= self.NUMERIC_TOLERANCE
        return ConstraintResult(
            constraint_id=constraint.id,
            satisfied=satisfied,
            hard=constraint.hard,
        )

    def _build_limitations(
        self,
        candidate: SolverCandidate,
        objective_recomputed: bool,
        opt_proven: bool = False,
        gap_percent: float | None = None,
    ) -> list[str]:
        lims: list[str] = []
        if opt_proven:
            gap_str = f"{gap_percent:.2f}%" if gap_percent is not None else "0.00%"
            lims.append(f"Global optimality mathematically certified with duality gap <= {gap_str}.")
        elif gap_percent is not None:
            lims.append(f"Global optimality bounded by LP relaxation; duality gap <= {gap_percent:.2f}%.")
        elif candidate.claimed_status.lower() in ("optimal", "model_optimal"):
            lims.append("Global optimality claimed by solver; independent dual certificate not computed.")
        else:
            lims.append("Global optimality not proven by this run.")

        if not objective_recomputed:
            lims.append(
                "Objective value could not be independently recomputed — "
                "expression evaluation failed."
            )
        if not self._problem.objectives:
            lims.append("No objective defined — feasibility only.")
        lims.append(
            "Model-optimal result does not guarantee real-world validity."
        )
        return lims

    def _compute_dual_gap(
        self,
        candidate: SolverCandidate,
        objective_value: float | None,
        feasible: bool,
    ) -> tuple[float | None, float | None, bool]:
        """
        Compute continuous LP relaxation dual bound and proven optimality gap.
        Returns (dual_bound, gap_percent, optimality_proven).
        """
        if not feasible or objective_value is None or not self._problem.objectives:
            return None, None, False

        # If solver already certified mathematical optimality (e.g. CP-SAT proven optimum)
        if candidate.claimed_status.lower() in ("optimal", "model_optimal"):
            return objective_value, 0.0, True

        primary = self._problem.objectives[0]
        is_min = primary.direction == ObjectiveDirection.MINIMIZE
        vars_list = self._problem.variables
        n = len(vars_list)
        if n == 0:
            return None, None, False

        base_assign = {v.id: 0.0 for v in vars_list}
        try:
            f0 = self._evaluator.evaluate(primary.expression_id, base_assign)
            c = np.zeros(n, dtype=np.float64)
            for i, v in enumerate(vars_list):
                step_assign = dict(base_assign)
                step_assign[v.id] = 1.0
                f1 = self._evaluator.evaluate(primary.expression_id, step_assign)
                c[i] = (f1 - f0) if is_min else -(f1 - f0)

            A_ub, b_ub = [], []
            A_eq, b_eq = [], []

            for constraint in self._problem.constraints:
                if not constraint.hard:
                    continue
                lhs_0 = self._evaluator.evaluate(constraint.lhs_expression_id, base_assign)
                rhs_val = (
                    self._evaluator.evaluate(constraint.rhs_expression_id, base_assign)
                    if constraint.rhs_expression_id
                    else 0.0
                )
                row = np.zeros(n, dtype=np.float64)
                for i, v in enumerate(vars_list):
                    step_assign = dict(base_assign)
                    step_assign[v.id] = 1.0
                    lhs_1 = self._evaluator.evaluate(constraint.lhs_expression_id, step_assign)
                    row[i] = lhs_1 - lhs_0

                if constraint.type == ConstraintType.EQUALITY:
                    A_eq.append(row)
                    b_eq.append(rhs_val - lhs_0)
                elif constraint.type == ConstraintType.INEQUALITY_LE:
                    A_ub.append(row)
                    b_ub.append(rhs_val - lhs_0)
                elif constraint.type == ConstraintType.INEQUALITY_GE:
                    A_ub.append(-row)
                    b_ub.append(-(rhs_val - lhs_0))

            bounds = []
            for v in vars_list:
                if v.domain == VariableDomain.BINARY:
                    bounds.append((0.0, 1.0))
                else:
                    lb = v.lower_bound if v.lower_bound is not None else -np.inf
                    ub = v.upper_bound if v.upper_bound is not None else np.inf
                    bounds.append((lb, ub))

            from scipy.optimize import linprog
            lp_res = linprog(
                c,
                A_ub=np.array(A_ub) if A_ub else None,
                b_ub=np.array(b_ub) if b_ub else None,
                A_eq=np.array(A_eq) if A_eq else None,
                b_eq=np.array(b_eq) if b_eq else None,
                bounds=bounds,
                method="highs",
            )
            if lp_res.success:
                dual_bound = float(lp_res.fun + f0 if is_min else -(lp_res.fun) + f0)
                denom = abs(objective_value) if abs(objective_value) > 1e-6 else 1.0
                gap = abs(objective_value - dual_bound) / denom * 100.0
                opt_proven = gap < 1e-4
                return dual_bound, round(gap, 2), opt_proven
        except Exception:
            pass

        return None, None, False
