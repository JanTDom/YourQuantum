# ARCHITECTURE.md — YourQuantum

**Status:** PLANNED · **Last updated:** 2026-09-09

---

## System Overview

YourQuantum is organised around five layers with strict directional dependencies
(outer layers depend on inner; inner layers do not depend on outer).

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND  (problem intake, result presentation)         │
├─────────────────────────────────────────────────────────┤
│  TRANSPORT  (API gateway, auth, rate limiting)           │
├─────────────────────────────────────────────────────────┤
│  APPLICATION  (use-cases: formalise, route, verify)      │
├─────────────────────────────────────────────────────────┤
│  DOMAIN  (problem IR, solvers, verifier, router)         │
├─────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE  (DB, queue, QPU adapters, storage)      │
└─────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### LLM Layer (Interpreter & Assistant)
- Translates user natural language into a structured Problem IR draft.
- Asks clarifying questions when the problem is under-specified.
- Does NOT produce solver results. Does NOT make algorithmic decisions alone.
- Its output is validated by the Formaliser before being used as a model.

### Problem IR (Versioned Contract)
- The canonical representation of a problem instance.
- Contains: variables, domains, data, objectives, constraints, assumptions,
  units, provenance, schema version.
- Immutable once approved; changes increment the version.
- See `docs/PROBLEM_IR.md` for full schema.

### Router & Decomposer
- Selects methods based on problem structure, budget, and capability registry.
- Decomposes large problems into tractable sub-problems.
- Assigns compute budgets and enforces stopping conditions.
- Does NOT call a result "globally optimal" if global search was not performed.

### Classical Solver Layer
- Pluggable adapters for: CP-SAT, OR-Tools, PuLP/HiGHS, SymPy, SciPy,
  Gurobi (licensed), Z3, and others.
- Each adapter exposes: `can_handle(problem_ir) → bool`,
  `solve(problem_ir, budget) → result`.
- See `docs/` + `yq-classical-solvers` skill.

### Quantum Core
- Real quantum algorithm module. See `docs/QUANTUM_CORE.md`.
- Components: encoder, cost operator builder, circuit composer,
  simulator (ideal + noise), QPU adapter, decoder, sampler.
- Execution path: problem IR → QUBO/Ising → circuit → execution →
  samples → decoded candidates → verifier.

### Verifier (Independent)
- Re-evaluates every candidate returned by any solver.
- Checks all constraints against the Problem IR.
- Computes objective value independently.
- Produces verification report: PASS / FAIL / PARTIAL + reasons.
- See `docs/VERIFICATION.md`.

### Worker & Queue
- Isolates computation from the API process.
- Enforces time, memory, and cost limits per job.
- Supports retry with backoff and dead-letter queue.
- Does NOT execute arbitrary code from user prompts.

### Frontend
- Problem-centric: the user sees their problem and result, not circuit diagrams
  unless explicitly requested.
- Three mandatory UI states: loading, empty/waiting, error.
- Full keyboard accessibility; WCAG 2.2 AA baseline.

---

## Capability Registry

All available solver and quantum capabilities are registered at startup.
The router queries the registry; it does not hard-code method selection.
Capability status is reflected in `docs/CAPABILITIES.md`.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|---------|
| Type safety | Strict TypeScript / Python type annotations throughout |
| Validation | Zod/Pydantic schemas at every external boundary |
| Observability | Structured JSON logs, OpenTelemetry traces, correlation IDs |
| Secrets | Environment variables / secret manager; never in code or docs |
| Testing | Unit (domain), integration (adapters), E2E (full user path) |

---

## Architecture Decisions

See `docs/memory/DECISIONS.md` for rationale behind each major choice.
