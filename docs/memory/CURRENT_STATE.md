# YourQuantum — CURRENT STATE
_Last updated: 2026-09-12_

## Status: PRODUKCJA STABILNA — SAFARI FIX + JAKOŚĆ WIP

Projekt jest wdrożony na `https://yourquantum.pl` (Vercel, commit `d3e063a`).

---

## Co działa (zweryfikowane empirycznie)

### ✅ 3D Brain Modal
- Przycisk `🧠 Mózg Silnika 3D` w topNav i stickyNav otwiera modal
- Modal jako `<div role="dialog" position:fixed>` — działa w **Chrome, Firefox i Safari**
- Three.js inicjalizuje się z poprawnym rozmiarem (rAF polling do 60 klatek)
- Złote cząstki, pierścienie, rdzeń — widoczne
- **Biała strona po "Wstecz" NAPRAWIONA**: `history.pushState({brainModal:true})` + `popstate` listener zamyka modal bez opuszczania SPA
- Safari kompatybilność: zrezygnowano z natywnego `<dialog>` (Safari wymusza `display:block`)

### ✅ Hero SG
- Nagłówek 4-liniowy: `Twój dylemat / ma jedno / właściwe / rozwiązanie.`
- Artwork `hero-entanglement.jpg` w pełni widoczny, niezasłonięty

### ✅ Backend
- `DecisionCase` z `InputQuality` (model z domyślnymi wartościami, backward-compat)
- LLMAdvisor z Gemini API — działa gdy podany klucz
- Solwery CP-SAT i QAOA działają
- Baza Supabase podłączona

---

## ⚠️ WIP — Walidacja jakości danych wejściowych (NASTĘPNY KROK)

Użytkownik zgłosił: **„ogólnikowe dyrdymały też liczą, powinien zmuszać do sprecyzowania"**

### Co zostało zrobione (commit `d3e063a`):
- `backend/domain/decision_case.py` — nowy model `InputQuality`:
  ```python
  level: "sufficient" | "too_vague" | "needs_options" | "needs_numbers"
  reason: str
  suggestions: list[str]
  ```
- `DecisionCase.input_quality` — pole z `default_factory=InputQuality` (domyślnie `sufficient`)
- Import `InputQuality` w `llm_advisor.py`

### Co jeszcze trzeba zrobić:

#### 1. Backend — `_assess_input_quality()` w `LLMAdvisor`
Dodać metodę która ocenia jakość tekstu i ustawia `input_quality` na budowanym `DecisionCase`.

Kryteria zbyt ogólnego opisu:
- < 15 słów → `too_vague`
- Brak jakichkolwiek opcji/wariantów/alternatyw → `needs_options`
- Brak liczb gdy kontekst liczbowy jest wymagany (inwestycje, budżet) → `needs_numbers`

W ścieżce Gemini — dodać do JSON response pole `input_quality_level` i `suggestions`.

#### 2. Frontend — UI blokady w `LandingPage.tsx`
W `handleHeroSubmit` — przed wywołaniem `onSubmit`:
- Szybka synchroniczna walidacja lokalna (długość, słowa kluczowe)
- `ConversationPanel.tsx` — inline `QualityWarning` komponent:
  - Żółty/czerwony alert z ikoną ⚠️
  - `reason` + lista `suggestions` jako bullet points
  - Dwa przyciski: `Popraw opis` (focus textarea) lub `Oblicz mimo to`

W `App.tsx` — po `analyzeCase()`:
- Jeśli `decisionCase.input_quality.level !== "sufficient"` → **nie przechodzi do CASE_WORKSPACE**
- Wraca do INTAKE z wyświetlonym alertem

---

## Następny konkretny krok

**`backend/domain/llm_advisor.py`** — dodać `_assess_input_quality(text: str) -> InputQuality` i wywołać ją w:
- `heuristic_analyze()` — przed `return DecisionCase(...)`
- `_call_gemini()` — rozszerzyć prompt o pole `input_quality`

Potem **`frontend/src/App.tsx`** i **`LandingPage.tsx`** — UI blokady.

---

## Deploy info
- GitHub: `https://github.com/JanTDom/YourQuantum` (main, commit `d3e063a`)
- Production: `https://yourquantum.pl` (Vercel, commit `cf85640` — Safari fix)
- Deploy command: `npx vercel --prod --yes` (BypassSandbox: true)
