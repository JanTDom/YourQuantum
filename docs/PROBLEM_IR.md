# PROBLEM_IR.md — Versioned Problem Intermediate Representation

**Status:** IMPLEMENTED (v0.3) · **Last updated:** 2026-09-13

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

## Problem Class Taxonomy (v0.3)

Every problem is explicitly classified into one of five fundamental classes:

- `CHOICE`: Selection of 1 from $N$ discrete options with multi-criteria analytical weighting and break-even shifts.
- `ALLOCATION`: Portfolio, knapsack, scheduling under resource budgets and logical dependencies.
- `DESIGN`: Multi-lever combinatorial system synthesis (e.g. healthcare reform) with one-hot choice, empirical option evidence, and non-zero synergies requiring verified provenance.
- `PARAMETER`: Continuous parameter optimization (SciPy HiGHS / minimize) with exact numerical residuals.
- `NOT_COMPUTABLE`: Value judgment, speculative forecast, or existential query; the system provides an honest refusal with constructive reframing suggestions into computable models.

---

## Schema (v0.3)

```typescript
interface ProblemIR {
  schema_version: "0.3";          // incremented on breaking changes
  problem_id: string;             // UUID, generated at intake
  parent_problem_id: string | null;
  version: number;
  created_at: string;             // ISO 8601
  description_raw: string;        // verbatim user input
  description_formalised: string; // structured restatement for user review
  mode: "satisfy" | "optimize" | "enumerate_all" | "pareto_frontier";
  problem_class?: "CHOICE" | "ALLOCATION" | "DESIGN" | "PARAMETER" | "NOT_COMPUTABLE";

  variables: Variable[];
  data_sources: DataSource[];
  expressions: ExpressionRegistry; // Safe expression tree without eval/exec
  objectives: Objective[];
  constraints: Constraint[];
  assumptions: Assumption[];
  missing_information: MissingInfo[];
  budget: ComputeBudget;
  approved: boolean;              // Requires deliberate human confirmation
  approved_at: string | null;
}

interface Variable {
  id: string;
  name: string;
  domain: "binary" | "integer" | "continuous" | "categorical" | "set";
  lower_bound?: number | null;
  upper_bound?: number | null;
  unit: string | null;
  provenance: "user_supplied" | "derived" | "assumed" | "web_sourced" | "llm_extracted";
  description?: string | null;
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
