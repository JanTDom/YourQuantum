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


def assess_input_quality(text: str, options_count: int = 0) -> InputQuality:
    """
    Evaluate whether the user prompt contains enough degrees of freedom
    and specific data to model an exact mathematical dilemma.

    Checks:
    1. Too short / vague (< 8 words)
    2. Lack of alternatives / degrees of freedom (< 2 options or lack of alternative markers)
    3. Missing numbers in financial / resource allocation contexts
    """
    cleaned = text.strip()
    words = [w for w in cleaned.split() if len(w) > 1]
    lower = cleaned.lower()

    # 1. Too short / vague
    if len(words) < 8:
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
        or re.search(r"\b(czy|albo|lub|zamiast|wyb[oó]r|wariant|opcj[aei]|versus|vs|mi[eę]dzy)\b", lower)
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
