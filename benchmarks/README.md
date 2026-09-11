# Benchmarks — YourQuantum

**Status:** PLANNED · **Last updated:** 2026-09-09

See `docs/BENCHMARK_PROTOCOL.md` for the full benchmark methodology,
required baselines, metrics, and the quantum advantage criterion.

---

## Directory Structure (planned)

```
benchmarks/
  README.md                    # This file
  problems/                    # Fixed, versioned problem instances
    combinatorial/             # TSP, graph colouring, max-cut, etc.
    continuous/                # Non-linear optimisation
    satisfiability/            # SAT / SMT instances
    scheduling/                # Job-shop, nurse rostering, etc.
    custom/                    # Real user problems (with permission)
  results/                     # Recorded benchmark runs (YAML)
    YYYY-MM-DD-<id>/
      config.yaml              # Solver configurations and budgets
      results.yaml             # Per-solver metrics
      notes.md                 # Observations
  reports/                     # Generated comparison reports
```

---

## How to Add a Problem

1. Source the problem from a published benchmark set or obtain user permission.
2. Fix the instance (no modifications after recording).
3. Record the source, version, and licence in `problems/<class>/SOURCES.md`.
4. Add the instance to version control.

**Do not tune any solver on benchmark problems.**

---

## How to Record a Run

1. Use the schema in `docs/BENCHMARK_PROTOCOL.md`.
2. Create a new directory `results/YYYY-MM-DD-<uuid>/`.
3. Include ALL required baselines (see protocol).
4. Do not modify result files after creation.

---

## Current Benchmark Status

No benchmarks have been run yet. No performance claims are made.
