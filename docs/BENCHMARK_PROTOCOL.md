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

---

## Empirical Benchmark Results (F2 Evidence Record)

**Execution Date:** 2026-09-13
**Platform / Hardware:** macOS Darwin x86_64, Python 3.12.14
**Artifact:** `benchmarks/results/benchmark_20260913_154536.json`
**Script:** `benchmarks/run.py`

### 1. Comparative Results Table

| Instance | Variables / Constr. | Solver | Status | Objective | Solve Time | Rel. Gap to CP-SAT | Ground State Prob | Amplification |
|---|---|---|---|---|---|---|---|---|
| **Healthcare Reform (DESIGN)** | 10 vars, 8 constr. | **OR-Tools CP-SAT** | COMPLETED | **12.50** | **0.852s** | **0.00% (Exact)** | — | — |
| | | **QAOA (Ideal Aer)** | COMPLETED | 12.50 | 0.272s | 0.00% | 0.0938 | 96.0x |
| | | **QAOA (Noise Model)** | COMPLETED | 12.50 | 14.832s | 0.00% | 0.0312 | 32.0x |
| **Allocation N=4** | 4 vars, 1 constr. | **OR-Tools CP-SAT** | COMPLETED | **44.00** | **0.009s** | **0.00% (Exact)** | — | — |
| | | **QAOA (Ideal Aer)** | COMPLETED | 44.00 | 0.277s | 0.00% | 0.0625 | 1.0x |
| | | **QAOA (Noise Model)** | COMPLETED | 44.00 | 1.097s | 0.00% | 0.0312 | 0.5x |
| **Allocation N=6** | 6 vars, 1 constr. | **OR-Tools CP-SAT** | COMPLETED | **54.00** | **0.007s** | **0.00% (Exact)** | — | — |
| | | **QAOA (Ideal Aer)** | COMPLETED | 54.00 | 0.555s | 0.00% | 0.0625 | 4.0x |
| | | **QAOA (Noise Model)** | COMPLETED | 54.00 | 7.383s | 0.00% | 0.0625 | 4.0x |
| **Allocation N=8** | 8 vars, 1 constr. | **OR-Tools CP-SAT** | COMPLETED | **121.00** | **0.005s** | **0.00% (Exact)** | — | — |
| | | **QAOA (Ideal Aer)** | COMPLETED | 121.00 | 1.401s | 0.00% | 0.1250 | 32.0x |
| | | **QAOA (Noise Model)** | COMPLETED | 121.00 | 14.047s | 0.00% | 0.0625 | 16.0x |
| **Allocation N=10** | 10 vars, 1 constr. | **OR-Tools CP-SAT** | COMPLETED | **130.00** | **0.006s** | **0.00% (Exact)** | — | — |
| | | **QAOA (Ideal Aer)** | COMPLETED | 123.00 | 1.079s | 5.38% | 0.0625 | 64.0x |
| | | **QAOA (Noise Model)** | COMPLETED | 123.00 | 28.279s | 5.38% | 0.0625 | 64.0x |

### 2. Scientific Findings & Verification
1. **Classical Dominance**: CP-SAT solves all tested instances to exact provable global optimality within 5–10 ms (combinatorial allocation) and 850 ms (multi-criteria design), substantially outperforming quantum circuit simulation in runtime and exactness.
2. **Heuristic Limits of Shallow QAOA ($p=1$)**: For $N=10$, QAOA finds a feasible near-optimal state (obj=123.0) with a 5.38% gap relative to CP-SAT (obj=130.0), empirically verifying that $p=1$ QAOA is an approximation heuristic, not an exact solver.
3. **Physical Noise Impact (Aer Depolarizing Channel)**: Depolarizing gate noise ($p_1=0.002, p_2=0.02$) sharply reduces ground state probability:
   - On Healthcare Reform: amplification factor drops from **96.0x** (ideal) to **32.0x** (noise) — a 3-fold attenuation.
   - On Allocation N=8: amplification drops from **32.0x** to **16.0x** — a 2-fold attenuation.
4. **Advantage Verdict**: **NO QUANTUM ADVANTAGE OBSERVED**. In accordance with AGENTS.md §2, YourQuantum defaults to CP-SAT as primary solver, presenting QAOA as a comparative benchmarking method.
