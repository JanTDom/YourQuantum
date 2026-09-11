---
name: yq-context
description: >-
  Use this skill at the start of any YourQuantum session, after a gap between
  sessions, or whenever documentation may have drifted from the code. It
  recovers full project context, detects inconsistencies between docs and
  implementation, and surfaces any stale decisions or superseded lessons.
  Activate before beginning work that depends on understanding the current
  project state.
---

# yq-context — Context Recovery and Doc/Code Alignment

## Input

- Access to the repository root.
- No assumptions about what has changed since the last session.

## Procedure

### 1. Read Core Memory (in order)

1. `AGENTS.md` (root) — project identity, rules, document map.
2. `docs/memory/INDEX.md` — project map summary.
3. `docs/memory/CURRENT_STATE.md` — current stage, what works, blockers,
   next actions.
4. `docs/memory/DECISIONS.md` — scan for decisions relevant to today's task.
5. `docs/memory/LESSONS.md` — scan for lessons relevant to today's task.

### 2. Check Repository State

Run the following to understand actual state:

```bash
git status
git log --oneline -10
```

If git is not initialised, note that in CURRENT_STATE.md.

Compare reported state in CURRENT_STATE.md against actual repository state.
Flag any discrepancy.

### 3. Check Documentation Consistency

For each doc listed in `docs/CAPABILITIES.md` with status IMPLEMENTED or TESTED:

- Confirm the corresponding code file exists.
- Confirm at least one test file covers it.
- If not found, flag as "status inconsistent — needs re-verification".

### 4. Run Structure Validation

```bash
bash scripts/validate-structure.sh
```

Review output. All checks should PASS.

### 5. Identify Drift

List any documents that reference plans not yet reflected in code, or code
not yet documented. This is normal — just make it explicit.

## Required Output

A concise context summary:
- Current stage (from CURRENT_STATE.md, verified against repo).
- Any discrepancies found between docs and code.
- Relevant past decisions for today's task.
- Relevant past lessons for today's task.
- Updated session start time in CURRENT_STATE.md (append, don't overwrite).

## Abort Conditions

- If CURRENT_STATE.md does not exist, create it from scratch using the template
  in `docs/memory/CURRENT_STATE.md` structure before proceeding.
- If AGENTS.md does not exist, create it from the backup in project history or
  request the user re-run the preparation step.

## What This Skill Does NOT Do

- Does not assume the previous session's context is still valid.
- Does not read other projects or global configuration.
- Does not modify source code.
