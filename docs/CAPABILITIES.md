# CAPABILITIES.md — Feature Registry

**Status:** ACTIVE REGISTRY · **Last updated:** 2026-09-13
**Dynamic API Endpoint:** `GET /api/v1/capabilities` (powered by `backend/domain/capabilities.py`)

Feature status lifecycle (AGENTS.md §7 — Evidence Rule):
- **PLANNED** — decided, not yet started.
- **IMPLEMENTED** — code written, awaiting test verification.
- **TESTED** — verified by automated tests in CI/pytest suite.
- **DEPLOYED** — running in production environment.

---

## Core Pipeline

| Feature | Status | Test Reference / Notes |
|---------|--------|-------------------------|
| Problem intake (natural language) | **TESTED** | `tests/test_formalizer.py` · LLM + cognitive fallback |
| Problem IR schema v0.2 | **TESTED** | `tests/test_problem_ir.py` · Strict Pydantic validation |
| IR user approval gate | **TESTED** | `tests/test_api_and_gate.py` · Deliberate human action |
| Compute budget enforcement | **TESTED** | `tests/test_universal_api.py` · Time & memory limits |
| Problem decomposition (Benders) | **TESTED** | `tests/test_hybrid_benders.py` · Master & Subproblem cuts |
| Dynamic method router | **IMPLEMENTED** | `backend/domain/router.py` (Phase B enhancement) |

---

## Classical Solvers

| Solver / Capability | Status | Test Reference / Notes |
|--------------------|--------|-------------------------|
| CP-SAT (Google OR-Tools) | **TESTED** | `tests/test_audit_regressions.py` · Discrete MIP |
| HiGHS LP Dual Relaxation | **TESTED** | `tests/test_dual_certificate.py` · Dual bounds & gap |
| Exhaustive Enumeration ($n \le 22$) | **TESTED** | `tests/test_audit_regressions.py` · Small state exact |
| Z3 SMT solver | PLANNED | Logical and symbolic problems |
| SciPy continuous optimisers | PLANNED | Continuous non-linear optimisation |
| Gurobi adapter | PLANNED | Commercial solver; optional |

---

## Quantum Core

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| QUBO encoder ($Q$-matrix) | **TESTED** | `tests/test_qubo.py` · Exact penalty calibration |
| Ising encoder ($h, J$ spins) | **TESTED** | `tests/test_qubo.py` · Spin mapping & zero ground check |
| QAOA ansatz (Qiskit Aer) | **TESTED** | `tests/test_qaoa.py` · Parameterized circuit simulation |
| Warm-Started QAOA | **TESTED** | `tests/test_warm_start_qaoa.py` · LP relaxation seeding |
| Parameter optimisers (COBYLA/Nelder-Mead) | **TESTED** | `tests/test_qaoa.py` · Multi-start optimization |
| Gate-level circuit telemetry | **TESTED** | `tests/test_qaoa.py` · Depth, gate counts, evidence |
| Noise model simulator (Kraus) | PLANNED | Phase F implementation |
| Physical QPU backends (IBM/Braket) | PLANNED | Hardware execution path |

---

## Verification & Robustness

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| Independent constraint re-evaluation | **TESTED** | `tests/test_verifier.py` · Zero solver trust |
| Objective value recomputation | **TESTED** | `tests/test_verifier.py` · AST expression evaluator |
| Feasibility & domain violation check | **TESTED** | `tests/test_verifier.py` · Bounds & integrality |
| Dual bound & optimality certificate | **TESTED** | `tests/test_dual_certificate.py` · Non-bypass verification |
| Sensitivity analysis (elasticity, stress test) | **TESTED** | `tests/test_sensitivity.py` · Parameter shock |
| Verification report SHA256 integrity | **TESTED** | `tests/test_verifier.py` · Tamper-proof reports |

---

## Cognitive Subsystem

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| Active Inference perception loop | **TESTED** | `tests/test_audit_regressions.py` · Self-correction |
| Global Workspace Working Memory | **TESTED** | `tests/test_audit_regressions.py` · Attention & hypotheses |
| Episodic Memory with tenant isolation | **TESTED** | `tests/test_audit_regressions.py` · Safe recall & no leak |
| Constraint sanity pre-check | **TESTED** | `tests/test_audit_regressions.py` · Contradiction catches |

---

## Frontend / API / Integrations

| Capability | Status | Test Reference / Notes |
|-----------|--------|-------------------------|
| Problem intake UI | **TESTED** | React frontend + Playwright E2E |
| Model approval gate | **TESTED** | React UI with coefficient inspection |
| Result presentation UI | **TESTED** | RecommendationView with honest copy |
| REST API with JWT/HMAC auth | **TESTED** | `tests/test_universal_api.py` |
| MCP Server (Model Context Protocol) | **TESTED** | `tests/test_mcp_server.py` |
