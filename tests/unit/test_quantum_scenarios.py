"""
Unit tests for Quantum Scenario & Probabilistic Risk Engine.
Validates Born-rule probabilities, state amplitudes, and scenario decomposition.
"""
import pytest
from backend.domain.quantum_scenarios import (
    ScenarioOutcome,
    EvidencePremise,
    compute_quantum_scenario_probabilities,
)
from backend.domain.cognitive.scenario_decomposer import (
    is_scenario_forecast_query,
    decompose_scenario_query_async,
)


def test_is_scenario_forecast_query_detection():
    # Geopolitical and predictive triggers
    assert is_scenario_forecast_query("Czy Rosja napadnie w najbliższym czasie na Polskę?")
    assert is_scenario_forecast_query("Czy wybuchnie wojna w Europie?")
    assert is_scenario_forecast_query("Jakie jest prawdopodobieństwo eskalacji konfliktu?")
    assert is_scenario_forecast_query("Czy nastąpi krach na rynku nieruchomości?")
    assert is_scenario_forecast_query("Jakie jest ryzyko recesji w 2026 roku?")

    # Standard choice dilemmas (not scenario forecast)
    assert not is_scenario_forecast_query("Zmienić pracę na korporację czy zostać w startupie?")
    assert not is_scenario_forecast_query("Wybór między ofertą A a ofertą B")


def test_quantum_scenario_probabilities_born_rule_normalization():
    scenarios = [
        ScenarioOutcome(id="s1", title="Status Quo / Odstraszanie", risk_level="LOW"),
        ScenarioOutcome(id="s2", title="Eskalacja podprogowa", risk_level="MEDIUM"),
        ScenarioOutcome(id="s3", title="Bezpośredni atak kinetyczny", risk_level="HIGH"),
    ]
    premises = [
        EvidencePremise(
            id="p1",
            name="Uwiązanie sił agresora w Ukrainie",
            impact_on_scenarios={"s1": 0.85, "s2": 0.2, "s3": -0.95},
            weight=1.0,
            confidence=0.95,
        ),
        EvidencePremise(
            id="p2",
            name="Wiarygodność art. 5 NATO",
            impact_on_scenarios={"s1": 0.90, "s2": -0.2, "s3": -0.95},
            weight=1.0,
            confidence=0.98,
        ),
    ]

    forecast = compute_quantum_scenario_probabilities(
        query="Czy nastąpi bezpośredni atak na terytorium RP?",
        scenarios=scenarios,
        premises=premises,
        shots=2048,
    )

    # 1. Total probability must sum to 1.0 (within numerical precision)
    total_prob = sum(s.probability for s in forecast.scenarios)
    assert pytest.approx(total_prob, abs=0.01) == 1.0

    # 2. Dominant scenario must be s1 (Status Quo) due to strong deterrence evidence
    assert forecast.dominant_scenario_id == "s1"
    assert forecast.scenarios[0].id == "s1"
    assert forecast.scenarios[0].probability > 0.80

    # 3. Born rule amplitude check: P(s) = |alpha|^2
    for s in forecast.scenarios:
        computed_p = s.amplitude_real ** 2 + s.amplitude_imag ** 2
        assert pytest.approx(computed_p, abs=0.02) == s.probability

    # 4. Executive briefing generated
    assert forecast.briefing is not None
    assert len(forecast.briefing.key_pillars) > 0
    assert len(forecast.tipping_points) > 0
    assert "aer_simulator" in forecast.quantum_telemetry.get("backend", "") or "classical_born" in forecast.quantum_telemetry.get("backend", "")


from unittest.mock import AsyncMock, MagicMock
from backend.infrastructure.llm_gateway import LLMGateway, LLMResponse, LLMCallTelemetry


@pytest.mark.asyncio
async def test_decompose_scenario_query_async_fallback():
    mock_gw = MagicMock(spec=LLMGateway)
    mock_gw.is_available = False

    case, forecast = await decompose_scenario_query_async(
        query="Czy Rosja zaatakuje kraje bałtyckie lub Polskę?",
        gateway=mock_gw,
    )

    assert len(case.options) >= 2
    assert len(case.criteria) >= 2
    assert forecast.dominant_scenario_id in [s.id for s in forecast.scenarios]
    assert forecast.briefing.headline != ""
    assert len(case.score_matrix) > 0


@pytest.mark.asyncio
async def test_decompose_scenario_query_async_with_mock_llm():
    mock_gw = MagicMock(spec=LLMGateway)
    mock_gw.is_available = True
    mock_gw.generate = AsyncMock(return_value=LLMResponse(
        text="",
        telemetry=LLMCallTelemetry(model="gemini-2.5-flash"),
        parsed_json={
            "domain": "Geopolityka Bałtycka",
            "scenarios": [
                {"id": "sc1", "title": "Scenariusz 1: Odstraszanie", "description": "Opis 1", "risk_level": "LOW"},
                {"id": "sc2", "title": "Scenariusz 2: Presja", "description": "Opis 2", "risk_level": "HIGH"},
            ],
            "premises": [
                {
                    "id": "pr1",
                    "name": "Przesłanka 1",
                    "description": "Opis pr 1",
                    "source": "Raport X",
                    "weight": 1.0,
                    "confidence": 0.9,
                    "impact_on_scenarios": {"sc1": 0.8, "sc2": -0.8},
                },
                {
                    "id": "pr2",
                    "name": "Przesłanka 2",
                    "description": "Opis pr 2",
                    "source": "Raport Y",
                    "weight": 1.0,
                    "confidence": 0.9,
                    "impact_on_scenarios": {"sc1": 0.7, "sc2": -0.5},
                },
            ],
        }
    ))

    case, forecast = await decompose_scenario_query_async(
        query="Czy Rosja zaatakuje kraje bałtyckie lub Polskę?",
        gateway=mock_gw,
    )

    assert len(case.options) == 2
    assert len(case.criteria) == 2
    assert forecast.dominant_scenario_id == "sc1"



