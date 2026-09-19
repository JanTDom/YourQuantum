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

## 5. Pomiar produkcyjny

**Zapytanie:** „Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?" na `https://yourquantum.pl/api/v1/cognitive/intake`.

### 5.1 Przed wdrożeniem (stary build, 2026-09-19, 21:03)

| Wielkość | Wartość |
|---|---|
| Udokumentowane komórki | 3 z 18 (16,7%) |
| Zweryfikowane cytaty odrzucone z obliczenia | 19 |
| Obszary bez danych | 1 („Standard cyfryzacji i telemedycyny") |
| Wynik | **wstrzymany** — „Nie mam wystarczających danych, żeby wskazać najlepszy wariant." |

Jeden obszar bez liczb skasował całą odpowiedź, a 19 zweryfikowanych cytatów przepadło bez śladu.

### 5.2 Przerwa: limit wydatków u dostawcy

Pierwsze biegi po wdrożeniu zwracały 0 stron w 7 sekund. Logi runtime Vercela podały przyczynę: `Gemini Search Grounding returned status 429: "Your project has exceeded its monthly spending cap"`. Nie był to defekt kodu — wyszukiwarka odmawiała odpowiedzi. Po podniesieniu limitu w Google AI Studio ścieżka ruszyła bez żadnej zmiany w aplikacji. Przy okazji dołożono telemetrię (`design_search_results_total`, `design_search_empty_queries`, `design_search_failures`, `design_search_available`), żeby następnym razem odróżnić „nic nie znaleziono" od „dostawca odmówił" bez zaglądania do logów.

### 5.3 Po wdrożeniu (2026-09-19, 23:5x)

| Wielkość | Wartość |
|---|---|
| Czas odpowiedzi | 183,8 s (silnik 170,6 s) |
| Zapytania do wyszukiwarki / pobrane strony | 5 / 10 |
| Wywołania ekstrakcji | 48 |
| Udokumentowane komórki | 6 z 44 (13,6%) |
| Obszary wyłączone z porównania | 0 — każdy z 4 obszarów miał dane |
| Cytaty odrzucone regułą 2B | 11, z czego **8 pokazanych** w sekcji „Co mówią dokumenty" |
| Cytaty stojące za policzonymi liczbami | 5 |
| Etykieta | **Wstępne** |
| Wynik | ranking policzony i pokazany, warianty wymienione z nazwy |

Nagłówek warstwy dla laika: *„Wstępnie, na danych, które udało się znaleźć, najlepiej wypada: Publiczny, oparty na składkach (Bismarckowski), Dominacja placówek prywatnych (kontraktowanych), Silna POZ z rolą 'gatekeepera' i jeszcze 1 wariant. Traktuj to jako wskazówkę, nie rozstrzygnięcie."*
Nota: *„Wynik stoi na 6 liczbach wyjętych z dokumentów; żadnej nie dopisałem od siebie."* — bez ani jednego procentu.

**Uwaga metodologiczna:** rozmiary macierzy w 5.1 i 5.2 różnią się (18 wobec 44 komórek), bo dekompozycja problemu powstaje osobno w każdym biegu. Porównywalna jest reguła, nie liczba komórek: przy pokryciu 13,6% stary build wstrzymałby wynik, nowy pokazuje go jako wstępny i nazywa warianty.

## 6. Do wykonania

1. Push i wdrożenie poprawki odmiany („i jeszcze 1 wariant" zamiast „i jeszcze 1") oraz telemetrii wyszukiwania — krok po stronie właściciela projektu.
2. Biała strona po kliknięciu w mózg 3D — osobny defekt, niezwiązany z DEC-048, wymaga reprodukcji w zalogowanej sesji.
