"""Testy warstwy opisowej dla laika (V24 §B / DEC-046)."""
from backend.domain.cognitive.plain_briefing import (
    BriefSentence,
    build_plain_briefing,
    find_jargon,
    find_unsupported,
    _pl,
)


class _Opt:
    def __init__(self, i, t):
        self.id, self.title = i, t


class _Lev:
    def __init__(self, i, n, opts):
        self.id, self.name, self.options = i, n, opts


class _Crit:
    def __init__(self, i, n):
        self.id, self.name = i, n


class _Cell:
    def __init__(self, value, quote, src="NFZ", ref="https://example.test/raport"):
        self.value, self.quote = value, quote
        self.source_title, self.source_ref = src, ref


def _problem(matrix=None):
    class P:
        levers = [
            _Lev("l1", "Model finansowania", [_Opt("o1", "Budżet państwa"), _Opt("o2", "Składka NFZ")]),
            _Lev("l2", "Rola POZ", [_Opt("o3", "Wzmocniona POZ")]),
        ]
        criteria = [_Crit("c1", "Efektywność kosztowa"), _Crit("c2", "Dostępność")]
        score_matrix = matrix or {}
    return P()


def test_kazde_zdanie_ma_podstawe():
    b = build_plain_briefing(
        _problem(), documented_cells=0, total_cells=6, empty_levers=["Model finansowania"],
        rejected_off_topic=2, rejected_duplicate=0, pages_fetched=5, extraction_calls=20,
        ranking_withheld=True, ranking_withheld_reason="Brak danych.",
    )
    assert find_unsupported(b) == []


def test_brak_zargonu_technicznego():
    b = build_plain_briefing(
        _problem(), documented_cells=3, total_cells=6, empty_levers=[],
        rejected_off_topic=0, rejected_duplicate=0, pages_fetched=5, extraction_calls=20,
        ranking_withheld=False, ranking_withheld_reason=None,
        optimal_titles={"l1": "Budżet państwa"},
    )
    assert find_jargon(b) == []


def test_zero_danych_daje_uczciwy_naglowek():
    b = build_plain_briefing(
        _problem(), documented_cells=0, total_cells=6, empty_levers=["Model finansowania", "Rola POZ"],
        rejected_off_topic=0, rejected_duplicate=0, pages_fetched=0, extraction_calls=0,
        ranking_withheld=True, ranking_withheld_reason="Brak danych.",
    )
    assert "wystarczających danych" in b.headline.text
    assert any("niczego nie wpisałem od siebie" in s.text for s in b.summary)


def test_cytaty_niosa_zrodlo_i_tresc():
    matrix = {"l1": {"o1": {"c1": _Cell(7.2, "Wydatki publiczne na zdrowie wyniosły 7,2 proc. PKB.")}}}
    b = build_plain_briefing(
        _problem(matrix), documented_cells=1, total_cells=6, empty_levers=["Rola POZ"],
        rejected_off_topic=0, rejected_duplicate=0, pages_fetched=4, extraction_calls=12,
        ranking_withheld=False, ranking_withheld_reason=None,
    )
    assert len(b.evidence) == 1
    assert b.evidence[0].basis == "quoted"
    assert b.evidence[0].quote
    assert b.evidence[0].source_ref == "https://example.test/raport"
    assert find_unsupported(b) == []


def test_zdanie_quoted_bez_cytatu_jest_wykrywane():
    b = build_plain_briefing(
        _problem(), documented_cells=0, total_cells=6, empty_levers=[],
        rejected_off_topic=0, rejected_duplicate=0, pages_fetched=1, extraction_calls=1,
        ranking_withheld=True, ranking_withheld_reason=None,
    )
    b.evidence.append(BriefSentence(text="Z doświadczeń innych krajów wynika, że...", basis="quoted", quote=None))
    assert find_unsupported(b), "zdanie bez cytatu musi zostać wykryte"


def test_polska_odmiana_liczebnika():
    assert _pl(1, "wariant", "warianty", "wariantów") == "wariant"
    assert _pl(3, "wariant", "warianty", "wariantów") == "warianty"
    assert _pl(5, "wariant", "warianty", "wariantów") == "wariantów"
    assert _pl(12, "wariant", "warianty", "wariantów") == "wariantów"
    assert _pl(22, "wariant", "warianty", "wariantów") == "warianty"


def test_briefing_serializuje_sie_do_slownika():
    b = build_plain_briefing(
        _problem(), documented_cells=0, total_cells=6, empty_levers=[],
        rejected_off_topic=0, rejected_duplicate=0, pages_fetched=0, extraction_calls=0,
        ranking_withheld=True, ranking_withheld_reason=None,
    )
    d = b.model_dump(mode="json")
    assert d["headline"]["basis"] == "computed"
    assert isinstance(d["summary"], list)


def test_wynik_wstepny_ma_ostrozny_naglowek():
    b = build_plain_briefing(
        _problem(), documented_cells=3, total_cells=18, empty_levers=[],
        rejected_off_topic=4, rejected_duplicate=0, pages_fetched=9, extraction_calls=36,
        ranking_withheld=False, ranking_withheld_reason=None,
        optimal_titles={"l1": "Budżet państwa"}, preliminary=True,
    )
    assert "Wstępnie" in b.headline.text
    assert "nie rozstrzygnięcie" in b.headline.text
    assert find_unsupported(b) == []
    assert find_jargon(b) == []


# --- DEC-048 ---------------------------------------------------------------

_BASE = dict(
    documented_cells=3, total_cells=12, empty_levers=[],
    rejected_off_topic=0, rejected_duplicate=0, pages_fetched=9, extraction_calls=40,
    ranking_withheld=False, ranking_withheld_reason=None,
)


def test_wylaczony_obszar_dostaje_jedno_zdanie_zamiast_blokady():
    b = build_plain_briefing(
        _problem(), **_BASE,
        optimal_titles={"Model finansowania": "Składka NFZ"},
        preliminary=True,
        excluded_levers=[{"name": "Rola POZ", "reason": "no_data"}],
    )
    assert b.label == "wstepne"
    assert "Składka NFZ" in b.headline.text
    zdania = " ".join(s.text for s in b.summary)
    assert "Rola POZ" in zdania
    assert "nie znalazłem twardych danych" in zdania
    assert not find_unsupported(b) and not find_jargon(b)


def test_obszar_nierozroznialny_jest_nazwany_wprost():
    b = build_plain_briefing(
        _problem(), **_BASE,
        optimal_titles={"Model finansowania": "Składka NFZ"},
        preliminary=True,
        excluded_levers=[{"name": "Rola POZ", "reason": "indistinguishable"}],
    )
    zdania = " ".join(s.text for s in b.summary)
    assert "Rola POZ" in zdania and "tak samo" in zdania


def test_odrzucone_cytaty_trafiaja_do_sekcji_dokumentow():
    b = build_plain_briefing(
        _problem(), **{**_BASE, "rejected_off_topic": 2},
        optimal_titles={"Model finansowania": "Składka NFZ"},
        context_findings=[
            {"quote": "Nakłady na ochronę zdrowia wyniosły 6,2% PKB.",
             "source_ref": "https://example.test/a", "source_title": "GUS"},
            {"quote": "Nakłady na ochronę zdrowia wyniosły 6,2% PKB.",
             "source_ref": "https://example.test/b", "source_title": "OECD"},
            {"quote": "Liczba lekarzy POZ wzrosła o 4%.",
             "source_ref": "https://example.test/c", "source_title": "NFZ"},
        ],
    )
    # duplikat cytatu odpada, zostają dwa różne
    assert len(b.context) == 2
    assert all(s.basis == "quoted" and s.quote for s in b.context)
    assert "GUS" in b.context[0].text
    assert not find_unsupported(b)


def test_warstwa_dla_laika_nie_pokazuje_procentow_ani_pokrycia():
    b = build_plain_briefing(
        _problem(), **_BASE,
        optimal_titles={"Model finansowania": "Składka NFZ"},
        excluded_levers=[{"name": "Rola POZ", "reason": "no_data"}],
    )
    widoczne = " ".join(
        s.text for s in [b.headline, b.confidence_note] + b.summary + b.tipping_points if s
    )
    assert "%" not in widoczne
    assert "pokryci" not in widoczne.lower()


def test_etykieta_policzone_gdy_komplet_obszarow():
    b = build_plain_briefing(
        _problem(), **_BASE,
        optimal_titles={"Model finansowania": "Składka NFZ"},
        preliminary=False,
        excluded_levers=[],
    )
    assert b.label == "policzone"


def test_brak_danych_to_jedyny_przypadek_bez_odpowiedzi():
    b = build_plain_briefing(
        _problem(), **{**_BASE, "documented_cells": 0, "ranking_withheld": True,
                       "ranking_withheld_reason": "Brak udokumentowanych danych."},
    )
    assert b.label == "brak_danych"
    assert "Nie mam wystarczających danych" in b.headline.text
