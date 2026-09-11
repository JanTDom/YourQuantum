# PROBLEM_IR.md — Versioned Problem Intermediate Representation

**Status:** PLANNED · **Last updated:** 2026-09-09

---

## Purpose

The Problem IR is the canonical, versioned, domain-agnostic representation of
a user's problem instance. It is the contract between:

- The LLM/Formaliser (producer)
- The Router (consumer for method selection)
- The Solvers (consumer for computation)
- The Verifier (consumer for validation)
- The User (approves the model before solving begins)

A mismatch between user intent and the IR is the most common source of wrong
results. The formalisation step exists to make this mismatch explicit and
correctable before computation starts.

---

## Schema (v0 — draft, not yet implemented)

```typescript
interface ProblemIR {
  schema_version: "0.1";          // incremented on breaking changes
  problem_id: string;             // UUID, generated at intake
  created_at: string;             // ISO 8601
  description_raw: string;        // verbatim user input
  description_formalised: string; // structured restatement for user review

  variables: Variable[];
  data: DataSource[];
  objectives: Objective[];
  constraints: Constraint[];
  assumptions: Assumption[];
  missing_information: MissingInfo[];
}

interface Variable {
  id: string;
  name: string;
  domain: Domain;      // continuous, integer, binary, categorical, set
  unit: string | null;
  provenance: "user_supplied" | "derived" | "assumed";
}

interface Objective {
  id: string;
  direction: "minimise" | "maximise";
  expression: string;  // symbolic or reference to data
  priority: number;    // for multi-objective: 1 = primary
}

interface Constraint {
  id: string;
  type: "equality" | "inequality" | "logical" | "cardinality";
  expression: string;
  hard: boolean;       // hard = must be satisfied; soft = penalised if violated
  penalty_weight: number | null;
}

interface Assumption {
  id: string;
  statement: string;
  confidence: "high" | "medium" | "low";
  source: "user_stated" | "model_inferred";
}

interface MissingInfo {
  id: string;
  description: string;
  impact: "blocks_solving" | "reduces_quality" | "minor";
  clarification_question: string;
}
```

---

## Formalisation Contract

Before any solver runs, the following must be satisfied:

1. All `MissingInfo` items with `impact: "blocks_solving"` are resolved.
2. The user has reviewed and explicitly approved the formalised model.
3. All variables have explicit domains and units (or "dimensionless" is stated).
4. At least one objective is defined.

Approval is a deliberate user action — not a model assumption.

---

## Versioning

- Approved IR instances are immutable.
- Any change (user correction, new data, clarified constraint) creates a new
  version with a new `problem_id` and a `parent_problem_id` reference.
- Solvers always operate on a specific, pinned IR version.

---

## Domain-Independence

The IR does not contain domain-specific fields (no "city", "portfolio",
"molecule"). Domain knowledge is captured in variable names, units, and
constraint expressions — not in special-cased schema extensions.
