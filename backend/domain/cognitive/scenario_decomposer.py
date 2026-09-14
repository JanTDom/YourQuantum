"""
YourQuantum — Scenario Decomposer & Evidence Synthesizer
Transforms predictive, forecasting, and scenario risk queries into discrete scenario spaces
with auditable evidence premises, computed via weighted softmax evidence aggregation.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from backend.domain.decision_case import (
    DecisionCase, Option, Criterion, ScoredValue, InputQuality,
)
from backend.domain.scenario_weighting import (
    ScenarioOutcome, EvidencePremise, ScenarioForecast,
    compute_scenario_distribution,
    normalize_polish_geopolitical_text,
)
from backend.domain.problem_classes import ExecutiveBriefing
from backend.infrastructure.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)


def is_scenario_forecast_query(query: str) -> bool:
    """
    Identifies whether a natural language query specifically requests
    future scenario forecasting or geopolitical event prediction.
    Does NOT match standard decision dilemmas (e.g. changing jobs, renting offices,
    choosing courses, selecting pricing plans, or assessing general project risks).
    """
    q = query.strip().lower()
    patterns = [
        # Explicit geopolitical invasion / military aggression queries
        r"\b(czy\s+rosja\s+(zaatakuje|napadnie)|wojn\w*\s+w\s+europ|wybuch\w*\s+wojn\w*|inwazj\w*\s+militarn|atak\s+militarn)\b",
        # Explicit scenario analysis requests
        r"\b(analiz\w*\s+scenariusz\w*|scenariusz\w*\s+rozwoju|warianty\s+rozwoju\s+sytuacji|prognoz\w*\s+scenariusz)\b",
        # Macro crisis / collapse forecasts (not everyday personal choices)
        r"\b(krach\s+rynk\w*|krach\s+finansow\w*|wybuch\s+kryzysu\s+globaln)\b",
    ]
    return any(bool(re.search(p, q)) for p in patterns)


SCENARIO_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "domain": {"type": "string"},
        "scenarios": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                },
                "required": ["id", "title", "description", "risk_level"],
            },
        },
        "premises": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "source": {"type": "string"},
                    "weight": {"type": "number"},
                    "confidence": {"type": "number"},
                    "impact_on_scenarios": {
                        "type": "object",
                        "additionalProperties": {"type": "number"}
                    }
                },
                "required": ["id", "name", "description", "weight", "impact_on_scenarios"],
            },
        },
    },
    "required": ["scenarios", "premises"],
}


async def decompose_scenario_query_async(
    query: str,
    web_snippets: list[str] | None = None,
    gateway: LLMGateway | None = None,
) -> tuple[DecisionCase, ScenarioForecast]:
    """
    Decomposes a scenario forecasting dilemma into distinct scenarios and evidence indicators,
    then executes weighted softmax aggregation with sensitivity analysis.
    All model-proposed premises are flagged with provenance='llm_suggested' and require
    user confirmation before entering calculation.
    """
    gw = gateway or LLMGateway()
    snippets_text = "\n".join(web_snippets) if web_snippets else "Brak bezpośrednich wyników wyszukiwania."

    scenarios: list[ScenarioOutcome] = []
    premises: list[EvidencePremise] = []
    domain = "Analiza scenariuszowa i badanie ryzyka"

    if gw.is_available:
        sys_inst = (
            "Jesteś precyzyjnym analitykiem metodologii scenariuszowej i probabilistyki w YourQuantum. "
            "Użytkownik zadaje pytanie o scenariusze rozwoju sytuacji lub ryzyko zdarzeń w przyszłości. "
            "Twoim zadaniem jest sformalizować ten dylemat jako przestrzeń 2-4 wzajemnie wykluczających się scenariuszy "
            "oraz 3-5 kluczowych przesłanek (wskaźników) empirycznych powiązanych ze sprawą. "
            "Dla każdej przesłanki określ wpływ (impact_on_scenarios od -1.0 do +1.0) na poszczególne scenariusze. "
            "Wartości dodatnie oznaczają, że dana przesłanka zwiększa szansę scenariusza; "
            "wartości ujemne oznaczają, że mu przeciwdziała lub go wyklucza.\n\n"
            "BEZWZGLĘDNA ZASADA ORTOGRAFII I JĘZYKA POLSKIEGO:\n"
            "- Wszystkie nazwy własne państw, sojuszy i instytucji pisz Z DUŻEJ LITERY (np. Polska, Ukraina, NATO, USA, UE).\n"
            "- Opisy formułuj w nienagannym, obiektywnym języku analitycznym.\n"
            "- Zakaz jakiegokolwiek żargonu pseudokwantowego (amplitudy, wektory stanów, fale)."
        )
        user_content = (
            f"Pytanie użytkownika:\n\"{query}\"\n\n"
            f"Kontekst i fakty z sieci:\n{snippets_text}\n\n"
            "Zbuduj 2-3 konkretne, wykluczające się scenariusze oraz 3-4 mierzalne przesłanki z ich wpływem na scenariusze."
        )
        try:
            res = await gw.generate(
                system_instruction=sys_inst,
                user_content=user_content,
                purpose="decompose_scenario_risk",
                response_schema=SCENARIO_EXTRACTION_SCHEMA,
                temperature=0.1,
            )
            if res.parsed_json and isinstance(res.parsed_json, dict):
                p_json = res.parsed_json
                domain = normalize_polish_geopolitical_text(p_json.get("domain", domain))
                for sc_data in p_json.get("scenarios", []):
                    scenarios.append(ScenarioOutcome(
                        id=str(sc_data["id"]),
                        title=normalize_polish_geopolitical_text(str(sc_data["title"])),
                        description=normalize_polish_geopolitical_text(str(sc_data.get("description", ""))),
                        risk_level=sc_data.get("risk_level", "MEDIUM"),
                    ))
                for pr_data in p_json.get("premises", []):
                    raw_impacts = pr_data.get("impact_on_scenarios", {})
                    impacts = {str(k): float(v) for k, v in raw_impacts.items()}
                    premises.append(EvidencePremise(
                        id=str(pr_data["id"]),
                        name=normalize_polish_geopolitical_text(str(pr_data["name"])),
                        description=normalize_polish_geopolitical_text(str(pr_data.get("description", ""))),
                        source=normalize_polish_geopolitical_text(str(pr_data.get("source", "propozycja modelu LLM"))),
                        confidence=float(pr_data.get("confidence", 0.85)),
                        weight=float(pr_data.get("weight", 1.0)),
                        impact_on_scenarios=impacts,
                        provenance="llm_suggested",
                        source_ref=str(pr_data.get("source", "propozycja modelu")),
                        is_accepted=False,
                    ))
        except Exception as exc:
            logger.warning("LLM scenario decomposition failed: %s", exc)

    # If insufficient items, do NOT inject invented geopolitical numbers.
    # Return empty case requiring user definition.
    if len(scenarios) < 2 or not premises:
        case = DecisionCase(
            title=f"Analiza scenariuszowa: {query}",
            context=query,
            options=[],
            criteria=[],
            score_matrix={},
            input_quality=InputQuality(
                level="too_vague",
                reason="Brak zdefiniowanych scenariuszy lub przesłanek do przeprowadzenia analizy.",
                suggestions=[
                    "Zdefiniuj co najmniej dwa wykluczające się scenariusze rozwoju sytuacji.",
                    "Wprowadź kluczowe przesłanki (fakty, wskaźniki) i określ ich wpływ na poszczególne scenariusze.",
                ],
            ),
            unknowns=[],
            facts=[],
        )
        empty_briefing = ExecutiveBriefing(
            headline="Wymagane zdefiniowanie scenariuszy i przesłanek",
            executive_summary="System wymaga podania scenariuszy i przesłanek decydenta przed obliczeniem rozkładu prawdopodobieństwa.",
            key_pillars=[],
            primary_tradeoff="Brak przesłanek uniemożliwia wyznaczenie kompromisu.",
            tipping_points=["Brak przesłanek do wyznaczenia punktów zwrotnych."],
        )
        forecast = ScenarioForecast(
            query=query,
            domain=domain,
            scenarios=[],
            dominant_scenario_id="",
            evidence_premises=[],
            tipping_points=["Brak przesłanek do wyznaczenia punktów zwrotnych."],
            tipping_point_details=[],
            sensitivity_band={},
            telemetry={"method": "weighted_softmax_aggregation", "beta": 1.0, "n_scenarios": 0, "n_premises": 0},
            briefing=empty_briefing,
        )
        return case, forecast

    # Compute scenario distribution using honest weighted softmax
    forecast = compute_scenario_distribution(
        query=query,
        scenarios=scenarios,
        premises=premises,
        domain=domain,
        beta=1.0,
    )

    # Build DecisionCase representation
    case_options: list[Option] = []
    for sc in forecast.scenarios:
        pct_formatted = f"{sc.probability * 100:.1f}%".replace(".", ",")
        if sc.risk_level == "LOW":
            pros = ["Wariant o niskim poziomie ryzyka, wspierany przez stabilizujące wskaźniki."]
            cons = ["Wymaga utrzymania warunków brzegowych i założeń decydenta."]
        elif sc.risk_level in ("HIGH", "CRITICAL"):
            pros = ["Scenariusz skrajny; pozwala przygotować plany awaryjne."]
            cons = ["Wiąże się z wysokim ryzykiem niepowodzenia lub strat."]
        else:
            pros = ["Scenariusz pośredni / umiarkowany."]
            cons = ["Generuje niepewność co do ostatecznego kierunku rozwoju sytuacji."]

        case_options.append(Option(
            id=sc.id,
            title=f"{sc.title} (Szacunek szans: {pct_formatted})",
            description=sc.description,
            pros=pros,
            cons=cons,
            attributes={"probability": sc.probability, "risk_level": sc.risk_level, "evidence_score": sc.evidence_score},
        ))

    case_criteria: list[Criterion] = []
    for pr in forecast.evidence_premises:
        case_criteria.append(Criterion(
            id=pr.id,
            name=pr.name,
            weight=pr.weight,
            direction="maximize",
            unit="wpływ",
        ))

    case_score_matrix: dict[str, dict[str, ScoredValue]] = {}
    for sc in forecast.scenarios:
        case_score_matrix[sc.id] = {}
        for pr in forecast.evidence_premises:
            raw_impact = pr.impact_on_scenarios.get(sc.id, 0.0)
            scaled_val = round(5.5 + 4.5 * max(-1.0, min(1.0, raw_impact)), 1)
            case_score_matrix[sc.id][pr.id] = ScoredValue(
                value=scaled_val,
                unit="skala 1-10",
                provenance=pr.provenance,
                source_ref=pr.source or "Propozycja modelu decyzyjnego",
                confidence=pr.confidence,
            )

    case = DecisionCase(
        title=f"Analiza scenariuszy ryzyka: {query}",
        context=query,
        options=case_options,
        criteria=case_criteria,
        score_matrix=case_score_matrix,
        input_quality=InputQuality(level="sufficient"),
        unknowns=[],
        facts=[],
    )

    return case, forecast
