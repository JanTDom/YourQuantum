# YOURQUANTUM — RAPORT V12: PRZESŁANKI I WAGI MAJĄ POCHODZIĆ Z DOKUMENTÓW, NIE Z MODELU
Data: 2026-09-17 · Gałąź: `feat/v12-documented-weights` (scalone do `main`) · Autor: Jan Domaniewski & Antigravity

---

## 1. Zestawienie wykonania punktów zlecenia V12

| Punkt | Zadanie | Status | Zmienione pliki | Test dowodowy |
|---|---|---|---|---|
| **Punkt 1** | Podniesienie timeoutu wyszukiwania Gemini do 30.0s, raportowanie zdolności pobierania (`can_fetch_content: True`), ignorowanie URL przekierowujących (`google.com/url`), dokumentacja w `docs/SOURCES.md` | **WDROŻONE** | `backend/infrastructure/web_research/search_adapter.py`, `docs/SOURCES.md` | `tests/test_scenario_web_sourcing.py` |
| **Punkt 2** | `config/source_classes.json` (v1.0.0, 4 klasy domen), moduł `backend/domain/evidence/evidence_weighting.py` z formułą wag $W$, integracja w `backend/domain/cognitive/active_inference_engine.py` | **WDROŻONE** | `config/source_classes.json`, `backend/domain/evidence/evidence_weighting.py`, `backend/domain/cognitive/active_inference_engine.py` | `tests/test_scenario_web_sourcing.py`, `tests/unit/test_scenario_weighting.py` |
| **Punkt 3** | Transparentny baner uczciwości w UI przy braku źródeł sieciowych (`web_quotes_verified === 0`) | **WDROŻONE PRODUKCYJNIE** | `frontend/src/components/RecommendationView.tsx` | Zbudowano `frontend/dist/assets/index-CwhrjICi.js`, wdrożono produkcyjnie na Vercel CLI (`https://yourquantum.pl`), zweryfikowano `curl` |
| **Punkt 4** | Pola `weight_breakdown` i `weight_justification` w schemacie frontendu, rozbicie wag i uzasadnienie w `WebEvidenceNotice` | **WDROŻONE PRODUKCYJNIE** | `frontend/src/api.ts`, `frontend/src/components/RecommendationView.tsx` | Kompilacja `npm run build`, weryfikacja wdrożenia produkcyjnego Vercel |
| **Punkt 5** | Rozszerzenie `scripts/check_doc_citations.py` o `docs/REPORT_V11.md` i `docs/REPORT_V12.md`, odnotowanie `DEC-037`, aktualizacja `docs/memory/LESSONS.md` i `docs/memory/CURRENT_STATE.md` | **WDROŻONE** | `scripts/check_doc_citations.py`, `docs/memory/DECISIONS.md`, `docs/memory/LESSONS.md`, `docs/memory/CURRENT_STATE.md`, `docs/REPORT_V12.md` | `python3 scripts/check_doc_citations.py` (PASS) |

---

## 2. Architektura i algorytm wyliczania wag (DEC-037)

Waga przesłanki pochodzenia `web_sourced` nie jest zmyślana przez model językowy, lecz obliczana deterministycznie na podstawie cech dokumentu:
$$W = 0.30 \cdot S_{\text{corroboration}} + 0.30 \cdot S_{\text{source\_class}} + 0.20 \cdot S_{\text{recency}} + 0.20 \cdot S_{\text{specificity}}$$

Składowe punktacji:
1. **$S_{\text{corroboration}}$**: $\min(1.0, 0.4 + 0.3 \cdot (N - 1))$ dla $N$ niezależnych domen potwierdzających przesłankę.
2. **$S_{\text{source\_class}}$**: ocena klasy domeny z `config/source_classes.json` (Tier 1: 1.0, Tier 2: 0.8, Tier 3: 0.6, Tier 4: 0.4, nieznana: 0.3).
3. **$S_{\text{recency}}$**: świeżość informacji ($1.0$ dla roku bieżącego, spadek o $0.2$ rocznie, minimum $0.2$).
4. **$S_{\text{specificity}}$**: obecność liczb, dat, kwot lub miar w cytacie ($1.0$ przy danych precyzyjnych, $0.5$ przy braku).

Zaimplementowano w `backend/domain/evidence/evidence_weighting.py` oraz `config/source_classes.json`.

---

## 3. Integralność przywołań w dokumentacji (G-DOCS)

Skrypt `scripts/check_doc_citations.py` został rozszerzony o pełną weryfikację raportów V11 i V12.
Wszystkie historyczne i bieżące przywołania linii w kodzie źródłowym oraz ścieżki plików w backtickach przeszły automatyczną kontrolę ze statusem PASS.

---

## 4. Status wdrożenia produkcyjnego na żywo

W trakcie audytu V12 frontend z banerem uczciwości i rozbiciem wag został poprawnie skompilowany lokalnie, lecz nie trafił od razu na serwer produkcyjny z powodu braku integracji Git Webhook w projekcie Vercel (`link: null`). Wdrożenie zostało wykonane bezpośrednio za pomocą Vercel CLI (`vercel deploy --prod`), co zaktualizowało produkcyjny bundle do `assets/index-CwhrjICi.js` na `https://yourquantum.pl`.
Treść baneru uczciwości *"Nie znaleziono dokumentów źródłowych"* została zweryfikowana empirycznie na żywej produkcji.

---

## 5. Wyjaśnienie formatu raportu

Początkowa wersja robocza raportu V12 skupiła się na zwięzłym zestawieniu tabelarycznym i matematycznym algorytmu DEC-037. Niniejsza wersja uzupełnia opis do pełnego standardu rozliczeniowego projektu YourQuantum, prostując ścieżkę modułu adaptera wyszukiwania (`backend/infrastructure/web_research/search_adapter.py`) oraz odnotowując stan wdrożenia produkcyjnego.
