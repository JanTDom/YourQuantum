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
The Antigravity customisation documentation (`agy-customizations/docs/rules.md`,
verified 2026-09-09) states that `AGENTS.md` and `GEMINI.md` are always active
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
The external audit archive is assembled via an isolated staging pipeline excluding all vendor artifacts (`node_modules`, `.venv`), build directories (`dist`, `build`), cache directories (`__pycache__`, `.pytest_cache`), local runtime databases (`*.db`), and secret configurations. The package is accompanied by `AUDIT_README.md`, `README.md`, `requirements.txt`, and `.env.example`.

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
Implement a WebGL 3D interactive cognitive brain (`EngineBrain3D.tsx`, `BrainModal.tsx`) using Three.js with three synchronized layers:
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
- `Dockerfile` w repozytorium definiuje oficjalny kontener obliczeniowy.
- Środowisko deweloperskie i testowe lokalnie (`pytest`) uruchamia ten sam kod bezpośrednio w venv lub kontenerze Docker.




