"""
YourQuantum — Scenario Weighting & Probabilistic Evidence Aggregation Engine
Computes honest scenario probability distributions using weighted evidence aggregation
and Gibbs-Boltzmann / Softmax distribution with empirical sensitivity bands.

Non-negotiable principles (Prompt V5 / Fable 5.1):
- Deterministic, verifiable mathematical computation (weighted softmax).
- Zero quantum metaphors: no artificial quantum states, no invented amplitudes, no fake interference.
- Full provenance tracking for all evidence premises.
- LLM suggestions do not impact distribution without explicit user acceptance.
- Sensitivity analysis across beta in {0.5, 1.0, 2.0, 3.0} to show uncertainty.
- Analytical tipping points (minimal weight delta required to flip dominant scenario).
"""
from __future__ import annotations

import logging
import math
import re
import time
from typing import Any, Literal
from pydantic import BaseModel, Field

from backend.domain.problem_classes import ExecutiveBriefing, KeyPillar

logger = logging.getLogger(__name__)


PROPER_NOUNS: set[str] = {
    # Państwa, krainy, sojusze, podmioty geopolityczne
    "polska", "polski", "polsce", "polskę", "polską",
    "rosja", "rosji", "rosję", "rosją",
    "ukraina", "ukrainy", "ukrainie", "ukrainę", "ukrainą",
    "białoruś", "białorusi", "białorusią",
    "chiny", "chin", "chinom", "chinami",
    "tajwan", "tajwanu", "tajwanie",
    "iran", "iranu", "iranie",
    "litwa", "litwy", "litwie", "litwę",
    "łotwa", "łotwy", "łotwie", "łotwę",
    "estonia", "estonii", "estonię",
    "niemcy", "niemiec", "niemcom", "niemcami",
    "francja", "francji", "francję",
    "europa", "europy", "europie", "europę",
    # Miasta, ośrodki, akweny
    "warszawa", "warszawy", "warszawie", "warszawę",
    "moskwa", "moskwy", "moskwie", "moskwę",
    "kijów", "kijowa", "kijowie",
    "kreml", "kremla", "kremlu", "kremlem",
    "bałtyk", "bałtyku", "bałtykiem",
    # Skrótowce
    "nato", "usa", "ue", "pkb", "mon", "isw", "osw", "sipri", "iiss", "bbn", "msz", "krld"
}

ACRONYMS: set[str] = {"nato", "usa", "ue", "pkb", "mon", "isw", "osw", "sipri", "iiss", "bbn", "msz", "krld"}


def to_polish_sentence_case(text: str) -> str:
    """
    W zdaniach i tytułach tylko pierwsza litera ma być wielka, chyba że występuje nazwa własna
    (np. Polska, Rosja, NATO). Przymiotniki od nazw państw (rosyjski, polski) są z małej litery.
    """
    if not text or not text.strip():
        return text

    def process_segment(seg: str) -> str:
        words = seg.split()
        if not words:
            return seg
        out_words = []
        for i, w in enumerate(words):
            clean = re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()
            prefix = re.match(r"^[^\w]+", w)
            p_str = prefix.group(0) if prefix else ""
            suffix = re.search(r"[^\w]+$", w)
            s_str = suffix.group(0) if suffix else ""

            # Jeśli to pierwsze słowo segmentu lub słowo w cudzysłowie
            if i == 0 or (p_str and any(q in p_str for q in ("'", '"', "„", "«", "'"))):
                if clean in ACRONYMS:
                    w_core = clean.upper()
                else:
                    w_core = clean.capitalize()
            else:
                if clean in ACRONYMS:
                    w_core = clean.upper()
                elif clean in PROPER_NOUNS:
                    w_core = clean.capitalize()
                else:
                    w_core = clean.lower()
            out_words.append(f"{p_str}{w_core}{s_str}")
        return " ".join(out_words)

    sentences = re.split(r"(?<=[.!?\n])\s+", text.strip())
    processed_sentences = []
    for s in sentences:
        if not s:
            continue
        if ": " in s:
            parts = s.split(": ")
            processed_parts = [process_segment(p) for p in parts]
            processed_sentences.append(": ".join(processed_parts))
        else:
            processed_sentences.append(process_segment(s))

    return " ".join(processed_sentences)


def normalize_polish_geopolitical_text(text: str) -> str:
    """
    Enforces correct Polish orthography, proper casing for countries,
    geographical names, and institutional acronyms (e.g. Ukraina, NATO, Polska, USA),
    as well as sentence case (only first letter capitalized unless proper noun).
    """
    if not text:
        return text

    res = to_polish_sentence_case(text)

    replacements: list[tuple[str, Any]] = [
        (r"\b(ukrain)(a|y|ie|ę|ą|o)\b", lambda m: "Ukrain" + m.group(2)),
        (r"\b(polsc)(e)\b", lambda m: "Polsc" + m.group(2)),
        (r"\b(polsk)(a|i|ę|ą|o)\b", lambda m: "Polsk" + m.group(2)),
        (r"\b(rzeczpospolit)(a|ej|ą)\b", lambda m: "Rzeczpospolit" + m.group(2)),
        (r"\b(rosj)(a|i|ę|ą|o)\b", lambda m: "Rosj" + m.group(2)),
        (r"\b(europ)(a|y|ie|ę|ą|o)\b", lambda m: "Europ" + m.group(2)),
        (r"\b(bia[łl]oru[sś])\b", "Białoruś"),
        (r"\b(bia[łl]orusi)(ą)?\b", lambda m: "Białorusi" + (m.group(2) or "")),
        (r"\b(ba[łl]tyk)(u|iem)?\b", lambda m: "Bałtyk" + (m.group(2) or "")),
        (r"\b(kreml)(a|u|em)?\b", lambda m: "Kreml" + (m.group(2) or "")),
        (r"\b(warszaw)(a|y|ie|ę|ą|o)\b", lambda m: "Warszaw" + m.group(2)),
        (r"\b(moskw)(a|y|ie|ę|ą|o)\b", lambda m: "Moskw" + m.group(2)),
        (r"\b(kijow)(a|ie|em)?\b", lambda m: "Kijow" + (m.group(2) or "")),
        (r"\b(kijów)\b", "Kijów"),
        (r"\b(nato)\b", "NATO"),
        (r"\b(usa)\b", "USA"),
        (r"\b(ue)\b", "UE"),
        (r"\b(pkb)\b", "PKB"),
        (r"\b(mon)\b", "MON"),
        (r"\b(isw)\b", "ISW"),
        (r"\b(osw)\b", "OSW"),
        (r"\b(sipri)\b", "SIPRI"),
        (r"\b(iiss)\b", "IISS"),
        (r"\b(bbn)\b", "BBN"),
        (r"\b(msz)\b", "MSZ"),
        (r"\b(krld)\b", "KRLD"),
        (r"\b(rp)\b", "RP"),
        (r"\b(fr)\b", "FR"),
        (r"\bart\.?\s*5\b", "art. 5"),
        (r"\bartyku[łl]\s*5\b", "artykuł 5"),
    ]
    for pattern, repl in replacements:
        res = re.sub(pattern, repl, res, flags=re.IGNORECASE)
    return res


# Verbal chance descriptor lookup table (strictly monotonic, no overlaps)
CHANCE_DESCRIPTORS_TABLE: list[tuple[float, str]] = [
    (0.95, "bardzo wysokie prawdopodobieństwo — ponad 95 szans na 100"),
    (0.80, "wysokie prawdopodobieństwo (ok. 80–94 szans na 100)"),
    (0.50, "umiarkowanie wysokie prawdopodobieństwo (ponad połowa szans)"),
    (0.20, "umiarkowane prawdopodobieństwo (ok. 20–49 szans na 100)"),
    (0.00, "niskie prawdopodobieństwo (poniżej 20 szans na 100)"),
]


def format_chance_description(probability: float) -> str:
    """Returns an honest Polish verbal description corresponding to the probability threshold."""
    for threshold, description in CHANCE_DESCRIPTORS_TABLE:
        if probability >= threshold:
            return description
    return "znikome prawdopodobieństwo"


class ScenarioOutcome(BaseModel):
    id: str
    title: str
    description: str = ""
    probability: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_score: float = 0.0
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"


class EvidencePremise(BaseModel):
    id: str
    name: str
    description: str = ""
    source: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    weight: float = Field(default=1.0, ge=0.0)
    impact_on_scenarios: dict[str, float] = Field(default_factory=dict)
    provenance: Literal["user_supplied", "web_sourced", "llm_suggested", "assumed"] = "assumed"
    source_ref: str | None = None
    is_accepted: bool = True  # If provenance == "llm_suggested", must be explicitly accepted to count
    impact_justification: dict[str, Any] = Field(default_factory=dict)
    impact_source: Literal["documented", "model_unverified", "user_defined"] = "documented"


class TippingPointItem(BaseModel):
    premise_id: str
    premise_name: str
    delta_weight_needed: float
    direction: Literal["decrease", "increase", "unachievable"]
    explanation: str


class ScenarioForecast(BaseModel):
    query: str
    domain: str = "Analiza scenariuszowa i badanie ryzyka"
    scenarios: list[ScenarioOutcome]
    dominant_scenario_id: str
    evidence_premises: list[EvidencePremise]
    tipping_points: list[str]
    tipping_point_details: list[TippingPointItem] = Field(default_factory=list)
    sensitivity_band: dict[str, dict[str, float]] = Field(default_factory=dict)
    telemetry: dict[str, Any]
    briefing: ExecutiveBriefing


def compute_tipping_points(
    scenarios: list[ScenarioOutcome],
    premises: list[EvidencePremise],
    beta: float = 1.0,
) -> tuple[list[str], list[TippingPointItem]]:
    """
    Analytically computes the minimal weight change (delta_w) for each premise
    required to flip the dominant scenario outcome.
    """
    if len(scenarios) < 2 or not premises:
        return (["Niewystarczająca liczba scenariuszy lub przesłanek do wyznaczenia punktów zwrotnych."], [])

    active_premises = [p for p in premises if p.provenance not in ("llm_suggested", "web_sourced") or p.is_accepted]
    if not active_premises:
        return (["Brak aktywnych przesłanek do wyznaczenia punktów zwrotnych."], [])

    # Sort scenarios by evidence_score descending
    sorted_scenarios = sorted(scenarios, key=lambda s: s.evidence_score, reverse=True)
    dominant = sorted_scenarios[0]
    runner_up = sorted_scenarios[1]
    score_gap = dominant.evidence_score - runner_up.evidence_score

    if score_gap <= 1e-9:
        msg = f"Scenariusze '{dominant.title}' oraz '{runner_up.title}' mają identyczne poparcie — układ jest w punkcie krytycznym."
        return ([msg], [])

    tipping_items: list[TippingPointItem] = []
    text_summaries: list[str] = []

    for p in active_premises:
        is_impact_active = (p.impact_source in ("documented", "user_defined") or p.provenance == "user_supplied")
        impact_dom = p.impact_on_scenarios.get(dominant.id, 0.0) if is_impact_active else 0.0
        impact_run = p.impact_on_scenarios.get(runner_up.id, 0.0) if is_impact_active else 0.0
        net_coupling = p.confidence * (impact_dom - impact_run)

        if abs(net_coupling) < 1e-6:
            tipping_items.append(TippingPointItem(
                premise_id=p.id,
                premise_name=p.name,
                delta_weight_needed=float("inf"),
                direction="unachievable",
                explanation=f"Przesłanka '{p.name}' oddziałuje równomiernie na oba czołowe warianty; zmiana jej wagi nie wpływa na relację dominacji.",
            ))
            continue

        if net_coupling > 0:
            # Dominant is supported more by this premise than runner-up.
            # To flip, we must reduce weight: delta_w = score_gap / net_coupling
            needed_reduction = score_gap / net_coupling
            if needed_reduction <= p.weight:
                pct_reduction = (needed_reduction / p.weight) * 100
                tipping_items.append(TippingPointItem(
                    premise_id=p.id,
                    premise_name=p.name,
                    delta_weight_needed=round(needed_reduction, 3),
                    direction="decrease",
                    explanation=(
                        f"Zmniejszenie wagi przesłanki '{p.name}' o {needed_reduction:.2f} "
                        f"(-{pct_reduction:.1f}%, z {p.weight:.2f} do {max(0.0, p.weight - needed_reduction):.2f}) "
                        f"spowoduje utratę dominacji na rzecz wariantu: '{runner_up.title}'."
                    ),
                ))
            else:
                # Even reducing weight to 0 does not flip dominance alone
                tipping_items.append(TippingPointItem(
                    premise_id=p.id,
                    premise_name=p.name,
                    delta_weight_needed=round(needed_reduction, 3),
                    direction="decrease",
                    explanation=(
                        f"Całkowite usunięcie przesłanki '{p.name}' (redukcja wagi o {p.weight:.2f}) "
                        f"zmniejsza przewagę, lecz sama ta zmiana nie wystarcza do odwrócenia wyniku (wymagane: -{needed_reduction:.2f})."
                    ),
                ))
        else:
            # Runner-up is supported more by this premise.
            # To flip, we must increase weight: delta_w = score_gap / |net_coupling|
            needed_increase = score_gap / abs(net_coupling)
            pct_increase = (needed_increase / max(0.001, p.weight)) * 100
            tipping_items.append(TippingPointItem(
                premise_id=p.id,
                premise_name=p.name,
                delta_weight_needed=round(needed_increase, 3),
                direction="increase",
                explanation=(
                    f"Zwiększenie wagi przesłanki '{p.name}' o {needed_increase:.2f} "
                    f"(+{pct_increase:.1f}%, z {p.weight:.2f} do {p.weight + needed_increase:.2f}) "
                    f"zrównoważy przewagę i wysunie na prowadzenie wariant: '{runner_up.title}'."
                ),
            ))

    # Sort items: achievable first, then by delta_weight_needed ascending
    achievable = [item for item in tipping_items if item.delta_weight_needed != float("inf")]
    achievable.sort(key=lambda item: item.delta_weight_needed)

    if achievable:
        for item in achievable[:3]:
            text_summaries.append(item.explanation)
    else:
        text_summaries.append(
            "Żadna pojedyncza zmiana wagi istniejących przesłanek nie odwraca dominacji czołowego scenariusza. "
            "Dominacja opiera się na spójnym wektorze wielu niezależnych wskaźników."
        )

    return text_summaries, tipping_items


def compute_scenario_distribution(
    query: str,
    scenarios: list[ScenarioOutcome],
    premises: list[EvidencePremise],
    domain: str = "Analiza scenariuszowa i badanie ryzyka",
    beta: float = 1.0,
) -> ScenarioForecast:
    """
    Computes rigorous scenario probability distribution using weighted evidence aggregation
    and Gibbs/Softmax distribution with sensitivity analysis across beta in {0.5, 1.0, 2.0, 3.0}.
    """
    start_time = time.monotonic()
    k = len(scenarios)
    if k < 2:
        raise ValueError("Co najmniej 2 scenariusze są wymagane do obliczenia rozkładu prawdopodobieństwa.")

    if not premises:
        raise ValueError("Brak przesłanek do obliczenia rozkładu. Zdefiniuj co najmniej jedną przesłankę.")

    # Filter premises: only accepted premises or user/assumed enter calculation
    active_premises = [p for p in premises if p.provenance not in ("llm_suggested", "web_sourced") or p.is_accepted]

    # 1. Compute support evidence score for each scenario
    # S(s_i) = sum_{p in active} (weight * confidence * impact)
    # DEC-040: Only documented or user-defined impacts enter softmax calculation.
    # Impacts with impact_source == "model_unverified" do NOT shape the distribution (effective impact is 0.0).
    support_scores: dict[str, float] = {}
    for sc in scenarios:
        s_val = 0.0
        for p in active_premises:
            is_impact_active = (p.impact_source in ("documented", "user_defined") or p.provenance == "user_supplied")
            if is_impact_active:
                impact = p.impact_on_scenarios.get(sc.id, 0.0)
                s_val += (impact * p.weight * p.confidence)
        support_scores[sc.id] = s_val
        sc.evidence_score = round(s_val, 4)

    # 2. Compute probabilities using Softmax / Gibbs distribution
    def _compute_distribution_for_beta(b_val: float) -> dict[str, float]:
        max_s = max(support_scores.values())
        unnormalized = {sc.id: math.exp(b_val * (support_scores[sc.id] - max_s)) for sc in scenarios}
        z_sum = sum(unnormalized.values())
        if z_sum <= 0:
            return {sc.id: round(1.0 / k, 4) for sc in scenarios}
        return {sc.id: round(unnormalized[sc.id] / z_sum, 4) for sc in scenarios}

    # Sensitivity band across beta in {0.5, 1.0, 2.0, 3.0}
    beta_candidates = [0.5, 1.0, 2.0, 3.0]
    sensitivity_band: dict[str, dict[str, float]] = {}
    for b_candidate in beta_candidates:
        dist = _compute_distribution_for_beta(b_candidate)
        sensitivity_band[f"beta_{b_candidate}"] = dist

    # Primary probabilities for the chosen beta
    primary_probabilities = _compute_distribution_for_beta(beta)

    # Assign calculated values and normalize texts
    for sc in scenarios:
        sc.title = normalize_polish_geopolitical_text(sc.title)
        sc.description = normalize_polish_geopolitical_text(sc.description)
        sc.probability = primary_probabilities.get(sc.id, 0.0)

    for pr in premises:
        pr.name = normalize_polish_geopolitical_text(pr.name)
        pr.description = normalize_polish_geopolitical_text(pr.description)
        if pr.source:
            pr.source = normalize_polish_geopolitical_text(pr.source)

    # Sort scenarios by probability descending
    scenarios.sort(key=lambda s: s.probability, reverse=True)
    dominant_scenario = scenarios[0]

    # 3. Analytically compute tipping points
    tipping_points_text, tipping_details = compute_tipping_points(scenarios, active_premises, beta=beta)

    # 4. Construct Executive Briefing
    pillars: list[KeyPillar] = []
    for p in active_premises[:4]:
        favored_sc = max(p.impact_on_scenarios.items(), key=lambda item: item[1])[0]
        fav_sc_obj = next((s for s in scenarios if s.id == favored_sc), None)
        fav_title = fav_sc_obj.title if fav_sc_obj else favored_sc

        direction_label = f"Kierunek: Najsilniej sprzyja wariantowi: '{fav_title}'"
        pillars.append(
            KeyPillar(
                title=normalize_polish_geopolitical_text(p.name),
                chosen_option=direction_label,
                rationale=normalize_polish_geopolitical_text(
                    f"{p.description} (Źródło: {p.source or 'analizy decyzyjne'}; pochodzenie: {p.provenance}). "
                    f"Waga dowodowa: {p.weight:.1f}, wiarygodność: {p.confidence:.2f}."
                ),
            )
        )

    dominant_pct_pl = f"{dominant_scenario.probability * 100:.1f}%".replace(".", ",")
    chance_descr = format_chance_description(dominant_scenario.probability)

    # Calculate sensitivity range for dominant scenario
    dom_probs_across_beta = [sensitivity_band[f"beta_{b}"][dominant_scenario.id] * 100 for b in beta_candidates]
    min_dom_pct = min(dom_probs_across_beta)
    max_dom_pct = max(dom_probs_across_beta)
    band_str = f"{min_dom_pct:.1f}%–{max_dom_pct:.1f}%".replace(".", ",")

    summary = (
        f"Ważona agregacja przesłanek empirycznych z jawną funkcją softmax wyznaczyła rozkład scenariuszy: "
        f"z wynikiem bazowym {dominant_pct_pl} (przedział wrażliwości: {band_str}, {chance_descr}) "
        f"przeważa wariant: '{dominant_scenario.title}'. "
        f"Wynik jest analityczną konsekwencją {len(active_premises)} przyjętych przesłanek dowodowych "
        f"i podlega natychmiastowemu przeliczeniu przy modyfikacji ich wag lub założeń decydenta."
    )

    briefing = ExecutiveBriefing(
        headline=f"Rozkład scenariuszowy: {dominant_scenario.title} ({dominant_pct_pl} / pasmo: {band_str})",
        executive_summary=summary,
        key_pillars=pillars,
        primary_tradeoff=f"Dominacja wariantu '{dominant_scenario.title}' zależy bezpośrednio od parametru ostrości rozkładu beta (wynik waha się od {band_str}).",
        tipping_points=tipping_points_text,
    )

    # Calculate impact_documented_share (DEC-040)
    total_active_impact_magnitude = sum(
        abs(p.impact_on_scenarios.get(sc.id, 0.0))
        for p in active_premises
        for sc in scenarios
    )
    documented_active_impact_magnitude = sum(
        abs(p.impact_on_scenarios.get(sc.id, 0.0))
        for p in active_premises
        if p.impact_source == "documented"
        for sc in scenarios
    )
    if total_active_impact_magnitude > 0:
        impact_documented_share = round((documented_active_impact_magnitude / total_active_impact_magnitude) * 100.0, 2)
    else:
        impact_documented_share = 0.0

    telemetry = {
        "method": "weighted_softmax_aggregation",
        "beta": beta,
        "n_scenarios": k,
        "n_premises": len(premises),
        "n_active_premises": len(active_premises),
        "dominant_scenario": dominant_scenario.title,
        "dominant_probability": dominant_scenario.probability,
        "dominant_sensitivity_band": band_str,
        "impact_documented_share": impact_documented_share,
        "solve_time_seconds": round(time.monotonic() - start_time, 4),
    }

    return ScenarioForecast(
        query=query,
        domain=domain,
        scenarios=scenarios,
        dominant_scenario_id=dominant_scenario.id,
        evidence_premises=premises,
        tipping_points=tipping_points_text,
        tipping_point_details=tipping_details,
        sensitivity_band=sensitivity_band,
        telemetry=telemetry,
        briefing=briefing,
    )
