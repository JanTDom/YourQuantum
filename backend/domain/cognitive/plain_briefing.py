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


# Etykiety stanu wyniku pokazywane laikowi (DEC-048). Tylko trzy, bez procentów.
LABEL_COMPUTED = "policzone"
LABEL_PRELIMINARY = "wstepne"
LABEL_NO_DATA = "brak_danych"


@dataclass
class PlainBriefing:
    headline: BriefSentence
    summary: list[BriefSentence] = field(default_factory=list)
    confidence_note: BriefSentence | None = None
    tipping_points: list[BriefSentence] = field(default_factory=list)
    evidence: list[BriefSentence] = field(default_factory=list)
    # DEC-048: zweryfikowane cytaty, które NIE weszły do obliczenia (nie wymieniały wariantu).
    # Warstwa wyłącznie prezentacyjna — żadna liczba stąd nie dotyka macierzy.
    context: list[BriefSentence] = field(default_factory=list)
    label: str = LABEL_COMPUTED

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        return {
            "headline": self.headline.model_dump(),
            "summary": [x.model_dump() for x in self.summary],
            "confidence_note": self.confidence_note.model_dump() if self.confidence_note else None,
            "tipping_points": [x.model_dump() for x in self.tipping_points],
            "evidence": [x.model_dump() for x in self.evidence],
            "context": [x.model_dump() for x in self.context],
            "label": self.label,
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


def _join_names(
    names: list[str],
    limit: int = 3,
    noun: tuple[str, str, str] = ("pozycja", "pozycje", "pozycji"),
) -> str:
    """Wylicza nazwy, a nadmiar skraca z poprawnie odmienionym rzeczownikiem."""
    shown = names[:limit]
    rest = len(names) - len(shown)
    joined = ", ".join(shown)
    if rest <= 0:
        return joined
    return f"{joined} i jeszcze {rest} {_pl(rest, *noun)}"


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
    preliminary: bool = False,
    excluded_levers: list[dict[str, str]] | None = None,
    context_findings: list[dict[str, Any]] | None = None,
) -> PlainBriefing:
    """Składa briefing wyłącznie z policzonych wielkości i zacytowanych dokumentów."""
    levers = list(getattr(design_problem, "levers", []) or [])
    criteria = list(getattr(design_problem, "criteria", []) or [])
    n_variants = sum(len(getattr(l, "options", []) or []) for l in levers)

    # DEC-048: obszary wyłączone z porównania. Starsze wywołania podają samą listę nazw
    # obszarów bez danych — traktujemy je jak wyłączenie z powodu "no_data".
    excluded = list(excluded_levers or [{"name": n, "reason": "no_data"} for n in empty_levers])
    excluded_no_data = [e["name"] for e in excluded if e.get("reason") == "no_data"]
    excluded_same = [e["name"] for e in excluded if e.get("reason") == "indistinguishable"]
    compared_levers = max(len(levers) - len(excluded), 0)

    # --- Nagłówek -----------------------------------------------------------
    # DEC-048: "brak odpowiedzi" zostaje wyłącznie dla przypadku zera zweryfikowanych faktów.
    if ranking_withheld or documented_cells == 0:
        label = LABEL_NO_DATA
        headline = _c("Nie mam wystarczających danych, żeby wskazać najlepszy wariant.")
    elif optimal_titles:
        wybrane = _join_names(
            list(optimal_titles.values()), noun=("wariant", "warianty", "wariantów")
        )
        label = LABEL_PRELIMINARY if preliminary else LABEL_COMPUTED
        if preliminary:
            headline = _c(
                f"Wstępnie, na danych, które udało się znaleźć, najlepiej wypada: {wybrane}. "
                f"Traktuj to jako wskazówkę, nie rozstrzygnięcie."
            )
        else:
            headline = _c(f"Przy podanych wagach najlepiej wypada: {wybrane}.")
    else:
        label = LABEL_PRELIMINARY if preliminary else LABEL_COMPUTED
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
    if excluded_no_data:
        summary.append(_c(
            f"O {_pl(len(excluded_no_data), 'obszarze', 'obszarach', 'obszarach')} "
            f"{_join_names(excluded_no_data, noun=('obszar', 'obszary', 'obszarów'))} nie znalazłem twardych danych, "
            f"więc porównanie opiera się na {_pl(compared_levers, 'pozostałym obszarze', 'pozostałych obszarach', 'pozostałych obszarach')}."
        ))
    if excluded_same:
        summary.append(_c(
            f"W {_pl(len(excluded_same), 'obszarze', 'obszarach', 'obszarach')} "
            f"{_join_names(excluded_same, noun=('obszar', 'obszary', 'obszarów'))} znalezione liczby wyszły dla wszystkich wariantów "
            f"tak samo, więc ten fragment niczego nie rozstrzyga."
        ))
    if rejected_off_topic:
        summary.append(_c(
            f"Do obliczenia nie weszło {rejected_off_topic} "
            f"{_pl(rejected_off_topic, 'znaleziona liczba', 'znalezione liczby', 'znalezionych liczb')}, "
            f"bo zdanie źródłowe nie mówiło wprost o porównywanym wariancie — "
            f"znajdziesz je niżej, w tym, co mówią dokumenty."
        ))
    if rejected_duplicate:
        summary.append(_c(
            f"Odrzuciłem {rejected_duplicate} {_pl(rejected_duplicate, 'liczbę', 'liczby', 'liczb')} "
            f"jako powtórzenie tego samego dowodu w innym miejscu."
        ))
    if ranking_withheld and ranking_withheld_reason:
        summary.append(_c(f"Wstrzymałem wskazanie najlepszego wariantu. Powód: {ranking_withheld_reason}"))

    # --- Na czym stoi wynik -------------------------------------------------
    # DEC-048: w warstwie dla laika nie ma procentów ani słowa "pokrycie" —
    # te wielkości zostają w warstwie technicznej.
    if documented_cells > 0:
        confidence_note = _c(
            f"Wynik stoi na {documented_cells} "
            f"{_pl(documented_cells, 'liczbie wyjętej z dokumentu', 'liczbach wyjętych z dokumentów', 'liczbach wyjętych z dokumentów')}; "
            f"żadnej nie dopisałem od siebie."
        )
    else:
        confidence_note = _c("Nie udało się zbudować żadnego porównania.")

    # --- Co by musiało się zmienić -----------------------------------------
    tipping: list[BriefSentence] = []
    if excluded_no_data:
        tipping.append(_c(
            f"Gdyby udało się znaleźć dane dla obszaru „{excluded_no_data[0]}”, wynik mógłby się zmienić — "
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

    # --- Co mówią dokumenty (DEC-048) --------------------------------------
    # Cytaty zweryfikowane co do treści, ale odrzucone z obliczenia, bo zdanie
    # nie wymieniało porównywanego wariantu. Wchodzą wyłącznie do prezentacji:
    # nie mają wartości liczbowej i nie dotykają macierzy wyników.
    context: list[BriefSentence] = []
    seen_quotes: set[str] = set()
    for item in (context_findings or []):
        quote = str(item.get("quote") or "").strip()
        if not quote or quote in seen_quotes:
            continue
        seen_quotes.add(quote)
        src = str(item.get("source_title") or item.get("source_ref") or "źródło").strip()
        context.append(_q(text=f"{src}: „{quote}”", source_ref=item.get("source_ref"), quote=quote))
        if len(context) >= 8:
            break

    return PlainBriefing(
        headline=headline,
        summary=summary,
        confidence_note=confidence_note,
        tipping_points=tipping,
        evidence=evidence,
        context=context,
        label=label,
    )


def find_jargon(briefing: PlainBriefing) -> list[str]:
    """Zwraca zdania zawierające żargon techniczny (kontrola dla bramki G-BRIEF)."""
    offenders: list[str] = []
    sentences = [briefing.headline] + briefing.summary + briefing.tipping_points + briefing.context
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
    sentences = (
        [briefing.headline] + briefing.summary + briefing.tipping_points
        + briefing.evidence + briefing.context
    )
    if briefing.confidence_note:
        sentences.append(briefing.confidence_note)
    for s in sentences:
        if s.basis not in ("computed", "quoted"):
            bad.append(s.text)
        elif s.basis == "quoted" and not (s.quote and s.quote.strip()):
            bad.append(s.text)
    return bad
