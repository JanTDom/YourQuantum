"""
YourQuantum — Cognitive IR Builder
Safe, deterministic construction of ProblemIR from cognitive specs without eval/exec.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from backend.domain.problem_ir import (
    ComputeBudget,
    Constraint,
    ConstraintType,
    ExprNode,
    ExpressionRegistry,
    Objective,
    ObjectiveDirection,
    ProblemIR,
    SolveMode,
    Variable,
    VariableDomain,
)


def build_problem_ir(
    raw_query: str,
    variables_spec: list[dict[str, Any]],
    objective_spec: dict[str, Any] | None,
    constraints_spec: list[dict[str, Any]],
    formalised_description: str = "",
    mode: SolveMode = SolveMode.OPTIMIZE,
    budget: ComputeBudget | None = None,
) -> ProblemIR:
    """
    Construct a validated, fully registered ProblemIR from structured specs.
    """
    reg = ExpressionRegistry()
    node_id_counter = 0

    def _next_node_id(prefix: str) -> str:
        nonlocal node_id_counter
        node_id_counter += 1
        return f"{prefix}_{node_id_counter}"

    # 1. Variables
    variables: list[Variable] = []
    for idx, v in enumerate(variables_spec):
        if isinstance(v, str):
            vid = v
            v_dict: dict[str, Any] = {"id": vid, "name": vid}
        elif isinstance(v, dict):
            v_dict = v
            vid = str(v.get("id") or v.get("name") or v.get("variable") or f"var_{idx+1}")
        else:
            continue

        domain_str = str(v_dict.get("domain", "binary")).lower()
        if domain_str == "binary":
            domain = VariableDomain.BINARY
            lb = 0.0
            ub = 1.0
        elif domain_str == "integer":
            domain = VariableDomain.INTEGER
            lb = float(v_dict.get("lower_bound", 0.0)) if v_dict.get("lower_bound") is not None else None
            ub = float(v_dict.get("upper_bound", 100.0)) if v_dict.get("upper_bound") is not None else None
        elif domain_str == "continuous":
            domain = VariableDomain.CONTINUOUS
            lb = float(v_dict.get("lower_bound", 0.0)) if v_dict.get("lower_bound") is not None else None
            ub = float(v_dict.get("upper_bound", 1000.0)) if v_dict.get("upper_bound") is not None else None
        else:
            domain = VariableDomain.BINARY
            lb, ub = 0.0, 1.0

        variables.append(
            Variable(
                id=vid,
                name=str(v_dict.get("name", vid)),
                domain=domain,
                lower_bound=lb,
                upper_bound=ub,
                unit=v_dict.get("unit"),
                description=v_dict.get("description"),
            )
        )
        # Register variable node
        reg.add(ExprNode(id=f"v_{vid}", op="var", value=vid))

    # Helper to build linear combinations
    def _build_linear_combination(terms: dict[str, float]) -> str:
        if not terms:
            nid = _next_node_id("const_zero")
            return reg.add(ExprNode(id=nid, op="const", value=0.0))

        prod_nodes: list[str] = []
        for vid, coeff in terms.items():
            cid = _next_node_id("coeff")
            reg.add(ExprNode(id=cid, op="const", value=float(coeff)))
            var_nid = f"v_{vid}"
            if var_nid not in reg.nodes:
                reg.add(ExprNode(id=var_nid, op="var", value=vid))
            mid = _next_node_id("mul")
            reg.add(ExprNode(id=mid, op="mul", children=[cid, var_nid]))
            prod_nodes.append(mid)

        if len(prod_nodes) == 1:
            return prod_nodes[0]
        sid = _next_node_id("sum")
        return reg.add(ExprNode(id=sid, op="sum", children=prod_nodes))

    # 2. Objective
    objectives: list[Objective] = []
    if objective_spec and variables:
        direction_str = str(objective_spec.get("direction", "maximize")).lower()
        direction = (
            ObjectiveDirection.MAXIMIZE
            if direction_str == "maximize"
            else ObjectiveDirection.MINIMIZE
        )
        coeffs = objective_spec.get("coefficients", {})
        obj_expr_id = _build_linear_combination(coeffs)
        objectives.append(
            Objective(
                id="obj_primary",
                direction=direction,
                expression_id=obj_expr_id,
                priority=1,
                description=objective_spec.get("description", "Primary objective function"),
            )
        )

    # 3. Constraints
    constraints: list[Constraint] = []
    for idx, c in enumerate(constraints_spec):
        cid = c.get("id") or f"c_{idx + 1}"
        ctype_str = str(c.get("type", "inequality_le")).lower()
        if ctype_str in ("inequality_le", "<=", "le"):
            ctype = ConstraintType.INEQUALITY_LE
        elif ctype_str in ("inequality_ge", ">=", "ge"):
            ctype = ConstraintType.INEQUALITY_GE
        elif ctype_str in ("equality", "==", "eq"):
            ctype = ConstraintType.EQUALITY
        else:
            ctype = ConstraintType.INEQUALITY_LE

        terms = c.get("lhs_terms", {})
        lhs_id = _build_linear_combination(terms)

        rhs_val = float(c.get("rhs", 0.0))
        rhs_id = _next_node_id("rhs")
        reg.add(ExprNode(id=rhs_id, op="const", value=rhs_val))

        hard = bool(c.get("hard", True))
        penalty = float(c.get("penalty_weight", 100.0)) if not hard else None

        constraints.append(
            Constraint(
                id=cid,
                type=ctype,
                lhs_expression_id=lhs_id,
                rhs_expression_id=rhs_id,
                hard=hard,
                penalty_weight=penalty,
                description=c.get("description", f"Constraint {cid}"),
            )
        )

    return ProblemIR(
        description_raw=raw_query,
        description_formalised=formalised_description or f"Cognitive Problem Formulation ({len(variables)} vars, {len(constraints)} constraints)",
        mode=mode,
        variables=variables,
        expressions=reg,
        objectives=objectives,
        constraints=constraints,
        budget=budget or ComputeBudget(),
        approved=False,
        approved_at=None,
    )
