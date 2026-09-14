"""
YourQuantum — Multi-Lever Design Decomposer (Phase D2 / N5)
Translates natural-language system architecture / policy reform queries
into a multi-lever combinatorial DesignProblem using LLMGateway with offline template fallback.
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from backend.domain.decision_case import ScoredValue
from backend.domain.problem_classes import (
    DesignCriterion,
    DesignLever,
    DesignProblem,
    Interaction,
    LeverOption,
    ProblemClass,
)
from backend.domain.problem_ir import Provenance
from backend.infrastructure.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)


def validate_design_problem_for_synthesis(problem: DesignProblem) -> tuple[bool, list[str]]:
    """
    Enforces N5 validation rules before computing design synthesis:
    1. At least 2 levers, each with >= 2 options.
    2. At least 1 criterion.
    3. Every (lever, option, criterion) cell in score_matrix must have a numeric value and source_ref.
    4. Any non-zero interaction synergy requires a verified source_ref or explicit assumption tag.
    """
    errors: list[str] = []

    if len(problem.levers) < 2:
        errors.append("Model DESIGN wymaga co najmniej dwóch dźwigni decyzyjnych.")
    for lever in problem.levers:
        if len(lever.options) < 2:
            errors.append(f"Dźwignia '{lever.name}' musi posiadać co najmniej dwa warianty (obecnie: {len(lever.options)}).")

    if len(problem.criteria) == 0:
        errors.append("Zdefiniuj co najmniej jedno kryterium oceny wielodźwigniowej.")

    # Check score_matrix completeness
    for lever in problem.levers:
        l_matrix = problem.score_matrix.get(lever.id, {})
        for opt in lever.options:
            o_matrix = l_matrix.get(opt.id, {})
            for crit in problem.criteria:
                cell = o_matrix.get(crit.id)
                if cell is None or cell.value is None:
                    errors.append(
                        f"Brak wartości w komórce: dźwignia '{lever.name}', wariant '{opt.title}', kryterium '{crit.name}'."
                    )
                elif not cell.source_ref or not str(cell.source_ref).strip():
                    errors.append(
                        f"Wartość w komórce ('{lever.name}' / '{opt.title}' / '{crit.name}') "
                        "nie posiada źródła (source_ref). Oznacz jako założenie lub podaj źródło."
                    )

    # Check synergies
    for inter in problem.interactions:
        if abs(inter.synergy) > 1e-6 and not inter.source_ref:
            errors.append(
                f"Niezerowa synergia ({inter.synergy}) między opcjami '{inter.option_a_id}' i '{inter.option_b_id}' "
                "wymaga podania źródła lub oznaczenia jako założenie."
            )

    return len(errors) == 0, errors


def create_offline_design_skeleton(query: str) -> DesignProblem:
    """
    Deterministic offline fallback skeleton for DESIGN queries (N5).
    Produces 3 domain-relevant or general levers with 2 variants each,
    empty score_matrix cells, and instructions for user completion.
    """
    q_lower = query.lower()

    if any(w in q_lower for w in ["zdrow", "szpital", "nfz", "pacjent", "lekar"]):
        title = "Projekt reformy systemu ochrony zdrowia"
        levers = [
            DesignLever(
                id="lev_finanse",
                name="Model finansowania świadczeń",
                description="Struktura płatnika i alokacja środków publicznych",
                options=[
                    LeverOption(
                        id="opt_fin_jednolity",
                        title="Jednolity płatnik publiczny (Single Payer)",
                        description="Centralizacja budżetu w jednym funduszu ze ścisłą kontrolą cen procedur.",
                        evidence_ref="Wymaga weryfikacji kosztów administracyjnych w źródłach publicznych",
                    ),
                    LeverOption(
                        id="opt_fin_konkurencja",
                        title="Zarządzana konkurencja kas chorych",
                        description="Wiele konkurujących regionalnych funduszy zdrowotnych z koszykiem gwarantowanym.",
                        evidence_ref="Wymaga weryfikacji wskaźników efektywności modeli wielopłatnikowych",
                    ),
                ],
            ),
            DesignLever(
                id="lev_poz",
                name="Rola Podstawowej Opieki Zdrowotnej",
                description="Sposób organizacji pierwszego kontaktu pacjenta z systemem",
                options=[
                    LeverOption(
                        id="opt_poz_gatekeeper",
                        title="Ścisły gatekeeping lekarza POZ",
                        description="Wymóg skierowania od lekarza POZ do wszystkich specjalistów.",
                        evidence_ref="Wymaga weryfikacji wpływu gatekeepingu na zbędne hospitalizacje",
                    ),
                    LeverOption(
                        id="opt_poz_otwarty",
                        title="Otwarty dostęp do ambulatoryjnej opieki specjalistycznej",
                        description="Bezpośredni dostęp do specjalistów bez konieczności wizyty w POZ.",
                        evidence_ref="Wymaga weryfikacji kolejek i kosztów wizyt ambulatoryjnych",
                    ),
                ],
            ),
            DesignLever(
                id="lev_cyfryzacja",
                name="Standard cyfryzacji i telemedycyny",
                description="Udział konsultacji zdalnych i centralnego rejestru EDM",
                options=[
                    LeverOption(
                        id="opt_cyfr_hybryda",
                        title="Hybrydowy model teleporad z limitem",
                        description="Maksymalnie 40% wizyt zdalnych, obowiązkowa pierwsza wizyta stacjonarna.",
                        evidence_ref="Wymaga weryfikacji wskaźników satysfakcji i trafności diagnoz",
                    ),
                    LeverOption(
                        id="opt_cyfr_cyfrowy_pierwszy",
                        title="Digital-First Triage",
                        description="Każdy kontakt rozpoczyna się od cyfrowego triażu i telekonsultacji.",
                        evidence_ref="Wymaga weryfikacji przepustowości i dostępności seniorów",
                    ),
                ],
            ),
        ]
        criteria = [
            DesignCriterion(id="crit_dostepnosc", name="Dostępność i skrócenie kolejek", direction="maximize", weight=1.0, unit="skala 1-10"),
            DesignCriterion(id="crit_koszt", name="Roczny koszt publiczny systemu", direction="minimize", weight=1.0, unit="mld PLN"),
            DesignCriterion(id="crit_jakosc", name="Jakość kliniczna i bezpieczeństwo", direction="maximize", weight=1.0, unit="skala 1-10"),
        ]
    else:
        title = f"Synteza architektoniczna: {query[:60]}"
        levers = [
            DesignLever(
                id="lev_arch_core",
                name="Architektura rdzenia systemu",
                description="Podstawowy model architektoniczny i podział odpowiedzialności",
                options=[
                    LeverOption(
                        id="opt_core_modular",
                        title="Modułowy monolit z twardymi granicami",
                        description="Pojedynczy wdrożeniowy artefakt z izolowanymi domenami i jawnymi kontraktami.",
                        evidence_ref="Sprawdź koszty infrastruktury i szybkość wdrożeń w porównywalnych projektach",
                    ),
                    LeverOption(
                        id="opt_core_distributed",
                        title="Rozproszone mikroserwisy sterowane zdarzeniami",
                        description="Niezależne usługi komunikujące się przez szynę zdarzeń.",
                        evidence_ref="Sprawdź narzut operacyjny i wymagania zespołu SRE",
                    ),
                ],
            ),
            DesignLever(
                id="lev_data_mgmt",
                name="Zarządzanie stanem i bazą danych",
                description="Topologia danych i model spójności",
                options=[
                    LeverOption(
                        id="opt_data_central",
                        title="Centralna baza ACID z replikacją odczytu",
                        description="Silna spójność transakcyjna, pojedyncze źródło prawdy.",
                        evidence_ref="Zweryfikuj limity skalowania pionowego",
                    ),
                    LeverOption(
                        id="opt_data_polyglot",
                        title="Poliglotyczna trwałość per domena",
                        description="Każda domena posiada własną zoptymalizowaną bazę ze spójnością ostateczną.",
                        evidence_ref="Zweryfikuj złożoność kompensacji i transakcji SAGA",
                    ),
                ],
            ),
            DesignLever(
                id="lev_deployment",
                name="Strategia infrastruktury i wdrożeń",
                description="Model hostingu i orkiestracji",
                options=[
                    LeverOption(
                        id="opt_deploy_managed",
                        title="Zarządzany Serverless / PaaS",
                        description="Minimalizacja narzutu utrzymaniowego, automatyczne skalowanie od zera.",
                        evidence_ref="Zweryfikuj koszty egress i cold starts",
                    ),
                    LeverOption(
                        id="opt_deploy_container",
                        title="Konteneryzowane środowisko dedykowane (K8s/Compose)",
                        description="Pełna kontrola nad środowiskiem uruchomieniowym i przewidywalny koszt stały.",
                        evidence_ref="Zweryfikuj koszt zarządzania klastrem i bezpieczeństwa",
                    ),
                ],
            ),
        ]
        criteria = [
            DesignCriterion(id="crit_skalowalnosc", name="Skalowalność i wydajność", direction="maximize", weight=1.0, unit="skala 1-10"),
            DesignCriterion(id="crit_koszt_utrzymania", name="Koszt wdrożenia i utrzymania", direction="minimize", weight=1.0, unit="tys. PLN/mc"),
            DesignCriterion(id="crit_niezawodnosc", name="Odporność na awarie i prostota", direction="maximize", weight=1.0, unit="skala 1-10"),
        ]

    # Initialize empty score_matrix (all cells empty for honest user input)
    score_matrix: dict[str, dict[str, dict[str, ScoredValue]]] = {}
    for lever in levers:
        score_matrix[lever.id] = {}
        for opt in lever.options:
            score_matrix[lever.id][opt.id] = {}

    # Empty interactions with default 0.0 synergy
    interactions = [
        Interaction(
            lever_a_id=levers[0].id,
            option_a_id=levers[0].options[0].id,
            lever_b_id=levers[1].id,
            option_b_id=levers[1].options[0].id,
            compatible=True,
            synergy=0.0,
            source_ref=None,
        )
    ]

    return DesignProblem(
        title=title,
        description=(
            f"Szkielet dźwigni architektonicznych dla zapytania: '{query}'. "
            "Uzupełnij wartości komórek macierzy dla każdego wariantu i kryterium "
            "(wprowadzając wartości ręcznie lub dozbierając z sieci) przed uruchomieniem syntezy Pareto."
        ),
        levers=levers,
        criteria=criteria,
        score_matrix=score_matrix,
        interactions=interactions,
    )


async def decompose_design_query_async(query: str, gateway: LLMGateway | None = None) -> DesignProblem:
    """
    Decomposes query into 3-7 levers with 2-5 options and criteria using LLMGateway.
    Falls back deterministically to create_offline_design_skeleton if offline or on error.
    """
    gw = gateway or LLMGateway()
    if not gw.is_configured:
        return create_offline_design_skeleton(query)

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "levers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "options": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "evidence_hint": {"type": "string"},
                                },
                                "required": ["id", "title", "description", "evidence_hint"],
                            },
                        },
                    },
                    "required": ["id", "name", "description", "options"],
                },
            },
            "criteria": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "direction": {"type": "string", "enum": ["maximize", "minimize"]},
                        "weight": {"type": "number"},
                        "unit": {"type": "string"},
                    },
                    "required": ["id", "name", "direction", "weight"],
                },
            },
        },
        "required": ["title", "description", "levers", "criteria"],
    }

    prompt = (
        "Rozłóż złożone zagadnienie architektoniczne lub reformę systemową na 3 do 7 kluczowych dźwigni decyzyjnych (levers).\n"
        "Dla każdej dźwigni podaj od 2 do 5 konkretnych, wykluczających się wariantów (options).\n"
        "Dla każdego wariantu podaj 'evidence_hint' — informację, jakie twarde dane empiryczne ze źródeł zewnętrznych należy sprawdzić.\n"
        "Zaproponuj 2 do 4 mierzalnych kryteriów oceny (criteria) z kierunkiem (maximize/minimize).\n\n"
        f"Zapytanie użytkownika:\n\"{query}\"\n"
    )

    try:
        res = await gw.generate(
            system_instruction="Jesteś ekspertem inżynierii systemowej i dekompozycji wielodźwigniowej. Zwracaj wyłącznie poprawny JSON.",
            user_content=prompt,
            purpose="decompose_design",
            response_schema=schema,
            temperature=0.1,
        )
        if res.parsed_json and isinstance(res.parsed_json, dict):
            raw_levers = res.parsed_json.get("levers") or []
            raw_criteria = res.parsed_json.get("criteria") or []

            if len(raw_levers) >= 2 and len(raw_criteria) >= 1:
                levers = []
                for l_idx, l in enumerate(raw_levers):
                    opts = []
                    for o_idx, o in enumerate(l.get("options", [])):
                        opts.append(
                            LeverOption(
                                id=str(o.get("id") or f"opt_{l_idx+1}_{o_idx+1}"),
                                title=str(o.get("title", f"Wariant {o_idx+1}")),
                                description=str(o.get("description", "")),
                                evidence_ref=str(o.get("evidence_hint", "Wymaga weryfikacji w źródłach")),
                                provenance=Provenance.ASSUMED,
                            )
                        )
                    levers.append(
                        DesignLever(
                            id=str(l.get("id") or f"lev_{l_idx+1}"),
                            name=str(l.get("name", f"Dźwignia {l_idx+1}")),
                            description=str(l.get("description", "")),
                            options=opts,
                        )
                    )

                criteria = []
                for c_idx, c in enumerate(raw_criteria):
                    direction = "minimize" if str(c.get("direction", "")).lower() == "minimize" else "maximize"
                    criteria.append(
                        DesignCriterion(
                            id=str(c.get("id") or f"crit_{c_idx+1}"),
                            name=str(c.get("name", f"Kryterium {c_idx+1}")),
                            direction=direction,
                            weight=float(c.get("weight", 1.0)),
                            unit=c.get("unit"),
                        )
                    )

                # Initialize empty score_matrix (N5: all scores start empty)
                score_matrix: dict[str, dict[str, dict[str, ScoredValue]]] = {}
                for lever in levers:
                    score_matrix[lever.id] = {}
                    for opt in lever.options:
                        score_matrix[lever.id][opt.id] = {}

                return DesignProblem(
                    title=str(res.parsed_json.get("title") or f"Projekt architektoniczny: {query[:50]}"),
                    description=str(res.parsed_json.get("description") or query),
                    levers=levers,
                    criteria=criteria,
                    score_matrix=score_matrix,
                    interactions=[],
                )
    except Exception as e:
        logger.warning("LLMGateway design decomposition failed, falling back to skeleton: %s", e)

    return create_offline_design_skeleton(query)


def decompose_design_query(query: str) -> DesignProblem:
    """Synchronous interface for offline design decomposition."""
    return create_offline_design_skeleton(query)
