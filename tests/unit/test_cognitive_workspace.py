"""
Unit tests for Cognitive Working Memory, Energy Budget, and Constraint Sanity.
"""
from __future__ import annotations

import pytest

from backend.domain.cognitive.constraint_sanity import check_constraints_sanity
from backend.domain.cognitive.ir_builder import build_problem_ir
from backend.domain.cognitive.workspace import EnergyBudget, GlobalWorkspace, WorkingMemory
from backend.domain.problem_ir import ProblemIR, Variable, VariableDomain


def test_energy_budget_consumption_and_exhaustion():
    budget = EnergyBudget(max_tokens=1000, max_cycles=3)
    assert not budget.is_exhausted()
    assert budget.remaining_tokens == 1000
    assert budget.remaining_cycles == 3

    # Normal consumption
    assert budget.consume(400) is True
    assert budget.tokens_used == 400
    assert budget.remaining_tokens == 600
    assert not budget.is_exhausted()

    # Exceeding consumption
    assert budget.consume(700) is False
    assert budget.tokens_used == 1000
    assert budget.remaining_tokens == 0
    assert budget.is_exhausted()

    # Negative consumption validation
    with pytest.raises(ValueError):
        budget.consume(-50)


def test_energy_budget_cycles():
    budget = EnergyBudget(max_tokens=1000, max_cycles=2)
    assert budget.current_cycle == 0

    assert budget.next_cycle() is True
    assert budget.current_cycle == 1
    assert not budget.is_exhausted()

    assert budget.next_cycle() is True
    assert budget.current_cycle == 2
    assert budget.is_exhausted()

    # Further cycle attempts return False
    assert budget.next_cycle() is False


def test_working_memory_state():
    wm = WorkingMemory(current_goal="Optymalizacja alokacji zasobów")
    assert wm.current_goal == "Optymalizacja alokacji zasobów"
    assert wm.active_hypothesis is None
    assert wm.focus_variables == []
    assert wm.prediction_errors == []

    wm.record_error("Błąd 1: Przekroczono budżet")
    wm.record_error("Błąd 1: Przekroczono budżet")  # duplicate
    assert len(wm.prediction_errors) == 1

    ir = build_problem_ir(
        raw_query="Test query",
        variables_spec=[
            {"id": "var_a", "name": "A", "domain": "binary"},
            {"id": "var_b", "name": "B", "domain": "binary"},
        ],
        objective_spec={"direction": "maximize", "coefficients": {"var_a": 5.0, "var_b": 10.0}},
        constraints_spec=[
            {"id": "c1", "type": "inequality_le", "lhs_terms": {"var_a": 1.0, "var_b": 2.0}, "rhs": 2.0}
        ],
    )

    wm.set_hypothesis(ir)
    assert wm.active_hypothesis is not None
    assert set(wm.focus_variables) == {"var_a", "var_b"}

    wm.clear_errors()
    assert len(wm.prediction_errors) == 0


def test_global_workspace_orchestration():
    ws = GlobalWorkspace(goal="Wybór projektów R&D", budget=EnergyBudget(max_tokens=500, max_cycles=2))
    ws.register_prediction_error("Odrzucono przez solver: infeasible")
    assert len(ws.memory.prediction_errors) == 1

    ir = build_problem_ir(
        raw_query="Wybór projektów R&D",
        variables_spec=[{"id": "p1", "name": "Proj 1", "domain": "binary"}],
        objective_spec={"direction": "maximize", "coefficients": {"p1": 10.0}},
        constraints_spec=[],
    )
    ws.update_hypothesis(ir, {"note": "initial_hypothesis"})
    assert len(ws.memory.cycle_history) == 1
    assert ws.memory.cycle_history[0]["note"] == "initial_hypothesis"

    state = ws.format_state_for_reasoning()
    assert state["goal"] == "Wybór projektów R&D"
    assert state["active_hypothesis"]["variables_count"] == 1
    assert "Odrzucono przez solver: infeasible" in state["prediction_errors"]


def test_constraint_sanity_checks():
    # Valid problem
    valid_ir = build_problem_ir(
        raw_query="Valid problem",
        variables_spec=[
            {"id": "x1", "name": "X1", "domain": "binary"},
            {"id": "x2", "name": "X2", "domain": "binary"},
        ],
        objective_spec={"direction": "maximize", "coefficients": {"x1": 1.0}},
        constraints_spec=[
            {"id": "c1", "type": "inequality_le", "lhs_terms": {"x1": 1.0, "x2": 1.0}, "rhs": 1.0}
        ],
    )
    sanity_res = check_constraints_sanity(valid_ir)
    assert sanity_res.passed is True
    assert len(sanity_res.errors) == 0

    # Inverted bounds
    bad_var_ir = valid_ir.model_copy(deep=True)
    bad_var_ir.variables.append(
        Variable(id="x_inv", name="Inv", domain=VariableDomain.INTEGER, lower_bound=10.0, upper_bound=5.0)
    )
    bad_sanity = check_constraints_sanity(bad_var_ir)
    assert bad_sanity.passed is False
    assert any("inverted bounds" in err for err in bad_sanity.errors)

    # Constant contradiction: 5 <= 2
    from backend.domain.problem_ir import Constraint, ConstraintType
    const_bad_ir = valid_ir.model_copy(deep=True)
    cid_lhs = const_bad_ir.expressions.const(5.0)
    cid_rhs = const_bad_ir.expressions.const(2.0)
    const_bad_ir.constraints.append(
        Constraint(
            id="c_impossible",
            type=ConstraintType.INEQUALITY_LE,
            lhs_expression_id=cid_lhs,
            rhs_expression_id=cid_rhs,
            hard=True,
        )
    )
    const_sanity = check_constraints_sanity(const_bad_ir)
    assert const_sanity.passed is False
    assert any("impossible constant contradiction" in err for err in const_sanity.errors)
