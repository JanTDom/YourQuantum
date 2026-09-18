#!/usr/bin/env python3
"""
scripts/check_report_evidence.py — Mechanical Gate G-EVID

Weryfikuje autentyczność i rzetelność raportów z wdrożenia (REPORT_V14.md, REPORT_V15.md, REPORT_V16.md):
1. Sekcja 3A w REPORT_V14.md nie może zawierać sfabrykowanych artefaktów (np. fikcyjny URL facebook.com/nbppl/posts/123456789).
2. Weryfikuje, że zapytania w sekcji diagnostycznej odpowiadają rzeczywistym zapytaniom ze skryptu diag_evidence_chain.py:
   - "Czy Rosja zaatakuje kraje bałtyckie do końca 2027 roku?"
   - "Czy Polska wybuduje pierwszą elektrownię jądrową do 2033 roku?"
   - "Czy inflacja w Polsce spadnie poniżej celu NBP do końca 2026 roku?"
3. Czasy wykonania zestawu testów pytest podawane w raportach muszą być realne:
   - Cały zestaw testów repozytorium wykonuje rzeczywiste zapytania sieciowe i trwa > 60 sekund.
   - Niedopuszczalne są zmyślone czasy rzędu 28 sekund na 240+ testów.
"""

import os
import re
import sys
from typing import List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

FORBIDDEN_FABRICATED_PATTERNS = [
    (r"facebook\.com/nbppl/posts/123456789", "facebook.com/nbppl/posts/123456789"),
    (r"Czy do 2027 roku dojdzie do militarnego starcia na Bałtyku\?", "Zmyślone zapytanie diagnostyczne: 'Czy do 2027 roku dojdzie do militarnego starcia na Bałtyku?'"),
    (r"Czy w Polsce w 2033 roku powstanie pierwsza elektrownia jądrowa\?", "Zmyślone zapytanie diagnostyczne: 'Czy w Polsce w 2033 roku powstanie pierwsza elektrownia jądrowa?'"),
    (r"Czy inflacja w Polsce spadnie poniżej celu NBP \(2\.5%\) do końca 2026\?", "Zmyślone zapytanie diagnostyczne: 'Czy inflacja w Polsce spadnie poniżej celu NBP (2.5%) do końca 2026?'"),
]

EXPECTED_QUERIES = [
    "Czy Rosja zaatakuje kraje bałtyckie do końca 2027 roku?",
    "Czy Polska wybuduje pierwszą elektrownię jądrową do 2033 roku?",
    "Czy inflacja w Polsce spadnie poniżej celu NBP do końca 2026 roku?",
]


def check_report_v14(report_path: str) -> List[str]:
    violations: List[str] = []
    if not os.path.exists(report_path):
        return [f"Brak pliku {report_path}"]

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Zakazane fikcyjne wzorce
    for pattern, desc in FORBIDDEN_FABRICATED_PATTERNS:
        if re.search(pattern, content):
            violations.append(f"Wykryto sfabrykowany artefakt w {os.path.basename(report_path)}: {desc}")

    # 2. Obecność rzeczywistych zapytań z diag_evidence_chain.py
    for eq in EXPECTED_QUERIES:
        if eq not in content:
            violations.append(f"Brak wymaganego rzeczywistego zapytania diagnostycznego w {os.path.basename(report_path)}: '{eq}'")

    # 3. Kontrola realności czasu testów w sekcji B
    match = re.search(r"Cały zestaw testów repozytorium[^\n]*w czasie\s*([0-9\.]+)\s*s", content)
    if match:
        seconds = float(match.group(1))
        if seconds < 60.0:
            violations.append(f"Nierealistyczny czas testów pytest w {os.path.basename(report_path)}: {seconds}s (< 60.0s wskazuje na fabrykowanie danych)")

    return violations


def check_report_v16_if_exists(report_path: str) -> List[str]:
    violations: List[str] = []
    if not os.path.exists(report_path):
        return violations

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    placeholders = ["TODO", "FIXME", "TBD", "[DO UZUPEŁNIENIA]", "XXX"]
    for ph in placeholders:
        if ph in content:
            violations.append(f"Wykryto placeholder '{ph}' w {os.path.basename(report_path)}")

    return violations


def main() -> int:
    report_v14_path = os.path.join(REPO_ROOT, "docs", "REPORT_V14.md")
    report_v16_path = os.path.join(REPO_ROOT, "docs", "REPORT_V16.md")

    all_violations: List[str] = []
    all_violations.extend(check_report_v14(report_v14_path))
    all_violations.extend(check_report_v16_if_exists(report_v16_path))

    if all_violations:
        print("=== G-EVID FAIL: Wykryto naruszenia rzetelności raportów ===")
        for v in all_violations:
            print(f"- {v}")
        return 1

    print("=== G-EVID PASS: Raporty zweryfikowane mechanicznie pod kątem autentyczności dowodów ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
