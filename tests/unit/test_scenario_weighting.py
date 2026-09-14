"""
Unit tests for Honest Scenario Weighting Engine (Prompt V5 / Fable 5.1).
Validates weighted softmax distribution, sensitivity bands, provenance rules,
analytical tipping points, verbal accuracy, strict routing, and zero Qiskit imports.
"""
from __future__ import annotations

import pathlib
import pytest
from unittest.mock import MagicMock

from backend.domain.scenario_weighting import (
    ScenarioOutcome,
    EvidencePremise,
    compute_scenario_distribution,
    compute_tipping_points,
    format_chance_description,
)
from backend.domain.cognitive.scenario_decomposer import (
    is_scenario_forecast_query,
    decompose_scenario_query_async,
)
from backend.infrastructure.llm_gateway import LLMGateway


def test_1_llm_suggested_premise_does_not_affect_distribution_until_accepted():
    """
    Case 1: Premise with provenance='llm_suggested' and is_accepted=False
    must NOT affect the distribution; once accepted, it must affect the distribution.
    """
    scenarios = [
        ScenarioOutcome(id="s1", title="Scenariusz A (Wzrost)", risk_level="LOW"),
        ScenarioOutcome(id="s2", title="Scenariusz B (Recesja)", risk_level="HIGH"),
    ]

    p1_accepted = EvidencePremise(
        id="p1",
        name="Wzrost inwestycji i zamówień przemysłowych",
        impact_on_scenarios={"s1": 1.0, "s2": -1.0},
        weight=1.5,
        confidence=0.9,
        provenance="user_supplied",
        is_accepted=True,
    )

    p2_unaccepted_llm = EvidencePremise(
        id="p2",
        name="Sygnały kryzysu płynnościowego w sektorze",
        impact_on_scenarios={"s1": -2.0, "s2": 2.0},
        weight=2.0,
        confidence=0.95,
        provenance="llm_suggested",
        is_accepted=False,
    )

    # 1. Without acceptance of p2: only p1 counts -> s1 dominates
    forecast_unaccepted = compute_scenario_distribution(
        query="Prognoza rozwoju koniunktury gospodarczej",
        scenarios=[sc.model_copy() for sc in scenarios],
        premises=[p1_accepted, p2_unaccepted_llm],
        beta=1.0,
    )
    assert forecast_unaccepted.dominant_scenario_id == "s1"
    s1_prob_before = next(s.probability for s in forecast_unaccepted.scenarios if s.id == "s1")
    s2_prob_before = next(s.probability for s in forecast_unaccepted.scenarios if s.id == "s2")
    assert s1_prob_before > s2_prob_before

    # 2. Accept p2 -> now p2 enters calculation with large weight -> s2 must dominate
    p2_accepted = p2_unaccepted_llm.model_copy(update={"is_accepted": True})
    forecast_accepted = compute_scenario_distribution(
        query="Prognoza rozwoju koniunktury gospodarczej",
        scenarios=[sc.model_copy() for sc in scenarios],
        premises=[p1_accepted, p2_accepted],
        beta=1.0,
    )
    assert forecast_accepted.dominant_scenario_id == "s2"
    s1_prob_after = next(s.probability for s in forecast_accepted.scenarios if s.id == "s1")
    s2_prob_after = next(s.probability for s in forecast_accepted.scenarios if s.id == "s2")
    assert s2_prob_after > s1_prob_after


def test_2_empty_premises_requires_clarification_no_geopolitical_defaults():
    """
    Case 2: If premises list is empty, function does not return a distribution
    but raises ValueError (demanding data); no default premises about Russia/NATO/GDP appear.
    """
    scenarios = [
        ScenarioOutcome(id="s1", title="Wariant 1", risk_level="LOW"),
        ScenarioOutcome(id="s2", title="Wariant 2", risk_level="HIGH"),
    ]

    with pytest.raises(ValueError, match="Brak przesłanek do obliczenia rozkładu"):
        compute_scenario_distribution(
            query="Jak potoczy się sytuacja?",
            scenarios=scenarios,
            premises=[],
        )

    # Also test decompose_scenario_query_async fallback when LLM is unavailable
    import asyncio
    mock_gw = MagicMock(spec=LLMGateway)
    mock_gw.is_available = False

    case, forecast = asyncio.run(decompose_scenario_query_async(
        query="Czy warto otworzyć nową kawiarnię w centrum?",
        gateway=mock_gw,
    ))

    # Must require user input, not inject Russia/NATO/4.7% GDP
    assert case.input_quality.level == "too_vague"
    all_premise_text = " ".join([p.name + " " + p.description for p in forecast.evidence_premises]).lower()
    assert "rosj" not in all_premise_text
    assert "nato" not in all_premise_text
    assert "4,7% pkb" not in all_premise_text


def test_3_sensitivity_band_contains_four_betas_and_varies_distinctly():
    """
    Case 3: sensitivity_band must contain {beta_0.5, beta_1.0, beta_2.0, beta_3.0}
    and the resulting probability distributions must strictly vary with beta.
    """
    scenarios = [
        ScenarioOutcome(id="s1", title="Scenariusz A", risk_level="LOW"),
        ScenarioOutcome(id="s2", title="Scenariusz B", risk_level="MEDIUM"),
    ]
    premises = [
        EvidencePremise(
            id="p1",
            name="Stabilne wsparcie instytucjonalne",
            impact_on_scenarios={"s1": 1.0, "s2": -0.5},
            weight=1.2,
            confidence=0.9,
            provenance="user_supplied",
            is_accepted=True,
        ),
    ]

    forecast = compute_scenario_distribution(
        query="Badanie wrażliwości scenariuszy",
        scenarios=scenarios,
        premises=premises,
        beta=1.0,
    )

    band = forecast.sensitivity_band
    assert "beta_0.5" in band
    assert "beta_1.0" in band
    assert "beta_2.0" in band
    assert "beta_3.0" in band

    p_05 = band["beta_0.5"]["s1"]
    p_10 = band["beta_1.0"]["s1"]
    p_20 = band["beta_2.0"]["s1"]
    p_30 = band["beta_3.0"]["s1"]

    # Dominant scenario probability strictly increases as beta sharpens the distribution
    assert p_05 < p_10 < p_20 < p_30
    assert pytest.approx(sum(band["beta_1.0"].values()), abs=1e-3) == 1.0


def test_4_compute_tipping_points_analytical_accuracy():
    """
    Case 4: compute_tipping_points returns exact minimal weight delta required
    to flip dominance between dominant and runner-up scenarios.
    """
    s1 = ScenarioOutcome(id="s1", title="Faworyt", risk_level="LOW", evidence_score=2.0)
    s2 = ScenarioOutcome(id="s2", title="Pretendent", risk_level="HIGH", evidence_score=0.0)

    # p1 supports s1 over s2: impact_s1 = 1.0, impact_s2 = 0.0 -> net_coupling = 1.0 * confidence = 1.0
    # Score gap = 2.0 - 0.0 = 2.0. Needed reduction in p1 weight = 2.0 / 1.0 = 2.0.
    p1 = EvidencePremise(
        id="p1",
        name="Kluczowy atut faworyta",
        impact_on_scenarios={"s1": 1.0, "s2": 0.0},
        weight=2.0,
        confidence=1.0,
        provenance="user_supplied",
        is_accepted=True,
    )

    texts, items = compute_tipping_points([s1, s2], [p1], beta=1.0)
    assert len(items) == 1
    item = items[0]
    assert item.premise_id == "p1"
    assert item.direction == "decrease"
    assert pytest.approx(item.delta_weight_needed, abs=0.05) == 2.0
    assert "Zmniejszenie wagi" in item.explanation


def test_5_verbal_chance_description_mathematical_consistency():
    """
    Case 5: Verbal description must not label 80% as 'over 95 in 100'.
    0.80 must produce 'wysokie prawdopodobieństwo (ok. 80–94 szans na 100)'.
    0.96 must produce 'ponad 95 szans na 100'.
    """
    desc_80 = format_chance_description(0.80)
    assert "ponad 95" not in desc_80
    assert "80" in desc_80 or "wysokie" in desc_80

    desc_96 = format_chance_description(0.96)
    assert "ponad 95 szans na 100" in desc_96

    desc_50 = format_chance_description(0.50)
    assert "połowa" in desc_50 or "umiarkowanie" in desc_50


def test_6_routing_eight_queries_strictness():
    """
    Case 6: Routing test on the 8 queries from prompt section 1.6.
    All 8 standard decision inquiries must NOT be classified as scenario forecasting!
    Explicit invasion / scenario forecasting inquiries MUST be classified as True.
    """
    test_queries_must_be_false = [
        "Czy będzie mi się opłacało zmienić pracę na etat w korporacji?",
        "Jakie jest ryzyko, że nie zdążę z projektem do marca?",
        "Czy będzie lepiej wynająć biuro czy pracować zdalnie?",
        "Wybór kursu językowego: hiszpański czy włoski?",
        "Czy dojdzie do porozumienia z kontrahentem, jeśli ustąpię w cenie?",
        "Zmiana dostawcy energii – który scenariusz cenowy wybrać?",
        "Które z dwóch mieszkań kupić?",
        "Który wariant umowy jest bezpieczniejszy dla mojej firmy?",
    ]

    for q in test_queries_must_be_false:
        assert not is_scenario_forecast_query(q), f"Query wrongly classified as scenario forecast: '{q}'"

    test_queries_must_be_true = [
        "Czy Rosja zaatakuje kraje bałtyckie lub Polskę?",
        "Czy wybuchnie wojna w Europie w najbliższych latach?",
        "Analiza scenariuszowa rozwoju sytuacji geopolitycznej",
        "Scenariusze rozwoju kryzysu na wschodniej granicy",
    ]

    for q in test_queries_must_be_true:
        assert is_scenario_forecast_query(q), f"Query failed to be classified as scenario forecast: '{q}'"


def test_7_zero_qiskit_imports_in_scenario_weighting():
    """
    Case 7: Verifies that backend/domain/scenario_weighting.py contains ZERO
    imports of Qiskit or AerSimulator and zero pseudo-quantum metaphors.
    """
    module_path = pathlib.Path(__file__).resolve().parent.parent.parent / "backend" / "domain" / "scenario_weighting.py"
    assert module_path.exists(), f"File {module_path} does not exist"

    code = module_path.read_text(encoding="utf-8")
    code_lower = code.lower()

    assert "import qiskit" not in code_lower
    assert "from qiskit" not in code_lower
    assert "aersimulator" not in code
    assert "quantumcircuit" not in code
    assert "statevector" not in code_lower
    assert "amplitude_real" not in code
    assert "amplitude_imag" not in code
    assert "born_rule" not in code_lower
