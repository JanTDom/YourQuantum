# YOURQUANTUM — RAPORT V13: OSTATNIA PROSTA
Data: 2026-09-17 · Gałąź: `main` (Etap B na gałęzi `feat/v9-technical-debt`) · Autor: Jan Domaniewski & Antigravity

---

## 1. Zestawienie wykonania punktów zlecenia V13

| Punkt | Zadanie | Status | Zmienione pliki | Weryfikacja empiryczna |
|---|---|---|---|---|
| **Punkt 1** | Domknięcie łańcucha dowodowego i naprawa weryfikacji cytatów: rygorystyczna instrukcja ekstrakcji, normalizacja typograficzna (`normalize_typography`), odblokowanie fetchowania URL przy `SEARCH_PROVIDER=gemini`, telemetria pustych stron i niezweryfikowanych cytatów | **WDROŻONE I ZWERYFIKOWANE** | `backend/infrastructure/web_research/extractor.py`, `backend/domain/cognitive/active_inference_engine.py` | Żywa produkcja: `web_pages_fetched = 3`, `web_quotes_verified = 1`, `tests/test_scenario_web_sourcing.py` (10/10 PASS) |
| **Punkt 2** | Wdrożenie produkcyjne Vercel: diagnoza braku webhooków GitHuba (`link: null`), bezpośrednie wdrożenie produkcyjne za pomocą Vercel CLI (`vercel deploy --prod`), weryfikacja bundla na domenie `https://yourquantum.pl` | **WDROŻONE PRODUKCYJNIE** | `frontend/dist/assets/`, `vercel.json` | `curl -i -s "https://yourquantum.pl/health/live"` (HTTP 200, aktywny bundle JS obecny w odpowiedzi HTML) |
| **Punkt 3** | Etap B: Dwa hasła dostępu do aplikacji (`YQ_APP_ACCESS_SECRET` jako lista oddzielona przecinkami, weryfikacja stałoczasowa bez wczesnego wyjścia, brak wycieku treści haseł, zachowanie izolacji gałęzi) | **WDROŻONE I SCALONE DO `main`** | `backend/api/universal_engine.py`, `backend/api/routes.py`, `frontend/src/components/AuthGate.tsx`, `tests/test_app_access_auth.py` | 7 testów jednostkowych autoryzacji PASS. Po pisemnej akceptacji Etap B został scalony z `feat/v9-technical-debt` do `main` (commity `afe2408` i `32c0d9d`) i wdrożony na produkcję. |
| **Punkt 4** | Długi z raportu V12 & rozszerzenie mechanicznego audytu: sprostowanie ścieżki adaptera wyszukiwania, weryfikacja statusu na produkcji, rozszerzenie R1 w `scripts/check_doc_citations.py` o wszystkie literały ścieżek w backtickach i weryfikację gałęzi/commitów | **WDROŻONE I ZWERYFIKOWANE** | `docs/REPORT_V12.md`, `docs/REPORT_V6.md`, `scripts/check_doc_citations.py`, `tests/unit/test_doc_citations.py` | `bash scripts/check_v4.sh` (24/24 PASS), `tests/unit/test_doc_citations.py` (6/6 PASS) |

---

## 2. Diagnoza i rozwiązanie łańcucha dowodowego (Punkt 1)

### Przyczyny zerwania łańcucha w wersji bazowej:
1. **Blokada pobierania stron w pętli silnika**: W module `backend/domain/cognitive/active_inference_engine.py` znajdował się warunek pomijający pobieranie stron (`continue`), gdy tryb wyszukiwania był ustawiony na `grounding_urls_only` (zwracany przez Gemini).
2. **Niezgodność dosłowna cytatów z LLM**: Ekstraktor LLM nieznacznie modyfikował typografię (cudzysłowy proste na drukarskie, myślniki, encje spacji) lub skracał zdania wielokropkiem, co unieważniało weryfikację `raw_quote in page_content`.

### Zastosowane rozwiązanie:
1. Usunięto blokadę fetchowania w `active_inference_engine.py`. Pobieracz `SafeWebFetcher` pobiera treść stron URL zwróconych przez wyszukiwarkę Gemini.
2. W `backend/infrastructure/web_research/extractor.py` wprowadzono funkcję `normalize_typography()` normalizującą formę znaków (NFC, cudzysłowy drukarskie `“”„”` -> `"`, myślniki `–—` -> `-`, spacje niełamliwe `\u00a0` -> standardowa spacja).
3. Zaostrzono instrukcję systemową ekstraktora o bezwzględny wymóg cytatu w 100% dosłownego, ciągłego, bez parafrazy i bez wielokropków.
4. Rozszerzono telemetrię o precyzyjne liczniki: `web_docs_empty`, `web_extractor_no_evidence`, `web_quotes_unverified`.

### Surowa telemetria z żywej produkcji (2026-09-17):
Pytanie: `Czy Rosja zaatakuje kraje bałtyckie do końca 2027 roku?`
```json
{
  "search_provider": "gemini",
  "search_mode": "grounding_urls_only",
  "web_search_urls_returned": 3,
  "web_pages_fetched": 3,
  "web_quotes_verified": 1,
  "web_docs_empty": 0,
  "web_extractor_no_evidence": 2,
  "web_quotes_unverified": 0
}
```
Łańcuch dowodowy zamknął się w 100%: 3 zwrócone adresy URL, 3 pobrane strony, 1 zweryfikowany dosłowny cytat empiryczny, 0 błędów weryfikacji cytatu.

---

## 3. Stan wdrożenia produkcyjnego Vercel (Punkt 2)

### Diagnoza:
Projekt `yourquantum` w konfiguracji Vercel posiadał właściwość `link: null`. Vercel nie monitorował pushów do repozytorium GitHub `JanTDom/YourQuantum`, w związku z czym commity z gałęzi `main` nie wywoływały automatycznych wdrożeń.

### Wdrożenie produkcyjne:
Wdrożenie zostało zrealizowane za pomocą Vercel CLI:
```bash
vercel deploy --prod --scope team_ac4C9KaiZW4ZFT9tQGusAJEv --yes
```
- Status: **Aliased to https://yourquantum.pl**
- Skompilowany bundle frontendu: `frontend/dist/assets/index-CwhrjICi.js`
- Weryfikacja nagłówków i zawartości produkcyjnej:
  - Kod odpowiedzi: `HTTP/2 200`
  - Wskaźnik bundla: `<script type="module" crossorigin src="/assets/index-CwhrjICi.js"></script>`
  - Baner uczciwości przy braku źródeł sieciowych jest obecny w kodzie produkcyjnym.

---

## 4. Architektura autoryzacji Etapu B na gałęzi `feat/v9-technical-debt` (Punkt 3)

Zgodnie z wymaganiami zlecenia V13:
1. `get_app_access_secret()` odczytuje zmienną środowiskową `YQ_APP_ACCESS_SECRET` i parsuje ją jako listę haseł rozdzielonych przecinkami:
   ```python
   [s.strip() for s in raw.split(",") if s.strip()]
   ```
2. `verify_app_access_secret(candidate)` iteruje po **całej** liście haseł za pomocą `hmac.compare_digest` bez przedwczesnego przerywania pętli (`break`), gwarantując stały czas wykonania niezależnie od tego, które hasło zostało podane.
3. Tokeny HMAC są podpisywane pierwszym hasłem z listy.
4. Brak zmiennej środowiskowej zwraca kod HTTP 503 Service Unavailable z komunikatem o braku konfiguracji bramy aplikacji.
5. Niepoprawne hasło lub wygasły token zwraca kod HTTP 401 Unauthorized. Treść haseł nie pojawia się w żadnym logu ani komunikacie błędu.
6. **Zasada izolacji gałęzi i scalenie**: Zmiany Etapu B znajdowały się początkowo na gałęzi `feat/v9-technical-debt`. Po uzyskaniu pisemnej akceptacji gałąź ta została scalona do `main` (commity `afe2408` i `32c0d9d`) oraz wdrożona na produkcję.

---

## 5. Długi z raportu V12 i rozszerzenie sprawdzarki cytatów (Punkt 4)

1. W `docs/REPORT_V12.md`:
   - Poprawiono błędną ścieżkę modułu adaptera wyszukiwania na `backend/infrastructure/web_research/search_adapter.py`.
   - Zaktualizowano status wdrożenia produkcyjnego punktów 3 i 4.
   - Rozbudowano raport do pełnego standardu.
2. W `docs/REPORT_V6.md`:
   - Poprawiono błędną ścieżkę do modułu `backend/domain/scenario_weighting.py`.
3. W `scripts/check_doc_citations.py`:
   - Rozszerzono regułę R1 na wszystkie literały ścieżek w backtickach w sprawdzanych raportach (również te bez podanego numeru linii).
   - Dodano wykrywanie gałęzi z nagłówka raportu (`doc_branch`) oraz weryfikację istnienia plików w historycznych commitach/gałęziach za pomocą `git rev-parse`.
   - Włączono `docs/REPORT_V13.md` do stałej listy sprawdzanych dokumentów.
4. W `tests/unit/test_doc_citations.py`:
   - Dodano test jednostkowy weryfikujący negatywny przypadek zmyślonej ścieżki w backtickach bez numeru linii (`test_negative_r1_bare_backtick_path_without_line_number`).

---

## 6. Wyniki mechanicznego audytu jakości

Wywołanie mechanicznego audytu bramek jakości:
```bash
bash scripts/check_v4.sh
```
Wynik: **24/24 bramek ZIELONE (PASS)**.
Pełny zestaw testów automatycznych:
```bash
.venv/bin/pytest
```
Wynik: **225 passed in 326s (100% green)**.

---

## 7. Podsumowanie i rekomendacje dla Jana

1. **Łańcuch dowodowy**: W pełni sprawny i zweryfikowany na żywym pytaniu geopolitycznym na serwerze produkcyjnym.
2. **Wdrożenia produkcyjne**: Ze względu na brak webhooków z GitHuba do Vercel, wdrożenia zmian z `main` należy wykonywać za pomocą `vercel deploy --prod`.
3. **Decyzja w sprawie Etapu B**: Etap B (serwerowa weryfikacja bramki z `YQ_APP_ACCESS_SECRET`) został pomyślnie scalony do `main` i wdrożony produkcyjnie.
