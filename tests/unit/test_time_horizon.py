"""
Testy deterministycznego dekodera horyzontu czasowego (DEC-034).

Regresja, którą te testy zamykają: pytanie "Czy Rosja do końca tego roku zaatakuje
Polskę?" było odrzucane przez bramkę jakości jako pozbawione perspektywy czasowej,
mimo że perspektywa była w nim wprost wyrażona.
"""
from datetime import date

import pytest

from backend.domain.cognitive.time_horizon import detect_time_horizon, has_time_horizon
from backend.domain.cognitive.quality_gate import assess_input_quality

TODAY = date(2026, 9, 15)


@pytest.mark.parametrize(
    "query,expected_end,expected_basis",
    [
        ("Czy Rosja do końca tego roku zaatakuje Polskę?", date(2026, 12, 31), "current_year"),
        ("Czy Rosja zaatakuje Polskę w tym roku?", date(2026, 12, 31), "current_year"),
        ("Czy Rosja zaatakuje Polskę w przyszłym roku?", date(2027, 12, 31), "next_year"),
        ("Czy Rosja zaatakuje Polskę do 2027?", date(2027, 12, 31), "explicit_year"),
        ("Czy do końca dekady wybuchnie wojna w Europie?", date(2029, 12, 31), "end_of_decade"),
        ("Czy do marca 2027 dojdzie do eskalacji?", date(2027, 3, 31), "explicit_month"),
        ("Czy w ciągu 18 miesięcy Rosja uderzy na kraje bałtyckie?", date(2028, 3, 15), "relative_months"),
        ("Czy w ciągu trzech lat dojdzie do ataku Rosji na NATO?", date(2029, 9, 15), "relative_years"),
        ("Czy Rosja w ciągu najbliższych 3 lat zaatakuje Polskę?", date(2029, 9, 15), "relative_years"),
    ],
)
def test_precise_horizons_are_decoded(query, expected_end, expected_basis):
    h = detect_time_horizon(query, today=TODAY)
    assert h is not None, f"nie rozpoznano horyzontu w: {query}"
    assert h.is_precise is True
    assert h.end_date == expected_end
    assert h.basis == expected_basis


def test_imprecise_phrase_is_recognised_but_no_date_is_invented():
    """Wyrażenie bez liczby jest horyzontem, ale daty nie wolno zmyślać."""
    h = detect_time_horizon("Czy w najbliższych miesiącach wybuchnie kryzys?", today=TODAY)
    assert h is not None
    assert h.is_precise is False
    assert h.end_date is None


@pytest.mark.parametrize(
    "query",
    [
        "Czy Rosja zaatakuje Polskę?",
        "Wybór kursu językowego: hiszpański czy włoski?",
        "",
    ],
)
def test_no_horizon_returns_none(query):
    assert detect_time_horizon(query, today=TODAY) is None
    assert has_time_horizon(query, today=TODAY) is False


def test_quality_gate_no_longer_asks_when_horizon_is_present():
    """
    Regresja wprost: to pytanie MUSI przejść bramkę, bez proszenia o horyzont.
    """
    q = assess_input_quality("Czy Rosja do końca tego roku zaatakuje Polskę?")
    assert q.level == "sufficient", f"bramka nadal odrzuca pytanie z horyzontem: {q.reason}"


def test_quality_gate_still_asks_when_horizon_is_absent():
    """Kontrola negatywna: bez perspektywy czasowej bramka nadal ma dopytać."""
    q = assess_input_quality("Czy Rosja zaatakuje Polskę?")
    assert q.level == "too_vague"
