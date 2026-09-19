# REPORT V25 — Odpowiedź zamiast odmowy (DEC-048)

**Data:** 2026-09-19
**Zakres:** klasa DESIGN — warunki wstrzymania wyniku, prezentacja materiału dowodowego, warstwa dla laika.
**Stan:** wdrożone w repozytorium, zweryfikowane lokalnie. Pomiar produkcyjny do wykonania po wdrożeniu.

---

## 1. Problem, który to naprawia

Pytanie „Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?" kończyło się komunikatem o braku danych, mimo że silnik miał kilkanaście zweryfikowanych faktów. Wystarczył jeden obszar bez liczb, żeby cała odpowiedź została wstrzymana. Równolegle 11–20 cytatów na bieg — zweryfikowanych co do dosłowności w tekście strony — było kasowanych tylko dlatego, że zdanie nie wymieniało porównywanego wariantu z nazwy.

Użytkownik przychodzi po odpowiedź. Uczciwość polega na powiedzeniu, na czym wynik stoi i czego zabrakło — nie na odmowie liczenia.

## 2. Co zostało zmienione

| # | Zmiana | Plik |
|---|--------|------|
| 1 | Obszar bez danych lub z identycznymi wartościami wszystkich wariantów **wypada z porównania**, zamiast je wstrzymywać. Nazwa i powód w `levers_excluded`. | `backend/domain/problem_classes.py` |
| 2 | Przestrzeń konfiguracji, ranking ważności, `optimal_titles` i filary briefingu liczone wyłącznie po obszarach aktywnych — wykluczony obszar nie dostaje podsuniętego wariantu. | `backend/domain/problem_classes.py` |
| 3 | Wstrzymanie wyniku zawężone do **zera zweryfikowanych faktów** (albo braku obszaru zdolnego odróżnić warianty). | `backend/domain/problem_classes.py` |
| 4 | Cytaty odrzucone regułą 2B zbierane i przekazywane do sekcji „Co mówią dokumenty (nie weszło do obliczenia)". Bez wartości liczbowej, bez kontaktu z macierzą. | `backend/domain/cognitive/active_inference_engine.py` |
| 5 | Warstwa dla laika: dwie etykiety (`Policzone`, `Wstępne`), zdania o wykluczonych obszarach, sekcja kontekstu, **zero procentów i zero słowa „pokrycie"**. | `backend/domain/cognitive/plain_briefing.py` |
| 6 | Interfejs: plakietka etykiety nad nagłówkiem, nowa sekcja cytatów spoza obliczenia, warstwa techniczna nadal zwinięta. | `frontend/src/components/DesignWorkspace.tsx` |
| 7 | Bramka G-BRIEF: reguła R5 (brak procentów, poprawna etykieta) i R6 (sekcja dokumentów wyłącznie z cytatami). | `scripts/check_plain_briefing.py` |

## 3. Czego ta zmiana NIE rusza

- `_verify_quote_in_text` pozostaje dosłowne. Żadnego dopasowania rozmytego, częściowego ani podobieństwowego.
- Reguła trafienia w wariant (2B) i zakaz duplikatów (2C) obowiązują bez zmian — cytat, który ich nie przechodzi, **nadal nie obsadza komórki**. Zmieniło się wyłącznie to, że zamiast trafić do kosza, zostaje pokazany jako kontekst.
- Liczba wchodzi do obliczenia wyłącznie ze zweryfikowanego dokumentu albo od decydenta.
- Ochrona SSRF i walidacja przekierowań w `backend/infrastructure/web_research/fetcher.py` — nietknięte.
- Żadne pole interfejsu nie prosi użytkownika o wpisanie brakujących liczb. Ręczne nadpisanie wartości pozostaje dostępne w warstwie technicznej, jako możliwość, a nie jako warunek otrzymania wyniku.

## 4. Weryfikacja lokalna

**Bramki mechaniczne** (`scripts/check_v4.sh`): 25 z 26 zielonych, w tym G-BRIEF z nowymi regułami R5 i R6.
G-TESTS czerwona z powodów środowiskowych, niezależnych od tej zmiany: `.venv/bin/pytest` ma shebang macOS, `node_modules` zawiera binarium rollup dla macOS, a interpreter pomocniczy nie ma `ortools`. Kompilacja `tsc -b` przechodzi czysto, 67 testów jednostkowych przechodzi.

**Testy jednostkowe dopisane w tej fazie:**

- `tests/unit/test_design_v22.py::test_empty_lever_is_excluded_not_blocking` — obszar bez danych wypada z porównania, wynik powstaje, obszar nie ma podsuniętego wariantu ani filaru, ale jest nazwany w założeniach.
- `tests/unit/test_design_v22.py::test_only_zero_facts_withholds_the_answer` — przy zerze faktów wstrzymanie nadal obowiązuje.
- `tests/unit/test_plain_briefing.py` — sześć testów: zdanie o obszarze bez danych, obszar nierozróżnialny, sekcja dokumentów z odsiewem powtórzonych cytatów, brak procentów i słowa „pokrycie", etykieta `policzone`, etykieta `brak_danych`.

**Przebieg kontrolny** na zestawie trzech obszarów (jeden z danymi, jeden z identycznymi wartościami wariantów, jeden pusty) dał wynik wstępny wskazujący wariant z nazwy, dwa zdania o wykluczonych obszarach oraz notę „Wynik stoi na 8 liczbach wyjętych z dokumentów; żadnej nie dopisałem od siebie." — bez ani jednego procentu w warstwie dla laika.

## 5. Do wykonania po wdrożeniu

1. `git push origin main` i wdrożenie produkcyjne — krok po stronie właściciela projektu.
2. Pomiar na `https://yourquantum.pl`: zapytanie o system ochrony zdrowia powinno zwrócić wynik z etykietą `Wstępne`, wymienić warianty z nazwy i pokazać sekcję „Co mówią dokumenty".
3. Dopisać wynik pomiaru do tego raportu.
