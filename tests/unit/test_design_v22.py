"""
tests/unit/test_design_v22.py — Testy jednostkowe dla zlecenia V22 (DEC-043).

Weryfikuje pozycje z Tabeli Odbioru V22:
- Pozycja 3: Trafienie w wariant — zdanie bez nazwy wariantu nie wypełnia komórki.
- Pozycja 5: Nierozróżnialne warianty — identyczne wartości dają komunikat, nie ranking.
- Brak duplikatów: ta sama para (URL, cytat) nie obsadza wielu komórek.
- Pokrycie: próg 25% oraz pusta dźwignia wstrzymują wyłanianie rankingu.
"""
from __future__ import annotations

import pytest
from backend.domain.problem_classes import (
    DesignProblem,
    DesignLever,
    LeverOption,
    DesignCriterion,
    compute_design_synthesis,
)
from backend.domain.decision_case import ScoredValue
from backend.domain.cognitive.variant_matcher import (
    verify_variant_in_quote,
    get_variant_keywords,
)


def test_variant_matching_accepts_quote_with_variant_name():
    """Zdanie wymieniające wariant lub jego synonim zostaje zaakceptowane."""
    opt_title = "Jednolity płatnik publiczny (Model budżetowy)"
    opt_id = "public_tax"

    # 1. Dosłowna wzmianka o modelu budżetowym
    quote_1 = "Model budżetowy oparty na podatkach ogólnych generuje koszty administracyjne rzędu 2.1%."
    assert verify_variant_in_quote(quote_1, option_title=opt_title, option_id=opt_id) is True

    # 2. Wzmianka o jednolitym płatniku (synonim)
    quote_2 = "Wprowadzenie jednolitego płatnika publicznego pozwoliło ograniczyć wydatki na obsługę."
    assert verify_variant_in_quote(quote_2, option_title=opt_title, option_id=opt_id) is True

    # 3. Wzmianka o finansowaniu z budżetu państwa
    quote_3 = "Bezpośrednie finansowanie z budżetu państwa stabilizuje przychody szpitali klinicznych."
    assert verify_variant_in_quote(quote_3, option_title=opt_title, option_id=opt_id) is True


def test_variant_matching_rejects_quote_without_variant_name():
    """
    Pozycja 3 Tabeli Odbioru: zdanie bez nazwy wariantu nie wypełnia komórki.
    Ogólny cytat o ochronie zdrowia nie może obsadzić konkretnego wariantu finansowania.
    """
    opt_title = "Model budżetowy (finansowanie z podatków ogólnych)"
    opt_id = "public_tax"

    # Ogólne zdanie o wyzwaniach systemu zdrowotnego bez wymienienia modelu budżetowego
    off_topic_quote = "Głównym wyzwaniem ochrony zdrowia w Polsce pozostają kolejki do lekarzy specjalistów."
    assert verify_variant_in_quote(off_topic_quote, option_title=opt_title, option_id=opt_id) is False

    # Zdanie o innym wariancie (np. ubezpieczeniach społecznych) nie może obsadzić public_tax
    other_variant_quote = "Składka na ubezpieczenie zdrowotne w NFZ wynosi obecnie 9% podstawy wymiaru."
    assert verify_variant_in_quote(other_variant_quote, option_title=opt_title, option_id=opt_id) is False


def test_indistinguishable_variants_give_message_not_ranking():
    """
    Pozycja 5 Tabeli Odbioru: identyczne wartości dają komunikat, nie ranking.
    Gdy dwa warianty w danej dźwigni mają identyczne oceny we wszystkich udokumentowanych kryteriach,
    system nie przedstawia jednego jako lepszego, lecz wstrzymuje ranking i zwraca jawny komunikat.
    """
    levers = [
        DesignLever(
            id="funding_model",
            name="Model finansowania",
            options=[
                LeverOption(id="public_tax", title="Model budżetowy", description=""),
                LeverOption(id="social_insurance", title="Ubezpieczenie społeczne", description=""),
            ],
        ),
    ]
    criteria = [
        DesignCriterion(id="cost_effectiveness", name="Efektywność kosztowa", direction="maximize", weight=1.0),
        DesignCriterion(id="access_to_services", name="Dostępność usług", direction="maximize", weight=1.0),
    ]

    # Oba warianty mają dokładnie identyczne wartości (np. 2.0 i 0.0 jak w audycie V22 §1)
    score_matrix = {
        "funding_model": {
            "public_tax": {
                "cost_effectiveness": ScoredValue(value=2.0, provenance="web_sourced", quote="Cytat A"),
                "access_to_services": ScoredValue(value=0.0, provenance="web_sourced", quote="Cytat B"),
            },
            "social_insurance": {
                "cost_effectiveness": ScoredValue(value=2.0, provenance="web_sourced", quote="Cytat C"),
                "access_to_services": ScoredValue(value=0.0, provenance="web_sourced", quote="Cytat D"),
            },
        },
    }

    dp = DesignProblem(
        id="dp_indistinguishable",
        title="Dylemat reformy finansowania",
        description="Porównanie modelu budżetowego z ubezpieczeniowym",
        levers=levers,
        criteria=criteria,
        score_matrix=score_matrix,
    )

    result = compute_design_synthesis(dp)

    # 1. Ranking musi być wstrzymany
    assert result.ranking_withheld is True
    assert result.insufficient_data is True
    assert result.pareto_frontier == []
    assert result.lever_importance_ranking == []

    # 2. Komunikat o nierozróżnialności wariantów musi wystąpić w wyniku
    assert len(result.indistinguishable_variants) >= 1
    msg = result.practical_manifestation
    assert "nierozróżnialne" in msg.lower() or "nierozróżnialne" in result.briefing.executive_summary.lower()
    assert "Model budżetowy" in result.indistinguishable_variants[0]
    assert "Ubezpieczenie społeczne" in result.indistinguishable_variants[0]


def test_empty_lever_is_excluded_not_blocking(): 
    """
    DEC-048: dźwignia bez danych nie wstrzymuje całego wyniku — wypada z porównania.
    Telemetria nadal podaje udokumentowane/wszystkie komórki oraz puste dźwignie,
    a wynik zostaje oznaczony jako wstępny, bo porównanie objęło tylko część obszarów.
    """
    levers = [
        DesignLever(
            id="l1",
            name="Model finansowania",
            options=[
                LeverOption(id="o1", title="Wariant A", description=""),
                LeverOption(id="o2", title="Wariant B", description=""),
            ],
        ),
        DesignLever(
            id="l2",
            name="Struktura szpitali",
            options=[
                LeverOption(id="o3", title="Konsolidacja", description=""),
                LeverOption(id="o4", title="Autonomia", description=""),
            ],
        ),
    ]
    criteria = [
        DesignCriterion(id="c1", name="Koszty", direction="minimize", weight=1.0),
        DesignCriterion(id="c2", name="Jakość", direction="maximize", weight=1.0),
    ]

    # Tylko dźwignia l1 posiada dane, dźwignia l2 jest całkowicie pusta
    score_matrix = {
        "l1": {
            "o1": {"c1": ScoredValue(value=5.0, provenance="web_sourced"), "c2": ScoredValue(value=8.0, provenance="web_sourced")},
            "o2": {"c1": ScoredValue(value=6.0, provenance="web_sourced"), "c2": ScoredValue(value=7.0, provenance="web_sourced")},
        },
        "l2": {
            "o3": {"c1": ScoredValue(value=None, provenance="unverified"), "c2": ScoredValue(value=None, provenance="unverified")},
            "o4": {"c1": ScoredValue(value=None, provenance="unverified"), "c2": ScoredValue(value=None, provenance="unverified")},
        },
    }

    dp = DesignProblem(
        id="dp_coverage",
        title="Test pokrycia",
        description="Dźwignia l2 pusta",
        levers=levers,
        criteria=criteria,
        score_matrix=score_matrix,
    )

    result = compute_design_synthesis(dp)

    assert result.design_matrix_total_cells == 8
    assert result.design_matrix_documented_cells == 4
    assert result.coverage_percentage == 50.0
    assert result.design_empty_levers == ["Struktura szpitali"]

    # DEC-048: pusta dźwignia wypada z porównania, ale wynik powstaje
    assert result.ranking_withheld is False
    assert result.insufficient_data is False
    assert result.levers_excluded == [{"name": "Struktura szpitali", "reason": "no_data"}]
    assert result.preliminary is True
    assert result.pareto_frontier != []

    # Wykluczony obszar nie może dostać podsuniętego wariantu
    assert "Struktura szpitali" not in result.optimal_titles
    assert "Model finansowania" in result.optimal_titles
    assert all(r["lever_name"] != "Struktura szpitali" for r in result.lever_importance_ranking)
    assert all(p.title != "Struktura szpitali" for p in result.briefing.key_pillars)

    # ...ale musi zostać nazwany wprost w warstwie założeń
    assert any("Struktura szpitali" in a for a in result.unknowns_and_decisive_assumptions)


def test_only_zero_facts_withholds_the_answer():
    """DEC-048: wstrzymanie odpowiedzi zostaje wyłącznie dla braku jakiegokolwiek faktu."""
    levers = [
        DesignLever(
            id="l1",
            name="Model finansowania",
            options=[
                LeverOption(id="o1", title="Wariant A", description=""),
                LeverOption(id="o2", title="Wariant B", description=""),
            ],
        ),
    ]
    criteria = [DesignCriterion(id="c1", name="Koszty", direction="minimize", weight=1.0)]
    dp = DesignProblem(
        id="dp_empty",
        title="Brak danych",
        description="Zero udokumentowanych komórek",
        levers=levers,
        criteria=criteria,
        score_matrix={
            "l1": {
                "o1": {"c1": ScoredValue(value=None, provenance="unverified")},
                "o2": {"c1": ScoredValue(value=None, provenance="unverified")},
            }
        },
    )
    result = compute_design_synthesis(dp)
    assert result.ranking_withheld is True
    assert result.insufficient_data is True
    assert result.preliminary is False


def test_scored_value_unit_normalization():
    """Unit 'null' lub pusty ciąg musi zamieniać się na czyste None."""
    s1 = ScoredValue(value=10.0, unit="null")
    assert s1.unit is None

    s2 = ScoredValue(value=10.0, unit="")
    assert s2.unit is None

    s3 = ScoredValue(value=10.0, unit="   ")
    assert s3.unit is None

    s4 = ScoredValue(value=10.0, unit="%")
    assert s4.unit == "%"
