# YOURQUANTUM — PROMPT KORYGUJĄCY V3 DLA ANTIGRAVITY
_Wersja: 2026-09-13 (po audycie wdrożenia `docs/BUILD_SPEC_V2.md`) · Autor zlecenia: Jan Domaniewski_

---

## 0. KONTEKST I TRYB PRACY

Wdrożyłeś `docs/BUILD_SPEC_V2.md` i zapisałeś w `docs/REPORT_V2.md` oraz `docs/memory/CURRENT_STATE.md`, że wszystkie fazy A–I są ukończone. Niezależny audyt kodu z 2026-09-13 (gałąź `main`, commit `4659817`) potwierdza dużą część pracy, ale wykazuje: (a) **cztery regresje**, w tym dwie łamiące zasady kardynalne mocniej niż stan sprzed V2, (b) **jedenaście braków** w punktach, które raport oznacza jako zrobione, (c) **nieprawdziwe stwierdzenia w dokumentacji** o plikach i funkcjach, które nie istnieją.

Zasady pracy pozostają jak w `BUILD_SPEC_V2.md` §0 i §1 (protokół sesji z `AGENTS.md`, reguła dowodu, zakaz fabrykowania, `AGENTS.md` wygrywa w konflikcie). Dodatkowo:

1. Zapisz ten prompt verbatim jako `docs/BUILD_SPEC_V3.md`. Pracuj na gałęzi `fix/v3-corrections`.
2. **Nowa reguła raportowania:** w raporcie i w `CURRENT_STATE.md` wolno napisać, że coś istnieje, tylko z podaniem ścieżki pliku, która istnieje w repo w chwili zapisu. Każde twierdzenie „zrobione" ma numer z tego promptu (R1…, N1…) i nazwę testu. Renumerowanie punktów jest zabronione — `REPORT_V2.md` w tabeli A13–A18 opisuje inne problemy niż `BUILD_SPEC_V2.md` A13–A18, co uniemożliwia weryfikację.
3. Kolejność obowiązkowa: **R (regresje) → N1 (produkcja) → N2–N5 (rdzeń produktu) → N6–N11 (reszta) → raport**.
4. Nie usuwaj niczego, co działa i ma test. Nie „poprawiaj" testów przez osłabianie asercji.

---

## 1. CO ZOSTAŁO POTWIERDZONE (nie ruszaj, chyba że punkt poniżej tego wymaga)

Audyt potwierdził w kodzie: A1 (enumeracja jako `CLASSICAL_SOLVER`, limit n ≤ 22), A2 (cięcia no-good dodawane do problemu, źródło klasyczne dla CP-SAT), A3 (weryfikator nie ufa `claimed_status`), A4 i A6 (brak wymyślonych liczb w fallbackach), A5 w `ir_builder.py`, A8, A9 w backendzie, A10 w `RecommendationView`/`QuantumEntanglementCanvas`, A12 (metafory tunelowania usunięte), A13 (odcisk Unicode + stop-słowa), A17 (`check_available()` w `health/solvers`), A18/E5 (zakresowanie i zgoda), A19 (`capabilities.py`), A20 (współczynniki w bramce), B2 (re-solve w `sensitivity.py`), B4 (`llm_gateway.py` istnieje), B6 (`router.py` używany w `runner.py`), C1–C5 jako moduły (`SafeWebFetcher`, `EvidenceExtractor` z weryfikacją cytatu, `ResearchPlanner`, adapter Tavily/Serper), D2–D3 jako silnik matematyczny (`problem_classes.py`: Pareto, ranking dźwigni), D4 (`continuous.py`), E2–E3 (trwała sesja, `process_verification_feedback` w runnerze), E6 (Cognitive Inspector), F1–F4, F6 (`qpu_adapter.py`), H2 (`security_guard.py` jako `Depends` na endpointach LLM), I1 (`scripts/ci.sh`), benchmark `benchmarks/results/benchmark_20260913_154536.json` (realny run CP-SAT vs QAOA). Cache pytest: 157 nodeids, `lastfailed` pusty.

To jest solidna baza. Problemy poniżej dotyczą tego, co **nie jest podłączone do produktu**, co **zostało sfabrykowane w UI** i co **nie trafiło na produkcję**.

---

## 2. REGRESJE — NAPRAW NAJPIERW

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
6. Test: `tests/test_v3_regressions.py::test_r1_no_hardcoded_sources_in_frontend` — grep źródeł frontendu pod kątem `stat.gov.pl|nfz.gov.pl|who.int|oecd.org` w literałach musi zwrócić 0 trafień; `test_r1_design_fixture_is_synthetic` — każdy URL w fixture zaczyna się od `https://example.test/`.

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

## 3. BRAKI — PUNKTY OZNACZONE JAKO ZROBIONE, KTÓRE NIE SĄ

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

**N10. Raport końcowy niezgodny z numeracją zlecenia.** `REPORT_V2.md` tabela A13–A18 opisuje inne problemy niż `BUILD_SPEC_V2.md` (np. A14 w raporcie = „wyciek między dzierżawcami", w zleceniu = „workspace porzucany, `process_verification_feedback` nie wywoływany"; A16 w raporcie = „brak runnera z limitami", w zleceniu = „`create_task` w serverless — zweryfikuj na produkcji"). Wymagane: `docs/REPORT_V3.md` z tabelą **według numeracji V2 i V3**, kolumny: ID, status (zrobione / częściowo / nie), ścieżka pliku, nazwa testu, uwagi. „Nie" i „częściowo" są dozwolone; ich brak przy niezrobionym punkcie nie jest.

**N11. Testy E2E mockują cały backend.** `v2-honest-engine.spec.ts` przez `page.route('**/api/v1/cognitive/intake', …)` podaje gotowe odpowiedzi, więc nie wykrywają N2–N5. Wymagane: `frontend/e2e/v3-real-backend.spec.ts` — Playwright startuje `uvicorn` (tryb offline LLM, `mock_fixtures` dla sieci) przez `webServer` w `playwright.config.ts`; mocki HTTP dozwolone tylko dla zewnętrznych domen. `scripts/ci.sh` uruchamia oba zestawy.

---

## 4. KRYTERIA UKOŃCZENIA V3

- [ ] Grep frontendu: 0 literałów `stat.gov.pl|nfz.gov.pl|who.int|oecd.org|A132a132|99.98|Halucynacji` (R1, R2, N8).
- [ ] Żaden sekret ani klucz podpisu nie ma wartości domyślnej w kodzie (R2, R3).
- [ ] Każda ścieżka wymieniona w `CURRENT_STATE.md`, `CAPABILITIES.md`, `DECISIONS.md` istnieje; `validate-structure.sh` to sprawdza (R4).
- [ ] `Dockerfile`, `docker-compose.yml`, `requirements-api.txt`, `requirements-worker.txt` istnieją; build Vercel zielony; surowe odpowiedzi produkcji wklejone do `CURRENT_STATE.md` (N1).
- [ ] Ścieżka CHOICE bez mocków: kryteria i wartości pochodzą od użytkownika/LLM-z-cytatem/sieci; przy zerze kryteriów modelowanie zablokowane; współczynniki ≠ 1.0 (N2).
- [ ] Przycisk badania sieci działa w UI; bez klucza — tryb URL; każdy dowód ma cytat zweryfikowany (N3).
- [ ] Klasa problemu proponowana z uzasadnieniem i potwierdzana przez użytkownika; regex tylko fallback (N4).
- [ ] DESIGN buduje dźwignie z zapytania użytkownika; fixture używany wyłącznie w testach i oznaczony jako syntetyczny (R1, N5).
- [ ] `grep -rn "httpx\.\(post\|Client\)" backend/domain` = 0; jeden model LLM; tokeny z `usageMetadata` (N6).
- [ ] `universal_engine` nie tworzy `approved=True` bez jawnego pola i używa `ProblemRouter` (N7).
- [ ] `schema_version == "0.3"` z migracją (N9).
- [ ] E2E z realnym backendem zielone w `ci.sh` (N11).
- [ ] `docs/REPORT_V3.md` w numeracji V2/V3 z kolumną statusu (N10).

---

## 5. FORMAT RAPORTU `docs/REPORT_V3.md`

1. Tabela R1–R5 i N1–N11: status, plik, test, uwagi.
2. Tabela retrospektywna A1–A20, B1–B7, C1–C7, D1–D6, E1–E7, F1–F6, G1–G6, H1–H6, I1–I3 **w numeracji `BUILD_SPEC_V2.md`** z tym samym zestawem kolumn.
3. Surowe wyniki: `pytest` (liczba, czas, pominięte i dlaczego), `npm run build`, oba zestawy Playwright, odpowiedzi produkcji (N1).
4. Czego nie zrobiłem i dlaczego.
5. Decyzje dla Jana (pozostają: rotacja hasła, dostawca wyszukiwania, hosting workera; dodaj koszty kontenera z realnego cennika z datą i źródłem w `SOURCES.md` lub „nie sprawdzono").

_Koniec promptu. Zacznij od sekcji 0, punkt 1, potem R1._
