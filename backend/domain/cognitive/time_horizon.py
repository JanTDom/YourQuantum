"""
YourQuantum — Deterministyczny dekoder horyzontu czasowego (język polski).

Wyodrębnia perspektywę czasową z pytania prognostycznego i normalizuje ją do daty
końcowej. Nie zgaduje: jeżeli wyrażenie jest nieprecyzyjne (np. "w najbliższych
miesiącach"), zwraca horyzont bez daty końcowej (`end_date=None`, `is_precise=False`),
zamiast wymyślać liczbę. Zero wywołań LLM — wyłącznie reguły.
"""
from __future__ import annotations

import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date

# Liczebniki słowne w dopełniaczu i mianowniku (1-12) + "kilku"/"kilkunastu" jako nieprecyzyjne.
_WORD_NUMERALS: dict[str, int] = {
    "jednego": 1, "jeden": 1, "roku": 1,
    "dwóch": 2, "dwoch": 2, "dwa": 2, "dwu": 2,
    "trzech": 3, "trzy": 3,
    "czterech": 4, "cztery": 4,
    "pięciu": 5, "pieciu": 5, "pięć": 5, "piec": 5,
    "sześciu": 6, "szesciu": 6, "sześć": 6, "szesc": 6,
    "siedmiu": 7, "siedem": 7,
    "ośmiu": 8, "osmiu": 8, "osiem": 8,
    "dziewięciu": 9, "dziewieciu": 9, "dziewięć": 9, "dziewiec": 9,
    "dziesięciu": 10, "dziesieciu": 10, "dziesięć": 10, "dziesiec": 10,
    "jedenastu": 11, "jedenaście": 11,
    "dwunastu": 12, "dwanaście": 12, "dwanascie": 12,
    "osiemnastu": 18, "osiemnaście": 18,
    "dwudziestu": 20, "dwadzieścia": 20,
}

_MONTHS: dict[str, int] = {
    "stycznia": 1, "styczeń": 1, "styczniu": 1,
    "lutego": 2, "luty": 2, "lutym": 2,
    "marca": 3, "marzec": 3, "marcu": 3,
    "kwietnia": 4, "kwiecień": 4, "kwietniu": 4,
    "maja": 5, "maj": 5, "maju": 5,
    "czerwca": 6, "czerwiec": 6, "czerwcu": 6,
    "lipca": 7, "lipiec": 7, "lipcu": 7,
    "sierpnia": 8, "sierpień": 8, "sierpniu": 8,
    "września": 9, "wrzesień": 9, "wrześniu": 9,
    "października": 10, "październik": 10, "październiku": 10,
    "listopada": 11, "listopad": 11, "listopadzie": 11,
    "grudnia": 12, "grudzień": 12, "grudniu": 12,
}

_MONTH_LABEL = {v: k for k, v in _MONTHS.items() if k.endswith("a") or k == "maja"}


@dataclass(frozen=True)
class TimeHorizon:
    """Rozpoznana perspektywa czasowa."""
    raw: str                  # dosłowny fragment pytania, z którego pochodzi
    label: str                # czytelny opis dla użytkownika
    end_date: date | None     # znormalizowana data końcowa (None = wyrażenie nieprecyzyjne)
    basis: str                # jak wyznaczono: reguła użyta do dekodowania
    is_precise: bool          # czy dało się wyznaczyć konkretną datę końcową


def _end_of_year(y: int) -> date:
    return date(y, 12, 31)


def _add_months(d: date, months: int) -> date:
    total = d.month - 1 + months
    y = d.year + total // 12
    m = total % 12 + 1
    return date(y, m, min(d.day, monthrange(y, m)[1]))


def _numeral(token: str) -> int | None:
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return _WORD_NUMERALS.get(token)


def detect_time_horizon(text: str, today: date | None = None) -> TimeHorizon | None:
    """
    Zwraca rozpoznany horyzont czasowy albo None, gdy pytanie go nie zawiera.
    `today` wstrzykiwane w testach; domyślnie bieżąca data systemowa.
    """
    if not text or not text.strip():
        return None
    now = today or date.today()
    t = " ".join(text.lower().split())

    # 1. Jawny rok: "do 2027", "do końca 2027 roku", "przed 2030", "w 2028 roku"
    m = re.search(r"\b(?:do|przed|w)\s+(?:ko[nń]ca\s+)?(?:roku\s+)?((?:19|20|21)\d{2})\b", t)
    if m:
        y = int(m.group(1))
        return TimeHorizon(m.group(0), f"do końca {y} roku", _end_of_year(y), "explicit_year", True)

    # 2. Jawny miesiąc z rokiem lub bez: "do marca 2027", "do końca marca"
    m = re.search(r"\bdo\s+(?:ko[nń]ca\s+)?(" + "|".join(_MONTHS) + r")(?:\s+((?:19|20|21)\d{2}))?\b", t)
    if m:
        mon = _MONTHS[m.group(1)]
        y = int(m.group(2)) if m.group(2) else (now.year if mon >= now.month else now.year + 1)
        end = date(y, mon, monthrange(y, mon)[1])
        return TimeHorizon(m.group(0), f"do końca {_MONTH_LABEL.get(mon, m.group(1))} {y}", end, "explicit_month", True)

    # 3. "do końca tego roku", "w tym roku", "jeszcze w tym roku"
    if re.search(r"\b(?:do\s+ko[nń]ca\s+(?:tego\s+)?roku|w\s+tym\s+roku|jeszcze\s+w\s+tym\s+roku|w\s+bie[zż][aą]cym\s+roku)\b", t):
        m2 = re.search(r"\b(?:do\s+ko[nń]ca\s+(?:tego\s+)?roku|w\s+tym\s+roku|jeszcze\s+w\s+tym\s+roku|w\s+bie[zż][aą]cym\s+roku)\b", t)
        return TimeHorizon(m2.group(0), f"do końca {now.year} roku", _end_of_year(now.year), "current_year", True)

    # 4. "w przyszłym roku", "do końca przyszłego roku"
    if re.search(r"\b(?:w\s+przysz[lł]ym\s+roku|do\s+ko[nń]ca\s+przysz[lł]ego\s+roku|w\s+nadchodz[aą]cym\s+roku)\b", t):
        m2 = re.search(r"\b(?:w\s+przysz[lł]ym\s+roku|do\s+ko[nń]ca\s+przysz[lł]ego\s+roku|w\s+nadchodz[aą]cym\s+roku)\b", t)
        y = now.year + 1
        return TimeHorizon(m2.group(0), f"do końca {y} roku", _end_of_year(y), "next_year", True)

    # 5. "w ciągu N lat", "w perspektywie najbliższych N lat", "przez N lat"
    m = re.search(
        r"\b(?:w\s+ci[aą]gu|w\s+perspektywie|przez|przez\s+najbli[zż]sze|w\s+ci[aą]gu\s+najbli[zż]szych|najbli[zż]szych|najbli[zż]sze)?\s*"
        r"([0-9]+|" + "|".join(_WORD_NUMERALS) + r")\s+(lat|lata|roku|rok|latach)\b", t)
    if m:
        n = _numeral(m.group(1))
        if n:
            end = date(now.year + n, now.month, min(now.day, monthrange(now.year + n, now.month)[1]))
            return TimeHorizon(m.group(0).strip(), f"w ciągu {n} lat (do {end.isoformat()})", end, "relative_years", True)

    # 6. "w ciągu N miesięcy", "najbliższych N miesięcy"
    m = re.search(
        r"\b(?:w\s+ci[aą]gu|w\s+perspektywie|przez|najbli[zż]szych|najbli[zż]sze)?\s*"
        r"([0-9]+|" + "|".join(_WORD_NUMERALS) + r")\s+(miesi[eę]cy|miesi[aą]ce|miesi[aą]ca|miesi[aą]c)\b", t)
    if m:
        n = _numeral(m.group(1))
        if n:
            end = _add_months(now, n)
            return TimeHorizon(m.group(0).strip(), f"w ciągu {n} miesięcy (do {end.isoformat()})", end, "relative_months", True)

    # 7. "do końca dekady"
    if re.search(r"\bdo\s+ko[nń]ca\s+(?:tej\s+)?dekady\b", t):
        y = (now.year // 10) * 10 + 9
        return TimeHorizon("do końca dekady", f"do końca {y} roku", _end_of_year(y), "end_of_decade", True)

    # 8. "w najbliższym roku"
    if re.search(r"\bw\s+najbli[zż]szym\s+roku\b", t):
        end = date(now.year + 1, now.month, min(now.day, monthrange(now.year + 1, now.month)[1]))
        return TimeHorizon("w najbliższym roku", f"w ciągu roku (do {end.isoformat()})", end, "relative_years", True)

    # 9. Wyrażenia nieprecyzyjne — horyzont JEST podany, ale bez liczby.
    #    Nie wymyślamy daty: end_date=None, is_precise=False.
    m = re.search(
        r"\b(w\s+najbli[zż]szych\s+(?:miesi[aą]cach|latach|tygodniach)|"
        r"w\s+najbli[zż]szym\s+czasie|w\s+perspektywie\s+d[lł]ugoterminowej|"
        r"w\s+kr[oó]tkim\s+okresie|w\s+d[lł]u[zż]szej\s+perspektywie|w\s+najbli[zż]szej\s+przysz[lł]o[sś]ci)\b", t)
    if m:
        return TimeHorizon(m.group(0), m.group(0), None, "imprecise_phrase", False)

    return None


def has_time_horizon(text: str, today: date | None = None) -> bool:
    """Skrót dla bramki jakości: czy pytanie zawiera jakkolwiek wyrażoną perspektywę czasową."""
    return detect_time_horizon(text, today) is not None
