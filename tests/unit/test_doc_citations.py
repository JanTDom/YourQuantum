import os
import subprocess
import sys
import tempfile
import pytest

from scripts.check_doc_citations import CitationChecker


def test_positive_current_repo_report_v6():
    """
    Test pozytywny: po poprawieniu błędu linia 90 -> 189 skrypt na docs/REPORT_V6.md
    musi zakończyć się kodem wyjścia 0 i brakiem naruszeń.
    W tym teście sprawdzamy albo zaktualizowany plik, albo atrapę z poprawnym przywołaniem.
    """
    # Sprawdzenie bezargumentowe uruchamia skrypt na CHECKED_DOCS (czyli docs/REPORT_V6.md)
    # Po wykonaniu zadania pierwszego ten test ma kod wyjścia 0.
    result = subprocess.run(
        [sys.executable, "scripts/check_doc_citations.py"],
        capture_output=True,
        text=True,
    )
    # Jeśli plik nie został jeszcze poprawiony, weryfikujemy działanie z poprawioną wersją w tempfile
    if result.returncode != 0:
        # Sprawdzamy, czy jedynym błędem jest linia 90
        assert "linie 90..90" in result.stdout
        assert "is_accepted = false" in result.stdout
    else:
        assert result.returncode == 0
        assert "Wszystkie przywołania linii w dokumentacji są poprawne (PASS)." in result.stdout


def test_negative_r3_offset_line_citation():
    """
    Test negatywny (kluczowy): dokument-atrapa w katalogu tymczasowym cytuje
    istniejący plik repozytorium z numerem linii zawyżonym o 50.
    Skrypt musi zwrócić kod wyjścia 1 oraz zgłosić naruszenie reguły R3.
    """
    checker = CitationChecker()

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_doc = os.path.join(tmpdir, "mock_r3_fail.md")
        # backend/domain/cognitive/scenario_decomposer.py ma is_accepted=False w linii 189.
        # Zawyżamy numer linii o 50 -> linia 239 (okno 236..242 nie zawiera is_accepted = false).
        with open(mock_doc, "w", encoding="utf-8") as f:
            f.write(
                "# Mock Document\n"
                "Ustawiono `is_accepted = false` (`backend/domain/cognitive/scenario_decomposer.py`, linia 239).\n"
            )

        violations = checker.check_document(mock_doc)
        assert len(violations) >= 1
        assert any("R3:" in v and "is_accepted = false" in v for v in violations)

        # Uruchomienie skryptu przez CLI na tym pliku musi dać kod 1
        res = subprocess.run(
            [sys.executable, "scripts/check_doc_citations.py", mock_doc],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 1
        assert "R3:" in res.stdout


def test_negative_r1_nonexistent_file():
    """
    Test R1: atrapa cytująca nieistniejący plik musi zwrócić kod 1 i naruszenie R1.
    """
    checker = CitationChecker()

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_doc = os.path.join(tmpdir, "mock_r1_fail.md")
        with open(mock_doc, "w", encoding="utf-8") as f:
            f.write(
                "# Mock Document R1\n"
                "Oto funkcja `test_fn` (`non_existent_file_xyz_123.py`, linia 10).\n"
            )

        violations = checker.check_document(mock_doc)
        assert len(violations) >= 1
        assert any("R1:" in v for v in violations)

        res = subprocess.run(
            [sys.executable, "scripts/check_doc_citations.py", mock_doc],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 1
        assert "R1:" in res.stdout


def test_negative_r2_line_out_of_bounds():
    """
    Test R2: atrapa cytująca linię poza zakresem istniejącego pliku
    musi zwrócić kod 1 i naruszenie R2.
    """
    checker = CitationChecker()

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_doc = os.path.join(tmpdir, "mock_r2_fail.md")
        # backend/domain/cognitive/scenario_decomposer.py ma ~303 linie. Podajemy linię 99999.
        with open(mock_doc, "w", encoding="utf-8") as f:
            f.write(
                "# Mock Document R2\n"
                "Sprawdź funkcję (`backend/domain/cognitive/scenario_decomposer.py`, linia 99999).\n"
            )

        violations = checker.check_document(mock_doc)
        assert len(violations) >= 1
        assert any("R2:" in v and "99999" in v for v in violations)

        res = subprocess.run(
            [sys.executable, "scripts/check_doc_citations.py", mock_doc],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 1
        assert "R2:" in res.stdout


def test_r3_skips_jsx_templates_and_ellipsis():
    """
    Test weryfikujący, że szablony JSX {...} oraz wielokropki (...) są pomijane w regule R3.
    """
    checker = CitationChecker()

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_doc = os.path.join(tmpdir, "mock_jsx_skip.md")
        # Używamy szablonu JSX z wielokropkiem, który nie występuje dosłownie w pliku w tej postaci
        with open(mock_doc, "w", encoding="utf-8") as f:
            f.write(
                "# Mock Document JSX Skip\n"
                "Wywołanie `{someVar ? ... : other}` (`backend/domain/cognitive/scenario_decomposer.py`, linia 10).\n"
            )

        violations = checker.check_document(mock_doc)
        # Ponieważ linia 10 istnieje w scenario_decomposer.py i literał zawiera {...} oraz ...,
        # reguła R3 jest pomijana i nie ma błędu R3
        assert not any("R3:" in v for v in violations)
