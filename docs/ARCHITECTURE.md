# ARCHITECTURE.md — YourQuantum

**Status:** IMPLEMENTED & VERIFIED (v2.0) · **Last updated:** 2026-09-13 (Phase I Complete)

---

## System Overview

YourQuantum is organized around strict directional layers with explicit trust boundaries:

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (React 18 / Vite / OKLCH / WCAG 2.2 AA)       │
│  - Problem Intake & Class Taxonomy Selector             │
│  - Case Workspace & Clarification Loop                  │
│  - Model Approval Gate (Decision Matrix & Provenance)   │
│  - Recommendation View (Pareto / Break-Even / Passport) │
├─────────────────────────────────────────────────────────┤
│  TRANSPORT & SECURITY GUARD (FastAPI Gateway)           │
│  - Sliding Window Rate Limiter (15/min anon, 150 auth)  │
│  - Daily Client Quota & Server Circuit Breaker (600/day)│
│  - HMAC-SHA256 Expiring Session Tokens (yq_sess_...)    │
│  - CORS / CSP Headers / SSRF URL Validator              │
├─────────────────────────────────────────────────────────┤
│  COGNITIVE SUBSYSTEM (Active Inference Engine)          │
│  - Single Intake Pathway (/cognitive/intake)            │
│  - Global Workspace Working Memory (Session SQLite)     │
│  - Metabolic Energy Budget Tracker & Loop Guard         │
│  - Tenant-Isolated Episodic Memory (Strict Consent Gate)│
│  - Cognitive Telemetry Inspector                        │
├─────────────────────────────────────────────────────────┤
│  EVIDENCE & WEB RESEARCH LAYER                          │
│  - SafeWebFetcher (SSRF, Link-Local, Cloud Metadata)    │
│  - EvidenceExtractor (Injection Defense & Escaping)     │
│  - Provenance Tracking (user, web, derived, assumed)    │
│  - Multi-source Consensus & Conflict Detection          │
├─────────────────────────────────────────────────────────┤
│  APPLICATION & DOMAIN CORE                              │
│  - Problem IR v0.3 (CHOICE, ALLOCATION, DESIGN, PARAM)  │
│  - Benchmark-Backed Dynamic Router                      │
│  - Publication & Re-approval Gate (Zero Bypass)         │
├─────────────────────────────────────────────────────────┤
│  SOLVER & QUANTUM ENGINE                                │
│  - Classical: Google OR-Tools CP-SAT, SciPy HiGHS       │
│  - Quantum Core: QUBO / Ising / QAOA (Qiskit Aer)       │
│  - Multi-Lever DESIGN QUBO ($H_C + H_{\text{one-hot}}$) │
│  - Noise Model Simulator (Kraus, Depolarizing)          │
│  - Physical QPU Adapter (Stub with Credentials Gate)    │
├─────────────────────────────────────────────────────────┤
│  INDEPENDENT VERIFIER & AUDIT PASSPORT                  │
│  - Zero Solver Trust Constraint Re-evaluation           │
│  - AST Objective Recomputation & Dual Bound Gap         │
│  - Analytical Break-Even Point (DEC-014 / B1)           │
│  - Cryptographic SHA-256 Audit Passport                 │
└─────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### 1. Single Intake Pathway & Cognitive Perception
- Translates natural language queries into a structured `DecisionCase` and `ProblemIR` via `/api/v1/cognitive/intake`.
- Detects the appropriate problem class among the 5 fundamental classes (`CHOICE`, `ALLOCATION`, `DESIGN`, `PARAMETER`, `NOT_COMPUTABLE`).
- When a problem is ethical or uncomputable, returns structured reframing advice rather than attempting ungrounded solving.

### 2. Evidence Layer & Safe Web Research
- Slices external facts through `SafeWebFetcher` with strict SSRF filtering (blocks loopback, private RFC 1918, link-local, and cloud metadata addresses like `169.254.169.254`).
- Sanitizes untrusted web content in `EvidenceExtractor`, escaping prompt injection markers and filtering adversarial instruction sentences.
- Tags every cell in the Decision Matrix with a provenance tag (`user_supplied`, `web_sourced`, `derived`, `assumed`) and a verified source URL and content hash.

### 3. Problem IR v0.3 & Publication Gate
- Versioned, domain-agnostic canonical representation.
- Prevents solving if any `MissingInfo` has `impact: "blocks_solving"`.
- Requires explicit user approval (`approved=True`) via `/api/v1/problems/{id}/approve` before solver execution.

### 4. Dynamic Router & Capability Registry
- Inspects solver capabilities via `backend/domain/capabilities.py`.
- Evaluates empirical benchmark JSON files in `benchmarks/results/` to select the method offering the best solution quality and proof of optimality.
- In discrete problems, prioritizes CP-SAT over quantum simulation because CP-SAT proves global optimality in milliseconds.

### 5. Classical Solvers
- **OR-Tools CP-SAT:** Discrete combinatorial optimization, exact proofs of optimality.
- **SciPy HiGHS:** Linear programming relaxation, continuous optimization (`ContinuousSolverAdapter`), and dual lower bound certificates.

### 6. Quantum Core & Honest Physics
- Real quantum algorithm module following `docs/QUANTUM_CORE.md`.
- Mathematical QUBO and Ising formulation with verified energy gap between feasible configurations and constraint violations.
- Parameterized QAOA execution via Qiskit Aer with noise model options (depolarizing, amplitude damping).
- Strict execution evidence validation: gate counts, circuit depth, evaluation counts. Rejects claimed quantum results lacking evidence.
- Physical QPU adapter stub requiring real hardware credentials and explicitly disclaiming physical quantum execution when simulating on CPU.

### 7. Independent Verifier & Cryptographic Passport
- Evaluates candidate solutions independently against the original Problem IR AST.
- Does not trust `claimed_status` from solvers.
- Calculates analytical break-even point for choice problems.
- Issues a cryptographic SHA-256 audit passport certifying 0 constraint violations.

---

## Security & Operational Boundaries

| Boundary | Enforcement |
|----------|-------------|
| Rate Limiting | In-memory sliding window: 15 req/min anonymous, 150 req/min authenticated |
| Denial-of-Wallet | Daily client quota (60/day anon, 600/day auth) + global circuit breaker (600/day) |
| Session Identity | HMAC-SHA256 expiring session tokens (`yq_sess_<exp>_<hash>_<sig>`) |
| Network SSRF | DNS pre-resolution rejecting private, loopback, and cloud metadata IPs |
| Prompt Injection | Content delimiter escaping, instruction neutralization, regex heuristics |
| Master API Secret | Must be supplied via `YQ_MASTER_API_SECRET` env var; no hardcoded defaults in code |
