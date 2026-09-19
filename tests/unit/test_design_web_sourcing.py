"""
Unit tests for DESIGN class evidence pipeline & Pareto on documented subset (DEC-042).
Validates:
1. Strict exclusion of unpopulated criteria from Pareto evaluation (reported in design_criteria_excluded).
2. Honest fallback when insufficient data exists (insufficient_data=True).
3. Zero machine-invented numbers (no provenance='assumed', no dummy 7.0/3.0).
4. Telemetry tracking (design_matrix_documented_cells, design_matrix_empty_cells).
"""
from __future__ import annotations

import pytest
from backend.domain.problem_classes import (
    DesignProblem,
    DesignLever,
    LeverOption,
    DesignCriterion,
    compute_design_synthesis,
    compute_design_pareto_frontier,
)
from backend.domain.decision_case import ScoredValue


def test_design_synthesis_empty_matrix_returns_insufficient_data():
    levers = [
        DesignLever(
            id="l1",
            name="Model finansowania",
            options=[
                LeverOption(id="o1", title="Jednolity płatnik (NFZ)", description=""),
                LeverOption(id="o2", title="Wielu ubezpieczycieli", description=""),
            ],
        ),
        DesignLever(
            id="l2",
            name="Organizacja szpitalnictwa",
            options=[
                LeverOption(id="o3", title="Konsolidacja powiatowa", description=""),
                LeverOption(id="o4", title="Autonomia placówek", description=""),
            ],
        ),
    ]
    criteria = [
        DesignCriterion(id="c1", name="Koszty operacyjne (% PKB)", direction="minimize", weight=1.0),
        DesignCriterion(id="c2", name="Dostępność do specjalistów (dni)", direction="minimize", weight=1.5),
    ]

    # Empty score matrix (values are None or absent)
    score_matrix = {
        "l1": {
            "o1": {"c1": ScoredValue(value=None, provenance="unverified"), "c2": ScoredValue(value=None, provenance="unverified")},
            "o2": {"c1": ScoredValue(value=None, provenance="unverified"), "c2": ScoredValue(value=None, provenance="unverified")},
        },
        "l2": {
            "o3": {"c1": ScoredValue(value=None, provenance="unverified"), "c2": ScoredValue(value=None, provenance="unverified")},
            "o4": {"c1": ScoredValue(value=None, provenance="unverified"), "c2": ScoredValue(value=None, provenance="unverified")},
        },
    }

    dp = DesignProblem(
        id="dp_test_empty",
        title="Test pustej macierzy",
        description="Test pustej macierzy ochrony zdrowia",
        levers=levers,
        criteria=criteria,
        score_matrix=score_matrix,
    )

    result = compute_design_synthesis(dp)
    assert result.insufficient_data is True
    assert "Nie znalazłem wystarczających danych" in result.practical_manifestation
    assert result.design_matrix_documented_cells == 0
    assert result.design_matrix_empty_cells == 8
    assert set(result.design_criteria_excluded) == {
        "Koszty operacyjne (% PKB)",
        "Dostępność do specjalistów (dni)",
    }
    assert result.pareto_frontier == []


def test_design_synthesis_partial_matrix_excludes_unpopulated_criteria():
    levers = [
        DesignLever(
            id="l1",
            name="Model finansowania",
            options=[
                LeverOption(id="o1", title="Jednolity płatnik", description=""),
                LeverOption(id="o2", title="Konkurencja kas chorych", description=""),
            ],
        ),
    ]
    criteria = [
        DesignCriterion(id="c1", name="Wydatki na ochronę zdrowia (% PKB)", direction="minimize", weight=1.0),
        DesignCriterion(id="c2", name="Zadowolenie pacjentów", direction="maximize", weight=1.0),
    ]

    score_matrix = {
        "l1": {
            "o1": {
                "c1": ScoredValue(value=6.8, provenance="web_sourced", source_ref="https://stat.gov.pl"),
                "c2": ScoredValue(value=None, provenance="unverified"),
            },
            "o2": {
                "c1": ScoredValue(value=8.2, provenance="web_sourced", source_ref="https://oecd.org"),
                "c2": ScoredValue(value=None, provenance="unverified"),
            },
        },
    }

    dp = DesignProblem(
        id="dp_test_partial",
        title="Test częściowej macierzy",
        description="Test częściowej macierzy ochrony zdrowia",
        levers=levers,
        criteria=criteria,
        score_matrix=score_matrix,
    )

    result = compute_design_synthesis(dp)
    assert result.insufficient_data is False
    assert result.design_matrix_documented_cells == 2
    assert result.design_matrix_empty_cells == 2
    assert result.design_criteria_excluded == ["Zadowolenie pacjentów"]
    assert len(result.pareto_frontier) >= 1
    assert result.optimal_configuration["l1"] == "o1"


def test_zero_machine_assumed_numbers_in_cells():
    cell_empty = ScoredValue(value=None, provenance="unverified")
    assert cell_empty.provenance == "unverified"
    assert cell_empty.value is None

    cell_web = ScoredValue(value=7.1, provenance="web_sourced", source_ref="https://who.int")
    assert cell_web.provenance == "web_sourced"
    assert cell_web.value == 7.1

    cell_user = ScoredValue(value=5.0, provenance="user_supplied")
    assert cell_user.provenance == "user_supplied"
    assert cell_user.value == 5.0
