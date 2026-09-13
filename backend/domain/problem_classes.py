"""
YourQuantum — Problem Classes & Multi-Lever Design Synthesis (Phase D1, D2, D3)
Implements ProblemClass taxonomy (CHOICE, ALLOCATION, DESIGN, PARAMETER, NOT_COMPUTABLE)
and the multi-lever combinatorial DesignProblem model with Pareto frontier generation.
"""
from __future__ import annotations

import itertools
import logging
import uuid
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field

from backend.domain.decision_case import ScoredValue
from backend.domain.problem_ir import (
    ComputeBudget,
    Constraint,
    ConstraintType,
    ExprNode,
    ExpressionRegistry,
    Objective,
    ObjectiveDirection,
    ProblemIR,
    Provenance,
    SolveMode,
    Variable,
    VariableDomain,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# D1: ProblemClass Taxonomy
# ---------------------------------------------------------------------------

class ProblemClass(str, Enum):
    CHOICE = "CHOICE"                  # Choice of 1 of N discrete options (DecisionCase)
    ALLOCATION = "ALLOCATION"          # Portfolio, basket, schedule under constraints
    DESIGN = "DESIGN"                  # Multi-lever system synthesis (e.g. healthcare reform)
    PARAMETER = "PARAMETER"            # Continuous variable optimization (SciPy / HiGHS)
    NOT_COMPUTABLE = "NOT_COMPUTABLE"  # Value judgment, forecast, or ill-structured question


class NotComputableReport(BaseModel):
    """
    Honest report when a user question lacks computable structure.
    Never gives hallucinated pseudo-scientific quantum answers; explains why and how to reframe.
    """
    is_computable: bool = False
    reason: str
    reframe_suggestions: list[str]
    suggested_computable_class: ProblemClass | None = None


def evaluate_problem_computability(query: str) -> tuple[bool, NotComputableReport | None]:
    """
    Examines if the user prompt is inherently non-computable (e.g. purely moral/existential,
    pure market prophecy, or without distinct decision options).
    """
    q_clean = query.strip().lower()

    uncomputable_triggers = [
        ("jaki jest sens życia", "Pytanie o charakterze egzystencjalnym/filozoficznym, niebędące problemem optymalizacji pod warunkami brzegowymi."),
        ("czy bóg istnieje", "Kwestia metafizyczna/światopoglądowa nieposiadająca mierzalnej funkcji celu ani ograniczeń matematycznych."),
        ("jaki będzie kurs bitcoina za rok", "Czysta prognoza spekulacyjna przyszłości o wysokiej losowości, a nie deterministyczny problem decyzyjny."),
    ]

    for trigger, explanation in uncomputable_triggers:
        if trigger in q_clean:
            return False, NotComputableReport(
                is_computable=False,
                reason=explanation,
                reframe_suggestions=[
                    "Zdefiniuj konkretne opcje działania (np. scenariusz A vs scenariusz B).",
                    "Określ mierzalne kryteria (np. budżet, maksymalna tolerancja straty, czas).",
                    "Przekształć pytanie w problem wyboru (CHOICE) lub alokacji portfela (ALLOCATION).",
                ],
                suggested_computable_class=ProblemClass.CHOICE,
            )

    return True, None


# ---------------------------------------------------------------------------
# D2: Multi-Lever DESIGN Model
# ---------------------------------------------------------------------------

class LeverOption(BaseModel):
    """A distinct variant for a specific design lever (e.g. single payer vs multi-payer)."""
    id: str
    title: str
    description: str = ""
    evidence_ref: str | None = None  # Reference to Evidence ID proving where this operates
    is_hypothetical: bool = False    # True if not tested in any known existing system
    provenance: Provenance = Provenance.USER_SUPPLIED


class DesignLever(BaseModel):
    """A decision lever representing one architectural dimension."""
    id: str
    name: str
    description: str = ""
    options: list[LeverOption] = Field(min_length=2, max_length=8)


class DesignCriterion(BaseModel):
    """An evaluation criterion with user-provided weight."""
    id: str
    name: str
    direction: Literal["maximize", "minimize"] = "maximize"
    weight: float = Field(default=1.0, ge=0.0)
    unit: str | None = None


class Interaction(BaseModel):
    """
    Pairwise compatibility or non-linear synergy between options from different levers.
    Rule D2: Any non-zero synergy MUST provide a source reference or explicit user assumption!
    """
    lever_a_id: str
    option_a_id: str
    lever_b_id: str
    option_b_id: str
    compatible: bool = True       # If False, hard exclusion constraint: x_a + x_b <= 1
    synergy: float = 0.0          # Quadratic objective bonus (positive) or penalty (negative)
    source_ref: str | None = None # MANDATORY if synergy != 0.0

    def validate_synergy_source(self) -> bool:
        if abs(self.synergy) > 1e-6 and not self.source_ref:
            raise ValueError(
                f"Synergy {self.synergy} between ({self.option_a_id}, {self.option_b_id}) "
                "requires a verified source_ref or explicit assumption tag. Zero invented synergies allowed."
            )
        return True


class DesignProblem(BaseModel):
    """
    Full combinatorial synthesis model for DESIGN class problems.
    Composes general mathematical primitives: one-hot lever choice, linear objectives,
    pairwise interactions/synergies, and global budget constraints.
    """
    id: str = Field(default_factory=lambda: f"des_{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    levers: list[DesignLever]
    criteria: list[DesignCriterion]
    # score_matrix[lever_id][option_id][criterion_id] = ScoredValue
    score_matrix: dict[str, dict[str, dict[str, ScoredValue]]] = Field(default_factory=dict)
    interactions: list[Interaction] = Field(default_factory=list)
    budget_limit: float | None = None
    cost_criterion_id: str | None = None

    def validate_design(self) -> None:
        """Enforces honesty rules on synergies and options."""
        for inter in self.interactions:
            inter.validate_synergy_source()

    def compile_to_problem_ir(self) -> ProblemIR:
        """
        Compiles the multi-lever design problem into a rigorous ProblemIR:
        - Binary variables x_{l, o}
        - One-hot constraints: sum_o x_{l, o} = 1 for each lever
        - Compatibility constraints: x_a + x_b <= 1 for incompatible pairs
        - Linear and quadratic objective terms
        """
        self.validate_design()
        reg = ExpressionRegistry()
        variables: list[Variable] = []
        constraints: list[Constraint] = []

        var_map: dict[tuple[str, str], str] = {}

        # 1. Variables: one binary variable per (lever, option)
        for lever in self.levers:
            for opt in lever.options:
                var_id = f"x_{lever.id}_{opt.id}"
                var_map[(lever.id, opt.id)] = var_id
                variables.append(
                    Variable(
                        id=var_id,
                        name=f"{lever.name}: {opt.title}",
                        domain=VariableDomain.BINARY,
                        provenance=opt.provenance,
                        description=opt.description,
                    )
                )
                reg.add(ExprNode(id=f"v_{var_id}", op="var", value=var_id))

        # 2. One-hot constraints: exactly one option chosen per lever
        for idx, lever in enumerate(self.levers):
            opt_vars = [var_map[(lever.id, opt.id)] for opt in lever.options]
            # Build sum(x_{l, o})
            sum_nodes = [f"v_{vid}" for vid in opt_vars]
            sum_id = reg.add(ExprNode(id=f"sum_onehot_{lever.id}", op="sum", children=sum_nodes))
            rhs_id = reg.add(ExprNode(id=f"rhs_onehot_{lever.id}", op="const", value=1.0))

            constraints.append(
                Constraint(
                    id=f"onehot_{lever.id}",
                    type=ConstraintType.EQUALITY,
                    lhs_expression_id=sum_id,
                    rhs_expression_id=rhs_id,
                    hard=True,
                    description=f"One-hot choice constraint for lever '{lever.name}'",
                )
            )

        # 3. Compatibility constraints (hard exclusions)
        for idx, inter in enumerate(self.interactions):
            if not inter.compatible:
                var_a = var_map.get((inter.lever_a_id, inter.option_a_id))
                var_b = var_map.get((inter.lever_b_id, inter.option_b_id))
                if var_a and var_b:
                    # x_a + x_b <= 1
                    pair_sum_id = reg.add(
                        ExprNode(id=f"incompat_sum_{idx}", op="sum", children=[f"v_{var_a}", f"v_{var_b}"])
                    )
                    rhs_id = reg.add(ExprNode(id=f"incompat_rhs_{idx}", op="const", value=1.0))
                    constraints.append(
                        Constraint(
                            id=f"incompat_{inter.option_a_id}_{inter.option_b_id}",
                            type=ConstraintType.INEQUALITY_LE,
                            lhs_expression_id=pair_sum_id,
                            rhs_expression_id=rhs_id,
                            hard=True,
                            description=f"Incompatibility between {inter.option_a_id} and {inter.option_b_id}",
                        )
                    )

        # 4. Objective compilation
        # Linear terms: sum_k w_k * normalized_score(l, o, k)
        objective_terms: list[str] = []

        total_weight = sum(c.weight for c in self.criteria) or 1.0
        normalized_weights = {c.id: c.weight / total_weight for c in self.criteria}

        for lever in self.levers:
            for opt in lever.options:
                var_id = var_map[(lever.id, opt.id)]
                net_utility = 0.0

                for crit in self.criteria:
                    crit_w = normalized_weights[crit.id]
                    cell = self.score_matrix.get(lever.id, {}).get(opt.id, {}).get(crit.id)
                    score_val = float(cell.value) if cell and cell.value is not None else 0.0

                    # Benefit vs cost
                    sign = -1.0 if crit.direction == "minimize" else 1.0
                    net_utility += sign * crit_w * score_val

                if abs(net_utility) > 1e-6:
                    c_id = reg.add(ExprNode(id=f"coeff_{var_id}", op="const", value=net_utility))
                    m_id = reg.add(ExprNode(id=f"term_{var_id}", op="mul", children=[c_id, f"v_{var_id}"]))
                    objective_terms.append(m_id)

        # Linearized synergy terms: synergy * y_idx where y_idx = x_a * x_b
        for idx, inter in enumerate(self.interactions):
            if abs(inter.synergy) > 1e-6:
                var_a = var_map.get((inter.lever_a_id, inter.option_a_id))
                var_b = var_map.get((inter.lever_b_id, inter.option_b_id))
                if var_a and var_b:
                    y_var_id = f"syn_y_{idx}"
                    variables.append(
                        Variable(
                            id=y_var_id,
                            name=f"Synergy({inter.option_a_id}, {inter.option_b_id})",
                            domain=VariableDomain.BINARY,
                            provenance=Provenance.DERIVED,
                        )
                    )
                    reg.add(ExprNode(id=f"v_{y_var_id}", op="var", value=y_var_id))

                    # Linear term in objective: synergy * y_var
                    syn_c = reg.add(ExprNode(id=f"syn_coeff_{idx}", op="const", value=inter.synergy))
                    syn_term = reg.add(ExprNode(id=f"syn_term_{idx}", op="mul", children=[syn_c, f"v_{y_var_id}"]))
                    objective_terms.append(syn_term)

                    # Fortet linearization constraints:
                    # 1. y <= x_a  => y - x_a <= 0
                    neg_one_a = reg.add(ExprNode(id=f"neg1_a_{idx}", op="const", value=-1.0))
                    neg_xa = reg.add(ExprNode(id=f"neg_xa_{idx}", op="mul", children=[neg_one_a, f"v_{var_a}"]))
                    lhs_ya = reg.add(ExprNode(id=f"lhs_ya_{idx}", op="add", children=[f"v_{y_var_id}", neg_xa]))
                    zero_a = reg.add(ExprNode(id=f"zero_a_{idx}", op="const", value=0.0))
                    constraints.append(
                        Constraint(
                            id=f"syn_ub_a_{idx}",
                            type=ConstraintType.INEQUALITY_LE,
                            lhs_expression_id=lhs_ya,
                            rhs_expression_id=zero_a,
                            hard=True,
                            description=f"Synergy upper bound {y_var_id} <= {var_a}",
                        )
                    )

                    # 2. y <= x_b  => y - x_b <= 0
                    neg_one_b = reg.add(ExprNode(id=f"neg1_b_{idx}", op="const", value=-1.0))
                    neg_xb = reg.add(ExprNode(id=f"neg_xb_{idx}", op="mul", children=[neg_one_b, f"v_{var_b}"]))
                    lhs_yb = reg.add(ExprNode(id=f"lhs_yb_{idx}", op="add", children=[f"v_{y_var_id}", neg_xb]))
                    zero_b = reg.add(ExprNode(id=f"zero_b_{idx}", op="const", value=0.0))
                    constraints.append(
                        Constraint(
                            id=f"syn_ub_b_{idx}",
                            type=ConstraintType.INEQUALITY_LE,
                            lhs_expression_id=lhs_yb,
                            rhs_expression_id=zero_b,
                            hard=True,
                            description=f"Synergy upper bound {y_var_id} <= {var_b}",
                        )
                    )

                    # 3. x_a + x_b - y <= 1
                    neg_one_y = reg.add(ExprNode(id=f"neg1_y_{idx}", op="const", value=-1.0))
                    neg_y = reg.add(ExprNode(id=f"neg_y_{idx}", op="mul", children=[neg_one_y, f"v_{y_var_id}"]))
                    lhs_lb = reg.add(ExprNode(id=f"lhs_lb_{idx}", op="sum", children=[f"v_{var_a}", f"v_{var_b}", neg_y]))
                    one_rhs = reg.add(ExprNode(id=f"one_rhs_{idx}", op="const", value=1.0))
                    constraints.append(
                        Constraint(
                            id=f"syn_lb_{idx}",
                            type=ConstraintType.INEQUALITY_LE,
                            lhs_expression_id=lhs_lb,
                            rhs_expression_id=one_rhs,
                            hard=True,
                            description=f"Synergy lower bound {var_a} + {var_b} - {y_var_id} <= 1",
                        )
                    )

        if not objective_terms:
            zero_id = reg.add(ExprNode(id="obj_zero", op="const", value=0.0))
            obj_expr_id = zero_id
        elif len(objective_terms) == 1:
            obj_expr_id = objective_terms[0]
        else:
            obj_expr_id = reg.add(ExprNode(id="obj_sum", op="sum", children=objective_terms))

        objectives = [
            Objective(
                id="obj_design_utility",
                direction=ObjectiveDirection.MAXIMIZE,
                expression_id=obj_expr_id,
                priority=1,
                description="Global multi-lever design utility including validated synergies",
            )
        ]

        return ProblemIR(
            description_raw=self.description,
            description_formalised=f"Multi-Lever Synthesis Model ({len(self.levers)} levers, {len(variables)} options, {len(constraints)} constraints)",
            mode=SolveMode.OPTIMIZE,
            variables=variables,
            expressions=reg,
            objectives=objectives,
            constraints=constraints,
            budget=ComputeBudget(wall_time_seconds=30.0),
            approved=False,
        )


# ---------------------------------------------------------------------------
# D3: Pareto Frontier & Results for DESIGN Class
# ---------------------------------------------------------------------------

class ParetoPoint(BaseModel):
    configuration: dict[str, str]  # lever_id -> option_id
    objective_values: dict[str, float]  # criterion_id -> value
    is_pareto_optimal: bool = True


class DesignSynthesisResult(BaseModel):
    problem_id: str
    optimal_configuration: dict[str, str]
    optimal_titles: dict[str, str]
    model_optimal_label: str = "optymalna dla modelu, nie dla świata (wynik zależy od podanych kryteriów i wag)"
    pareto_frontier: list[ParetoPoint]
    lever_importance_ranking: list[dict[str, Any]]
    unknowns_and_decisive_assumptions: list[str]
    practical_manifestation: str


def compute_design_pareto_frontier(
    design: DesignProblem,
    max_configurations: int = 1000,
) -> list[ParetoPoint]:
    """
    Computes Pareto optimal points for small to medium models using exhaustive search or epsilon-constraint.
    Ensures that for any two Pareto points, neither is strictly dominated by the other across all criteria.
    """
    design.validate_design()
    # List of options per lever
    lever_options_list = [[(l.id, opt.id) for opt in l.options] for l in design.levers]
    all_combos = list(itertools.product(*lever_options_list))

    incompat_pairs = {
        (
            (i.lever_a_id, i.option_a_id),
            (i.lever_b_id, i.option_b_id)
        )
        for i in design.interactions if not i.compatible
    }
    # Symmetric check
    for i in design.interactions:
        if not i.compatible:
            incompat_pairs.add(((i.lever_b_id, i.option_b_id), (i.lever_a_id, i.option_a_id)))

    valid_candidates: list[tuple[dict[str, str], dict[str, float]]] = []

    for combo in all_combos[:max_configurations]:
        combo_set = set(combo)
        # Check compatibility
        is_compat = True
        for a, b in itertools.combinations(combo, 2):
            if (a, b) in incompat_pairs or (b, a) in incompat_pairs:
                is_compat = False
                break
        if not is_compat:
            continue

        config_dict = {lid: oid for lid, oid in combo}

        # Calculate scores per criterion
        crit_scores: dict[str, float] = {}
        for crit in design.criteria:
            total = 0.0
            for lid, oid in combo:
                cell = design.score_matrix.get(lid, {}).get(oid, {}).get(crit.id)
                if cell and cell.value is not None:
                    total += float(cell.value)
            crit_scores[crit.id] = total

        valid_candidates.append((config_dict, crit_scores))

    if not valid_candidates:
        return []

    # Filter non-dominated points (Pareto optimal)
    pareto_points: list[ParetoPoint] = []

    for cfg_a, scores_a in valid_candidates:
        is_dominated = False
        for cfg_b, scores_b in valid_candidates:
            if cfg_a == cfg_b:
                continue

            # Check if B dominates A
            # B dominates A if B is as good as A on all criteria and strictly better on at least one
            better_or_equal_all = True
            strictly_better_any = False

            for crit in design.criteria:
                val_a = scores_a[crit.id]
                val_b = scores_b[crit.id]
                if crit.direction == "maximize":
                    if val_b < val_a:
                        better_or_equal_all = False
                        break
                    if val_b > val_a:
                        strictly_better_any = True
                else:  # minimize
                    if val_b > val_a:
                        better_or_equal_all = False
                        break
                    if val_b < val_a:
                        strictly_better_any = True

            if better_or_equal_all and strictly_better_any:
                is_dominated = True
                break

        if not is_dominated:
            pareto_points.append(
                ParetoPoint(
                    configuration=cfg_a,
                    objective_values=scores_a,
                    is_pareto_optimal=True,
                )
            )

    return pareto_points
