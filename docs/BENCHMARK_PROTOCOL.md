# BENCHMARK_PROTOCOL.md — Benchmark Protocol & Empirical Findings

**Status:** ACTIVE PROTOCOL & EMPIRICAL RESULTS RECORDED · **Last updated:** 2026-09-13 (Phase F & I Verification)

---

## Purpose

Benchmarks are the only valid evidence for claims about YourQuantum's
performance relative to alternatives. No performance claim enters product
documentation without a corresponding benchmark result in `benchmarks/results/`.

---

## First Empirical Benchmark Run (2026-09-13)

**Evidence Record:** [`benchmarks/results/benchmark_20260913_154536.json`](file:///Users/macbookpro/PROJEKTY/YOURQUANTUM/benchmarks/results/benchmark_20260913_154536.json)
**Environment:** macOS x86_64, Python 3.12.14, OR-Tools 9.15.6755, Qiskit Aer 0.17.2.
**Test Instances Evaluated:** 5 standard instances (Healthcare Reform DESIGN, Resource Allocation, Discrete Choice, Knapsack, Graph Coloring).

### Comparative Results Summary

| Instance | CP-SAT Time (s) | CP-SAT Status | QAOA Ideal Time (s) | QAOA Ideal Status | QAOA Noise Time (s) | Quantum Advantage? |
|----------|-----------------|---------------|---------------------|-------------------|---------------------|-------------------|
| Healthcare Reform (`DESIGN`) | 0.85s | **OPTIMAL** | 0.27s | FEASIBLE | 14.83s | **NIE (CP-SAT dominuje w dowodzie)** |
| Resource Allocation (`ALLOCATION`) | 0.04s | **OPTIMAL** | 0.08s | FEASIBLE | 4.12s | **NIE (CP-SAT 2x szybszy + dowód)** |
| Discrete Choice (`CHOICE`) | 0.01s | **OPTIMAL** | 0.03s | FEASIBLE | 1.85s | **NIE (CP-SAT natychmiastowy)** |
| Knapsack Portfolio | 0.02s | **OPTIMAL** | 0.05s | FEASIBLE | 2.45s | **NIE (CP-SAT dominuje)** |
| Graph Coloring 3-color | 0.03s | **OPTIMAL** | 0.07s | FEASIBLE | 3.10s | **NIE (CP-SAT dominuje)** |

### Scientific Conclusions (DEC-003 & DEC-019)
1. **Zero Quantum Advantage on Classical CPU Simulation:** Simulating quantum statevectors or Kraus noise channels on CPU inherently incurs exponential classical overhead. CP-SAT solves all tested discrete problem instances to proven optimality in under 1 second.
2. **QAOA Algorithmic Validity Confirmed:** QAOA ansatz compilation produces valid energy gaps where the ground state matches the integer optimum. State amplification reaches $> 10\times$ over uniform sampling.
3. **Router Policy:** The router defaults to OR-Tools CP-SAT for exact discrete optimization. QAOA Aer is provided as an experimental variational simulation engine and benchmark baseline.

---

## Comparison Baselines (Required for Any Claim)

Every benchmark run MUST include ALL of the following baselines:

| Baseline | Description |
|----------|-------------|
| LLM alone | Best LLM answer without tools or computation |
| LLM + tools | LLM with calculator, code interpreter, search |
| Best classical solver | Best known classical method for the problem class (e.g. CP-SAT, HiGHS) |
| YourQuantum without quantum module | Classical path only |
| YourQuantum with quantum module | Full system (QAOA / QUBO) |

Omitting any baseline invalidates the comparison for that metric.

---

## Quantum Advantage Criterion (Non-Negotiable)

Quantum advantage is claimed ONLY when:

1. The quantum path outperforms the best classical baseline on at least one metric, measured on the same problem set with the same resource budget.
2. The result is reproduced on at least 3 independent problem instances.
3. Statistical significance is reported (confidence interval, $n$ runs).
4. The result is recorded in `benchmarks/results/` with full configuration and cryptographic audit trail.

If these conditions are not met, no advantage is claimed — not even tentatively.
