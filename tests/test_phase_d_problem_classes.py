"""
YourQuantum — Phase D Test Suite (Problem Classes, Multi-Lever Design Synthesis, Continuous Solver)
Verifies D1-D6 requirements: taxonomy, non-computable reframing, one-hot constraints,
synergy provenance enforcement, Pareto frontier generation, continuous HiGHS adapter,
and healthcare fixture synthesis.
"""
import json
import os
import pytest

from backend.domain.problem_classes import (
    DesignCriterion,
    DesignLever,
    DesignProblem,
    Interaction,
    LeverOption,
    ProblemClass,
    compute_design_pareto_frontier,
    evaluate_problem_computability,
)
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
from backend.solvers.base import MathStatus, ComputeSource
from backend.solvers.continuous import ContinuousSolverAdapter
from backend.solvers.cpsat import CPSATAdapter


# ---------------------------------------------------------------------------
# D1: ProblemClass Taxonomy & Computability Gate
# ---------------------------------------------------------------------------

def test_d1_problem_class_taxonomy_and_not_computable():
    """D1: ProblemClass taxonomy and honest rejection of non-computable questions with reframing advice."""
    assert ProblemClass.CHOICE == "CHOICE"
    assert ProblemClass.ALLOCATION == "ALLOCATION"
    assert ProblemClass.DESIGN == "DESIGN"
    assert ProblemClass.PARAMETER == "PARAMETER"
    assert ProblemClass.NOT_COMPUTABLE == "NOT_COMPUTABLE"

    # Non-computable existential / philosophical query
    is_computable, report = evaluate_problem_computability("Jaki jest sens życia?")
    assert not is_computable
    assert report is not None
    assert "filozoficznym" in report.reason.lower() or "egzystencjalnym" in report.reason.lower()
    assert len(report.reframe_suggestions) >= 2

    # Computable architectural query
    is_computable_ok, report_ok = evaluate_problem_computability("Jaki byłby optymalny model ochrony zdrowia w Polsce?")
    assert is_computable_ok
    assert report_ok is None


# ---------------------------------------------------------------------------
# D2: Multi-Lever Synergy Provenance Enforcement
# ---------------------------------------------------------------------------

def test_d2_synergy_without_source_is_strictly_rejected():
    """D2: Zero invented synergies. Any non-zero synergy must have a source_ref or raise ValueError."""
    # 1. Synergy with missing source_ref must fail validation
    bad_interaction = Interaction(
        lever_a_id="l1",
        option_a_id="o1",
        lever_b_id="l2",
        option_b_id="o2",
        compatible=True,
        synergy=15.0,
        source_ref=None,
    )
    with pytest.raises(ValueError, match="requires a verified source_ref"):
        bad_interaction.validate_synergy_source()

    # 2. Synergy with valid source_ref succeeds
    valid_interaction = Interaction(
        lever_a_id="l1",
        option_a_id="o1",
        lever_b_id="l2",
        option_b_id="o2",
        compatible=True,
        synergy=15.0,
        source_ref="badanie_nfz_poz_2024",
    )
    assert valid_interaction.validate_synergy_source() is True


# ---------------------------------------------------------------------------
# D2: Compilation to ProblemIR (One-hot & Compatibility Constraints)
# ---------------------------------------------------------------------------

def test_d2_design_problem_compiles_to_strict_problem_ir():
    """D2: Compiling DesignProblem generates binary one-hot constraints and quadratic synergy objectives."""
    lever1 = DesignLever(
        id="l_fin",
        name="Finansowanie",
        options=[
            LeverOption(id="opt_skladka", title="Składkowy"),
            LeverOption(id="opt_budzet", title="Budżetowy"),
        ],
    )
    lever2 = DesignLever(
        id="l_poz",
        name="POZ",
        options=[
            LeverOption(id="opt_gate", title="Gatekeeping"),
            LeverOption(id="opt_open", title="Otwarty"),
        ],
    )
    criterion = DesignCriterion(id="c_cost", name="Koszt", direction="minimize", weight=1.0)

    design = DesignProblem(
        title="Mini Design",
        description="Test syntezy",
        levers=[lever1, lever2],
        criteria=[criterion],
        interactions=[
            Interaction(
                lever_a_id="l_fin",
                option_a_id="opt_budzet",
                lever_b_id="l_poz",
                option_b_id="opt_open",
                compatible=False,
                synergy=0.0,
                source_ref="wzajemne_wykluczenie_analiza",
            ),
            Interaction(
                lever_a_id="l_fin",
                option_a_id="opt_skladka",
                lever_b_id="l_poz",
                option_b_id="opt_gate",
                compatible=True,
                synergy=5.0,
                source_ref="raport_synergii_2024",
            ),
        ],
    )

    ir = design.compile_to_problem_ir()

    # Variables: 2 levers * 2 options + 1 linearized synergy variable = 5 binary variables
    assert len(ir.variables) == 5
    for v in ir.variables:
        assert v.domain == VariableDomain.BINARY

    # Constraints: 2 one-hot + 1 incompatibility + 3 synergy Fortet bounds = 6 constraints
    assert len(ir.constraints) == 6
    onehot_constraints = [c for c in ir.constraints if c.type == ConstraintType.EQUALITY]
    assert len(onehot_constraints) == 2

    incompat_constraints = [c for c in ir.constraints if "incompat" in c.id]
    assert len(incompat_constraints) == 1

    # Objective is defined
    assert len(ir.objectives) == 1
    assert ir.objectives[0].direction == ObjectiveDirection.MAXIMIZE


# ---------------------------------------------------------------------------
# D3: Pareto Frontier on Healthcare Fixture
# ---------------------------------------------------------------------------

def test_d3_pareto_frontier_computation_on_fixture():
    """D3: Computes non-dominated Pareto front points for healthcare synthesis fixture."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "design", "healthcare_pl.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    levers = [DesignLever(**l) for l in data["levers"]]
    criteria = [DesignCriterion(**c) for c in data["criteria"]]
    interactions = [Interaction(**i) for i in data["interactions"]]

    design = DesignProblem(
        title=data["title"],
        description=data["description"],
        levers=levers,
        criteria=criteria,
        score_matrix=data["scores"],
        interactions=interactions,
    )

    pareto_points = compute_design_pareto_frontier(design)
    assert len(pareto_points) > 0

    # Ensure no Pareto point strictly dominates another
    for idx_a, pa in enumerate(pareto_points):
        for idx_b, pb in enumerate(pareto_points):
            if idx_a == idx_b:
                continue
            # It is impossible for pa to be strictly better on all criteria than pb
            better_count = 0
            for crit in criteria:
                val_a = pa.objective_values[crit.id]
                val_b = pb.objective_values[crit.id]
                if (crit.direction == "maximize" and val_a > val_b) or (crit.direction == "minimize" and val_a < val_b):
                    better_count += 1
            # pa cannot be strictly better on every single criterion than pb
            assert better_count < len(criteria)


# ---------------------------------------------------------------------------
# D4: Continuous Optimization Solver Adapter (SciPy HiGHS)
# ---------------------------------------------------------------------------

def test_d4_continuous_solver_adapter_highs():
    """D4: ContinuousSolverAdapter solves continuous LP using SciPy HiGHS and reports numerical residual."""
    reg = ExpressionRegistry()
    # Problem: Maximize 3*x1 + 2*x2 subject to x1 + x2 <= 10, x1 <= 6, x1, x2 >= 0
    reg.add(ExprNode(id="v_x1", op="var", value="x1"))
    reg.add(ExprNode(id="v_x2", op="var", value="x2"))

    c1 = reg.add(ExprNode(id="c1", op="const", value=3.0))
    c2 = reg.add(ExprNode(id="c2", op="const", value=2.0))
    t1 = reg.add(ExprNode(id="t1", op="mul", children=[c1, "v_x1"]))
    t2 = reg.add(ExprNode(id="t2", op="mul", children=[c2, "v_x2"]))
    obj_id = reg.add(ExprNode(id="obj_sum", op="sum", children=[t1, t2]))

    # x1 + x2 <= 10
    sum_12 = reg.add(ExprNode(id="sum_12", op="sum", children=["v_x1", "v_x2"]))
    rhs_10 = reg.add(ExprNode(id="rhs_10", op="const", value=10.0))

    # x1 <= 6
    rhs_6 = reg.add(ExprNode(id="rhs_6", op="const", value=6.0))

    ir = ProblemIR(
        description_raw="Continuous LP test",
        description_formalised="Continuous optimization",
        mode=SolveMode.OPTIMIZE,
        variables=[
            Variable(id="x1", name="x1", domain=VariableDomain.CONTINUOUS, lower_bound=0.0, upper_bound=20.0),
            Variable(id="x2", name="x2", domain=VariableDomain.CONTINUOUS, lower_bound=0.0, upper_bound=20.0),
        ],
        expressions=reg,
        objectives=[Objective(id="obj1", direction=ObjectiveDirection.MAXIMIZE, expression_id=obj_id)],
        constraints=[
            Constraint(id="con_sum", type=ConstraintType.INEQUALITY_LE, lhs_expression_id=sum_12, rhs_expression_id=rhs_10),
            Constraint(id="con_bound", type=ConstraintType.INEQUALITY_LE, lhs_expression_id="v_x1", rhs_expression_id=rhs_6),
        ],
        budget=ComputeBudget(wall_time_seconds=10.0),
        approved=True,
    )

    adapter = ContinuousSolverAdapter()
    assert adapter.supports(ir) is True

    res = adapter.solve(ir, ir.budget)
    assert res.execution_status.value == "COMPLETED"
    assert res.math_status == MathStatus.OPTIMAL
    assert res.source == ComputeSource.CLASSICAL_SOLVER
    assert res.assignment is not None
    # Expected solution: x1 = 6, x2 = 4 -> objective = 3*6 + 2*4 = 26.0
    assert abs(res.assignment["x1"] - 6.0) < 1e-4
    assert abs(res.assignment["x2"] - 4.0) < 1e-4
    assert abs(float(res.objective_value) - 26.0) < 1e-4
    assert res.numerical_residual < 1e-5


# ---------------------------------------------------------------------------
# D6: Healthcare Synthesis End-to-End Solving with CP-SAT
# ---------------------------------------------------------------------------

def test_d6_healthcare_synthesis_cpsat_solving():
    """D6: Full multi-lever healthcare problem compiles to IR and is solved by CP-SAT."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "design", "healthcare_pl.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    levers = [DesignLever(**l) for l in data["levers"]]
    criteria = [DesignCriterion(**c) for c in data["criteria"]]
    interactions = [Interaction(**i) for i in data["interactions"]]

    design = DesignProblem(
        title=data["title"],
        description=data["description"],
        levers=levers,
        criteria=criteria,
        score_matrix=data["scores"],
        interactions=interactions,
    )

    ir = design.compile_to_problem_ir()
    ir.approved = True

    cpsat = CPSATAdapter()
    res = cpsat.solve(ir, ir.budget)

    assert res.execution_status.value == "COMPLETED"
    assert res.math_status in (MathStatus.OPTIMAL, MathStatus.FEASIBLE)
    assert res.source == ComputeSource.CLASSICAL_SOLVER

    # Verify that exactly one option is chosen per lever in the assignment
    chosen_options = [k for k, v in res.assignment.items() if v > 0.5 and k.startswith("x_")]
    assert len(chosen_options) == len(levers)

    # Verify incompatibility constraint was respected:
    # budzetowy_centralny (x_lever_finansowanie_budzetowy_centralny) and
    # kasy_regionalne (x_lever_platnik_kasy_regionalne) cannot be chosen together!
    incompat_a = "x_lever_finansowanie_budzetowy_centralny" in chosen_options
    incompat_b = "x_lever_platnik_kasy_regionalne" in chosen_options
    assert not (incompat_a and incompat_b)

    # Verify synergy variable syn_y_1 is correctly triggered
    assert res.assignment.get("syn_y_1") == 1.0
