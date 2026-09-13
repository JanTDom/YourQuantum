# CAPABILITIES.md — Feature Registry

**Status:** ACTIVE REGISTRY · **Last updated:** 2026-09-13 (Phase I Verification)
**Dynamic API Endpoint:** `GET /api/v1/capabilities` (powered by `backend/domain/capabilities.py`)

Feature status lifecycle (AGENTS.md §7 — Evidence Rule):
- **PLANNED** — decided, not yet started.
- **IMPLEMENTED** — code written, awaiting test verification.
- **TESTED** — verified by automated tests in CI/pytest suite and E2E Playwright.
- **DEPLOYED** — running in production environment.

---

## Core Pipeline

| Feature | Status | Test Reference / Notes |
|---------|--------|-------------------------|
| Problem intake (Single Intake Pathway `/cognitive/intake`) | **TESTED** | `tests/test_phase_e_cognitive.py` · LLM + Active Inference fallback |
| Problem IR schema v0.3 (5 problem classes) | **TESTED** | `tests/test_phase_d_problem_classes.py` · Pydantic validation, provenance tracking |
| IR user approval gate (Decision Matrix + Provenance Gate) | **TESTED** | `tests/test_phase_g_ui_and_copy.py` · Deliberate human approval blocks on `BLOCKS_SOLVING` |
| Compute budget enforcement (time, memory, shots) | **TESTED** | `tests/test_universal_api.py` · Time & memory limits |
| Problem decomposition (Benders) | **TESTED** | `tests/test_hybrid_benders.py` · Master & Subproblem cuts |
| Dynamic method router (Benchmark-backed routing) | **TESTED** | `tests/test_phase_f_quantum_honesty.py` · Routes to best solver based on empirical evidence |

---

## Problem Classes Taxonomy (Phase D)

| Problem Class | Status | Test Reference / Notes |
|---------------|--------|-------------------------|
| `CHOICE` (Multi-criteria Discrete Variant Selection) | **TESTED** | `tests/test_phase_d_problem_classes.py` · CP-SAT, analytical break-even (B1) |
| `ALLOCATION` (Knapsack / Resource Partitioning) | **TESTED** | `tests/test_phase_d_problem_classes.py` · CP-SAT discrete optimization |
| `DESIGN` (Multi-Lever Architectural Synthesis) | **TESTED** | `tests/test_phase_d_problem_classes.py`, `tests/test_phase_g_ui_and_copy.py` · Pareto frontier, lever ranking |
| `PARAMETER` (Continuous / Hybrid Parameter Tuning) | **TESTED** | `tests/test_phase_d_problem_classes.py` · HiGHS linear/continuous solver adapter |
| `NOT_COMPUTABLE` (Ethical / Subjective Reframing Gate) | **TESTED** | `tests/test_phase_d_problem_classes.py`, `tests/test_phase_e_cognitive.py` · Explanatory reframing advice |

---

## Evidence & Web Research Layer (Phase C & H)

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| Evidence Models & Provenance (`user_supplied`, `web_sourced`, `derived`, `assumed`) | **TESTED** | `tests/test_phase_c_evidence.py` · Full provenance schema |
| SafeWebFetcher (SSRF protection, size bounds, timeout) | **TESTED** | `tests/test_phase_h_security.py` · Loopback, link-local, cloud metadata blocked |
| EvidenceExtractor (Boundary sanitization, indirect injection defense) | **TESTED** | `tests/test_phase_h_security.py` · Malicious injection payloads filtered |
| Multi-source Consensus & Conflict Detection | **TESTED** | `tests/test_phase_c_evidence.py` · Discrepancy flagging |
| Institutional Evidence Sources (GUS, NFZ, WHO, OECD) | **TESTED** | `tests/test_phase_c_evidence.py`, `tests/test_phase_g_ui_and_copy.py` |

---

## Classical Solvers

| Solver / Capability | Status | Test Reference / Notes |
|--------------------|--------|-------------------------|
| CP-SAT (Google OR-Tools) | **TESTED** | `tests/test_audit_regressions.py` · Discrete MIP |
| HiGHS Continuous / Linear Adapter (`ContinuousSolverAdapter`) | **TESTED** | `tests/test_phase_d_problem_classes.py` · Continuous optimization |
| HiGHS LP Dual Relaxation & Certificate | **TESTED** | `tests/test_dual_certificate.py` · Dual bounds & optimality gap |
| Exhaustive Enumeration ($n \le 22$) | **TESTED** | `tests/test_audit_regressions.py` · Small state exact verification |
| Z3 SMT solver | PLANNED | Symbolic verification |
| Gurobi adapter | PLANNED | Commercial solver adapter |

---

## Quantum Core (Phase F & Honest Physics)

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| QUBO encoder ($Q$-matrix) | **TESTED** | `tests/test_qubo.py` · Exact penalty calibration |
| Ising encoder ($h, J$ spins) | **TESTED** | `tests/test_qubo.py` · Spin mapping & energy preservation |
| Multi-lever DESIGN QUBO Encoding ($H_{\text{cost}} + H_{\text{one-hot}} + H_{\text{excl}}$) | **TESTED** | `tests/test_phase_f_quantum_honesty.py` · Feasible ground state energy gap |
| QAOA ansatz (Qiskit Aer) | **TESTED** | `tests/test_qaoa.py` · Parameterized circuit simulation |
| Noise Model Simulation (Depolarizing, Amplitude Damping) | **TESTED** | `tests/test_phase_f_quantum_honesty.py` · AerSimulator with noise models |
| Warm-Started QAOA | **TESTED** | `tests/test_warm_start_qaoa.py` · LP relaxation continuous seeding |
| Parameter optimisers (COBYLA/Nelder-Mead) | **TESTED** | `tests/test_qaoa.py` · Multi-start optimization |
| Quantum Execution Evidence Validator | **TESTED** | `tests/test_phase_f_quantum_honesty.py` · Circuit depth, gate counts, strict gate against fake results |
| Physical QPU Backends (IBM Quantum / AWS Braket) | **IMPLEMENTED (Stub)** | `backend/domain/qpu_adapter.py` · Honest stub with credentials requirement, no fake QPU claims |

---

## Verification & Robustness

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| Independent constraint re-evaluation | **TESTED** | `tests/test_verifier.py` · Zero solver trust |
| Objective value recomputation | **TESTED** | `tests/test_verifier.py` · AST expression evaluator |
| Feasibility & domain violation check | **TESTED** | `tests/test_verifier.py` · Bounds & integrality |
| Dual bound & optimality certificate | **TESTED** | `tests/test_dual_certificate.py` · Non-bypass verification |
| Sensitivity analysis (elasticity, stress test) | **TESTED** | `tests/test_sensitivity.py` · Parameter shock |
| Cryptographic Audit Passport (SHA-256) | **TESTED** | `tests/test_verifier.py`, `frontend/e2e/v2-honest-engine.spec.ts` |
| Analytical Break-Even Point (DEC-014 / B1) | **TESTED** | `tests/test_phase_b_matrix.py`, `tests/test_phase_g_ui_and_copy.py` |

---

## Cognitive Subsystem (Phase E)

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| Active Inference perception loop & Re-approval Gate | **TESTED** | `tests/test_phase_e_cognitive.py` · Self-correction with mandatory re-approval |
| Global Workspace Working Memory (Session SQLite) | **TESTED** | `tests/test_phase_e_cognitive.py` · Session persistence, cleanup, GDPR deletion |
| Metabolic Energy Budget Tracker | **TESTED** | `tests/test_phase_e_cognitive.py` · Loop guard and exhaustion recommendations |
| Episodic Memory with Tenant Isolation & Consent Gate | **TESTED** | `tests/test_phase_e_cognitive.py`, `tests/test_phase_h_security.py` · Strictly consent-gated |
| Cognitive Telemetry Inspector Endpoint | **TESTED** | `tests/test_phase_e_cognitive.py` · `/api/v1/cognitive/inspector` |

---

## Security & Rate Limiting (Phase H)

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| Sliding Window Rate Limiting (15 req/min anon, 150 auth) | **TESTED** | `tests/test_phase_h_security.py` · In-memory sliding window with 429 Retry-After |
| Daily Client Quotas & Server Circuit Breaker | **TESTED** | `tests/test_phase_h_security.py` · Denial-of-wallet protection (600 global/day limit) |
| HMAC-SHA256 Expiring Session Tokens (`yq_sess_...`) | **TESTED** | `tests/test_phase_h_security.py` · Ephemeral anonymous session tokens |
| SSRF Defense (Loopback, Link-Local, RFC 1918, Cloud Metadata) | **TESTED** | `tests/test_phase_h_security.py` · DNS resolution and IP validation |
| Indirect Prompt Injection Defense (Delimiter escaping, heuristics) | **TESTED** | `tests/test_phase_h_security.py` · Malicious injection payload rejection |

---

## Frontend / UI / UX (Phase G & I)

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| Landing Page with Honest Telemetry & Disclaimers (G1) | **TESTED** | `frontend/e2e/v2-honest-engine.spec.ts` · CPU simulation disclaimer |
| Interactive Problem Class Selector (5 classes) (G2) | **TESTED** | `tests/test_phase_g_ui_and_copy.py` |
| Model Approval Gate with Decision Matrix & Provenance (G3) | **TESTED** | `frontend/e2e/v2-honest-engine.spec.ts` |
| Recommendation View (Dual Mode: DESIGN & CHOICE) (G4) | **TESTED** | `frontend/e2e/v2-honest-engine.spec.ts` · 5 DEC-014 sections, Pareto chart, sensitivity ranking |
| Dynamic Help Center introspecting capabilities & benchmarks (G6) | **TESTED** | `tests/test_phase_g_ui_and_copy.py` · `/api/v1/help/topics` |
| WCAG 2.2 AA Accessibility & Polish (G5) | **TESTED** | Contrast tokens, focus rings, semantic HTML5 |
