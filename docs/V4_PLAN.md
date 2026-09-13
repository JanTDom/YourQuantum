# YourQuantum — Plan Wykonania Promptu Korygującego V4

Dokument stanowi formalną tabelę deklaracji i potwierdzenia pełnego zrozumienia zakresu V4 przed modyfikacją jakiegokolwiek pliku produktu, zgodnie z §1 pkt 3 `docs/BUILD_SPEC_V4.md`.

---

## 1. Tabela Wykonania ID (R1–R6, N1–N11)

Kolejność nienegocjowalna (§1 pkt 5):
$$\text{R6} \to \text{R1} \to \text{R2} \to \text{R3} \to \text{R5} \to \text{R4} \to \text{N1} \to \text{N2} \to \text{N3} \to \text{N4} \to \text{N5} \to \text{N6} \to \text{N7} \to \text{N8} \to \text{N9} \to \text{N11} \to \text{N10}$$

| ID | Kolejność | Tytuł zadania | Pliki do zmiany | Test dowodowy |
|---|:---:|---|---|---|
| **R6** | 1 | Google Search Grounding = lista URL, nie treść strony ani dokument źródłowy | `backend/infrastructure/web_research/search_adapter.py`<br>`backend/domain/evidence/models.py`<br>`docs/memory/DECISIONS.md` (DEC-029) | `tests/test_v4_regressions.py::test_r6_grounding_quote_verification`<br>`tests/test_v4_regressions.py::test_r6_fetch_failure_yields_zero_evidence`<br>`tests/test_v4_regressions.py::test_r6_no_chunks_yields_no_results_and_no_google_search_url`<br>`tests/test_v4_regressions.py::test_r6_grep_no_google_search_literal` |
| **R1** | 2 | Usunięcie zmyślonych źródeł GUS/NFZ/WHO/OECD i odpięcie healthcare fixture z UI | `frontend/src/components/RecommendationView.tsx`<br>`tests/fixtures/design/healthcare_pl.json`<br>`backend/api/routes.py`<br>`frontend/src/components/LandingPage.tsx`<br>`docs/REPORT_V2.md` | `tests/test_v4_regressions.py::test_r1_no_hardcoded_sources_in_frontend`<br>`tests/test_v4_regressions.py::test_r1_design_fixture_is_synthetic`<br>`tests/test_v4_regressions.py::test_r1_fixture_endpoint_disabled_by_default` |
| **R2** | 3 | Całkowita eliminacja literału hasła master z repozytorium | `frontend/src/components/ApiPortalModal.tsx`<br>`frontend/src/components/AppHeader.tsx`<br>`backend/sdk/yourquantum_sdk.py`<br>`backend/sdk/yourquantum_client.ts`<br>`mcp_server/smoke_test.py`<br>`mcp_server/README.md`<br>`tests/test_universal_api.py` | `tests/test_v4_regressions.py::test_r2_no_master_secret_literal_in_repo` |
| **R3** | 4 | Usunięcie domyślnego klucza podpisu HMAC w `verifier.py` | `backend/verifier/verifier.py`<br>`backend/api/routes.py`<br>`frontend/src/components/RecommendationView.tsx` | `tests/test_v4_regressions.py::test_r3_signing_key_has_no_default` |
| **R5** | 5 | Usunięcie zmyślonych domyślnych wartości telemetrii w Cognitive Inspector | `frontend/src/components/EvidenceDrawer.tsx` | Playwright: sprawdzenie `—` z tooltipem przy braku telemetrii |
| **R4** | 6 | Uzgodnienie dokumentacji z rzeczywistymi ścieżkami na dysku | `docs/memory/DECISIONS.md`<br>`docs/memory/CURRENT_STATE.md`<br>`docs/CAPABILITIES.md`<br>`scripts/validate-structure.sh` | `bash scripts/validate-structure.sh` |
| **N1** | 7 | Rozdzielenie zależności (API vs Worker), Dockerfile, weryfikacja produkcji | `requirements-api.txt`<br>`requirements-worker.txt`<br>`Dockerfile`<br>`docker-compose.yml`<br>`vercel.json`<br>`backend/api/runner.py`<br>`backend/worker/compute_worker.py`<br>`frontend/src/components/LandingPage.tsx`<br>`docs/memory/CURRENT_STATE.md` | Testy integracyjne runnera w trybie inline/queue; odpytanie produkcji `health/solvers` |
| **N2** | 8 | Wypełnianie macierzy decyzyjnej z cytatów tekstu użytkownika, edytor i blokada | `backend/domain/cognitive/llm_gateway.py`<br>`backend/domain/cognitive/llm_advisor.py`<br>`backend/domain/cognitive/active_inference_engine.py`<br>`backend/domain/decision_case.py`<br>`backend/domain/formalizer.py`<br>`frontend/src/components/CaseWorkspace.tsx`<br>`frontend/src/components/RecommendationView.tsx` | `tests/test_v4_regressions.py::test_n2_decision_case_blocks_on_zero_criteria`<br>`tests/test_v4_regressions.py::test_n2_offline_intake_matrix_end_to_end` |
| **N3** | 9 | Podłączenie warstwy dowodowej sieci do UI | `frontend/src/components/CaseWorkspace.tsx`<br>`frontend/src/api.ts`<br>`frontend/src/App.tsx`<br>`backend/api/cognitive_routes.py` | Playwright E2E z backendem w trybie mock_fixtures |
| **N4** | 10 | Klasyfikacja klas problemów przez LLMGateway z uzasadnieniem i override | `backend/domain/cognitive/llm_gateway.py`<br>`backend/domain/cognitive/active_inference_engine.py`<br>`backend/domain/problem_classes.py`<br>`backend/api/cognitive_routes.py`<br>`frontend/src/api.ts`<br>`frontend/src/components/LandingPage.tsx` | `tests/test_v4_regressions.py::test_n4_classification_override` |
| **N5** | 11 | Dynamiczna dekompozycja klasy DESIGN z zapytania użytkownika i edytor | `backend/domain/cognitive/lever_decomposer.py`<br>`backend/api/cognitive_routes.py`<br>`frontend/src/components/DesignWorkspace.tsx`<br>`frontend/src/App.tsx` | `tests/test_v4_regressions.py::test_n5_design_decomposition_offline_to_pareto` |
| **N6** | 12 | Konsolidacja wszystkich wywołań LLM w LLMGateway i usunięcie metod deprecated | `backend/domain/formalizer.py`<br>`backend/domain/cognitive/llm_advisor.py`<br>`backend/domain/cognitive/active_inference_engine.py`<br>`backend/domain/cognitive/llm_gateway.py` | `tests/test_v4_regressions.py::test_n6_no_direct_httpx_in_domain` |
| **N7** | 13 | Naprawa universal_engine: brak approved=True, routing przez ProblemRouter | `backend/api/universal_engine.py` | `tests/test_v4_regressions.py::test_n7_universal_engine_approval_and_router` |
| **N8** | 14 | Usunięcie resztek niedozwolonego copy o halucynacjach | `frontend/src/components/ConversationPanel.tsx`<br>`backend/api/help_service.py` | `tests/test_v4_regressions.py::test_n8_no_prohibited_copy` |
| **N9** | 15 | Podniesienie wersji schematu Problem IR do 0.3 z migracją wsteczną | `backend/domain/problem_ir.py` | `tests/test_v4_regressions.py::test_n9_schema_0_3_migration` |
| **N11** | 16 | Testy E2E Playwright z realnym backendem uvicorn | `frontend/playwright.config.ts`<br>`frontend/e2e/v4-real-backend.spec.ts`<br>`scripts/ci.sh` | Uruchomienie suite `npx playwright test e2e/v4-real-backend.spec.ts` |
| **N10** | 17 | Raport końcowy docs/REPORT_V4.md w pełnej numeracji V4 i V2 | `docs/REPORT_V4.md` | Sprawdzenie kompletności bramek mechanicznych `check_v4.sh` |

---

## 2. Propozycje (do zatwierdzenia przez Jana — niezaimplementowane bez zgody)

1. **Wdrożenie dedykowanego workera na Fly.io / GCP Cloud Run**:
   - Koszt minimalny: ~$5-7/miesięcznie (Fly.io shared-cpu-1x 1GB RAM) lub Cloud Run (płatność per request/CPU-sekundę z darmowym pakietem 2 mln wywołań).
   - Pozwoli na asynchroniczne liczenie pełnego QAOA i OR-Tools z realnym czasem >60s bez ograniczeń Vercela.
2. **Automatyczna rotacja klucza HMAC i Master Secret**:
   - Zastosowanie rotacji w oparciu o HashiCorp Vault / AWS Secrets Manager / Vercel Environment Variables API.
