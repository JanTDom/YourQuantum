# SOURCES.md — Official Sources, Library Versions, Decision Justifications

**Status:** ACTIVE · **Last updated:** 2026-09-09

This file records every external source consulted during design decisions.
Each entry states: what was checked, when, the version or date, and which
decision it justifies. Do not record sources that were not actually consulted.

---

## Antigravity Customisation System

| Source | Date checked | Key finding | Justifies |
|--------|-------------|-------------|-----------|
| Built-in skill: `agy-customizations/SKILL.md` | 2026-09-09 | Skills: `.agents/skills/<name>/SKILL.md` with `name` + `description` frontmatter | Skill directory structure |
| Built-in skill: `agy-customizations/docs/rules.md` | 2026-09-09 | `AGENTS.md` / `GEMINI.md` are always-active (no frontmatter); discovered by walking up from CWD | Using AGENTS.md as always-on rule |
| Built-in skill: `agy-customizations/docs/skills.md` | 2026-09-09 | Progressive disclosure: only name+description injected by default; full SKILL.md loaded on activation | Keeping SKILL.md files concise |

---

## Library Versions (to be filled when implementation begins)

Entries will be added here when specific library versions are selected.
Format:

| Library | Version | Purpose | Licence | Last audited |
|---------|---------|---------|---------|-------------|
| (none yet — awaiting BUILD_SPEC) | | | | |

---

## Quantum Computing Sources

To be populated when the quantum module is designed in detail.
Expected sources: Qiskit documentation, PennyLane documentation,
original QAOA paper (Farhi et al. 2014), D-Wave QUBO guide, etc.

---

## Problem Domains and Benchmark Sources

To be populated as benchmark problem sets are selected.
Expected: TSPLIB, MIPLIB, QPLIB, SATlib references.

---

## How to Add an Entry

1. Record the source only after actually consulting it.
2. Note the specific date — documentation changes over time.
3. Quote the key finding that influenced a decision.
4. Link the finding to the specific decision it justifies (by decision ID in
   `docs/memory/DECISIONS.md`).
5. Do not copy-paste large documentation excerpts here; summarise the key point.
