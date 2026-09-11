---
name: yq-routing-and-decomposition
description: >-
  Use this skill when selecting which solver or method to use for a given
  Problem IR, decomposing a large problem into sub-problems, allocating compute
  budgets across methods, or deciding when to abandon an unpromising solver
  branch. Activate when the problem has arrived as an approved IR and the
  system needs to determine how to solve it. This skill never calls a
  heuristically merged result a global optimum.
---

# yq-routing-and-decomposition — Method Routing and Problem Decomposition

## Input

- An approved, versioned Problem IR.
- Total compute budget (wall time, cost, memory).
- Current capability registry (from `docs/CAPABILITIES.md`, status TESTED or
  DEPLOYED only).

## Procedure

### 1. Problem Characterisation

Classify the problem along these axes:

| Dimension | Options |
|-----------|---------|
| Variable type | Binary, integer, continuous, mixed, categorical |
| Objective count | Single, multi-objective |
| Constraint type | Linear, non-linear, logical, cardinality |
| Problem size | Number of variables, constraints |
| Structure | Dense, sparse, decomposable, hierarchical |
| Known hardness class | P, NP-complete, NP-hard, undecidable (if known) |

Document the classification in the routing record.

### 2. Capability Query

Query the capability registry for solvers that return `can_handle(problem_ir) = True`.
Only use capabilities with status TESTED or DEPLOYED.

Do NOT hard-code solver selection. The router reads the registry.

### 3. Method Selection

Rank candidate methods by:

1. Expected solution quality for this problem structure.
2. Compute cost within the given budget.
3. Verification certainty (exact vs heuristic).

Prefer exact methods when the problem is small enough.
Use heuristics only when the problem is provably too large for exact methods
within the budget.

### 4. Budget Allocation

Split the total budget across:
- Formalisation check (minimal).
- Primary solver (largest share).
- Alternative solver (if budget allows).
- Verification (fixed overhead; never skipped).

Record the budget split in the routing record.

### 5. Problem Decomposition (if applicable)

When the problem is decomposable:
- Identify independent or weakly-coupled sub-problems.
- Solve sub-problems with appropriate sub-budgets.
- Reassemble results.

**IMPORTANT:** Reassembled results are NOT globally optimal unless the
decomposition is provably lossless (e.g., by problem structure or
mathematical proof). State the actual guarantee.

### 6. Early Termination

Abandon a solver branch when:
- The branch has consumed its budget with no feasible solution.
- The best bound indicates the remaining gap is not worth the remaining cost.
- A better result is already available from another method.

Record the termination reason in the routing record.

### 7. Quantum Routing

Route to the quantum module (yq-quantum-core) only when:
- The problem is QUBO-encodeable within the available qubit budget.
- The quantum path is competitive with classical alternatives (or this is a
  benchmarking run where comparison is the goal).

Do NOT route to quantum by default. Route to quantum when it is expected to help.

## Required Output

- Routing record: problem characterisation, candidates queried, selected method,
  budget allocation, decomposition plan (if any).
- Initiated solver job(s) with pinned IR version and budget.

## Abort Conditions

- If no registered, tested capability can handle the problem: return a clear
  "no solver available" result with the reason. Do not invent a solver.
- If the problem is under-specified after formalisation: return to the
  formaliser rather than guessing at a solution.

## What This Skill Does NOT Do

- Does not merge sub-problem results and call them globally optimal without proof.
- Does not bypass the capability registry.
- Does not route to quantum methods for branding reasons.
- Does not continue a solver branch indefinitely past its budget.
