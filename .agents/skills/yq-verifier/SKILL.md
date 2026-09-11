---
name: yq-verifier
description: >-
  Use this skill when independently verifying a candidate solution against the
  Problem IR: re-evaluating the objective function, checking all constraints,
  computing numerical residuals, searching for counter-examples, or validating
  solver certificates. Activate whenever a solver (classical or quantum) has
  produced a candidate result that must be checked before being shown to the user.
  This skill clearly distinguishes verification of a candidate from proof of
  global optimality.
---

# yq-verifier — Independent Verification

## Input

- An approved, versioned Problem IR (the check basis).
- One or more candidate results from a solver.
- The solver's claimed status (optimal, feasible, etc.).

## Procedure

The Verifier reads only the Problem IR and the candidate. It does NOT read
the solver's internal state, algorithm, or intermediate steps.

### 1. Read Verification Protocol

Read `docs/VERIFICATION.md` before writing any check.

### 2. Feasibility Check

For every constraint in the Problem IR:

```python
for constraint in problem_ir.constraints:
    result = evaluate_constraint(constraint, candidate.solution)
    record(constraint_id=constraint.id,
           satisfied=result.satisfied,
           violation_magnitude=result.violation_magnitude)
```

Hard constraints must all be satisfied for PASS verdict.
Soft constraints contribute to PARTIAL if violated.

### 3. Domain Check

For every variable in the Problem IR:
Confirm the candidate value is within the declared domain.
Values outside the domain are a constraint violation.

### 4. Objective Re-evaluation

Re-compute the objective function independently from the solver:

```python
recomputed_objective = evaluate_objective(problem_ir.objectives[0],
                                          candidate.solution)
assert abs(recomputed_objective - candidate.objective_value) < tolerance
```

If there is a significant discrepancy, report it as a FAIL with both values.

### 5. Numerical Residual (for continuous problems)

Compute ||Ax - b||₂ for equality constraints and max(0, Ax - b) for
inequalities. Record the residual magnitude.

### 6. Counter-Example Search (optional, if budget allows)

For claimed optimal solutions:
Search the local neighbourhood (flip one binary variable, perturb one
continuous variable by ε) for a strictly better feasible solution.

If found: the claimed optimality is wrong. Report the counter-example.
If not found: state "no local improvement found in neighbourhood" — not
"globally optimal".

### 7. Certificate Validation (if supplied)

If the solver supplies a certificate (e.g., dual variables for LP, UNSAT
core for SAT):
Validate it according to the certificate type.
Record: certificate type, validation result, limitations.

### 8. Produce Verification Report

```python
report = VerificationReport(
    problem_id=problem_ir.problem_id,
    candidate_id=candidate.id,
    verified_at=now_iso(),
    feasible=all_hard_constraints_satisfied,
    objective_value=recomputed_objective,
    constraint_results=constraint_results,
    numerical_residual=residual,
    certificate=validated_certificate,
    verdict=compute_verdict(),   # PASS / FAIL / PARTIAL
    verdict_reason=reason,
    limitations=honest_list_of_what_was_not_proven
)
```

The `limitations` list MUST include at minimum:
- "Global optimality not proven" (unless a complete solver certificate is
  present and validated).
- Any constraints that could not be fully evaluated (e.g., stochastic, external
  data).

## Verdict Rules

| Condition | Verdict |
|-----------|---------|
| All hard constraints satisfied, objective re-evaluation matches | PASS |
| Any hard constraint violated | FAIL |
| All hard constraints satisfied, soft constraints violated | PARTIAL |
| Objective re-evaluation discrepancy > tolerance | FAIL |

## Required Output

- A `VerificationReport` for every candidate checked.
- The report is passed to the frontend for display.
- PASS/FAIL/PARTIAL is always visible to the user — never hidden.

## Abort Conditions

- If the Problem IR is not available (e.g., pinned version not found), FAIL
  the verification and report "IR not available for checking".
- If the candidate solution is malformed (missing variables), FAIL immediately.

## What This Skill Does NOT Do

- Does not re-run the solver.
- Does not modify the candidate to make it feasible.
- Does not claim PASS means the result is practically useful.
- Does not skip the limitations list to make results look cleaner.
