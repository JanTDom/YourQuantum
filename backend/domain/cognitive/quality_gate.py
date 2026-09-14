"""
YourQuantum — Cognitive Input Quality Gate
Assesses whether a user's natural language input contains enough degrees of freedom,
concrete alternatives, and parameter bounds to model an honest mathematical dilemma.
Prevents garbage-in, garbage-out.
"""
from __future__ import annotations

import logging
import re
from backend.domain.decision_case import InputQuality

logger = logging.getLogger(__name__)


def assess_input_quality(text: str, options_count: int = 0, problem_class: str = "CHOICE") -> InputQuality:
    """
    Evaluate whether the user prompt contains enough degrees of freedom
    and specific data to model an exact mathematical dilemma.

    For CHOICE:
    1. Too short / vague (< 8 words)
    2. Lack of alternatives / degrees of freedom (< 2 options or lack of alternative markers)
    3. Missing numbers in financial / resource allocation contexts

    For DESIGN (systemic synthesis):
    1. Only rejects if extremely short (< 4 words)
    2. Does not require user to pre-specify options, as the engine decomposes
       the system into architectural levers via domain knowledge and web research.
    """
    cleaned = text.strip()
    words = [w for w in cleaned.split() if len(w) > 1]
    lower = cleaned.lower()

    # DESIGN class handling: systemic architecture & policy synthesis
    is_design_context = (
        problem_class == "DESIGN"
        or bool(re.search(r"\b(dźwigni|wielopoziomow|reforma|architektur.*system|syntez.*system|design|ochron.*zdrow)\b", lower))
    )
    if is_design_context:
        if len(words) < 4:
            return InputQuality(
                level="too_vague",
                reason="Opis systemu jest zbyt skrótowy, by wyodrębnić dźwignie architektoniczne.",
                suggestions=[
                    "Wskaż dziedzinę i cel reformy (np. 'Jak zreformować system ochrony zdrowia w Polsce, aby skrócić kolejki').",
                    "Określ główny obszar odpowiedzialności lub kontekst instytucjonalny.",
                ],
            )
        return InputQuality(level="sufficient", reason="", suggestions=[])

    # Scenario forecasting & future risk handling (Quantum Scenario Combinatorics)
    is_scenario_context = bool(
        re.search(r"\b(czy\s+rosja|czy\s+zaatakuje|czy\s+napadnie|wojn\w*|inwazj\w*|konflikt\w*|prawdopodobie[nń]stw\w*|prognoz\w*|ryzyk\w*|scenariusz\w*|szansa\s+na|zagro[zż]eni\w*|krach\w*|kryzys\w*)\b", lower)
    )
    if is_scenario_context:
        if len(words) < 3:
            return InputQuality(
                level="too_vague",
                reason="Pytanie o prognozę przyszłości jest zbyt krótkie.",
                suggestions=["Sformułuj pełniejsze pytanie o scenariusze rozwoju sytuacji."],
            )
        return InputQuality(level="sufficient", reason="", suggestions=[])

    # 1. Too short / vague (< 5 words)
    if len(words) < 5:
        return InputQuality(
            level="too_vague",
            reason="Opis sytuacji jest zbyt skrótowy lub ogólnikowy, by zbudować z niego rzetelny model matematyczny.",
            suggestions=[
                "Podaj konkretne warianty lub ścieżki wyboru (np. 'Kupić mieszkanie czy wynajmować').",
                "Określ kluczowe ograniczenia: dostępny budżet, czas lub nieprzekraczalne warunki.",
                "Sprecyzuj swój główny cel: maksymalizacja zysku, spokój, czy minimalizacja ryzyka?",
            ],
        )

    # 2. Lack of alternatives / degrees of freedom
    has_alternatives = bool(
        options_count >= 2
        or re.search(r"\b(czy|albo|lub|zamiast|wyb[oó]r|wybierz|wariant|opcj[aei]|versus|vs|mi[eę]dzy|spo[sś]r[oó]d|ofert[aeiy]|projekt[a-ząćęłńóśźż]*)\b", lower)
        or re.search(r"\b(zmieni[cć]|zosta[cć]|kupi[cć]|sprzeda[cć]|zainwestowa[cć])\b", lower)
    )
    if not has_alternatives and options_count < 2:
        return InputQuality(
            level="needs_options",
            reason="Brak zdefiniowanych alternatyw decyzyjnych. Optymalizacja wymaga co najmniej dwóch konkurencyjnych ścieżek.",
            suggestions=[
                "Wskaż minimum dwie opcje (np. 'Opcja A: etat w korporacji, Opcja B: własny software house').",
                "Określ, co rozważasz jako alternatywę dla obecnego stanu rzeczy.",
            ],
        )

    # 3. Missing numbers in financial / numerical context
    financial_keywords = re.search(
        r"\b(inwest\w*|bud[zż]et\w*|koszt\w*|zarob\w*|kredyt\w*|cen\w*|kwot\w*|oszcz[eę]dn\w*|kapita[łl]\w*|pensj\w*|pieni[aą]dz\w*)\b",
        lower,
    )
    has_numbers = bool(re.search(r"\d+", cleaned))
    if financial_keywords and not has_numbers:
        return InputQuality(
            level="needs_numbers",
            reason="Dylemat dotyczy finansów lub alokacji zasobów, ale nie podano żadnych liczb ani limitów.",
            suggestions=[
                "Podaj szacunkowy budżet lub maksymalny akceptowalny koszt (np. 'limit 50 000 zł').",
                "Określ spodziewane zarobki lub wydatki w liczbach.",
                "Wskaż horyzont czasowy w miesiącach lub latach.",
            ],
        )

    return InputQuality(level="sufficient", reason="", suggestions=[])
