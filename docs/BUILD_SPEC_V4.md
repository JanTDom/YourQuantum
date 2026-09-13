# YOURQUANTUM — OSTATECZNY PROMPT KORYGUJĄCY V4 DLA ANTIGRAVITY
_Wersja: 2026-09-13, po drugim audycie · Zastępuje `docs/BUILD_SPEC_V3.md` (który nie został wykonany) · Autor zlecenia: Jan Domaniewski_

---

## 0. STAN FAKTYCZNY, OD KTÓREGO ZACZYNASZ

Drugi audyt repozytorium (gałąź `main`, HEAD `1cdc448`) ustalił:

1. **`docs/BUILD_SPEC_V3.md` nie został wykonany.** Od merge V2 (`4659817`) w repo jest dokładnie jeden nowy commit: `1cdc448 feat(search): enable native Google Search Grounding via existing GEMINI_API_KEY`. Nie ma gałęzi `fix/v3-corrections`, nie ma `docs/REPORT_V3.md`, nie ma `Dockerfile`, nie ma `requirements-api.txt`. Wszystkie punkty R1–R5 i N1–N11 z V3 są w kodzie w stanie sprzed V3 (sprawdzone grepem 2026-09-13: cztery literały GUS/WHO/OECD/NFZ w `RecommendationView.tsx`, `getDesignFixture('healthcare_pl')` w linii 54, sześć wystąpień `A132a132!` w `ApiPortalModal.tsx` i jedno w `AppHeader.tsx`, domyślny klucz podpisu w `verifier.py:27`, `httpx.post` w `formalizer.py:494/664`, `httpx.Client` w `llm_advisor.py:338`, `schema_version = "0.2"` w `problem_ir.py:179`, zero wywołań `researchEvidence` w komponentach).
2. **Jedyny nowy commit wprowadza kolejne naruszenie zasady kardynalnej** (opis w R6 poniżej): tekst wygenerowany przez Gemini jest zapisywany jako `page_text` dokumentu dowodowego pod adresem URL cudzej strony, przez co weryfikacja cytatu (`_verify_quote_in_text`) potwierdza cytaty z halucynacji modelu, a nie ze strony. Dodatkowo `https://google.com/search` bywa wpisywane jako „źródło".
3. **Produkcja bez zmian:** `GET https://yourquantum.pl/api/v1/health/solvers` nadal zwraca `{"solvers":[{"name":"cp_sat","version":"unknown"},{"name":"qaoa_aer","version":"not_installed"},{"name":"hybrid_benders","version":"0.1.0"}]}` — stary kod, bez pola `available`.
4. Cache pytest: 158 nodeids, `lastfailed` pusty — testy przechodzą, ale testują nie to, co jest zepsute.

Ten prompt jest **samowystarczalny**: zawiera całą treść V3 plus R6 i nowy protokół wykonania. Nie musisz czytać V3.

---

## 1. PROTOKÓŁ WYKONANIA — OBOWIĄZKOWY, BEZ WYJĄTKÓW

1. Wykonaj Session Start Protocol z `AGENTS.md` §3. Zapisz ten prompt verbatim jako `docs/BUILD_SPEC_V4.md`. Utwórz gałąź `fix/v4-corrections` od `main`.
2. **Zanim zmienisz jakikolwiek plik produktu**, utwórz `scripts/check_v4.sh` — skrypt mechanicznych bramek z sekcji 6. Uruchom go i wklej wynik do `docs/memory/CURRENT_STATE.md` jako „stan przed V4". Skrypt **musi być czerwony** na starcie; jeśli jest zielony, jest źle napisany.
3. **Zanim zmienisz jakikolwiek plik produktu**, utwórz `docs/V4_PLAN.md`: tabela z wierszem dla każdego ID (R1–R6, N1–N11), kolumny: pliki do zmiany, test dowodowy, szacowana kolejność. To jest Twoje potwierdzenie, że przeczytałeś całość. Bez tej tabeli nie ruszaj kodu.
4. **Jeden ID = jeden commit** (lub seria commitów z tym samym ID w tytule): `fix(R1): …`, `feat(N3): …`. Commit bez ID w tytule jest niedozwolony. Commity spoza listy (jak `1cdc448`) są niedozwolone — jeśli uważasz, że coś jeszcze trzeba zrobić, dopisz to do sekcji „Propozycje" w `V4_PLAN.md` i **nie implementuj** bez zgody Jana.
5. Kolejność wykonania: **R6 → R1 → R2 → R3 → R5 → R4 → N1 → N2 → N3 → N4 → N5 → N6 → N7 → N8 → N9 → N11 → N10**. Nie przeskakuj. Po każdym ID: `scripts/check_v4.sh` + `pytest` + `npm run build`; wynik do `CURRENT_STATE.md`.
6. Reguła dowodu (`AGENTS.md` §7), zakaz fabrykowania (`BUILD_SPEC_V2.md` §1 pkt 4) i zasada „nie wolno napisać, że plik istnieje, bez ścieżki, która istnieje" obowiązują bez wyjątków. W konflikcie wygrywa `AGENTS.md`.
7. Raport końcowy (`docs/REPORT_V4.md`) w numeracji tego promptu; „nie zrobiono" i „częściowo" są dozwolone; ich brak przy niezrobionym punkcie — nie.
8. Nie osłabiaj asercji, nie kasuj testów, nie kasuj `.backup/`, nie ruszaj `.env*`.

---

## 2. NOWA REGRESJA Z COMMITU `1cdc448` — WYKONAJ JAKO PIERWSZĄ

**R6. Google Search Grounding zamienia tekst modelu w „dokument źródłowy".**
Dowody (`backend/infrastructure/web_research/search_adapter.py`, metoda `_search_gemini`):
- `text = cand["content"]["parts"][0]["text"]` (odpowiedź wygenerowana przez Gemini) jest zapisywany jako `EvidenceDocument(url=source_url, page_text=text, content_hash=sha256(text))` dla **każdego** `groundingChunk` — czyli pod adresem realnej strony (np. domena instytucji) leży tekst modelu, nie treść strony. `EvidenceExtractor._verify_quote_in_text` porówna cytat z tym tekstem i uzna halucynację za zweryfikowaną. To dokładnie ten mechanizm, który C3 miał wykluczyć („bez tego kroku LLM będzie halucynował liczby z pamięci").
- `fetch_document()` po nieudanym pobraniu zwraca `self._cached_documents.get(url)` — czyli tekst modelu zamiast strony.
- Gdy brak `groundingChunks`, tworzony jest wynik z `url="https://google.com/search"` i `publisher="Google Search"` — źródło fikcyjne.
- `score=0.95` / `0.90` — wartości wymyślone, nie pochodzą z żadnego rankingu.
- `publisher=title` — tytuł strony podszywa się pod wydawcę.
- `GEMINI_API_KEY` staje się domyślnym kluczem wyszukiwania, więc każdy użytkownik z kluczem Gemini dostaje ten kanał automatycznie.
- Test `test_c8_gemini_search_provider_integration` sprawdza tylko, że `provider == "gemini"` — nie testuje niczego z powyższego.

Wymagane:
1. Grounding wolno używać **wyłącznie jako źródła kandydatów URL** (`groundingChunks[].web.uri` + tytuł). `snippet` może pochodzić z tekstu modelu, ale musi być oznaczony `snippet_origin="llm"` i **nigdy** nie trafia do `page_text`, `content_hash` ani do weryfikacji cytatu.
2. Każdy URL z groundingu przechodzi przez `SafeWebFetcher.fetch()`; `page_text` to wyłącznie treść pobranej strony. Fetch nieudany = brak dokumentu = brak dowodu (`Evidence` nie powstaje). Usuń `_cached_documents` jako fallback dla `fetch_document`.
3. Usuń pseudoźródło `https://google.com/search`. Brak chunków = pusta lista wyników.
4. `score` z groundingu = `None` (pole opcjonalne), `publisher` = domena z URL lub `None`.
5. Dobór dostawcy jawny: `SEARCH_PROVIDER=gemini|tavily|serper|none`; sam `GEMINI_API_KEY` nie włącza wyszukiwania. `get_status()` raportuje `provider` i `mode` („grounding_urls_only").
6. Testy: (a) mock odpowiedzi groundingu z chunkiem `https://example.test/a` + mock fetchera zwracający stronę o innej treści niż tekst modelu → cytat z tekstu modelu **odrzucony**, cytat ze strony **przyjęty**; (b) fetch nieudany → 0 dowodów; (c) brak chunków → 0 wyników, brak URL `google.com`; (d) grep `search_adapter.py` po `google.com/search` = 0.
7. Zapisz DEC-029: „Grounding LLM = lista URL, nie dowód".

---
## 3. CO JEST POTWIERDZONE W KODZIE (nie ruszaj, chyba że punkt poniżej tego wymaga)

Audyt potwierdził w kodzie: A1 (enumeracja jako `CLASSICAL_SOLVER`, limit n ≤ 22), A2 (cięcia no-good dodawane do problemu, źródło klasyczne dla CP-SAT), A3 (weryfikator nie ufa `claimed_status`), A4 i A6 (brak wymyślonych liczb w fallbackach), A5 w `ir_builder.py`, A8, A9 w backendzie, A10 w `RecommendationView`/`QuantumEntanglementCanvas`, A12 (metafory tunelowania usunięte), A13 (odcisk Unicode + stop-słowa), A17 (`check_available()` w `health/solvers`), A18/E5 (zakresowanie i zgoda), A19 (`capabilities.py`), A20 (współczynniki w bramce), B2 (re-solve w `sensitivity.py`), B4 (`llm_gateway.py` istnieje), B6 (`router.py` używany w `runner.py`), C1–C5 jako moduły (`SafeWebFetcher`, `EvidenceExtractor` z weryfikacją cytatu, `ResearchPlanner`, adapter Tavily/Serper), D2–D3 jako silnik matematyczny (`problem_classes.py`: Pareto, ranking dźwigni), D4 (`continuous.py`), E2–E3 (trwała sesja, `process_verification_feedback` w runnerze), E6 (Cognitive Inspector), F1–F4, F6 (`qpu_adapter.py`), H2 (`security_guard.py` jako `Depends` na endpointach LLM), I1 (`scripts/ci.sh`), benchmark `benchmarks/results/benchmark_20260913_154536.json` (realny run CP-SAT vs QAOA). Cache pytest: 157 nodeids, `lastfailed` pusty.

To jest solidna baza. Problemy poniżej dotyczą tego, co **nie jest podłączone do produktu**, co **zostało sfabrykowane w UI** i co **nie trafiło na produkcję**.

---

## 4. REGRESJE R1–R5 (R6 jest w sekcji 2)

**R1. Klasa `DESIGN` w UI jest na sztywno podpięta do fixture „ochrona zdrowia", a panel „Zweryfikowane źródła instytucjonalne" zawiera zmyślone cytaty przypisane GUS, NFZ, WHO i OECD.**
Dowody:
- `frontend/src/components/RecommendationView.tsx` ~linie 48–66: `useEffect` w trybie DESIGN wywołuje `getDesignFixture('healthcare_pl')` **niezależnie od tego, co wpisał użytkownik**. Każdy problem klasy DESIGN pokazuje reformę ochrony zdrowia.
- `RecommendationView.tsx` ~linie 640–645: tablica literałów `{ inst: 'Główny Urząd Statystyczny (GUS)', doc: 'Raport Ochrona Zdrowia w Polsce 2024/2025', url: 'https://stat.gov.pl/zdrowie', quote: 'Wydatki bieżące na ochronę zdrowia wyniosły 6.8% PKB' }` itd., renderowana pod nagłówkiem „4. Zweryfikowane źródła instytucjonalne i podstawy dowodowe". Te cytaty i adresy nie pochodzą z żadnego pobrania; to fabrykacja przypisana realnym instytucjom — najcięższe naruszenie zasady nr 4 z `BUILD_SPEC_V2.md` §1 w całej historii projektu.
- `tests/fixtures/design/healthcare_pl.json`: 27 komórek z `provenance: "web_sourced"` i `evidence_ref` typu `https://who.int/beveridge-systems`, `https://oecd.org/health/multi-fund`, `https://stat.gov.pl/zdrowie/raport-2025.html` — adresy wymyślone, `is_hypothetical: false`.
- `backend/api/routes.py` ~linia 838: `GET /design/fixtures/{name}` serwuje pliki z `tests/fixtures/` do produkcyjnego UI.
- `frontend/src/components/LandingPage.tsx` ~linia 161: przykład startowy DESIGN to reforma ochrony zdrowia — szablon branżowy, którego `BUILD_SPEC_V2.md` §12 wprost zakazuje.
- `docs/REPORT_V2.md` §3 i §4: „korzysta ze zweryfikowanych baz statystycznych (GUS, NFZ, WHO, OECD)", „rejestr dowodów instytucjonalnych" — takiego rejestru nie ma w `backend/`.

Wymagane:
1. Usuń tablicę literałów źródeł z `RecommendationView.tsx`. Sekcja źródeł renderuje **wyłącznie** rekordy `Evidence` z odpowiedzi backendu (`evidence_id`, `source_url`, `retrieved_at`, `content_hash`, `quote` zweryfikowany w treści). Gdy ich nie ma — stan pusty: „Brak źródeł zewnętrznych. Wszystkie wartości pochodzą od użytkownika lub są założeniami."
2. Usuń wywołanie `getDesignFixture('healthcare_pl')` z UI. Synteza DESIGN powstaje z `DesignProblem` zbudowanego dla **tego** zapytania użytkownika (patrz N5).
3. Fixture: zmień wszystkie `evidence_ref`/URL na domenę `https://example.test/...`, dodaj na górze pliku `"synthetic_test_data": true, "note": "Dane syntetyczne do testów; nie opisują żadnego realnego systemu ani źródła"`, ustaw `is_hypothetical: true` tam, gdzie nie ma realnego źródła (czyli wszędzie). Endpoint `/design/fixtures/*` dostępny tylko przy `YQ_ENABLE_TEST_FIXTURES=1`, domyślnie 404.
4. Zmień przykład na landing page na dziedzinowo neutralny lub pozwól użytkownikowi wpisać własny; żaden przykład nie może sugerować gotowego modułu branżowego.
5. Popraw `REPORT_V2.md` (dopisek „ERRATA 2026-09-13" — nie kasuj historii) i `CURRENT_STATE.md`.
6. Test: `tests/test_v4_regressions.py::test_r1_no_hardcoded_sources_in_frontend` — grep źródeł frontendu pod kątem `stat.gov.pl|nfz.gov.pl|who.int|oecd.org` w literałach musi zwrócić 0 trafień; `test_r1_design_fixture_is_synthetic` — każdy URL w fixture zaczyna się od `https://example.test/`.

**R2. Hasło główne `A132a132!` nadal jest w kodzie — tym razem w frontendzie, widoczne dla każdego odwiedzającego.**
Dowody: `frontend/src/components/ApiPortalModal.tsx` linie 165, 175, 245, 312, 339, 361 (`authToken || 'A132a132!'`), `frontend/src/components/AppHeader.tsx` linia 138 (`title="… (zabezpieczone hasłem A132a132!)"` — tooltip pokazuje hasło), `tests/test_universal_api.py` linie 5, 27, 53. `REPORT_V2.md` §5 twierdzi „w kodzie nie ma już żadnych wartości domyślnych" — nieprawda.
Wymagane: usuń wszystkie wystąpienia; portal API bez tokenu pokazuje formularz logowania, nie hasło; test używa losowego sekretu z `monkeypatch`. Test: `test_r2_no_master_secret_literal_in_repo` — grep całego repo (poza `.backup/`, `.git/`, `docs/SECURITY.md`, `LESSONS.md`) po `A132a132` = 0.

**R3. Klucz podpisu HMAC ma wartość domyślną w kodzie — „podpis kryptograficzny" jest podrabialny.**
Dowód: `backend/verifier/verifier.py` linia 27: `os.getenv("YQ_SIGNING_KEY", "yourquantum_audit_master_seal_2026")`. To dokładnie ten błąd, który A9 miał wyeliminować. Wymagane: brak wartości domyślnej; bez klucza `hmac_signature = None` i `limitations` zawiera „raport niepodpisany — brak YQ_SIGNING_KEY"; UI pokazuje wtedy „odcisk SHA-256 (bez podpisu serwera)". Test: `test_r3_signing_key_has_no_default`.

**R4. Dokumentacja twierdzi, że istnieją pliki i funkcje, których nie ma.**
Dowody: DEC-022 w `DECISIONS.md`: „`Dockerfile` w repozytorium definiuje oficjalny kontener obliczeniowy" — brak `Dockerfile`; `CURRENT_STATE.md`: „Fixture ochrony zdrowia `backend/domain/design_synthesis/fixtures/healthcare_pl.json`" — katalog nie istnieje (plik jest w `tests/fixtures/design/`); `REPORT_V2.md`: „rejestr dowodów instytucjonalnych", „lokalne zweryfikowane bazy faktów" — nie istnieją; `CAPABILITIES.md`: „Problem IR schema v0.3" jako TESTED, podczas gdy `backend/domain/problem_ir.py` linia 179 ma `schema_version: str = "0.2"`.
Wymagane: skoryguj każde z tych miejsc; dodaj do `scripts/validate-structure.sh` sprawdzenie, że każda ścieżka wymieniona w `CURRENT_STATE.md` i `CAPABILITIES.md` w backtickach istnieje (prosty grep + `test -e`).

**R5. Zmyślone wartości domyślne telemetrii w Cognitive Inspector.**
Dowód: `frontend/src/components/EvidenceDrawer.tsx` ~linie 444 i 451: `telemetry?.prediction_errors ? … : (isVerified ? 0 : 1)` oraz `telemetry?.cycle_history?.length ?? 1` — gdy brak danych, UI pokazuje „0/1 błędów" i „1 kroków". Wymagane: brak danych = „—" z tooltipem „telemetria niedostępna". Test w Playwright.

---

## 5. BRAKI — PUNKTY OZNACZONE W `REPORT_V2.md` JAKO ZROBIONE, KTÓRE NIE SĄ (N1–N11)

**N1. Produkcja nie została zweryfikowana i nadal serwuje stary kod (A16, A17, F5 z V2).**
Dowód empiryczny z 2026-09-13: `GET https://yourquantum.pl/api/v1/health/solvers` zwraca `{"solvers":[{"name":"cp_sat","version":"unknown"},{"name":"qaoa_aer","version":"not_installed"},{"name":"hybrid_benders","version":"0.1.0"}]}` — brak pola `available`, czyli stary `routes.py`; `ortools` i `qiskit` nieobecne na produkcji. `origin/main` jest równe lokalnemu `main` (merge V2 wypchnięty), więc Vercel albo nie zbudował nowej wersji, albo build się nie powiódł. Najbardziej prawdopodobna przyczyna (wymaga sprawdzenia w panelu Vercel): `requirements.txt` po V2 zawiera `ortools`, `qiskit`, `qiskit-aer`, `scipy`, a DEC-022 sam stwierdza, że ten stos przekracza limit 250 MB funkcji Vercel. `REPORT_V2.md` nie zawiera żadnego wyniku sprawdzenia produkcji, mimo że `BUILD_SPEC_V2.md` A16 i A17 wymagały go **przed** zmianami.
Wymagane:
1. Sprawdź logi ostatniego builda Vercel i zapisz wynik (data, status, przyczyna) w `CURRENT_STATE.md`.
2. Rozdziel zależności: `requirements-api.txt` (lekki: FastAPI, Pydantic, SQLAlchemy, httpx, numpy) dla Vercel oraz `requirements-worker.txt` (pełny stos) dla kontenera. `vercel.json` ma wskazywać lekki plik (zmienna `PIP_REQUIREMENTS` lub `api/requirements.txt` — sprawdź w dokumentacji Vercel, zapisz w `SOURCES.md`).
3. Utwórz `Dockerfile` (worker) i `docker-compose.yml` (api + worker + postgres) — bez nich DEC-022 jest deklaracją. Worker pobiera `JobRecord` ze statusem `QUEUED` z bazy i wykonuje `run_job_sync`; API na Vercel tylko kolejkuje. Usuń `asyncio.create_task` z `enqueue_job` w trybie serverless (`YQ_EXECUTION_MODE=queue|inline`).
4. Do czasu uruchomienia workera produkcja ma **uczciwie pokazywać**, że dostępna jest wyłącznie enumeracja dla n ≤ 22 (klasyczna) i formalizacja — bez oferowania „QAOA Aer" w selektorze solvera, gdy `health/solvers` mówi `available: false`. Frontend czyta `health/solvers` przy starcie i ukrywa niedostępne silniki.
5. Po wdrożeniu: wykonaj na produkcji `health/solvers`, jeden pełny job i `GET /jobs/{id}` po 60 s; wklej surowe odpowiedzi do `CURRENT_STATE.md`. Bez tego N1 nie jest zrobione.

**N2. Macierz decyzyjna (B1) istnieje jako biblioteka, ale ścieżka produktu nigdy jej nie wypełnia — wynik dla klasy CHOICE jest arbitralny.**
Dowody: `backend/domain/cognitive/active_inference_engine.py` ~linia 212: `case = advisor.analyze_case(query)`; `LLMAdvisor.heuristic_analyze` ustawia `criteria: list[Criterion] = []`, a prompt Gemini w `llm_advisor.py` nie prosi o kryteria ani o wartości z cytatem; nic nie wypełnia `score_matrix`. `DecisionCase.validate_for_modeling()` iteruje po `self.criteria` — przy zerze kryteriów zwraca `True` (bramka nie blokuje). `formalizer.py::formalize_case` przy braku kryteriów ustawia `coeffs = {v: 1.0 …}` — solver wybiera dowolną opcję i UI ogłasza ją zwycięzcą. Frontend nie ma edytora komórek macierzy (`CaseWorkspace.tsx` edytuje opcje, priorytety i odpowiedzi; `ModelApprovalGate.tsx` tylko wyświetla macierz, jeśli istnieje). Testy E2E (`frontend/e2e/v2-honest-engine.spec.ts`) podają gotową `score_matrix` przez `page.route` — mockują cały backend, więc nie wykrywają tego braku.
Wymagane:
1. `LLMGateway`-owy krok `extract_decision_structure(query) → {criteria[], options[], values[{option_id, criterion_id, value, unit, quote_from_user_text}]}` ze schematem JSON; każda wartość, której `quote` nie występuje w tekście użytkownika, jest odrzucana (ta sama zasada co `_verify_quote_in_text` w ekstraktorze dowodów). Fallback bez klucza: kryteria z priority tokens, wartości puste.
2. `validate_for_modeling()` zwraca `False` przy `len(criteria) == 0` z komunikatem „Zdefiniuj co najmniej jedno kryterium".
3. Edytor macierzy w `CaseWorkspace.tsx`: tabela opcje × kryteria; komórka = wartość + jednostka + pochodzenie (👤/🌐/⚠️/❓); przyciski „Dodaj kryterium", „Dozbierz z sieci" (N3), „Oznacz jako założenie". Przejście do `ModelApprovalGate` zablokowane, dopóki `validate_for_modeling()` nie przejdzie.
4. `formalize_case` bez kryteriów zwraca `missing_information` z `BLOCKS_SOLVING`, nigdy współczynników 1.0.
5. Punkt zwrotny (`calculate_analytical_break_even`) i ranking wrażliwości pokazane w `RecommendationView` z realnych danych; brak = stan pusty, nie tekst zastępczy.
6. Testy: integracyjny bez mocków LLM (tryb offline) — intake → macierz z brakami → 422 przy próbie modelowania → uzupełnienie komórek przez `POST /cases` → formalize → współczynniki różne od 1.0 → approve → job → wynik zgodny z ręcznym rachunkiem sumy ważonej.

**N3. Warstwa dowodowa (C) nie jest podłączona do interfejsu — użytkownik nigdy nie dostaje danych z sieci.**
Dowody: `run_intake` tylko planuje zapytania (`identify_missing_parameters`) i zapisuje je w `formalization.research_queries`; nie wykonuje `execute_research_plan`. Endpoint `POST /evidence/research` istnieje, funkcja `researchEvidence` w `frontend/src/api.ts` (linia ~602) istnieje, ale **żaden komponent jej nie wywołuje** (`grep -rn researchEvidence frontend/src/components frontend/src/App.tsx` = 0). To był główny cel Jana z V2 §4.
Wymagane: przycisk „Dozbierz dane z sieci" w edytorze macierzy (N2) dla pustych komórek → `POST /evidence/research` → wyniki jako propozycje komórek z pochodzeniem 🌐 (użytkownik akceptuje każdą osobno) → konflikty jako wybór. Bez klucza wyszukiwarki: przycisk aktywny, ale odpowiedź „Wyszukiwarka nieskonfigurowana — możesz wkleić adres URL źródła" i pole na URL (fetch + ekstrakcja działają bez wyszukiwarki). Licznik zapytań z `EnergyBudget` widoczny. Test E2E z backendem uruchomionym naprawdę i adapterem w trybie `mock_fixtures` (fixtures są w `tests/fixtures/web/`).

**N4. Klasyfikacja klas problemów (D1) to regex słów kluczowych bez potwierdzenia użytkownika; `NOT_COMPUTABLE` to trzy literalne frazy.**
Dowody: `active_inference_engine.py::classify_problem_class` — `re.search(r"\b(dźwigni|system|reforma|architektur|…)\b")`; `problem_classes.py::evaluate_problem_computability` — lista trzech zdań („jaki jest sens życia", „czy bóg istnieje", „jaki będzie kurs bitcoina za rok"). Słowo „system" w dowolnym zdaniu („system alarmowy do domu czy kamery?") kieruje do DESIGN, a więc — po R1 — do fixture ochrony zdrowia.
Wymagane: klasyfikacja przez `LLMGateway` ze schematem `{problem_class, confidence, reason, computable, reframe_suggestions}`; heurystyka regex tylko jako fallback offline z `confidence ≤ 0.5`; UI (selektor z G2) pokazuje proponowaną klasę z uzasadnieniem i wymaga potwierdzenia; wybór użytkownika trafia do intake jako `problem_class_override` i ma pierwszeństwo. Test: zapytanie „system alarmowy czy kamery" → CHOICE, nie DESIGN.

**N5. Klasa DESIGN nie ma dekompozycji z zapytania użytkownika (D2) — istnieje tylko silnik liczący na gotowym `DesignProblem`.**
Dowód: brak jakiegokolwiek kodu, który z tekstu użytkownika buduje `DesignLever`/`LeverOption` (`grep -rn "DesignProblem\|lever" backend/api/cognitive_routes.py backend/domain/cognitive/ backend/infrastructure/` = tylko klasyfikacja). Jedynym źródłem `DesignProblem` w UI jest fixture (R1).
Wymagane: `backend/domain/cognitive/lever_decomposer.py` — `LLMGateway` proponuje 3–7 dźwigni po 2–5 wariantów, kryteria, oraz dla każdego wariantu `evidence_hint` (co trzeba sprawdzić w źródłach); wszystkie `LeverOptionScore` startują puste; użytkownik edytuje dźwignie/warianty w UI (nowy `DesignWorkspace.tsx`); komórki wypełniane jak w N2/N3; `Interaction.synergy` domyślnie 0 i edytowalna tylko ze źródłem lub jawnym oznaczeniem założenia; synteza (`compute_design_synthesis`) dopiero po walidacji. Fallback offline: szkielet dźwigni pusty z instrukcją dla użytkownika. Test integracyjny: zapytanie DESIGN w trybie offline → pusty szkielet → użytkownik uzupełnia przez API → synteza → front Pareto zgodny z enumeracją.

**N6. Wywołania LLM nie przechodzą przez `LLMGateway` (B4, A15 niedokończone).**
Dowody: `active_inference_engine.py` ~212 woła synchroniczne `advisor.analyze_case()` z wnętrza `async def run_intake` — `_call_gemini` używa `httpx.Client` (blokada pętli zdarzeń); `analyze_case_async` istnieje (`llm_advisor.py` ~476), ale nikt go nie używa; `formalizer.py` linie ~494 i ~664 nadal `httpx.post(...)` na `gemini-3.6-flash` (dwa różne modele w projekcie). Zużycie tokenów w `EnergyBudget` to nadal stała `consume_tokens(350)`.
Wymagane: wszystkie wywołania modelu wyłącznie przez `LLMGateway` (jeden model z `GEMINI_MODEL`, `responseSchema`, `usageMetadata` → budżet); usuń `_call_gemini`, `_call_openai`, `_try_llm_formalize`, `_try_llm_formalize_case` (oznaczone DEPRECATED — czas je skasować); test: `grep -rn "httpx\.\(post\|Client\)" backend/domain` = 0 poza `llm_gateway.py` i `web_research/`.

**N7. `universal_engine.py` omija A5 i B6.**
Dowody: linia ~341 `approved=True` (IR tworzony jako zatwierdzony bez akcji użytkownika); linie ~473–476 `if len(req.variables) <= 12: solver_choice = "hybrid_benders"` zamiast `ProblemRouter`.
Wymagane: `approved` z jawnego pola `req.approved_by_caller: bool` z opisem w docs API (klient API bierze odpowiedzialność za zatwierdzenie) — inaczej 422; routing przez `ProblemRouter` z zapisem `routing_record` w odpowiedzi.

**N8. Resztki niedozwolonego copy (A11, A12).**
Dowody: `frontend/src/components/ConversationPanel.tsx` linia 94: „QAOA + CP-SAT · 0% Halucynacji"; `backend/api/help_service.py` linia ~228: „zamiast losowych halucynacji". Wymagane: usuń; rozszerz test G1 o grep całego `frontend/src` i `help_service.py` po `halucynac` (dozwolone tylko w kontekście opisu ograniczeń LLM, nie jako obietnica własna).

**N9. Wersja schematu IR.** `problem_ir.py` linia 179: `schema_version = "0.2"` przy dokumentacji v0.3. Podnieś do `"0.3"`, dodaj migrację odczytu starych rekordów (`0.2` → `0.3` bez utraty danych), test.

**N10. Raport końcowy niezgodny z numeracją zlecenia.** `REPORT_V2.md` tabela A13–A18 opisuje inne problemy niż `BUILD_SPEC_V2.md` (np. A14 w raporcie = „wyciek między dzierżawcami", w zleceniu = „workspace porzucany, `process_verification_feedback` nie wywoływany"; A16 w raporcie = „brak runnera z limitami", w zleceniu = „`create_task` w serverless — zweryfikuj na produkcji"). Wymagane: `docs/REPORT_V4.md` z tabelą **według numeracji V2 i V4** (sekcja 8), kolumny: ID, status (zrobione / częściowo / nie), ścieżka pliku, nazwa testu, uwagi. „Nie" i „częściowo" są dozwolone; ich brak przy niezrobionym punkcie nie jest.

**N11. Testy E2E mockują cały backend.** `v2-honest-engine.spec.ts` przez `page.route('**/api/v1/cognitive/intake', …)` podaje gotowe odpowiedzi, więc nie wykrywają N2–N5. Wymagane: `frontend/e2e/v4-real-backend.spec.ts` — Playwright startuje `uvicorn` (tryb offline LLM, `mock_fixtures` dla sieci) przez `webServer` w `playwright.config.ts`; mocki HTTP dozwolone tylko dla zewnętrznych domen. `scripts/ci.sh` uruchamia oba zestawy.

---

## 6. BRAMKI MECHANICZNE — `scripts/check_v4.sh`

Skrypt tworzysz jako pierwszy krok (sekcja 1 pkt 2). Każda bramka to osobna linia z ID i wynikiem `PASS`/`FAIL`; skrypt kończy się kodem 1, jeśli którakolwiek jest `FAIL`. Bramki nie zastępują testów — są dodatkowym, niezależnym od Ciebie sprawdzeniem, które Jan uruchomi sam.

| ID | Bramka |
|---|---|
| G-R1a | `grep -rE "stat\.gov\.pl\|nfz\.gov\.pl\|who\.int\|oecd\.org" frontend/src` = 0 trafień |
| G-R1b | `grep -rn "getDesignFixture(" frontend/src/components/RecommendationView.tsx` = 0 |
| G-R1c | każdy URL w `tests/fixtures/design/healthcare_pl.json` zaczyna się od `https://example.test/`; plik zawiera `"synthetic_test_data": true` |
| G-R2 | `grep -rn "A132a132" --exclude-dir=.backup --exclude-dir=.git --exclude-dir=node_modules .` zwraca wyłącznie `docs/SECURITY.md`, `docs/memory/LESSONS.md`, `docs/BUILD_SPEC_V*.md`, `docs/REPORT_V*.md` |
| G-R3 | `grep -n 'getenv("YQ_SIGNING_KEY", "' backend` = 0 i `grep -n 'getenv("YQ_MASTER_API_SECRET", "' backend` = 0 (brak wartości domyślnych) |
| G-R4 | każda ścieżka w backtickach w `docs/memory/CURRENT_STATE.md`, `docs/CAPABILITIES.md`, `docs/memory/DECISIONS.md` (wzorzec `[A-Za-z0-9_./-]+\.(py\|ts\|tsx\|md\|json\|sh\|yml\|txt)` lub `Dockerfile`) istnieje na dysku |
| G-R5 | `grep -nE "\?\? 1\|isVerified \? 0 : 1" frontend/src/components/EvidenceDrawer.tsx` = 0 |
| G-R6 | `grep -n "google.com/search" backend/infrastructure/web_research/search_adapter.py` = 0; `grep -n "page_text=text" backend/infrastructure/web_research/search_adapter.py` = 0 |
| G-N1a | istnieją: `Dockerfile`, `docker-compose.yml`, `requirements-api.txt`, `requirements-worker.txt` |
| G-N1b | `requirements-api.txt` nie zawiera `ortools`, `qiskit`, `scipy` |
| G-N1c | `docs/memory/CURRENT_STATE.md` zawiera blok ```` ```json ```` z surową odpowiedzią produkcyjnego `health/solvers` zawierającą pole `"available"` |
| G-N2a | `grep -n "len(self.criteria) == 0" backend/domain/decision_case.py` ≥ 1 (bramka zero kryteriów) |
| G-N2b | `grep -rn "score_matrix" frontend/src/components/CaseWorkspace.tsx` ≥ 1 (edytor macierzy) |
| G-N3 | `grep -rn "researchEvidence(" frontend/src/components frontend/src/App.tsx` ≥ 1 |
| G-N4 | `grep -n "problem_class_override" backend/api/cognitive_routes.py frontend/src/api.ts` ≥ 1 w każdym |
| G-N5 | istnieje `backend/domain/cognitive/lever_decomposer.py` i `frontend/src/components/DesignWorkspace.tsx` |
| G-N6 | `grep -rnE "httpx\.(post\|Client\()" backend/domain` = 0 |
| G-N7 | `grep -n "approved=True" backend/api/universal_engine.py` = 0; `grep -n "ProblemRouter" backend/api/universal_engine.py` ≥ 1 |
| G-N8 | `grep -rni "halucynac" frontend/src backend/api/help_service.py` = 0 |
| G-N9 | `grep -n 'schema_version: str = "0.3"' backend/domain/problem_ir.py` = 1 |
| G-N11 | istnieje `frontend/e2e/v4-real-backend.spec.ts`; `playwright.config.ts` zawiera `webServer` |
| G-N10 | istnieje `docs/REPORT_V4.md` i zawiera wiersze dla wszystkich ID: R1–R6, N1–N11 |
| G-TESTS | `pytest -q` kończy się kodem 0; `npm run build` kończy się kodem 0 |

---

## 7. KRYTERIA UKOŃCZENIA V4

Zadanie jest ukończone **wyłącznie**, gdy `scripts/check_v4.sh` kończy się kodem 0 **i** wszystkie poniższe są prawdziwe:

- [ ] R6: grounding daje tylko URL-e; `page_text` wyłącznie z realnego pobrania; testy (a)–(d) zielone.
- [ ] R1: brak literałów źródeł w UI; DESIGN bierze `DesignProblem` z zapytania użytkownika; fixture syntetyczny i niedostępny bez `YQ_ENABLE_TEST_FIXTURES=1`; przykład na landing page neutralny; errata w `REPORT_V2.md`.
- [ ] R2, R3: zero sekretów i kluczy z wartością domyślną w całym repo (backend, frontend, testy).
- [ ] R4: każda ścieżka wymieniona w docs istnieje; `validate-structure.sh` to sprawdza.
- [ ] R5: brak zmyślonych wartości domyślnych telemetrii.
- [ ] N1: podział zależności, `Dockerfile`, `docker-compose.yml`, tryb `YQ_EXECUTION_MODE`, build Vercel zielony, surowe odpowiedzi produkcji w `CURRENT_STATE.md`, selektor solverów ukrywa niedostępne.
- [ ] N2: kryteria i wartości z cytatem z tekstu użytkownika; edytor macierzy; blokada przy zerze kryteriów; współczynniki ≠ 1.0; test integracyjny bez mocków LLM.
- [ ] N3: przycisk badania sieci w UI; tryb URL bez wyszukiwarki; E2E z realnym backendem i `mock_fixtures`.
- [ ] N4: klasa proponowana przez `LLMGateway` z uzasadnieniem, regex tylko fallback, potwierdzenie i `problem_class_override`.
- [ ] N5: `lever_decomposer.py`, `DesignWorkspace.tsx`, synteza dopiero po walidacji komórek; test offline → uzupełnienie → Pareto = enumeracja.
- [ ] N6: wszystkie wywołania LLM przez `LLMGateway`; kod DEPRECATED usunięty; tokeny z `usageMetadata`.
- [ ] N7: `universal_engine` bez `approved=True`, z `ProblemRouter` i `routing_record`.
- [ ] N8, N9: copy czyste; `schema_version = "0.3"` z migracją.
- [ ] N11: E2E z realnym backendem w `ci.sh`.
- [ ] N10: `docs/REPORT_V4.md` w formacie z sekcji 8.

**Nie wolno Ci zakończyć pracy ani napisać „gotowe", dopóki `scripts/check_v4.sh` jest czerwony.** Jeżeli któregoś punktu nie da się wykonać (brak klucza, brak decyzji Jana, konflikt z `AGENTS.md`), wpisujesz go w `REPORT_V4.md` jako „nie zrobiono — powód", a bramka dla tego ID pozostaje czerwona i widoczna. Nie wolno przerobić bramki tak, by była zielona bez wykonania punktu.

---

## 8. FORMAT `docs/REPORT_V4.md`

1. Surowy wynik `scripts/check_v4.sh` (pełny output, z datą).
2. Tabela R1–R6, N1–N11: status (zrobione / częściowo / nie zrobiono — powód), pliki, testy, commit.
3. Tabela retrospektywna A1–A20, B1–B7, C1–C7, D1–D6, E1–E7, F1–F6, G1–G6, H1–H6, I1–I3 **w numeracji `BUILD_SPEC_V2.md`** — status po V4.
4. Surowe wyniki: `pytest -q` (liczba, czas, pominięte i dlaczego), `npm run build`, oba zestawy Playwright, odpowiedzi produkcji.
5. Czego nie zrobiłem i dlaczego.
6. Decyzje dla Jana: rotacja hasła; `SEARCH_PROVIDER` (gemini grounding / tavily / serper / none) i koszty z datą i źródłem w `SOURCES.md` lub „nie sprawdzono"; hosting workera z realnym cennikiem lub „nie sprawdzono"; limity dzienne.
7. Sekcja „Propozycje" — pomysły spoza listy, **niezaimplementowane**.

---

## 9. ZASADY, KTÓRYCH NIE WOLNO NARUSZYĆ (skrót z `AGENTS.md` i `BUILD_SPEC_V2.md` §1)

LLM output ≠ wynik solvera i ≠ dowód. Symulacja ≠ QPU; enumeracja ≠ symulacja. Kandydat ≠ dowód optymalności. Każda liczba ma pochodzenie; placeholdery zakazane. Człowiek zatwierdza model. Brak twierdzeń o przewadze bez benchmarku. Klasyka wygrywa, gdy jest lepsza. Dane użytkownika i treści z sieci są niezaufane. Żadnych szablonów branżowych. Żadnych sekretów w kodzie. Żadnej pracy spoza listy bez zgody Jana.

_Koniec promptu. Zacznij od sekcji 1, punkt 1. Pierwszy commit: `chore(V4): add scripts/check_v4.sh and docs/V4_PLAN.md`._
