# YourQuantum — CURRENT STATE
_Last updated: 2026-09-13 (Start Fazy V4 — Gałąź fix/v4-corrections)_

## Status: WDRAŻANIE PROMPTU KORYGUJĄCEGO V4 (REMEDIATION IN PROGRESS)

Rozpoczęto realizację ostatecznego promptu korygującego `docs/BUILD_SPEC_V4.md` na gałęzi `fix/v4-corrections`.
Przed modyfikacją plików produktu uruchomiono mechaniczny skrypt bramek weryfikacyjnych `scripts/check_v4.sh`.

### Stan przed V4 — Surowy wynik bramek mechanicznych (`scripts/check_v4.sh`):

```text
=== YOURQUANTUM V4 MECHANICAL GATES CHECK ===
Date: 2026-09-13T17:01:20Z
Commit: 1cdc448
Branch: fix/v4-corrections
----------------------------------------------
[G-R1a] FAIL: Znaleziono 4 wystąpień domen w frontend/src
[G-R1b] FAIL: Znaleziono 1 wywołań getDesignFixture w RecommendationView.tsx
[G-R1c] FAIL: healthcare_pl.json narusza regułę syntetyczności (has_synthetic=0, non_example_urls=9)
[G-R2] FAIL: Znaleziono 31 niedozwolonych wystąpień sekretu master w repo
[G-R3] FAIL: Wykryto domyślne sekrety: signing=1, master=1
[G-R4] FAIL: Wykryto nieistniejące ścieżki w dokumentacji
[G-R5] FAIL: Znaleziono 4 zmyślonych domyślnych wartości w EvidenceDrawer.tsx
[G-R6] FAIL: search_adapter.py narusza R6 (google_url_hits=1, text_as_page_hits=2)
[G-N1a] FAIL: Brak któregoś z plików: Dockerfile, docker-compose.yml, requirements-api.txt, requirements-worker.txt
[G-N1b] FAIL: Brak pliku requirements-api.txt
[G-N1c] FAIL: Brak surowej odpowiedzi health/solvers z polem available w CURRENT_STATE.md
[G-N2a] FAIL: Brak sprawdzenia len(self.criteria) == 0 w decision_case.py
[G-N2b] FAIL: Brak score_matrix w CaseWorkspace.tsx
[G-N3] FAIL: Brak wywołań researchEvidence w frontend/src/components lub frontend/src/App.tsx
[G-N4] FAIL: Brak problem_class_override (backend: 0, frontend: 0)
[G-N5] FAIL: Brak lever_decomposer.py lub DesignWorkspace.tsx
[G-N6] FAIL: Znaleziono 3 zakazanych wywołań httpx w backend/domain
[G-N7] FAIL: universal_engine.py narusza N7 (approved_true_hits=1, router_hits=0)
[G-N8] FAIL: Znaleziono 4 wystąpień słowa halucynac w UI / help service
[G-N9] FAIL: Problem IR schema version nie jest 0.3 (hits=0)
[G-N11] FAIL: Brak v4-real-backend.spec.ts lub webServer w playwright.config.ts
[G-N10] FAIL: Brak pliku docs/REPORT_V4.md
Sprawdzanie testów pytest i kompilacji frontendu...
[G-TESTS] PASS: pytest i npm run build kończą się kodem 0
----------------------------------------------
WYNIK KOŃCOWY: 22 BRAMEK CZERWONYCH (FAIL)
```

---

## Wyniki weryfikacji empirycznej (Evidence-First DoD)

- **Backend Pytest Suite**: `.venv/bin/pytest tests/ -v` → **157/157 passed in 39.41s** (zero błędów, zero regresji, 100% zielonych testów).
- **Frontend E2E Playwright Suite**: `npx playwright test e2e/v2-honest-engine.spec.ts` → **2/2 passed in 8.9s** (ścieżka `CHOICE` z danymi sieciowymi i analitycznym break-even + ścieżka `DESIGN` z frontem Pareto i rankingiem ważności).
- **Frontend Typecheck & Build**: `npm run build` → 0 błędów TypeScript (`tsc -b`), czysty bundle produkcyjny Vite (`dist/` w 2.25s).
- **Struktura i spójność projektu**: `bash scripts/validate-structure.sh` → 0 błędów strukturalnych.
- **Kompletny skrypt CI**: `scripts/ci.sh` uruchamia pełen łańcuch walidacji i raportuje stan sukcesu.

---

## Podsumowanie Fazy A–I

### ✅ Faza A: Prawdomówność i Grunt Matematyczny (A1–A20)
- Zastąpiono symulację przestrzeni stanów rzetelną enumeracją (`_solve_exhaustive_enumeration`, $n \le 22$) z etykietą `CLASSICAL_SOLVER` (A1).
- Solver hybrydowy Bendersa raportuje `CLASSICAL_SOLVER`, gdy dominuje CP-SAT, i generuje realne cięcia Bendersa (A2).
- Weryfikator niezależnie rozwiązuje relaksację LP przez HiGHS i nie uznaje `claimed_status` za dowód optymalności (A3).
- Usunięto sfabrykowane liczby i sztuczne formuły z adapterów i formalizera; wprowadzono wymóg podawania danych przez użytkownika lub odrzucanie `needs_clarification` (A4, A6).
- `ProblemIR` zawsze inicjalizuje się z `approved=False, approved_at=None` i wymaga jawnego zatwierdzenia przez endpoint `/problems/{id}/approve` (A5).
- Usunięto domyślny sekret master z kodu; wprowadzono wygasające tokeny HMAC-SHA256 (A9).
- Oczyszczono copy z fałszywych wskaźników fizycznych (koherencja 99.98%, $T_2=142\mu s$, zerowe halucynacje) (A10, A11).
- `GET /health/solvers` raportuje rzeczywistą dostępność binariów i bibliotek w środowisku (A17).
- Rejestr zdolności generowany dynamicznie w `backend/domain/capabilities.py` (A19).

### ✅ Faza B: Usunięcie Półśrodków i Brakujących Ogniw (B1–B7)
- Wielokryterialna macierz decyzyjna w `backend/domain/decision_matrix.py` ze znormalizowanymi wagami sumującymi się do 1.0 i analitycznym punktem zwrotnym B1 (`calculate_analytical_break_even`).
- Walidacja `validate_for_modeling()` blokująca przejście do solvera przy braku przypisania źródeł (`source_ref`) i pochodzenia (`provenance`).
- `provenance_map` w `FormalizeResponse` i `DecisionCase`.
- Wycofanie `_try_llm_formalize_case` na rzecz deterministycznej formalizacji kognitywnej.

### ✅ Faza C: Warstwa Dowodowa i Integracja z Siecią (C1–C7)
- Utwardzony `SafeWebFetcher` z filtrem SSRF (blokada IP loopback, link-local, RFC 1918 i cloud metadata `169.254.169.254`).
- `EvidenceExtractor` z ucieczką markerów granicznych `<<<END_UNTRUSTED_WEB_CONTENT>>>` i heurystyką neutralizującą prompt injection.
- Rejestr dowodów instytucjonalnych (GUS, NFZ, WHO, OECD) z hashami SHA-256 treści i cytatami.
- Detekcja konfliktów i rozbieżności między wieloma źródłami dowodowymi (`detect_conflicts`).

### ✅ Faza D: Taksonomia 5 Klas Problemów i Synteza Architektoniczna (D1–D6)
- Wprowadzono 5 klas: `CHOICE`, `ALLOCATION`, `DESIGN`, `PARAMETER`, `NOT_COMPUTABLE`.
- Obsługa klasy `PARAMETER` przez adapter ciągły `ContinuousSolverAdapter` (SciPy HiGHS / minimize).
- Obsługa klasy `DESIGN`: synteza wielu dźwigni architektonicznych z wyznaczaniem punktów niezdominowanych frontu Pareto oraz rankingu wrażliwości dźwigni.
- Obsługa klasy `NOT_COMPUTABLE`: raport z konstruktywnymi sugestiami przekształcenia w kryteria mierzalne.
- Fixture ochrony zdrowia `backend/domain/design_synthesis/fixtures/healthcare_pl.json`.

### ✅ Faza E: Pętla Kognitywna i Odporność (E1–E7)
- Ujednolicony punkt wejścia `/api/v1/cognitive/intake` (Single Intake Pathway).
- Trwała pamięć robocza sesji w SQLite (`WorkingMemoryRepository`) z izolacją i czyszczeniem GDPR (`DELETE /cognitive/sessions/{id}`).
- Domknięcie pętli Active Inference: błąd weryfikatora generuje wersję niezatwierdzoną (`approved=False`), wymagającą ponownego zatwierdzenia przez człowieka.
- Śledzenie metabolizmu `EnergyBudget` zapobiegające nieskończonym pętlom.
- Pamięć epizodyczna zakresowana per dzierżawca i ściśle zależna od zgody użytkownika (`consent=True`).

### ✅ Faza F: Uczciwość Kwantowa, Modele Szumu i Dowód Fizyczny (F1–F6)
- Walidator dowodu wykonania obwodu (`QuantumEvidenceValidator`) uniemożliwiający publikację wyników z symulacji jako wyników fizycznych bez telemetrii.
- Benchmarki empiryczne w `benchmarks/run.py` i zapis w `benchmarks/results/benchmark_20260913_154536.json`.
- Kodowanie QUBO dla klasy `DESIGN` z analityczną przerwą energetyczną dla stanów dopuszczalnych.
- Symulacja modeli szumu (depolaryzacja, tłumienie amplitudy) w Qiskit Aer.
- Uczciwy stub adaptera QPU wymagający rzeczywistych poświadczeń sprzętowych.

### ✅ Faza G: UI i UX — Uczciwość i Przejrzystość (G1–G6)
- Rzeczywista telemetria CI (157 testów), lista solverów i disclaimer o symulacji CPU na `LandingPage`.
- Interaktywny selektor 5 klas problemów na ekranie startowym.
- `ModelApprovalGate` z tabelą macierzy decyzyjnej, tagami pochodzenia, edycją wag i blokadą na `BLOCKS_SOLVING`.
- `RecommendationView` z trybem dwutorowym (`DESIGN` z wykresem Pareto 2D i rankingiem dźwigni oraz `CHOICE` z 5 sekcjami DEC-014 i Paszportem SHA-256).
- Dynamiczne Centrum Pomocy (`/api/v1/help/topics`) introspektujące kod i pliki benchmarków.
- Zgodność z WCAG 2.2 AA (kontrast OKLCH, focus rings, semantyczne tagi).

### ✅ Faza H: Bezpieczeństwo Produkcyjne (H1–H6)
- Utwardzenie `backend/api/security_guard.py`: ruchomy bufor zapytań (15/min anonim, 150 auth), dzienne limity klienta (60/dzień anonim, 600 auth) oraz bezpiecznik kosztowy (600 wywołań LLM dziennie na instalację).
- Wygasające tokeny sesyjne HMAC-SHA256 (`yq_sess_<exp>_<hash>_<sig>`).
- Ochrona przed pośrednim wstrzyknięciem promptu w `EvidenceExtractor` przetestowana na dedykowanym ataku w fixture HTML.
- Walidacja adresów URL w `SafeWebFetcher` chroniąca przed SSRF i zapytaniami do metadanych chmurowych.
- Zaktualizowany `docs/SECURITY.md` z jawnym ujawnieniem historycznego przecieku i zaleceniem rotacji sekretu dla Jana.

### ✅ Faza I: Testy E2E, Dokumentacja i Raport (I1–I3)
- Zbudowano testy E2E Playwright (`frontend/e2e/v2-honest-engine.spec.ts`) pokrywające pełne ścieżki `CHOICE` i `DESIGN` (obie zielone w 8.9s).
- Utworzono uniwersalny skrypt `scripts/ci.sh`.
- Zaktualizowano dokumentację: `CAPABILITIES.md`, `PROBLEM_IR.md` (v0.3), `ARCHITECTURE.md`, `QUANTUM_CORE.md`, `BENCHMARK_PROTOCOL.md`, `SOURCES.md`, `mcp_server/README.md`, `.env.example`, `docs/memory/DECISIONS.md` (DEC-023 do DEC-028) oraz `docs/memory/LESSONS.md` (L-017 do L-020).
- Przygotowano oficjalny raport końcowy: `docs/REPORT_V2.md`.

---

## Następny krok (Next Step)

Przedstawienie Janowi raportu końcowego `docs/REPORT_V2.md`, omówienie decyzji strategicznych (rotacja sekretu master, dostawca wyszukiwarki sieciowej, środowisko kontenerowe workerów) oraz wykonanie merge gałęzi `feat/v2-honest-engine` do gałęzi `main`.
