"""Tests for ProblemFormalizer."""
from backend.domain.formalizer import ProblemFormalizer


def test_empty_input():
    formalizer = ProblemFormalizer()
    res = formalizer.formalize("   ")
    assert res.binary_variables == []
    assert len(res.missing_information) > 0


def test_knapsack_heuristic():
    formalizer = ProblemFormalizer()
    res = formalizer.formalize("Chcę rozwiązać problem plecakowy o udźwigu 7 kg dla 4 przedmiotów")
    assert res.identified_archetype == "knapsack"
    assert len(res.binary_variables) == 4
    assert res.objective_direction == "maximize"
    assert len(res.inequality_constraints) == 1
    assert res.inequality_constraints[0]["rhs"] == 7.0


def test_maxcut_heuristic():
    formalizer = ProblemFormalizer()
    res = formalizer.formalize("Zoptymalizuj podział grafu Max-Cut dla 4 wierzchołków")
    assert res.identified_archetype == "max_cut"
    assert len(res.binary_variables) == 4
    assert "v0" in res.binary_variables


def test_portfolio_heuristic():
    formalizer = ProblemFormalizer()
    res = formalizer.formalize("Maksymalizuj zysk z inwestycji w projekty, wybierz dokładnie 2 z nich")
    assert res.identified_archetype == "portfolio"
    assert res.objective_direction == "maximize"
    assert len(res.equality_constraints) == 1
    assert res.equality_constraints[0]["rhs"] == 2.0


def test_linear_selection_fallback():
    formalizer = ProblemFormalizer()
    res = formalizer.formalize("Maksymalizuj zysk dla x0, x1, x2 gdzie suma wynosi 2")
    assert "x0" in res.binary_variables
    assert "x1" in res.binary_variables
    assert res.objective_direction == "maximize"
    assert len(res.equality_constraints) == 1
    assert res.equality_constraints[0]["rhs"] == 2.0
