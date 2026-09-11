---
name: yq-benchmark
description: >-
  Use this skill when designing, running, or recording comparative benchmarks
  for YourQuantum. Activate when evaluating whether a new method improves
  results, when preparing evidence for a performance claim, or when comparing
  the quantum module against classical baselines. All benchmark runs must
  include the required baselines defined in docs/BENCHMARK_PROTOCOL.md.
  This skill enforces shared data, equal budgets, and honest reporting.
---

# yq-benchmark — Comparative Benchmarking

## Input

- Problem set (fixed, versioned instances).
- All solver configurations to compare.
- Equal compute budget for all baselines.
- Success criterion defined before running.

## Procedure

### 1. Read Benchmark Protocol

Read `docs/BENCHMARK_PROTOCOL.md` in full before running any benchmark.

### 2. Fix the Problem Set

1. Select problem instances from `benchmarks/problems/`.
2. Record the exact instance IDs and versions.
3. **Do not modify instances after this point.**
4. **Do not tune any solver on benchmark problems.**

### 3. Confirm All Required Baselines

The following baselines MUST ALL be present in every comparative run:

- [ ] LLM alone (no tools or computation).
- [ ] LLM + tools (calculator, code interpreter, search).
- [ ] Best classical solver available for this problem class.
- [ ] YourQuantum without quantum module (classical path only).
- [ ] YourQuantum with quantum module (full system).

Omitting any baseline invalidates the comparison for quantum advantage claims.

### 4. Equal Budget Enforcement

All baselines receive the same:
- Wall time limit.
- Memory limit.
- Cost limit (if applicable).
- For quantum: same shot count.

Document the budget for each baseline in the result record.

### 5. Run and Record

For each solver and problem instance:
- Set random seed (if applicable) and record it.
- Run within budget.
- Pass every candidate through the Verifier before recording.
- Record: objective value, feasibility, solve time, verification verdict.

Use the result schema from `docs/BENCHMARK_PROTOCOL.md`.

### 6. Quantum Advantage Assessment

Quantum advantage is claimed ONLY when ALL of the following hold:

1. Quantum path outperforms the best classical baseline on at least one metric.
2. The result holds on at least 3 independent problem instances.
3. Statistical significance is reported (confidence interval, number of runs).
4. The hardware/execution mode is recorded (simulation vs QPU).

If these conditions are not met: report the result honestly without an
advantage claim. "The quantum path did not outperform classical baselines on
this problem set" is a valid and important result.

### 7. Store Results

Create `benchmarks/results/YYYY-MM-DD-<uuid>/` with:
- `config.yaml`: solver configs, budget, problem set IDs, hardware.
- `results.yaml`: per-solver per-instance metrics.
- `notes.md`: observations, anomalies, next steps.

Do NOT retroactively modify result files.

### 8. Update Documentation

If benchmark results contradict any claim in `docs/PRODUCT.md` or any
user-facing copy, update the documentation before the next release.

## Required Output

- Complete result record in `benchmarks/results/`.
- Honest assessment of whether the quantum advantage criterion was met.
- Updated `docs/SOURCES.md` with the benchmark record reference.

## Abort Conditions

- If any required baseline cannot be run (e.g., solver unavailable), halt the
  benchmark rather than running a partial comparison that might be misread.
- If problem instances were modified after being recorded, invalidate the run.

## What This Skill Does NOT Do

- Does not accept partial comparisons as evidence for advantage claims.
- Does not run benchmarks on tuned instances.
- Does not report unverified candidates.
- Does not claim advantage from simulation results that were not compared to
  classical baselines on the same problem.
