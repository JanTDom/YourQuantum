"""
YourQuantum — warstwa opisowa dla laika (V24 §B / DEC-046).

Buduje krótkie, zrozumiałe podsumowanie wyniku analizy projektowej (klasa DESIGN).

BEZWZGLĘDNA ZASADA: każde zdanie briefingu ma jedną z dwóch podstaw:
  - "computed" — zdanie opisuje wyłącznie to, co policzył silnik (liczby wariantów,
    komórek, obszarów, marginesy). Powstaje deterministycznie z danych, nie z modelu.
  - "quoted"  — zdanie przytacza dokument źródłowy; niesie cytat i odnośnik.

Moduł NIE wywołuje modelu językowego. Nie ma tu miejsca, w którym mogłaby powstać
liczba lub teza bez pokrycia. Zdanie bez podstawy nie może zostać utworzone,
bo pole `basis` jest wymagane, a bramka G-BRIEF sprawdza to mechanicznie.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# Żargon, który nie ma prawa pojawić się w warstwie dla laika (V24 §B1).
FORBIDDEN_JARGON = ("pareto", "softmax", "front ", "dominacj", "gibbs", "argmax")


@dataclass
class BriefSentence:
    """Pojedyncze zdanie briefingu wraz z podstawą, na której stoi."""
    text: str
    basis: Literal["computed", "quoted"]
    source_ref: str | None = None
    quote: str | None = None

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        return {"text": self.text, "basis": self.basis,
                "source_ref": self.source_ref, "quote": self.quote}


@dataclass
class PlainBriefing:
    headline: BriefSentence
    summary: list[BriefSentence] = field(default_factory=list)
    confidence_note: BriefSentence | None = None
    tipping_points: list[BriefSentence] = field(default_factory=list)
    evidence: list[BriefSentence] = field(default_factory=list)

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        return {
            "headline": self.headline.model_dump(),
            "summary": [x.model_dump() for x in self.summary],
            "confidence_note": self.confidence_note.model_dump() if self.confidence_note else None,
            "tipping_points": [x.model_dump() for x in self.tipping_points],
            "evidence": [x.model_dump() for x in self.evidence],
        }


def _c(text: str) -> BriefSentence:
    return BriefSentence(text=text, basis="computed")


def _q(text: str, source_ref: str | None, quote: str | None) -> BriefSentence:
    return BriefSentence(text=text, basis="quoted", source_ref=source_ref, quote=quote)


def _pl(n: int, one: str, few: str, many: str) -> str:
    """Poprawna polska odmiana liczebnika: 1 wariant, 2 warianty, 5 wariantów."""
    n = abs(int(n))
    if n == 1:
        return one
    last, last_two = n % 10, n % 100
    if 2 <= last <= 4 and not (12 <= last_two <= 14):
        return few
    return many


def _join_names(names: list[str], limit: int = 3) -> str:
    shown = names[:limit]
    rest = len(names) - len(shown)
    joined = ", ".join(shown)
    return f"{joined} i jeszcze {rest}" if rest > 0 else joined


def build_plain_briefing(
    design_problem: Any,
    *,
    documented_cells: int,
    total_cells: int,
    empty_levers: list[str],
    rejected_off_topic: int,
    rejected_duplicate: int,
    pages_fetched: int,
    extraction_calls: int,
    ranking_withheld: bool,
    ranking_withheld_reason: str | None,
    optimal_titles: dict[str, str] | None = None,
) -> PlainBriefing:
    """Składa briefing wyłącznie z policzonych wielkości i zacytowanych dokumentów."""
    levers = list(getattr(design_problem, "levers", []) or [])
    criteria = list(getattr(design_problem, "criteria", []) or [])
    n_variants = sum(len(getattr(l, "options", []) or []) for l in levers)

    # --- Nagłówek -----------------------------------------------------------
    if ranking_withheld or documented_cells == 0:
        headline = _c("Nie mam wystarczających danych, żeby wskazać najlepszy wariant.")
    elif optimal_titles:
        wybrane = _join_names(list(optimal_titles.values()))
        headline = _c(f"Przy podanych wagach najlepiej wypada: {wybrane}.")
    else:
        headline = _c("Porównanie policzone na znalezionych danych — szczegóły poniżej.")

    # --- Streszczenie -------------------------------------------------------
    summary: list[BriefSentence] = [
        _c(
            f"Porównałem {n_variants} {_pl(n_variants, 'wariant', 'warianty', 'wariantów')} "
            f"w {len(levers)} {_pl(len(levers), 'obszarze', 'obszarach', 'obszarach')}, "
            f"według {len(criteria)} {_pl(len(criteria), 'kryterium', 'kryteriów', 'kryteriów')}."
        ),
        _c(
            f"Sprawdziłem {pages_fetched} {_pl(pages_fetched, 'stronę', 'strony', 'stron')} w sieci "
            f"i wykonałem {extraction_calls} {_pl(extraction_calls, 'próbę', 'próby', 'prób')} odczytania z nich danych."
        ),
    ]
    if documented_cells == 0:
        summary.append(_c(
            f"Nie znalazłem ani jednej z {total_cells} potrzebnych danych — i niczego nie wpisałem od siebie."
        ))
    else:
        summary.append(_c(
            f"Znalazłem {documented_cells} z {total_cells} potrzebnych danych — "
            f"każda pochodzi z dokumentu, żadnej nie wymyśliłem."
        ))
    if empty_levers:
        summary.append(_c(
            f"Dla {len(empty_levers)} {_pl(len(empty_levers), 'obszaru', 'obszarów', 'obszarów')} "
            f"nie znalazłem żadnych liczb ({_join_names(empty_levers)}), więc nie wpłynęły one na wynik."
        ))
    if rejected_off_topic:
        summary.append(_c(
            f"Odrzuciłem {rejected_off_topic} "
            f"{_pl(rejected_off_topic, 'znalezioną liczbę', 'znalezione liczby', 'znalezionych liczb')}, "
            f"bo zdanie źródłowe nie dotyczyło porównywanego wariantu."
        ))
    if rejected_duplicate:
        summary.append(_c(
            f"Odrzuciłem {rejected_duplicate} {_pl(rejected_duplicate, 'liczbę', 'liczby', 'liczb')} "
            f"jako powtórzenie tego samego dowodu w innym miejscu."
        ))
    if ranking_withheld and ranking_withheld_reason:
        summary.append(_c(f"Wstrzymałem wskazanie najlepszego wariantu. Powód: {ranking_withheld_reason}"))

    # --- Na czym stoi wynik -------------------------------------------------
    if total_cells > 0:
        pct = round(documented_cells / total_cells * 100, 1)
        confidence_note = _c(
            f"Wynik opiera się na {documented_cells} z {total_cells} danych, czyli na {pct}% tego, "
            f"co byłoby potrzebne do pełnego porównania."
        )
    else:
        confidence_note = _c("Nie udało się zbudować żadnego porównania.")

    # --- Co by musiało się zmienić -----------------------------------------
    tipping: list[BriefSentence] = []
    if empty_levers:
        tipping.append(_c(
            f"Gdyby udało się znaleźć dane dla obszaru „{empty_levers[0]}”, wynik mógłby się zmienić — "
            f"dziś ten obszar w ogóle nie waży."
        ))
    if documented_cells > 0 and not ranking_withheld:
        tipping.append(_c(
            "Zmiana wag kryteriów przelicza wynik natychmiast — możesz sprawdzić, przy jakim ustawieniu przewaga znika."
        ))
    tipping.append(_c(
        "Każdą liczbę możesz nadpisać własną; wtedy wchodzi do obliczenia na równi z danymi z sieci."
    ))

    # --- Cytaty z dokumentów ------------------------------------------------
    evidence: list[BriefSentence] = []
    score_matrix = getattr(design_problem, "score_matrix", {}) or {}
    for lev in levers:
        for opt in getattr(lev, "options", []) or []:
            for crit in criteria:
                cell = score_matrix.get(lev.id, {}).get(opt.id, {}).get(crit.id)
                if cell is None or getattr(cell, "value", None) is None:
                    continue
                quote = getattr(cell, "quote", None)
                if not quote:
                    continue
                src = getattr(cell, "source_title", None) or getattr(cell, "source_ref", None) or "źródło"
                evidence.append(_q(
                    text=f"{src} — {opt.title}, {crit.name}: „{quote.strip()}”",
                    source_ref=getattr(cell, "source_ref", None),
                    quote=quote,
                ))
                if len(evidence) >= 5:
                    break
            if len(evidence) >= 5:
                break
        if len(evidence) >= 5:
            break

    return PlainBriefing(
        headline=headline,
        summary=summary,
        confidence_note=confidence_note,
        tipping_points=tipping,
        evidence=evidence,
    )


def find_jargon(briefing: PlainBriefing) -> list[str]:
    """Zwraca zdania zawierające żargon techniczny (kontrola dla bramki G-BRIEF)."""
    offenders: list[str] = []
    sentences = [briefing.headline] + briefing.summary + briefing.tipping_points
    if briefing.confidence_note:
        sentences.append(briefing.confidence_note)
    for s in sentences:
        low = s.text.lower()
        if any(j in low for j in FORBIDDEN_JARGON):
            offenders.append(s.text)
    return offenders


def find_unsupported(briefing: PlainBriefing) -> list[str]:
    """Zdania bez prawidłowej podstawy albo zdania 'quoted' bez cytatu (bramka G-BRIEF)."""
    bad: list[str] = []
    sentences = [briefing.headline] + briefing.summary + briefing.tipping_points + briefing.evidence
    if briefing.confidence_note:
        sentences.append(briefing.confidence_note)
    for s in sentences:
        if s.basis not in ("computed", "quoted"):
            bad.append(s.text)
        elif s.basis == "quoted" and not (s.quote and s.quote.strip()):
            bad.append(s.text)
    return bad
