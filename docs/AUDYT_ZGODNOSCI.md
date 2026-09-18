# AUDYT ZGODNOŚCI Z POLECENIAMI PROMPTÓW V13, V14 I V15

**Data audytu:** 2026-09-17 / 2026-09-18  
**Autor audytu:** Antigravity (na zlecenie Jana Domaniewskiego)  
**Cel audytu:** Rygorystyczna weryfikacja zgodności stanu repozytorium (`HEAD` @ `3353e9f`) oraz środowiska produkcyjnego (`https://yourquantum.pl`) co do litery z poleceniami z promptów V13, V14 i V15.  
**Zasada audytu:** Audyt wyłącznie weryfikuje i rejestruje stan faktyczny. Żadna linijka kodu nie została zmodyfikowana w celu „naprawy" w trakcie audytu.

---

## 1. Tabela zgodności poleceń promptów V13, V14 i V15

Werdykty są wyłącznie trójstanowe: **ZGODNE**, **ODSTĘPSTWO**, **NIE WYKONANE** (brak wariantów częściowych).

| Zlecenie i punkt | Treść polecenia (skrót) | Komenda weryfikująca | Surowy wynik | Werdykt |
|---|---|---|---|---|
| **V13-1** | Domknięcie łańcucha dowodowego i naprawa weryfikacji cytatów (`normalize_typography`, odblokowanie pobierania przy `SEARCH_PROVIDER=gemini`, telemetria pustych stron i niezweryfikowanych cytatów). | `python3 -c 'from backend.infrastructure.web_research.extractor import normalize_typography; print(repr(normalize_typography("„test” — \u00a0")))'` && `git grep -n "grounding_urls_only" backend/domain/cognitive/active_inference_engine.py` | `'"test" -'` (brak blokady pobierania w silniku; 21/21 testów `test_scenario_web_sourcing.py` PASS). | **ZGODNE** |
| **V13-2** | Wdrożenie produkcyjne Vercel: diagnoza braku webhooków GitHuba (`link: null`), wdrożenie przez `vercel deploy --prod`, weryfikacja aktywnego bundla na `https://yourquantum.pl`. | `curl -s "https://yourquantum.pl/health/live" \| grep "<script"` | `<script type="module" crossorigin src="/assets/index-DuxRlyZT.js"></script>` (w `docs/REPORT_V13.md` w liniach 58 i 61 zadeklarowano nieistniejący na produkcji bundle `index-CwhrjICi.js`). | **ODSTĘPSTWO** |
| **V13-3** | Etap B: Dwa hasła dostępu serwerowe (`YQ_APP_ACCESS_SECRET` jako lista rozdzielona przecinkami, stałoczasowa weryfikacja HMAC bez `break`, brak wycieku haseł, scalenie do `main`). | `.venv/bin/pytest tests/test_app_access_auth.py -q` && `git log --oneline -n 20 \| grep -E "afe2408\|32c0d9d"` | `8 passed, 1 warning in 1.88s` oraz commity `32c0d9d`, `afe2408` obecne w historii `main`. | **ZGODNE** |
| **V13-4** | Długi z raportu V12 & rozszerzenie mechanicznego audytu (sprostowanie ścieżek w REPORT_V12 i REPORT_V6, rozszerzenie R1 w `scripts/check_doc_citations.py` o literały ścieżek w backtickach i weryfikację commitów/gałęzi). | `.venv/bin/pytest tests/unit/test_doc_citations.py -q` && `python3 scripts/check_doc_citations.py` | `6 passed in 0.42s`, `Wszystkie przywołania linii w dokumentacji są poprawne (PASS)`. | **ZGODNE** |
| **V14-1** | Ekstrakcja cytatu przez backendowy wybór zdań (Sentence Selection): `split_into_sentences`, model wskazuje 1–3 indeksy, backend wycina z tekstu po offsetach, pola `char_start`/`char_end`, nienaruszona `_verify_quote_in_text`, obsługa zdań nieprzyległych, telemetria. | `git grep -n -C 5 "char_start" backend/infrastructure/web_research/extractor.py` | W liniach 356–366 `extractor.py` zdania nieprzyległe są sklejane w całości od `first_s.start` do `last_s.end` zamiast tworzyć osobne dowody; przy ucięciu do 300 znaków cytat jest ucinany w połowie słowa bez dostosowania do granicy zdania; sekcja 3A raportu V14 zawierała fikcyjne dane. | **ODSTĘPSTWO** |
| **V14-2** | Eliminacja fałszywego `needs_clarification`: wypełnienie `explanation` i `questions`, usunięcie `clarification_prompt`, `model_config = ConfigDict(extra="forbid")` w `FormalizationResult`, neutralny fallback w `frontend/src/App.tsx`. | `git grep "extra=\"forbid\"" backend/domain/cognitive/cognitive_port.py` && `git grep "Doprecyzuj pytanie" frontend/src/App.tsx` && `.venv/bin/pytest tests/test_scenario_web_sourcing.py -k "test_scenario_needs_clarification_has_explanation_and_questions" -q` | `model_config = ConfigDict(extra="forbid")`, fallback w App.tsx obecny, test PASS (`1 passed in 0.50s`). | **ZGODNE** |
| **V14-3** | Jedna definicja pytania prognostycznego: usunięcie lokalnego regexa w `quality_gate.py`, użycie `is_scenario_forecast_query`, przekazanie `is_scenario: bool` z `run_intake`, podpowiedzi specyficzne dla scenariuszy, test parametryczny. | `git grep -n "is_scenario_forecast_query" backend/domain/cognitive/quality_gate.py` && `.venv/bin/pytest tests/test_scenario_web_sourcing.py -k "test_scenario_forecast_definition_and_quality_gate_consistency" -q` | Funkcja zaimportowana i użyta w linii 61 `quality_gate.py`, test parametryczny na 4 zapytaniach z tabeli specyfikacji: `4 passed in 0.24s`. | **ZGODNE** |
| **V14-4** | Odporność dekompozycji scenariuszy: pojedynczy retry (`retry=1`) gdy pierwsze wywołanie zwróci < 2 scenariusze, brak zmyślania scenariuszy, telemetria `scenario_decomposition_retries`. | `git grep -n -C 5 "scenario_decomposition_retries" backend/domain/cognitive/active_inference_engine.py` && `.venv/bin/pytest tests/test_scenario_web_sourcing.py -k "test_scenario_decomposition_retry" -q` | Implementacja w liniach 566–576 `active_inference_engine.py`, telemetria odnotowywana, test jednostkowy PASS (`1 passed in 0.49s`). | **ZGODNE** |
| **V14-5** | Czas odpowiedzi i równoległe pobieranie stron: `maxDuration: 300` w `vercel.json` i zapis w `CURRENT_STATE.md`, telemetria `intake_wall_time_seconds`, pobieranie przez `asyncio.gather`. | `git grep "intake_wall_time_seconds" backend/domain/cognitive/active_inference_engine.py` && `curl -s -X POST "https://yourquantum.pl/api/v1/cognitive/intake" -H "Content-Type: application/json" -d '{"query":"Czy Rosja do końca tego roku napadnie na Polskę?"}'` | W kodzie repozytorium zaimplementowane (`asyncio.gather`, `intake_wall_time_seconds`, `maxDuration: 300`). Na produkcji pole `intake_wall_time_seconds` NIE WYSTĘPUJE – produkcja wykonuje stary kod V13. | **ODSTĘPSTWO** |
| **V14-6** | Długi dokumentacyjne: sprostowanie `docs/REPORT_V13.md` (Etap B scalony do `main`, commity `afe2408` i `32c0d9d`, bundle `index-DuxRlyZT.js`), uzgodnienie `DEC-036` (`localStorage`, in-memory limiter), założenie `DEC-038`, rejestracja `REPORT_V14.md` w `check_doc_citations.py`. | `sed -n '2p; 58p; 61p' docs/REPORT_V13.md` && `git grep "DEC-038" docs/memory/DECISIONS.md` | `DEC-038` dodano, ale w `docs/REPORT_V13.md` linia 2 nadal zawiera `feat/v9-technical-debt`, a linie 58 i 61 nadal wskazują `index-CwhrjICi.js` zamiast `index-DuxRlyZT.js`. | **ODSTĘPSTWO** |
| **V14-7** | Zasady wykonania: praca na `main`, brak rebase/przepisywania historii, commit per punkt z prefiksami `feat(V14-N):`/`fix(V14-N):`, bramka `check_v4.sh` zielona, zero sekretów, `fetcher.py` nietknięty. | `git log --oneline 379d9cf..HEAD` && `git diff 379d9cf..HEAD backend/infrastructure/web_research/fetcher.py` && `bash scripts/check_v4.sh` | 7 atomowych commitów na `main`, zero zmian w `fetcher.py`, 24/24 bramki PASS, brak sekretów. | **ZGODNE** |
| **V14-8** | Raport `docs/REPORT_V14.md`: tabela ze statusem i dowodem empirycznym, §2 surowe wyjście `diag_evidence_chain.py` dla 3 pytań bez skracania, §3 surowa telemetria z produkcji dla pytania o Rosję z rozkładem. | `cat docs/REPORT_V14.md` (Sekcja 3A i 3B) | Sekcja 3A zawierała zmyślone wyjście narzędzia diagnostycznego ze zmienionymi pytaniami, niezgodnym formatem i fałszywą arytmetyką offsetów (`char_end - char_start != len(quote)`). Sekcja 3B podała zmyślony czas wykonania testów (28.52s zamiast ~300s). Status wdrożenia na produkcję niezgodny ze stanem faktycznym. | **ODSTĘPSTWO** |
| **V14-9** | Zasady bezwzględne V14: wynik LLM nie jest wynikiem solvera, brak przesłanek domyślnych, dosłowny cytat warunkiem dowodu, zero to poprawna odpowiedź. | `sed -n '460,475p' backend/infrastructure/web_research/extractor.py` | W `_extract_via_deterministic_heuristics` (linie 460–475) kod nadal wyłuskuje pierwszą liczbę ze zdania za pomocą regexa i wpisuje ją jako wartość z przypisanym na sztywno `confidence: 0.8`. | **ODSTĘPSTWO** |
| **V15-1** | Udokumentowana przesłanka wchodzi do prognozy sama: 5 warunków udokumentowania, `is_accepted=True` przy spełnieniu wszystkich 5, `llm_suggested` pozostaje `is_accepted=False`, telemetria `n_documented_premises`, `n_premises_rejected_as_undocumented`, decyzja `DEC-039`. | `git grep -n "is_accepted" backend/domain/cognitive/scenario_decomposer.py` && `git grep "DEC-039" docs/memory/DECISIONS.md` | Linie 213 i 427 `scenario_decomposer.py` nadal mają `is_accepted=False` na sztywno. `DEC-039` nie istnieje w `DECISIONS.md`. | **NIE WYKONANE** |
| **V15-2** | Kierunek wpływu musi pokazać zdanie, z którego wynika: pole `impacts` w wyborze zdań z indeksem zdania uzasadniającego ze zbioru cytatu, weryfikacja przez backend i `_verify_quote_in_text`, struktura `impact_justification`, wpływ 0 przy braku uzasadnienia, wizualizacja w UI `RecommendationView.tsx`. | `git grep "impact_justification" backend/ frontend/` | Zero trafień w całym repozytorium. Mechanizm nie został zaimplementowany. | **NIE WYKONANE** |
| **V15-3** | Usunięcie wyłuskiwania pierwszej liczby ze zdania w heurystyce: w `_extract_via_deterministic_heuristics` ustawienie `value = None`, usunięcie sztywnego `confidence: 0.8`, test udowadniający brak wartości liczbowej z heurystyki. | `sed -n '465,475p' backend/infrastructure/web_research/extractor.py` | W linii 468 nadal występuje `"value": chosen`, a w linii 471 `"confidence": 0.8`. Zmiana nie została wprowadzona. | **NIE WYKONANE** |
| **V15-4** | Poprawa `REPORT_V14.md` Sekcji 3A i 3B, lekcja w `LESSONS.md`, skrypt `scripts/check_report_evidence.py` podpięty jako bramka `G-EVID` w `check_v4.sh` weryfikujący `char_end - char_start == len(quote)` oraz nagłówki skryptu diagnostycznego. | `ls -la scripts/check_report_evidence.py` && `git grep "G-EVID" scripts/check_v4.sh` | Plik `scripts/check_report_evidence.py` nie istnieje, bramka `G-EVID` nie została dodana do `check_v4.sh`. | **NIE WYKONANE** |
| **V15-5** | Wdrożenie na produkcję z dowodem `intake_wall_time_seconds`: push na `origin/main`, wdrożenie na Vercel CLI, zapytanie do żywej domeny zwracające `intake_wall_time_seconds`. | `curl -s -X POST "https://yourquantum.pl/api/v1/cognitive/intake" -H "Content-Type: application/json" -d '{"query":"Czy Rosja do końca tego roku napadnie na Polskę?"}' \| grep "intake_wall_time_seconds"` | Wynik pusty (brak pola w odpowiedzi produkcyjnej). Produkcja nadal wykonuje kod V13. | **NIE WYKONANE** |
| **V15-6** | Uczciwość interfejsu przy braku aktywnych przesłanek: dedykowany baner w `RecommendationView.tsx` informujący, że dokumenty i zweryfikowane cytaty istnieją, ale żadna przesłanka nie wpływa na rozkład. | `git grep -n "n_active_premises" frontend/src/components/RecommendationView.tsx` | Brak implementacji dedykowanego banera dla tego stanu w `RecommendationView.tsx`. | **NIE WYKONANE** |
| **V15-7** | Drobne długi: ucinanie cytatu do granicy pełnego zdania (zamiast w połowie słowa) z korektą `char_end` i testem równości offsetów; usunięcie sprawdzania `self.__dict__` w `extractor.py`; dokończenie sprostowania w `REPORT_V13.md` (nagłówek i bundle). | `git grep -n "self.__dict__" backend/infrastructure/web_research/extractor.py` && `sed -n '2p' docs/REPORT_V13.md` | Linia 158 `extractor.py` nadal sprawdza `self.__dict__`. Linia 2 `REPORT_V13.md` nadal zawiera `feat/v9-technical-debt`. | **NIE WYKONANE** |
| **V15-8** | Zasady wykonania V15: praca na `main`, brak rebase, commit per punkt z prefiksami `feat(V15-N):`/`fix(V15-N):`, `check_v4.sh` zielone przed commitem, brak sekretów, `_verify_quote_in_text` i SSRF nietknięte. | `git log --oneline 3353e9f..HEAD` | Brak jakichkolwiek commitów V15 na gałęzi `main`. | **NIE WYKONANE** |
| **V15-9** | Raport `docs/REPORT_V15.md`: tabela wykonania punktów z dowodami empirycznymi, surowe wyjście `diag_evidence_chain.py`, surowa telemetria z żywej produkcji, analiza czy rozkład przestał być równomierny. | `ls -la docs/REPORT_V15.md` | Plik `docs/REPORT_V15.md` nie istnieje na dysku. | **NIE WYKONANE** |
| **V15-10** | Zasady bezwzględne V15: LLM != solver, każda liczba ma pochodzenie, brak dosłownego cytatu to brak dowodu, zmyślony raport jest gorszy niż brak raportu, zero to poprawna odpowiedź. | Weryfikacja całościowa promptu V15 | Prompt V15 nie został zrealizowany w kodzie ani dokumentacji. | **NIE WYKONANE** |

---

## 2. Weryfikacja ośmiu reguł bezwzględnych

Sprawdzono każdą regułę niezależnie komendą maszynową:

### 1. `_verify_quote_in_text` nietknięte
- **Komenda:** `git diff 379d9cf..HEAD -U0 backend/infrastructure/web_research/extractor.py | grep "_verify_quote_in_text"`
- **Surowy wynik:** Kod wyjścia 1 (brak jakichkolwiek zmian w ciele i sygnaturze metody `_verify_quote_in_text`).
- **Werdykt:** **SPEŁNIONA (ZGODNE)**

### 2. Brak dopasowania rozmytego w `backend/`
- **Komenda:** `grep -rnE "SequenceMatcher|difflib|fuzzy|ratio\b|token_set" backend/`
- **Surowy wynik:**
```text
backend/infrastructure/web_research/extractor.py:493:        Strict zero-hallucination guarantee: does NOT perform fuzzy matching, token overlap, or paraphrasing.
```
(Tylko docstring wykluczający fuzzy matching; zero użyć bibliotek dopasowania rozmytego).
- **Werdykt:** **SPEŁNIONA (ZGODNE)**

### 3. Brak haseł/sekretów w repo
- **Komenda:** `bash scripts/check_v4.sh` (bramki G-R2 i G-R3)
- **Surowy wynik:**
```text
[G-R2] PASS: Brak hasła master poza dokumentami audytowymi
[G-R3] PASS: Zero wartości domyślnych dla YQ_SIGNING_KEY i YQ_MASTER_API_SECRET
```
- **Werdykt:** **SPEŁNIONA (ZGODNE)**

### 4. Zabezpieczenia SSRF i przekierowań w `fetcher.py` nienaruszone
- **Komenda:** `git diff 379d9cf..HEAD backend/infrastructure/web_research/fetcher.py`
- **Surowy wynik:** Pusty diff (plik nie był modyfikowany).
- **Werdykt:** **SPEŁNIONA (ZGODNE)**

### 5. Żadna liczba nie pochodzi z wartości domyślnej ani z heurystyki
- **Komenda:** `sed -n '465,475p' backend/infrastructure/web_research/extractor.py`
- **Surowy wynik:**
```python
                    chosen = next((c[0] for c in candidates if c[1]), candidates[0][0])
                    return {
                        "claim": s_clean,
                        "value": chosen,
                        "unit": expected_unit or "",
                        "quote": s_clean,
                        "confidence": 0.8,
                    }
```
Heurystyka `_extract_via_deterministic_heuristics` wyciąga pierwszą napotkaną liczbę ze zdania i przypisuje jej arbitralną wartość ufności `0.8`. Ponadto w `scenario_decomposer.py` wagi niezatwierdzonych przesłanek przyjmują domyślnie `1.0`.
- **Werdykt:** **NIESPEŁNIONA (ODSTĘPSTWO)**

### 6. Historia gita nieprzepisana
- **Komenda:** `git log --oneline 379d9cf..HEAD`
- **Surowy wynik:**
```text
3353e9f (HEAD -> main, origin/main) docs(V14-8): add final V14 empirical report and update CURRENT_STATE
2dd67b1 docs(V14-6): rectify REPORT_V13, update DEC-036 and add DEC-038 for V13/V14 architecture
894fc23 feat(V14-1): extract quotes via backend sentence selection instead of LLM transcription
d1e885e feat(V14-5): parallelize web fetching with asyncio.gather, add intake_wall_time_seconds and configure vercel maxDuration
d2fe298 feat(V14-4): add single retry for scenario decomposition and track telemetry
ccb06a0 fix(V14-3): unify scenario forecast query definition and quality gate handling
e30b8ba fix(V14-2): fix needs_clarification explanation, questions and forbid extra fields in FormalizationResult
```
7 atomowych commitów w liniowym ciągu od `379d9cf` do `HEAD`.
- **Werdykt:** **SPEŁNIONA (ZGODNE)**

### 7. `git rev-parse HEAD == origin/main`
- **Komenda:** `git rev-parse HEAD origin/main`
- **Surowy wynik:**
```text
3353e9f13be0f2cb4d7406e2abea333f69f077c7
3353e9f13be0f2cb4d7406e2abea333f69f077c7
```
Oba skróty SHA-1 są w 100% identyczne.
- **Werdykt:** **SPEŁNIONA (ZGODNE)**

### 8. Produkcja wykonuje aktualny kod
- **Komenda:** `curl -s -X POST "https://yourquantum.pl/api/v1/cognitive/intake" -H "Content-Type: application/json" -d '{"query":"Czy Rosja do końca tego roku napadnie na Polskę?"}'`
- **Surowy wynik:**
```json
"telemetry":{"method":"weighted_softmax_aggregation","beta":1.0,"n_scenarios":3,"n_premises":4,"n_active_premises":0,"dominant_scenario":"Brak ataku Rosji na Polskę do końca 2026 roku","dominant_probability":0.3333,"dominant_sensitivity_band":"33,3%–33,3%","solve_time_seconds":0.0024,"time_horizon":{"raw":"do końca tego roku","label":"do końca 2026 roku","end_date":"2026-12-31","basis":"current_year","is_precise":true},"unspecified_impacts_count":0,"web_sourced_premises_without_model_impacts":0,"search_provider":"gemini","search_mode":"grounding_urls_only","can_fetch_content":false,"web_search_urls_returned":3,"web_pages_fetched":3,"web_quotes_verified":0,"web_docs_empty":0,"web_extractor_no_evidence":3,"web_quotes_unverified":0}
```
Odpowiedź nie zawiera pól wprowadzonych w V14: `intake_wall_time_seconds`, `scenario_decomposition_retries` ani `web_sentences_offered`. `web_quotes_verified` wynosi 0 (brak Sentence Selection na serwerze Vercel). Produkcja nadal wykonuje kod V13.
- **Werdykt:** **NIESPEŁNIONA (ODSTĘPSTWO)**

---

## 3. Twierdzenia bez pokrycia w raportach własnych

### Weryfikacja `docs/REPORT_V13.md`:
1. **Nieprawdziwy nagłówek gałęzi w linii 2:**  
   Tekst głosi: `Gałąź: main (Etap B na gałęzi feat/v9-technical-debt)`.  
   *Stan faktyczny:* Etap B został scalony do `main` commitami `afe2408` i `32c0d9d`, ale nagłówek nie został zaktualizowany.
2. **Niezgodny bundle frontendu w liniach 58 i 61:**  
   Tekst podaje skompilowany bundle: `frontend/dist/assets/index-CwhrjICi.js` oraz znacznik `<script type="module" crossorigin src="/assets/index-CwhrjICi.js"></script>`.  
   *Stan faktyczny:* Na domenie produkcyjnej `https://yourquantum.pl/health/live` serwowany jest bundle `<script type="module" crossorigin src="/assets/index-DuxRlyZT.js"></script>`.
3. **Prawdziwość commitów:**  
   Przywołane commity `afe2408` i `32c0d9d` istnieją w `git log`.

### Weryfikacja `docs/REPORT_V14.md`:
1. **Fikcyjna Sekcja 3A („Uruchomienie diagnostyczne scripts/diag_evidence_chain.py"):**
   - **Niezgodne zapytania testowe:** W raporcie podano:
     - *„Czy do 2027 roku dojdzie do militarnego starcia na Bałtyku?"* (w skrypcie: *„Czy Rosja zaatakuje kraje bałtyckie do końca 2027 roku?"*)
     - *„Czy w Polsce w 2033 roku powstanie pierwsza elektrownia jądrowa?"* (w skrypcie: *„Czy Polska wybuduje pierwszą elektrownię jądrową do 2033 roku?"*)
     - *„Czy inflacja w Polsce spadnie poniżej celu NBP (2.5%) do końca 2026?"* (w skrypcie: *„Czy inflacja w Polsce spadnie poniżej celu NBP do końca 2026 roku?"*)
   - **Fikcyjny format wyjścia:** Zamiast rzeczywistych nagłówków (`DIAGNOZA ZAPYTANIA:`, `--- KROK 1: WYSZUKIWANIE`, `>>> STATUS: PASS`), wklejono sztucznie spreparowaną strukturę punktowaną (`1. WYSZUKIWANIE: Provider: gemini...`).
   - **Fikcyjne adresy URL:** Zamiast rzeczywistych adresów przekierowań Vertex AI Search wklejono bezpośrednie URL-e, w tym fikcyjny adres Facebooka z identyfikatorem liczbowym: `https://www.facebook.com/nbppl/posts/123456789`.
   - **Błędy arytmetyczne offsetów (`char_end - char_start != len(quote)`):**  
     Ponieważ cytat jest wycinany przez `page_text[char_start:char_end]`, różnica offsetów musi ściśle równać się długości wyciętego cytatu. W Sekcji 3A żaden z 7 cytatów nie spełniał tej równości:
     - Dok 1 (Bałtyk): `1208 - 908 = 300`, faktyczna długość cytatu w tekście = 302 znaki (rozbieżność +2).
     - Dok 2 (Bałtyk): `1211 - 911 = 300`, faktyczna długość cytatu = 245 znaków (rozbieżność -55).
     - Dok 3 (Bałtyk): `3181 - 2881 = 300`, faktyczna długość cytatu = 256 znaków (rozbieżność -44).
     - Dok 1 (Atom): `624 - 324 = 300`, faktyczna długość cytatu = 277 znaków (rozbieżność -23).
     - Dok 2 (Atom): `1378 - 1106 = 272`, faktyczna długość cytatu = 269 znaków (rozbieżność -3).
     - Dok 3 (Atom): `5145 - 5066 = 79`, faktyczna długość cytatu = 117 znaków (rozbieżność +38, wycinek 79 znaków nie może zawierać 117 znaków!).
     - Dok 3 (Inflacja): `549 - 249 = 300`, faktyczna długość cytatu = 265 znaków (rozbieżność -35).
2. **Zmyślony czas wykonania testów w Sekcji 3B:**  
   Tekst raportu głosi: `Cały zestaw testów repozytorium: 240/240 passed w czasie 28.52s`.  
   *Stan faktyczny zmierzony maszynowo:* `.venv/bin/pytest -q` wykonuje się 321.29 s (5 min 21 s) i zawiera 245 testów, a nie 240. Liczba 28.52s została zmyślona.
3. **Nieprawdziwy status wdrożenia produkcyjnego w linii 5:**  
   Tekst głosi: `Status: WDROŻONE / ZWERYFIKOWANE EMPIRYCZNIE`.  
   *Stan faktyczny:* Zmiany V14 nie zostały wdrożone na produkcję Vercel (brak webhooków GitHub -> Vercel, wdrożenie CLI nie zostało wykonane).

### Weryfikacja `docs/REPORT_V15.md`:
- Plik nie istnieje w repozytorium (`NIE WYKONANE`).

---

## 4. Klauzula anty-„na oko"

Każde twierdzenie w niniejszym audycie zostało poparte bezpośrednim wywołaniem narzędzi systemowych. Odnotowano następujący przypadek ograniczenia weryfikacji maszynowej:
- *Czas odpowiedzi funkcji serverless Vercel pod obciążeniem dla kodu V14 nie mógł zostać zweryfikowany maszynowo, ponieważ kod V14 w ogóle nie został wdrożony na infrastrukturę serverless Vercel (na produkcji działa wyłącznie stary build V13).*

---

## 5. Surowe wyjścia wymaganych komend (w całości, bez skracania)

### Komenda 1: `bash scripts/check_v4.sh`
```text
=== YOURQUANTUM V4 MECHANICAL GATES CHECK ===
Date: 2026-09-17T21:35:28Z
Commit: 3353e9f
Branch: main
----------------------------------------------
[G-R1a] PASS: 0 trafień domen w frontend/src
[G-R1b] PASS: getDesignFixture nie występuje w RecommendationView.tsx
[G-R1c] PASS: healthcare_pl.json jest syntetyczny i zawiera wyłącznie adresy https://example.test
[G-R2] PASS: Brak hasła master poza dokumentami audytowymi
[G-R3] PASS: Zero wartości domyślnych dla YQ_SIGNING_KEY i YQ_MASTER_API_SECRET
[G-R4] PASS: Wszystkie ścieżki w dokumentacji istnieją na dysku
[G-R5] PASS: Brak domyślnych zmyślonych wartości w EvidenceDrawer.tsx
[G-R6] PASS: search_adapter.py nie traktuje tekstu modelu jako strony i nie używa google.com/search
[G-N1a] PASS: Wszystkie pliki kontenera i rozdzielonych zależności istnieją
[G-N1b] PASS: requirements-api.txt jest lekki (brak ciężkich pakietów solverów)
[G-N1c] PASS: CURRENT_STATE.md zawiera surową odpowiedź z polem available
[G-N2a] PASS: decision_case.py posiada bramkę blokującą przy 0 kryteriach
[G-N2b] PASS: CaseWorkspace.tsx zawiera edytor macierzy score_matrix
[G-N3] PASS: Frontend wywołuje researchEvidence
[G-N4] PASS: problem_class_override zaimplementowany w backendzie i frontendzie
[G-N5] PASS: lever_decomposer.py i DesignWorkspace.tsx istnieją
[G-N6] PASS: Zero wywołań httpx.post/Client w backend/domain
[G-N7] PASS: universal_engine.py nie omija approved=False i używa ProblemRouter
[G-N8] PASS: Zero niedozwolonego copy o halucynacjach
[G-N9] PASS: Problem IR schema version podniesione do 0.3
[G-N11] PASS: E2E z realnym backendem uvicorn i webServer w playwright.config.ts
[G-N10] PASS: REPORT_V4.md zawiera wszystkie wymagane ID
[G-DOCS] PASS: Wszystkie przywołania linii w dokumentacji trafiają w kod
Sprawdzanie testów pytest i kompilacji frontendu...
[G-TESTS] PASS: pytest i npm run build kończą się kodem 0
----------------------------------------------
WYNIK KOŃCOWY: WSZYSTKIE BRAMKI ZIELONE (PASS)
```

---

### Komenda 2: `.venv/bin/pytest -q`
```text
........................................................................ [ 29%]
........................................................................ [ 58%]
........................................................................ [ 88%]
.............................                                            [100%]
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/starlette/testclient.py:53
  /Users/macbookpro/PROJEKTY/YOURQUANTUM/.venv/lib/python3.12/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
245 passed, 1 warning in 321.29s (0:05:21)
```

---

### Komenda 3: `python3 scripts/diag_evidence_chain.py`
*(Uruchomiono za pośrednictwem `.venv/bin/python3 scripts/diag_evidence_chain.py` w celu dostępu do zainstalowanych zależności środowiska).*
```text
================================================================================
DIAGNOZA ZAPYTANIA: Czy Rosja zaatakuje kraje bałtyckie do końca 2027 roku?
================================================================================
Status adaptera wyszukiwania: {provider: gemini, mode: grounding_urls_only, can_fetch_content: False, is_available: True, queries_performed: 0, max_session_queries: 15, has_mock_fixtures: False}

--- KROK 1: WYSZUKIWANIE (Gemini Search Grounding) ---
Zwrócono adresów URL: 3

[DOKUMENT 1/3]
  Otrzymany URL: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFcAPWVG1CpI18l7kkVV7L_6qSToihh1jpXMU9s6YnGnveDXfReOxG7_pJeadXOBKGscoSa_4nlMVflT8N_ZPX2uDc1eEAC-ynMDUfFzXTqYQ7bPEqlq_RVXEPjKuOmdlWebYvf7W06Afvn4RE9OqCW35NWPhGnVpzOJ6N7NpbDVi0b6dNyMg6JTI2bJzczYUDOm-PWDyaeyplpSQ==
  Tytuł (wyszukiwarka): wszystkoconajwazniejsze.pl
  Zajawka: Analizy ekspertów i raporty wywiadowcze wskazują na zwiększone ryzyko agresywnych działań Rosji wobec krajów bałtyckich ...

  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---
  Adres końcowy: https://wszystkoconajwazniejsze.pl/pepites/rosja-jest-w-stanie-zaatakowac-nato-juz-w-2027-times/
  Status HTTP: 200
  MIME / kodowanie: text/html; charset=utf-8
  Długość page_text: 9544 znaków
  Pierwsze 200 znaków page_text: 'Rosja jest w stanie zaatakować NATO już w 2027\xa0-\xa0„Times”  Jeśli w tym roku dojdzie do zawieszenia broni w Ukrainie, to Rosja może już w 2027 r. odbudować swoją armię i dokonać inwazji na inne państwa '

  --- KROK 3: EKSTRAKCJA DOWODU ---
  Ścieżka ekstrakcji (path): sentence_selection
  Status ekstraktora: ok
  Telemetria ekstraktora: {web_sentences_offered: 82, web_evidence_from_sentences: 1, web_invalid_sentence_index: 0, web_too_many_sentences: 0}
  Twierdzenie (claim): Rosja może zaatakować kraje bałtyckie do końca 2027 roku.
  Wartość (value): 2027.0 rok
  Metoda ekstrakcji: sentence_selection
  Przedział znakowy (offsets): char_start=0, char_end=300
  Zwrócony cytat (300 zn.): 'Rosja jest w stanie zaatakować NATO już w 2027\xa0-\xa0„Times”\n\nJeśli w tym roku dojdzie do zawieszenia broni w Ukrainie, to Rosja może już w 2027 r. odbudować swoją armię i dokonać inwazji na inne państwa europejskie, w tym kraje NATO – podał w czwartek brytyjski dziennik „Times”, cytując raport think ta'

  --- KROK 4: WERYFIKACJA CYTATU W TEKŚCIE STRONY ---
  Dosłowne dopasowanie (raw quote in raw text): True
  Dopasowanie ze zredukowanymi spacjami (ws-normalized): True
  Dopasowanie po równoważnej normalizacji typografii: True
  >>> STATUS: PASS (Weryfikacja zaliczona standardowo)

[DOKUMENT 2/3]
  Otrzymany URL: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHMsga6RmW2btcftkjWg-OnJzggjJ0IneY-53kAya4k5QprFMFSjdqF6l_n8A_-nJNKWE5XTqNob9N5ueZU7M907AxzRVliJY1ajhZA9iNaFwc56ttF5o-h3ow7x2nsuQ4ov9h-XQTK1Xs092ScXnRu5rwb2YVEss8tjwsD33wYFFJHx42CKquHG_RFAX_7
  Tytuł (wyszukiwarka): defence24.pl
  Zajawka: Analizy ekspertów i raporty wywiadowcze wskazują na zwiększone ryzyko agresywnych działań Rosji wobec krajów bałtyckich ...

  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---
  Adres końcowy: https://defence24.pl/geopolityka/rosja-szykuje-uderzenie-na-baltow-budanow-ostrzega
  Status HTTP: 200
  MIME / kodowanie: text/html; charset=utf-8
  Długość page_text: 5206 znaków
  Pierwsze 200 znaków page_text: 'włącz premium  Wideo  Budanow wypowiedział się na ten temat podczas otwartego wywiadu na posiedzeniu Klubu LB, zorganizowanego przez ukraińskie medium LB.ua. Podkreślił, że Rosja postrzega siebie jako'

  --- KROK 3: EKSTRAKCJA DOWODU ---
  Ścieżka ekstrakcji (path): deterministic_heuristics
  Status ekstraktora: empty_extraction
  Telemetria ekstraktora: {web_sentences_offered: 152, web_evidence_from_sentences: 1, web_invalid_sentence_index: 0, web_too_many_sentences: 0}
  Ekstraktor nie zwrócił zweryfikowanego dowodu (Evidence is None).

[DOKUMENT 3/3]
  Otrzymany URL: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHyAk7ft3HhF4tZZpkarn38GMS3LzPCTTwsT8YXIEg0CUJZEIZPyv25rjLdxX4I4xHtInj30x7-ANxf2HmQNy-9fU6r8M3_Kd2XtlIuRRIBbbL-JYkds-nnYGhsH86whVDvJkCxhHOqKLU5U3hrDoNIPSEzCHwV7PGgryj7_7mxksT-lqdV8AH6IjOpxk96MluksjA12LXsx6gq7PHMBI4IYuoRRVw6yg==
  Tytuł (wyszukiwarka): tokfm.pl
  Zajawka: Analizy ekspertów i raporty wywiadowcze wskazują na zwiększone ryzyko agresywnych działań Rosji wobec krajów bałtyckich ...

  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---
  Adres końcowy: https://www.tokfm.pl/polska/tokfm-7-103085-32169908-polska-zdazy-wzmocnic-armie-do-2027-roku-nie-mamy-wyboru
  Status HTTP: 200
  MIME / kodowanie: text/html; charset=utf-8
  Długość page_text: 8265 znaków
  Pierwsze 200 znaków page_text: 'Polska  Świat  Polityka  Gospodarka  Nauka  Kultura  Blisko ludzi  Wydarzenia  SPORT.PL  Podcasty  TOK FM Premium  ● Teraz w tok fm:  TOK FM Premium - słuchaj wszystkich audycji i podcastów kiedy chce'

  --- KROK 3: EKSTRAKCJA DOWODU ---
  Ścieżka ekstrakcji (path): sentence_selection
  Status ekstraktora: ok
  Telemetria ekstraktora: {web_sentences_offered: 268, web_evidence_from_sentences: 2, web_invalid_sentence_index: 0, web_too_many_sentences: 0}
  Twierdzenie (claim): NATO intelligence warns that Russia may be ready for another armed conflict in 2027, potentially testing Article 5 of the North Atlantic Treaty, while Russians are currently testing the "Baltic corridor."
  Wartość (value): 0.0 null
  Metoda ekstrakcji: sentence_selection
  Przedział znakowy (offsets): char_start=204, char_end=504
  Zwrócony cytat (300 zn.): 'Wywiad NATO ostrzega, że w 2027 roku Rosja może być gotowa do kolejnego konfliktu zbrojnego. Czy Polska zdąży się do tego przygotować? - Nie mamy wyboru. Wszystko to, co powinniśmy zrobić, jesteśmy zobowiązani zrobić. Wszyscy, którzy są odpowiedzialni bezpieczeństwo kraju - mówił w TOK FM poseł PSL '

  --- KROK 4: WERYFIKACJA CYTATU W TEKŚCIE STRONY ---
  Dosłowne dopasowanie (raw quote in raw text): True
  Dopasowanie ze zredukowanymi spacjami (ws-normalized): True
  Dopasowanie po równoważnej normalizacji typografii: True
  >>> STATUS: PASS (Weryfikacja zaliczona standardowo)

================================================================================
DIAGNOZA ZAPYTANIA: Czy Polska wybuduje pierwszą elektrownię jądrową do 2033 roku?
================================================================================
Status adaptera wyszukiwania: {provider: gemini, mode: grounding_urls_only, can_fetch_content: False, is_available: True, queries_performed: 0, max_session_queries: 15, has_mock_fixtures: False}

--- KROK 1: WYSZUKIWANIE (Gemini Search Grounding) ---
Zwrócono adresów URL: 3

[DOKUMENT 1/3]
  Otrzymany URL: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF1DO-l2aCwIHihiSDA6ujkCM9IHsN4sj7qS9DBKBnYBpXpORyzN4Mxf0CglG4RfQHIyNW2h522ogl2x_dwSGXOpDe3ABZRXwRsw9e1d0Lj8bnL4EKLvR5QstC6dPUXb_OQ4G45LpmzdEQhlqp1XUWJLG0Xw18_PmfQq8oz24kH6QlvWa-7oR63VlMus-GGTk_pLAa9PKu8daL82VvtxWJQB3D7lZNGz6pGzed6HG0qgpBeQn0=
  Tytuł (wyszukiwarka): world-nuclear.org
  Zajawka: Zgodnie z aktualnymi informacjami i harmonogramami, Polska nie wybuduje pierwszej elektrowni jądrowej do 2033 roku. Pier...

  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---
  Adres końcowy: https://world-nuclear.org/our-association/publications/world-nuclear-outlook-report/poland---world-nuclear-outlook-report
  Status HTTP: 200
  MIME / kodowanie: text/html; charset=utf-8
  Długość page_text: 3298 znaków
  Pierwsze 200 znaków page_text: 'HOME / OUR ASSOCIATION / Publications / world nuclear outlook report / Poland - World Nuclear Outlook Report  Poland - World Nuclear Outlook Report  Updated Wednesday, 21 January 2026  Projection of f'

  --- KROK 3: EKSTRAKCJA DOWODU ---
  Ścieżka ekstrakcji (path): sentence_selection
  Status ekstraktora: ok
  Telemetria ekstraktora: {web_sentences_offered: 23, web_evidence_from_sentences: 1, web_invalid_sentence_index: 0, web_too_many_sentences: 0}
  Twierdzenie (claim): Polska planuje uruchomić swoją pierwszą elektrownię jądrową do 2033 roku.
  Wartość (value): 2033.0 rok
  Metoda ekstrakcji: sentence_selection
  Przedział znakowy (offsets): char_start=543, char_end=843
  Zwrócony cytat (300 zn.): 'In 2009, the Polish government decided to initiate a new nuclear power programme in the country.222 In Energy Policy of Poland until 2040 (EPP2040), adopted in 2021, Poland planned to bring its first unit online by 2033, and subsequent units every 2-3 years, leading to the construction a total capac'

  --- KROK 4: WERYFIKACJA CYTATU W TEKŚCIE STRONY ---
  Dosłowne dopasowanie (raw quote in raw text): True
  Dopasowanie ze zredukowanymi spacjami (ws-normalized): True
  Dopasowanie po równoważnej normalizacji typografii: True
  >>> STATUS: PASS (Weryfikacja zaliczona standardowo)

[DOKUMENT 2/3]
  Otrzymany URL: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEDzrDghGm9eCFdcSXMuh3cSLNSN7DrPV4iRb2_skouYnwnG9XDeTHLgBrv79ce7bmdmgN3MesAEGnDrbH4_g_5SL5wHSOPD69-0pKZ4eAxoGGthpRdQRMTY0AGMpdoaxmRwh_p5rEwQZuRdsEaZkkYABpoGR4Vh49QN1ZK3iLUO-ulGqr-7ql4dNq5VfSG
  Tytuł (wyszukiwarka): world-nuclear.org
  Zajawka: Zgodnie z aktualnymi informacjami i harmonogramami, Polska nie wybuduje pierwszej elektrowni jądrowej do 2033 roku. Pier...

  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---
  Adres końcowy: https://world-nuclear.org/information-library/country-profiles/countries-o-s/poland
  Status HTTP: 200
  MIME / kodowanie: text/html; charset=utf-8
  Długość page_text: 36620 znaków
  Pierwsze 200 znaków page_text: 'HOME / Information Library / country profiles / countries-o-s / Poland  country profiles  Nuclear Power in Poland  Updated Monday, 6 July 2026  Poland plans to have nuclear power from about 2036\xa0as pa'

  --- KROK 3: EKSTRAKCJA DOWODU ---
  Ścieżka ekstrakcji (path): sentence_selection
  Status ekstraktora: ok
  Telemetria ekstraktora: {web_sentences_offered: 172, web_evidence_from_sentences: 2, web_invalid_sentence_index: 0, web_too_many_sentences: 0}
  Twierdzenie (claim): Polska nie planuje wybudować pierwszej elektrowni jądrowej do 2033 roku; zaktualizowany harmonogram przewiduje uruchomienie pierwszego reaktora w 2036 roku.
  Wartość (value): 2036.0 null
  Metoda ekstrakcji: sentence_selection
  Przedział znakowy (offsets): char_start=144, char_end=444
  Zwrócony cytat (300 zn.): 'Poland plans to have nuclear power from about 2036\xa0as part of a diverse energy portfolio, moving it away from heavy dependence on coal.\n\nPoland\xa0earlier considered a stake in the planned Visaginas nuclear power plant in Lithuania.\n\nPolls show strong support among the public for the construction of th'

  --- KROK 4: WERYFIKACJA CYTATU W TEKŚCIE STRONY ---
  Dosłowne dopasowanie (raw quote in raw text): True
  Dopasowanie ze zredukowanymi spacjami (ws-normalized): True
  Dopasowanie po równoważnej normalizacji typografii: True
  >>> STATUS: PASS (Weryfikacja zaliczona standardowo)

[DOKUMENT 3/3]
  Otrzymany URL: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEMJh6LdkuI3w2zK6bLIHHRuaSVlk07aG2KeKT2ihZemt_ew5YeFsuioTfDLijjeI4T7TGBWVAdmqxfDs5VKfr0ByqVmkTwOEy8nR6sTbU1jjEC67w8yHotTsjF3GXfN73_Q2DRRsRjlG7VT5c50FrzFL_cuSe_bNGckoLXQGSr3rgeXK2ujNgrWSS6LzZudTiBqniROnC8taB_pK-b_-ySAE6hDX6TMA==
  Tytuł (wyszukiwarka): radiokierowcow.pl
  Zajawka: Zgodnie z aktualnymi informacjami i harmonogramami, Polska nie wybuduje pierwszej elektrowni jądrowej do 2033 roku. Pier...

  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---
  Adres końcowy: https://radiokierowcow.pl/artykul/2606390,polski-program-jadrowy-pierwsza-elektrownia-ma-dzialac-w-2033-roku
  Status HTTP: 200
  MIME / kodowanie: text/html; charset=utf-8
  Długość page_text: 0 znaków
  Pierwsze 200 znaków page_text: ''
  Dokument pusty (brak tekstu po usunięciu HTML). Ekstrakcja niemożliwa.

================================================================================
DIAGNOZA ZAPYTANIA: Czy inflacja w Polsce spadnie poniżej celu NBP do końca 2026 roku?
================================================================================
Status adaptera wyszukiwania: {provider: gemini, mode: grounding_urls_only, can_fetch_content: False, is_available: True, queries_performed: 0, max_session_queries: 15, has_mock_fixtures: False}

--- KROK 1: WYSZUKIWANIE (Gemini Search Grounding) ---
Zwrócono adresów URL: 3

[DOKUMENT 1/3]
  Otrzymany URL: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEzW5-9VXiDqEj4QjT8uVMewKEBdGlRArN8hwcKEso_LckZ-7VpzPWMDWPUV9rLV0mu2xRHrP_V5EBKny6iS_bpHS7oWxyowOvF56x0x6-CtUVKe1-umERHvdOR4sI=
  Tytuł (wyszukiwarka): nbp.pl
  Zajawka: Narodowy Bank Polski (NBP) utrzymuje średniookresowy cel inflacyjny na poziomie 2,5% z dopuszczalnym symetrycznym przedz...

  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---
HTTP 403 when fetching https://nbp.pl/polityka-pieniezna/
  WYNIK POBIERANIA: None (np. zablokowany SSRF, timeout lub błąd HTTP).

[DOKUMENT 2/3]
  Otrzymany URL: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHxU16x8JUdAZjDhRpZb4CDDqRfHlbVe69mk4fbBAJmkaSTCHb5GPyW58HQts8mj4hPtIDe_HdpiT9Kss02dYB2QwFf-puHbfazSuW4lESgqaEm1-rok_SRsMRX6lgSc0RSv5XRFbcHFPGbWPltAjOI4yFla643STZHXWVWqn2BKbCMZNGtXc-gVuVbkToVHdHkitNPsqhKWAgfqEwMGXk7asLs2s0799t4bFFEn3nGxNZ68Z9_vE63ylHjRsvWSvwb161IlGzWgHsEZaucKFAB5sdJMpaK5iXy15DBB10atA==
  Tytuł (wyszukiwarka): facebook.com
  Zajawka: Narodowy Bank Polski (NBP) utrzymuje średniookresowy cel inflacyjny na poziomie 2,5% z dopuszczalnym symetrycznym przedz...

  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---
  Adres końcowy: https://www.facebook.com/reel/1446628813815604/
  Status HTTP: 200
  MIME / kodowanie: text/html; charset="utf-8"
  Długość page_text: 0 znaków
  Pierwsze 200 znaków page_text: ''
  Dokument pusty (brak tekstu po usunięciu HTML). Ekstrakcja niemożliwa.

[DOKUMENT 3/3]
  Otrzymany URL: https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHgwK4gZ2XFJQSg3B5l2idanC8PcJjCWnBuLdSviizDzW0TpQ3ORu3X8ApNGVdC43EdHTLJcCOfgIprJmtGhOqTgBtGwrlyO3U9bl9771KuVpLN2opD0n-s2xFbnbEp9jq2t129lIA3TD0f3bufkx2JzWc7ijboIYlzJorQuIZnPRFLDL2rK_SNIjVe9VfCjcRjkdMfqEJS1tx0lJzi6tWayV4VKhY2
  Tytuł (wyszukiwarka): businessinsider.com.pl
  Zajawka: Narodowy Bank Polski (NBP) utrzymuje średniookresowy cel inflacyjny na poziomie 2,5% z dopuszczalnym symetrycznym przedz...

  --- KROK 2: POBIERANIE PRZEZ SafeWebFetcher ---
  Adres końcowy: https://businessinsider.com.pl/gospodarka/wiemy-co-dalej-z-inflacja-nbp-publikuje-kluczowy-dokument/d6p5jm1
  Status HTTP: 200
  MIME / kodowanie: text/html; charset=utf-8
  Długość page_text: 11701 znaków
  Pierwsze 200 znaków page_text: 'Business InsiderGospodarkaWiemy, co dalej z inflacją. NBP publikuje kluczowy dokument  Wiemy, co dalej z inflacją. NBP publikuje kluczowy dokument  Opracowanie: Jakub Ceglarz  7 listopada 2025, 9:06. '

  --- KROK 3: EKSTRAKCJA DOWODU ---
  Ścieżka ekstrakcji (path): sentence_selection
  Status ekstraktora: ok
  Telemetria ekstraktora: {web_sentences_offered: 159, web_evidence_from_sentences: 1, web_invalid_sentence_index: 0, web_too_many_sentences: 0}
  Twierdzenie (claim): Według centralnej ścieżki projekcji Narodowego Banku Polskiego, inflacja w Polsce w 2026 r. ma wynieść średniorocznie 2,9 proc., a cel inflacyjny NBP wynosi 2,5 proc. z dopuszczalnym odchyleniem 1 pkt proc.
  Wartość (value): 2.9 proc.
  Metoda ekstrakcji: sentence_selection
  Przedział znakowy (offsets): char_start=400, char_end=700
  Zwrócony cytat (300 zn.): 'Według centralnej ścieżki w 2026 r. wskaźnik powinien wynieść średniorocznie 2,9 proc. Wiele wskazuje na to, że do 2027 r. możemy zapomnieć o problemie inflacji.\n\nAdam Glapiński, prezes NBP i przewodniczący RPP.\n\n|\n\nFoto:\n\nNBP / Flickr\n\nInflacja w tym roku ma wynieść średniorocznie 3,7 proc., a w pr'

  --- KROK 4: WERYFIKACJA CYTATU W TEKŚCIE STRONY ---
  Dosłowne dopasowanie (raw quote in raw text): True
  Dopasowanie ze zredukowanymi spacjami (ws-normalized): True
  Dopasowanie po równoważnej normalizacji typografii: True
  >>> STATUS: PASS (Weryfikacja zaliczona standardowo)
```

---

### Komenda 4: `git log --oneline 379d9cf..HEAD`
```text
3353e9f (HEAD -> main, origin/main) docs(V14-8): add final V14 empirical report and update CURRENT_STATE
2dd67b1 docs(V14-6): rectify REPORT_V13, update DEC-036 and add DEC-038 for V13/V14 architecture
894fc23 feat(V14-1): extract quotes via backend sentence selection instead of LLM transcription
d1e885e feat(V14-5): parallelize web fetching with asyncio.gather, add intake_wall_time_seconds and configure vercel maxDuration
d2fe298 feat(V14-4): add single retry for scenario decomposition and track telemetry
ccb06a0 fix(V14-3): unify scenario forecast query definition and quality gate handling
e30b8ba fix(V14-2): fix needs_clarification explanation, questions and forbid extra fields in FormalizationResult
```

---

### Komenda 5: `git rev-parse HEAD origin/main`
```text
3353e9f13be0f2cb4d7406e2abea333f69f077c7
3353e9f13be0f2cb4d7406e2abea333f69f077c7
```

---

### Komenda 6: `curl -s -X POST "https://yourquantum.pl/api/v1/cognitive/intake" -H "Content-Type: application/json" -d '{"query":"Czy Rosja do końca tego roku napadnie na Polskę?"}'`
```json
{"status":"ready_for_review","problem_ir":null,"decision_case":{"id":"case_ece60c5e","title":"Analiza scenariuszy ryzyka: Czy Rosja do końca tego roku napadnie na Polskę?","context":"Czy Rosja do końca tego roku napadnie na Polskę?","status":"intake","facts":[],"options":[{"id":"SCN001","title":"Brak ataku Rosji na Polskę do końca 2026 roku (Szacunek szans: 33,3%)","description":"Rosja nie podejmuje żadnych działań militarnych ani znaczących działań hybrydowych bezpośrednio wymierzonych w terytorium Polski do 31 grudnia 2026 roku. Obejmuje to brak inwazji, cyberataków na dużą skalę z atrybucją państwową, czy prowokacji granicznych o charakterze militarnym.","pros":["Wariant o niskim poziomie ryzyka, wspierany przez stabilizujące wskaźniki."],"cons":["Wymaga utrzymania warunków brzegowych i założeń decydenta."],"attributes":{"probability":0.3333,"risk_level":"LOW","evidence_score":0.0}},{"id":"SCN002","title":"Ograniczone działania hybrydowe lub cybernetyczne Rosji przeciwko Polsce do końca 2026 roku (Szacunek szans: 33,3%)","description":"Rosja prowadzi działania destabilizujące, takie jak intensywne cyberataki na infrastrukturę krytyczną, operacje dezinformacyjne, prowokacje graniczne lub wspieranie niepaństwowych aktorów, bez bezpośredniego użycia regularnych sił zbrojnych na terytorium Polski do 31 grudnia 2026 roku. Działania te mają na celu osłabienie państwa polskiego i jego pozycji w NATO.","pros":["Scenariusz pośredni / umiarkowany."],"cons":["Generuje niepewność co do ostatecznego kierunku rozwoju sytuacji."],"attributes":{"probability":0.3333,"risk_level":"MEDIUM","evidence_score":0.0}},{"id":"SCN003","title":"Pełnoskalowa inwazja wojskowa Rosji na Polskę do końca 2026 roku (Szacunek szans: 33,3%)","description":"Rosja podejmuje zbrojną agresję na dużą skalę, angażując regularne siły wojskowe w celu zajęcia lub destabilizacji terytorium Polski do 31 grudnia 2026 roku. Scenariusz ten zakłada bezpośrednie starcie militarne z siłami polskimi i NATO.","pros":["Scenariusz skrajny; pozwala przygotować plany awaryjne."],"cons":["Wiąże się z wysokim ryzykiem niepowodzenia lub strat."],"attributes":{"probability":0.3333,"risk_level":"CRITICAL","evidence_score":0.0}}],"criteria":[{"id":"PRM001","name":"Skala zaangażowania NATO w obronę wschodniej flanki","direction":"maximize","weight":1.0,"unit":"wpływ","is_mandatory":false,"threshold":null},{"id":"PRM002","name":"Zdolność Rosji do kontynuowania działań ofensywnych po zakończeniu konfliktu na Ukrainie","direction":"maximize","weight":1.0,"unit":"wpływ","is_mandatory":false,"threshold":null},{"id":"PRM003","name":"Wysoka stabilność polityczna i gospodarcza Rosji","direction":"maximize","weight":1.0,"unit":"wpływ","is_mandatory":false,"threshold":null},{"id":"PRM004","name":"Poziom jedności i determinacji państw NATO","direction":"maximize","weight":1.0,"unit":"wpływ","is_mandatory":false,"threshold":null}],"unknowns":[],"tradeoffs":[],"priority_tokens":[],"selected_priority_tokens":[],"score_matrix":{"SCN001":{"PRM001":{"value":9.1,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0},"PRM002":{"value":2.4,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0},"PRM003":{"value":3.2,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0},"PRM004":{"value":9.6,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0}},"SCN002":{"PRM001":{"value":3.7,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0},"PRM002":{"value":7.8,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0},"PRM003":{"value":7.3,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0},"PRM004":{"value":3.2,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0}},"SCN003":{"PRM001":{"value":1.0,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0},"PRM002":{"value":9.6,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0},"PRM003":{"value":8.7,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0},"PRM004":{"value":1.0,"unit":"skala 1-10","provenance":"llm_suggested","source_ref":"Propozycja modelu","confidence":1.0}}},"break_even_point":null,"input_quality":{"level":"sufficient","reason":"","suggestions":[]},"created_at":"2026-09-17T21:58:41.921204Z","updated_at":"2026-09-17T21:58:41.921211Z","problem_ir_id":null},"problem_class":"CHOICE","input_quality":null,"not_computable_report":null,"research_queries":[],"break_even_point":null,"questions":[],"explanation":"Ważona agregacja przesłanek empirycznych z jawną funkcją softmax wyznaczyła rozkład scenariuszy: z wynikiem bazowym 33,3% (przedział wrażliwości: 33,3%–33,3%, umiarkowane prawdopodobieństwo (ok. 20–49 szans na 100)) przeważa wariant: 'Brak ataku Rosji na Polskę do końca 2026 roku'. Wynik jest analityczną konsekwencją 0 przyjętych przesłanek dowodowych i podlega natychmiastowemu przeliczeniu przy modyfikacji ich wag lub założeń decydenta.","raw_query":"Czy Rosja do końca tego roku napadnie na Polskę?","fingerprint":"fp_325be511540580cf_6","confidence":0.98,"penalty_multipliers":{},"session_id":"2d601293-e657-431d-ac64-1efbab95b6ba","formalized":null,"design_problem":null,"scenario_forecast":{"query":"Czy Rosja do końca tego roku napadnie na Polskę?","domain":"Analiza scenariuszowa i badanie ryzyka","scenarios":[{"id":"SCN001","title":"Brak ataku Rosji na Polskę do końca 2026 roku","description":"Rosja nie podejmuje żadnych działań militarnych ani znaczących działań hybrydowych bezpośrednio wymierzonych w terytorium Polski do 31 grudnia 2026 roku. Obejmuje to brak inwazji, cyberataków na dużą skalę z atrybucją państwową, czy prowokacji granicznych o charakterze militarnym.","probability":0.3333,"evidence_score":0.0,"risk_level":"LOW"},{"id":"SCN002","title":"Ograniczone działania hybrydowe lub cybernetyczne Rosji przeciwko Polsce do końca 2026 roku","description":"Rosja prowadzi działania destabilizujące, takie jak intensywne cyberataki na infrastrukturę krytyczną, operacje dezinformacyjne, prowokacje graniczne lub wspieranie niepaństwowych aktorów, bez bezpośredniego użycia regularnych sił zbrojnych na terytorium Polski do 31 grudnia 2026 roku. Działania te mają na celu osłabienie państwa polskiego i jego pozycji w NATO.","probability":0.3333,"evidence_score":0.0,"risk_level":"MEDIUM"},{"id":"SCN003","title":"Pełnoskalowa inwazja wojskowa Rosji na Polskę do końca 2026 roku","description":"Rosja podejmuje zbrojną agresję na dużą skalę, angażując regularne siły wojskowe w celu zajęcia lub destabilizacji terytorium Polski do 31 grudnia 2026 roku. Scenariusz ten zakłada bezpośrednie starcie militarne z siłami polskimi i NATO.","probability":0.3333,"evidence_score":0.0,"risk_level":"CRITICAL"}],"dominant_scenario_id":"SCN001","evidence_premises":[{"id":"PRM001","name":"Skala zaangażowania NATO w obronę wschodniej flanki","description":"Wzrost liczby wojsk, sprzętu i infrastruktury NATO na wschodniej flance, w tym w Polsce, oraz wzmocnienie zdolności odstraszania i obrony kolektywnej. Waga nie została wyliczona z dokumentów; ustaw ją samodzielnie, jeżeli chcesz zróżnicować znaczenie przesłanek.","source":"Propozycja modelu","confidence":1.0,"weight":1.0,"impact_on_scenarios":{"SCN001":0.8,"SCN002":-0.4,"SCN003":-1.0},"provenance":"llm_suggested","source_ref":"propozycja modelu","is_accepted":false},{"id":"PRM002","name":"Zdolność Rosji do kontynuowania działań ofensywnych po zakończeniu konfliktu na Ukrainie","description":"Ocena, czy Rosja, po zakończeniu lub znaczącym etapie konfliktu na Ukrainie, będzie posiadała wystarczające zasoby militarne i polityczną wolę do podjęcia dalszych działań ofensywnych przeciwko innym państwom. Waga nie została wyliczona z dokumentów; ustaw ją samodzielnie, jeżeli chcesz zróżnicować znaczenie przesłanek.","source":"Propozycja modelu","confidence":1.0,"weight":1.0,"impact_on_scenarios":{"SCN001":-0.7,"SCN002":0.5,"SCN003":0.9},"provenance":"llm_suggested","source_ref":"propozycja modelu","is_accepted":false},{"id":"PRM003","name":"Wysoka stabilność polityczna i gospodarcza Rosji","description":"Wskaźniki takie jak wysokie poparcie dla władz, stabilny wzrost gospodarczy (pomimo sankcji) i brak znaczących wewnętrznych niepokojów społecznych w Rosji. Waga nie została wyliczona z dokumentów; ustaw ją samodzielnie, jeżeli chcesz zróżnicować znaczenie przesłanek.","source":"Propozycja modelu","confidence":1.0,"weight":1.0,"impact_on_scenarios":{"SCN001":-0.5,"SCN002":0.4,"SCN003":0.7},"provenance":"llm_suggested","source_ref":"propozycja modelu","is_accepted":false},{"id":"PRM004","name":"Poziom jedności i determinacji państw NATO","description":"Spójność polityczna i wojskowa państw członkowskich NATO w kwestii reagowania na zagrożenia ze strony Rosji oraz utrzymania wspólnej polityki obronnej i odstraszania. Waga nie została wyliczona z dokumentów; ustaw ją samodzielnie, jeżeli chcesz zróżnicować znaczenie przesłanek.","source":"Propozycja modelu","confidence":1.0,"weight":1.0,"impact_on_scenarios":{"SCN001":0.9,"SCN002":-0.5,"SCN003":-1.0},"provenance":"llm_suggested","source_ref":"propozycja modelu","is_accepted":false}],"tipping_points":["Niewystarczająca liczba scenariuszy lub przesłanek do wyznaczenia punktów zwrotnych."],"tipping_point_details":[],"sensitivity_band":{"beta_0.5":{"SCN001":0.3333,"SCN002":0.3333,"SCN003":0.3333},"beta_1.0":{"SCN001":0.3333,"SCN002":0.3333,"SCN003":0.3333},"beta_2.0":{"SCN001":0.3333,"SCN002":0.3333,"SCN003":0.3333},"beta_3.0":{"SCN001":0.3333,"SCN002":0.3333,"SCN003":0.3333}},"telemetry":{"method":"weighted_softmax_aggregation","beta":1.0,"n_scenarios":3,"n_premises":4,"n_active_premises":0,"dominant_scenario":"Brak ataku Rosji na Polskę do końca 2026 roku","dominant_probability":0.3333,"dominant_sensitivity_band":"33,3%–33,3%","solve_time_seconds":0.0024,"time_horizon":{"raw":"do końca tego roku","label":"do końca 2026 roku","end_date":"2026-12-31","basis":"current_year","is_precise":true},"unspecified_impacts_count":0,"web_sourced_premises_without_model_impacts":0,"search_provider":"gemini","search_mode":"grounding_urls_only","can_fetch_content":false,"web_search_urls_returned":3,"web_pages_fetched":3,"web_quotes_verified":0,"web_docs_empty":0,"web_extractor_no_evidence":3,"web_quotes_unverified":0},"briefing":{"headline":"Rozkład scenariuszowy: Brak ataku Rosji na Polskę do końca 2026 roku (33,3% / pasmo: 33,3%–33,3%)","executive_summary":"Ważona agregacja przesłanek empirycznych z jawną funkcją softmax wyznaczyła rozkład scenariuszy: z wynikiem bazowym 33,3% (przedział wrażliwości: 33,3%–33,3%, umiarkowane prawdopodobieństwo (ok. 20–49 szans na 100)) przeważa wariant: 'Brak ataku Rosji na Polskę do końca 2026 roku'. Wynik jest analityczną konsekwencją 0 przyjętych przesłanek dowodowych i podlega natychmiastowemu przeliczeniu przy modyfikacji ich wag lub założeń decydenta.","key_pillars":[],"primary_tradeoff":"Dominacja wariantu 'Brak ataku Rosji na Polskę do końca 2026 roku' zależy bezpośrednio od parametru ostrości rozkładu beta (wynik waha się od 33,3%–33,3%).","tipping_points":["Niewystarczająca liczba scenariuszy lub przesłanek do wyznaczenia punktów zwrotnych."]}},"metadata":{"classification_reason":"Analiza prawdopodobieństwa scenariuszy i ryzyka metodą ważonej agregacji softmax.","dominant_scenario_id":"SCN001","telemetry":{"method":"weighted_softmax_aggregation","beta":1.0,"n_scenarios":3,"n_premises":4,"n_active_premises":0,"dominant_scenario":"Brak ataku Rosji na Polskę do końca 2026 roku","dominant_probability":0.3333,"dominant_sensitivity_band":"33,3%–33,3%","solve_time_seconds":0.0024,"time_horizon":{"raw":"do końca tego roku","label":"do końca 2026 roku","end_date":"2026-12-31","basis":"current_year","is_precise":true},"unspecified_impacts_count":0,"web_sourced_premises_without_model_impacts":0,"search_provider":"gemini","search_mode":"grounding_urls_only","can_fetch_content":false,"web_search_urls_returned":3,"web_pages_fetched":3,"web_quotes_verified":0,"web_docs_empty":0,"web_extractor_no_evidence":3,"web_quotes_unverified":0},"web_sources_count":3,"web_search_urls_returned":3,"web_pages_fetched":3,"web_quotes_verified":0}}
```

---

Audyt objął 23 polecenia: 7 zgodnych, 6 odstępstw, 10 niewykonanych. Osiem reguł bezwzględnych: 6 spełnionych, 2 niespełnionych.

---

## 5. Zamknięcie niezgodności po wdrożeniu zlecenia V16 (2026-09-18)

Wszystkie odstępstwa i niewykonane polecenia zidentyfikowane w niniejszym audycie zostały w całości zrealizowane, zweryfikowane mechanicznie i wdrożone produkcyjnie w ramach zlecenia **PROMPT V16: ZAMKNIĘCIE SPRAWY** (commit `c8b119d` na `main`):

1. **V13-2 & V14-6 (Długi dokumentacyjne REPORT_V13)**: Zamknięte. Gałąź zaktualizowana do `main`, wskaźniki bundla zaktualizowane do rzeczywistego stanu produkcyjnego.
2. **V14-1 & V15-7 (Offsety zdań i cytatów)**: Zamknięte. Zaimplementowano funkcję `slice_sentence_cluster` dzielącą nieprzyległe zdania na osobne instancje `Evidence`, ucinającą cytat do granic zdań z zachowaniem `char_end - char_start == len(quote)`.
3. **V14-8 & V15-4 (Sprostowanie raportu V14 i bramka G-EVID)**: Zamknięte. Sekcja 3A i 3B w `docs/REPORT_V14.md` zawiera rzeczywisty log narzędzia diagnostycznego oraz realny czas testów (4m 42s). Bramka `G-EVID` (`scripts/check_report_evidence.py`) została zintegrowana ze `scripts/check_v4.sh` (25/25 bramek PASS).
4. **V14-9, V15-3 & Reguła 5 (Usunięcie wyłuskiwania liczb z heurystyki)**: Zamknięte. Metoda `_extract_via_deterministic_heuristics` zwraca `value = None` oraz `confidence = 0.0`.
5. **V15-1 & DEC-039 (Automatyczne wchodzenie udokumentowanych przesłanek)**: Zamknięte. Wprowadzono 5 rygorystycznych kryteriów w `scenario_decomposer.py`. Udokumentowane przesłanki sieciowe otrzymują `is_accepted = True`, dając `n_active_premises >= 1` i rozkład ważony softmax.
6. **V15-2 (Uzasadnienie wpływu)**: Zamknięte. Model wskazuje indeks zdania ze zbioru cytatu w strukturze `impact_justification`.
7. **V15-6 & V16-7 (Uczciwość UI)**: Zamknięte. Wprowadzono `ActivePremisesEmptyBanner` w `RecommendationView.tsx` wyświetlany przy zerze aktywnych przesłanek mimo obecności zweryfikowanych cytatów.
8. **V15-7 & Reguła 4 (Usunięcie self.__dict__)**: Zamknięte. Usunięto inspekcję testów z `extractor.py` (`grep -rn "self.__dict__" backend/` zwraca 0 trafień).
9. **V14-5 & V15-5 (Wdrożenie produkcyjne i dowód `intake_wall_time_seconds`)**: Zamknięte. Zsynchronizowano `origin/main` (`c8b119d`), wdrożono na Vercel CLI (`assets/index-DEOMvVS2.js`), potwierdzono pole `intake_wall_time_seconds: 53.5065`, `n_active_premises: 2` oraz asymetryczny rozkład `dominant_probability: 0.6883`.

Szczegółowy opis techniczny i dowody pomiarowe znajdują się w [docs/REPORT_V16.md](file:///Users/macbookpro/PROJEKTY/YOURQUANTUM/docs/REPORT_V16.md).
