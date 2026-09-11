# VERIFICATION.md — Independent Verification

**Status:** PLANNED · **Last updated:** 2026-09-09

---

## Why Independent Verification

A solver reporting success does not mean the result is correct.
The Verifier is structurally independent from all solvers: it reads only the
Problem IR and the candidate result, never the solver's internal state.

---

## What Can Be Verified Independently

| Check | Description | Confidence |
|-------|-------------|------------|
| Constraint satisfaction | Every constraint in the IR evaluated against the candidate | High (deterministic) |
| Objective value recomputation | Objective function re-evaluated from scratch | High (deterministic) |
| Feasibility | All variable domains respected | High (deterministic) |
| Numerical residual | For continuous problems: ||Ax - b|| and constraint violations | Quantitative |
| Counter-example search | For claimed optima: local neighbourhood check | Partial |
| Solver certificate validation | If solver provides a dual certificate | Solver-dependent |

---

## What Cannot Be Independently Proven

| Claim | Limitation |
|-------|-----------|
| Global optimality | Only provable with complete solvers (e.g., branch-and-bound to completion) |
| QPU advantage | Requires controlled benchmark comparison |
| Real-world validity | Model-optimal ≠ real-world-optimal |
| Infeasibility | Timeout during search ≠ proof of infeasibility |
| LLM formalisation correctness | Verifier checks IR conformance, not user intent |

---

## Verification Report Schema (planned)

```typescript
interface VerificationReport {
  problem_id: string;         // pinned to the IR version
  candidate_id: string;
  verified_at: string;        // ISO 8601
  verifier_version: string;

  feasible: boolean;
  objective_value: number | null;
  objective_recomputed: boolean;

  constraint_results: ConstraintResult[];
  numerical_residual: number | null;
  certificate: SolverCertificate | null;

  verdict: "PASS" | "FAIL" | "PARTIAL";
  verdict_reason: string;
  limitations: string[];       // honest list of what was NOT proven
}

interface ConstraintResult {
  constraint_id: string;
  satisfied: boolean;
  violation_magnitude: number | null;
  note: string | null;
}
```

---

## Verification in the UI

- Every result shown to the user includes the verification verdict.
- PASS, FAIL, and PARTIAL are displayed distinctly — never merged into a
  generic "success" state.
- The `limitations` list is always visible, not hidden behind a "details" toggle.

---

## What the Verifier Does NOT Do

- Does not re-run the solver.
- Does not modify the candidate.
- Does not interpret user intent — it only checks the IR.
- Does not claim a PASS means the result is practically useful.
