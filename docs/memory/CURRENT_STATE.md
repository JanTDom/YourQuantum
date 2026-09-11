# YourQuantum — CURRENT STATE
_Last updated: 2026-09-09_

## Status: POST-AUDIT REBUILD COMPLETE & VERIFIED

All 20 external audit deficiencies have been addressed, refactored, and verified with a regression suite. The application has been transformed into a calm human decision studio with rigorous mathematical execution, independent constraint verification, and zero background task leaks.

---

### What works (empirically verified by unit, integration, and browser tests)

1. **Human Decision Case & Formalizer (`backend/domain/decision_case.py`, `formalizer.py`, `llm_advisor.py`)**:
   - Two-tier decoupled architecture: `DecisionCase` (human dilemma, explicit facts, candidate options, criteria, unknowns, trade-offs) vs `ProblemIR` (computational AST).
   - Zero hallucination: Never fabricates projects or fake profits (e.g. 12, 18, 9, 15).
   - Accurate inequalities: "maksymalnie K" translates to $\le K$ (inequality, never equality).
   - Life dilemmas ("czy zmienić pracę, czy zostać"): extracts realistic options and generates clarification questions instead of synthesizing fake $x_0, x_1, x_2$.
   - Max-Cut: Quadratic cut formulation $\sum_{(u,v)} (x_u + x_v - 2 x_u x_v)$, not a linear sum.

2. **Server Publication Gate & Explicit Approval (`backend/worker/runner.py`, `backend/api/routes.py`, `backend/db/models.py`)**:
   - `ProblemRecord` defaults to `approved=False`. Solving unapproved problems is strictly rejected (HTTP 422).
   - Dedicated endpoint `POST /api/v1/problems/{id}/approve` records explicit human sign-off.
   - `JobRecord` tracks `publication_status`:
     * `PUBLISHED_VERIFIED` only when independent verifier returns `Verdict.PASS`.
     * `REJECTED_UNVERIFIED` on verification failure or non-finite math.
     * `UNVERIFIED` otherwise.
   - Elimination of all false "100% gwarancja" claims.

3. **Rigorous Solvers & Numerical Safeguards**:
   - `ComputeBudget`: Pydantic bounds enforce $(0, 600]$\,s wall time, $(0, 4096]$\,MB memory, $(0, 10000]$ shots.
   - `ExpressionEvaluator`: NaN and infinity detection raises `EvaluationError`.
   - `IndependentVerifier`: Re-evaluates objective and all constraints from scratch; rejects non-finite math.
   - `QUBOEncoder`: Fixed quadratic coefficient deduplication ($x_i x_j$ no longer doubled); fixed polynomial expansion with constants; inequality bounds preserved.
   - `QAOAAdapter`: Tracks best-seen parameters during optimization, recomputes true objective from original ProblemIR, decodes and ranks feasible bitstrings.
   - `CPSATAdapter`: Rational scaling factor up to $10^4$ eliminates blind int-rounding errors; raises `SolverModelError` without silent `except Exception: pass`.

4. **Modular Frontend Rebuild (`frontend/src/`)**:
   - Replaced monolithic `App.tsx` with modular components:
     * `tokens.css`: Porcelain & Slate calm studio design system. High contrast (#0f172a / #334155), WCAG 2.2 AA.
     * `AppHeader.tsx`: Responsive navigation with clean sentence-case branding.
     * `ConversationPanel.tsx`: Prominent input card with everyday situations.
     * `CaseWorkspace.tsx`: Structured human dilemma view (options, unknowns with interactive answers, trade-offs).
     * `ModelApprovalGate.tsx`: Transparent pre-compute verification gate with solver choice.
     * `RecommendationView.tsx`: 5 core human sections (1. Co z tego wynika dla Ciebie, 2. Kluczowe powody, 3. Kompromisy i koszty, 4. Co-jeśli, 5. Następny krok).
     * `EvidenceDrawer.tsx`: Collapsible accordion with solver metrics and independent audit report.
   - Vite build: **0 errors, 0 TypeScript warnings**.

5. **Intelligent Gemini Intake & Clarification Loop (`backend/domain/llm_advisor.py`, `backend/domain/formalizer.py`)**:
   - Integrated Gemini 3.6 Flash for natural language dilemma intake and clarification interview.
   - Extracts real decision options (e.g. "Pierwsze wydawnictwo", "Drugie wydawnictwo") instead of dummy $x_0, x_1, x_2$.
   - Formulates 2-3 deep, non-obvious clarification questions addressing missing information, trade-offs, and board/budget support.
   - Interactive answering in `CaseWorkspace`: user answers are compiled into `DecisionCase` and re-formalized into calibrated objective coefficients.
   - Elimination of empty option state and automatic normalization of option labels in `RecommendationView`.

6. **Quantum Simulation Engine Upgrade (`backend/solvers/quantum/qaoa.py`, `frontend/src/components/EvidenceDrawer.tsx`)**:
   - **TQA (Trotterized Quantum Annealing) Adiabatic Ramp Initialization**: Replaced blind random initialization with adiabatic physics ramp schedule ($\gamma_l, \beta_l$), dramatically improving convergence.
   - **Multi-Start Variational Pre-screening**: Evaluates candidate trajectories (adiabatic, perturbed, phase-shifted) before COBYLA convergence.
   - **Gate Physics Breakdown**: Explicit tracking of 2-qubit entangling gates (CNOT), single-qubit rotations ($RZ, RX, H$), and circuit depth.
   - **Quantum Amplification Factor ($A_Q$)**: Computes ground state measurement probability vs classical uniform random guess ($1/2^n$).
   - **Visual Quantum Physics in Evidence Drawer**: Displays circuit depth, entangling gates, quantum amplification badge, and proportional state measurement distribution bars.

7. **Ultra-Premium Domain-Agnostic Decision Studio (`backend/`, `frontend/src/`)**:
   - **Domain-Agnostic Intelligence**: Supports any human, business, financial, or life dilemma (housing, career, investments, education, relocations), without being constrained to job dilemmas.
   - **Layperson-Friendly Priority Pills (Tokens)**: Replaced raw numerical sliders with intuitive, domain-specific priority chips with emojis (e.g. `[⏱️ Oszczędność czasu]`, `[🔄 Elastyczność i swoboda]`, `[🏡 Większy metraż]`, `[💰 Niższy koszt]`), plus an interactive `[+ Wpisz własny priorytet]` prompt. The solver weights these tokens with top priority.
   - **Dynamic Option Management**: Interactive `+ Dodaj kolejną opcję / alternatywę` directly in the case workspace, allowing users to test third paths or "neither" options.
   - **Bilans Decyzyjny (Zwycięzca vs Alternatywa)**: High-contrast 2-column comparative section presenting exactly why the winning option prevailed over the runner-up based on user priorities and mathematical optimality.
   - **Punkt Zwrotny do Negocjacji (Break-Even Box)**: Actionable analysis in plain Polish explaining what specific parameters (salary, remote work, price) would need to shift for the losing option to become optimal.
   - **1-Click Executive Print Report (A4 / PDF)**: Dedicated `@media print` stylesheet with official verification seal, dilemma overview, timestamp, and audit trail, stripping all dark web chrome for a crisp printable document.

8. **Production Cloud Deployment & Custom Domain**:
   - Deployed on Vercel (`macieto/yourquantum`) with Supabase PostgreSQL integration (`aws-1-eu-west-1.pooler.supabase.com:6543/postgres`).
   - Configured `statement_cache_size=0` for asyncpg to resolve PgBouncer transaction pooling collisions.
   - Connected custom domain `https://yourquantum.pl` and `https://www.yourquantum.pl` with live A records (`76.76.21.21`) configured on nazwa.pl DNS.
   - SSL certificates active, HTTP/2 200 on all endpoints.

9. **Dynamic Auto-Updating Layperson Help System (`backend/api/help_service.py`, `frontend/src/components/HelpCenterModal.tsx`)**:
   - Dynamic engine introspection via `GET /api/v1/help` and `GET /api/v1/help/snapshot`.
   - Automatically reflects registered solvers (`SOLVER_REGISTRY`), version, and supported dilemma domains without hardcoding.
   - 5 structured tabs: Przewodnik krok po kroku, Gotowe przykłady z życia (one-click prefill), Pytania i odpowiedzi (FAQ), Słowniczek pojęć, Stan Silnika Live.
   - Context-aware stage awareness (Intake -> Workspace -> Approval -> Recommendation).

10. **3D Interactive Cognitive Brain (`frontend/src/components/EngineBrain3D.tsx`, `frontend/src/components/BrainModal.tsx`)**:
    - Built with Three.js (WebGL hardware-accelerated 60 FPS).
    - Features 24-node cognitive hypergraph with pulsing icosahedrons and glowing additive bezier synapses.
    - Continuous undulating QUBO / Hamiltonian energy manifold with central gravity well (Global Optimum ground state).
    - Triple concentric phase interference gyroscope rings.
    - 360° mouse drag orbit controls and scroll zoom.
    - Dynamic layer switcher (Wszystko / Topologia / Krajobraz QUBO / Faza i Fale) and interactive shockwave trigger ("Wyślij impuls kwantowy ⚡").
    - Strict know-how protection: communicates scientific rigor via abstract topological and physical metrics (phase coherence, synergy vector, boundary margins) with zero proprietary code or formula leaks.

11. **Empirical Test Suite**:
    - Pytest suite: **54/54 PASS** across domain, verifier, quantum solvers, help service, and formalizer tests.
    - TypeScript build: **0 errors, 0 warnings** (`tsc -b && vite build`).
    - Synced to GitHub repository `https://github.com/JanTDom/YourQuantum`.

---

## Next Step

Gather early user feedback on live domain `yourquantum.pl` and test additional edge-case life dilemmas.

