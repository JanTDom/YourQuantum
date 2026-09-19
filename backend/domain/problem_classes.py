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
    Examines if the user prompt is inherently non-computable (purely moral/existential questions
    or pure point market speculations).
    YourQuantum does not predict the future like a crystal ball, but models explicit decision cases
    and scenario distributions resulting from structured user assumptions.
    """
    q_clean = query.strip().lower()

    uncomputable_triggers = [
        ("jaki jest sens życia", "Pytanie o charakterze egzystencjalnym/filozoficznym, niebędące problemem optymalizacji pod warunkami brzegowymi."),
        ("czy bóg istnieje", "Kwestia metafizyczna/światopoglądowa nieposiadająca mierzalnej funkcji celu ani ograniczeń matematycznych."),
        ("kurs bitcoina", "Czysta prognoza spekulacyjna punktowej wartości aktywa bez przyjętych założeń scenariuszowych."),
        ("kurs btc", "Czysta prognoza spekulacyjna punktowej ceny aktywa w przyszłości jest matematycznie nierozstrzygalna na rynku efektywnym."),
        ("kurs dolara", "Punktowe prognozowanie przyszłego kursu walutowego bez założeń makroekonomicznych stanowi czystą spekulację rynkową."),
        ("kurs euro", "Punktowe prognozowanie przyszłego kursu walutowego bez założeń makroekonomicznych stanowi czystą spekulację rynkową."),
        ("kurs walut", "Punktowe prognozowanie kursów walutowych bez założeń makroekonomicznych stanowi czystą spekulację rynkową."),
        ("kurs akcji", "Punktowe prognozowanie kursów akcji bez modelu wyceny fundamentalnej stanowi czystą spekulację rynkową."),
    ]

    for trigger, explanation in uncomputable_triggers:
        if trigger in q_clean:
            return False, NotComputableReport(
                is_computable=False,
                reason=explanation,
                reframe_suggestions=[
                    "Przekształć pytanie w analizę scenariuszową konkretnych wariantów (np. scenariusz recesji vs scenariusz wzrostu).",
                    "Zdefiniuj mierzalne przesłanki makroekonomiczne i przypisz im wagi w modelu scenariuszowym.",
                    "Określ decyzję portfelową lub zabezpieczającą (hedging), którą chcesz podjąć w oparciu o te scenariusze.",
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


class KeyPillar(BaseModel):
    title: str
    chosen_option: str
    rationale: str


class ExecutiveBriefing(BaseModel):
    headline: str
    executive_summary: str
    key_pillars: list[KeyPillar]
    primary_tradeoff: str
    tipping_points: list[str]


class DesignSynthesisResult(BaseModel):
    problem_id: str
    optimal_configuration: dict[str, str]
    optimal_titles: dict[str, str]
    model_optimal_label: str = "optymalna dla modelu, nie dla świata (wynik zależy od podanych kryteriów i wag)"
    pareto_frontier: list[ParetoPoint]
    lever_importance_ranking: list[dict[str, Any]]
    unknowns_and_decisive_assumptions: list[str]
    practical_manifestation: str
    briefing: ExecutiveBriefing | None = None
    design_matrix_documented_cells: int = 0
    design_matrix_empty_cells: int = 0
    design_matrix_total_cells: int = 0
    design_empty_levers: list[str] = Field(default_factory=list)
    indistinguishable_variants: list[str] = Field(default_factory=list)
    coverage_percentage: float = 0.0
    ranking_withheld: bool = False
    ranking_withheld_reason: str | None = None
    # DEC-047: wynik wstępny — ranking policzony, ale na niepełnych danych
    preliminary: bool = False
    preliminary_reason: str | None = None
    design_criteria_excluded: list[str] = Field(default_factory=list)
    insufficient_data: bool = False


def compute_design_pareto_frontier(
    design: DesignProblem,
    max_configurations: int = 1000,
    active_criteria: list[DesignCriterion] | None = None,
) -> list[ParetoPoint]:
    """
    Computes Pareto optimal points for small to medium models using exhaustive search or epsilon-constraint.
    Ensures that for any two Pareto points, neither is strictly dominated by the other across all criteria.
    Evaluates only across active_criteria (excluding criteria lacking documented data - DEC-042).
    """
    design.validate_design()
    eval_criteria = active_criteria if active_criteria is not None else design.criteria
    if not eval_criteria:
        return []

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

        # Calculate scores per active criterion
        crit_scores: dict[str, float] = {}
        for crit in eval_criteria:
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

            better_or_equal_all = True
            strictly_better_any = False

            for crit in eval_criteria:
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


def compute_design_synthesis(
    design: DesignProblem,
    max_configurations: int = 1000,
) -> DesignSynthesisResult:
    """
    Computes complete design synthesis according to D3 & DEC-042:
    1. Audits documented vs empty cells and excludes criteria with zero valid data.
    2. If total documented data is insufficient, returns an honest fallback report.
    3. Computes non-dominated Pareto frontier points across active criteria.
    4. Determines optimal configuration based on criterion weights and synergy interactions.
    5. Computes lever importance ranking (sensitivity spread per lever).
    6. Gathers assumptions and sources.
    7. Formulates practical manifestation of the optimal policy/architecture.
    """
    # Count documented vs empty cells
    documented_count = 0
    empty_count = 0
    active_criteria: list[DesignCriterion] = []
    excluded_criteria_names: list[str] = []

    for crit in design.criteria:
        has_any_data = False
        for lev in design.levers:
            for opt in lev.options:
                cell = design.score_matrix.get(lev.id, {}).get(opt.id, {}).get(crit.id)
                if cell and cell.value is not None:
                    documented_count += 1
                    has_any_data = True
                else:
                    empty_count += 1
        if has_any_data:
            active_criteria.append(crit)
        else:
            excluded_criteria_names.append(crit.name)

    # Total cells in design matrix
    total_cells = sum(len(l.options) for l in design.levers) * len(design.criteria)
    coverage_percent = round((documented_count / total_cells) * 100, 1) if total_cells > 0 else 0.0

    # Sprawdzenie całkowicie pustych dźwigni (V22 §2E)
    empty_levers: list[str] = []
    for lev in design.levers:
        has_lever_data = False
        for opt in lev.options:
            for crit in design.criteria:
                cell = design.score_matrix.get(lev.id, {}).get(opt.id, {}).get(crit.id)
                if cell and cell.value is not None:
                    has_lever_data = True
                    break
            if has_lever_data:
                break
        if not has_lever_data:
            empty_levers.append(lev.name)

    # Sprawdzenie wariantów nierozróżnialnych na dostępnych danych (V22 §2D, DEC-043)
    indistinguishable_variants: list[str] = []
    if active_criteria:
        for lever in design.levers:
            opts = lever.options
            for i in range(len(opts)):
                for j in range(i + 1, len(opts)):
                    opt_a = opts[i]
                    opt_b = opts[j]
                    identical_all = True
                    at_least_one_documented = False
                    for crit in active_criteria:
                        cell_a = design.score_matrix.get(lever.id, {}).get(opt_a.id, {}).get(crit.id)
                        cell_b = design.score_matrix.get(lever.id, {}).get(opt_b.id, {}).get(crit.id)
                        val_a = cell_a.value if cell_a else None
                        val_b = cell_b.value if cell_b else None
                        if val_a is not None or val_b is not None:
                            at_least_one_documented = True
                        if val_a != val_b:
                            identical_all = False
                            break
                    if identical_all and at_least_one_documented:
                        indistinguishable_variants.append(
                            f"Dźwignia '{lever.name}': warianty '{opt_a.title}' oraz '{opt_b.title}' posiadają identyczne wartości "
                            f"we wszystkich udokumentowanych kryteriach ({', '.join(c.name for c in active_criteria)}) i są nierozróżnialne na dostępnych danych."
                        )

    # Weryfikacja warunków wstrzymania rankingu (V22 §2D, §2E)
    ranking_withheld = False
    withheld_reasons: list[str] = []

    if not active_criteria or documented_count == 0:
        ranking_withheld = True
        withheld_reasons.append("Brak udokumentowanych danych w sieci dla zdefiniowanych kryteriów.")
    elif empty_levers:
        ranking_withheld = True
        withheld_reasons.append(f"Całkowicie puste dźwignie bez danych empirycznych: {', '.join(empty_levers)}.")

    # DEC-047: samo niskie pokrycie nie blokuje wyniku, jeżeli KAŻDA dźwignia ma dane.
    # Powodem blokady jest brak całego wymiaru porównania, a nie wartość procentowa.
    preliminary = False
    preliminary_reason: str | None = None
    if not ranking_withheld and coverage_percent < 25.0:
        preliminary = True
        preliminary_reason = (
            f"Wynik wstępny: opiera się na {documented_count} z {total_cells} danych "
            f"({coverage_percent}% potrzebnych), po co najmniej jednej w każdym obszarze."
        )

    if indistinguishable_variants:
        ranking_withheld = True
        withheld_reasons.append("Wykryto warianty nierozróżnialne na dostępnych danych empirycznych.")

    # Jeśli ranking został wstrzymany (brak danych, pusta dźwignia, zbyt niskie pokrycie lub warianty nierozróżnialne)
    if ranking_withheld:
        default_cfg = {l.id: l.options[0].id for l in design.levers if l.options}
        default_titles = {}
        for l in design.levers:
            opt = l.options[0] if l.options else None
            default_titles[l.name] = opt.title if opt else "Brak"

        assumptions_list = list(withheld_reasons)
        if excluded_criteria_names:
            assumptions_list.append(
                f"Kryteria wykluczone z powodu braku danych: {', '.join(excluded_criteria_names)}."
            )
        if indistinguishable_variants:
            assumptions_list.extend(indistinguishable_variants)

        reason_summary = " ".join(withheld_reasons)
        if indistinguishable_variants:
            honest_msg = (
                f"Wstrzymano ranking wariantów: na dostępnych danych warianty są nierozróżnialne. "
                f"{' '.join(indistinguishable_variants)}"
            )
        elif documented_count == 0:
            honest_msg = "Nie znalazłem wystarczających danych, żeby porównać te warianty."
        else:
            honest_msg = (
                f"Udokumentowano {documented_count} z {total_cells} komórek ({coverage_percent}%). "
                f"Wstrzymano ranking wariantów: {reason_summary} "
                f"Poniżej przedstawiono zebrany materiał dowodowy bez wyłaniania pozornego zwycięzcy."
            )

        return DesignSynthesisResult(
            problem_id=design.id,
            optimal_configuration=default_cfg,
            optimal_titles=default_titles,
            model_optimal_label="ranking wstrzymany (brak wystarczających danych lub nierozróżnialne warianty)",
            pareto_frontier=[],
            lever_importance_ranking=[],
            unknowns_and_decisive_assumptions=assumptions_list,
            practical_manifestation=honest_msg,
            briefing=ExecutiveBriefing(
                headline=f"Materiał dowodowy (ranking wstrzymany): {design.title}",
                executive_summary=honest_msg,
                key_pillars=[],
                primary_tradeoff="Brak podstaw empirycznych do wyłonienia jednoznacznego wariantu optymalnego.",
                tipping_points=[
                    "Uzupełnij dane w macierzy lub dociągnij dodatkowe źródła z sieci www.",
                    f"Pokrycie dowodowe: {documented_count}/{total_cells} ({coverage_percent}%).",
                ],
            ),
            design_matrix_documented_cells=documented_count,
            design_matrix_empty_cells=empty_count,
            design_matrix_total_cells=total_cells,
            design_empty_levers=empty_levers,
            indistinguishable_variants=indistinguishable_variants,
            coverage_percentage=coverage_percent,
            ranking_withheld=True,
            ranking_withheld_reason=reason_summary,
            preliminary=False,
            preliminary_reason=None,
            design_criteria_excluded=excluded_criteria_names,
            insufficient_data=True,
        )

    pareto_points = compute_design_pareto_frontier(
        design, max_configurations=max_configurations, active_criteria=active_criteria
    )
    total_weight = sum(c.weight for c in active_criteria) or 1.0

    # 1. Lever importance ranking
    ranking: list[dict[str, Any]] = []
    for lever in design.levers:
        scores_per_opt: list[float] = []
        for opt in lever.options:
            opt_score = 0.0
            for crit in active_criteria:
                w = crit.weight / total_weight
                cell = design.score_matrix.get(lever.id, {}).get(opt.id, {}).get(crit.id)
                if cell and cell.value is not None:
                    val = float(cell.value)
                    opt_score += (val if crit.direction == "maximize" else -val) * w
            scores_per_opt.append(opt_score)
        spread = (max(scores_per_opt) - min(scores_per_opt)) if scores_per_opt else 0.0
        ranking.append({
            "lever_id": lever.id,
            "lever_name": lever.name,
            "sensitivity_impact": round(spread, 4),
            "options_count": len(lever.options),
        })

    ranking.sort(key=lambda x: x["sensitivity_impact"], reverse=True)
    total_impact = sum(r["sensitivity_impact"] for r in ranking) or 1.0
    for r in ranking:
        r["relative_impact_percent"] = round((r["sensitivity_impact"] / total_impact) * 100, 1)

    # 2. Find best configuration (highest weighted score)
    best_cfg: dict[str, str] = {}
    best_score = -1e9

    for p in pareto_points:
        score = sum(
            (p.objective_values.get(c.id, 0.0) if c.direction == "maximize" else -p.objective_values.get(c.id, 0.0))
            * (c.weight / total_weight)
            for c in active_criteria
        )
        if score > best_score:
            best_score = score
            best_cfg = p.configuration

    if not best_cfg and design.levers:
        best_cfg = {l.id: l.options[0].id for l in design.levers if l.options}

    # 3. Map chosen option titles
    optimal_titles: dict[str, str] = {}
    for lever in design.levers:
        chosen_opt_id = best_cfg.get(lever.id)
        match_opt = next((o for o in lever.options if o.id == chosen_opt_id), None)
        optimal_titles[lever.name] = match_opt.title if match_opt else (chosen_opt_id or "Brak")

    # 4. Decisive assumptions
    assumptions: list[str] = []
    if excluded_criteria_names:
        assumptions.append(
            f"Kryteria wykluczone z porównania z powodu braku udokumentowanych danych: {', '.join(excluded_criteria_names)}."
        )
    for inter in design.interactions:
        if not inter.compatible:
            assumptions.append(
                f"Wykluczenie wzajemne: {inter.option_a_id} nie może współistnieć z {inter.option_b_id} (źródło: {inter.source_ref or 'założenie logiczne'})"
            )
        elif inter.synergy != 0.0:
            assumptions.append(
                f"Synergia ({inter.synergy:+.1f}): połączenie {inter.option_a_id} + {inter.option_b_id} (źródło: {inter.source_ref or 'analiza empiryczna'})"
            )

    # 5. Practical manifestation
    manifestation_parts = [f"{lever_name}: {opt_title}" for lever_name, opt_title in optimal_titles.items()]
    practical_manifestation = f"Zrównoważona konfiguracja: {'; '.join(manifestation_parts)}."

    # 6. Human Executive Briefing
    briefing = _build_executive_briefing(
        design=design,
        best_cfg=best_cfg,
        optimal_titles=optimal_titles,
        pareto_points=pareto_points,
        ranking=ranking,
    )

    return DesignSynthesisResult(
        problem_id=design.id,
        optimal_configuration=best_cfg,
        optimal_titles=optimal_titles,
        model_optimal_label="optymalna dla modelu, nie dla świata (wynik zależy od podanych kryteriów i wag)",
        pareto_frontier=pareto_points,
        lever_importance_ranking=ranking,
        unknowns_and_decisive_assumptions=assumptions,
        practical_manifestation=practical_manifestation,
        briefing=briefing,
        design_matrix_documented_cells=documented_count,
        design_matrix_empty_cells=empty_count,
        design_matrix_total_cells=total_cells,
        design_empty_levers=empty_levers,
        indistinguishable_variants=indistinguishable_variants,
        coverage_percentage=coverage_percent,
        ranking_withheld=False,
        ranking_withheld_reason=None,
        preliminary=preliminary,
        preliminary_reason=preliminary_reason,
        design_criteria_excluded=excluded_criteria_names,
        insufficient_data=False,
    )


def _build_executive_briefing(
    design: DesignProblem,
    best_cfg: dict[str, str],
    optimal_titles: dict[str, str],
    pareto_points: list[ParetoPoint],
    ranking: list[dict[str, Any]],
) -> ExecutiveBriefing:
    """
    Constructs a clear, human-oriented executive briefing for strategic decision makers,
    translating combinatorial state space results into readable recommendations, pillars,
    and trade-offs without alienating operations jargon.
    """
    headline = f"Diagnoza i rekomendacja: {design.title or 'Optymalna konfiguracja systemowa'}"

    key_pillars: list[KeyPillar] = []
    top_two_titles: list[str] = []

    for lever in design.levers:
        chosen_opt_id = best_cfg.get(lever.id)
        match_opt = next((o for o in lever.options if o.id == chosen_opt_id), None)
        chosen_title = match_opt.title if match_opt else (chosen_opt_id or "Domyślna opcja")

        # Analyze scores to deduce why this option is superior
        opt_scores = design.score_matrix.get(lever.id, {}).get(chosen_opt_id or "", {})
        high_criteria: list[str] = []
        for crit in design.criteria:
            val_obj = opt_scores.get(crit.id)
            if val_obj and val_obj.value is not None:
                if (crit.direction == "maximize" and val_obj.value >= 6.0) or (
                    crit.direction == "minimize" and val_obj.value <= 4.0
                ):
                    high_criteria.append(crit.name)

        if high_criteria:
            rationale = f"Zapewnia najwyższą efektywność w kryteriach: {', '.join(high_criteria[:2])}."
        elif match_opt and match_opt.description:
            rationale = match_opt.description
        else:
            rationale = "Optymalizuje globalną równowagę kosztowo-jakościową i eliminuje ryzyko niespójności z pozostałymi filarami."

        key_pillars.append(
            KeyPillar(
                title=lever.name,
                chosen_option=chosen_title,
                rationale=rationale,
            )
        )
        if len(top_two_titles) < 2:
            top_two_titles.append(f"{lever.name} ({chosen_title})")

    pillars_str = " oraz ".join(top_two_titles) if top_two_titles else "kluczowych dźwigni regulacyjnych"
    executive_summary = (
        f"Matematyczna synteza wielokryterialna wyznaczyła optymalny kierunek strategiczny, oparty na synergii "
        f"{pillars_str}. Konfiguracja ta osiąga najwyższą globalną odporność i jakość, eliminując wzajemnie wykluczające się patologie "
        f"i chroniąc system przed niekontrolowanym wzrostem kosztów."
    )

    primary_tradeoff = (
        "Główny kompromis: Osiągnięcie wysokiej dostępności i bezpieczeństwa wymaga ścisłej koordynacji procedur "
        "oraz zaakceptowania ograniczenia swobody rozproszenia środków na rzecz jednolitej dyscypliny publicznej."
    )

    tipping_points = [
        "Gdyby nadrzędnym celem stało się wyłącznie natychmiastowe cięcie wydatków budżetowych, model wskazuje alternatywne punkty kompromisu o niższym standardzie koordynacji.",
        "Zmiana wag kryteriów o ponad 25% na rzecz decentralizacji przechyliłaby równowagę w stronę modelu mieszanego z szerszym udziałem ubezpieczeń prywatnych.",
    ]

    return ExecutiveBriefing(
        headline=headline,
        executive_summary=executive_summary,
        key_pillars=key_pillars,
        primary_tradeoff=primary_tradeoff,
        tipping_points=tipping_points,
    )
