"""
YourQuantum — Cognitive Constraint Sanity Checker
Pre-solver validation evaluating domain consistency and bounds contradictions
to trigger early active inference prediction errors without executing expensive solvers.
"""
from __future__ import annotations

import logging
from typing import Any
from pydantic import BaseModel, Field

from backend.domain.problem_ir import (
    ConstraintType,
    ExprNode,
    ProblemIR,
    SolveMode,
    Variable,
    VariableDomain,
)
from backend.domain.evaluator import ExpressionEvaluator

logger = logging.getLogger(__name__)


class SanityCheckResult(BaseModel):
    """Outcome of pre-solver constraint and domain sanity evaluation."""
    passed: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def check_constraints_sanity(problem: ProblemIR) -> SanityCheckResult:
    """
    Perform deep static consistency and domain checks on a candidate ProblemIR.
    Detects impossible constraints, inverted domains, and conflicting single-variable bounds.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Structural checks
    if not problem.variables:
        errors.append("Problem defines zero decision variables.")
        return SanityCheckResult(passed=False, errors=errors, warnings=warnings)

    if problem.mode == SolveMode.OPTIMIZE and not problem.objectives:
        errors.append("Problem is set to OPTIMIZE mode but defines no objective function.")

    # 2. Variable bounds consistency
    var_bounds: dict[str, dict[str, float]] = {}
    for var in problem.variables:
        min_val = var.lower_bound
        max_val = var.upper_bound

        if var.domain == VariableDomain.BINARY:
            # Binary variables have implicit bounds [0, 1]
            if min_val is None:
                min_val = 0.0
            if max_val is None:
                max_val = 1.0
            if min_val > 1.0 or max_val < 0.0:
                errors.append(
                    f"Binary variable '{var.id}' has domain conflicting bounds [{min_val}, {max_val}]."
                )

        if min_val is not None and max_val is not None:
            if min_val > max_val:
                errors.append(
                    f"Variable '{var.id}' has inverted bounds: lower_bound ({min_val}) > upper_bound ({max_val})."
                )

        var_bounds[var.id] = {
            "lower": min_val if min_val is not None else float("-inf"),
            "upper": max_val if max_val is not None else float("inf"),
        }

    # 3. Constraint analysis
    evaluator = ExpressionEvaluator(problem.expressions)
    reg_nodes = problem.expressions.nodes

    for c in problem.constraints:
        lhs_node = reg_nodes.get(c.lhs_expression_id)
        rhs_node = reg_nodes.get(c.rhs_expression_id) if c.rhs_expression_id else None

        if lhs_node is None:
            errors.append(f"Constraint '{c.id}' references missing lhs_expression_id '{c.lhs_expression_id}'.")
            continue

        # Check pure constant vs constant contradictions (e.g. 5 <= 2)
        if lhs_node.op == "const" and rhs_node is not None and rhs_node.op == "const":
            lhs_val = float(lhs_node.value) if lhs_node.value is not None else 0.0
            rhs_val = float(rhs_node.value) if rhs_node.value is not None else 0.0
            if c.type == ConstraintType.INEQUALITY_LE and lhs_val > rhs_val:
                errors.append(
                    f"Constraint '{c.id}' is an impossible constant contradiction: {lhs_val} <= {rhs_val}."
                )
            elif c.type == ConstraintType.INEQUALITY_GE and lhs_val < rhs_val:
                errors.append(
                    f"Constraint '{c.id}' is an impossible constant contradiction: {lhs_val} >= {rhs_val}."
                )
            elif c.type == ConstraintType.EQUALITY and abs(lhs_val - rhs_val) > 1e-9:
                errors.append(
                    f"Constraint '{c.id}' is an impossible constant contradiction: {lhs_val} == {rhs_val}."
                )

        # Check single variable bounds induced by constraint, e.g. x <= 5, x >= 10
        single_var_id, coeff = _extract_single_var_and_coeff(lhs_node, reg_nodes)
        if single_var_id is not None and coeff != 0 and rhs_node is not None and rhs_node.op == "const":
            rhs_val = float(rhs_node.value) if rhs_node.value is not None else 0.0
            normalized_bound = rhs_val / coeff

            if c.type == ConstraintType.INEQUALITY_LE:
                effective_upper = normalized_bound if coeff > 0 else float("inf")
                effective_lower = normalized_bound if coeff < 0 else float("-inf")
            elif c.type == ConstraintType.INEQUALITY_GE:
                effective_lower = normalized_bound if coeff > 0 else float("-inf")
                effective_upper = normalized_bound if coeff < 0 else float("inf")
            elif c.type == ConstraintType.EQUALITY:
                effective_lower = normalized_bound
                effective_upper = normalized_bound
            else:
                effective_lower = float("-inf")
                effective_upper = float("inf")

            cur = var_bounds.get(single_var_id, {"lower": float("-inf"), "upper": float("inf")})
            new_lower = max(cur["lower"], effective_lower)
            new_upper = min(cur["upper"], effective_upper)

            if new_lower > new_upper:
                errors.append(
                    f"Contradictory bounds detected for variable '{single_var_id}': "
                    f"requires lower bound >= {new_lower} while upper bound <= {new_upper} (constraint '{c.id}')."
                )
            else:
                var_bounds[single_var_id] = {"lower": new_lower, "upper": new_upper}

    passed = len(errors) == 0
    return SanityCheckResult(passed=passed, errors=errors, warnings=warnings)


def _extract_single_var_and_coeff(
    node: ExprNode,
    nodes: dict[str, ExprNode],
) -> tuple[str | None, float]:
    """
    Inspect node to see if it represents a single variable or scalar product c * x.
    """
    if node.op == "var" and isinstance(node.value, str):
        return node.value, 1.0

    if node.op == "mul" and len(node.children) == 2:
        c1 = nodes.get(node.children[0])
        c2 = nodes.get(node.children[1])
        if c1 and c2:
            if c1.op == "const" and c2.op == "var" and isinstance(c2.value, str):
                return c2.value, float(c1.value) if c1.value is not None else 1.0
            if c2.op == "const" and c1.op == "var" and isinstance(c1.value, str):
                return c1.value, float(c2.value) if c2.value is not None else 1.0

    return None, 0.0
