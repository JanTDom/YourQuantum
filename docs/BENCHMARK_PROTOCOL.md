# BENCHMARK_PROTOCOL.md — Benchmark Protocol

**Status:** PLANNED · **Last updated:** 2026-09-09

---

## Purpose

Benchmarks are the only valid evidence for claims about YourQuantum's
performance relative to alternatives. No performance claim enters product
documentation without a corresponding benchmark result.

---

## Comparison Baselines (required for any quantum claim)

Every benchmark run MUST include ALL of the following baselines:

| Baseline | Description |
|----------|-------------|
| LLM alone | Best LLM answer without tools or computation |
| LLM + tools | LLM with calculator, code interpreter, search |
| Best classical solver | Best known classical method for the problem class |
| YourQuantum without quantum module | Classical path only |
| YourQuantum with quantum module | Full system |

Omitting any baseline invalidates the comparison for that metric.

---

## Shared Problem Set Requirements

- Problems must be sourced from or replicable from published benchmarks
  (TSPLIB, MIPLIB, QPLIB, SATlib, etc.) or from real user problems
  with permission.
- Problem instances must be fixed and versioned before any solver runs.
- No tuning of any system on the benchmark problems before comparison.
- Results must be replicable from the stored problem instances.

---

## Metrics

| Metric | Definition | Unit |
|--------|-----------|------|
| Solution quality | Objective value relative to best known / optimal | % gap |
| Feasibility rate | Fraction of runs producing feasible solutions | % |
| Time to first feasible | Wall time until first feasible candidate | seconds |
| Time to best | Wall time until best found solution | seconds |
| Resource cost | Compute cost (CPU-hours, QPU shots, API cost) | USD or units |
| Verification pass rate | Fraction of candidates passing independent verification | % |
| Quantum module contribution | Quality delta from using the quantum path | Δ% |

---

## Quantum Advantage Criterion

Quantum advantage is claimed ONLY when:

1. The quantum path outperforms the best classical baseline on at least one
   metric, measured on the same problem set with the same resource budget.
2. The result is reproduced on at least 3 independent problem instances.
3. Statistical significance is reported (confidence interval, n runs).
4. The result is recorded in `benchmarks/` with full configuration.

If these conditions are not met, no advantage is claimed — not even tentatively.

---

## Budget Fairness

Classical and quantum baselines receive equal wall-time and cost budgets.
Comparing an unlimited classical run to a shot-limited quantum run is invalid.

---

## Result Record Schema (planned)

```yaml
benchmark_id: uuid
run_date: ISO 8601
problem_set: name + version + source URL
solver_config:
  - name: system_name
    version: x.y.z
    params: {key: value}
budget:
  wall_time_seconds: N
  cost_usd: N (if applicable)
  shots: N (for quantum)
results:
  - solver: name
    objective_value: number
    feasible: bool
    time_to_best_seconds: number
    verification_verdict: PASS | FAIL | PARTIAL
    limitations: [string]
hardware:
  classical: CPU model, RAM
  quantum: backend name, job ID, qubit count, noise model (if simulation)
```

---

## Storage

Benchmark results are stored in `benchmarks/` with one subdirectory per
problem class. See `benchmarks/README.md`.

Benchmark raw data is never modified retroactively. Corrections are new runs
with a new `benchmark_id`.
