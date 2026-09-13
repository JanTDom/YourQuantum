"""Tests for ProblemFormalizer."""
from backend.domain.formalizer import ProblemFormalizer


def test_empty_input():
    formalizer = ProblemFormalizer()
    res = formalizer.formalize("   ")
    assert res.binary_variables == []
    assert len(res.missing_information) > 0


def test_knapsack_heuristic():
    formalizer = ProblemFormalizer()
    res = formalizer.formalize("Chcę rozwiązać problem plecakowy o udźwigu 7 kg. Przedmioty: A waga 2 zysk 5, B waga 3 zysk 8, C waga 4 zysk 9, D waga 1 zysk 3")
    assert res.identified_archetype == "knapsack"
    assert len(res.binary_variables) == 4
    assert res.objective_direction == "maximize"
    assert len(res.inequality_constraints) == 1
    assert res.inequality_constraints[0]["rhs"] == 7.0

    # Also verify that omitting items triggers honest missing_information (A6)
    res_missing = formalizer.formalize("Problem plecakowy o udźwigu 10 kg bez przedmiotów")
    assert len(res_missing.missing_information) > 0


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
