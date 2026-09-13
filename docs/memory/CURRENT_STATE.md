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

---

## Wyniki weryfikacji empirycznej
- **Backend Test Suite**: `./.venv/bin/pytest tests/` → **111 passed in 59.75s** (100% zielonych testów, zero błędów, zero regresji).
  * 11 dedykowanych testów Phase A regressions (`tests/test_phase_a_regressions.py`).
  * 12 testów kognitywnych i API w `tests/unit/` oraz `tests/integration/`.
  * 88 testów regresyjnych, solverów, weryfikatora, QUBO, QAOA, MCP i API.
- **Frontend Typecheck & Build**: `npm run build` → 0 błędów TypeScript (`tsc -b`), czysty build produkcyjny Vite (`dist/`).
- **Git Branch**: `feat/v2-honest-engine`.

---

## Następny krok (Next Step)
- Rozpoczęcie **Fazy B (Usunięcie półśrodków i brakujących ogniw, B1–B7)**:
  * B1: Implementacja wielokryterialnej macierzy decyzyjnej `DecisionMatrix` z obiektami `ScoredValue(value, unit, provenance, source_ref)` oraz analitycznym punktem zwrotnym (break-even point).
  * B2: Rozszerzenie analizy wrażliwości o tryb `re-solve` w `backend/domain/sensitivity.py`.
  * B3: Weryfikacja podpisów HMAC w `IndependentVerifier` i endpoint `POST /api/v1/verification/check`.
  * B4: Zunifikowany gateway LLM `backend/infrastructure/llm_gateway.py` z budżetowaniem tokenów i fallbackami.
  * B5: Rozszerzenie `ProblemIR` o metadane proweniencji.
  * B6: Dynamiczny router solverów w `backend/domain/router.py`.
  * B7: Aktualizacja narzędzi w `mcp_server/server.py`.

