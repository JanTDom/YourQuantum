#!/usr/bin/env python3
"""
scripts/check_doc_citations.py

Weryfikuje maszynowo przywołania kodu w dokumentacji YourQuantum.
Sprawdza trzy reguły:
- R1: Przywołany plik istnieje na dysku (obsługuje ścieżki pełne i skrócone).
- R2: Przywołana linia (lub zakres) mieści się w granicach pliku.
- R3: Literał w backtickach bezpośrednio poprzedzający przywołanie występuje
      w oknie ±3 linie od przywołania w pliku źródłowym (z normalizacją białych znaków,
      pomijając szablony JSX {...} oraz wielokropki).
"""

import sys
import os
import re
import subprocess
from typing import List, Tuple, Optional, Dict

CHECKED_DOCS: List[str] = [
    "docs/REPORT_V6.md",
    "docs/REPORT_V9.md",
    "docs/REPORT_V11.md",
    "docs/REPORT_V12.md",
    "docs/REPORT_V13.md",
    "docs/REPORT_V14.md",
    "docs/REPORT_V18.md",
    "docs/REPORT_V19.md",
]

# Ignorowane katalogi przy indeksowaniu plików
IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".pytest_cache"}


class CitationChecker:
    def __init__(self, repo_root: Optional[str] = None):
        self.repo_root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self._file_cache: Optional[Dict[str, List[str]]] = None

    def _build_file_cache(self) -> Dict[str, List[str]]:
        if self._file_cache is not None:
            return self._file_cache
        cache: Dict[str, List[str]] = {}
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), self.repo_root)
                cache.setdefault(f, []).append(rel_path)
        self._file_cache = cache
        return cache

    def resolve_file(self, fname: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Zwraca (relatywna_ścieżka_pliku, komunikat_błędu).
        """
        fname = fname.strip("`'\" \t")
        full_candidate = os.path.join(self.repo_root, fname)
        if os.path.isfile(full_candidate):
            return os.path.relpath(full_candidate, self.repo_root), None

        cache = self._build_file_cache()
        base = os.path.basename(fname)
        matches = cache.get(base, [])

        if len(matches) == 1:
            matched = matches[0]
            if "/" in fname and not matched.endswith(fname):
                return None, f"R1: Przywołany plik '{fname}' nie istnieje na dysku (znaleziono plik o tej samej nazwie w innej ścieżce: '{matched}')."
            return matched, None
        elif len(matches) > 1:
            return None, f"R1: Nazwa pliku '{fname}' jest niejednoznaczna ({len(matches)} trafień: {', '.join(matches)}). Podaj pełną ścieżkę."
        else:
            return None, f"R1: Przywołany plik '{fname}' nie istnieje na dysku."

    @staticmethod
    def normalize_for_r3(s: str) -> str:
        """
        Normalizacja do porównania R3:
        - ciągi białych znaków zamieniane na pojedyncze spacje, obcięcie brzegów
        - spacje wokół operatorów i separatorów (=, :, ,)
        - usunięcie cudzysłowów i apostrofów wokół kluczy/stringów
        - małe litery
        """
        s = " ".join(s.split())
        s = re.sub(r"\s*([=:,])\s*", r"\1", s)
        s = re.sub(r"[\"\'\`]", "", s)
        return s.lower()

    def check_document(self, doc_path: str) -> List[str]:
        import subprocess

        violations: List[str] = []
        full_doc_path = os.path.join(self.repo_root, doc_path) if not os.path.isabs(doc_path) else doc_path

        if not os.path.isfile(full_doc_path):
            violations.append(f"{doc_path}:1 - R1: Dokument do sprawdzenia '{doc_path}' nie istnieje na dysku.")
            return violations

        with open(full_doc_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        sticky_file: Optional[str] = None

        # Wykrywamy gałąź odniesienia z nagłówka dokumentu (np. Gałąź: `feat/v9-technical-debt`)
        doc_branch: Optional[str] = None
        for head_line in lines[:10]:
            b_match = re.search(r"(?:branch|ga[ł\u0142][a\u0105][ź\u017a])[^\`\n]*?\`([a-zA-Z0-9_./-]+)\`", head_line, re.IGNORECASE)
            if b_match:
                doc_branch = b_match.group(1).strip("`'\" ()")
                break

        for line_no, line_text in enumerate(lines, 1):
            # R1: Sprawdzenie wszystkich ścieżek plików w backtickach w całym dokumencie (nawet bez numerów linii)
            for bt_match in re.finditer(r"\`([^\`\n]+)\`", line_text):
                raw_cand = bt_match.group(1).strip()
                if not raw_cand or " " in raw_cand or "\t" in raw_cand:
                    continue
                cand = raw_cand.split("::")[0].strip("'\"()[]{}")
                if cand.startswith(("http://", "https://", "api/", "/api/", "assets/", "dist/", "frontend/dist/")):
                    continue
                if any(c in cand for c in "*?$<>="):
                    continue
                if cand.endswith("/"):
                    continue

                ext = os.path.splitext(cand)[1].lower()
                base = os.path.basename(cand)
                is_file = (base in {"Dockerfile", "Makefile"}) or (
                    ext in {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".sh", ".yml", ".yaml", ".txt", ".html", ".css", ".sql", ".toml"}
                    and ("/" in cand or ext in {".py", ".tsx", ".ts", ".sh"} or base in {"package.json", "tsconfig.json"})
                )
                if not is_file:
                    continue

                resolved_path, err = self.resolve_file(cand)
                if err:
                    # Sprawdzamy gałąź z nagłówka, gałąź z linii lub commit
                    target_refs: List[str] = []
                    if doc_branch:
                        target_refs.append(doc_branch)
                    for lb in re.finditer(r"(?:branch|ga[ł\u0142][a\u0105eę][źz][a-z]*)[^\`\n]*?\`([a-zA-Z0-9_./-]+)\`", line_text, re.IGNORECASE):
                        target_refs.append(lb.group(1).strip("`'\" ()"))
                    for lc in re.finditer(r"\b([0-9a-f]{7,40})\b", line_text):
                        target_refs.append(lc.group(1))

                    found_in_ref = False
                    for ref in target_refs:
                        check_ref = subprocess.run(
                            ["git", "rev-parse", "--verify", f"{ref}:{cand}"],
                            capture_output=True,
                            cwd=self.repo_root,
                        )
                        if check_ref.returncode == 0:
                            found_in_ref = True
                            break

                    if found_in_ref:
                        continue

                    violations.append(f"{doc_path}:{line_no} - {err}")
            # Szukamy nawiasów zawierających przywołania linii: (linia N), (linie N–M), (plik, linia N) itp.
            for p_match in re.finditer(r"\(([^)\n]*?lini[a-z]*?[^)\n]*?)\)", line_text, re.IGNORECASE):
                inside = p_match.group(1)
                p_start = p_match.start()

                # Szukamy literału w backtickach w odległości do 200 znaków wstecz w tym samym zdaniu
                prefix = line_text[:p_start]
                bt_matches = list(re.finditer(r"\`([^\`\n]+)\`", prefix))
                literal: Optional[str] = None
                if bt_matches:
                    last_bt = bt_matches[-1]
                    if p_start - last_bt.end() <= 200:
                        between = prefix[last_bt.end():]
                        # Sprawdzamy, czy nie przekroczono granicy zdania (. ! ? z następującą spacją)
                        if not re.search(r"(?<![0-9a-zA-Z_./\-])[.!?]\s+", between):
                            literal = last_bt.group(1)

                # Wnętrze nawiasu może zawierać wiele przywołań rozdzielonych średnikiem
                sub_citations = inside.split(";")
                for sub in sub_citations:
                    sub = sub.strip()
                    if not sub:
                        continue

                    # Sprawdzenie, czy przywołanie zawiera jawną nazwę pliku
                    fn_match = re.search(r"\`?([a-zA-Z0-9_./-]+\.(?:tsx|ts|py|md|json|sh|yml|txt|html))\`?", sub)
                    if not fn_match:
                        # Może nazwa pliku występuje w prefixie bezpośrednio przed nawiasem? (np. `plik.py` (linie X-Y))
                        prefix_fn = re.search(r"\`?([a-zA-Z0-9_./-]+\.(?:tsx|ts|py|md|json|sh|yml|txt|html))\`?\s*$", prefix)
                        if prefix_fn:
                            fn_match = prefix_fn
                    if fn_match:
                        fname_raw = fn_match.group(1)
                        resolved_path, err = self.resolve_file(fname_raw)
                        if err:
                            violations.append(f"{doc_path}:{line_no} - {err}")
                            continue
                        sticky_file = resolved_path

                    # Parsowanie numeru linii / zakresu: linia N, linie N–M, linie N-M, linie N, M
                    num_match = re.search(r"lini[a-z]*\s*([0-9\s–—,-]+)", sub, re.IGNORECASE)
                    if not num_match:
                        continue

                    raw_nums = num_match.group(1)
                    ranges: List[Tuple[int, int]] = []
                    for part in raw_nums.split(","):
                        part = part.strip()
                        range_match = re.search(r"(\d+)\s*[-–—]\s*(\d+)", part)
                        if range_match:
                            ranges.append((int(range_match.group(1)), int(range_match.group(2))))
                        else:
                            single_match = re.search(r"(\d+)", part)
                            if single_match:
                                val = int(single_match.group(1))
                                ranges.append((val, val))

                    if not ranges:
                        continue

                    # R1: Brak pliku lepkiego / bieżącego
                    if not sticky_file:
                        violations.append(f"{doc_path}:{line_no} - R1: Przywołanie '{sub}' bez nazwy pliku, a brak wcześniejszego pliku odniesienia.")
                        continue

                    target_abs = os.path.join(self.repo_root, sticky_file)
                    if not os.path.isfile(target_abs):
                        violations.append(f"{doc_path}:{line_no} - R1: Przywołany plik '{sticky_file}' nie istnieje na dysku.")
                        continue

                    with open(target_abs, "r", encoding="utf-8", errors="replace") as tf:
                        target_file_lines = tf.readlines()

                    total_lines = len(target_file_lines)

                    # R2: Linia istnieje w pliku
                    r2_failed = False
                    for start_l, end_l in ranges:
                        if start_l < 1 or end_l > total_lines or start_l > end_l:
                            violations.append(
                                f"{doc_path}:{line_no} - R2: Zakres linii {start_l}..{end_l} wykracza poza rozmiar pliku '{sticky_file}' (plik ma {total_lines} linii)."
                            )
                            r2_failed = True
                    if r2_failed:
                        continue

                    # R3: Sprawdzenie trafienia w treść
                    if literal:
                        # Jeśli literał to po prostu nazwa pliku odniesienia, pomijamy szukanie go w treści kodu
                        if (fn_match and literal == fn_match.group(1)) or (sticky_file and (literal == sticky_file or literal == os.path.basename(sticky_file))):
                            literal = None

                    if literal:
                        # Pomijamy szablony JSX {...} oraz wielokropki (...) i (…)
                        if re.search(r"\{.*?\}|\.\.\.|\u2026", literal):
                            continue

                        min_line = min(r[0] for r in ranges)
                        max_line = max(r[1] for r in ranges)

                        # Okno: cytowana linia ±3 linie (dla zakresu: min - 3 do max + 3)
                        w_start = max(1, min_line - 3)
                        w_end = min(total_lines, max_line + 3)

                        window_text = "".join(target_file_lines[w_start - 1 : w_end])
                        norm_window = self.normalize_for_r3(window_text)
                        norm_lit = self.normalize_for_r3(literal)

                        # Opcjonalnie odcięcie dopisanego wyniku ewaluacji wyrażenia (=true, =false)
                        lit_core = re.sub(r"=(true|false)$", "", norm_lit).strip()

                        matches_literal = (norm_lit in norm_window) or (bool(lit_core) and lit_core in norm_window)

                        if not matches_literal:
                            violations.append(
                                f"{doc_path}:{line_no} - R3: Przywołanie ({sticky_file}, linie {min_line}..{max_line}) nie zawiera literału `{literal}` w oknie linii {w_start}..{w_end}."
                            )

        return violations

    def run(self, doc_list: Optional[List[str]] = None) -> int:
        docs_to_check = doc_list or CHECKED_DOCS
        all_violations: List[str] = []

        for doc in docs_to_check:
            violations = self.check_document(doc)
            all_violations.extend(violations)

        if all_violations:
            print("Wykryto naruszenia przywołań kodu w dokumentacji:")
            for v in all_violations:
                print(v)
            return 1
        else:
            print("Wszystkie przywołania linii w dokumentacji są poprawne (PASS).")
            return 0


def main() -> None:
    args = sys.argv[1:]
    doc_list = args if args else None
    checker = CitationChecker()
    exit_code = checker.run(doc_list)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
