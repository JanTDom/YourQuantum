import os
import tempfile
import pytest
from scripts.check_report_evidence import check_report_v14, check_report_v16_if_exists


def test_positive_current_repo_report_v14():
    repo_v14 = os.path.join(os.path.dirname(__file__), "../../docs/REPORT_V14.md")
    violations = check_report_v14(repo_v14)
    assert violations == [], f"Oczekiwano braku naruszeń w docs/REPORT_V14.md, otrzymano: {violations}"


def test_negative_fabricated_facebook_url():
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as f:
        f.write("""
Czy Rosja zaatakuje kraje bałtyckie do końca 2027 roku?
Czy Polska wybuduje pierwszą elektrownię jądrową do 2033 roku?
Czy inflacja w Polsce spadnie poniżej celu NBP do końca 2026 roku?
URL: https://www.facebook.com/nbppl/posts/123456789
Cały zestaw testów repozytorium: 250 passed w czasie 120.0s.
""")
        tmp_path = f.name
    try:
        violations = check_report_v14(tmp_path)
        assert any("facebook.com/nbppl/posts/123456789" in v for v in violations)
    finally:
        os.remove(tmp_path)


def test_negative_unrealistic_test_time():
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as f:
        f.write("""
Czy Rosja zaatakuje kraje bałtyckie do końca 2027 roku?
Czy Polska wybuduje pierwszą elektrownię jądrową do 2033 roku?
Czy inflacja w Polsce spadnie poniżej celu NBP do końca 2026 roku?
Cały zestaw testów repozytorium: 240/240 passed w czasie 28.52s.
""")
        tmp_path = f.name
    try:
        violations = check_report_v14(tmp_path)
        assert any("Nierealistyczny czas testów" in v for v in violations)
    finally:
        os.remove(tmp_path)


def test_negative_fabricated_query_names():
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as f:
        f.write("""
[1/3] Zapytanie: Czy do 2027 roku dojdzie do militarnego starcia na Bałtyku?
Czy Polska wybuduje pierwszą elektrownię jądrową do 2033 roku?
Czy inflacja w Polsce spadnie poniżej celu NBP do końca 2026 roku?
Cały zestaw testów repozytorium: 250 passed w czasie 120.0s.
""")
        tmp_path = f.name
    try:
        violations = check_report_v14(tmp_path)
        assert any("Zmyślone zapytanie diagnostyczne" in v for v in violations)
    finally:
        os.remove(tmp_path)
