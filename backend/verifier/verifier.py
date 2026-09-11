"""
YourQuantum — Independent Verifier
Reads only ProblemIR + candidate. Never reads solver internals.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any

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
            hard_violations.append(
                ConstraintResult(
                    constraint_id="__objective_check__",
                    satisfied=False,
                    hard=True,
                    note=(
                        f"Objective mismatch: solver claimed "
                        f"{candidate.claimed_objective}, "
                        f"verifier computed {objective_value}"
                    ),
                )
            )
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

        # 8. Honest limitations
        limitations = self._build_limitations(candidate, objective_recomputed)

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
        self, candidate: SolverCandidate, objective_recomputed: bool
    ) -> list[str]:
        lims: list[str] = []
        if candidate.claimed_status not in ("optimal",):
            lims.append(
                "Global optimality not proven — solver did not certify optimality."
            )
        else:
            lims.append(
                "Global optimality claimed by solver; no independent certificate validated."
            )
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
