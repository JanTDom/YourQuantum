# CAPABILITIES.md — Feature Registry

**Status:** PLANNED · **Last updated:** 2026-09-09

Feature status lifecycle:
- **PLANNED** — decided, not yet started.
- **IMPLEMENTED** — code written, not yet tested.
- **TESTED** — automated tests passing.
- **DEPLOYED** — live in production environment.

---

## Core Pipeline

| Feature | Status | Notes |
|---------|--------|-------|
| Problem intake (natural language) | PLANNED | LLM-assisted formalisation |
| Problem IR schema v0 | PLANNED | See PROBLEM_IR.md |
| IR user approval step | PLANNED | Deliberate user action required |
| Method routing engine | PLANNED | Capability-registry-driven |
| Problem decomposition | PLANNED | Sub-problem splitting |
| Compute budget enforcement | PLANNED | Per-job limits |

---

## Classical Solvers

| Solver / Capability | Status | Notes |
|--------------------|--------|-------|
| CP-SAT (OR-Tools) | PLANNED | Constraint satisfaction and optimisation |
| HiGHS / PuLP | PLANNED | Linear and mixed-integer programming |
| Z3 SMT solver | PLANNED | Logical and symbolic problems |
| SciPy optimisers | PLANNED | Continuous optimisation (SLSQP, etc.) |
| SymPy | PLANNED | Symbolic computation |
| Gurobi adapter | PLANNED | Licensed solver; optional |

---

## Quantum Core

| Capability | Status | Notes |
|-----------|--------|-------|
| Complex amplitude state vector | PLANNED | |
| Gate-level circuit composition | PLANNED | |
| Ideal statevector simulator | PLANNED | |
| Noise model simulator | PLANNED | Kraus channels |
| Measurement sampling | PLANNED | Configurable shots |
| QUBO encoder | PLANNED | Problem IR → Q matrix |
| Ising encoder | PLANNED | Problem IR → h, J |
| Cost Hamiltonian builder | PLANNED | |
| QAOA ansatz | PLANNED | |
| VQE ansatz | PLANNED | |
| Variational parameter optimiser | PLANNED | COBYLA, SPSA, Adam |
| QPU adapter interface | PLANNED | Abstract; backends TBD |
| IBM Quantum backend | PLANNED | Requires API key |
| AWS Braket backend | PLANNED | Requires AWS credentials |

---

## Verification

| Capability | Status | Notes |
|-----------|--------|-------|
| Constraint satisfaction check | PLANNED | Independent re-evaluation |
| Objective value recomputation | PLANNED | |
| Feasibility check | PLANNED | |
| Numerical residual computation | PLANNED | |
| Verification report generation | PLANNED | |

---

## Data I/O

| Capability | Status | Notes |
|-----------|--------|-------|
| JSON / CSV import | PLANNED | |
| Schema validation at import | PLANNED | |
| Unit normalisation | PLANNED | |
| Missing data detection | PLANNED | |
| Result export (JSON, CSV) | PLANNED | |

---

## Frontend / API

| Capability | Status | Notes |
|-----------|--------|-------|
| Problem intake UI | PLANNED | |
| IR review and approval UI | PLANNED | |
| Result presentation UI | PLANNED | |
| Verification verdict display | PLANNED | PASS/FAIL/PARTIAL always visible |
| REST API | PLANNED | |
| Authentication | PLANNED | |

---

## Benchmarking

| Capability | Status | Notes |
|-----------|--------|-------|
| Benchmark runner | PLANNED | See BENCHMARK_PROTOCOL.md |
| Result storage and retrieval | PLANNED | |
| Comparison report generation | PLANNED | |
