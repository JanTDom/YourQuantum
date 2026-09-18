# YourQuantum — RAPORT Z WDROŻENIA PROMPTU V18
**Data:** 2026-09-18  
**Autor:** Antigravity (Senior Autonomous Frontier Engineer)  
**Zleceniodawca:** Jan Domaniewski  
**Status bramek mechanicznych (`scripts/check_v4.sh`):** 25/25 ZIELONE (PASS)  

---

## 1. Cel zlecenia V18 i diagnoza stanu wyjściowego

W audycie Promptu V17 i badaniach stabilności stwierdzono, że we wszystkich dotychczasowych biegach silnika:
```text
impacts_proposed = 0
impacts_accepted = 0
impact_rejected_unsupported = 0
```
Mimo obecności zweryfikowanych cytatów ze źródeł sieciowych (`web_quotes_verified > 0`) mechanizm uziemiania liczb wpływu nie generował propozycji powiązanych z dokumentami. Asymetria rozkładu prawdopodobieństw (np. 55,9% / 26,5% / 17,6% lub 60,9% / 28,6% / 10,4%) nie wynikała z zebranych faktów, lecz wyłącznie z nieugruntowanych w cytatach liczb proponowanych przez drugie wywołanie LLM (dekompozytora scenariuszy).

### Przyczyna źródłowa (Root Cause)
1. **Zła kolejność etapów w silniku**: Silnik najpierw pobierał strony i uruchamiał ekstraktor dowodów (`EvidenceExtractor`), a dopiero potem tworzył scenariusze. W efekcie `extractor.extract_parameter_evidences` nie otrzymywał listy scenariuszy (`candidate_scenarios=None`) i nie mógł powiązać zdań ze scenariuszami ani zaproponować liczb wpływu.
2. **Kształtowanie rozkładu przez niezweryfikowane liczby**: Gdy drugie wywołanie modelu (dekompozytor) wygenerowało liczby wpływu bez uziemienia w zdaniu dokumentu, po wdrożeniu DEC-039 liczby te trafiały bezpośrednio do obliczeń softmax, powodując asymetrię na domysłach modelu.

---

## 2. Wdrożone rozwiązania architektoniczne i domenowe

### A. Odwrócenie kolejności etapów (Prompt V18-1)
W module `backend/domain/cognitive/active_inference_engine.py` zmieniono sekwencję potoku wnioskowania:
1. **Etap 1 (Dekompozycja wstępna)**: Z samego zapytania generowane są scenariusze kandydujące (`candidate_scenarios`) oraz wstępne przesłanki analityczne (`candidate_premises`).
2. **Etap 2 (Wyszukiwanie sieciowe)**: Pobranie adresów URL z wyszukiwarki.
3. **Etap 3 (Współbieżne pobieranie i ekstrakcja ze scenariuszami)**: Do `extractor.extract_parameter_evidences` przekazywana jest lista `candidate_scenarios`. Ekstraktor wymaga od modelu podania `sentence_index` uzasadniającego wpływ na poszczególne scenariusze i weryfikuje cytat funkcją `_verify_quote_in_text`. Wpływy ze zweryfikowanym cytatem uzyskują status `impact_source = "documented"`.
4. **Etap 4 (Integracja)**: W przypadku braku zweryfikowanych dowodów sieciowych, wynik wstępny jest natychmiast reużywany bez zbędnych wywołań LLM. W przypadku obecności dowodów sieciowych następuje ich deterministyczna integracja.

### B. Reguła DEC-040: Zakaz kształtowania rozkładu przez `model_unverified` (Prompt V18-2)
W `backend/domain/scenario_weighting.py` oraz `docs/memory/DECISIONS.md` wdrożono regułę **DEC-040**:
- Dodano pole `impact_source: Literal["documented", "model_unverified", "user_defined"]` do modelu `EvidencePremise`.
- Wpływy bez zweryfikowanego zdania z dokumentu otrzymują `impact_source = "model_unverified"`.
- W funkcji `compute_scenario_distribution` wpływy z `impact_source == "model_unverified"` są traktowane jako `0.0` i NIE MAJĄ PRAWA trafić do sumy ocen scenariuszy, dopóki decydent nie zatwierdzi ich ręcznie w UI (`impact_source = "user_defined"`).
- Wpływy ugruntowane w zweryfikowanym cytacie (`impact_source = "documented"`) wchodzą do rozkładu automatycznie.
- **Płaski rozkład jako wymagany stan zerowy**: Gdy brak udokumentowanych wpływów, rozkład prawdopodobieństw pozostaje ściśle płaski ($1/k$, np. 33,3% / 33,3% / 33,3%).
- **Wskaźnik `impact_documented_share`**: Wprowadzono do telemetrii wskaźnik udziału ugruntowanego wpływu:
  $$\text{impact\_documented\_share} = \frac{\sum_{\text{doc}} |I(s, p)|}{\sum_{\text{total}} |I(s, p)|} \times 100\%$$

### C. Zgodność interfejsu i zdanie pod liczbą (Prompt V18-3)
W `frontend/src/components/RecommendationView.tsx`:
- Dosłowne zdanie uzasadniające wyświetlane jest pod liczbą wpływu wyłącznie dla `impact_source === 'documented'`.
- Dla `impact_source === 'model_unverified'` interfejs wyświetla jawne oznaczenie:
  *„ocena modelu, bez pokrycia w dokumencie”* oraz przycisk „Zatwierdź wpływ”.
- W hooku `liveForecast = useMemo(...)` wpływy `model_unverified` są wykluczone z obliczeń wag softmax do momentu zatwierdzenia przez decydenta.

### D. Rozbicie czasów wykonania (Prompt V18-4)
W telemetrii prognozy zarejestrowano precyzyjne czasy poszczególnych etapów:
- `time_search_seconds`
- `time_fetch_seconds`
- `time_extraction_seconds`
- `time_decomposition_seconds`
- `time_aggregation_seconds`
- `intake_wall_time_seconds`

---

## 3. Rzeczywiste wyniki pomiarów stabilności (10 biegów)

Pomiary wykonano skryptem `scripts/measure_forecast_stability.py` na zapytaniu:  
*„Czy Rosja do końca tego roku napadnie na Polskę?”*  
przy aktywnym połączeniu z Gemini 2.5 Flash i rzeczywistym przeszukiwaniu sieci.

### Tabela wyników pomiaru stabilności (10 biegów)
| Bieg | Zweryfikowane cytaty | Aktywne przesłanki | impacts_proposed | impacts_accepted | impact_rejected_unsupported | impact_documented_share | Czas całkowity | Rozkład |
|---|---|---|---|---|---|---|---|---|
| Bieg A | 7 | 7 | 12 | 10 | 2 | 100,0% | 101,26 s | 53,8% / 40,7% / 5,4% |
| Bieg B | 3 | 3 | 0 | 0 | 0 | 0,0% | 93,78 s | 33,3% / 33,3% / 33,3% |
| Bieg C | 6 | 6 | 9 | 9 | 0 | 100,0% | 56,33 s | 85,5% / 7,3% / 7,2% |
| Bieg D | 7 | 7 | 10 | 10 | 0 | 100,0% | 95,66 s | 80,7% / 9,9% / 9,4% |
| Bieg E | 9 | 9 | 9 | 8 | 1 | 100,0% | 65,65 s | 56,7% / 41,6% / 1,7% |
| Bieg F | 8 | 8 | 15 | 15 | 0 | 100,0% | 73,49 s | 57,3% / 31,3% / 11,4% |
| Bieg G | 7 | 7 | 7 | 6 | 1 | 100,0% | 47,92 s | 82,3% / 8,8% / 8,8% |
| Bieg H | 7 | 7 | 13 | 13 | 0 | 100,0% | 40,34 s | 61,0% / 30,3% / 8,8% |
| Bieg I | 0 | 0 | 0 | 0 | 0 | 0,0% | 31,93 s | 33,3% / 33,3% / 33,3% |
| Bieg J | 5 | 5 | 3 | 3 | 0 | 100,0% | 99,19 s | 60,4% / 19,8% / 19,8% |

### Rozbicie czasu wykonania (Timing Breakdown)
| Bieg | Wyszukiwanie (s) | Pobieranie (s) | Ekstrakcja (s) | Dekompozycja (s) | Agregacja (s) | Całkowity wall time (s) |
|---|---|---|---|---|---|---|
| Bieg A | 19.84 | 3.63 | 61.20 | 16.54 | 0.0158 | 101.26 |
| Bieg B | 15.45 | 2.09 | 62.32 | 13.90 | 0.0099 | 93.78 |
| Bieg C | 15.87 | 2.04 | 19.47 | 18.93 | 0.0108 | 56.33 |
| Bieg D | 15.73 | 2.44 | 62.64 | 14.83 | 0.0206 | 95.66 |
| Bieg E | 15.97 | 1.67 | 13.42 | 34.58 | 0.0181 | 65.65 |
| Bieg F | 14.75 | 1.18 | 39.67 | 17.87 | 0.0169 | 73.49 |
| Bieg G | 9.52 | 3.98 | 15.79 | 18.62 | 0.0158 | 47.92 |
| Bieg H | 12.34 | 1.74 | 14.03 | 12.22 | 0.0162 | 40.34 |
| Bieg I | 14.43 | 0.00 | 0.00 | 17.50 | 0.0000 | 31.93 |
| Bieg J | 10.93 | 9.50 | 62.22 | 16.52 | 0.0130 | 99.19 |

### Statystyki czasowe (10 biegów)
- **Mediana czasu całkowitego:** 69,57 s
- **Najgorszy przypadek (worst-case):** 101,26 s
- **Najlepszy przypadek (best-case):** 31,93 s
- **Mediana czasu ekstrakcji dowodów:** 39,67 s
- **Mediana czasu dekompozycji scenariuszy:** 17,02 s
- **Mediana czasu wyszukiwania:** 15,10 s
- **Mediana czasu pobierania stron:** 2,07 s
- **Czas agregacji matematycznej:** < 0,025 s (pomijalny ułamek sekundy)

---

## 4. Wnioski z pomiarów

1. **`impacts_proposed` jest teraz trwale większe od zera**:
   W 8 na 10 biegów ekstraktor zaproponował od 3 do 15 udokumentowanych wpływów na scenariusze ze zweryfikowanymi cytatami.
2. **Bezwzględna czystość rozkładu**:
   - W każdym biegu, w którym wystąpiły udokumentowane wpływy (A, C, D, E, F, G, H, J), `impact_documented_share` wynosi **100,0%**. Ani jeden nieugruntowany wpływ nie wpłynął na rozkład.
   - W biegach, w których ekstraktor nie znalazł zdań uzasadniających wpływ (Bieg B) lub wyszukiwarka nie zwróciła stron (Bieg I), rozkład pozostał **ściśle jednostajny 33,3% / 33,3% / 33,3%**, zgodnie z nakazem DEC-040.
3. **Analiza czasu odpowiedzi**:
   - Wąskim gardłem pozostaje czas ekstrakcji dowodów przez LLM (mediana 39,67 s), który w 4 biegach osiągnął ~62 s z powodu złożoności analizy 3 pełnych dokumentów z cytowaniem zdań.
   - Dzięki ustawieniu `maxDuration: 300` w `vercel.json` (V14-5) wszystkie 10 biegów zakończyło się sukcesem (zero timeoutów).

---

## 5. Status bramek mechanicznych (`scripts/check_v4.sh`)

```text
=== YOURQUANTUM V4 MECHANICAL GATES CHECK ===
Date: 2026-09-18T16:36:51Z
Commit: 13531ce
Branch: main
----------------------------------------------
[G-R1a] PASS: 0 trafień domen w frontend/src
[G-R1b] PASS: getDesignFixture nie występuje w RecommendationView.tsx
[G-R1c] PASS: healthcare_pl.json jest syntetyczny i zawiera wyłącznie adresy https://example.test
[G-R2] PASS: Brak hasła master poza dokumentami audytowymi
[G-R3] PASS: Zero wartości domyślnych dla YQ_SIGNING_KEY i YQ_MASTER_API_SECRET
[G-R4] PASS: Wszystkie ścieżki w dokumentacji istnieją na dysku
[G-R5] PASS: Brak domyślnych zmyślonych wartości w EvidenceDrawer.tsx
[G-R6] PASS: search_adapter.py nie traktuje tekstu modelu jako strony i nie używa google.com/search
[G-N1a] PASS: Wszystkie pliki kontenera i rozdzielonych zależności istnieją
[G-N1b] PASS: requirements-api.txt jest lekki (brak ciężkich pakietów solverów)
[G-N1c] PASS: CURRENT_STATE.md zawiera surową odpowiedź z polem available
[G-N2a] PASS: decision_case.py posiada bramkę blokującą przy 0 kryteriach
[G-N2b] PASS: CaseWorkspace.tsx zawiera edytor macierzy score_matrix
[G-N3] PASS: Frontend wywołuje researchEvidence
[G-N4] PASS: problem_class_override zaimplementowany w backendzie i frontendzie
[G-N5] PASS: lever_decomposer.py i DesignWorkspace.tsx istnieją
[G-N6] PASS: Zero wywołań httpx.post/Client w backend/domain
[G-N7] PASS: universal_engine.py nie omija approved=False i używa ProblemRouter
[G-N8] PASS: Zero niedozwolonego copy o halucynacjach
[G-N9] PASS: Problem IR schema version podniesione do 0.3
[G-N11] PASS: E2E z realnym backendem uvicorn i webServer w playwright.config.ts
[G-N10] PASS: REPORT_V4.md zawiera wszystkie wymagane ID
[G-DOCS] PASS: Wszystkie przywołania linii w dokumentacji trafiają w kod
[G-EVID] PASS: Raporty zweryfikowane pod kątem autentyczności dowodów
Sprawdzanie testów pytest i kompilacji frontendu...
[G-TESTS] PASS: pytest i npm run build kończą się kodem 0
----------------------------------------------
WYNIK KOŃCOWY: WSZYSTKIE BRAMKI ZIELONE (PASS)
```
