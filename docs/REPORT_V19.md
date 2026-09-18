# RAPORT Z WDROŻENIA V19: ROZDZIAŁ SŁOWNIKÓW WPŁYWÓW, TELEMETRIA PRZYCZYN BRAKU PROPOZYCJI I POMIAR PRODUKCYJNY

**Data:** 2026-09-18  
**Autor wdrożenia:** Antigravity  
**Zlecenie:** Prompt V19 (Jan Domaniewski)  
**Środowisko:** Produkcja `https://yourquantum.pl` (Vercel deployment `macieto`)  
**Commit docelowy:** `70e3f59` (origin/main)

---

## 1. Cel i zakres zmian V19

Prompt V19 zamknął trzy kluczowe zagadnienia podniesione po audycie wdrożenia V18:
1. **Rozdział słowników wpływów i statusu `impact_source` per wpływ (Usterka poprawności):**
   - Wpływy ugruntowane w zweryfikowanych zdaniach z dokumentów (`ev.impact_on_scenarios`) trafiają wyłącznie do słownika `impact_on_scenarios: dict[str, float]`.
   - Nowe pole `impact_proposed: dict[str, float]` w modelu `EvidencePremise` przechowuje propozycje dekomponującego modelu językowego. Te propozycje nigdy nie są automatycznie scalane z ugruntowanymi wpływami i nigdy nie nadpisują zweryfikowanych liczb.
   - Pole `impact_source` stało się słownikiem `ImpactSourceDict` mapującym `scenario_id -> 'documented' | 'model_unverified' | 'user_defined'`, z pełną kompatybilnością wsteczną dla wartości pojedynczych stringów.
   - W agregacji softmax (`compute_scenario_distribution`) rozkład wyliczany jest **wyłącznie** ze słownika `impact_on_scenarios`. Niezaakceptowane propozycje z `impact_proposed` mają zerowy wpływ na rozkład (pozostaje ściśle neutralny / równomierny przy braku innych ugruntowanych przesłanek).
   - W interfejsie użytkownika (`frontend/src/components/RecommendationView.tsx`) komponent `PremiseScenarioImpacts` renderuje ugruntowane wpływy oraz niezweryfikowane propozycje modelu w sposób rozdzielny, umożliwiając decydentowi świadome zatwierdzenie każdej propozycji per scenariusz.

2. **Telemetria `impacts_not_proposed_reason`:**
   - W `EvidenceExtractor` (`backend/infrastructure/web_research/extractor.py`) oraz `ActiveInferenceOrchestrator` (`backend/domain/cognitive/active_inference_engine.py`) dodano pole `impacts_not_proposed_reason`.
   - Gdy `impacts_proposed == 0`, pole przyjmuje jedną z czterech ustandaryzowanych wartości:
     * `brak candidate_scenarios`
     * `model zwrócił pustą tablicę impacts`
     * `odpowiedź modelu nie przeszła walidacji schematu`
     * `przekroczony budżet`
   - Gdy propozycje zostały wygenerowane, pole ma wartość `None`.

3. **Optymalizacja czasu odpowiedzi (współbieżność):**
   - W `ActiveInferenceOrchestrator` Etap 1 (dekompozycja zapytania na scenariusze) oraz Etap 2 (wyszukiwanie sieciowe) zostały zrównoleglone za pomocą `asyncio.gather`, ponieważ oba etapy zależą wyłącznie od zapytania `query`.
   - Każdy pobrany dokument analizowany jest w Etapie 3 przez dedykowaną instancję `EvidenceExtractor`, eliminując współdzielony stan mutowalny.

---

## 2. Wyniki 10-biegowego pomiaru na żywej produkcji (`https://yourquantum.pl`)

Pomiar zrealizowano za pomocą zaktualizowanego skryptu `scripts/measure_forecast_stability.py` wysyłającego zapytania HTTP POST do produkcyjnego endpointu `/api/v1/cognitive/intake`:
- **Pytanie testowe:** *„Czy Rosja do końca tego roku napadnie na Polskę?”*
- **Liczba biegów:** 10 (od Biegu A do Biegu J)
- **Cel:** `https://yourquantum.pl`

### Tabela wyników pomiaru produkcyjnego

| Bieg | Zweryfikowane cytaty | Aktywne przesłanki | impacts_proposed | impacts_accepted | impact_rejected_unsupported | impacts_not_proposed_reason | impact_documented_share | Czas całkowity | Rozkład prawdopodobieństwa |
|------|----------------------|--------------------|------------------|------------------|-----------------------------|-----------------------------|-------------------------|----------------|----------------------------|
| Bieg A | 6 | 6 | 6 | 6 | 0 | — | 100,0% | 50,09 s | 76,0% / 18,3% / 5,7% |
| Bieg B | 6 | 6 | 9 | 9 | 0 | — | 100,0% | 33,47 s | 91,5% / 5,9% / 2,5% |
| Bieg C | 6 | 6 | 5 | 4 | 1 | — | 100,0% | 31,31 s | 43,0% / 43,0% / 14,0% |
| Bieg D | 5 | 5 | 7 | 5 | 2 | — | 100,0% | 35,83 s | 39,1% / 32,0% / 28,9% |
| Bieg E | 4 | 4 | 6 | 4 | 2 | — | 100,0% | 29,22 s | 69,5% / 19,0% / 11,5% |
| Bieg F | 7 | 7 | 10 | 10 | 0 | — | 100,0% | 34,74 s | 96,6% / 3,4% |
| Bieg G | 3 | 3 | 1 | 1 | 0 | — | 100,0% | 31,74 s | 37,7% / 37,7% / 24,7% |
| Bieg H | 7 | 7 | 6 | 4 | 2 | — | 100,0% | 36,27 s | 46,3% / 26,9% / 26,9% |
| Bieg I | 7 | 7 | 5 | 5 | 0 | — | 100,0% | 78,71 s | 51,0% / 26,2% / 22,8% |
| Bieg J | 6 | 6 | 9 | 6 | 3 | — | 100,0% | 29,88 s | 74,9% / 14,4% / 10,7% |

### Analiza parametrów telemetrii
1. **Liczba biegów z `impact_documented_share > 0`:**
   - **10 z 10 biegów (100,0%)** wykazało `impact_documented_share > 0`.
   - **Rozrzut `impact_documented_share`:** wartość minimalna = 100,0%, maksymalna = 100,0%, średnia = 100,0%.
   - Ani razu nie wystąpiła sytuacja, w której nieudokumentowane propozycje kształtowałyby rozkład bez uzasadnienia.
2. **Filtracja nieugruntowanych propozycji (`impact_rejected_unsupported`):**
   - Łącznie model zaproponował 64 wpływy w 10 biegach (`impacts_proposed` = 64).
   - Mechaniczna bramka G-EVID / DEC-040 zweryfikowała i zaakceptowała 54 wpływy poparte dosłownym zdaniem ze źródła (`impacts_accepted` = 54).
   - Odrzucono 10 propozycji nieposiadających zweryfikowanego zdania uzasadniającego (`impact_rejected_unsupported` = 10, występujące w Biegach C, D, E, H, J).
3. **Przyczyna braku propozycji (`impacts_not_proposed_reason`):**
   - We wszystkich 10 biegach `impacts_proposed > 0`, wobec czego pole `impacts_not_proposed_reason` pozostało puste (`—`).

---

## 3. Rozbicie czasów wykonania i efekty optymalizacji współbieżnej

Dzięki zrównolegleniu Etapu 1 (dekompozycja) i Etapu 2 (wyszukiwanie sieciowe) za pomocą `asyncio.gather`, całkowity czas odpowiedzi uległ skróceniu o ok. 13–16 sekund w stosunku do wykonania sekwencyjnego.

### Tabela rozbicia czasów (Timing Breakdown)

| Bieg | Wyszukiwanie (s) | Pobieranie (s) | Ekstrakcja (s) | Dekompozycja (s) | Agregacja (s) | Całkowity wall time (s) |
|------|------------------|----------------|----------------|------------------|---------------|--------------------------|
| Bieg A | 13,28 | 0,36 | 35,44 | 14,16 | 0,0100 | 50,09 |
| Bieg B | 13,00 | 0,29 | 17,15 | 15,91 | 0,0114 | 33,47 |
| Bieg C | 15,13 | 1,43 | 12,26 | 17,50 | 0,0098 | 31,31 |
| Bieg D | 14,91 | 0,33 | 16,82 | 18,54 | 0,0099 | 35,83 |
| Bieg E | 16,74 | 0,34 | 11,96 | 13,94 | 0,0130 | 29,22 |
| Bieg F | 20,30 | 0,30 | 14,13 | 11,85 | 0,0093 | 34,74 |
| Bieg G | 16,26 | 0,32 | 14,98 | 12,37 | 0,0074 | 31,74 |
| Bieg H | 15,53 | 0,52 | 20,03 | 13,08 | 0,0097 | 36,27 |
| Bieg I | 15,91 | 0,59 | 61,91 | 16,07 | 0,0102 | 78,71 |
| Bieg J | 14,99 | 0,62 | 14,07 | 14,88 | 0,0095 | 29,88 |

### Statystyki czasowe
- **Mediana całkowitego czasu odpowiedzi:** **34,11 s**
- **Najlepszy czas (best-case):** **29,22 s** (Bieg E)
- **Najgorszy czas (worst-case):** **78,71 s** (Bieg I – w którym zewnętrzny model Gemini przy ekstrakcji 7 dokumentów odpowiedział z opóźnieniem 61,91 s)
- **Średni narzut wyszukiwania:** ~15,6 s (wykonywany w tle równolegle z dekompozycją trwającą ~14,8 s)

---

## 4. Weryfikacja mechaniczna i zgodność repozytorium

Przed i po wdrożeniu wykonano pełen zestaw testów i automatycznych bramek jakościowych:
1. `scripts/check_v4.sh`: **25/25 bramek PASS** (w tym G-DOCS, G-EVID, G-TESTS, G-R1..G-R6, G-N1..G-N11).
2. `tests/test_scenario_web_sourcing.py`: **29/29 testów PASS** (w tym nowy test `test_v19_separate_impact_dictionaries_and_per_impact_source`).
3. Zestaw testów pytest repozytorium: **257/257 testów PASS**.
4. Kompilacja frontendu (`npm run build`): **0 błędów**.
5. Funkcja `_verify_quote_in_text`: **100% nienaruszona** (zero modyfikacji).
6. Zero sekretów w repozytorium.
