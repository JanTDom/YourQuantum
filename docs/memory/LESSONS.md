# LESSONS.md — Repeatable Lessons with Evidence

**Last updated:** 2026-09-09

Each entry: problem → cause → evidence → fix → future rule.
Status: CONFIRMED | PROPOSED | SUPERSEDED

Only repeatable lessons are recorded here. One-off debugging notes go in
`CURRENT_STATE.md`. Do not copy conversation transcripts here.

---

## LESSON-001 — Verify Antigravity rule format before writing rules

**Status:** CONFIRMED
**Date:** 2026-09-09

**Problem:** Risk of writing rule files with frontmatter triggers (e.g.,
`trigger: always_on`) that are not supported in the installed version,
resulting in silently inactive rules.

**Cause:** Antigravity documentation describes multiple customisation types
(rules, skills, plugins, hooks). The supported activation mechanism for
standalone rule files differs from what one might assume from reading skills docs.

**Evidence:** `agy-customizations/docs/rules.md` (verified 2026-09-09) states:
"Standalone `GEMINI.md` / `AGENTS.md` files do not support frontmatter and are
always active for their directory scope." No `always_on` frontmatter trigger
for standalone `.md` rule files is documented.

**Fix:** Use `AGENTS.md` at the project root for always-active rules. Do not
write rule files with unverified frontmatter.

**Future rule:** Before writing any Antigravity configuration (rules, skills,
hooks), read the relevant documentation in `agy-customizations/docs/` and
record the source + date in `docs/SOURCES.md`.

---

## LESSON-002 — Do not conflate "file created" with "configuration active"

**Status:** CONFIRMED
**Date:** 2026-09-09

**Problem:** Creating configuration files does not guarantee the agent
will discover and apply them. Discovery depends on the file's location relative
to the working directory and the specific Antigravity discovery rules.

**Cause:** Antigravity walks from the current working directory up to the
repository root. Files placed outside this path, or in unsupported locations,
are silently ignored.

**Evidence:** `agy-customizations/SKILL.md` documents the discovery walk:
".agents/ (or .agent/, _agents/, _agent/) at the root of your project."
AGENTS.md must be at the repository root or a parent directory of the CWD.

**Fix:** Always place `AGENTS.md` at the repository root. Verify the working
directory assumption when starting a session in a subdirectory.

**Future rule:** After creating configuration, record its expected discovery
path. When starting a session in a subdirectory, verify that the root AGENTS.md
is in an ancestor directory.

## 2026-09-09 — Implementation Session

### L-007: dataclasses.asdict() fails with datetime fields in JSON columns
`dataclasses.asdict()` includes Python `datetime` objects verbatim. SQLAlchemy's JSON column serialiser cannot handle them. Solution: walk the dict recursively and convert `datetime → .isoformat()`, `Enum → .value`. Created `_solver_result_to_json()` helper in runner.py.

### L-008: Variable IDs must match objective_coefficients keys
When building ProblemIR from user request, the variable `id` must equal the key used in `objective_coefficients`. Prefix `v_` on IDs caused CP-SAT to silently build an empty objective (evaluator returned `None`), resulting in objective=0. Rule: use the user-supplied name directly as the variable ID.

### L-009: CP-SAT linear expression builder needs `mul` support for weighted sums
The `sum(coeff * var)` pattern goes through `mul` nodes. Without `mul` handling in `_build_linear_expr`, the entire objective evaluates to `None` and CP-SAT runs an unconstrained trivial solve (all-zero). Always implement `mul` with const×var detection.

### L-010: SQLite readonly error after rm+touch in sandbox
After `rm data/yourquantum.db && touch data/yourquantum.db`, the file had write permission but the server process held a stale connection. Fix: kill and restart server after resetting DB. Better: don't delete the DB file during development; run `init_db()` once.

### L-011: npm create vite -- needs TTY for template selection
`npm create vite@latest` with `--yes` or `--` flags cancels with "Operation cancelled" in non-TTY shell. Solution: create package.json + tsconfig + index.html + vite.config.ts manually without scaffold command.

### L-012: system Python (3.14) in sandbox vs .venv (3.12)
Shell commands like `python3 -c "..."` use system Python 3.14. All test scripts must use `.venv/bin/python3` explicitly. Also: json pipe through system python3 fails differently (backslash escaping in description field). Use .venv/bin/python3 for all inline python in shell scripts.

### L-013: SQLite ALTER TABLE auto-migration in init_db
When adding new columns (e.g. `publication_status`) to SQLAlchemy models during development, `Base.metadata.create_all` does NOT alter existing SQLite tables. Solution: In `init_db()`, execute lightweight `ALTER TABLE ... ADD COLUMN` inside try/except blocks to ensure zero downtime and prevent `OperationalError: table has no column named ...`.

### L-014: Process hygiene and daemon task management
Leaving long-running dev servers (`uvicorn`, `vite`) as unmanaged background tasks causes resource drain, port conflicts, and user annoyance. Always explicitly inspect running tasks with `manage_task list` and terminate them cleanly with `manage_task kill` at the end of each verification stage.

### L-015: 3D WebGL in React requires ErrorBoundary and 2D fallback to prevent blank white screens
When rendering Three.js / WebGL in React, if WebGL context creation fails or throws without an ErrorBoundary, React 18/19 unmounts the entire application root (`#root`), leaving a completely blank white page ("biała strona"). Always wrap 3D canvases in a resilient React ErrorBoundary, detect WebGL capabilities beforehand, provide a Canvas 2D fallback, protect aspect ratio calculations against 0-height containers, and expose clear return/exit navigation actions.

### L-016: Async pytest fixtures require @pytest_asyncio.fixture
When declaring asynchronous fixtures (`async def async_test_session()`) in modern `pytest-asyncio` (v0.24+ / 1.4+), standard `@pytest.fixture` fails during fixture setup with deprecation/unsupported errors. Always explicitly import `pytest_asyncio` and decorate async test fixtures with `@pytest_asyncio.fixture`.

### L-017: Optional array fields in Pydantic/TypeScript require optional chaining in JSX
When rendering lists from API responses where fields like `inequality_constraints` or `binary_variables` are optional, doing `formalized.inequality_constraints.map(...)` throws `Cannot read properties of undefined (reading 'map')` and crashes the React tree. Always use optional chaining `formalized.inequality_constraints?.map(...)` and fallback counts `(formalized.inequality_constraints?.length || 0)`.

### L-018: Full E2E mocking in Playwright requires intercepting Job Status as well as Result
When testing asynchronous solver workflows in Playwright where the frontend polls `GET /api/v1/jobs/:id` until `execution_status === 'COMPLETED'` before calling `GET /api/v1/jobs/:id/result`, mocking only the result endpoint causes Vite's dev server proxy to attempt forwarding the status check to backend port 8000 (raising ECONNREFUSED). Always mock the job creation, polling status, and result endpoints as a complete lifecycle.

### L-019: macOS Sandboxing Mach port rendezvous in Playwright Chrome
Spawning Google Chrome inside the sandboxed terminal subshell on macOS triggers Mach port bootstrap errors (`bootstrap_check_in com.google.Chrome.MachPortRendezvousServer: Permission denied`). Browser automation tasks must be executed with `BypassSandbox: true` to permit operating system IPC with the display and window server.

### L-020: Indirect prompt injection boundary escaping
When ingesting third-party web content into LLM reasoning contexts, adversaries may plant boundary reset tokens (such as `<<<END_UNTRUSTED_WEB_CONTENT>>>`) to break out of delimiters. Always sanitize untrusted input by replacing delimiter patterns with escaped strings and applying regex filters to strip imperative adversarial commands ("ignore previous instructions", "set value=0").

### L-021: Prawidłowa matematyka użyta na zmyślonych danych wejściowych daje wynik, który wygląda na zmierzony. Reguła Borna zastosowana do liczb wymyślonych przez LLM nie czyni ich pomiarem
W DEC-031 mechanizm błędu polegał na tym, że model językowy generował subiektywne wagi, wiarygodności i wpływy przesłanek, po czym funkcja pakowała te liczby w wektor amplitud `qc.initialize` w Qiskit AerSimulator i odczytywała prawdopodobieństwa z modułu kwadratu amplitud ($|\psi_i|^2$). Mimo że implementacja reguły Borna była poprawna algebraicznie, symulator kwantowy nie wykonywał żadnej fizycznej transformacji ani interferencji (obwód miał 0 bramek), a wynik był tożsamy ze zwykłym softmaxem z $\beta=1.8$. Użycie aparatury mechaniki kwantowej na zmyślonych liczbach wejściowych stwarzało iluzję obiektywnego fizycznego pomiaru zjawiska w świecie rzeczywistym. Zasada na przyszłość: Aparat matematyczny i algorytmy kwantowe mają sens wyłącznie na realnych problemach kombinatorycznych z jawnymi ograniczeniami lub na rzetelnie zmierzonych danych z precyzyjnie udokumentowanym pochodzeniem (`provenance`). Liczby pochodzące od LLM lub zmyślonych stałych w kodzie nigdy nie mogą być prezentowane użytkownikowi jako zmierzone prawdopodobieństwa przyszłych zdarzeń.
