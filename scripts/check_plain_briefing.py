#!/usr/bin/env python3
"""
Bramka G-BRIEF (V24 §B5 / DEC-046).

Sprawdza mechanicznie, że warstwa opisowa dla laika nie może przemycić twierdzenia
bez pokrycia:

  R1. Każde zdanie briefingu ma podstawę "computed" albo "quoted".
  R2. Zdanie oznaczone "quoted" niesie niepusty cytat.
  R3. Zdania streszczenia nie zawierają żargonu technicznego (Pareto, softmax, ...).
  R4. Moduł budujący briefing nie wywołuje modelu językowego.
  R5. Warstwa dla laika nie pokazuje procentów ani słowa "pokrycie" (DEC-048).
  R6. Sekcja "Co mówią dokumenty" niesie wyłącznie zacytowane zdania z cytatem,
      a żadna liczba z niej nie ma wartości wchodzącej do obliczenia (DEC-048).

Kod wyjścia 0 = wszystko w porządku.
"""
from __future__ import annotations

import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

MODULE_PATH = os.path.join(REPO, "backend", "domain", "cognitive", "plain_briefing.py")
LLM_CALL_PATTERNS = (
    r"LLMGateway", r"GeminiCognitiveAdapter", r"generate_content",
    r"\.complete\(", r"reasoning_port", r"openai", r"anthropic",
)


def check_no_llm_in_module() -> list[str]:
    if not os.path.isfile(MODULE_PATH):
        return ["Brak pliku backend/domain/cognitive/plain_briefing.py"]
    src = open(MODULE_PATH, encoding="utf-8").read()
    bad = [f"R4: moduł briefingu odwołuje się do modelu językowego ({pat})"
           for pat in LLM_CALL_PATTERNS if re.search(pat, src)]
    return bad


def check_briefing_contract() -> list[str]:
    from backend.domain.cognitive.plain_briefing import (
        build_plain_briefing, find_jargon, find_unsupported,
    )

    class _Opt:
        def __init__(self, i, t): self.id, self.title = i, t

    class _Lev:
        def __init__(self, i, n, opts): self.id, self.name, self.options = i, n, opts

    class _Crit:
        def __init__(self, i, n): self.id, self.name = i, n

    class _Problem:
        def __init__(self):
            self.levers = [_Lev("l1", "Model finansowania", [_Opt("o1", "Budżet"), _Opt("o2", "Składka")])]
            self.criteria = [_Crit("c1", "Efektywność")]
            self.score_matrix = {}

    problems: list[str] = []

    # Przypadek pozytywny: brak danych -> uczciwy nagłówek, zero zdań bez podstawy.
    b = build_plain_briefing(
        _Problem(), documented_cells=0, total_cells=2, empty_levers=["Model finansowania"],
        rejected_off_topic=3, rejected_duplicate=0, pages_fetched=7, extraction_calls=24,
        ranking_withheld=True, ranking_withheld_reason="Brak danych.",
    )
    problems += [f"R1/R2: {t}" for t in find_unsupported(b)]
    problems += [f"R3: żargon w zdaniu: {t}" for t in find_jargon(b)]
    if "wystarczających danych" not in b.headline.text:
        problems.append("R1: przy zerze danych nagłówek nie mówi wprost o braku danych")

    # R5: warstwa widoczna dla laika bez procentów i bez słowa "pokrycie".
    b2 = build_plain_briefing(
        _Problem(), documented_cells=4, total_cells=12, empty_levers=[],
        rejected_off_topic=2, rejected_duplicate=1, pages_fetched=11, extraction_calls=48,
        ranking_withheld=False, ranking_withheld_reason=None,
        optimal_titles={"Model finansowania": "Składka"},
        preliminary=True,
        excluded_levers=[{"name": "Rola POZ", "reason": "no_data"}],
        context_findings=[{"quote": "Nakłady wyniosły 6,2% PKB.",
                           "source_ref": "https://example.test/a", "source_title": "GUS"}],
    )
    widoczne = " ".join(
        x.text for x in ([b2.headline] + b2.summary + b2.tipping_points
                         + ([b2.confidence_note] if b2.confidence_note else []))
    )
    if "%" in widoczne:
        problems.append("R5: warstwa dla laika zawiera procenty")
    if "pokryci" in widoczne.lower():
        problems.append("R5: warstwa dla laika używa słowa 'pokrycie'")
    if b2.label not in ("policzone", "wstepne", "brak_danych"):
        problems.append(f"R5: nieznana etykieta wyniku: {b2.label}")
    if b2.label != "wstepne":
        problems.append("R5: wynik na niepełnych obszarach musi mieć etykietę 'wstepne'")

    # R6: sekcja kontekstu — same cytaty, żadnej wartości liczbowej do obliczenia.
    for x in b2.context:
        if x.basis != "quoted" or not (x.quote and x.quote.strip()):
            problems.append(f"R6: zdanie sekcji dokumentów bez cytatu: {x.text}")
        if getattr(x, "value", None) is not None:
            problems.append("R6: zdanie sekcji dokumentów niesie wartość liczbową")
    problems += [f"R1/R2: {t}" for t in find_unsupported(b2)]
    problems += [f"R3: żargon w zdaniu: {t}" for t in find_jargon(b2)]

    # Przypadek negatywny: zdanie 'quoted' bez cytatu musi zostać wykryte.
    from backend.domain.cognitive.plain_briefing import BriefSentence
    b.evidence.append(BriefSentence(text="Coś tam podobno wynika.", basis="quoted", quote=None))
    if not find_unsupported(b):
        problems.append("R2: kontrola nie wykrywa zdania 'quoted' bez cytatu")

    return problems


def main() -> int:
    issues = check_no_llm_in_module() + check_briefing_contract()
    if issues:
        for i in issues[:10]:
            print(i, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
