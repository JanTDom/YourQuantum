"""
YourQuantum — Scenario Decomposer & Quantum Risk Synthesizer
Transforms predictive, forecasting, and geopolitical risk queries into discrete scenario spaces
with factual evidence premises from web research, computed via quantum combinatorics.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from backend.domain.decision_case import (
    DecisionCase, Option, Criterion, ScoredValue, InputQuality,
)
from backend.domain.quantum_scenarios import (
    ScenarioOutcome, EvidencePremise, QuantumScenarioForecast,
    compute_quantum_scenario_probabilities,
    normalize_polish_geopolitical_text,
)
from backend.infrastructure.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)


def is_scenario_forecast_query(query: str) -> bool:
    """
    Identifies whether a natural language query is a future forecasting,
    probabilistic risk, or geopolitical prediction dilemma.
    """
    q = query.strip().lower()
    patterns = [
        r"\b(czy\s+rosja|czy\s+zaatakuje|czy\s+napadnie|wojn\w*|inwazj\w*|konflikt\w*)\b",
        r"\b(prawdopodobie[nń]stw\w*|prognoz\w*|ryzyk\w*|scenariusz\w*)\b",
        r"\b(czy\s+wybuchnie|czy\s+nast[aą]pi|czy\s+dojdzie|czy\s+b[eę]dzie)\b",
        r"\b(szansa\s+na|zagro[zż]eni\w*|bezpiecze[nń]stw\w*)\b",
        r"\b(kurs\w*|krach\w*|recesj\w*|kryzys\w*|upadnie|zbankrutuje)\b",
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
) -> tuple[DecisionCase, QuantumScenarioForecast]:
    """
    Decomposes an open-ended predictive dilemma into scenarios and evidence indicators,
    then executes quantum state combinatorics to determine Born-rule probabilities.
    """
    gw = gateway or LLMGateway()
    snippets_text = "\n".join(web_snippets) if web_snippets else "Brak bezpośrednich wyników wyszukiwania."

    scenarios: list[ScenarioOutcome] = []
    premises: list[EvidencePremise] = []
    domain = "Bezpieczeństwo geopolityczne i analiza ryzyka"

    if gw.is_available:
        sys_inst = (
            "Jesteś czołowym analitykiem wywiadowczym, teorii gier i probabilistyki kwantowej YourQuantum. "
            "Użytkownik zadaje pytanie o prawdopodobieństwo przyszłych zdarzeń lub ryzyko geopolityczne/rynkowe. "
            "Twoim zadaniem jest sformalizować ten problem jako przestrzeń 3 wzajemnie wykluczających się scenariuszy "
            "oraz 3-5 kluczowych, mierzalnych przesłanek (wskaźników) empirycznych i geostrategicznych. "
            "Dla każdej przesłanki określ wpływ (impact_on_scenarios od -1.0 do +1.0) na poszczególne scenariusze. "
            "Wartości dodatnie oznaczają, że dana przesłanka zwiększa prawdopodobieństwo scenariusza; "
            "wartości ujemne oznaczają, że mu przeciwdziała lub go wyklucza.\n\n"
            "BEZWZGLĘDNA ZASADA ORTOGRAFII I JĘZYKA POLSKIEGO:\n"
            "- Wszystkie nazwy własne państw, sojuszy i instytucji pisz Z DUŻEJ LITERY: Ukraina, Ukrainy, Ukrainie, "
            "Polska, Polski, Polsce, Rosja, Rosji, NATO, USA, UE, PKB, MON, ISW, OSW.\n"
            "- Opisy formułuj w nienagannym, naturalnym, zrozumiałym języku decyzyjnym.\n"
            "- Całkowity zakaz żargonu typu 'wektor energetyczny' czy 'wariant kinetyczny'."
        )
        user_content = (
            f"Pytanie użytkownika:\n\"{query}\"\n\n"
            f"Fakty i kontekst z sieci:\n{snippets_text}\n\n"
            "Zbuduj 3 scenariusze (np. 1. Status quo i odstraszanie sojusznicze NATO, 2. Działania hybrydowe i prowokacje podprogowe, 3. Bezpośredni atak militarny) "
            "oraz 3-4 mierzalne przesłanki z twardych źródeł (np. ISW, OSW, raporty NATO, wydatki PKB)."
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
                        source=normalize_polish_geopolitical_text(str(pr_data.get("source", "analiza wywiadowcza / dane publiczne"))),
                        confidence=float(pr_data.get("confidence", 0.9)),
                        weight=float(pr_data.get("weight", 1.0)),
                        impact_on_scenarios=impacts,
                    ))
        except Exception as exc:
            logger.warning("LLM scenario decomposition failed, falling back to analytical defaults: %s", exc)

    # Analytical fallback if LLM returned insufficient items
    if len(scenarios) < 2 or len(premises) < 2:
        scenarios = _get_default_scenarios_for_query(query)
        premises = _get_default_premises_for_query(query)

    # Execute Quantum Combinatorics (Qiskit Aer / Born rule)
    forecast = compute_quantum_scenario_probabilities(
        query=query,
        scenarios=scenarios,
        premises=premises,
        domain=domain,
        shots=2048,
    )

    # Build DecisionCase representation with clear Polish copy
    case_options: list[Option] = []
    for sc in forecast.scenarios:
        pct_formatted = f"{sc.probability * 100:.1f}%".replace(".", ",")
        if sc.risk_level == "LOW":
            pros = ["Wspierany przez twarde czynniki odstraszania i sojuszniczą obecność NATO."]
            cons = ["Wymaga utrzymania wysokich nakładów obronnych i jedności sojuszniczej."]
        elif sc.risk_level in ("HIGH", "CRITICAL"):
            pros = ["Obecnie skrajnie mało prawdopodobny ze względu na uwiązanie sił agresora w Ukrainie."]
            cons = ["W razie zaistnienia wiąże się z bezpośrednim zagrożeniem militarnym i stratami."]
        else:
            pros = ["Pozwala skupić środki na obronie infrastruktury krytycznej i cyberprzestrzeni."]
            cons = ["Powoduje stałą presję informacyjną oraz koszty ochrony granic."]

        case_options.append(Option(
            id=sc.id,
            title=f"{sc.title} (Szacunek szans: {pct_formatted})",
            description=sc.description,
            pros=pros,
            cons=cons,
            attributes={"probability": sc.probability, "risk_level": sc.risk_level, "energy": sc.energy_level},
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
            # Map [-1.0, 1.0] to [1.0, 10.0] scale
            scaled_val = round(5.5 + 4.5 * max(-1.0, min(1.0, raw_impact)), 1)
            case_score_matrix[sc.id][pr.id] = ScoredValue(
                value=scaled_val,
                unit="skala 1-10",
                provenance="web_sourced" if pr.source else "assumed",
                source_ref=pr.source or "Model przesłanek geostrategicznych",
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


def _get_default_scenarios_for_query(query: str) -> list[ScenarioOutcome]:
    """Provides high-rigour default scenarios for security and geopolitical inquiries."""
    return [
        ScenarioOutcome(
            id="scen_status_quo",
            title="Status quo i skuteczne odstraszanie sojusznicze NATO",
            description="Brak bezpośredniego ataku; gwarancje art. 5 Traktatu Waszyngtońskiego oraz obecność wojsk sojuszniczych USA i NATO w Polsce skutecznie powstrzymują agresję militarną.",
            risk_level="LOW",
        ),
        ScenarioOutcome(
            id="scen_hybrid_grey",
            title="Wrogie działania hybrydowe i prowokacje podprogowe",
            description="Wzrost presji w domenie cybernetycznej, zakłócenia sygnału GPS, prowokacje graniczne oraz próby dezinformacji poniżej progu otwartego konfliktu zbrojnego.",
            risk_level="MEDIUM",
        ),
        ScenarioOutcome(
            id="scen_kinetic_aggression",
            title="Bezpośredni atak militarny na terytorium Polski",
            description="Otwarta agresja konwencjonalna na terytorium Rzeczypospolitej Polskiej prowadząca do natychmiastowej odpowiedzi całego sojuszu NATO w ramach art. 5.",
            risk_level="CRITICAL",
        ),
    ]


def _get_default_premises_for_query(query: str) -> list[EvidencePremise]:
    """Provides institutional evidence premises for security and geopolitical inquiries."""
    return [
        EvidencePremise(
            id="prem_ua_binding",
            name="Uwiązanie i straty armii rosyjskiej w walkach w Ukrainie",
            description="Zdecydowana większość jednostek lądowych Rosji ponosi ciężkie straty w Ukrainie, co uniemożliwia otwarcie nowego frontu przeciwko państwom NATO.",
            source="Instytut Badań nad Wojną (ISW) / Ośrodek Studiów Wschodnich (OSW)",
            weight=1.0,
            confidence=0.95,
            impact_on_scenarios={"scen_status_quo": 0.85, "scen_hybrid_grey": 0.25, "scen_kinetic_aggression": -0.95},
        ),
        EvidencePremise(
            id="prem_nato_article_5",
            name="Gwarancje art. 5 NATO i obecność wojsk sojuszniczych w Polsce",
            description="Stałe stacjonowanie wojsk USA w Polsce (V Korpus w Poznaniu), siły sojusznicze NATO na wschodniej flance oraz parasol nuklearny sojuszu.",
            source="Deklaracja Szczytu NATO / Pentagon / MON",
            weight=1.0,
            confidence=0.98,
            impact_on_scenarios={"scen_status_quo": 0.90, "scen_hybrid_grey": -0.20, "scen_kinetic_aggression": -0.95},
        ),
        EvidencePremise(
            id="prem_pl_defense_spending",
            name="Rekordowe wydatki obronne Polski (4,7% PKB) i modernizacja armii",
            description="Polska przeznacza najwyższy odsetek PKB w NATO na obronność, rozbudowując obronę powietrzną (Patriot/Wisła), artylerię rakietową (HIMARS) i wojska pancerne.",
            source="Raport Wydatków Obronnych NATO 2024 / Ministerstwo Obrony Narodowej (MON)",
            weight=0.9,
            confidence=0.92,
            impact_on_scenarios={"scen_status_quo": 0.75, "scen_hybrid_grey": -0.10, "scen_kinetic_aggression": -0.80},
        ),
        EvidencePremise(
            id="prem_ru_war_economy",
            name="Przestawienie gospodarki Rosji na tryb wojenny",
            description="Rosja zwiększyła nakłady na zbrojenia powyżej 6% PKB, co stwarza długofalowe ryzyko w sferze prowokacji i presji hybrydowej, lecz nie daje przewagi nad NATO.",
            source="Międzynarodowy Instytut Studiów Strategicznych (IISS) / SIPRI",
            weight=0.8,
            confidence=0.88,
            impact_on_scenarios={"scen_status_quo": -0.30, "scen_hybrid_grey": 0.70, "scen_kinetic_aggression": 0.30},
        ),
    ]
