---
name: yq-formalizer
description: >-
  Use this skill when translating a user's natural-language problem description
  into a versioned Problem IR (intermediate representation). Activate when a
  new problem arrives, when the user corrects or extends an existing problem
  model, or when the existing IR needs to be reviewed for completeness before
  solving begins. This skill never guesses missing data and never forces every
  problem into QUBO form.
---

# yq-formalizer — Problem Formalisation

## Input

- User's natural-language problem description.
- Any structured data the user has supplied (files, tables, formulas).
- Existing Problem IR (if this is a revision).

## Procedure

### 1. Read Problem IR Schema

Read `docs/PROBLEM_IR.md` for the current schema version before writing
any output.

### 2. Elicit Missing Information

For each of the following, determine if the user has provided it or if it must
be asked:

| Required | Questions to ask if missing |
|----------|---------------------------|
| Variables | What are the decision variables? What can change? |
| Domains | What values can each variable take? Integer, real, binary, set? |
| Data | What data is given? What are the units? |
| Objectives | What should be maximised or minimised? Is there a priority order? |
| Constraints | What must always hold? What is preferred but can be violated? |
| Assumptions | What does the user assume about the problem structure? |

Do NOT guess. If information is missing and cannot be reasonably inferred,
list it as `MissingInfo` with impact level and a clarifying question.

### 3. Construct the Problem IR Draft

Produce a draft conforming to the schema in `docs/PROBLEM_IR.md`.

- Assign unique IDs to all variables, objectives, constraints, assumptions.
- Mark every field with its provenance: `user_supplied`, `derived`, `assumed`.
- Include all `MissingInfo` items with impact level.
- Assign schema version from `docs/PROBLEM_IR.md`.

### 4. Present to User for Review

Show the formalised model in a readable format:

```
PROBLEM FORMALISATION DRAFT (v0.1 — not yet approved)

Variables:
  x₁: [name], domain: [domain], unit: [unit] (user_supplied)
  ...

Objectives:
  Minimise: [expression] (primary)

Constraints:
  [id]: [expression] — hard / soft
  ...

Assumptions:
  [statement] (confidence: high / medium / low)

Missing information (please clarify before solving):
  [BLOCKS SOLVING] [question]
  [REDUCES QUALITY] [question]
```

### 5. Await Explicit Approval

Do NOT proceed to solving or method routing until the user explicitly approves
the model. Approval is a deliberate user action.

### 6. Finalise and Version

Once approved:
- Assign a `problem_id` (UUID).
- Record `created_at` timestamp.
- Record `description_raw` verbatim.
- Increment version if this is a revision of an existing IR.
- Store the approved IR (location determined by ARCHITECTURE.md).

## Required Output

- A draft Problem IR ready for user review.
- A list of blocking questions (if any).
- On approval: a finalised, versioned IR record.

## Verification

The produced IR must validate against the JSON schema in `docs/PROBLEM_IR.md`.
If schema validation tooling is not yet implemented, manually check all required
fields are present and typed correctly.

## Abort Conditions

- If the problem is entirely under-specified with no recoverable information,
  return a structured request for clarification rather than a partial IR.
- If the user supplies data that contradicts stated constraints, flag the
  contradiction explicitly before proceeding.

## What This Skill Does NOT Do

- Does not produce QUBO encodings (that is `yq-quantum-core`).
- Does not select solver methods (that is `yq-routing-and-decomposition`).
- Does not guess values for `MissingInfo` items that block solving.
- Does not treat JSON Schema conformance as proof of intent conformance.
