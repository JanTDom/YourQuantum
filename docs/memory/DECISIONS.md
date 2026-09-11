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

**Rationale:**
Allows non-technical decision-makers to obtain executive-level clarity, practical negotiation leverage, and formal mathematical certitude without needing quantum physics knowledge or mathematical modeling training.


