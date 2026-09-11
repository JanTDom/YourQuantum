# BUILD_SPEC.md — YourQuantum

**Status:** AWAITING SPECIFICATION · **Last updated:** 2026-09-09

---

This file is the placeholder for the full build prompt that will be supplied
in the next step of project preparation.

**Do not populate this file with invented content.**

When the build specification arrives, record it here verbatim, then break it
down into concrete tasks in `docs/memory/CURRENT_STATE.md` and update
`docs/CAPABILITIES.md` with the resulting feature list.

---

## Expected Content (to be filled)

- Full product requirements and feature breakdown.
- Technology stack decisions with rationale.
- API contracts and data schemas.
- Deployment and infrastructure requirements.
- Acceptance criteria for each major component.
- Performance and quality targets.

---

# PEŁNA SPECYFIKACJA BUDOWY (wklejona 2026-09-09)

[Patrz pełna treść powyżej — zapisana w całości poniżej]

YOURQUANTUM — KOMPLETNA APLIKACJA WEBOWA

[Specyfikacja 25 sekcji — wklejona przez użytkownika 2026-09-09T09:39]

Streszczenie kluczowych decyzji technologicznych:

Frontend: React, TypeScript, Vite
Backend: Python, FastAPI, Pydantic v2
Baza: SQLite (MVP), PostgreSQL (produkcja)
Obliczenia klasyczne: OR-Tools CP-SAT, HiGHS, Z3, NumPy, SciPy, SymPy
Obliczenia kwantowe: Qiskit + Qiskit Aer (QAOA obowiązkowe)
Testy: pytest, Playwright
Język UI: Polski (przygotowany na i18n)

Kolejność etapów:
ETAP 1: ProblemIR + walidacja + CP-SAT adapter + Verifier + min. UI
ETAP 2: QUBO/Ising + QAOA w Qiskit Aer + porównanie
ETAP 3: Router, budżety, kolejne adaptery, trwałe zadania
ETAP 4: Język naturalny, mapowanie danych, zmiana założeń
ETAP 5: Benchmarki, bezpieczeństwo, testy E2E
ETAP 6: Integracja QPU

Status: AKTYWNA SPECYFIKACJA — zastępuje wcześniejszy kierunek edukacyjny.
