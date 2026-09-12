# YourQuantum — CURRENT STATE
_Last updated: 2026-09-12_

## Status: PRODUKCJA STABILNA — SAFARI FIX + JAKOŚĆ WIP

Projekt jest wdrożony na `https://yourquantum.pl` (Vercel, commit `d3e063a`).

---

## Co działa (zweryfikowane empirycznie)

### ✅ Flagship Quantum Terminal & Komunikacja Przewagi nad Czatami AI
- **Flagship Terminal**: Pole wprowadzania dylematu (`heroInputWrap`) przekształcone w terminal obliczeń kwantowych w stylu high-tech (pasek statusu z pulsującą diodą `● TERMINAL OBLICZEŃ KWANTOWYCH`, badge `QAOA + CP-SAT · 0% HALUCYNACJI`, wysoki kontrast, precyzyjne chipy przykładów, magnetyczny przycisk `⚡ OBLICZ ROZWIĄZANIE KWANTOWE →`).
- **Mocna komunikacja w Hero**: Wyróżniony pill badge `● MECHANIZM KWANTOWY ZAMIAST ZGADYWANIA CZATU AI` oraz podtytuł precyzujący kontrast między autoregresyjnym zgadywaniem LLM a optymalizacją w przestrzeni stanów.
- **Tabela porównawcza**: Sekcja `Dlaczego nie chatbot` została wzmocniona o konkretne techniczne argumenty: QAOA vs autoregresja, twarde gwarancje CP-SAT vs łamanie ograniczeń, niezależny certyfikat matematyczny vs subiektywne opinie.
- **Dolny panel `ConversationPanel`**: Spójny, ciemny design terminala kwantowego z identyczną paletą OKLCH i estetyką.
- **Pełna responsywność mobile i desktop**: Dostosowane odstępy, eliminacja zawijania przycisków w topNav na ekranach iPhone, 100% widoczności terminala.
- **Weryfikacja**: 5/5 testów Playwright zakończonych sukcesem, zrzuty ekranu (`desktop_quantum_terminal.png`, `mobile_quantum_terminal.png`, `quantum_terminal_card.png`, `comparison_quantum_vs_ai.png`).

### ✅ 3D Brain Modal & Pełna Responsywność Mobile (iPhone/Safari)
- Przycisk `🧠 Mózg Silnika 3D` w topNav i stickyNav otwiera modal
- Modal jako `<div role="dialog" position:fixed>` z obsługą `100dvh` i Safe Area Inset — działa w **Chrome, Firefox i Safari iOS**
- **Mobile (`<= 768px`)**: Układ kolumnowy (`EngineBrain3D.module.css`). Na górze wycentrowany obszar WebGL 3D, w środku zadokowany poziomy pasek zakładek 4 płatów (`scroll-snap-type`), na dole płynnie przewijalna karta ze szczegółami, telemetrią i CTA.
- **Gesty dotykowe 3D**: `touchstart`, `touchmove`, `touchend` z `touch-action: none` — obracanie mózgu jednym palcem z bezwładnością na telefonach.
- **Kompaktowy nagłówek mobilny**: Jednopoziomowy pasek `🧠 Mózg 3D • 60 FPS` + przyciski `← Dylemat` i `✕ Zamknij` bez ucinania liter pod paskiem adresu Safari.
- Three.js inicjalizuje się z poprawnym rozmiarem (usunięto sztywny floor 400px, pełna adaptacja do kontenera)
- **Biała strona po "Wstecz" NAPRAWIONA**: `history.pushState({brainModal:true})` + `popstate` listener zamyka modal bez opuszczania SPA
- Zweryfikowane testem Playwright na profilu iPhone (`e2e/mobile-brain.spec.ts`).

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
