"""
YourQuantum — Scenario Decomposer & Evidence Synthesizer
Transforms predictive, forecasting, and scenario risk queries into discrete scenario spaces
with auditable evidence premises, computed via weighted softmax evidence aggregation.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from backend.domain.decision_case import DecisionCase, Option, Criterion, ScoredValue, InputQuality
from backend.domain.evidence.models import Evidence
from backend.domain.evidence.evidence_weighting import compute_evidence_weight
from backend.domain.scenario_weighting import (
    ScenarioOutcome, EvidencePremise, ScenarioForecast,
    compute_scenario_distribution,
    normalize_polish_geopolitical_text,
)
from backend.domain.problem_classes import ExecutiveBriefing
from backend.domain.cognitive.time_horizon import detect_time_horizon
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

    # Exclude everyday commercial/personal choice queries that happen to mention pricing, courses, jobs, or contracts
    if re.search(r"\b(scenariusz\s+cenow|który\s+scenariusz\s+cenowy\s+wybrać|zmienić\s+pracę|wynająć\s+biuro|wybór\s+kursu|kontrahent|mieszkań\s+kupić|umowy|projekt\s+do\s+marca)\b", q):
        return False

    patterns = [
        # Geopolitical / military attack & invasion queries with intervening timeframes or modifiers
        # e.g. "Czy Rosja w najbliższym roku napadnie na Polskę?", "Czy Rosja zaatakuje kraje bałtyckie?", "Czy Putin uderzy na NATO?"
        r"\b(czy|kiedy|jak)\b.*?\b(rosj\w*|rosyjsk\w*|putin\w*|chin\w*|białoruś\w*|nato|iran\w*)\b.*?\b(zaatakuj\w*|napadn\w*|napaś\w*|uderzy\w*|wkroczy\w*|dokona\w*\s+inwazji|rozpocznie\s+wojn\w*)\b",
        # Reverse order: "Czy dojdzie do ataku Rosji...", "Czy grozi inwazja ze strony Rosji..."
        r"\b(czy|kiedy|jak|grozi)\b.*?\b(zaatakuj\w*|napadn\w*|napaś\w*|inwazj\w*|uderzen\w*|agresj\w*|atak\w*|wojn\w*)\b.*?\b(rosj\w*|rosyjsk\w*|putin\w*|chin\w*|nato)\b",
        # War outbreak queries
        r"\b(wybuch\w*\s+wojn\w*|wojn\w*\s+w\s+europ\w*|wojn\w*\s+z\s+rosj\w*|inwazj\w*\s+militarn\w*|atak\s+militarn\w*|agresj\w*\s+zbrojn\w*|konflikt\s+zbrojn\w*)\b",
        r"\b(czy\s+wybuchnie\s+wojna|czy\s+będzie\s+wojna|czy\s+grozi\s+nam\s+wojna)\b",
        # Explicit scenario analysis requests
        r"\b(analiz\w*\s+scenariusz\w*|scenariusz\w*\s+rozwoju|warianty\s+rozwoju\s+sytuacji|prognoz\w*\s+scenariusz\w*)\b",
        # Macro crisis / collapse forecasts
        r"\b(krach\s+rynk\w*|krach\s+finansow\w*|wybuch\s+kryzysu\s+globaln\w*)\b",
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
                    "impacts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "scenario_id": {"type": "string"},
                                "impact": {"type": "number"}
                            },
                            "required": ["scenario_id", "impact"]
                        }
                    }
                },
                "required": ["id", "name", "description", "weight", "impacts"],
            },
        },
    },
    "required": ["scenarios", "premises"],
}


async def decompose_scenario_query_async(
    query: str,
    web_snippets: list[str] | None = None,
    verified_evidences: list[Evidence] | None = None,
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

    # Horyzont czasowy z pytania (DEC-034). Jeżeli użytkownik go podał, scenariusze
    # muszą być nim ograniczone — inaczej model prognozuje "kiedykolwiek".
    horizon = detect_time_horizon(query)
    if horizon is not None:
        if horizon.is_precise:
            horizon_instruction = (
                f"\n\nHORYZONT CZASOWY PODANY PRZEZ UŻYTKOWNIKA: {horizon.label} "
                f"(data graniczna: {horizon.end_date.isoformat()}).\n"
                "Wszystkie scenariusze MUSZĄ dotyczyć wyłącznie tego okresu i mieć go wpisanego w opis. "
                "Nie buduj scenariuszy wykraczających poza tę datę. Przesłanki dobieraj pod kątem tego okresu."
            )
        else:
            horizon_instruction = (
                f"\n\nHORYZONT CZASOWY PODANY PRZEZ UŻYTKOWNIKA: {horizon.label} (wyrażenie nieprecyzyjne — "
                "nie przypisuj mu konkretnej daty i nie zmyślaj jej).\n"
                "Scenariusze opisz w tej perspektywie, nie podając wymyślonych dat granicznych."
            )
    else:
        horizon_instruction = ""

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
            "- W zdaniach, tytułach scenariuszy i nazwach przesłanek TYLKO pierwsza litera w zdaniu/tytule ma być wielka (sentence case), chyba że występuje nazwa własna (np. Polska, Rosja, NATO, Ukraina).\n"
            "- NIGDY nie pisz każdego wyrazu wielką literą (zakaz angielskiego Title Case). Przymiotniki od nazw państw (np. rosyjski, polski, ukraiński) pisz z małej litery.\n"
            "- Wszystkie nazwy własne państw, sojuszy i instytucji pisz Z DUŻEJ LITERY (np. Polska, Ukraina, NATO, USA, UE).\n"
            "- Opisy formułuj w nienagannym, obiektywnym języku analitycznym.\n"
            "- Zakaz jakiegokolwiek żargonu pseudokwantowego (amplitudy, wektory stanów, fale)."
        )
        user_content = (
            f"Pytanie użytkownika:\n\"{query}\"\n\n"
            f"Kontekst i fakty z sieci:\n{snippets_text}"
            f"{_format_verified_evidence_prompt(verified_evidences)}"
            f"{horizon_instruction}\n\n"
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
                    raw_impacts = pr_data.get("impacts") or pr_data.get("impact_on_scenarios", {})
                    if isinstance(raw_impacts, list):
                        impacts = {
                            str(item["scenario_id"]): float(item["impact"])
                            for item in raw_impacts
                            if isinstance(item, dict) and "scenario_id" in item and "impact" in item
                        }
                    elif isinstance(raw_impacts, dict):
                        impacts = {str(k): float(v) for k, v in raw_impacts.items()}
                    else:
                        impacts = {}

                    # Ensure all known scenarios have an entry (default 0.0 if not specified)
                    for sc in scenarios:
                        if sc.id not in impacts:
                            impacts[sc.id] = 0.0

                    premises.append(EvidencePremise(
                        id=str(pr_data["id"]),
                        name=normalize_polish_geopolitical_text(str(pr_data["name"])),
                        description=(f"{normalize_polish_geopolitical_text(str(pr_data.get('description', '')))} Waga nie została wyliczona z dokumentów; ustaw ją samodzielnie, jeżeli chcesz zróżnicować znaczenie przesłanek.".strip()),
                        source=normalize_polish_geopolitical_text(str(pr_data.get("source", "propozycja modelu"))),
                        confidence=1.0,
                        weight=1.0,
                        impact_on_scenarios=impacts,
                        provenance="llm_suggested",
                        source_ref=str(pr_data.get("source", "propozycja modelu")),
                        is_accepted=False,
                    ))
        except Exception as exc:
            logger.warning("LLM scenario decomposition failed: %s", exc)
    premises, scenarios, unspec_count, n_doc, n_rej = _integrate_verified_evidences(premises, scenarios, verified_evidences, p_json if "p_json" in locals() else None, query)

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
        forecast.telemetry["unspecified_impacts_count"] = unspec_count
        forecast.telemetry["n_documented_premises"] = n_doc
        forecast.telemetry["n_premises_rejected_as_undocumented"] = n_rej
        return case, forecast

    # Compute scenario distribution using honest weighted softmax
    forecast = compute_scenario_distribution(
        query=query,
        scenarios=scenarios,
        premises=premises,
        domain=domain,
        beta=1.0,
    )

    # Rozpoznany horyzont trafia do telemetrii jako fakt odczytany z pytania (DEC-034).
    # Gdy wyrażenie jest nieprecyzyjne, data graniczna pozostaje pusta — nie jest zmyślana.
    if horizon is not None:
        forecast.telemetry["time_horizon"] = {
            "raw": horizon.raw,
            "label": horizon.label,
            "end_date": horizon.end_date.isoformat() if horizon.end_date else None,
            "basis": horizon.basis,
            "is_precise": horizon.is_precise,
        }

    forecast.telemetry["unspecified_impacts_count"] = unspec_count
    forecast.telemetry["web_sourced_premises_without_model_impacts"] = unspec_count
    forecast.telemetry["n_documented_premises"] = n_doc
    forecast.telemetry["n_premises_rejected_as_undocumented"] = n_rej

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


def _format_verified_evidence_prompt(verified_evidences: list[Evidence] | None) -> str:
    if not verified_evidences:
        return ""
    lines = ["\n\nZWERYFIKOWANE FAKTY Z POBRANYCH DOKUMENTÓW ŹRÓDŁOWYCH (potwierdzone cytatami ze stron www):"]
    for idx, ev in enumerate(verified_evidences):
        pub = ev.publisher or ev.source_title or ev.source_url
        lines.append(f"- ID: web_{idx+1}\n  Fakt: {ev.claim}\n  Cytat dosłowny ze strony: „{ev.quote}”\n  Wydawca / Źródło: {pub}")
    lines.append(
        "UWAGA: Dla każdego z powyższych zweryfikowanych faktów (web_1, web_2...) określ wpływ "
        "(impact_on_scenarios od -1.0 do +1.0) na poszczególne scenariusze. "
        "Możesz też zaproponować dodatkowe przesłanki analityczne modelu (id: pr_1, pr_2...).\n"
    )
    return "\n".join(lines)


def _integrate_verified_evidences(
    premises: list[EvidencePremise],
    scenarios: list[ScenarioOutcome],
    verified_evidences: list[Evidence] | None,
    p_json: dict[str, Any] | None,
    query: str,
) -> tuple[list[EvidencePremise], list[ScenarioOutcome], int, int, int]:
    """
    Integrates verified evidences into evidence premises.
    Under DEC-039, premises meeting all 5 conditions of documentation are automatically accepted (is_accepted = True).
    Returns (premises, scenarios, unspecified_impacts_count, n_documented_premises, n_premises_rejected_as_undocumented).
    """
    if not verified_evidences or len(scenarios) < 2:
        return premises, scenarios, 0, 0, 0

    raw_premises_data = p_json.get("premises", []) if isinstance(p_json, dict) else []
    web_premises: list[EvidencePremise] = []
    unspecified_impacts_count = 0
    n_documented = 0
    n_rejected_undoc = 0

    for idx, ev in enumerate(verified_evidences):
        web_id = f"web_{idx+1}"
        pub = ev.publisher or ev.source_title or "Zweryfikowane źródło sieciowe"
        impacts: dict[str, float] = dict(ev.impact_on_scenarios) if ev.impact_on_scenarios else {}
        weight = 1.0
        has_model_impacts = bool(impacts)

        # Also check if decomposing model provided impacts for this web premise
        for pr_data in raw_premises_data:
            pid = str(pr_data.get("id", ""))
            if pid == web_id or f"web_{idx+1}" in pid:
                raw_impacts = pr_data.get("impacts") or pr_data.get("impact_on_scenarios", {})
                if isinstance(raw_impacts, list):
                    for item in raw_impacts:
                        if isinstance(item, dict) and "scenario_id" in item and "impact" in item:
                            impacts[str(item["scenario_id"])] = float(item["impact"])
                elif isinstance(raw_impacts, dict):
                    for k, v in raw_impacts.items():
                        impacts[str(k)] = float(v)
                weight = float(pr_data.get("weight", 1.0))
                if len(impacts) > 0:
                    has_model_impacts = True
                break

        for sc in scenarios:
            if sc.id not in impacts:
                impacts[sc.id] = 0.0

        wb = compute_evidence_weight(ev, all_evidences=verified_evidences)
        computed_weight = wb.final_weight

        # Check 5 conditions of DEC-039 (documented premise)
        c1_provenance = True  # will be web_sourced
        c2_quote = bool(ev.quote and ev.quote.strip())
        c3_offsets = (ev.char_start is not None) and (ev.char_end is not None)
        c4_url = bool(ev.source_url and ev.source_url.startswith("http"))
        c5_weight = computed_weight > 0.0

        is_fully_documented = c1_provenance and c2_quote and c3_offsets and c4_url and c5_weight

        if is_fully_documented:
            premise_accepted = True
            n_documented += 1
        else:
            premise_accepted = False
            n_rejected_undoc += 1

        if not has_model_impacts:
            unspecified_impacts_count += 1
            desc_impact_text = "Wpływ na scenariusze nie został określony; przesłanka nie przeważa rozkładu, dopóki nie nadasz jej wag ręcznie."
            source_ref_val = f"{ev.source_url} [wpływy: nieokreślone]" if ev.source_url else "[wpływy: nieokreślone]"
        else:
            desc_impact_text = "Liczbowy wpływ na scenariusze jest propozycją analityczną modelu i wymaga zatwierdzenia przez decydenta."
            source_ref_val = str(ev.source_url) if ev.source_url else None

        web_premises.append(EvidencePremise(
            id=web_id,
            name=normalize_polish_geopolitical_text(str(ev.claim)[:80]),
            description=(
                f"Cytat: „{ev.quote}” (źródło: {pub}). "
                f"{wb.justification_summary} "
                f"{desc_impact_text}"
            ),
            source=str(pub),
            confidence=float(ev.confidence),
            weight=computed_weight,
            impact_on_scenarios=impacts,
            provenance="web_sourced",
            source_ref=source_ref_val,
            is_accepted=premise_accepted,
            impact_justification=dict(ev.impact_justification) if ev.impact_justification else {},
        ))

    clean_llm = [p for p in premises if not p.id.startswith("web_")]
    return web_premises + clean_llm, scenarios, unspecified_impacts_count, n_documented, n_rejected_undoc

