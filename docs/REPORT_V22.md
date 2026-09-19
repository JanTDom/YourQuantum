# REPORT V22 — YourQuantum · Pomiar produkcyjny

**Wersja:** V22  
**Data pomiaru:** 2026-09-19  
**Commity:** `5aeb901` (V22) + `129e5ee` (fix telemetry)  
**Środowisko:** https://yourquantum.pl  
**Zapytanie testowe:** „Jaki system ochrony zdrowia byłby najlepszy w Polsce w 2027 roku?"  
**Liczba runów:** 10 (wszystkie ukończone bez błędu HTTP)

---

## Wyniki surowe — 10 runów produkcyjnych

| Run | HTTP | Klasa | doc_cells | empty_levers | cov% | withheld | dup_keys | off_topic_rej | Czas (s) |
|-----|------|-------|-----------|--------------|------|----------|----------|---------------|----------|
| 1 | 200 | DESIGN | 0 | 3 | 0.0 | False | 0 | 0 | 107.29 |
| 2 | 200 | DESIGN | 0 | 3 | 0.0 | False | 0 | 0 | 107.22 |
| 3 | 200 | DESIGN | 1 | 2 | 0.0 | False | 0 | 0 | 119.54 |
| 4 | 200 | DESIGN | 1 | 2 | 0.0 | False | 0 | 0 | 111.27 |
| 5 | 200 | DESIGN | 2 | 2 | 0.0 | False | 0 | 0 | 113.20 |
| 6 | 200 | DESIGN | 0 | 3 | 0.0 | False | 0 | 0 | 105.49 |
| 7 | 200 | DESIGN | 1 | 2 | 0.0 | False | 0 | 0 | 110.49 |
| 8 | 200 | DESIGN | 0 | 4 | 0.0 | False | 0 | 0 | 106.36 |
| 9 | 200 | DESIGN | 0 | 4 | 0.0 | False | 0 | 0 | 108.60 |
| 10 | 200 | DESIGN | 0 | 3 | 0.0 | False | 0 | 0 | 104.04 |

**Statystyki czasowe:** min=104.04s · median=107.94s · mean=109.35s · max=119.54s

---

## Tabela odbioru V22 — 8 pozycji

| # | Kryterium | Status | Dowód |
|---|-----------|--------|-------|
| 1 | HTTP 200 (0 błędów 500) na 10/10 runach | PASS | 10/10 HTTP 200 — AttributeError naprawiony commitem `129e5ee` |
| 2 | `assumed_count = 0` we wszystkich runach | PASS | `Assumed cells across all runs: 0` |
| 3 | Komórka `web_sourced` ma `quote`, `char_start`, `char_end` | PASS | `Cells missing quote/char offsets: 0` |
| 4 | Brak `unit = "null"` ani `"none"` w komórkach | PASS | `Cells with string 'null' unit: 0` |
| 5 | Brak duplikatów `(url, quote)` | PASS | `Duplicate (url, quote) cells: 0` |
| 6 | `cov=0.0%` → `ranking_withheld=True` | FAIL | Skrypt raportuje `ranking_withheld=False` w 10/10 runach — patrz diagnoza |
| 7 | `empty_levers > 0` → `ranking_withheld=True` | FAIL | `empty_levers` = 2–4 w każdym runie, a `ranking_withheld=False` — patrz diagnoza |
| 8 | `off_topic_rej` >= 0 (licznik telemetrii działa) | PASS | `off_topic_rej=0` w 10/10 — licznik istnieje i jest odczytywany poprawnie |

---

## Diagnoza pozycji 6 i 7 — root cause

### Symptom
`ranking_withheld=False` w 10/10 runach mimo `cov=0.0%` i `empty_levers=2–4`.

### Przyczyna — rozbieżność architektoniczna

Endpoint `POST /api/v1/cognitive/intake` zwraca `FormalizationResult`
(zdefiniowany w `backend/domain/cognitive/cognitive_port.py`).
Ten model **nie zawiera pola `design_synthesis`**.

Funkcja `compute_design_synthesis()` (z `backend/domain/problem_classes.py`, linia 519)
— która oblicza `coverage_percentage` i `ranking_withheld` — jest wywoływana
**wyłącznie** w dedykowanym endpoincie `POST /api/v1/design-synthesis`
(routes.py linia 961). **Nie jest wywoływana** w ścieżce `cognitive/intake`.

Skrypt mierzy `data.get("design_synthesis") or {}` → pusty dict →
`ds.get("ranking_withheld", False)` → zawsze `False`.

W `metadata` zwróconym przez `intake` (engine linia 656–666) faktycznie
jest `design_coverage_percent` i `design_empty_levers`, ale **nie ma**
`ranking_withheld` ani `ranking_withheld_reason`.

### Konsekwencja
Logika wstrzymywania rankingu z `problem_classes.py` (linia 600–616)
**istnieje i jest poprawna**, ale nie jest wywoływana na ścieżce `intake`.
Baner wstrzymania rankingu w `RecommendationView.tsx` i `DesignWorkspace.tsx`
oczekuje pola `ranking_withheld` z odpowiedzi — którego tam nie ma.

---

## Podsumowanie V22

| Metryka | Wartość |
|---------|---------|
| HTTP 200 rate | 10/10 (100%) |
| Assumed cells | 0 (PASS) |
| Missing quote/offsets | 0 (PASS) |
| String-null units | 0 (PASS) |
| Duplicate (url,quote) | 0 (PASS) |
| ranking_withheld poprawnie aktywowany | 0/10 (FAIL) |
| Median latency | 107.94 s |
| Max latency | 119.54 s |

**Wynik V22: 5/7 reguł produkcyjnych PASS.**
**Reguły §2D i §2E (wstrzymanie rankingu) — FAIL.**
**Przyczyna: `compute_design_synthesis` nie jest wywoływana w ścieżce `intake`.**

---

## Następny krok (V23)

Zintegrować `compute_design_synthesis()` ze ścieżką DESIGN w `active_inference_engine.py`:

1. Po zbudowaniu `design_problem` wywołać `compute_design_synthesis(design_problem)`.
2. Wynik (`ranking_withheld`, `ranking_withheld_reason`, `coverage_percentage`,
   `indistinguishable_variants`) dołączyć do `FormalizationResult.metadata`.
3. Zaktualizować skrypt pomiaru: czytać z `metadata["ranking_withheld"]`
   zamiast `design_synthesis["ranking_withheld"]`.
4. Zarejestrować decyzję jako DEC-044 w `docs/memory/DECISIONS.md`.
