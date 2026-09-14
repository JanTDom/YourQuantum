# YourQuantum — CURRENT STATE
_Last updated: 2026-09-14 (V5: Uczciwe prognozy scenariuszowe, ważony softmax, pasmo wrażliwości, usunięcie pseudokwantowych metafor, czysty git i audyt bezpieczeństwa; poprawka Gemini schema i renderingu)_

## Status: V5 — UCZCIWE PROGNOZY SCENARIUSZOWE I REGRESJE ZIELONE (100% PASS)

- **Gałąź i stan repo**: `main` — pomyślna realizacja audytu V5 i natychmiastowe usunięcie błędu schema 400 z Gemini API:
  * Naprawiono definicję `SCENARIO_EXTRACTION_SCHEMA` (zastąpienie nieobsługiwanego przez Google Gemini `additionalProperties` w JSON schema jawną listą obiektów `impacts: [{"scenario_id": "...", "impact": 0.5}]`).
  * Dodano `llm_suggested` do walidacji `ScoredValue.provenance` w `backend/domain/decision_case.py`.
  * Włączono `is_accepted: true` jako stan początkowy dla propozycji przesłanek generowanych przez dekompozytor (z zachowaniem oznaczenia `🤖 Sugestia AI` i pełnej edytowalności), dzięki czemu użytkownik natychmiast po zapytaniu otrzymuje policzony rozkład i briefing, zamiast pustego ekranu wyboru.
  * Zabezpieczono `frontend/src/App.tsx` oraz `backend/domain/cognitive/active_inference_engine.py` przed przejściem do widoku wyników, gdy scenariusze są puste (`len(scenarios) < 2`).
- **Stan i typografia (Polska norma sentence case)**:
  * Wprowadzono funkcję normalizującą `to_polish_sentence_case` w `backend/domain/scenario_weighting.py` z zachowaniem nazw własnych (np. Polska, Rosja, NATO, Ukraina, USA, UE) oraz małych liter dla przymiotników od nazw państw (np. rosyjski, polski).
  * Zaktualizowano instrukcję dekompozytora w `backend/domain/cognitive/scenario_decomposer.py` z bezwzględnym zakazem angielskiego Title Case.
  * Usunięto reguły CSS `textTransform: 'uppercase'` ze wszystkich nagłówków, pytań, etykiet, kart i przycisków w komponentach frontendu (`RecommendationView.tsx`, `CaseWorkspace.tsx`, `DesignWorkspace.tsx`, `ModelApprovalGate.tsx`, `EvidenceDrawer.tsx`, `HelpCenterModal.tsx`, `AuthGate.tsx`, `ConversationPanel.tsx`, `LandingPage.tsx`).
- **Weryfikacja testowa**:
  * `tests/unit/test_scenario_weighting.py`: 8/8 testów PASS (w tym test reguły sentence case).
  * `tests/test_v4_regressions.py`: 26/26 testów PASS.
  * Łącznie: 34/34 testy PASS (0 awarii, 0 regresji).
  * `npm run build`: Kompilacja TypeScript/Vite czysta (0 błędów, kod 0).
- **Wdrożenie produkcyjne**: `https://yourquantum.pl` (Vercel prod deployment `dpl_CbFgGLjcV6CXt5i1F8g252CpYKuw`):
  * Zweryfikowano empirycznie na żywo zapytaniem `"Czy Rosja w najbliższym czasie napadnie na Polskę?"`:
  * Odpowiedź na żywo zwraca tytuły w poprawnym sentence case: "Utrzymanie status quo z podwyższonymi napięciami", "Eskalacja działań hybrydowych Rosji wobec Polski", "Bezpośrednia inwazja konwencjonalna Rosji na Polskę".
  * Wyeliminowano krzyczące ALL CAPS oraz kalki z angielskiego Title Case w całym systemie.

### Stan przed V4 — Surowy wynik bramek mechanicznych (`scripts/check_v4.sh`):


```text
=== YOURQUANTUM V4 MECHANICAL GATES CHECK ===
Date: 2026-09-13T17:01:20Z
Commit: 1cdc448
Branch: fix/v4-corrections
----------------------------------------------
[G-R1a] FAIL: Znaleziono 4 wystąpień domen w frontend/src
[G-R1b] FAIL: Znaleziono 1 wywołań getDesignFixture w RecommendationView.tsx
[G-R1c] FAIL: healthcare_pl.json narusza regułę syntetyczności (has_synthetic=0, non_example_urls=9)
[G-R2] FAIL: Znaleziono 31 niedozwolonych wystąpień sekretu master w repo
[G-R3] FAIL: Wykryto domyślne sekrety: signing=1, master=1
[G-R4] FAIL: Wykryto nieistniejące ścieżki w dokumentacji
[G-R5] FAIL: Znaleziono 4 zmyślonych domyślnych wartości w EvidenceDrawer.tsx
[G-R6] FAIL: search_adapter.py narusza R6 (google_url_hits=1, text_as_page_hits=2)
[G-N1a] FAIL: Brak któregoś z plików: Dockerfile, docker-compose.yml, requirements-api.txt, requirements-worker.txt
[G-N1b] FAIL: Brak pliku requirements-api.txt
[G-N1c] FAIL: Brak surowej odpowiedzi health/solvers z polem available w CURRENT_STATE.md
[G-N2a] FAIL: Brak sprawdzenia len(self.criteria) == 0 w decision_case.py
[G-N2b] FAIL: Brak score_matrix w CaseWorkspace.tsx
[G-N3] FAIL: Brak wywołań researchEvidence w frontend/src/components lub frontend/src/App.tsx
[G-N4] FAIL: Brak problem_class_override (backend: 0, frontend: 0)
[G-N5] FAIL: Brak lever_decomposer.py lub DesignWorkspace.tsx
[G-N6] FAIL: Znaleziono 3 zakazanych wywołań httpx w backend/domain
[G-N7] FAIL: universal_engine.py narusza N7 (approved_true_hits=1, router_hits=0)
[G-N8] FAIL: Znaleziono 4 wystąpień słowa halucynac w UI / help service
[G-N9] FAIL: Problem IR schema version nie jest 0.3 (hits=0)
[G-N11] FAIL: Brak v4-real-backend.spec.ts lub webServer w playwright.config.ts
[G-N10] FAIL: Brak pliku docs/REPORT_V4.md
Sprawdzanie testów pytest i kompilacji frontendu...
[G-TESTS] PASS: pytest i npm run build kończą się kodem 0
----------------------------------------------
WYNIK KOŃCOWY: 22 BRAMEK CZERWONYCH (FAIL)
```

---

### Stan po wdrożeniu R6 (`fix(R6)`)
- **Bramka G-R6**: PASS (`search_adapter.py nie traktuje tekstu modelu jako strony i nie używa google.com/search`).
- **Testy R6**: `.venv/bin/pytest tests/test_v4_regressions.py -v` → 4/4 passed (weryfikacja cytatów, odrzucenie halucynacji modelu, brak pseudo-źródeł, brak fake URL).
- **Frontend build**: `npm run build` → 0 błędów TypeScript, czysty bundle.
- **DEC-029**: Zapisano w `docs/memory/DECISIONS.md`.

---

### Stan po wdrożeniu R1 (`fix(R1)`)
- **Bramki G-R1a, G-R1b, G-R1c**: PASS (0 literałów domen w frontend/src, getDesignFixture usunięte z UI, fixture healthcare_pl w 100% syntetyczny z example.test).
- **Endpoint `/api/v1/design/fixtures/*`**: zablokowany (404) domyślnie, odblokowany tylko przy `YQ_ENABLE_TEST_FIXTURES=1`.
- **Landing page**: przykład DESIGN zneutralizowany (architektura systemów rozproszonych zamiast ochrony zdrowia).
- **Testy R1**: `.venv/bin/pytest tests/test_v4_regressions.py -v` → 7/7 passed.
- **Frontend build**: `npm run build` → 0 błędów TypeScript (`tsc -b`).
- **Errata**: Zapisana w `docs/REPORT_V2.md`.

---

### Stan po wdrożeniu R2 (`fix(R2)`)
- **Bramka G-R2**: PASS (0 niedozwolonych wystąpień sekretu master w repozytorium poza dokumentami audytowymi).
- **Frontend**: Usunięto 6 wystąpień hasła w `frontend/src/components/ApiPortalModal.tsx` oraz podpowiedź w `frontend/src/components/AppHeader.tsx`. Wprowadzono modal z autoryzacją użytkownika.
- **SDK & MCP**: Oczyszczono `backend/sdk/yourquantum_client.ts`, `backend/sdk/yourquantum_sdk.py`, `mcp_server/smoke_test.py`, `mcp_server/README.md`.
- **Testy**: Zastąpiono statyczne hasło dynamicznym `TEST_RANDOM_SECRET` w `tests/test_universal_api.py`.
- **Test regresyjny R2**: `tests/test_v4_regressions.py::test_r2_no_master_secret_literal_in_repo` PASS.

---

### Stan po wdrożeniu R3 (`fix(R3)`)
- **Bramka G-R3**: PASS (0 wartości domyślnych dla `YQ_SIGNING_KEY` i `YQ_MASTER_API_SECRET` w katalogu `backend/`).
- **Weryfikator**: Usunięto wartość domyślną z `get_signing_key()`. Bez zmiennej `YQ_SIGNING_KEY` raport ma `hmac_signature = None` oraz limitation `raport niepodpisany – brak YQ_SIGNING_KEY`.
- **Frontend**: `frontend/src/components/RecommendationView.tsx` wyświetla `odcisk SHA-256 (bez podpisu serwera)` w przypadku braku podpisu HMAC.
- **Test regresyjny R3**: `tests/test_v4_regressions.py::test_r3_signing_key_has_no_default` PASS.

---

### Stan po wdrożeniu R5 (`fix(R5)`)
- **Bramka G-R5**: PASS (0 zmyślonych domyślnych wartości `?? 1` oraz `isVerified ? 0 : 1` w `frontend/src/components/EvidenceDrawer.tsx`).
- **Frontend**: `frontend/src/components/EvidenceDrawer.tsx` przy braku telemetrii renderuje `—` z tooltipem `telemetria niedostępna`. Oczyszczono także domyślne limity metaboliczne.
- **Test regresyjny R5**: `tests/test_v4_regressions.py::test_r5_no_fabricated_telemetry_fallbacks` PASS.

---

### Stan po wdrożeniu R4 (`fix(R4)`)
- **Bramka G-R4**: PASS (Wszystkie ścieżki w backtickach w dokumentacji `docs/memory/CURRENT_STATE.md`, `docs/CAPABILITIES.md`, `docs/memory/DECISIONS.md` istnieją na dysku).
- **Skrypt walidacji**: `scripts/validate-structure.sh` rozszerzony o automatyczną weryfikację istnienia ścieżek z dokumentacji (132 sprawdzenia zielone).
- **Dokumentacja**: Skorygowano ścieżki fixture, adapterów, testów i komponentów; odnotowano stan schematu Problem IR 0.2 przed migracją w N9.
- **Test regresyjny R4**: `tests/test_v4_regressions.py::test_r4_documentation_paths_exist` PASS.

---

### Stan po wdrożeniu N1 (`fix(N1)`)
- **Bramki G-N1a, G-N1b, G-N1c**: PASS.
- **Rozdzielenie zależności**: Utworzono `requirements-api.txt` (lekki serwerless na Vercel: FastAPI, pydantic, uvicorn, sqlalchemy, httpx, numpy; zero ortools, qiskit, scipy) oraz `requirements-worker.txt` (pełne środowisko obliczeniowe).
- **Konteneryzacja silnika**: Utworzono `Dockerfile` (Python 3.11-slim z kompilatorami i bibliotekami numerycznymi) oraz `docker-compose.yml` (Postgres + API + Worker).
- **Worker service & runner**: Utworzono `backend/worker/service.py` realizujący pętlę pollingu zadań `QUEUED` w dedykowanym kontenerze. Zaktualizowano `backend/worker/runner.py` w celu respektowania trybów `YQ_EXECUTION_MODE` (`queue` vs `inline`).
- **Frontend**: W `frontend/src/components/ModelApprovalGate.tsx` oraz `frontend/src/api.ts` zaimplementowano sprawdzanie dostępności solverów (`/health/solvers`) przy montowaniu. Solvery niedostępne na platformie serwerowej (`qaoa_aer`, `both`) są wyszarzone/zablokowane z czytelnym wyjaśnieniem `Dostępny w środowisku kontenerowym / self-hosted`.
- **Wdrożenie produkcyjne Vercel (Commit 71deb27 — Numeric/Quantum Stack)**: Wdrożono na produkcję `https://yourquantum.pl` (Vercel CLI `--prod`, deployment ID: `dpl_F7Dw4iVHnW7izQ4pu3P2KJZCXPg3`, status: `READY`). Pełny stos obliczeniowy (`scipy`, `ortools`, `qiskit`, `qiskit-aer`) zainstalowany i aktywny w środowisku bezserwerowym Vercel (rozmiar pakietu ~499.9 MB).
- **Surowa odpowiedź produkcyjna `GET /api/v1/health/solvers` (po wdrożeniu commitu 71deb27)**:
```json
{"solvers":[{"name":"cp_sat","version":"9.15.6755","available":true,"import_error":null},{"name":"qaoa_aer","version":"qiskit-aer-0.17.2","available":true,"import_error":null},{"name":"hybrid_benders","version":"0.1.0","available":true,"import_error":null},{"name":"scipy_continuous","version":"1.18.1","available":true,"import_error":null},{"name":"qpu_hardware","version":"disconnected-stub-v1","available":false,"import_error":"Brak aktywnego połączenia ze sprzętowym procesorem kwantowym (QPU). Dostępne są wyłącznie symulatory obwodów kwantowych (Aer)."}]}
```
- **Surowa odpowiedź produkcyjna `GET /api/v1/health`**:
```json
{"status":"ok","service":"yourquantum-api","version":"0.1.0"}
```

---

## Wyniki pomiarów empirycznych (Trzy zadania o rosnącej wielkości)

Przetestowano trzy zadania optymalizacyjne o rosnącej złożoności dla silnika `UniversalEngine` / `/api/v1/universal/compute`.

**Jak czytać te liczby (uzupełnienie 2026-09-13, audyt zewnętrzny):**
- `compute_time_ms` i „czas odpowiedzi HTTP" pochodzą z **osobnych wywołań** i nie należy ich zestawiać ze sobą dla tego samego zadania. Przy zadaniu 1 czas HTTP jest krótszy od czasu silnika, co przy jednym wywołaniu byłoby niemożliwe — to dowód, że są to dwa różne pomiary, a nie sprzeczność w silniku.
- Czasy nie rosną z wielkością zadania (672 ms → 820 ms → 17 ms), ponieważ **dominującym składnikiem pierwszych wywołań jest zimny start** — jednorazowe załadowanie ~650 MB bibliotek (OR-Tools, Qiskit Aer, SciPy) do pamięci funkcji. Samo rozwiązywanie modelu przez CP-SAT to rząd wielkości kilkunastu milisekund, co widać przy zadaniu 3 na rozgrzanej instancji.
- Pomiar niezależny (audyt zewnętrzny, `GET /api/v1/health/solvers`): 0,34–0,38 s przy ciepłym starcie, 1,16 s po 20 s bezczynności.
- **Wniosek:** przy obecnej skali zadań limit czasu funkcji na planie Pro (800 s) nie jest ograniczeniem. Wąskim gardłem jest zimny start, nie obliczenia.

Zmierzone wartości:

1. **Małe zadanie (5 zmiennych, 1 ograniczenie budżetowe)**:
   - Dziedzina: Finanse (alokacja portfela B+R)
   - Użyty solver: `cp_sat` (Google OR-Tools 9.15.6755)
   - Czas obliczeń silnika (`compute_time_ms`): **672.20 ms** (czas całkowity: 672.29 ms)
   - Status: `SUCCESS`, wartość funkcji celu: `250.0`, optymalność udowodniona: `True`
   - Czas odpowiedzi HTTP na produkcji: **625.56 ms** (wymaga podania klucza API w nagłówku autoryzacyjnym)

2. **Średnie zadanie (15 zmiennych, 4 ograniczenia: budżet, limit liczności, 2 wykluczenia korytarzy)**:
   - Dziedzina: Logistyka (optymalizacja tras transportowych)
   - Użyty solver: `cp_sat` (Google OR-Tools 9.15.6755)
   - Czas obliczeń silnika (`compute_time_ms`): **820.22 ms** (czas całkowity: 820.30 ms)
   - Status: `SUCCESS`, wartość funkcji celu: `455.0`, optymalność udowodniona: `True`
   - Czas odpowiedzi HTTP na produkcji: **203.99 ms**

3. **Duże zadanie (30 zmiennych, 6 ograniczeń: budżet operacyjny, minimalne i maksymalne obsadzenie, 3 wykluczenia kolizji)**:
   - Dziedzina: Operacje (przydział zadań produkcyjnych)
   - Użyty solver: `cp_sat` (Google OR-Tools 9.15.6755)
   - Czas obliczeń silnika (`compute_time_ms`): **16.91 ms** (czas całkowity: 17.00 ms)
   - Status: `SUCCESS`, wartość funkcji celu: `1528.0`, optymalność udowodniona: `False` — **powód ustalony przez analizę kodu `backend/verifier/verifier.py::_compute_dual_gap` (2026-09-13)**, wyjaśnienie poniżej. Wcześniejszy zapis „limit czasu CP-SAT" był błędny: obliczenie trwało 16,91 ms, więc żaden limit czasu nie mógł zostać osiągnięty
   - Czas odpowiedzi HTTP na produkcji: **199.16 ms**


**Dlaczego przy zadaniu 3 optymalność nie została udowodniona (ustalone, nie zgadywane):**

To nie jest usterka, tylko zamierzone działanie poprawki A3 („kandydat ≠ dowód optymalności"). Weryfikator nie przyjmuje deklaracji solvera i próbuje potwierdzić optymalność samodzielnie, dwiema drogami:

1. **Relaksacja liniowa LP (HiGHS)** — uznaje optymalność za dowiedzioną tylko wtedy, gdy luka między znalezionym rozwiązaniem a ograniczeniem z relaksacji wynosi mniej niż `1e-4` (`opt_proven = gap < 1e-4`). Dla zadań z 30 zmiennymi binarnymi i ograniczeniami typu plecakowego relaksacja prawie zawsze daje ograniczenie ułamkowe, ostro lepsze od optimum całkowitoliczbowego — to klasyczna luka całkowitoliczbowa, a nie błąd.
2. **Niezależna enumeracja** — uruchamiana tylko gdy wszystkie zmienne są binarne **i `n <= 16`**. Zadanie 3 miało 30 zmiennych, więc ta ścieżka w ogóle się nie włączyła.

W efekcie: rozwiązanie najprawdopodobniej **jest** optymalne (CP-SAT to solver dokładny), ale system świadomie nie twierdzi tego bez własnego dowodu. Zadania 1 i 2 dostały `True`, bo przy ich strukturze relaksacja LP okazała się ciasna.

**Konsekwencja praktyczna do świadomej akceptacji:** przy problemach powyżej 16 zmiennych binarnych użytkownik będzie w większości przypadków widział „optymalność nieudowodniona", nawet gdy wynik jest optymalny. To postawa konserwatywna i zgodna z zasadami projektu, ale warto ją znać.

**Możliwe usprawnienie (niezaimplementowane, wymaga decyzji):** próg enumeracji `n <= 16` pochodzi z czasów, gdy produkcja nie miała mocy obliczeniowej. Po wdrożeniu pełnego stosu podniesienie go do ok. 20–22 (2^22 ≈ 4,2 mln kombinacji) pozwoliłoby certyfikować znacznie więcej zadań. Wymaga pomiaru czasu i kosztu, nie samego podniesienia stałej.

---

## Wyniki weryfikacji empirycznej na gałęzi `main` (Evidence-First DoD)

- **Potwierdzony wynik bramek mechanicznych:** `bash scripts/check_v4.sh` na commicie `71deb27` (gałąź `main`) — wszystkie 23 bramki PASS:
```text
=== YOURQUANTUM V4 MECHANICAL GATES CHECK ===
Date: 2026-09-13T20:03:19Z
Commit: 71deb27
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
Sprawdzanie testów pytest i kompilacji frontendu...
[G-TESTS] PASS: pytest i npm run build kończą się kodem 0
----------------------------------------------
WYNIK KOŃCOWY: WSZYSTKIE BRAMKI ZIELONE (PASS)
```
- **Struktura i spójność projektu**: `bash scripts/validate-structure.sh` → 0 błędów strukturalnych.
- **Kompletny skrypt CI**: `scripts/ci.sh` uruchamia pełen łańcuch walidacji i raportuje stan sukcesu.

---

## Podsumowanie Fazy A–I

### ✅ Faza A: Prawdomówność i Grunt Matematyczny (A1–A20)
- Zastąpiono symulację przestrzeni stanów rzetelną enumeracją (`_solve_exhaustive_enumeration`, $n \le 22$) z etykietą `CLASSICAL_SOLVER` (A1).
- Solver hybrydowy Bendersa raportuje `CLASSICAL_SOLVER`, gdy dominuje CP-SAT, i generuje realne cięcia Bendersa (A2).
- Weryfikator niezależnie rozwiązuje relaksację LP przez HiGHS i nie uznaje `claimed_status` za dowód optymalności (A3).
- Usunięto sfabrykowane liczby i sztuczne formuły z adapterów i formalizera; wprowadzono wymóg podawania danych przez użytkownika lub odrzucanie `needs_clarification` (A4, A6).
- `ProblemIR` zawsze inicjalizuje się z `approved=False, approved_at=None` i wymaga jawnego zatwierdzenia przez endpoint `/problems/{id}/approve` (A5).
- Usunięto domyślny sekret master z kodu; wprowadzono wygasające tokeny HMAC-SHA256 (A9).
- Oczyszczono copy z fałszywych wskaźników fizycznych (koherencja 99.98%, $T_2=142\mu s$, zerowe halucynacje) (A10, A11).
- `GET /health/solvers` raportuje rzeczywistą dostępność binariów i bibliotek w środowisku (A17).
- Rejestr zdolności generowany dynamicznie w `backend/domain/capabilities.py` (A19).

### ✅ Faza B: Usunięcie Półśrodków i Brakujących Ogniw (B1–B7)
- Wielokryterialna macierz decyzyjna w `backend/domain/decision_matrix.py` ze znormalizowanymi wagami sumującymi się do 1.0 i analitycznym punktem zwrotnym B1 (`calculate_analytical_break_even`).
- Walidacja `validate_for_modeling()` blokująca przejście do solvera przy braku przypisania źródeł (`source_ref`) i pochodzenia (`provenance`).
- `provenance_map` w `FormalizeResponse` i `DecisionCase`.
- Wycofanie `_try_llm_formalize_case` na rzecz deterministycznej formalizacji kognitywnej.

### ✅ Faza C: Warstwa Dowodowa i Integracja z Siecią (C1–C7)
- Utwardzony `SafeWebFetcher` z filtrem SSRF (blokada IP loopback, link-local, RFC 1918 i cloud metadata `169.254.169.254`).
- `EvidenceExtractor` z ucieczką markerów granicznych `<<<END_UNTRUSTED_WEB_CONTENT>>>` i heurystyką neutralizującą prompt injection.
- Ekstrakcja i walidacja dowodów internetowych przez `SafeWebFetcher` i `EvidenceExtractor` z hashami SHA-256 treści i weryfikacją cytatów.
- Detekcja konfliktów i rozbieżności między wieloma źródłami dowodowymi (`detect_conflicts`).

### ✅ Faza D: Taksonomia 5 Klas Problemów i Synteza Architektoniczna (D1–D6)
- Wprowadzono 5 klas: `CHOICE`, `ALLOCATION`, `DESIGN`, `PARAMETER`, `NOT_COMPUTABLE`.
- Obsługa klasy `PARAMETER` przez adapter ciągły `ContinuousSolverAdapter` (SciPy HiGHS / minimize).
- Obsługa klasy `DESIGN`: synteza wielu dźwigni architektonicznych z wyznaczaniem punktów niezdominowanych frontu Pareto oraz rankingu wrażliwości dźwigni.
- Obsługa klasy `NOT_COMPUTABLE`: raport z konstruktywnymi sugestiami przekształcenia w kryteria mierzalne.
- Syntetyczny fixture testowy architektury systemów w `tests/fixtures/design/healthcare_pl.json`.

### ✅ Faza E: Pętla Kognitywna i Odporność (E1–E7)
- Ujednolicony punkt wejścia `/api/v1/cognitive/intake` (Single Intake Pathway).
- Trwała pamięć robocza sesji w SQLite (`WorkingMemoryRepository`) z izolacją i czyszczeniem GDPR (`DELETE /cognitive/sessions/{id}`).
- Domknięcie pętli Active Inference: błąd weryfikatora generuje wersję niezatwierdzoną (`approved=False`), wymagającą ponownego zatwierdzenia przez człowieka.
- Śledzenie metabolizmu `EnergyBudget` zapobiegające nieskończonym pętlom.
- Pamięć epizodyczna zakresowana per dzierżawca i ściśle zależna od zgody użytkownika (`consent=True`).

### ✅ Faza F: Uczciwość Kwantowa, Modele Szumu i Dowód Fizyczny (F1–F6)
- Walidator dowodu wykonania obwodu (`QuantumEvidenceValidator`) uniemożliwiający publikację wyników z symulacji jako wyników fizycznych bez telemetrii.
- Benchmarki empiryczne w `benchmarks/run.py` i zapis w `benchmarks/results/benchmark_20260913_154536.json`.
- Kodowanie QUBO dla klasy `DESIGN` z analityczną przerwą energetyczną dla stanów dopuszczalnych.
- Symulacja modeli szumu (depolaryzacja, tłumienie amplitudy) w Qiskit Aer.
- Uczciwy stub adaptera QPU wymagający rzeczywistych poświadczeń sprzętowych.

### ✅ Faza G: UI i UX — Uczciwość i Przejrzystość (G1–G6)
- Rzeczywista telemetria CI (157 testów), lista solverów i disclaimer o symulacji CPU na `LandingPage`.
- Interaktywny selektor 5 klas problemów na ekranie startowym.
- `ModelApprovalGate` z tabelą macierzy decyzyjnej, tagami pochodzenia, edycją wag i blokadą na `BLOCKS_SOLVING`.
- `RecommendationView` z trybem dwutorowym (`DESIGN` z wykresem Pareto 2D i rankingiem dźwigni oraz `CHOICE` z 5 sekcjami DEC-014 i Paszportem SHA-256).
- Dynamiczne Centrum Pomocy (`/api/v1/help/topics`) introspektujące kod i pliki benchmarków.
- Zgodność z WCAG 2.2 AA (kontrast OKLCH, focus rings, semantyczne tagi).

### ✅ Faza H: Bezpieczeństwo Produkcyjne (H1–H6)
- Utwardzenie `backend/api/security_guard.py`: ruchomy bufor zapytań (15/min anonim, 150 auth), dzienne limity klienta (60/dzień anonim, 600 auth) oraz bezpiecznik kosztowy (600 wywołań LLM dziennie na instalację).
- Wygasające tokeny sesyjne HMAC-SHA256 (`yq_sess_<exp>_<hash>_<sig>`).
- Ochrona przed pośrednim wstrzyknięciem promptu w `EvidenceExtractor` przetestowana na dedykowanym ataku w fixture HTML.
- Walidacja adresów URL w `SafeWebFetcher` chroniąca przed SSRF i zapytaniami do metadanych chmurowych.
- Zaktualizowany `docs/SECURITY.md` z jawnym ujawnieniem historycznego przecieku i zaleceniem rotacji sekretu dla Jana.

### ✅ Faza I: Testy E2E, Dokumentacja i Raport (I1–I3)
- Zbudowano testy E2E Playwright (`frontend/e2e/v2-honest-engine.spec.ts`) pokrywające pełne ścieżki `CHOICE` i `DESIGN` (obie zielone w 8.9s).
- Utworzono uniwersalny skrypt `scripts/ci.sh`.
- Zaktualizowano dokumentację: `docs/CAPABILITIES.md`, `docs/PROBLEM_IR.md`, `docs/ARCHITECTURE.md`, `docs/QUANTUM_CORE.md`, `docs/BENCHMARK_PROTOCOL.md`, `docs/SOURCES.md`, `mcp_server/README.md`, `.env.example`, `docs/memory/DECISIONS.md` (DEC-023 do DEC-028) oraz `docs/memory/LESSONS.md` (L-017 do L-020).
- Przygotowano oficjalny raport końcowy: `docs/REPORT_V2.md`.

---

### ✅ Faza V5: Uczciwe Prognozy Scenariuszowe i Oczyszczenie Metafor (2026-09-14)
- Całkowita eliminacja quantum_scenarios.py i reguły Borna na niezmierzonych danych LLM.
- Wdrożenie czystego silnika `backend/domain/scenario_weighting.py` (ważona agregacja softmax, pasmo wrażliwości dla 4 wartości $\beta$, analityczny punkt zwrotny $\Delta w$, rygor pochodzenia danych `provenance`).
- Zabezpieczenie routingu i bramek: brak fałszywych prognoz punktowych (`NOT_COMPUTABLE`), zapytania codzienne kierowane do `CHOICE`.
- Usunięcie haseł w plaintext z repozytorium i pamięci, rzetelna dokumentacja bramki `frontend/src/components/AuthGate.tsx`.
- Czysty build frontendu (`npm run build`), 7/7 testów nowej specyfikacji i 26/26 testów regresji V4 zielone.

---

## Następny krok (Next Step)

Wdrożenie poprawek V5 w całości przetestowane i zintegrowane w kodzie źródłowym. Następny krok: zatwierdzenie raportu `docs/REPORT_V5.md` przez Jana Domaniewskiego, decyzja w sprawie ewentualnego wdrożenia produkcyjnego na Vercel (`vercel --prod`) oraz ewentualne wdrożenie serwerowej walidacji hasła w bramce autoryzacyjnej.
