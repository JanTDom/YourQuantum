# DECISIONS.md — Architecture and Product Decisions

**Last updated:** 2026-09-09

Each decision records: ID, date, decision, rationale, alternatives considered,
consequences, status, and whether it has been superseded.

Status: ACTIVE | PROPOSED | SUPERSEDED

---

## DEC-001 — Use AGENTS.md as the always-active rule file

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
Embed all always-active project rules in the root `AGENTS.md` file rather than
in `.agents/rules/*.md` files with frontmatter triggers.

**Rationale:**
The Antigravity customisation documentation (agy-customizations/docs/rules.md,
verified 2026-09-09) states that `AGENTS.md` (and global GEMINI.md) are always active
for their directory scope without requiring frontmatter. The documentation does
not describe a supported `always_on` frontmatter trigger for standalone rule
files. Using `AGENTS.md` is the confirmed, supported path.

**Alternatives considered:**
- `.agents/rules/*.md` with `trigger: always_on` frontmatter — no evidence this
  is supported in the current version; would risk silent failure.
- Multiple AGENTS.md files per subdirectory — premature; not needed at this stage.

**Consequences:**
- AGENTS.md is the single source of always-active rules.
- Changing a rule requires editing AGENTS.md and updating this decision log.
- Future versions of Antigravity may support richer rule triggers; migrate then.

---

## DEC-002 — Problem IR is the contract between all components

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
All components (LLM formaliser, router, solvers, verifier, frontend) communicate
through the versioned Problem IR. No component reads another component's internal
state.

**Rationale:**
This is the only design that makes independent verification possible. A verifier
that reads solver state cannot be independent. A router that calls solvers
directly couples method selection to implementation.

**Alternatives considered:**
- Passing solver-specific configs directly — rejected because it couples router to
  solver internals and prevents swapping solvers without changing the router.
- Having the LLM produce solver configs directly — rejected because LLM output is
  untrusted and would bypass the formalisation/approval step.

**Consequences:**
- All breaking changes to the IR require version increment.
- User approval is tied to the IR version; re-approval needed on version change.
- Each solver adapter must implement `can_handle(problem_ir)` and
  `solve(problem_ir, budget)`.

---

## DEC-003 — Quantum module is mandatory architecture, optional per task

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
The quantum algorithm module is a required architectural component. Its use on
any specific problem is determined by the router based on problem structure,
budget, and capability comparison — not assumed.

**Rationale:**
This avoids both failure modes: (a) omitting quantum entirely when it would
genuinely help, and (b) using quantum on every task for branding purposes at the
cost of result quality.

**Alternatives considered:**
- Quantum always used — rejected (degrades results when classical is better).
- Quantum as optional plugin — rejected (risks it never being built or tested).

**Consequences:**
- The quantum module must be built and benchmarked even if it is not the default
  path for most problems.
- The router must have access to classical/quantum performance estimates.

---

## DEC-004 — No performance claims without benchmark data

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
No efficiency, speed, or quantum advantage claim enters any product document,
README, or UI copy until it is supported by a recorded benchmark result that
satisfies the criteria in `docs/BENCHMARK_PROTOCOL.md`.

**Rationale:**
Premature claims create technical debt, mislead users, and undermine trust when
benchmarks are eventually run and contradict the claims.

**Alternatives considered:**
- Qualitative claims ("may offer advantage") — rejected because these are
  indistinguishable from marketing and are still misleading without evidence.

**Consequences:**
- `docs/PRODUCT.md` and all user-facing copy must be audited before release
  for unsubstantiated performance claims.
- Benchmarking is a first-class development task, not an afterthought.

---

## DEC-008 — Two-Tier Architecture for Problem Formalizer

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
The Problem Formalizer operates on a two-tier model:
1. Primary: Deterministic semantic heuristic engine (100% offline, zero-dependency, parses common archetypes like Knapsack, Max-Cut, Portfolio, and linear equations).
2. Secondary / Optional: LLM adapter (activates only when `GEMINI_API_KEY` or `OPENAI_API_KEY` is present in the environment).

**Rationale:**
Conforms strictly to the project rule: *"Nie wymagaj płatnej infrastruktury do uruchomienia pierwszej lokalnej wersji"*, while providing immediate intelligent text understanding out-of-the-box.

---

## DEC-009 — Dual-Run Benchmark Architecture (CP-SAT vs QAOA)

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
Provide a native `POST /api/v1/benchmarks` endpoint and UI button that executes classical (`cp_sat`) and quantum simulation (`qaoa_aer`) concurrently on the exact same ProblemIR with identical time and resource constraints.

**Rationale:**
Enforces the core rule: *"When a classical method outperforms the quantum module, give the user the better result — not a slower computation for the product name's sake."* Benchmarks provide honest, side-by-side comparisons of runtime, optimality, and feasibility.

---

## DEC-010 — Transparent Quantum Inspection Panel

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
Every QAOA run exposes physical circuit metrics (number of qubits, circuit depth, gate count, layers $p$, variational angles $\vec{\gamma}, \vec{\beta}$) and a full measurement sampling distribution histogram in the UI.

**Rationale:**
Prevents black-box quantum claims. Every bitstring count and percentage is verifiable, with an explicit honest badge: *"Symulacja stanu kwantowego na CPU (Qiskit Aer), nie fizyczny procesor kwantowy"*.

---

## DEC-011 — Clean External Audit Packaging Protocol

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
The external audit archive is assembled via an isolated staging pipeline excluding all vendor artifacts (`node_modules`, `.venv`), build directories (`dist`, `build`), cache directories (`__pycache__`, `.pytest_cache`), local runtime databases (`*.db`), and secret configurations. The package is accompanied by audit instructions (AUDIT_README.md, README.md), `requirements.txt`, and `.env.example`.

**Rationale:**
Allows independent third-party auditors to reproduce, inspect, run unit/E2E test suites, and audit architecture without risk of credentials leakage, environment pollution, or symlink vulnerabilities.

---

## DEC-012 — Two-Tier Problem Modeling: DecisionCase Decoupled from ProblemIR

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
Decouple the human dilemma and decision-making model (`DecisionCase`) from the computational intermediate representation (`ProblemIR`).
- `DecisionCase` captures options, explicit user facts with units, unknowns (with interactive clarification Q&A), and trade-offs.
- `ProblemIR` is an immutable, versioned mathematical AST (variables, constraints, objective trees).
- Solvers are never fed fabricated $x_0, x_1, x_2$ variables for qualitative life dilemmas.

**Rationale:**
Everyday users think in terms of dilemmas, options, and tradeoffs, not binary matrix representations. This prevents premature mathematical projection and hallucinated variables.

---

## DEC-013 — Server-Side Publication Gate for Recommendations

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
Implement a strict publication gate on `JobRecord`:
- Results are only marked `PUBLISHED_VERIFIED` if the `IndependentVerifier` re-evaluates all constraints and objective from scratch and yields `Verdict.PASS`.
- Violations or evaluation exceptions yield `REJECTED_UNVERIFIED`.
- Problems require explicit human sign-off via `POST /problems/{id}/approve` before solver jobs can be queued.

**Rationale:**
Eliminates unverified candidate leaks and removes false certainty claims.

---

## DEC-014 — Porcelain & Slate Calm Studio Interface & 5-Section Recommendation Architecture

**Date:** 2026-09-09
**Status:** ACTIVE

**Decision:**
Replace monolithic single-file UI with a calm studio component architecture:
1. Palette: Porcelain & Slate (`tokens.css`), eliminating neon gradients and dark quantum photos.
2. Recommendation format strictly follows 5 human answers:
   1. Co z tego wynika dla Ciebie
   2. 2–3 kluczowe powody wyboru
   3. Kompromisy i koszty wyboru
   4. Analiza wrażliwości („Co-jeśli”)
   5. Bezpośredni następny krok
3. Technical verification details and solver metrics are collapsed into an `EvidenceDrawer`.

**Rationale:**
Delivers an accessible, dignified product experience for everyday human problem-solving without cognitive overload.

---

## DEC-015 — Domain-Agnostic Priority Tokens, Break-Even Negotiation & Print Reporting

**Date:** 2026-09-11
**Status:** ACTIVE

**Decision:**
1. **Priority Tokens over Raw Numerical Sliders**: Replace all numerical mathematical sliders with contextual priority pills (e.g. `⏱️ Oszczędność czasu`, `🔄 Elastyczność`, `🏡 Większy metraż`, `💰 Niższy koszt`, plus user-defined custom priority creation). The optimization model translates these tokens into calibrated objective weights without exposing mathematical jargon to the user.
2. **Universal Domain-Agnostic Scope**: Dilemma intake, option generation, and formalization support any human, business, financial, or personal dilemma (not restricted to employment/jobs).
3. **Punkt Zwrotny (Break-Even Box)**: Provide explicit, actionable negotiation criteria describing what concrete conditions would need to shift for the runner-up option to become optimal.
4. **Bilans Decyzyjny (2-Column Comparison)**: Provide side-by-side comparative clarity on why the winning option prevailed over the runner-up.
5. **Executive Print Report (A4 / PDF)**: Provide 1-click clean printable output with official verification seal, hiding web navigation and ambient dark effects.


---

## DEC-016 — Dynamic Self-Synchronizing Layperson Help System

**Date:** 2026-09-11
**Status:** ACTIVE

**Decision:**
Implement an introspective knowledge base (`backend/api/help_service.py`) exposed via `GET /api/v1/help` and `GET /api/v1/help/snapshot`.
- Introspects live engine solver registry (`SOLVER_REGISTRY`), version, and supported dilemma domains dynamically.
- Formats guidance in crystal-clear layperson language (real-life examples, why the AI asks questions, slider trade-offs, independent verification, and common dilemmas).
- Syncs automatically whenever new solvers or capabilities are registered.

**Rationale:**
Prevents documentation rot. A changing solver or verification suite updates the help center instantly without manual copywriting edits.

---

## DEC-017 — 3D Cognitive Brain Architecture with Protected Know-How

**Date:** 2026-09-11
**Status:** ACTIVE

**Decision:**
Implement a WebGL 3D interactive cognitive brain (`frontend/src/components/EngineBrain3D.tsx`, `frontend/src/components/BrainModal.tsx`) using Three.js with three synchronized layers:
1. **Cognitive Hypergraph**: Multi-criteria nodes connected by additive glowing synaptic curves.
2. **QUBO / Hamiltonian Energy Landscape**: Continuous undulating wave surface converging to a deep gravitational well (Global Optimum ground state).
3. **Interference Gyroscope Rings**: Orthogonal concentric rings visualizing phase coherence and quantum tunneling.
4. **Strict Know-How Protection**: Visualizes topological energy landscapes and multi-criteria balance as abstract physical metaphors (coherence, synergy vector, boundary margins) without exposing private proprietary formulas, penalty multipliers, or source code.

**Rationale:**
Delivers an Awwwards/FWA-grade presentation that inspires trust and awe in the engine's scientific depth while guarding intellectual property.

---

## DEC-018 — Total Quantum Supremacy Engine (Warm-Start QAOA, Exact Slack, Dual Bound Certificate & Shock Testing)

**Date:** 2026-09-12
**Status:** ACTIVE

**Decision:**
To cement an indisputable mathematical and algorithmic advantage over autoregressive AI chatbots (ChatGPT/Claude), implement a six-pillar supremacy upgrade across the backend and frontend:
1. **Algebraic Input Quality Gate**: Automatically detect and flag underspecified inputs (<15 words, lacking concrete alternatives, or missing required quantitative constraints) before entering combinatorial optimization.
2. **Exact QUBO Binary Slack Expansion**: Map linear inequalities $\sum a_i x_i \le B$ to QUBO without approximate heuristic penalties by computing exact integer slack bounds and binary logarithmic expansions with dynamically calibrated quadratic penalties.
3. **Warm-Started QAOA**: Continuous quadratic relaxation via L-BFGS-B in $[0, 1]^n$ mapped to single-qubit $R_y(\theta_i)$ angles ($\theta_i = 2 \arcsin(\sqrt{x_i^*})$), seeding the initial quantum state and cutting variational parameter convergence time.
4. **Independent Dual Bound Gap & SHA-256 Audit Passport**: Independent LP continuous relaxation via HiGHS to establish rigorous dual lower bounds, computing proven optimality gap percentages, alongside a cryptographic SHA-256 hash sealing the verified decision state.
5. **Multi-Horizon Stress-Testing Engine**: Systematic sensitivity testing against $\pm 5\%$, $\pm 15\%$, and $\pm 25\%$ parameter and constraint shocks, yielding a definitive robustness index and stability verdict.
6. **Hybrid Benders Decomposition Solver**: Co-scheduling QAOA master combinatorial solver with CP-SAT constraint feasibility verification and integer cut generation.

**Rationale:**
LLM chatbots generate plausible probabilistic text but cannot guarantee constraint satisfaction, bounds, or mathematical proofs. YourQuantum produces verifiable, cryptographically sealed, and shock-tested solutions.

---

---

## DEC-020 — Official Model Context Protocol (MCP) Server Integration for Claude and Cowork

**Date:** 2026-09-12
**Status:** ACTIVE

**Decision:**
Implement an official Model Context Protocol (MCP) server in Python (`mcp_server/`) operating over stdio transport. Expose 4 core tools:
1. `yq_optimize_options`: general multi-criteria discrete optimization with strict input validation and zero silent defaults.
2. `yq_solve_portfolio`: capital / project portfolio allocation under hard budget limits.
3. `yq_analyze_dilemma`: Input Quality Gate assessing completeness, options, and numbers in natural language.
4. `yq_get_engine_status`: API connectivity and active solver telemetry.

**Non-Negotiable Honesty Rule:**
The MCP server strictly enforces that the returned result is a mathematical optimum relative ONLY to the explicitly provided criteria, weights, and constraints. It never poses as an absolute oracle, never silently substitutes default weights or parameters, and reports failures with actionable human guidance.

**Rationale:**
Allows AI workflows in Claude Desktop, Claude Code, and Cowork to delegate combinatorial and multi-criteria optimization to YourQuantum with SHA-256 audit passports and stress-testing sensitivity reports.

---

## DEC-021 — Brain-Inspired Cognitive Architecture (Prefrontal Working Memory, Episodic Hippocampus & Active Inference with Gemini & Offline Fallback)

**Date:** 2026-09-13
**Status:** ACTIVE

**Decision:**
Implement a neurobiology-inspired cognitive orchestration layer (Stage 4) using:
1. **Prefrontal Cortex / Working Memory & Cybernetic Homeostasis**: `EnergyBudget` preventing runaway token/cycle usage and `GlobalWorkspace` managing active goal, focal variables, hypotheses (`ProblemIR`), and prediction errors in process RAM.
2. **Hippocampal Episodic Memory**: Persistent database storage in `cognitive_traces` table with associative recall based on structural problem fingerprints, ranking historical high-reward patterns.
3. **Karl Friston Active Inference Loop**: Initial hypothesis formulation, static constraint sanity checking to fast-fail obvious contradictions, and reflection on independent verifier failure signals as prediction errors to iteratively adjust models and penalty weights.
4. **Hexagonal Reasoning Port & Gemini Adapter**: `CognitiveReasoningPort` domain interface with `GeminiCognitiveAdapter` (Gemini 2.5 Flash, structured JSON, temperature 0.0) and seamless local deterministic rule-based offline fallback when `GEMINI_API_KEY` is missing or when network errors occur.

**Rationale:**
Provides transparent, biologically motivated problem intake and formulation while preserving the core scientific boundary: LLMs only help translate and calibrate hypotheses, while hard solvers compute solutions and independent verifiers certify them.

---

## DEC-022 — Kontenerowa architektura serwisów obliczeniowych (Compute Worker Container)

**Date:** 2026-09-13
**Status:** ACTIVE

**Decision:**
Rozdzielić architekturę wdrożeniową YourQuantum na dwie odrębne warstwy:
1. **Frontend & API Gateway (Vercel / Edge)**: statyczny interfejs React/Vite, lightweight proxy API, intake parsers i routing.
2. **Dedicated Compute Worker Container (Docker / Cloud Run / Fly.io / Kubernetes)**: asynchroniczny kontener wykonawczy z pełnym stosem obliczeniowym (Python 3.11+, Google OR-Tools C++ extensions, Qiskit Aer C++ simulator, SciPy, HiGHS, Z3). Komunikacja za pośrednictwem kolejki zadań (PostgreSQL jobs table / Redis BullMQ) z pollingiem lub WebSockets/SSE.

**Rationale:**
Platformy serverless (takie jak Vercel Functions czy AWS Lambda) nakładają twarde ograniczenia:
- Maksymalny czas wykonania (execution timeout): 10–60 sekund, co uniemożliwia wielominutowe optymalizacje kombinatoryczne, przeszukiwania branch-and-bound czy symulacje obwodów QAOA.
- Maksymalny rozmiar spakowanego artefaktu (bundle limit): 250 MB (rozpakowane) / 50 MB (zip). Stos obliczeniowy (`ortools`, `qiskit`, `qiskit_aer`, `scipy`, `numpy`) przekracza 650 MB i wymaga natywnych bibliotek C++ (glibc, OpenMP).
Dedykowany kontener roboczy (Worker Container) eliminuje limity rozmiaru pamięci podręcznej i czasu wykonania, gwarantując determinizm środowiska numerycznego.

**Alternatives considered:**
- Uruchamianie solverów bezpośrednio w Vercel Serverless Functions: odrzucone z powodu przekroczenia limitu rozmiaru paczki (bundle size > 500MB) oraz timeoutów przy trudnych instancjach NP-trudnych.
- Client-side WebAssembly (Pyodide): odrzucone, brak pełnej obsługi wielowątkowego Qiskit Aer i OR-Tools CP-SAT w środowisku przeglądarki.

**Consequences:**
- Obliczenia backendowe działają asynchronicznie (`JobRecord` ze statusem `QUEUED` -> `RUNNING` -> `COMPLETED`/`FAILED`).
- Dedykowany kontener obliczeniowy zdefiniowany przez specyfikację Dockerfile (tworzoną i wdrażaną w N1).

### SUPERSEDED BY (2026-09-13 — Ship Numeric/Quantum Stack in Vercel Function)
Uzasadnienie dotyczące twardego limitu 250 MB dla funkcji Pythona na platformie Vercel uległo dezaktualizacji:
- 29 czerwca 2026 r. Vercel ogłosił wsparcie dla "Large Functions" do 5 GB (wymagające Fluid compute z włączonym Active CPU; włączane zmienną środowiskową `VERCEL_SUPPORT_LARGE_FUNCTIONS=1`).
- Standardowy limit nieskompresowanej paczki dla funkcji Python został oficjalnie podniesiony z 250 MB do 500 MB.
- Źródła oficjalne (odnotowane w `docs/SOURCES.md`):
  * https://vercel.com/docs/functions/limitations (aktualizacja 2026-08-24) — limit 500 MB dla Pythona oraz do 5 GB dla Large Functions.
  * https://vercel.com/changelog/vercel-functions-can-now-be-up-to-5-gb-in-package-size (2026-06-29).
  * https://vercel.com/changelog/python-vercel-functions-bundle-size-limit-increased-to-500mb.
- W rezultacie pełny stos obliczeniowy (`scipy`, `ortools`, `qiskit`, `qiskit-aer`) o zoptymalizowanym rozmiarze pakietu ~499.9 MB został przywrócony bezpośrednio do `api/requirements.txt` (commit `71deb27`) i z sukcesem wdrożony na produkcję `https://yourquantum.pl`.
- Endpoint `GET /api/v1/health/solvers` potwierdza `available=true` dla solverów `cp_sat`, `qaoa_aer`, `hybrid_benders` oraz `scipy_continuous`.
- Architektura kontenerowa (`Dockerfile`, `docker-compose.yml`, `requirements-worker.txt`) pozostaje w repozytorium jako wariant alternatywny/zapasowy, na wypadek zadań wymagających wielominutowego czasu procesora przekraczającego limity funkcji (300 s / 800 s) lub ze względów optymalizacji kosztowej Active CPU.
---

## DEC-023 — Rozszerzenie Problem IR o 5 klas problemów (Taxonomy v0.3)

**Date:** 2026-09-13
**Status:** ACTIVE

**Decision:**
Rozszerzyć Problem IR do wersji 0.3 wprowadzając taksonomię 5 fundamentalnych klas problemów:
1. `CHOICE` — wielokryterialny wybór z dyskretnej listy opcji (wagi od użytkownika, analityczny próg zwrotny).
2. `ALLOCATION` — podział zasobu/budżetu (plecak, portfel, harmonogramowanie) z ograniczeniami pojemności.
3. `DESIGN` — synteza architektoniczna wielodźwigniowa (równoczesny dobór opcji z synergią i wykluczeniami).
4. `PARAMETER` — ciągłe dostrajanie parametrów (SciPy HiGHS / minimalizacja ciągła).
5. `NOT_COMPUTABLE` — dylematy etyczne/światopoglądowe; system odmawia fałszywych obliczeń i oferuje konstruktywne przekształcenie w mierzalne kryteria.

**Rationale:**
Zapobiega sztucznemu wtłaczaniu każdego pytania w jeden schemat (np. unikanie wymuszania QUBO tam, gdzie naturalny jest CP-SAT lub problem jest nieobliczalny).

---

## DEC-024 — Warstwa dowodowa, obrona przed wstrzyknięciem promptu i ochrona SSRF

**Date:** 2026-09-13
**Status:** ACTIVE

**Decision:**
Wprowadzić warstwę `Evidence Layer` pobierającą fakty z internetu wyłącznie przez utwardzony `SafeWebFetcher` z pre-rezolucją DNS i filtrem SSRF (blokującym loopback, link-local, RFC 1918 i adresy metadata chmury `169.254.169.254`). Treść stron zewnętrznych podlega sanityzacji w `EvidenceExtractor`: ucieczce markerów granicznych, neutralizacji poleceń prompt injection oraz heurystycznemu filtrowaniu zdań atakujących.

**Rationale:**
Zewnętrzne strony internetowe są z natury niezaufane na granicy systemu. Nieostrożne wstrzyknięcie tekstu strony w kontekst LLM mogłoby zafałszować liczby w modelu decyzyjnym (np. zerując koszty).

---

## DEC-025 — Synteza wielodźwigniowa (DESIGN Class) z frontem Pareto i rankingiem ważności

**Date:** 2026-09-13
**Status:** ACTIVE

**Decision:**
Dla klasy `DESIGN` interfejs i backend zwracają:
1. Konfigurację optymalną z dowodem spójności reguł wykluczenia.
2. Interaktywny 2D front Pareto punktów niezdominowanych (wielokryterialny trade-off).
3. Ranking wrażliwości dźwigni (procentowy udział każdej dźwigni w zmienności wyniku systemu).
4. Obowiązkowe zastrzeżenie formalne: *"Rozwiązanie model-optymalne (optymalne dla zdefiniowanego modelu i wag, nie absolutnie optymalne dla świata)"*.

**Rationale:**
Złożone decyzje publiczne i architektoniczne (np. reforma ochrony zdrowia) nie mają jednego „magicznego" punktu bez kompromisów; użytkownik musi widzieć przestrzeń wariantów Pareto i wiedzieć, która dźwignia decyduje o wyniku.

---

## DEC-026 — Rygorystyczna walidacja dowodu wykonania obwodu kwantowego (F1 Quantum Execution Evidence)

**Date:** 2026-09-13
**Status:** ACTIVE

**Decision:**
Wprowadzić moduł dowodów kwantowych `backend/domain/evidence/models.py` (rekord `QAOARunRecord`). Żaden wynik oznaczony jako `source == QUANTUM_CIRCUIT_SIMULATION` lub `PHYSICAL_QPU_EXECUTION` nie może zostać opublikowany bez weryfikowalnego rekordu telemetrii obwodu: `circuit_depth > 0`, `gate_count > 0`, `shots > 0`, backend name.

**Rationale:**
Zgodnie z regułą dowodową AGENTS.md §7 i eliminacją błędu A1, zabrania się podszywania obliczeń klasycznych lub losowych liczb pod obwody kwantowe.

---

## DEC-027 — Wielopoziomowe limity zapytań (Sliding Window, Quotas, Circuit Breaker) i tokeny sesyjne

**Date:** 2026-09-13
**Status:** ACTIVE

**Decision:**
Wdrożyć `RateLimiter` w `backend/api/security_guard.py`:
1. Ruchomy bufor czasowy (Sliding Window): 15 zapytań/min dla sesji anonimowych, 150 dla uwierzytelnionych.
2. Dzienny limit per klient: 60 zapytań/dzień anonimowo, 600 zapytań/dzień autoryzowany.
3. Globalny bezpiecznik kosztowy (Circuit Breaker): 600 wywołań LLM dziennie na całą instalację.
4. Podpisywane kryptograficznie tokeny sesyjne HMAC-SHA256 (`yq_sess_<exp>_<hash>_<sig>`).

**Rationale:**
Ochrona budżetu API przed atakami Denial-of-Wallet oraz wyczerpaniem limitów zewnętrznych modeli bez autoryzacji.

---

## DEC-028 — Ścisła izolacja dzierżawców i bramka zgody w pamięci epizodycznej

**Date:** 2026-09-13
**Status:** ACTIVE

**Decision:**
Pamięć robocza sesji (`WorkingMemory`) jest trwała w ramach aktywnej sesji użytkownika w SQLite, natomiast pamięć epizodyczna (`EpisodicMemory`) podlega ścisłemu zakresowaniu per dzierżawca (`tenant_id`) i wymaga jednoznacznej, uprzedniej zgody użytkownika (`consent=True`). Przy braku zgody konsolidacja zostaje pominięta (`skipped`).

**Rationale:**
Zgodność z RODO/GDPR oraz eliminacja ryzyka przecieku danych wrażliwych i dylematów decyzyjnych między różnymi użytkownikami platformy.

---

## DEC-029 — Grounding LLM = lista URL, nie dowód

**Date:** 2026-09-13
**Status:** ACTIVE

**Decision:**
Mechanizm Google Search Grounding modelu Gemini (oraz wszelkie pokrewne narzędzia wyszukiwania wbudowane w LLM) może być wykorzystywany **wyłącznie jako źródło kandydatów URL** (`groundingChunks[].web.uri` + metadane tytułu).
1. Treść wygenerowana przez model (`parts[].text`) nigdy nie jest traktowana jako treść strony (`page_text`), nie stanowi podstawy do obliczenia skrótu kryptograficznego `content_hash` i nie bierze udziału w weryfikacji cytatu (`_verify_quote_in_text`).
2. Każdy dokument dowodowy (`EvidenceDocument`) musi zostać realnie pobrany i zdezynfekowany przez `SafeWebFetcher`. Jeśli pobranie się nie powiedzie, dokument i dowód nie powstają (`Evidence` nie jest tworzone).
3. Niedozwolone jest tworzenie fikcyjnych źródeł syntetycznych (np. `https://google.com/search`). Przy braku realnych linków lista wyników jest pusta.
4. Dobór dostawcy wyszukiwania jest jawny (`SEARCH_PROVIDER=gemini|tavily|serper|none`). Sama obecność `GEMINI_API_KEY` nie włącza wyszukiwania.

**Rationale:**
Zgodnie z regułą dowodową i eliminacją halucynacji (BUILD_SPEC_V2.md §1 pkt 4 oraz audyt V4 R6), uznanie tekstu wygenerowanego przez model za „stronę źródłową" prowadzi do samopotwierdzenia halucynacji modelu w weryfikatorze cytatów, podszywając się pod obiektywne dane empiryczne.

---

## DEC-030 — Prezentacja dwuwarstwowa: Executive Briefing dla decydenta i rozwijany rdzeń techniczny

**Date:** 2026-09-14
**Status:** ACTIVE

**Decision:**
Ekran rekomendacji i syntezy decyzyjnej (`frontend/src/components/RecommendationView.tsx`, `DesignSynthesisResult`) zostaje podzielony na dwie rozłączne warstwy percepcyjne:
1. **Warstwa 1 (Główna, domyślnie widoczna): Human Executive Briefing**
   - Naturalny, strategiczny język (klasa ChatGPT/Claude na poziomie doradcy zarządu/decydenta).
   - Diagnoza sytuacji i *Wnioski w pigułce* wyjaśniające kierunek w sposób zrozumiały dla każdego decydenta.
   - *Kluczowe Filary Rozwiązania* z kartami odpowiedzi na pytanie: `Dlaczego to rozwiązanie?`.
   - *Główny kompromis (Cena wyboru)* oraz *Kiedy wynik uległby zmianie (Punkty wrażliwości)*.
   - Całkowita eliminacja surowego żargonu badań operacyjnych („Front Pareto”, „Dźwignia #1”, „Optymalna konfiguracja architektury systemowej”) z warstwy strategicznej.
2. **Warstwa 2 (Szuflada analityczna, domyślnie zwinięta): Rdzeń matematyczny i weryfikator**
   - Przycisk `#btn-toggle-technical-details` rozwijający interaktywny wykres 2D frontu Pareto z wyborem osi kryteriów, ranking ważności dźwigni, synergie i wykluczenia, źródła instytucjonalne oraz dowód weryfikatora.
   - Zachowuje 100% rygoru dowodowego (brak fikcyjnych danych, niezależna weryfikacja naruszeń ograniczeń).

**Rationale:**
Użytkownicy i decydenci potrzebują natychmiastowego zrozumienia rekomendacji i jej ceny (kompromisu) w naturalnym języku. Zmuszanie użytkownika do dekodowania surowych wykresów Pareto i macierzy przed zrozumieniem wniosku budziło opór percepcyjny, mimo że silnik obliczeniowy pod spodem działał bezbłędnie. Architektura dwuwarstwowa łączy zrozumiałość interfejsu czatu z niezawodnością i dowodowością matematyczną.

---

## DEC-031 — Kwantowa kombinatoryka scenariuszy i prognozowanie ryzyka metodą reguły Borna

**Date:** 2026-09-14
**Status:** SUPERSEDED BY DEC-032 (2026-09-14)

**Powód zastąpienia (Ustalenia audytu zewnętrznego V5):**
1. **Warstwa kwantowa nie wykonywała żadnego obliczenia fizycznego ani kwantowego**:
   W usuniętym module pseudokwantowym (zastąpionym obecnie przez `backend/domain/scenario_weighting.py`) kod wyliczał analityczne wagi Gibbsa, normalizował je, ładował wektor amplitud przez `qc.initialize` do symulatora `AerSimulator`, po czym odczytywał `save_statevector()` i podnosił moduł do kwadratu. Obwód nie posiadał ani jednej bramki (brak ewolucji, brak interferencji, brak splątania) — zwracał dokładnie to, co wprowadzono:
   ```text
   ścieżka przez Qiskit Aer : {'s1': 0.905733, 's2': 0.087247, 's3': 0.00702}
   ścieżka analityczna      : {'s1': 0.905733, 's2': 0.087247, 's3': 0.00702}
   identyczne?              : True
   ```
   Była to klasyczna funkcja softmax w przebraniu symulatora kwantowego, co bezpośrednio naruszało regułę z `AGENTS.md` §2 (*„Do NOT call weight changes 'quantum interference'”*).
2. **Zmyślone liczby wejściowe**: wagi, wiarygodność i wpływy generował model językowy bez weryfikacji dowodowej, a fallback zawierał wpisane w kodzie geopolityczne stałe (np. wpływ 0.85 / 0.25 / -0.95 przy pewności 0.98).
3. **Powołanie się na SafeWebFetcher było nieuprawnione**: silnik pobierał jedynie krótkie snippety z wyszukiwarki i wklejał je do promptu LLM, omijając bezpieczne pobieranie stron, sprawdzanie cytatów i hashowanie treści.
4. **Ukryta stała beta = 1.8**: wynik zależał w przeważającej mierze od arbitralnie dobranej stałej sterującej ostrością rozkładu.

---

## DEC-032 — Uczciwa prognoza scenariuszowa i badanie wrażliwości założeń decydenta (Ważony Softmax)

**Date:** 2026-09-14
**Status:** ACTIVE

**Decision:**
Funkcja analizy scenariuszowej zostaje zachowana, lecz oczyszczona z wszelkich fałszywych metafor kwantowych i zastąpiona rzetelnym modelem ważonej agregacji założeń decydenta:
1. **Silnik ważonej agregacji (`backend/domain/scenario_weighting.py`)**:
   - Całkowite usunięcie zależności od Qiskit Aer z tej ścieżki (moduł kwantowy w `backend/solvers/quantum/` i klasa `DESIGN` pozostają nietknięte).
   - Jawny wzór matematyczny softmax / Gibbsa z bazowym parametrem $\beta = 1.0$:
     $$S(s_i) = \sum_{p \in P_{aktywne}} w_p \cdot c_p \cdot I(s_i, p)$$
     $$P(s_i) = \frac{\exp(\beta (S(s_i) - \max_j S(s_j)))}{\sum_k \exp(\beta (S(s_k) - \max_j S(s_j)))}$$
   - Każdy wynik zawiera pasmo wrażliwości (`sensitivity_band`) dla $\beta \in \{0.5, 1.0, 2.0, 3.0\}$, a interfejs prezentuje przedział (np. 56%–98%), uniemożliwiając przedstawianie pojedynczego procentu jako obiektywnej prawdy o świecie.
2. **Ścisły reżim pochodzenia danych (`provenance`)**:
   - Przesłanki z oznaczeniem `llm_suggested` **nie wchodzą do obliczeń**, dopóki użytkownik jawnie ich nie zatwierdzi (`is_accepted=True`).
   - Oznaczenie `web_sourced` przysługuje wyłącznie faktom zweryfikowanym przez `SafeWebFetcher` i `EvidenceExtractor`.
   - Brak domyślnych stałych geopolitycznych — brak danych skutkuje żądaniem ich wprowadzenia przez użytkownika.
3. **Analityczne punkty zwrotne (`compute_tipping_points`)**:
   - Zastąpienie generowanych akapitów geopolitycznych analitycznym wyliczaniem minimalnej delty wagi $\Delta w$ dla każdej przesłanki, która odwraca dominację wariantu wiodącego.
4. **Zawężenie routingu i przywrócenie rygorystycznych bramek**:
   - Usunięcie szerokich regexów z `is_scenario_forecast_query`; zapytania o zmianę pracy, wynajem biura, kurs językowy czy wybór taryfy trafiają do standardowej klasy `CHOICE`.
   - Bramka jakości wejścia dla prognoz scenariuszowych wymaga horyzontu czasowego, przedmiotu i alternatyw.
   - Przywrócenie odrzucania czystej punktowej spekulacji rynkowej (`NOT_COMPUTABLE`).
5. **Uczciwy interfejs w `frontend/src/components/RecommendationView.tsx`**:
   - Usunięcie etykiet kwantowych, tabel amplitud i fałszywych zapewnień o "obliczaniu przyszłości".
   - Wdrożenie interaktywnego edytora wag przesłanek z natychmiastowym przeliczaniem rozkładu i pasma wrażliwości.

---

## DEC-033 — Przywołania kodu w dokumentacji są weryfikowane maszynowo

**Date:** 2026-09-15
**Status:** ACTIVE

**Decision:**
Wszystkie formalne przywołania plików i numerów linii kodu w dokumentacji audytowej, raportowej i technicznej podlegają automatycznej, deterministycznej weryfikacji maszynowej przez skrypt `scripts/check_doc_citations.py`:
1. **Reguła R1 (Istnienie pliku):** Każdy przywołany plik (zarówno w postaci pełnej ścieżki, jak i jednoznacznej nazwy pliku) musi fizycznie istnieć w repozytorium.
2. **Reguła R2 (Zakres linii):** Wskazany numer linii lub przedział linii (`linie X–Y`) musi mieścić się w granicach pliku źródłowego ($1 \le line \le total\_lines$).
3. **Reguła R3 (Spójność cytatu/literału):** Literał w backtickach bezpośrednio poprzedzający przywołanie w nawiasie musi występować w oknie $\pm 3$ linii od wskazanej linii w pliku źródłowym (z normalizacją białych znaków, z wyłączeniem szablonów dynamicznych JSX `{...}` i wielokropków `...`).
4. **Bramka mechaniczna `G-DOCS`:** Skrypt `scripts/check_doc_citations.py` został włączony do `scripts/check_v4.sh` jako bramka `G-DOCS` wykonywana przed testami jednostkowymi i buildem frontendu. Jakiekolwiek naruszenie skutkuje błędem bramki (FAIL) i zablokowaniem merge'a.
5. **Dedykowany zestaw testów jednostkowych:** Skrypt posiada pełne pokrycie testami w `tests/unit/test_doc_citations.py`, weryfikującymi przypadek poprawny oraz testy negatywne (R1, R2, R3 z przesunięciem linii o +50, filtry JSX).

**Rationale:**
Lekcja z audytu V7/V8 wykazała, że nawet po gruntownym przepisaniu raportu w oparciu o kod źródłowy, błąd ludzki może doprowadzić do drobnego rozjazdu indeksów linii (wskazanie linii 90 schematu zamiast linii 189 domyślnej flagi w `backend/domain/cognitive/scenario_decomposer.py`). Zgodnie z zasadami L-021, L-022 oraz L-023 reguła dowodu wymaga, by spójność dokumentacji z kodem była egzekwowana mechanicznie w potoku CI/bramkach, a nie opierała się na deklaracjach.

---

## DEC-034 — Horyzont czasowy jest dekodowany deterministycznie, a nie zgadywany

**Date:** 2026-09-15
**Status:** ACTIVE

**Kontekst:**
Bramka jakości wykrywała perspektywę czasową pytania prognostycznego pojedynczym wyrażeniem regularnym (`202\d|lat\w*|miesi[aą]c\w*|perspektyw\w*|horyzont\w*|czas\w*|najbli[zż]sz\w*`). Wzorzec nie zawierał słowa „rok" w żadnej formie, przez co pytania takie jak „Czy Rosja do końca tego roku zaatakuje Polskę?", „w tym roku", „w przyszłym roku", „do końca dekady" czy „w ciągu 18 miesięcy" (odmiana „miesięcy" też nie była objęta) były odrzucane jako pozbawione horyzontu — mimo że horyzont był w nich wprost wyrażony. Dodatkowo próg długości (`len(words) < 7`) odrzucał poprawne, krótkie pytania w rodzaju „Czy Rosja zaatakuje Polskę do 2027?".

**Decyzja:**
1. Horyzont czasowy dekoduje dedykowany moduł `backend/domain/cognitive/time_horizon.py` (`detect_time_horizon`), deterministycznie i bez udziału modelu językowego.
2. Moduł **normalizuje** wyrażenie do daty granicznej (`end_date`) i podaje podstawę wyznaczenia (`basis`), dzięki czemu horyzont jest nie tylko wykrywany, ale i używany dalej.
3. Wyrażenia nieprecyzyjne („w najbliższych miesiącach") są rozpoznawane jako horyzont, ale otrzymują `end_date=None` oraz `is_precise=False`. **Daty nie wolno zmyślać** — to bezpośrednie zastosowanie zakazu fabrykowania liczb.
4. Rozpoznany horyzont jest przekazywany do promptu dekompozytora scenariuszy, aby scenariusze były ograniczone do wskazanego okresu, oraz zapisywany w telemetrii prognozy jako fakt odczytany z pytania.
5. Próg długości dla pytań scenariuszowych obniżono z 7 do 5 słów; o dopytaniu decyduje brak horyzontu, a nie długość zdania.

**Konsekwencje:**
Użytkownik nie jest pytany o perspektywę czasową, którą już podał. Rozszerzenie zakresu rozpoznawanych sformułowań wymaga dopisania reguły w `backend/domain/cognitive/time_horizon.py` wraz z testem w `tests/unit/test_time_horizon.py` — nie zaś rozbudowywania wyrażenia regularnego w bramce jakości.

---

## DEC-035 — Uziemienie przesłanek prognoz scenariuszowych w zweryfikowanych dokumentach sieciowych

**Date:** 2026-09-15
**Status:** ACTIVE

**Kontekst:**
W ścieżce analizy scenariuszowej (`backend/domain/cognitive/active_inference_engine.py`) silnik pobierał jedynie snippety z wyszukiwarki i wklejał je do promptu modelu językowego. W efekcie wszystkie przesłanki miały oznaczenie `provenance="llm_suggested"`, a znacznik `🌐 Zweryfikowane źródło sieciowe` w interfejsie (`frontend/src/components/RecommendationView.tsx`) pozostawał kodem nieosiągalnym.

**Decyzja:**
1. **Pełne pobieranie stron z weryfikacją**: Ścieżka scenariuszowa pobiera rzeczywistą treść stron za pomocą `SafeWebFetcher.fetch(url)` (ochrona SSRF, limit rozmiaru, hash SHA-256) oraz ekstraktuje dowody przez `EvidenceExtractor.extract_parameter_evidence(...)`.
2. **Weryfikacja dosłownego cytatu**: Przesłanka otrzymuje oznaczenie `provenance="web_sourced"` wyłącznie wtedy, gdy dosłowny cytat zostanie w 100% odnaleziony w pobranym tekście strony źródłowej.
3. **Rozdział faktu od interpretacji numerycznej**: Ze źródła sieciowego pochodzi *fakt i dosłowny cytat*. Wpływy liczbowe na poszczególne scenariusze proponuje model językowy, a decydent ma ich pełną świadomość dzięki dedykowanemu opisowi w interfejsie użytkownika.
4. **Bramka zatwierdzenia decydenta**: Zgodnie z zasadą ograniczonego zaufania do danych zewnętrznych, przesłanki `web_sourced` są domyślnie tworzone z `is_accepted=False` i nie wchodzą do obliczeń rozkładu bez aktywnej zgody człowieka. W związku z tym filtr aktywnych przesłanek w funkcjach `compute_scenario_distribution` oraz `compute_tipping_points` (`backend/domain/scenario_weighting.py`) obejmuje od teraz również przesłanki o pochodzeniu `web_sourced` (wymagając dla nich `is_accepted=True`).
5. **Budżet i telemetria**: Pobieranie ograniczone do maksymalnie 3 adresów URL per zapytanie z limitem czasu i kontrolą `ws.energy_budget`. Rzeczywiste liczby (zwrócone adresy, pobrane strony, zweryfikowane cytaty) są bez zmyślania zapisywane w telemetrii.

---

## DEC-036 — Bezpieczna weryfikacja bramki dostępu do aplikacji po stronie serwera

**Date:** 2026-09-15
**Status:** ACTIVE

**Kontekst:**
Bramka dostępu do aplikacji weryfikowała hasło po stronie klienta (`frontend/src/components/AuthGate.tsx`), porównując skróty SHA-256 ze stałą tablicą `AUTHORIZED_HASHES`. Choć nie ujawniało to hasła w tekście jawnym, lista skrótów była publicznie widoczna w bundlu JavaScript, co narażało ją na ataki słownikowe offline, a zmiana hasła wymagała ponownej kompilacji i wdrożenia frontendu.

**Decyzja:**
1. **Endpoint weryfikacyjny**: Utworzono dedykowany endpoint `POST /api/v1/auth/verify-app-access` w `backend/api/routes.py`.
2. **Sekret serwerowy**: Hasło dostępu konfigurowane jest w zmiennej środowiskowej `YQ_APP_ACCESS_SECRET`. Przy braku konfiguracji sekretu serwer zwraca kod HTTP 503 Service Unavailable z czytelnym komunikatem o konieczności konfiguracji środowiska.
3. **Bezpieczne porównanie**: Weryfikacja po stronie serwera odbywa się w stałym czasie za pomocą `hmac.compare_digest`. Obsługiwana jest lista haseł oddzielonych przecinkami w `YQ_APP_ACCESS_SECRET`; pętla porównuje kandydatów w pełnym przebiegu bez przedwczesnego przerywania (`early break`), zapobiegając atakom typu timing leak.
4. **Ograniczenie liczby prób (Rate Limiting)**: Wdrożono mechanizm ograniczania prób w pamięci procesu (5 nieudanych prób na 15 minut per adres IP; 6. próba zwraca kod HTTP 429 Too Many Requests). Uwaga architektoniczna: w środowisku serverless (Vercel) pamięć procesu nie jest współdzielona między niezależnymi instancjami lambd, w związku z czym ochrona w pamięci procesu chroni daną instancję; docelowe globalne ograniczanie prób wymaga zewnętrznego magazynu stanu (np. Redis / Upstash).
5. **Wygasający token sesyjny**: Po pomyślnej autoryzacji serwer wystawia podpisany kryptograficznie token HMAC-SHA256 (`yq_app_<exp>_<sig>`), który klient przechowuje w pamięci przeglądarki (`localStorage` w `frontend/src/components/AuthGate.tsx`).
6. **Eliminacja skrótów z klienta**: Tablica `AUTHORIZED_HASHES` została w całości usunięta z kodu frontendu.
7. **Wdrożenie produkcyjne (2026-09-17)**: Po pisemnej akceptacji Etap B został scalony z `feat/v9-technical-debt` do `main` (commity `afe2408` i `32c0d9d`) i wdrożony na żywą produkcję Vercel (`https://yourquantum.pl`). Zweryfikowano empirycznie: brak `AUTHORIZED_HASHES` w bundlu frontendu, kod HTTP 401 przy błędnym haśle z żywej domeny produkcyjnej.

---

## DEC-037 — Deterministyczne wyznaczanie wag przesłanek na podstawie cech dokumentów źródłowych

**Date:** 2026-09-17
**Status:** ACTIVE

**Kontekst:**
W wersjach V1–V11 wagi przesłanek (`weight`) oraz ich wiarygodności (`confidence`) były generowane subiektywnie przez model językowy (`backend/domain/cognitive/scenario_decomposer.py`), a w przypadku przesłanek sieciowych otrzymywały arbitralną domyślną wagę `1.0`. Model językowy oceniał wiarygodność na podstawie własnych asocjacji, co prowadziło do sytuacji, w których twierdzenia z blogów mogły otrzymać wagę wyższą lub równą oficjalnym raportom wywiadowczym lub instytucjonalnym, a decydent nie miał wglądu w to, dlaczego dana przesłanka ma określony wpływ.

**Decyzja:**
1. **Waga jako funkcja cech dokumentu**: Wagi przesłanek o pochodzeniu `web_sourced` nie pochodzą od modelu językowego ani arbitralnych stałych, lecz są obliczane deterministycznie w module `backend/domain/evidence/evidence_weighting.py` za pomocą jawnej formuły:
   $$W = 0.30 \cdot S_{\text{corroboration}} + 0.30 \cdot S_{\text{source\_class}} + 0.20 \cdot S_{\text{recency}} + 0.20 \cdot S_{\text{specificity}}$$
   gdzie:
   - $S_{\text{corroboration}} \in [0.1, 1.0]$: liczba niezależnych domen potwierdzających daną przesłankę ($\min(1.0, 0.4 + 0.3 \cdot (N - 1))$).
   - $S_{\text{source\_class}} \in [0.1, 1.0]$: klasa wiarygodności domeny wg konfiguracji `config/source_classes.json` (Tier 1: 1.0, Tier 2: 0.8, Tier 3: 0.6, Tier 4: 0.4, nieznane: 0.3).
   - $S_{\text{recency}} \in [0.1, 1.0]$: świeżość dokumentu względem daty publikacji lub wzmianek w tekście.
   - $S_{\text{specificity}} \in [0.1, 1.0]$: konkretność cytatu mierzona obecnością liczb, dat, kwot i wskaźników statystycznych.
2. **Pełna audytowalność**: Każda przesłanka zawiera pola `weight_breakdown` (wartości cząstkowe $S$) oraz `weight_justification` (tekstowe uzasadnienie wyliczenia).
3. **Transparentność w UI**: Komponent `WebEvidenceNotice` w `frontend/src/components/RecommendationView.tsx` wyświetla decydentowi rozbicie składowych wagi oraz uzasadnienie.
4. **Przesłanki bez źródeł**: Gdy brak źródeł sieciowych (`provenance === "llm_suggested"`), wagi pozostają neutralne ($1.00$), a interfejs wyświetla żółty baner uczciwości informujący, że przesłanki pochodzą wyłącznie od modelu i nie posiadają zweryfikowanych źródeł.

---

## DEC-038 — Uziemienie dowodów sieciowych przez selekcję indeksów zdań zamiast transkrypcji cytatów

**Date:** 2026-09-17
**Status:** ACTIVE

**Kontekst:**
W wersjach V12–V13 model językowy w zadaniu ekstrakcji dowodów (`EvidenceExtractor`) otrzymywał instrukcję przepisania dosłownego cytatu z dokumentu. Pomiary na żywej produkcji ujawniły, że LLM ma tendencję do sklejania komórek tabel, wstawiania wielokropków w miejsce pominiętych fraz, parafrazowania lub modyfikacji interpunkcji, co skutkowało odrzuceniem cytatu w bramce weryfikacyjnej (`web_quotes_verified = 0`, `web_quotes_unverified > 0`), mimo że pobrana strona zawierała poszukiwane fakty.

**Decyzja:**
1. **Model nie przepisuje cytatów**: Backend dzieli pobraną stronę na ponumerowane zdania za pomocą `split_into_sentences()` w `backend/infrastructure/web_research/extractor.py`, uwzględniając polskie skróty i formaty liczb, oraz śledzi dokładne indeksy znakowe (`char_start`, `char_end`) w tekście źródłowym.
2. **Selekcja indeksów zdań**: Model LLM otrzymuje ponumerowane zdania i wskazuje od 1 do 3 indeksów zdań (`sentence_indices`) zawierających dowód lub wskaźnik empiryczny, nie generując żadnego tekstu cytatu.
3. **Deterministyczne wycinanie przez backend**: Cytat jest wycinany bezpośrednio z tekstu strony za pomocą przedziału `[first_sentence.start, last_sentence.end]`. Długość cytatu jest ograniczona do 300 znaków, a `char_start` i `char_end` są zapisywane w modelu `Evidence` (`backend/domain/evidence/models.py`).
4. **Nienegocjowalna weryfikacja**: Metoda `_verify_quote_in_text(quote, document.page_text)` pozostaje w 100% aktywna i nienaruszona jako niezależny filtr uczciwości.
5. **Obsługa krawędziowa i telemetria**: Gdy strona zawiera mniej niż 2 zdania, następuje bezpieczny fallback do ścieżki dosłownej (`legacy_verbatim`). Jeśli model wskaże więcej niż 3 zdania lub niepoprawny indeks, dowód jest odrzucany z odpowiednim licznikiem telemetrii (`web_too_many_sentences`, `web_invalid_sentence_index`).

---

## DEC-039 — Automatyczne włączanie w pełni udokumentowanych przesłanek sieciowych do obliczeń

**Date:** 2026-09-18
**Status:** ACTIVE

**Kontekst:**
W wersjach V11–V15 wszystkie przesłanki sieciowe (`provenance == "web_sourced"`) otrzymywały domyślnie `is_accepted = False` (zgodnie z wcześniejszym DEC-032 / DEC-035). Skutkowało to tym, że nawet po pomyślnym pobraniu stron i zweryfikowaniu cytatów ze źródeł, liczba aktywnych przesłanek w biegu silnika wynosiła zero (`n_active_premises = 0`), a obliczany rozkład scenariuszy pozostawał sztucznie jednostajny (np. 33,3% / 33,3% / 33,3%), dopóki użytkownik nie kliknął akceptacji w UI. Powodowało to paraliż dowodowy w API i brak realnego wpływu zebranych faktów na wynik.

**Decyzja:**
1. **Definicja przesłanki udokumentowanej**: Przesłanka sieciowa jest uznawana za w pełni udokumentowaną i otrzymuje automatycznie status `is_accepted = True` wtedy i tylko wtedy, gdy spełnia łącznie 5 rygorystycznych warunków:
   - `provenance == "web_sourced"`
   - Posiada niepusty, dosłowny cytat zweryfikowany w tekście dokumentu przez `_verify_quote_in_text`.
   - Posiada określone przedziały znakowe w tekście źródłowym (`char_start is not None` oraz `char_end is not None`).
   - Posiada poprawny adres źródłowy (`source_url` zaczynający się od `http`).
   - Posiada deterministycznie wyliczoną wagę dowodową $W > 0.0$ (`WeightBreakdown` wg DEC-037).
2. **Odrzucenie nieudokumentowanych**: Jeśli którykolwiek z 5 warunków nie jest spełniony, przesłanka zachowuje `is_accepted = False`, a powód odrzucenia jest odnotowywany w opisie i liczniku telemetrii.
3. **Uzasadnienie wpływu**: Wpływ przesłanki na scenariusze (`impact_on_scenarios`) musi być powiązany z konkretnym indeksem zdania w dokumencie (`impact_justification`), co zapobiega zmyślaniu kierunku asocjacji przez model.
4. **Telemetria**: Dodano metryki telemetrii `n_documented_premises` oraz `n_premises_rejected_as_undocumented`. Gdy w pełni udokumentowane przesłanki są obecne, wchodzą one bezpośrednio do agregacji probabilistycznej `compute_scenario_distribution`, dając `n_active_premises >= 1` i niejednostajny, ugruntowany dowodowo rozkład prawdopodobieństw.

---

## DEC-040 — Rozdział wpływu udokumentowanego od proponowanego i zakaz kształtowania rozkładu przez model_unverified

**Date:** 2026-09-18
**Status:** ACTIVE

**Kontekst:**
W audycie Promptu V17 i V18 stwierdzono, że we wszystkich wcześniejszych biegach silnika `impacts_proposed = 0` z powodu braku przekazywania listy `candidate_scenarios` do ekstraktora (`EvidenceExtractor`). W konsekwencji ekstraktor nie generował liczb wpływu ze zweryfikowanym cytatem, a jedyne liczby wpływu pochodziły z drugiego wywołania modelu (dekompozytora), które nie posiadało uzasadnienia w konkretnym zdaniu dokumentu ani weryfikacji przez `_verify_quote_in_text`. Mimo to, po wdrożeniu DEC-039 liczby te wchodziły do obliczeń softmax, kształtując asymetrię rozkładu na podstawie niezweryfikowanych domysłów modelu.

**Decyzja:**
1. **Dekompozycja wstępna przed pobieraniem stron (V18-1)**: Silnik generuje scenariusze kandydujące (`candidate_scenarios`) bezpośrednio z pytania użytkownika przed pobraniem stron, a następnie przekazuje je do `extractor.extract_parameter_evidences`. Ekstraktor wymaga wskazania `sentence_index` uzasadniającego wpływ na poszczególne scenariusze i weryfikuje cytat zdania funkcją `_verify_quote_in_text`.
2. **Kategoryczny zakaz kształtowania rozkładu przez niezweryfikowany wpływ (V18-2)**:
   - Wpływy pochodzące z propozycji modelu bez zweryfikowanego zdania z dokumentu otrzymują status `impact_source = "model_unverified"`.
   - W funkcji `compute_scenario_distribution` (`backend/domain/scenario_weighting.py`) wpływy z `impact_source == "model_unverified"` są traktowane jako `0.0` (nie wchodzą do sumy `support_scores`), dopóki użytkownik jawnie nie zatwierdzi ich w interfejsie (`impact_source = "user_defined"`).
   - Wpływy ze zweryfikowanym zdaniem uzasadniającym otrzymują status `impact_source = "documented"` i wchodzą do rozkładu automatycznie.
3. **Płaski rozkład jako prawidłowa odpowiedź**: Gdy brak udokumentowanych wpływów (wszystkie aktywne przesłanki mają wpływ zerowy lub niezweryfikowany), rozkład prawdopodobieństw pozostaje ściśle płaski (jednostajny, $1/k$). Niedopuszczalne jest wymuszanie asymetrii na niezweryfikowanych liczbach.
4. **Zdanie pod liczbą w interfejsie (V18-3)**: W UI (`frontend/src/components/RecommendationView.tsx`) dosłowne zdanie uzasadniające wyświetlane jest wyłącznie dla `impact_source == "documented"`. Dla `model_unverified` interfejs wyświetla jawne ostrzeżenie: *„ocena modelu, bez pokrycia w dokumencie”* oraz przycisk umożliwiający decydentowi świadome zatwierdzenie propozycji.
5. **Telemetria `impact_documented_share` (V18-2)**: Do telemetrii prognozy dodano wskaźnik procentowego udziału wpływu udokumentowanego w łącznym module wpływów aktywnych przesłanek:
   $$\text{impact\_documented\_share} = \frac{\sum_{\text{doc}} |I(s, p)|}{\sum_{\text{total}} |I(s, p)|} \times 100\%$$

---

## DEC-041: Rozdział słowników wpływów, per-scenariuszowy impact_source i równoległa dekompozycja zapytania z wyszukiwaniem

**Data:** 2026-09-18  
**Autor:** Antigravity (Prompt V19, zatwierdzone przez Jana Domaniewskiego)  
**Kontekst:** Weryfikacja audytu V18 wykazała usterkę poprawności w `backend/domain/cognitive/scenario_decomposer.py`: ugruntowany wpływ i propozycja modelu trafiały do tego samego słownika `impact_on_scenarios`. Ponadto telemetria nie wyjaśniała przyczyny braku propozycji (`impacts_proposed == 0`), a sekwencyjne wykonywanie dekompozycji i wyszukiwania niepotrzebnie wydłużało czas odpowiedzi.

**Decyzja:**
1. **Rozdział słowników `impact_on_scenarios` i `impact_proposed` (V19-1)**:
   - Słownik `impact_on_scenarios: dict[str, float]` w `EvidencePremise` przechowuje **wyłącznie** wpływy ugruntowane w zweryfikowanych zdaniach z dokumentów (`ev.impact_on_scenarios`).
   - Nowe pole `impact_proposed: dict[str, float]` przechowuje propozycje analityczne dekomponującego modelu językowego. Nigdy nie są one automatycznie scalane z ugruntowanymi wpływami i nigdy nie nadpisują zweryfikowanych wartości.
2. **Słownik `impact_source` per scenariusz (V19-1)**:
   - Pole `impact_source` stało się słownikiem `ImpactSourceDict` mapującym `scenario_id -> 'documented' | 'model_unverified' | 'user_defined'`.
   - Klasa `ImpactSourceDict` zachowuje kompatybilność wsteczną w porównaniach równościowych ze stringami (`impact_source == 'documented'`), a metoda pomocnicza `get_impact_source(scenario_id: str) -> str` zwraca precyzyjne źródło dla zadanego scenariusza.
3. **Izolacja matematyczna w softmax (V19-1)**:
   - Funkcja `compute_scenario_distribution` (`backend/domain/scenario_weighting.py`) czyta wyłącznie `impact_on_scenarios`.
   - Propozycje z `impact_proposed` nie mają żadnego wpływu na rozkład prawdopodobieństw, dopóki decydent nie dokona jawnego zatwierdzenia propozycji (co przenosi wpływ do `impact_on_scenarios` ze statusem `impact_source = 'user_defined'`).
4. **Telemetria `impacts_not_proposed_reason` (V19-2)**:
   - Gdy `impacts_proposed == 0`, silnik raportuje jedną z czterech standaryzowanych przyczyn: `"brak candidate_scenarios"`, `"model zwrócił pustą tablicę impacts"`, `"odpowiedź modelu nie przeszła walidacji schematu"`, `"przekroczony budżet"`.
5. **Współbieżność Etapu 1 i 2 (V19-3)**:
   - Dekompozycja zapytania na scenariusze kandydujące (Etap 1) oraz wyszukiwanie w sieci (Etap 2) wykonywane są równolegle przez `asyncio.gather`, skracając czas odpowiedzi na produkcji do mediany 34,11 s bez obniżania limitów czasu ani liczby stron.

---

## DEC-042: Ujednolicony rurociąg dowodowy z sieci dla klasy DESIGN, eliminacja zmyślonych liczb i Pareto na udokumentowanym podzbiorze

**Data:** 2026-09-19  
**Autor:** Antigravity (Prompt V21, zatwierdzone przez Jana Domaniewskiego)  
**Kontekst:** W pytaniach systemowych i architektonicznych klasy DESIGN (np. *„Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?”*) użytkownik otrzymywał pustą macierz do ręcznego wypełnienia, a w silniku istniały sztuczne wartości (`7.0`/`3.0`, `provenance="assumed"`). Reguła naczelna projektu wymaga, by dane były czerpane z sieci i weryfikowane u źródła, bez zmyślania ocen przez model.

**Decyzja:**
1. **Podpięcie klasy DESIGN pod istniejący rurociąg dowodowy (V21-1)**:
   - Zamiast budować oddzielny moduł, faza intake klasy DESIGN została połączona z istniejącym, przetestowanym rurociągiem: wyszukiwanie w sieci, ochrona SSRF w `SafeWebFetcher` oraz ekstrakcja z dosłowną weryfikacją cytatów w tekście źródłowym (`EvidenceExtractor._verify_quote_in_text`).
2. **Kategoryczny zakaz zmyślania liczb przez model (zero assumed numbers)**:
   - Całkowicie wyeliminowano sztuczne wartości domyślne (np. 7.0/3.0) oraz status `provenance="assumed"`.
   - Komórka macierzy ocen (`score_matrix`), dla której w dokumentach sieciowych nie znaleziono zweryfikowanej wartości liczbowej, pozostaje pusta (`value=None`, `provenance="unverified"`). Wartość może pochodzić wyłącznie ze zweryfikowanego źródła (`web_sourced`) albo z bezpośredniego wpisu decydenta (`user_supplied`).
3. **Ocena Pareto na udokumentowanym podzbiorze kryteriów (V21-2)**:
   - Puste komórki nie są zastępowane zerami ani średnimi (co zafałszowałoby relacje dominacji).
   - Kryteria, dla których nie ma ani jednej udokumentowanej wartości w żadnej opcji, są wykluczane z kalkulacji Pareto i jawnie raportowane decydentowi w liście `design_criteria_excluded`.
   - Obliczanie frontu Pareto (`compute_design_pareto_frontier`) odbywa się wyłącznie na aktywnych kryteriach posiadających ugruntowane dane.
4. **Uczciwy fallback przy braku danych (V21-3)**:
   - Jeżeli macierz nie zawiera żadnych udokumentowanych komórek (`documented_cells == 0`), silnik nie wyznacza pozornego zwycięzcy, lecz zwraca `insufficient_data=True` z jasnym komunikatem: *„Nie znalazłem wystarczających danych, żeby porównać te warianty.”*
5. **Telemetria i interakcja w interfejsie (V21-4)**:
   - Dodano pola telemetrii: `design_matrix_documented_cells`, `design_matrix_empty_cells`, `design_criteria_excluded`, `insufficient_data`.
   - W interfejsie `frontend/src/components/DesignWorkspace.tsx` usunięto jednostkowe przyciski „oznacz jako założenie”, dodano zbiorczy przycisk `🌐 Dociągnij dane z sieci` (ze ścisłym budżetem do 6 brakujących komórek per kliknięcie), umożliwiono ręczną edycję komórek decydentowi (`user_supplied`) oraz odblokowano syntezę Pareto natychmiast, gdy decydent lub sieć udokumentuje chociaż jedno kryterium.





