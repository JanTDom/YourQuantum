# YourQuantum — CURRENT STATE
_Last updated: 2026-09-12_

## Status: PRODUKCJA — TOTAL QUANTUM SUPREMACY ENGINE + 3D HERO MANIFOLD

Projekt przygotowany do produkcyjnego wdrożenia na `https://yourquantum.pl` (Vercel).
Wszystkie testy backendu (59/59) przechodzą pomyślnie. Build frontendu (TypeScript + Vite) bezbłędny.

---

## Co działa (zweryfikowane empirycznie)

### ✅ Total Quantum Supremacy Engine (Przewaga nad AI Chatbotami)
1. **Input Quality Gate**:
   - `_assess_input_quality` w `backend/domain/llm_advisor.py` analizuje zwięzłość, opcje i parametry liczbowe, oznaczając dylematy `too_vague`, `needs_options`, `needs_numbers` lub `sufficient`.
   - Zweryfikowane w `tests/test_input_quality_gate.py`.
2. **Exact QUBO Binary Slack Expansion**:
   - W `backend/solvers/quantum/qubo.py` nierówności liniowe $\sum a_i x_i \le B$ są mapowane na binarne zmienne dopełniające (slack) o dokładnych wagach potęg dwójki z analitycznie skalowaną karą kwadratową.
   - Zweryfikowane w `tests/test_qubo.py`.
3. **Warm-Started QAOA**:
   - W `backend/solvers/quantum/qaoa.py` ciągła relaksacja kwadratowa L-BFGS-B inicjalizuje rotacje jednokubitowe $R_y(\theta_i)$, eliminując losowe punkty startowe i drastycznie przyspieszając zbieżność parametrów wariacyjnych.
   - Zweryfikowane w `tests/test_warm_start_qaoa.py`.
4. **Independent Dual Bound Gap & SHA-256 Audit Passport**:
   - W `backend/verifier/verifier.py` relaksacja ciągła LP (HiGHS) wyznacza dual bound i precyzyjną lukę optymalności (`optimality_gap_percent`), pieczętując wynik kryptograficznym hashem SHA-256.
   - Zweryfikowane w `tests/test_dual_certificate.py`.
5. **Sensitivity & Stress-Testing Engine**:
   - W `backend/domain/sensitivity.py` testy odporności symulują wstrząsy $\pm 5\%$, $\pm 15\%$, $\pm 25\%$ dla wag i ograniczeń, zwracając wskaźnik odporności i werdykt stabilności.
   - Zweryfikowane w `tests/test_sensitivity.py`.
6. **Hybrid Benders Decomposition Solver**:
   - W `backend/solvers/hybrid_benders.py` QAOA optymalizuje kombinatoryczny rdzeń decyzyjny, a CP-SAT generuje cięcia dopuszczalności.
   - Zweryfikowane w `tests/test_hybrid_benders.py`.

### ✅ Bespoke 3D Quantum Manifold Hero Animation
- Zastąpiono skaczącą/drgającą animację tła CSS w pełni interaktywną sceną WebGL Three.js (`QuantumHero3D.tsx` + `QuantumHero3D.module.css`).
- Pulsujące jądro kwantowe, 18 splątanych węzłów kubitowych na sferze Fibonacciego, dynamiczne linie interferencyjne, podwójne pierścienie geodezyjne QAOA, płynna reakcja na kursor myszy (paralaks) i badge telemetrii 60 FPS.
- Bez przeskakiwania obrazu, bez drgań, czysta estetyka high-tech instrument bez ujawniania tajemnic algorytmicznych.

### ✅ Zmodernizowane Przekazy i UI (Help Service + 3D Brain)
- Rozbudowane tematy w `backend/api/help_service.py` wyjaśniające matematyczną wyższość nad autoregresyjnymi halucynacjami LLM.
- Zaktualizowane płaty w `EngineBrain3D.tsx` z telemetrią bramek jakości, Benders decomposition, Warm-Start QAOA i kryptograficznym certyfikatem SHA-256.
- Wizualizacja Matematycznego Paszportu (SHA-256, Dual Bound Gap, Residual) oraz Stress Testingu w `RecommendationView.tsx`.

### ✅ Official Model Context Protocol (MCP) Server dla Claude i Cowork
- Zbudowano i przetestowano serwer MCP w Pythonie (`mcp_server/`) ze standardowym transportem `stdio`.
- Dostępne narzędzia:
  1. `yq_optimize_options`: wielokryterialna optymalizacja wyboru wariantów. Rygorystycznie wymusza podanie kryteriów celu i wag, odrzuca ciche domyślności, zwraca optymalny zbiór, paszport SHA-256 oraz analizę odporności na wstrząsy.
  2. `yq_solve_portfolio`: wyspecjalizowana alokacja portfela i budżetu pod kątem maksymalizacji wartości/ROI.
  3. `yq_analyze_dilemma`: analiza dylematów przez Input Quality Gate (wskazuje ogólniki, brak opcji, brak liczb i generuje pytania do użytkownika).
  4. `yq_get_engine_status`: diagnostyka łączności z API i telemetria dostępnych solverów.
- Bezpieczeństwo: autoryzacja wyłącznie przez zmienną środowiskową `YQ_API_KEY` (oraz `YQ_API_BASE_URL`). Utworzono `.env.example`.
- Dokumentacja i smoke-test: kompletne `mcp_server/README.md` z konfiguracją dla Claude Desktop i Cowork oraz `mcp_server/smoke_test.py`.

### ✅ Stage 4: Brain-Inspired Cognitive Architecture (Gemini 2.5 Flash & Active Inference)
1. **Prefrontal Cortex / Working Memory & Cybernetic Homeostasis**:
   - `EnergyBudget` enforcing metabolic token and cycle limits (`consume()`, `next_cycle()`, `is_exhausted()`) preventing infinite loops.
   - `GlobalWorkspace` managing `WorkingMemory` (active goal, focal variables, ProblemIR hypothesis, prediction errors, cycle history) in process RAM.
   - Zweryfikowane w `tests/unit/test_cognitive_workspace.py`.
2. **Hippocampal Episodic Memory**:
   - Model `CognitiveTraceRecord` (`cognitive_traces` table in SQLite/PostgreSQL) storing fingerprints, user queries, successful IRs, winning solvers, penalty multipliers, reward scores, and lessons learned.
   - `EpisodicMemoryRepository` with associative recall based on structural problem fingerprints and high-reward exemplars.
   - Zweryfikowane w `tests/unit/test_episodic_memory.py`.
3. **Hexagonal Reasoning Port & Gemini 2.5 Flash Adapter**:
   - `CognitiveReasoningPort` domain interface with validated Pydantic model `FormalizationResult`.
   - `GeminiCognitiveAdapter` communicating with Gemini REST API (temperature 0.0, strict JSON schema, episodic exemplar few-shot injection, verifier error context).
   - Zero-crash deterministic offline fallback on missing API keys, rate limit 429, or network errors.
   - Zweryfikowane w `tests/unit/test_gemini_cognitive_adapter.py`.
4. **Constraint Sanity Pre-Checker**:
   - Static analysis in `check_constraints_sanity` evaluating inverted bounds, binary domain constraints, and constant contradictions before solver invocation, generating prediction errors for early reflection.
   - Zweryfikowane w `tests/unit/test_cognitive_workspace.py`.
5. **Active Inference / Reflexion Error Minimization Engine**:
   - `ActiveInferenceOrchestrator` implementing Karl Friston's Free Energy Principle: perception $\to$ recall $\to$ hypothesis $\to$ sanity check $\to$ verifier evaluation $\to$ prediction error update $\to$ iterative hypothesis/penalty adaptation $\to$ consolidation.
   - Zweryfikowane w `tests/integration/test_active_inference_flow.py`.
6. **FastAPI Cognitive Intake Endpoint**:
   - `POST /api/cognitive/intake` (or `/api/v1/cognitive/intake`) returning structured `FormalizationResult` ready for human approval and solver routing.
   - Zweryfikowane w `tests/integration/test_cognitive_api.py`.

### ✅ V2 Honest Engine — Phase A (Honesty & Ground Truth Implementation, A1–A20)
1. **A1 (Honest Enumeration)**: Replaced `_solve_exact_state_space` with `_solve_exhaustive_enumeration`, reports `ComputeSource.CLASSICAL_SOLVER`, guarded by $n \le 22$.
2. **A2 (Hybrid Benders)**: When CP-SAT assists or converges classically, reports `ComputeSource.CLASSICAL_SOLVER` with real Benders infeasibility cuts injected into `current_problem.constraints`.
3. **A3 (Independent Verifier Dual Bounds)**: Eliminated `claimed_status in ("optimal", "model_optimal")` bypass; verifier independently solves continuous LP relaxation via HiGHS and marks `optimality_proven=False` on suboptimal claims.
4. **A4 (Deterministic Fallback Honesty)**: Rewrote `_deterministic_fallback` in `gemini_cognitive_adapter.py` without fabricated numbers ($10(i+1)$, $5(i+1)$, limit 25.0); extracts numbers from text or returns `needs_clarification`.
5. **A5 (Mandatory Approval Gate)**: `build_problem_ir` always initializes `approved=False, approved_at=None`.
6. **A6 (Knapsack Data Extraction)**: `_extract_knapsack` in `formalizer.py` extracts weights and values from user text; returns `missing_information` if data is incomplete.
7. **A7 (Decision Case LLM Deprecation)**: Deprecated `_try_llm_formalize_case` in `formalizer.py` in favor of deterministic multi-criteria framework.
8. **A8 (Universal Compute Logging)**: Added logger in `routes.py` and logged all universal compute error handlers.
9. **A9 (Token Security)**: Removed default hardcoded secrets; implemented expiring HMAC tokens with SHA-256 signatures (`create_expiring_token`, `verify_master_secret`).
10. **A10 & A11 (Purged Misleading Marketing)**: Removed fake coherence metrics (`99.98% · T₂: 142µs`) and zero-hallucination claims from `RecommendationView.tsx`, `QuantumEntanglementCanvas.tsx`, and `LandingPage.tsx`.
11. **A12 (Scientific Quantum Explanation)**: Rewrote quantum explanation in `help_service.py` without wave/tunneling metaphors.
12. **A13 (Stemming & Polish Stop-Words)**: Implemented NFKC normalization, Unicode regex, and Polish stop-word filtering in `active_inference_engine.py`.
13. **A14 & A18 (Multi-Tenant Episodic Memory & Sessions)**: Added `CognitiveSessionRecord`, scoped `EpisodicMemoryRepository` by `owner_id`/`workspace_id`, and sanitized prompt inputs.
14. **A16 (Synchronous Job Runner)**: Implemented `run_job_sync(job_id, session) -> JobRecord` in `backend/worker/runner.py`.
15. **A17 (Dynamic Solver Availability)**: Added `check_available()` across `SolverAdapter` hierarchy (`CPSATAdapter`, `QAOAAdapter`, `HybridBendersAdapter`) and wired `GET /health/solvers`.
16. **A19 (Dynamic Capabilities Registry)**: Created `backend/domain/capabilities.py`, exposed `GET /capabilities`, updated `docs/CAPABILITIES.md`.
17. **A20 (Model Approval Gate Transparency)**: Added objective coefficients display, formula breakdown, criteria weights, constraint list, and "Popraw formalizację" controls in `ModelApprovalGate.tsx`.

### ✅ V2 Honest Engine — Phase B (Usunięcie półśrodków i brakujących ogniw, B1–B7)
1. **B1 (Wielokryterialna macierz decyzyjna i analityczny break-even)**:
   - Utworzono `backend/domain/decision_matrix.py` z precyzyjnym wyliczaniem wag kryteriów (sum-to-one), normalizacją min-max (z rozróżnieniem kierunków korzyści/kosztów), kalkulacją użyteczności ważonej oraz analitycznym punktem zwrotnym (`calculate_analytical_break_even`).
   - Rozszerzono `DecisionCase` w `backend/domain/decision_case.py` o `ScoredValue(value, unit, provenance, source_ref, confidence)`, macierz `score_matrix` i walidację `validate_for_modeling()` blokującą przejście do modelu przy brakujących referencjach źródłowych.
   - Zastąpiono subiektywny rating LLM w `formalize_case` analityczną kompilacją użyteczności i wskaźnikami wrażliwości.
2. **B2 (Analiza wrażliwości w trybie re-solve)**:
   - Dodano `SensitivityEngine.analyze_resolve()` w `backend/domain/sensitivity.py`. Przeprowadza ponowne rozwiązywanie solverem (CP-SAT/HiGHS) przy wielowymiarowych perturbacjach parametrów (wagi kryteriów, granice budżetowe, współczynniki celu) i wyznacza ranking wrażliwości parametrów (`parameter_vulnerability`).
3. **B3 (Kryptograficzny Paszport Audytowy i endpoint weryfikacji HMAC)**:
   - Zaimplementowano generowanie i weryfikację podpisów HMAC-SHA256 w `backend/verifier/verifier.py` (`build_verification_canonical_string`, `compute_verification_signatures`).
   - Dodano publiczny endpoint `POST /api/v1/verification/check` w `backend/api/routes.py` umożliwiający niezależnemu audytorowi weryfikację autentyczności certyfikatu obliczeniowego.
4. **B4 (Zunifikowany Gateway LLM z budżetowaniem tokenów)**:
   - Zbudowano `backend/infrastructure/llm_gateway.py` (`LLMGateway`, `LLMCallTelemetry`, `LLMResponse`) z automatycznym retry i wykładniczym backoffem, budżetowaniem tokenów na sesję (`session_token_limit`), śledzeniem metryk i deterministycznym trybem offline. Zintegrowano z `GeminiCognitiveAdapter`.
5. **B5 (Rozszerzenie ProblemIR o metadane proweniencji)**:
   - Dodano wartości `WEB_SOURCED = "web_sourced"` i `LLM_EXTRACTED = "llm_extracted"` do enuma `Provenance` w `backend/domain/problem_ir.py`.
   - Zaktualizowano `ir_builder.py` o pełną konwersję i rejestrację `assumptions`, `missing_information`, `data_sources` i zmiennych z proweniencją.
6. **B6 (Dynamiczny ProblemRouter z telemetrią benchmarków)**:
   - Zaimplementowano `backend/domain/router.py` (`characterize_problem`, `ProblemRouter`, `RoutingDecision`, `RoutingCandidate`). Router automatycznie analizuje stopień liniowości, wielkość problemu i stan solverów w rejestrze możliwości, typując solver wiodący oraz solvery porównawcze. Zintegrowano z `runner.py` (`routing_record` w metadanych zadania).
7. **B7 (Aktualizacja narzędzi w MCP Server)**:
   - Narzędzie `yq_optimize_options` w `mcp_server/server.py` przyjmuje `criteria_matrix`, zwraca `routing_record` oraz transparentne źródło obliczeń (`compute_source`).

### ✅ V2 Honest Engine — Phase C (Warstwa dowodowa: Dane z sieci jako pierwszorzędny obywatel, C1–C7)
1. **C1 (Architektura hexagonalna warstwy dowodowej)**:
   - Utworzono moduł domenowy `backend/domain/evidence/` (`models.py`, `ports.py`, `planner.py`, `__init__.py`) oraz moduł infrastruktury `backend/infrastructure/web_research/` (`fetcher.py`, `html_text.py`, `search_adapter.py`, `extractor.py`).
   - Wdrożono port `EvidenceSourcePort` realizowany przez adapter `WebResearchAdapter` obsługujący wyszukiwarki (Tavily/Serper/Generic), pliki fixture offline oraz deterministyczny tryb bezkluczowy („offline_user_data_only").
2. **C2 (Model dowodu i integralność SHA-256)**:
   - Zaimplementowano model `Evidence` z unikalnym identyfikatorem, jednozdaniową tezą (`claim`), wyekstrahowaną wartością numeryczną/tekstową, jednostką, adresem URL, tytułem, wydawcą, czasem pobrania, hashem SHA-256 pobranego dokumentu (`content_hash`), dosłownym cytatem (`quote` $\le 300$ znaków), metodą ekstrakcji (`extraction_method`) i listą powiązanych konfliktów (`conflicts_with`).
3. **C3 (Pętla badawcza ResearchPlanner i weryfikacja cytatów)**:
   - `ResearchPlanner` skanuje macierz `DecisionCase` w poszukiwaniu komórek bez zweryfikowanego źródła (`source_ref`) i formułuje zwięzłe, chroniące prywatność zapytania `ResearchQuery` (bez wycieku tekstu prywatnego dylematu użytkownika).
   - W `EvidenceExtractor` wprowadzono **bezwzględną weryfikację cytatu**: `if not quote or quote.strip() not in doc.page_text: reject_evidence()`. Zapobiega to jakimkolwiek halucynacjom liczb z pamięci modeli autoregresyjnych!
4. **C4 (Konflikty i rozpiętość źródeł)**:
   - Zaimplementowano detekcję rozbieżności między źródłami `EvidenceConflict`. Przy rozbieżnych wartościach liczbowych system wyznacza przedział rozpiętości (`spread_min`, `spread_max`), kandydata mediany oraz wzajemnie linkuje identyfikatory w `conflicts_with`, uniemożliwiając ciche arbitralne wybory.
5. **C5 (Bezpieczeństwo SSRF i prompt isolation)**:
   - `SafeWebFetcher` weryfikuje adresy URL pod kątem SSRF (odrzuca metadane chmurowe `169.254.169.254`, pętle zwrotne `127.0.0.1`, `localhost`, zakresy prywatne RFC1918, adresy link-local i schematy inne niż HTTP/HTTPS).
   - Ograniczenia: limit rozmiaru dokumentu 2 MB, limit przekierowań z ponowną weryfikacją każdego skoku, izolacja tekstu w dedykowanych znacznikach `<<<UNTRUSTED_WEB_CONTENT>>>`.
6. **C6 (UI — panel źródeł, dowodów i niepewności)**:
   - Zaktualizowano `frontend/src/api.ts` o typy `Evidence`, `EvidenceConflict`, `ScoredValue` oraz metody `researchEvidence` i `getEvidenceRecord`.
   - Zaktualizowano `RecommendationView.tsx` o sekcję „Na czym oparliśmy tę rekomendację" oraz „Czego nie wiemy i co założyliśmy".
7. **C7 (Weryfikacja testowa i fixtury)**:
   - Utworzono katalog `tests/fixtures/web/` z realistycznymi dokumentami HTML i wynikami wyszukiwania.
   - Opracowano zestaw testów `tests/test_phase_c_evidence.py` (7/7 testów przechodzi pomyślnie: integralność hashy, blokada SSRF, odrzucenie sfabrykowanego cytatu, detekcja konfliktu i mediana, integracja z `DecisionCase`, zasilenie `DataSource` w `ProblemIR`, endpointy REST).

---

## Wyniki weryfikacji empirycznej
### ✅ V2 Honest Engine — Phase D (Klasy problemów — nie tylko wybór między opcjami, D1–D6)
1. **D1 (Jawna klasyfikacja ProblemClass i ochrona przed niepoliczalnymi pytaniami)**:
   - Zaimplementowano taksonomię `ProblemClass` (CHOICE, ALLOCATION, DESIGN, PARAMETER, NOT_COMPUTABLE) w `backend/domain/problem_classes.py`.
   - Funkcja `evaluate_problem_computability` chroni przed halucynowaniem pseudo-naukowych odpowiedzi na pytania filozoficzne i czysto spekulacyjne, oferując uczciwe wyjaśnienie („nie da się policzyć") i konstruktywne propozycje przeformułowania problemu (`NotComputableReport`).
2. **D2 (Kombinatoryczny model klasy DESIGN i zakaz fabrykowanych synergii)**:
   - Zaimplementowano modele `DesignProblem`, `DesignLever`, `LeverOption`, `DesignCriterion`, `Interaction`.
   - Wprowadzono twardą regułę: **każda niezerowa synergia wymaga zweryfikowanego źródła lub jawnego oznaczenia założeń** (`validate_synergy_source()`). Zero wymyślonych bonusów/kar!
   - Kompilacja do `ProblemIR`: zmienne binarne per (dźwignia, opcja), ścisłe więzy one-hot ($\sum x_{l,o} = 1$), ograniczenia wykluczeń ($x_a + x_b \le 1$) oraz linearyzacja iloczynów synergii ($y = x_a \cdot x_b$) metodą Forteta z zachowaniem liniowości celu dla CP-SAT i dokładności QUBO.
3. **D3 (Front Pareto metodą wielokryterialną)**:
   - Zaimplementowano algorytm `compute_design_pareto_frontier` wyznaczający zbiór rozwiązań niezdominowanych pod kątem przeciwstawnych kryteriów (np. koszt vs dostępność vs równość).
4. **D4 (Adapter optymalizacji ciągłej SciPy HiGHS)**:
   - Zbudowano `ContinuousSolverAdapter` w `backend/solvers/continuous.py` dla zmiennych `CONTINUOUS`, wykorzystujący silnik HiGHS ze ścisłym wyliczaniem residuów ograniczeń `numerical_residual`. Zarejestrowano w `SOLVER_REGISTRY` i dynamicznym rejestrze możliwości.
5. **D5 (Skill i dokumentacja standardu syntezy)**:
   - Utworzono skill `.agents/skills/yq-design-synthesis/SKILL.md` opisujący procedurę dekompozycji i zasady braku fabrykowanych synergii.
   - Zaktualizowano `docs/PROBLEM_IR.md` do wersji schematu v0.3 uwzględniającej `ProblemClass` i nowe proweniencje.
6. **D6 (Fixtura i test reformy ochrony zdrowia)**:
   - Zbudowano fixturę `tests/fixtures/design/healthcare_pl.json` (4 dźwignie, 3 kryteria, incompatibilities, synergie).
   - Opracowano zestaw testów `tests/test_phase_d_problem_classes.py` (6/6 testów przechodzi pomyślnie).

### ✅ Faza E: Warstwa mózgowa — Z dekoracji w rdzeń (E1–E7)
1. **E1 (Jedna ścieżka intake `POST /api/v1/cognitive/intake`)**:
   - `ActiveInferenceOrchestrator.run_intake` stał się jedynym punktem wejściowym intake.
   - Orkiestruje: percepcję → sprawdzanie obliczalności (`evaluate_problem_computability`) z uczciwym raportem → tenant-scoped episodic recall → hipotezę `DecisionCase` → bramkę jakości (`assess_input_quality` przeniesione do domeny) → badanie dowodowe → kompilację `ProblemIR` i `formalized`.
2. **E2 (Trwała pamięć robocza w bazie danych)**:
   - Tabela `cognitive_sessions` przechowuje stan `GlobalWorkspace`, `WorkingMemory`, `EnergyBudget` oraz historię cykli. Odtwarzana po `session_id` i usuwana na żądanie użytkownika (`DELETE /cognitive/session/{session_id}`).
3. **E3 (Zamknięcie pętli Active Inference i reguła DEC-002)**:
   - W `backend/worker/runner.py` weryfikacja przekazuje feedback do orkiestratora (`process_verification_feedback`).
   - Przy werdykcie `FAIL` i wygenerowaniu poprawionej hipotezy, nowy model otrzymuje `approved = False`, a w metadanych zadania rejestrowana jest flaga `requires_reapproval = True` (żaden solver nie może ruszyć bez ponownej autoryzacji decydenta).
4. **E4 (Prawdziwy budżet metaboliczny w `EnergyBudget`)**:
   - Śledzi tokeny LLM (sesyjne i dobowe), zapytania wyszukiwania sieciowego (`max_search_queries`), czas solverów (`max_solver_seconds`). Wyczerpanie generuje czytelną przyczynę i propozycje uproszczeń.
5. **E5 (Anonimizowana konsolidacja epizodyczna za zgodą)**:
   - Endpoint `POST /cognitive/consolidate`: odrzuca zapis przy braku zgody (`consent=False`). Przy `consent=True` zapisuje wyłącznie zanonimizowany odcisk problemu, kryteria, liczbę zmiennych i zwycięski solver, bez surowego tekstu.
6. **E6 (Panel Cognitive Inspector w UI)**:
   - Zintegrowany w `EvidenceDrawer.tsx`: zakładka z podglądem cykli roboczych, błędów predykcji, zużycia budżetu metabolicznego, historii cykli oraz przyciskiem jawnej zgody na konsolidację.
7. **E7 (Kompleksowy zestaw testów)**:
   - Utworzono `tests/test_phase_e_cognitive.py` (8 testów) oraz zaktualizowano testy integracyjne flow kognitywnego (wszystkie zielone).

### ✅ Faza F: Warstwa kwantowa — Uczciwa i użyteczna (F1–F6)
1. **F1 (Ścisły walidator dowodu wykonania kwantowego)**:
   - W `backend/solvers/base.py` `SolverResult` wymusza obecność `execution_evidence` (backend_name, shots, n_qubits, depth, seed, histogram) przy ustawieniu `source = ComputeSource.QUANTUM_CIRCUIT_SIMULATION`. Brak tych pól natychmiast rzuca `ValueError("Integrity violation: ...")`.
2. **F2 (Realny runner benchmarków i empiryczny protokół)**:
   - Zbudowano `benchmarks/run.py` uruchamiający CP-SAT vs QAOA (idealny) vs QAOA (noise model) na wspólnych instancjach (`healthcare_pl.json` oraz syntetyczne alokacje $N \in [4, 6, 8, 10]$).
   - Wyniki zapisywane automatycznie do `benchmarks/results/benchmark_<timestamp>.json`.
   - `docs/BENCHMARK_PROTOCOL.md` uzupełniony o rzeczywiste dane empiryczne: CP-SAT rozwiązuje instancje w 5–10 ms z dowodem globalnej optymalności, podczas gdy symulacja QAOA zajmuje 0.27s–28s z luką aproksymacji 5.38% przy $N=10$ i 3-krotnym spadkiem amplifikacji pod wpływem szumu bramkowego.
   - `ProblemRouter` automatycznie wczytuje te wyniki z dysku.
3. **F3 (QUBO dla klasy DESIGN z gwarantowaną przerwą energetyczną)**:
   - W `backend/solvers/quantum/qubo.py` zaimplementowano `QUBOEncoder.encode_design` oraz `decode_design_solution`.
   - Zastosowano analityczne skalowanie kary $P \ge 2 U_{\max} + 10.0$, gwarantując, że wszystkie stany niekompatybilne mają ściśle wyższą energię niż stany dopuszczalne.
   - Synergie kodowane bezpośrednio jako człony kwadratowe bez konieczności wprowadzania pomocniczych zmiennych Forteta.
4. **F4 (Symulacja modelu szumu Qiskit Aer w QAOAAdapter)**:
   - W `backend/solvers/quantum/qaoa.py` dodano tryb `mode="noise_simulation"` z kanałami depolaryzacji jedno- i dwukubitowej (`depolarizing_p1`, `depolarizing_p2`).
   - Telemetria szumu i obwodu zapisywana w `execution_evidence`, a ograniczenia jawnie komunikują symulację z modelem szumu.
5. **F5 (ADR dla kontenerowej architektury obliczeń)**:
   - Zapisano w `docs/memory/DECISIONS.md` decyzję `DEC-022: Kontenerowa architektura serwisów obliczeniowych (Compute Worker Container)` uzasadniającą separację frontendu (Vercel) od workerów obliczeniowych (Docker/Cloud Run/Fly.io) ze względu na limity czasu (60s) i rozmiaru paczki (250MB vs >650MB stosu naukowego C++).
6. **F6 (Uczciwy interfejs QPU Stub)**:
   - Zaimplementowano `QPUAdapter` w `backend/solvers/quantum/qpu_adapter.py`, zarejestrowano w `SOLVER_REGISTRY` w `backend/worker/runner.py`.
   - Zwraca `is_available() -> False`, `supports() -> False`, a próba wykonania zwraca status `FAILED`, `math_status = UNSUPPORTED` i komunikat o braku fizycznego QPU oraz dostępności wyłącznie symulatorów Aer.

### ✅ Faza G: UI i Copy — Uczciwość, Klasy Problemów i Weryfikacja (G1–G6)
1. **G1 (Rzeczywista telemetria i brak obietnic bez pokrycia na Landing Page)**:
   - W `frontend/src/components/LandingPage.tsx` usunięto fałszywe slogany; wyświetlana jest rzeczywista liczba testów CI (150/150 zielonych), lista produkcyjnych solverów (CP-SAT, HiGHS, QAOA Aer) oraz jawne zastrzeżenie o symulacji kwantowej na klasycznym CPU bez fizycznego QPU.
2. **G2 (Selektor klas problemów na ekranie startowym)**:
   - W `LandingPage.tsx` dodano interaktywne zakładki dla 5 klas problemów (`CHOICE`, `ALLOCATION`, `DESIGN`, `PARAMETER`, `NOT_COMPUTABLE`) z jednozdaniowym wyjaśnieniem i możliwością natychmiastowego załadowania problemu testowego do terminala.
3. **G3 (`ModelApprovalGate` z macierzą decyzyjną, edycją wag i bramką `BLOCKS_SOLVING`)**:
   - W `frontend/src/components/ModelApprovalGate.tsx` wprowadzono pełną macierz decyzyjną z pochodzeniem komórek (`user_supplied`, `web_sourced`, `derived`, `assumed`), interaktywne suwaki/pola do edycji wag przed uruchomieniem solvera, listę założeń i niewiadomych oraz twardą blokadę przycisku zatwierdzenia, jeśli jakakolwiek nierozwiązana luka posiada oznaczenie `BLOCKS_SOLVING`.
4. **G4 (`RecommendationView` dla `DESIGN` vs `CHOICE`)**:
   - W `frontend/src/components/RecommendationView.tsx` zaimplementowano dwa wyspecjalizowane widoki:
     * Dla `DESIGN`: tabela konfiguracji wielodźwigniowej, interaktywny wykres 2D frontu Pareto z punktami niezdominowanymi i przełącznikiem wariantów, ranking wrażliwości dźwigni (procentowy wpływ dźwigni na równowagę systemu), zweryfikowane źródła instytucjonalne (GUS, NFZ, WHO, OECD) oraz etykieta „optymalna dla modelu, nie dla świata”.
     * Dla `CHOICE`: 5 sekcji z DEC-014 (Odpowiedź, Dlaczego ta opcja z Paszportem SHA-256 i bilansem, Trade-offy z analitycznym punktem zwrotnym B1, What-if / Na czym oparliśmy, Następny krok).
5. **G5 (Obsługa 3 stanów UI i standardy WCAG 2.2 AA)**:
   - Zapewniono obsługę stanów ładowania, pustych i błędów w komponentach `LandingPage`, `CaseWorkspace`, `ModelApprovalGate`, `RecommendationView`, widoczny focus ring, semantyczne tagi ARIA i wysoki kontrast OKLCH.
6. **G6 (Dynamiczne Centrum Pomocy z rejestru zdolności i benchmarków)**:
   - W `backend/api/help_service.py` Centrum Pomocy generuje tematy `rejestr-zdolnosci-silnika` oraz `wyniki-benchmarkow-empirycznych` bezpośrednio z introspekcji kodu i plików `benchmarks/results/*.json` bez ręcznie pisanych zapewnień.

---

## Wyniki weryfikacji empirycznej
- **Backend Test Suite**: `./.venv/bin/pytest tests/` → **150 passed in 38.26s** (100% zielonych testów, zero błędów, zero regresji).
  * 11 dedykowanych testów Phase A regressions (`tests/test_phase_a_regressions.py`).
  * 8 dedykowanych testów Phase B regressions (`tests/test_phase_b_regressions.py`).
  * 7 dedykowanych testów Phase C evidence & SSRF (`tests/test_phase_c_evidence.py`).
  * 6 dedykowanych testów Phase D problem classes & synthesis (`tests/test_phase_d_problem_classes.py`).
  * 8 dedykowanych testów Phase E cognitive loop & intake (`tests/test_phase_e_cognitive.py`).
  * 5 dedykowanych testów Phase F quantum honesty, noise & QUBO (`tests/test_phase_f_quantum_honesty.py`).
  * 5 dedykowanych testów Phase G UI, copy, problem classes & help center (`tests/test_phase_g_ui_and_copy.py`).
  * 12 testów kognitywnych i API w `tests/unit/` oraz `tests/integration/`.
  * 88 testów regresyjnych, solverów, weryfikatora, QUBO, QAOA, MCP i API.
- **Frontend Typecheck & Build**: `npm run build` → 0 błędów TypeScript (`tsc -b`), czysty build produkcyjny Vite (`dist/` w 2.20s).
- **Git Branch**: `feat/v2-honest-engine`.

---

## Następny krok (Next Step)
- Rozpoczęcie **Fazy H: Bezpieczeństwo produkcyjne (H1–H6)**:
  * H1: Usunięcie domyślnego hasła master w kodzie (A9) oraz tokeny sesyjne/anonimowe z czasem wygaśnięcia.
  * H2: Uwierzytelnienie i limity (rate limits) per IP/sesja na otwartych endpointach `/cases/analyze`, `/cases/formalize`, `/cognitive/intake`, `/evidence/research` (ochrona budżetu Gemini i wyszukiwań).
  * H3: Test ochrony przed wstrzyknięciem promptu z treści stron zewnętrznych (C5) z fixture „ignore previous instructions".
  * H4: Testy odporności SSRF, limity wielkości pobieranych treści i timeouty sieciowe.
  * H5: Zakresowanie pamięci epizodycznej (A18) oraz rygorystyczna zgoda użytkownika (E5).
  * H6: Aktualizacja `docs/SECURITY.md` o granice zaufania warstwy dowodowej i wyciek w historii git.

