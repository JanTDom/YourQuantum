---
name: yq-learning
description: >-
  Use this skill at the end of a work stage when a repeatable lesson was
  learned, a significant decision was made, or when CURRENT_STATE.md needs
  to be updated to reflect actual progress. Also activate when considering
  whether to use the /learn slash command to persist a rule — verify first
  where /learn actually stores data to avoid creating a conflicting memory
  source. This skill does not change scientific foundations or security rules
  based on a single suggestion or failure.
---

# yq-learning — Persisting Lessons and Updating Context

## Input

- The work completed in the current stage.
- Any errors encountered and how they were resolved.
- Any decisions made that are not yet recorded.
- Current state of the repository.

## Procedure

### 1. Update CURRENT_STATE.md

Update `docs/memory/CURRENT_STATE.md` with:
- Today's date.
- Current stage.
- What actually works (tested, not assumed).
- What is not yet implemented.
- Last executed tests and their actual output (not assumed).
- Active blockers.
- Next three specific actions.
- Code version (git commit hash or "uncommitted" if no commit yet).

Do NOT report planned features as working.
Do NOT write a fictional git commit hash.

### 2. Record New Decisions

For any decision made during this session that affects architecture, product
direction, security, or scientific integrity:

Add to `docs/memory/DECISIONS.md` with:
- Decision ID (next sequential ID).
- Date.
- Decision (one sentence).
- Rationale (why this and not the alternatives).
- Alternatives considered.
- Consequences.
- Status: ACTIVE.

### 3. Record Repeatable Lessons

For any lesson that is likely to recur across sessions:

Add to `docs/memory/LESSONS.md` with:
- Lesson ID (next sequential ID).
- Status: CONFIRMED (if witnessed), PROPOSED (if inferred).
- Problem → Cause → Evidence → Fix → Future rule.

Do NOT record:
- One-off debugging steps.
- Conversation snippets.
- User-specific data.

### 4. Consider /learn

If the lesson is about agent behaviour (not project specifics), consider using
`/learn` to persist it as a global rule.

Before using `/learn`:
1. Check where it stores data (verify it goes to `~/.gemini/config/` or similar).
2. Confirm it will not conflict with existing project rules in `AGENTS.md`.
3. If conflict is possible, record only in `LESSONS.md` and update `AGENTS.md`
   instead.

### 5. Archive Stale Content

If any section of CURRENT_STATE.md or LESSONS.md is more than 2 stages old
and no longer relevant to current work:
Move it to a dated archive file (`docs/memory/archive/YYYY-MM-DD-<topic>.md`)
rather than deleting or leaving it to accumulate.

## Constraints

- Do NOT change scientific integrity rules based on a single failure or suggestion.
  A change to AGENTS.md rules requires: evidence from at least 2 occurrences,
  an entry in DECISIONS.md, and explicit user review.
- Do NOT store customer data, personal data, or secrets in any memory file.
- Do NOT copy entire conversation transcripts into memory files.

## Required Output

- Updated `docs/memory/CURRENT_STATE.md`.
- New entries in `docs/memory/DECISIONS.md` and/or `docs/memory/LESSONS.md`
  (if applicable).

## What This Skill Does NOT Do

- Does not change the scientific or security rules in `AGENTS.md` without
  the user's explicit review and approval.
- Does not automate LLM weight changes (not technically possible; stated here
  to avoid the metaphor being acted upon).
- Does not create a second, conflicting source of permanent project memory.
