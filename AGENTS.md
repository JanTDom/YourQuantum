# YOURQUANTUM — PROJECT RULES & MAP

> **Antigravity reads this file automatically at every session.**
> It is the single source of truth for project identity, session protocol, and
> memory pointers. Keep it concise. Full detail lives in the linked documents.

---

## 1. PROJECT IDENTITY

**Product:** YourQuantum
**Mission:** An environment for solving hard problems — not an educational quantum lab.

A user presents a problem in plain language, supplies data, states requirements,
and receives a result backed by real computation, constraint checking, analysis,
or an appropriate proof.

**Core path:**

```
USER PROBLEM
→ UNDERSTANDING & FORMALISATION
→ APPROVED MODEL
→ METHOD SELECTION
→ REAL COMPUTATION
→ INDEPENDENT VERIFICATION
→ RESULT WITH ITS LIMITATIONS
```

New use-cases emerge from composing general mathematical and computational
primitives — not from pre-built industry templates.

---

## 2. QUANTUM PRINCIPLE (non-negotiable)

YourQuantum includes a real quantum-algorithm module:
complex-amplitude representation, state preparation and evolution, operators and
circuits, measurement sampling, variational optimisation, QUBO/Ising compilation,
and QPU connectivity.

Simulating these on CPU/GPU is classical computation. Do not call it a physical
quantum computer.

- Do NOT call a candidate list "superposition".
- Do NOT call weight changes "quantum interference".
- Do NOT call standard simulated annealing "quantum annealing".

When a classical method outperforms the quantum module, give the user the better
result — not a slower computation for the product name's sake.

---

## 3. SESSION START PROTOCOL (mandatory before changing code)

1. Read `docs/memory/INDEX.md` (project map, key rules, links).
2. Read `docs/memory/CURRENT_STATE.md` (what actually works, blockers, next steps).
3. Read `docs/memory/DECISIONS.md` for decisions relevant to the task.
4. Read task-specific docs from `docs/` (e.g., `ARCHITECTURE.md`, `QUANTUM_CORE.md`).
5. Select only the Skills needed for the task.
6. Define the completion criterion for the current task.
7. Only then change code.

---

## 4. SESSION END PROTOCOL (mandatory after each work stage)

1. Run appropriate tests; record real output and test configuration.
2. Update `docs/memory/CURRENT_STATE.md` with actual state.
3. Record any new decision in `docs/memory/DECISIONS.md`.
4. Record any repeatable lesson in `docs/memory/LESSONS.md`.
5. Review diff; confirm no secrets were committed.
6. Leave one specific next step in `CURRENT_STATE.md`.

---

## 5. CORE SCIENTIFIC RULES (always enforced)

- LLM output is NOT a solver result.
- Simulation is NOT QPU execution.
- A candidate is NOT a proof of optimality.
- A timeout is NOT a proof of infeasibility.
- JSON Schema conformance does NOT prove intent conformance.
- Model-optimal result does NOT guarantee real-world success.
- Do NOT promise quantum advantage without benchmark data.

---

## 6. SECURITY RULES (always enforced)

- User data and LLM outputs are untrusted at the boundary.
- No secrets in project memory, docs, or rules.
- No execution of arbitrary code from prompts.
- No paid external tasks without explicit user consent.
- No automatic weakening of security constraints.

---

## 7. EVIDENCE RULE (always enforced)

A feature is done only after real verification.
Build output, a screenshot, and a model's assurance do NOT substitute for a test.

---

## 8. DOCUMENT MAP

| File | Purpose |
|------|---------|
| `docs/memory/INDEX.md` | Short project map — read first every session |
| `docs/memory/CURRENT_STATE.md` | What works, what doesn't, next step |
| `docs/memory/DECISIONS.md` | Key architectural and product decisions |
| `docs/memory/LESSONS.md` | Repeatable lessons with evidence |
| `docs/PRODUCT.md` | Goal, audience, promise, scope, exclusions |
| `docs/BUILD_SPEC.md` | Full build prompt (awaiting specification) |
| `docs/BUILD_SPEC_V2.md` | V2 remediation & development prompt (2026-09-13) |
| `docs/ARCHITECTURE.md` | System architecture and component contracts |
| `docs/PROBLEM_IR.md` | Versioned problem intermediate representation |
| `docs/QUANTUM_CORE.md` | Quantum module design and execution path |
| `docs/VERIFICATION.md` | What can be verified and how |
| `docs/BENCHMARK_PROTOCOL.md` | Quality, cost, and quantum-contribution metrics |
| `docs/SECURITY.md` | Trust boundaries, isolation, secrets, limits |
| `docs/CAPABILITIES.md` | Feature registry: PLANNED / IMPLEMENTED / TESTED / DEPLOYED |
| `docs/SOURCES.md` | Official sources, dates, library versions, decisions justified |
| `benchmarks/README.md` | Benchmark suite entry point |

---

## 9. SKILLS MAP

Skills live in `.agents/skills/`. Activate only those needed for the task.

| Skill | Responsibility |
|-------|---------------|
| `yq-context` | Context recovery and doc/code alignment |
| `yq-formalizer` | Translate user language → versioned problem model |
| `yq-architect` | Engine architecture, contracts, versioning, worker, capability registry |
| `yq-classical-solvers` | Constraint/optimisation/logic/symbolic solver selection |
| `yq-quantum-core` | QUBO/Ising, QAOA, circuit simulation, sampling, QPU integration |
| `yq-routing-and-decomposition` | Method routing, problem decomposition, compute budgets |
| `yq-verifier` | Independent result verification, constraint checking, certificates |
| `yq-benchmark` | Comparative benchmarking with shared data and success criteria |
| `yq-data-io` | Safe import, data mapping, units, missing data, versioning, export |
| `yq-product-engineering` | Problem-focused frontend/backend; full browser path verification |
| `yq-security` | Client isolation, permissions, files, secrets, resource limits |
| `yq-learning` | Persisting verified lessons, updating context memory |
| **PREMIUM FRONTEND SKILLS** | |
| `creative-web-craftsmanship` | Awwwards/FWA-level visual design, bespoke layouts, OKLCH, Scroll-driven animations, View Transitions, Container Queries, micro-interactions |
| `editorial-typography-and-design-systems` | Anti-generic art direction, modular type scales, perceptual color (OKLCH), design tokens, bento grids, WCAG contrast |
| `creative-motion-and-physics` | Spring physics, motion choreography, staggered entrances, GPU-accelerated transitions, View Transitions API, prefers-reduced-motion |
| `core-web-vitals-and-performance` | LCP/INP/CLS targets, bundle tree-shaking, code splitting, virtualized lists, memory leak prevention |
| `product-storytelling-and-copy` | UX copywriting, zero-placeholder policy, action-oriented microcopy, empty states, error messaging |
| `modern-web-guidance` | CLI search tool for authoritative browser-native best-practice guides; run FIRST for all HTML/CSS/JS tasks |

---

## 10. WHAT THIS PROJECT IS NOT

- Not an educational quantum laboratory.
- Not a collection of industry-template solvers.
- Not a system that guarantees solutions to all possible problems.
- Not a system where quantum is used on every task regardless of merit.
