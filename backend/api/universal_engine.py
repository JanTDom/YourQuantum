"""
YourQuantum — Universal Multi-Domain Compute Engine
Transforms generic, multi-purpose business, engineering, and financial optimization
requests into mathematically rigorous ProblemIR, runs quantum or classical solvers,
and produces cryptographically stamped, independently verified results.
"""

from __future__ import annotations

import hmac
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from backend.domain.problem_ir import (
    ComputeBudget,
    Constraint,
    ConstraintType,
    ExprNode,
    ExpressionRegistry,
    Objective,
    ObjectiveDirection,
    ProblemIR,
    Variable,
    VariableDomain,
)
from backend.domain.sensitivity import RobustnessReport, SensitivityEngine
from backend.solvers.base import ExecutionStatus, MathStatus, SolverResult
from backend.solvers.cpsat import CPSATAdapter
from backend.solvers.hybrid_benders import HybridBendersAdapter
from backend.solvers.quantum.qaoa import QAOAAdapter
from backend.verifier.verifier import IndependentVerifier, SolverCandidate, Verdict, VerificationReport

# Secret master password / key for universal API access
MASTER_API_SECRET = os.getenv("YQ_MASTER_API_SECRET", "A132a132!").strip()


def verify_master_secret(key_or_password: str) -> bool:
    """Constant-time verification of master access password or derived API key."""
    if not key_or_password:
        return False
    candidate = key_or_password.strip()
    # Accept direct password or Bearer yq_...
    if candidate.startswith("Bearer "):
        candidate = candidate[len("Bearer ") :].strip()
    if candidate.startswith("yq_live_master_"):
        # Match against hash of secret
        import hashlib
        expected_token = "yq_live_master_" + hashlib.sha256(MASTER_API_SECRET.encode()).hexdigest()[:24]
        return hmac.compare_digest(candidate, expected_token)
    return hmac.compare_digest(candidate, MASTER_API_SECRET)


class VariableDef(BaseModel):
    id: str
    name: str
    cost: Optional[float] = None
    value: Optional[float] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ConstraintDef(BaseModel):
    id: str = Field(default_factory=lambda: f"c_{uuid.uuid4().hex[:6]}")
    name: Optional[str] = None
    type: Literal[
        "budget",
        "cardinality_exact",
        "cardinality_max",
        "cardinality_min",
        "incompatible",
        "dependency",
        "linear",
    ]
    attribute: Optional[str] = None
    limit: Optional[float] = None
    count: Optional[int] = None
    var_ids: List[str] = Field(default_factory=list)
    linear_lhs: Dict[str, float] = Field(default_factory=dict)
    linear_op: Literal["<=", ">=", "=="] = "<="
    linear_rhs: float = 0.0


class UniversalComputeRequest(BaseModel):
    domain: str = "general"
    title: str = "Uniwersalne Zadanie Optymalizacyjne"
    variables: List[VariableDef] = Field(min_length=1)
    objective_direction: Literal["maximize", "minimize"] = "maximize"
    objective_attribute: Optional[str] = "value"
    objective_coefficients: Dict[str, float] = Field(default_factory=dict)
    constraints: List[ConstraintDef] = Field(default_factory=list)
    solver: Literal["auto", "hybrid_benders", "qaoa", "cpsat"] = "auto"
    include_stress_test: bool = True


class UniversalComputeResponse(BaseModel):
    status: Literal["SUCCESS", "INFEASIBLE", "ERROR"]
    title: str
    domain: str
    solver_used: str
    compute_time_ms: float
    optimal_assignment: Dict[str, int]
    optimal_selection: List[Dict[str, Any]]
    total_objective_value: float
    dual_bound: Optional[float] = None
    optimality_gap_percent: Optional[float] = None
    optimality_proven: bool = False
    sha256_passport: str
    verification: Dict[str, Any]
    sensitivity_report: Optional[Dict[str, Any]] = None


class UniversalEngine:
    """Compiles and executes universal, multi-domain optimization dilemmas."""

    def compile_to_ir(self, req: UniversalComputeRequest) -> ProblemIR:
        reg = ExpressionRegistry()
        variables: List[Variable] = []
        node_counter = 0

        def _const(val: float) -> str:
            nonlocal node_counter
            nid = f"c_{node_counter}"
            node_counter += 1
            reg.add(ExprNode(id=nid, op="const", value=val))
            return nid

        def _var(vid: str) -> str:
            nid = f"v_{vid}"
            if nid not in reg.nodes:
                reg.add(ExprNode(id=nid, op="var", value=vid))
            return nid

        def _mul(cid: str, vid: str) -> str:
            nonlocal node_counter
            nid = f"m_{node_counter}"
            node_counter += 1
            reg.add(ExprNode(id=nid, op="mul", children=[cid, vid]))
            return nid

        def _sum(cids: List[str]) -> str:
            nonlocal node_counter
            nid = f"s_{node_counter}"
            node_counter += 1
            reg.add(ExprNode(id=nid, op="sum", children=cids))
            return nid

        # 1. Variables
        for v in req.variables:
            variables.append(Variable(id=v.id, name=v.name, domain=VariableDomain.BINARY))

        # 2. Objective
        obj_term_ids: List[str] = []
        is_max = req.objective_direction == "maximize"

        for v in req.variables:
            coeff = 0.0
            if v.id in req.objective_coefficients:
                coeff = req.objective_coefficients[v.id]
            elif req.objective_attribute and req.objective_attribute in v.attributes:
                coeff = float(v.attributes[req.objective_attribute])
            elif req.objective_attribute == "value" and v.value is not None:
                coeff = float(v.value)
            elif req.objective_attribute == "cost" and v.cost is not None:
                coeff = float(v.cost)
            else:
                coeff = 1.0

            # For maximization, ProblemIR minimizes -coeff
            effective_coeff = -coeff if is_max else coeff
            cid = _const(effective_coeff)
            vid = _var(v.id)
            obj_term_ids.append(_mul(cid, vid))

        obj_expr_id = _sum(obj_term_ids) if obj_term_ids else _const(0.0)
        objectives = [
            Objective(
                id="universal_objective",
                direction=ObjectiveDirection.MINIMIZE,
                expression_id=obj_expr_id,
            )
        ]

        # 3. Constraints
        constraints: List[Constraint] = []
        for c in req.constraints:
            if c.type == "budget":
                # sum(attr_i * x_i) <= limit
                limit_val = c.limit or 0.0
                attr_name = c.attribute or "cost"
                terms = []
                for v in req.variables:
                    val = 0.0
                    if attr_name in v.attributes:
                        val = float(v.attributes[attr_name])
                    elif attr_name == "cost" and v.cost is not None:
                        val = float(v.cost)
                    elif attr_name == "value" and v.value is not None:
                        val = float(v.value)
                    if val != 0.0:
                        terms.append(_mul(_const(val), _var(v.id)))

                lhs = _sum(terms) if terms else _const(0.0)
                rhs = _const(limit_val)
                constraints.append(
                    Constraint(
                        id=c.id,
                        type=ConstraintType.INEQUALITY_LE,
                        lhs_expression_id=lhs,
                        rhs_expression_id=rhs,
                        hard=True,
                        description=c.name or f"Limit budżetowy {attr_name} <= {limit_val}",
                    )
                )

            elif c.type in ("cardinality_exact", "cardinality_max", "cardinality_min"):
                target_count = float(c.count or 1)
                terms = [_var(v.id) for v in req.variables]
                lhs = _sum(terms) if terms else _const(0.0)
                rhs = _const(target_count)
                ctype = (
                    ConstraintType.EQUALITY
                    if c.type == "cardinality_exact"
                    else (
                        ConstraintType.INEQUALITY_LE
                        if c.type == "cardinality_max"
                        else ConstraintType.INEQUALITY_GE
                    )
                )
                constraints.append(
                    Constraint(
                        id=c.id,
                        type=ctype,
                        lhs_expression_id=lhs,
                        rhs_expression_id=rhs,
                        hard=True,
                        description=c.name or f"Wybór {c.type} {target_count}",
                    )
                )

            elif c.type == "incompatible":
                # x_a + x_b <= 1
                if len(c.var_ids) >= 2:
                    terms = [_var(vid) for vid in c.var_ids]
                    lhs = _sum(terms)
                    rhs = _const(1.0)
                    constraints.append(
                        Constraint(
                            id=c.id,
                            type=ConstraintType.INEQUALITY_LE,
                            lhs_expression_id=lhs,
                            rhs_expression_id=rhs,
                            hard=True,
                            description=c.name or f"Wykluczenie wzajemne {c.var_ids}",
                        )
                    )

            elif c.type == "dependency":
                # x_b <= x_a (x_b requires x_a) -> x_b - x_a <= 0
                if len(c.var_ids) == 2:
                    req_var, dep_var = c.var_ids[0], c.var_ids[1]
                    m_neg = _mul(_const(-1.0), _var(req_var))
                    lhs = _sum([_var(dep_var), m_neg])
                    rhs = _const(0.0)
                    constraints.append(
                        Constraint(
                            id=c.id,
                            type=ConstraintType.INEQUALITY_LE,
                            lhs_expression_id=lhs,
                            rhs_expression_id=rhs,
                            hard=True,
                            description=c.name or f"{dep_var} wymaga {req_var}",
                        )
                    )

            elif c.type == "linear":
                terms = []
                for vid, coeff in c.linear_lhs.items():
                    terms.append(_mul(_const(coeff), _var(vid)))
                lhs = _sum(terms) if terms else _const(0.0)
                rhs = _const(c.linear_rhs)
                ctype = (
                    ConstraintType.INEQUALITY_LE
                    if c.linear_op == "<="
                    else (
                        ConstraintType.INEQUALITY_GE
                        if c.linear_op == ">="
                        else ConstraintType.EQUALITY
                    )
                )
                constraints.append(
                    Constraint(
                        id=c.id,
                        type=ctype,
                        lhs_expression_id=lhs,
                        rhs_expression_id=rhs,
                        hard=True,
                        description=c.name or "Liniowe ograniczenie",
                    )
                )

        return ProblemIR(
            description_raw=req.title,
            description_formalised=f"Universal {req.domain} optimization: {len(variables)} variables, {len(constraints)} constraints",
            variables=variables,
            expressions=reg,
            objectives=objectives,
            constraints=constraints,
            approved=True,
            approved_at=datetime.now(timezone.utc),
        )

    def execute(self, req: UniversalComputeRequest) -> UniversalComputeResponse:
        start_time = time.perf_counter()
        ir = self.compile_to_ir(req)

        # Solver selection
        solver_choice = req.solver
        if solver_choice == "auto":
            if len(req.variables) <= 12:
                solver_choice = "hybrid_benders"
            else:
                solver_choice = "cpsat"

        if solver_choice == "qaoa":
            adapter = QAOAAdapter()
        elif solver_choice == "hybrid_benders":
            adapter = HybridBendersAdapter()
        else:
            adapter = CPSATAdapter()

        budget = ComputeBudget(wall_time_seconds=10.0)
        solver_res: SolverResult = adapter.solve(ir, budget)

        if solver_res.execution_status != ExecutionStatus.COMPLETED or solver_res.math_status not in (
            MathStatus.OPTIMAL,
            MathStatus.FEASIBLE,
        ):
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return UniversalComputeResponse(
                status="INFEASIBLE",
                title=req.title,
                domain=req.domain,
                solver_used=adapter.name,
                compute_time_ms=round(elapsed_ms, 2),
                optimal_assignment={},
                optimal_selection=[],
                total_objective_value=0.0,
                sha256_passport="",
                verification={"feasible": False, "verdict": "FAIL", "residual": 1.0},
            )

        # Independent Verification
        verifier = IndependentVerifier(ir)
        cand = SolverCandidate(
            candidate_id=solver_res.candidate_id,
            assignment=solver_res.assignment,
            claimed_objective=solver_res.objective_value,
            claimed_status="optimal" if solver_res.math_status == MathStatus.OPTIMAL else "feasible",
        )
        report: VerificationReport = verifier.verify(cand)

        # Real objective value (inverted if was maximized)
        computed_obj = report.objective_value or 0.0
        final_value = -computed_obj if req.objective_direction == "maximize" else computed_obj

        # Optimal selection of items
        var_dict = {v.id: v for v in req.variables}
        selected_items = []
        assignment_clean: Dict[str, int] = {}

        for vid, assigned_val in solver_res.assignment.items():
            if assigned_val == 1 and vid in var_dict:
                v = var_dict[vid]
                selected_items.append({
                    "id": v.id,
                    "name": v.name,
                    "cost": v.cost,
                    "value": v.value,
                    "attributes": v.attributes,
                })
            if vid in var_dict:
                assignment_clean[vid] = int(assigned_val)

        # Sensitivity Stress-Testing
        sens_data = None
        if req.include_stress_test:
            engine = SensitivityEngine(ir)
            rob_report: RobustnessReport = engine.analyze(
                cand.candidate_id, cand.assignment, report.objective_value
            )
            sens_data = {
                "robustness_score": rob_report.robustness_score,
                "verdict": rob_report.verdict,
                "summary_pl": rob_report.summary_pl,
            }

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return UniversalComputeResponse(
            status="SUCCESS",
            title=req.title,
            domain=req.domain,
            solver_used=adapter.name,
            compute_time_ms=round(elapsed_ms, 2),
            optimal_assignment=assignment_clean,
            optimal_selection=selected_items,
            total_objective_value=round(final_value, 4),
            dual_bound=report.dual_bound,
            optimality_gap_percent=report.optimality_gap_percent,
            optimality_proven=report.optimality_proven,
            sha256_passport=report.sha256_hash,
            verification={
                "feasible": report.feasible,
                "verdict": report.verdict.value,
                "residual": report.numerical_residual or 0.0,
            },
            sensitivity_report=sens_data,
        )
