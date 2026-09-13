# INDEX.md — YourQuantum Project Map

**Last updated:** 2026-09-09 · **Stage:** Context preparation complete

This is the first document to read at the start of every session.
Maximum ~120 lines. Full detail is in the linked documents.

---

## Product in One Sentence

YourQuantum solves hard problems by formalising user input, routing to the
best classical or quantum method, computing real results, and verifying them
independently — not by wrapping an LLM response in quantum branding.

---

## Current Stage

**PREPARATION COMPLETE — AWAITING BUILD SPEC**

Memory, rules, skills, and documentation scaffolding are in place.
No application code exists yet.
Next action: paste the build specification prompt into `docs/BUILD_SPEC.md`.

---

## Non-Negotiable Rules (always enforced)

1. LLM output ≠ solver result.
2. Simulation ≠ QPU execution.
3. Candidate ≠ proof of optimality.
4. Timeout ≠ proof of infeasibility.
5. No secrets anywhere in project files.
6. No arbitrary code execution from prompts.
7. A feature is done only after a real test passes.
8. Quantum is used when it helps; classical wins when it's better.

---

## Document Map (quick reference)

| Document | Purpose |
|----------|---------|
| `AGENTS.md` (root) | Always-active rules + full document/skill map |
| `docs/memory/CURRENT_STATE.md` | **Read 2nd every session** — what works, blockers |
| `docs/memory/DECISIONS.md` | Key decisions with rationale and alternatives |
| `docs/memory/LESSONS.md` | Repeatable lessons with evidence |
| `docs/PRODUCT.md` | Product goal, audience, scope, exclusions |
| `docs/BUILD_SPEC.md` | Full build prompt (awaiting) |
| `docs/BUILD_SPEC_V2.md` | V2 remediation & development prompt (2026-09-13) |
| `docs/ARCHITECTURE.md` | 5-layer architecture, component contracts |
| `docs/PROBLEM_IR.md` | Versioned problem representation schema (v0.3) |
| `docs/QUANTUM_CORE.md` | Quantum module design and execution path |
| `docs/VERIFICATION.md` | What can be verified and how |
| `docs/BENCHMARK_PROTOCOL.md` | How benchmarks are run and reported |
| `docs/SECURITY.md` | Trust boundaries, isolation, secrets, limits |
| `docs/CAPABILITIES.md` | Feature registry: PLANNED/IMPLEMENTED/TESTED/DEPLOYED |
| `docs/SOURCES.md` | Sources consulted, dates, versions, decisions justified |
| `benchmarks/README.md` | Benchmark suite entry point |

---

## Skills (activate only what the task needs)

| Skill | When to use |
|-------|------------|
| `yq-context` | Session start, doc/code drift, after a gap |
| `yq-formalizer` | Translating user input into Problem IR |
| `yq-architect` | Engine design, contracts, capability registry |
| `yq-classical-solvers` | Selecting/integrating classical solvers |
| `yq-quantum-core` | QUBO/Ising, circuits, sampling, QPU |
| `yq-routing-and-decomposition` | Method routing, decomposition, budgets |
| `yq-verifier` | Result verification, constraint checking |
| `yq-benchmark` | Running and recording benchmarks |
| `yq-data-io` | Data import/export, units, missing data |
| `yq-product-engineering` | Frontend/backend product work |
| `yq-security` | Security review, isolation, permissions |
| `yq-learning` | Persisting lessons, updating memory docs |

---

## Session Protocol Summary

**START:** Read INDEX → CURRENT_STATE → DECISIONS (relevant ones) →
task-specific docs → select skills → define completion criterion → then code.

**END:** Run tests → update CURRENT_STATE → record decision/lesson if any →
check diff for secrets → leave one specific next step.
