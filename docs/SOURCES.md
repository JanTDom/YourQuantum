# SOURCES.md — Official Sources, Library Versions, Decision Justifications

**Status:** ACTIVE & VERIFIED · **Last updated:** 2026-09-13 (Phase I Verification)

This file records every external source, library version, and API consulted and verified in code.
Each entry states: what was checked, when, the exact version, and which decision it justifies.

---

## Verified Library Versions (Environment: Python 3.12.14 / Node v20)

| Library | Version | Purpose | Licence | Last audited | Justifies |
|---------|---------|---------|---------|-------------|-----------|
| `ortools` (Google) | 9.15.6755 | Discrete MIP and CP-SAT exact solving | Apache-2.0 | 2026-09-13 | DEC-004, DEC-019 (Primary exact discrete solver) |
| `scipy` | 1.15.2 | HiGHS LP continuous solver, dual certificates | BSD-3-Clause | 2026-09-13 | DEC-013, DEC-018 (Continuous & dual relaxation) |
| `qiskit` | 1.4.2 | Quantum circuit composition, operators | Apache-2.0 | 2026-09-13 | DEC-003, DEC-019 (Quantum Core foundation) |
| `qiskit-aer` | 0.17.2 | AerSimulator CPU simulation with noise models | Apache-2.0 | 2026-09-13 | DEC-019 (CPU quantum simulation & Kraus channels) |
| `fastapi` | 0.115.12 | REST API, OpenAPI 3.1, dependency injection | MIT | 2026-09-13 | DEC-001, DEC-020 (Security guards, session tokens) |
| `pydantic` | 2.10.6 | Data boundary validation, Problem IR v0.3 | MIT | 2026-09-13 | DEC-002, DEC-012 (Strict typing, provenance) |
| `httpx` | 0.28.1 | Safe async HTTP client for evidence scraping | BSD-3-Clause | 2026-09-13 | DEC-015 (SafeWebFetcher with SSRF defenses) |
| `beautifulsoup4` | 4.13.3 | HTML parsing and text extraction | MIT | 2026-09-13 | DEC-015 (EvidenceExtractor) |
| `pytest` | 9.1.1 | Test execution framework (157 unit/integration) | MIT | 2026-09-13 | AGENTS.md §7 (100% evidence-first DoD) |
| `react` / `react-dom` | 18.3.1 | Declarative component UI | MIT | 2026-09-13 | DEC-014, DEC-017 (Frontend application) |
| `vite` | 6.4.3 | High-performance build tool & HMR server | MIT | 2026-09-13 | Clean production build in 2.25s |
| `playwright` | 1.50.0 | End-to-end browser verification (CHOICE & DESIGN) | Apache-2.0 | 2026-09-13 | Phase I E2E verification standard |

---

## Scientific & Institutional Evidence Sources

| Source | Date consulted | Key finding | Justifies |
|--------|---------------|-------------|-----------|
| GUS (Główny Urząd Statystyczny) | 2026-09-13 | Podstawy statystyczne ochrony zdrowia i wynagrodzeń w Polsce | DEC-015, DEC-016 (Healthcare fixture & salary benchmarks) |
| NFZ (Narodowy Fundusz Zdrowia) | 2026-09-13 | Struktura kosztów hospitalizacji i świadczeń gwarantowanych | DEC-016 (Multi-lever healthcare reform fixture) |
| Farhi et al. (2014) *A Quantum Approximate Optimization Algorithm* | 2026-09-13 | Alternating operator ansatz $e^{-i \beta H_M} e^{-i \gamma H_C}$ | DEC-003, DEC-019 (QAOA ansatz formulation) |
| Lucas (2014) *Ising formulations of many NP problems* | 2026-09-13 | Exact quadratic penalty calibrations for one-hot and knapsack | DEC-003, DEC-019 (Penalty weights & energy gap proofs) |
| WHO Beveridge vs Bismarck Guidelines | 2026-09-13 | Wzorce organizacyjne systemów ochrony zdrowia w Europie | DEC-016 (Multi-lever architectural synthesis taxonomy) |

---

## Antigravity Customisation System

| Source | Date checked | Key finding | Justifies |
|--------|-------------|-------------|-----------|
| Built-in skill: `agy-customizations/SKILL.md` | 2026-09-09 | Skills: `.agents/skills/<name>/SKILL.md` with `name` + `description` frontmatter | Skill directory structure |
| Built-in skill: `agy-customizations/docs/rules.md` | 2026-09-09 | `AGENTS.md` is always-active (no frontmatter); discovered by walking up from CWD | Using AGENTS.md as always-on rule |
| Built-in skill: `agy-customizations/docs/skills.md` | 2026-09-09 | Progressive disclosure: only name+description injected by default; full SKILL.md loaded on activation | Keeping SKILL.md files concise |

---

## Vercel — limity rozmiaru funkcji (sprawdzone 2026-09-13)

Źródła skonsultowane bezpośrednio 2026-09-13:

- https://vercel.com/docs/functions/limitations (strona aktualizowana 2026-08-24) — "For Python functions, the maximum uncompressed size is 500 MB." oraz "Large functions let you deploy uncompressed bundles up to 5 GB. (...) Large functions require fluid compute with Active CPU enabled." Wsparcie runtime'ów: nodejs, bun, python. Włączenie dla istniejącego projektu: zmienna środowiskowa `VERCEL_SUPPORT_LARGE_FUNCTIONS=1`. Nieobsługiwane przy Secure Compute i Static IPs.
- https://vercel.com/changelog/vercel-functions-can-now-be-up-to-5-gb-in-package-size — data zmiany: 29 czerwca 2026.
- https://vercel.com/changelog/python-vercel-functions-bundle-size-limit-increased-to-500mb — podniesienie limitu Pythona z 250 MB do 500 MB.

Limity czasu i pamięci wg tej samej strony dokumentacji: Pro — domyślnie 300 s, maksymalnie 800 s (1800 s w becie); pamięć domyślnie 2 GB / 1 vCPU, maksymalnie 4 GB / 2 vCPU.

**Konsekwencja dla projektu:** uzasadnienie DEC-022 (limit 250 MB jako powód wydzielenia kontenera obliczeniowego) jest nieaktualne od 29.06.2026. Stos obliczeniowy (~650 MB) mieści się w limicie 5 GB. `Dockerfile` i `docker-compose.yml` pozostają jako alternatywa na wypadek, gdyby koszty Active CPU lub limity czasu okazały się nie do przyjęcia — decyzja wymaga pomiaru, nie założeń.
