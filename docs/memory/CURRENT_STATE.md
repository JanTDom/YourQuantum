# YourQuantum — CURRENT STATE
_Last updated: 2026-09-19 (V21: DANE Z SIECI TAKŻE W KLASIE DESIGN — eliminacja zmyślonych liczb, podpięcie pod rurociąg SafeWebFetcher/EvidenceExtractor, synteza Pareto na udokumentowanym podzbiorze kryteriów, 10-biegowy pomiar produkcyjny: 10/10 sukcesów, 0 komórek assumed, mediana 109,16 s, 25/25 bramek PASS)_

## Status: V21 — DANE Z SIECI TAKŻE W KLASIE DESIGN (WDROŻONE I OPOMIAROWANE NA PRODUKCJI)

- **Gałąź i stan repo**: `main` (wypchnięte na `origin/main` i wdrożone na produkcję):
  * **Zlecenie V21 (Dane z sieci w klasie DESIGN, DEC-042)**:
    - **Eliminacja liczb zmyślonych przez model (DEC-042)**: Usunięto arbitralne domyślne oceny `7.0` i `3.0` oraz status `provenance="assumed"`. Komórki bez zweryfikowanych faktów w sieci pozostają puste (`value=None`, `provenance="unverified"`).
    - **Podpięcie klasy DESIGN pod rurociąg dowodowy**: W fazie intake dla klasy `DESIGN` uruchamiane jest wyszukiwanie w sieci, pobieranie stron przez `backend/infrastructure/web_research/fetcher.py` (`SafeWebFetcher` z ochroną SSRF) oraz ekstrakcja z dosłowną weryfikacją cytatów `backend/infrastructure/web_research/extractor.py` (`EvidenceExtractor._verify_quote_in_text`).
    - **Kalkulacja Pareto na udokumentowanym podzbiorze kryteriów**: Puste komórki nie są zastępowane zerami ani średnimi. Kryteria nieposiadające danych liczbowych w żadnej opcji są wykluczane z dominacji Pareto i raportowane w `design_criteria_excluded`. W przypadku braku jakichkolwiek danych zwracany jest uczciwy fallback `insufficient_data=True` z komunikatem *„Nie znalazłem wystarczających danych, żeby porównać te warianty.”*
    - **Modernizacja interfejsu**: W `frontend/src/components/DesignWorkspace.tsx` usunięto jednostkowe przyciski założeń, dodano zbiorczy przycisk `🌐 Dociągnij dane z sieci`, licznik ugruntowanych i pustych komórek oraz możliwość edycji manualnej przez decydenta (`user_supplied`).
    - **Pomiary produkcyjne (10 biegów na `https://yourquantum.pl` dla zapytania o ochronę zdrowia)**:
      * **Skuteczność**: **10 na 10 biegów (100%)** zakończonych sukcesem 200 OK w klasie `DESIGN`.
      * **Komórki `assumed`**: **0 we wszystkich 10 biegach (100% rygoru empirycznego)**.
      * **Ugruntowanie empiryczne**: W 7/10 biegów pozyskano od 2 do 5 udokumentowanych komórek z cytatami z polskich portali branżowych i ekonomicznych; w 3/10 biegów uczciwy stan 0 danych.
      * **Czas całkowity**: Mediana **109,16 s** (min 99,06 s, max 119,01 s, średnia 109,28 s).
    - **Oficjalny raport**: Utworzono `docs/REPORT_V21.md`.
- **Weryfikacja testowa**:
  * `scripts/check_v4.sh`: Wszystkie bramki PASS (**25/25 ZIELONE**).
  * `pytest`: Wszystkie 262 testy automatyczne PASS (w tym nowy zestaw `tests/unit/test_design_web_sourcing.py` 3/3 PASS).
  * `npm run build`: Kompilacja Vite/TypeScript czysta (kod 0, 0 błędów).
- **Wdrożenie produkcyjne**: `https://yourquantum.pl` (Vercel prod deployment, status `READY`).



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

### ✅ Faza V9: Trzy Zaległe Długi Techniczne (2026-09-16)
- **Etap A (Dowód optymalności)**: Utworzono narzędzie pomiarowe `scripts/bench_enumeration.py` mierzące czas wykonania niezależnej enumeracji `_independent_small_n_enumeration` dla $n \in \{16, 18, 20, 22, 24\}$ (5 przebiegów per rozmiar, 3 instancje). Wyniki (mediana 3.65s dla $n=16$, 15.91s dla $n=18$) jednoznacznie potwierdziły przekroczenie budżetu 2.0s już przy $n=18$. Próg pozostawiono na poziomie 16 zmiennych, ujednolicając trzy rozproszone literały do nazwanej stałej `MAX_ENUMERATION_VARS = 16` w `backend/verifier/verifier.py`.
- **Horyzont Czasowy**: Wdrożono deterministyczny moduł `backend/domain/cognitive/time_horizon.py` do dekodowania perspektyw czasowych w języku polskim (DEC-034).
- **Etap B (Bramka dostępu po stronie serwera)**: Usunięto tablicę `AUTHORIZED_HASHES` z frontendu. Wdrożono serwerowy endpoint `POST /api/v1/auth/verify-app-access` weryfikujący sekret `YQ_APP_ACCESS_SECRET` stałoczasowo (`hmac.compare_digest`), zabezpieczony ograniczeniem prób (5 nieudanych prób na 15 min per IP) oraz wydający wygasające tokeny sesyjne HMAC-SHA256 (DEC-036).
- **Etap C (Uziemienie przesłanek w sieci)**: Podłączono pobieranie stron `SafeWebFetcher.fetch()` oraz weryfikację cytatów `EvidenceExtractor.extract_parameter_evidence()` w ścieżce prognoz scenariuszowych `backend/domain/cognitive/active_inference_engine.py`. Przesłanki z potwierdzonym cytatem uzyskują oznaczenie `web_sourced`, a decydent zatwierdza je w `frontend/src/components/RecommendationView.tsx` z jawną adnotacją, że fakt i cytat pochodzą z sieci, a wagi i wpływy proponuje model (DEC-035).

---

### ✅ Faza V11: Dwa Zmyślone Miejsca i Wdrożenie Produkcji (2026-09-16)
- **Punkt 1 (Wpływy przesłanek sieciowych)**: Całkowicie wyeliminowano arbitralny fallback `0.5` / `-0.5` w `_integrate_verified_evidences` (`backend/domain/cognitive/scenario_decomposer.py`). W przypadku braku specyfikacji wag przez model stosowane jest neutralne `0.0`. Dodano oznacznik w polu `source_ref` (`f"{ev.source_url} [wpływy: nieokreślone]"`) oraz dwa warianty opisu (`"Wpływ na scenariusze nie został określony; przesłanka nie przeważa rozkładu, dopóki nie nadasz jej wag ręcznie."` vs `"Liczbowy wpływ na scenariusze jest propozycją analityczną modelu i wymaga zatwierdzenia przez decydenta."`). Licznik nieokreślonych przesłanek jest rejestrowany w `forecast.telemetry["unspecified_impacts_count"]`.
- **Punkt 2 (Eliminacja zmyślonych scenariuszy fallback)**: Usunięto sztuczne scenariusze `sc_1` / `sc_2` z fałszywymi poziomami ryzyka. Gdy model zwróci mniej niż 2 scenariusze, silnik zwraca czysty stan `too_vague` wymagający podania alternatyw przez decydenta.
- **Punkt 3 (Wdrożenie produkcyjne Vercel)**: Rozwiązano problem braku automatycznego deploymentu przy pushu do GitHuba. Wdrożono build na żywo przez Vercel CLI (`https://yourquantum.pl`). Zweryfikowano identyczność sumy kontrolnej SHA-256 bundla produkcyjnego `assets/index-CCa7IAFf.js` z lokalnym (`9ed9b1b933b3a0ddb040b32e5e8049fda00f8fa85f70d20d83975ffcff0686a3`). Na produkcji obecne są frazy Etapu C i V11 (`analityczną propozycją modelu`, `Fakt i cytat zweryfikowane:`, `Zweryfikowane źródło sieciowe`, `nie zatwierdzono jeszcze żadnej przesłanki`).
- **Punkt 4 (Realna telemetria)**: Zarejestrowano przebieg zapytania scenariuszowego z aktywnym providerem `gemini`. Potwierdzono poprawne rejestrowanie surowej telemetrii (`forecast.telemetry`) bez zakłamywania danych przy awariach sieciowych.
- **Punkt 5 (Dokumentacja i bramki)**: Skorygowano commit w `docs/REPORT_V9.md`, uzupełniono `DEC-035` w `docs/memory/DECISIONS.md`, rozszerzono maszynową weryfikację cytatów `scripts/check_doc_citations.py` o `docs/REPORT_V9.md`. Wszystkie 24 bramki `scripts/check_v4.sh` zielone.

### ✅ Faza V13: Ostatnia Prosta — Weryfikacja Cytatów i Domknięcie Łańcucha Dowodowego (2026-09-17)
- **Punkt 1 (Łańcuch dowodowy)**: Usunięto barierę pomijania fetchowania stron w `backend/domain/cognitive/active_inference_engine.py` przy `search_mode == "grounding_urls_only"`. Wprowadzono symetryczną normalizację typograficzną `normalize_typography()` w `backend/infrastructure/web_research/extractor.py` oraz rygorystyczny prompt systemowy dla ekstraktora LLM, eliminując odrzucanie cytatów przez formatowanie. Wprowadzono precyzyjne liczniki telemetrii (`web_docs_empty`, `web_extractor_no_evidence`, `web_quotes_unverified`). Zweryfikowano na żywej produkcji: 3 zwrócone URL, 3 pobrane strony, 1 zweryfikowany dosłowny cytat.
- **Punkt 2 (Wdrożenia Vercel)**: Ustalono przyczynę braku wdrożeń (`link: null`). Wdrożono na żywą produkcję bundle `assets/index-CwhrjICi.js` za pomocą Vercel CLI.
### ✅ Faza V14: Wycinanie Cytatów ze Zdań, Spójność Bramki i Eliminacja Halucynacji (2026-09-17)
- **Ekstrakcja przez wybór zdań (V14-1)**: Wprowadzono metodę `sentence_selection` w `backend/infrastructure/web_research/extractor.py`. LLM otrzymuje ponumerowane zdania ze strony i wybiera 1–3 indeksy; backend sam wycina cytat na podstawie offsetów `char_start` i `char_end` (do 300 znaków). Weryfikacja `_verify_quote_in_text` osiągnęła 100% PASS na rzeczywistych stronach w `scripts/diag_evidence_chain.py` (7/7 zweryfikowanych cytatów, 0 halucynacji).
- **Fałszywe needs_clarification (V14-2)**: Usunięto pole `clarification_prompt`, dodano `ConfigDict(extra="forbid")` do `FormalizationResult`, obsłużono neutralny fallback w `frontend/src/App.tsx`.
- **Jednolita definicja zapytania scenariuszowego (V14-3)**: Wprowadzono `is_scenario_forecast_query` jako jedyne źródło prawdy w `backend/domain/cognitive/quality_gate.py` i silniku.
- **Odporność dekompozycji scenariuszy (V14-4)**: Dodano jednokrotny retry przy < 2 scenariuszach oraz licznik `scenario_decomposition_retries`.
- **Czas odpowiedzi i konfiguracja serverless (V14-5)**: Skonfigurowano limit `maxDuration: 300` w `vercel.json`, zrównoleglono pobieranie stron przez `asyncio.gather`, dodano telemetrię `intake_wall_time_seconds`.
- **Dokumentacja i bramki (V14-6, V14-8)**: Zaktualizowano `docs/REPORT_V13.md`, `docs/memory/DECISIONS.md` (DEC-036, DEC-038), zarejestrowano i wygenerowano `docs/REPORT_V14.md` z surową telemetrią diagnostyczną. 24/24 bramki zielone.

---

### ✅ Faza V18: Liczby Muszą Pochodzić z Dokumentów (2026-09-18)
- **Odwrócenie kolejności (V18-1)**: `backend/domain/cognitive/active_inference_engine.py` tworzy `candidate_scenarios` przed pobieraniem stron i przekazuje je do `extractor.extract_parameter_evidences`. Zapewnia to generowanie `impacts_proposed > 0` i `impacts_accepted > 0` ze zweryfikowanymi cytatami.
- **Reguła DEC-040 (V18-2)**: Wpływy nieugruntowane w zdaniu dokumentu otrzymują `impact_source = "model_unverified"` i nie mają prawa wejść do agregacji softmax; rozkład przy ich obecności pozostaje ściśle płaski (1/k). Jedynie wpływy `documented` lub zatwierdzone przez decydenta `user_defined` kształtują rozkład. Wprowadzono wskaźnik telemetrii `impact_documented_share` (100,0% we wszystkich biegach z ugruntowanym wpływem).
- **Spójność interfejsu (V18-3)**: W `frontend/src/components/RecommendationView.tsx` dosłowne zdanie uzasadniające wyświetlane jest wyłącznie dla `impact_source === 'documented'`. Dla `impact_source === 'model_unverified'` interfejs wyświetla: *„ocena modelu, bez pokrycia w dokumencie”* oraz przycisk „Zatwierdź wpływ”.
- **Rozbicie czasów wykonania (V18-4)**: Do telemetrii dodano `time_search_seconds`, `time_fetch_seconds`, `time_extraction_seconds`, `time_decomposition_seconds`, `time_aggregation_seconds`.
- **Pomiary 10 biegów (`scripts/measure_forecast_stability.py`)**: Mediana 69,57 s, worst-case 101,26 s, best-case 31,93 s; mediana ekstrakcji 39,67 s, mediana dekompozycji 17,02 s. Zero timeoutów.
- **Raport**: Utworzono `docs/REPORT_V18.md`, zaktualizowano `docs/AUDYT_ZGODNOSCI.md`, wszystkie 25 bramek `scripts/check_v4.sh` zielone.

---

### ✅ Faza V19: Trzy Domknięcia (2026-09-18)
- **Rozdział słowników wpływów i per-scenariuszowy `impact_source` (V19-1, DEC-041)**:
  - `impact_on_scenarios: dict[str, float]` przechowuje wyłącznie wpływy ugruntowane w zweryfikowanych zdaniach cytowanych z dokumentów.
  - `impact_proposed: dict[str, float]` w `EvidencePremise` przechowuje propozycje analityczne modelu językowego. Propozycje te nigdy nie są scalane automatycznie i nigdy nie nadpisują zweryfikowanych wartości.
  - Słownik `impact_source` z klasą `ImpactSourceDict` mapuje `scenario_id -> 'documented' | 'model_unverified' | 'user_defined'` i zachowuje pełną kompatybilność wsteczną w porównaniach z łańcuchami znaków.
  - Softmax (`compute_scenario_distribution`) czyta wyłącznie ze słownika `impact_on_scenarios`. Niezaakceptowane propozycje nie wpływają na rozkład prawdopodobieństw.
  - W `frontend/src/components/RecommendationView.tsx` komponent `PremiseScenarioImpacts` rozdziela prezentację wpływów ugruntowanych od propozycji analitycznych modelu i umożliwia selektywne zatwierdzanie per scenariusz.
- **Telemetria `impacts_not_proposed_reason` (V19-2)**:
  - Zaimplementowano raportowanie ustandaryzowanych przyczyn braku propozycji wpływów (`brak candidate_scenarios`, `model zwrócił pustą tablicę impacts`, `odpowiedź modelu nie przeszła walidacji schematu`, `przekroczony budżet`).
- **Optymalizacja czasu odpowiedzi (V19-3)**:
  - Zrównoleglono dekompozycję zapytania na scenariusze (Etap 1) oraz wyszukiwanie sieciowe (Etap 2) za pomocą `asyncio.gather`.
  - Wdrożono dedykowane instancje `EvidenceExtractor` na każdy dokument w Etapie 3, eliminując współdzielony stan mutowalny.
- **Pomiar produkcyjny 10 biegów (`scripts/measure_forecast_stability.py --target https://yourquantum.pl --runs 10`)**:
  - **10 na 10 biegów (100,0%)** wykazało `impact_documented_share > 0`.
  - **Rozrzut `impact_documented_share`**: ściśle **100,0%** we wszystkich 10 biegach.
  - **Telemetria wpływów**: 64 zaproponowane, 54 zaakceptowane, 10 odrzuconych jako nieugruntowane przez bramkę G-EVID/DEC-040.
  - **Czasy odpowiedzi**: Mediana **34,11 s**, najlepszy czas **29,22 s**, najgorszy czas **78,71 s** (skrócenie mediany z ~69,5 s w V18 do 34,11 s).
- **Raport**: Utworzono `docs/REPORT_V19.md`, zarejestrowano decyzję DEC-041 w `docs/memory/DECISIONS.md`.

---

### ✅ Faza V21: Dane z Sieci Także w Klasie DESIGN (2026-09-19)
- **Eliminacja zmyślonych liczb modelu (DEC-042)**: Usunięto arbitralne domyślne oceny `7.0` i `3.0` oraz status `provenance="assumed"`. Komórki bez zweryfikowanych faktów w sieci pozostają puste (`value=None`, `provenance="unverified"`).
- **Podpięcie klasy DESIGN pod rurociąg dowodowy**: W fazie intake dla klasy `DESIGN` uruchamiane jest wyszukiwanie w sieci, pobieranie stron przez `backend/infrastructure/web_research/fetcher.py` (`SafeWebFetcher` z ochroną SSRF) oraz ekstrakcja z dosłowną weryfikacją cytatów `backend/infrastructure/web_research/extractor.py` (`EvidenceExtractor._verify_quote_in_text`).
- **Kalkulacja Pareto na udokumentowanym podzbiorze kryteriów**: Puste komórki nie są zastępowane zerami ani średnimi. Kryteria nieposiadające danych liczbowych w żadnej opcji są wykluczane z dominacji Pareto i raportowane w `design_criteria_excluded`. W przypadku braku jakichkolwiek danych zwracany jest uczciwy fallback `insufficient_data=True` z komunikatem *„Nie znalazłem wystarczających danych, żeby porównać te warianty.”*
- **Modernizacja interfejsu**: W `frontend/src/components/DesignWorkspace.tsx` usunięto jednostkowe przyciski założeń, dodano zbiorczy przycisk `🌐 Dociągnij dane z sieci`, licznik ugruntowanych i pustych komórek oraz możliwość edycji manualnej przez decydenta (`user_supplied`).
- **Pomiary produkcyjne (10 biegów na `https://yourquantum.pl` dla zapytania o ochronę zdrowia)**:
  * **Skuteczność**: **10 na 10 biegów (100%)** zakończonych sukcesem 200 OK w klasie `DESIGN`.
  * **Komórki `assumed`**: **0 we wszystkich 10 biegach (100% rygoru empirycznego)**.
  * **Ugruntowanie empiryczne**: W 7/10 biegów pozyskano od 2 do 5 udokumentowanych komórek z cytatami z polskich portali branżowych i ekonomicznych; w 3/10 biegów uczciwy stan 0 danych.
  * **Czas całkowity**: Mediana **109,16 s** (min 99,06 s, max 119,01 s, średnia 109,28 s).
- **Raport**: Utworzono `docs/REPORT_V21.md`, zarejestrowano decyzję DEC-042 w `docs/memory/DECISIONS.md`.

---

## Następny krok (Next Step)

Zlecenie V21 ukończone, przetestowane (25/25 bramek PASS w `scripts/check_v4.sh`), wdrożone produkcyjnie na `https://yourquantum.pl` i zweryfikowane pełnym 10-biegowym pomiarem produkcyjnym (10/10 sukcesów 200 OK, 0 komórek assumed, do 5 zweryfikowanych komórek z sieci www, mediana czasu 109,16 s). Oczekiwanie na dyspozycję Jana co do kolejnych kroków i dalszych ulepszeń platformy.
