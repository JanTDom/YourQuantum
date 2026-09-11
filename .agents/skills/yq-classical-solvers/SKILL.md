---
name: yq-classical-solvers
description: >-
  Use this skill when selecting, integrating, or debugging classical solver
  adapters: constraint programming (CP-SAT, OR-Tools), linear/integer
  programming (HiGHS, PuLP), SMT (Z3), continuous optimisation (SciPy),
  symbolic computation (SymPy), or commercial solvers (Gurobi). Activate when
  implementing a new solver adapter, evaluating which solver fits a problem
  class, or diagnosing a solver failure.
---

# yq-classical-solvers — Classical Solver Integration

## Input

- A Problem IR (approved, versioned).
- The specific solver or problem class in question.
- Compute budget (time, memory).

## Procedure

### 1. Verify Solver Capabilities Against Current Library Versions

Before selecting or configuring a solver:

1. Check the solver's actual installed version (`pip show <pkg>` or
   `npm list <pkg>`).
2. Verify the specific API used exists in that version (do not use docs from
   a different version).
3. Record source and version in `docs/SOURCES.md`.

### 2. Implement the Adapter Interface

Every solver adapter must implement:

```python
def can_handle(problem_ir: ProblemIR) -> bool:
    """Return True iff this solver can attempt the problem."""
    ...

def solve(problem_ir: ProblemIR, budget: ComputeBudget) -> SolverResult:
    """
    Attempt to solve the problem within the given budget.
    Must return a SolverResult even on failure (with error field populated).
    Must never raise an unhandled exception to the caller.
    """
    ...
```

### 3. Budget Enforcement

- Solvers MUST respect the time limit from `budget.wall_time_seconds`.
- Solvers MUST respect the memory limit from `budget.memory_mb`.
- On budget exhaustion: return the best solution found so far (if any),
  with `status: "timeout"` or `status: "memory_limit"`. Do NOT raise.

### 4. Solver-Specific Notes

| Solver | Key constraint | Pitfall to avoid |
|--------|---------------|-----------------|
| OR-Tools CP-SAT | Integer/Boolean domains | Does not handle continuous vars natively |
| HiGHS / PuLP | Linear constraints only | Non-linear objectives need reformulation |
| Z3 | Exact logical reasoning | May time out on large instances |
| SciPy | Continuous variables | Local optima only; not for combinatorial |
| SymPy | Symbolic; exact | Not a numeric solver; no optimisation |
| Gurobi | Best MIP performance | Requires valid licence at runtime |

### 5. Result Schema

```python
@dataclass
class SolverResult:
    solver_name: str
    solver_version: str
    problem_id: str
    status: Literal["optimal", "feasible", "infeasible", "timeout",
                    "memory_limit", "error"]
    objective_value: float | None
    solution: dict[str, Any] | None  # variable_id → value
    solve_time_seconds: float
    certificate: dict | None         # dual certificate if available
    limitations: list[str]           # honest list of what was NOT proven
    error_message: str | None
```

### 6. Route to Verifier

Every solver result MUST be passed to the Verifier (yq-verifier) before
being shown to the user. The Verifier runs independently.

### 7. Update Capabilities Registry

After successfully integrating and testing a new solver:
Update its status in `docs/CAPABILITIES.md` from PLANNED to IMPLEMENTED,
then to TESTED when tests pass.

## Required Output

- Working solver adapter with tests.
- Updated `docs/CAPABILITIES.md`.
- Updated `docs/SOURCES.md` with verified library version.

## Abort Conditions

- If the solver's actual API does not match the documented API, stop and
  verify the correct version before proceeding.
- If the solver requires executing user-supplied code strings, reject the
  integration.

## What This Skill Does NOT Do

- Does not claim a feasible solution is globally optimal unless the solver
  certifies it.
- Does not ignore resource limits because the solver "usually finishes fast".
- Does not skip the Verifier step.
