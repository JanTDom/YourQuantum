---
name: yq-architect
description: >-
  Use this skill when designing or extending the YourQuantum engine architecture:
  defining component contracts, API schemas, worker and queue design, capability
  registry, versioning strategy, or cross-cutting concerns. Activate when
  making architectural decisions, designing a new major component, or reviewing
  architectural consistency before a significant implementation phase.
---

# yq-architect — Engine Architecture

## Input

- `docs/ARCHITECTURE.md` (current state).
- `docs/PROBLEM_IR.md` (IR schema).
- `docs/CAPABILITIES.md` (current capability inventory).
- `docs/memory/DECISIONS.md` (existing decisions to respect).
- The specific architectural question or task.

## Procedure

### 1. Read Current Architecture

Read `docs/ARCHITECTURE.md` in full before proposing any change.
Identify all components the change will affect.

### 2. Check Existing Decisions

Read `docs/memory/DECISIONS.md` for decisions relevant to the area.
Do not re-litigate settled decisions without new evidence.

### 3. Define Contracts First

Every new component must have a defined interface before implementation:

- Input type (schema, validation rules).
- Output type (schema, possible error states).
- Preconditions and postconditions.
- Resource limits (memory, time, external calls).

### 4. Capability Registry

Every new capability (solver, quantum method, data format) must be registered in
`docs/CAPABILITIES.md` with:

- Unique capability ID.
- `can_handle(problem_ir) → bool` contract.
- Status: PLANNED / IMPLEMENTED / TESTED / DEPLOYED.

The router selects methods by querying the registry, not by hard-coded logic.

### 5. Worker and Queue Design

For any capability that runs in a worker:
- Define job schema (input, output, error).
- Define timeout and resource limits.
- Define retry policy and dead-letter handling.
- Confirm no user-prompt code reaches the worker as executable input.

### 6. Versioning

- Problem IR changes → increment schema version.
- API contract changes → version the endpoint.
- Capability behaviour changes → update capability version in registry.
- Breaking changes → record in `docs/memory/DECISIONS.md`.

### 7. Record the Decision

For any architectural decision made during this skill:
Record it in `docs/memory/DECISIONS.md` with ID, date, rationale, alternatives,
and consequences.

Update `docs/ARCHITECTURE.md` with the new component or change.

## Required Output

- Updated `docs/ARCHITECTURE.md` if architecture changed.
- Updated `docs/CAPABILITIES.md` if new capabilities added.
- New or updated decision in `docs/memory/DECISIONS.md`.
- Concrete interface definition(s) for new components.

## Abort Conditions

- If a proposed architecture change conflicts with an ACTIVE decision in
  DECISIONS.md, surface the conflict and ask the user to resolve it before
  proceeding.
- If a new component bypasses the Problem IR contract (e.g., a solver that reads
  user prompts directly), reject the design.

## What This Skill Does NOT Do

- Does not implement code — only designs contracts and updates docs.
- Does not override existing ACTIVE decisions silently.
- Does not assume performance characteristics without benchmark evidence.
