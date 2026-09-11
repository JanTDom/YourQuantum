# PRODUCT.md — YourQuantum

**Status:** PLANNED · **Last updated:** 2026-09-09

---

## Goal

YourQuantum is an environment for solving hard problems.

A user presents a problem in plain language, supplies data, states requirements,
and receives a result backed by real computation, constraint checking, analysis,
or an appropriate proof — along with an honest account of that result's limitations.

---

## Target Audience

- Researchers, engineers, and analysts who encounter computationally hard problems
  in their domain and need verified, reproducible results.
- Teams that want to evaluate whether quantum algorithms offer a real advantage
  for their specific workload.
- Problem owners who can articulate a problem clearly but do not want to become
  experts in solver configuration.

The product does NOT target beginners learning quantum computing for its own sake.

---

## Core Promise

Given a well-specified problem and sufficient data, YourQuantum will:

1. Formalise the problem into a verified mathematical model.
2. Select the best available method (classical, hybrid, or quantum) for the budget
   and constraints.
3. Compute a result using real algorithms — not LLM interpolation.
4. Verify the result independently.
5. Return the result with an honest account of its quality and limitations.

High efficiency relative to alternatives is a hypothesis to be validated by
benchmarks — not a marketing claim.

---

## Scope (in)

- Problem intake in plain language, structured data, or API call.
- Formalisation into a versioned, domain-agnostic intermediate representation.
- Classical solver integration (constraint programming, optimisation,
  symbolic/numeric computation, SAT/SMT).
- Quantum algorithm module: QUBO/Ising encoding, QAOA, VQE, circuit simulation,
  measurement sampling, QPU connectivity.
- Method routing: selecting the best approach per budget and problem structure.
- Independent verification: constraint check, re-evaluation, certificates.
- Result presentation with quality metrics, limitations, and comparisons.
- Benchmarking against baseline methods.

---

## Scope (out — explicit exclusions)

- **Not** an educational quantum computing simulator or tutorial system.
- **Not** a general-purpose notebook or REPL.
- **Not** a system with fixed industry templates as the primary organising
  principle. New use-cases emerge from composing general primitives.
- **Not** a promise to solve every possible problem. Intractable or
  under-specified problems get an honest "cannot solve" with explanation.
- **Not** a system that uses quantum methods on every task regardless of benefit.
- **Not** a system that calls LLM output a "computation result".

---

## Product-Level Definitions

| Term | Meaning in YourQuantum |
|------|------------------------|
| **Quantum** | Real amplitude/operator/circuit representation; not metaphor |
| **Advantage** | Empirically measured on shared benchmark problems |
| **Verified** | Independently re-evaluated against problem constraints |
| **Optimal** | Optimal for the stated model; real-world validity is separate |
| **Simulation** | Classical CPU/GPU execution of quantum-circuit mathematics |
| **QPU** | Real quantum processing unit (hardware backend) |
