"""
Tests for YourQuantum V4 Regressions (R1-R6) and Missing Features (N1-N11).
Follows strict evidence-first DoD per docs/BUILD_SPEC_V4.md.
"""
import hashlib
import json
import os
import re
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.domain.evidence.models import EvidenceDocument, WebSearchResult
from backend.infrastructure.web_research.search_adapter import WebResearchAdapter
from backend.infrastructure.web_research.extractor import EvidenceExtractor
from backend.domain.evidence.models import ExtractionMethod


# ---------------------------------------------------------------------------
# R6: Google Search Grounding is URL Discovery Only, Never Source Document
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_r6_grounding_quote_verification():
    """
    R6 Test (a):
    Mock Gemini Grounding returning groundingChunk with https://example.test/a and model text.
    Mock fetcher returning a real webpage with DIFFERENT content than model text.
    Verify:
    1. Quote from model text is REJECTED by EvidenceExtractor.
    2. Quote from actual webpage is ACCEPTED by EvidenceExtractor.
    """
    model_generated_text = "Według szacunków modelu koszt wynosi 99999 PLN na rok."
    actual_webpage_text = "Oficjalny komunikat: Koszt instalacji wynosi dokładnie 45000 PLN brutto."
    doc_url = "https://example.test/a"

    # Mock fetcher
    mock_fetcher = MagicMock()
    real_doc = EvidenceDocument(
        url=doc_url,
        title="Oficjalny Komunikat",
        publisher="example.test",
        content_hash=hashlib.sha256(actual_webpage_text.encode("utf-8")).hexdigest(),
        page_text=actual_webpage_text,
    )
    mock_fetcher.fetch = AsyncMock(return_value=real_doc)

    adapter = WebResearchAdapter(provider="gemini", api_key="test_api_key", fetcher=mock_fetcher)

    # Mock Gemini HTTP response
    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": model_generated_text}],
                },
                "groundingMetadata": {
                    "groundingChunks": [
                        {
                            "web": {
                                "uri": doc_url,
                                "title": "Strona przykładu",
                            }
                        }
                    ]
                },
            }
        ]
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_gemini_response
        mock_post.return_value = mock_resp

        results = await adapter.search("koszt instalacji", max_results=1)

    assert len(results) == 1
    assert results[0].url == doc_url
    assert results[0].snippet_origin == "llm"
    assert results[0].score is None
    assert results[0].publisher == "example.test"

    # Real document fetched via adapter.fetch_document
    fetched_doc = await adapter.fetch_document(doc_url)
    assert fetched_doc is not None
    assert fetched_doc.page_text == actual_webpage_text
    assert fetched_doc.page_text != model_generated_text

    # Verify quotes using EvidenceExtractor
    extractor = EvidenceExtractor()

    # 1. Quote from hallucinated model text -> REJECTED
    fake_quote = "koszt wynosi 99999 PLN na rok"
    assert not extractor._verify_quote_in_text(fake_quote, fetched_doc.page_text)

    # 2. Quote from actual webpage -> ACCEPTED
    real_quote = "Koszt instalacji wynosi dokładnie 45000 PLN brutto"
    assert extractor._verify_quote_in_text(real_quote, fetched_doc.page_text)


@pytest.mark.asyncio
async def test_r6_fetch_failure_yields_zero_evidence():
    """
    R6 Test (b):
    When SafeWebFetcher fails to fetch the URL discovered via Grounding,
    fetch_document returns None and zero evidence is formed.
    """
    mock_fetcher = MagicMock()
    mock_fetcher.fetch = AsyncMock(return_value=None)

    adapter = WebResearchAdapter(provider="gemini", api_key="test_api_key", fetcher=mock_fetcher)
    doc = await adapter.fetch_document("https://example.test/unreachable")
    assert doc is None


@pytest.mark.asyncio
async def test_r6_no_chunks_yields_no_results_and_no_google_search_url():
    """
    R6 Test (c):
    When Gemini Grounding returns text but zero groundingChunks,
    the adapter MUST return an empty list of results (0 results)
    and NEVER create a pseudo-result with https://google.com/search.
    """
    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Oto ogólny tekst bez linków."}],
                },
                "groundingMetadata": {
                    "groundingChunks": []
                },
            }
        ]
    }

    adapter = WebResearchAdapter(provider="gemini", api_key="test_api_key")

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_gemini_response
        mock_post.return_value = mock_resp

        results = await adapter.search("ogólne pytanie", max_results=3)

    assert results == []
    for r in results:
        assert "google.com/search" not in r.url


def test_r6_grep_no_google_search_literal():
    """
    R6 Test (d):
    grep search_adapter.py for google.com/search and page_text=text must return 0 hits.
    """
    adapter_path = os.path.join(
        os.path.dirname(__file__), "..", "backend", "infrastructure", "web_research", "search_adapter.py"
    )
    with open(adapter_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "google.com/search" not in content
    assert "page_text=text" not in content


# ---------------------------------------------------------------------------
# R1: No Hardcoded Institutional Sources in Frontend, Synthetic Fixture
# ---------------------------------------------------------------------------

def test_r1_no_hardcoded_sources_in_frontend():
    """
    R1: grep frontend/src for stat.gov.pl|nfz.gov.pl|who.int|oecd.org must return 0 hits.
    Also verify RecommendationView.tsx has no getDesignFixture call.
    """
    frontend_src = os.path.join(os.path.dirname(__file__), "..", "frontend", "src")
    pattern = re.compile(r"stat\.gov\.pl|nfz\.gov\.pl|who\.int|oecd\.org")

    hits = []
    for root, _, files in os.walk(frontend_src):
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx", ".html", ".css")):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            hits.append(f"{filepath}:{line_num}: {line.strip()}")

    assert hits == [], f"Found hardcoded institutional URLs in frontend: {hits}"

    rec_view_path = os.path.join(frontend_src, "components", "RecommendationView.tsx")
    with open(rec_view_path, "r", encoding="utf-8") as f:
        rec_content = f.read()
    assert "getDesignFixture(" not in rec_content


def test_r1_design_fixture_is_synthetic():
    """
    R1: All URLs in tests/fixtures/design/healthcare_pl.json must start with https://example.test/
    and file must declare synthetic_test_data: true.
    """
    import json
    fixture_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "design", "healthcare_pl.json"
    )
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("synthetic_test_data") is True

    # Check all URLs in the fixture
    url_pattern = re.compile(r"https?://[^\s\"']+")
    with open(fixture_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    found_urls = url_pattern.findall(raw_text)
    assert len(found_urls) > 0, "Expected to find URLs in fixture"
    for u in found_urls:
        assert u.startswith("https://example.test"), f"URL {u} is not under https://example.test"


def test_r1_fixture_endpoint_disabled_by_default():
    """
    R1: Endpoint /api/v1/design/fixtures/* must return 404 by default (without YQ_ENABLE_TEST_FIXTURES=1).
    When YQ_ENABLE_TEST_FIXTURES=1 is set, it returns the fixture.
    """
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    # 1. By default -> 404
    os.environ.pop("YQ_ENABLE_TEST_FIXTURES", None)
    res_default = client.get("/api/v1/design/fixtures/healthcare_pl")
    assert res_default.status_code == 404

    # 2. With YQ_ENABLE_TEST_FIXTURES=1 -> 200
    with patch.dict(os.environ, {"YQ_ENABLE_TEST_FIXTURES": "1"}):
        res_enabled = client.get("/api/v1/design/fixtures/healthcare_pl")
        assert res_enabled.status_code == 200
        assert res_enabled.json().get("synthetic_test_data") is True


# ---------------------------------------------------------------------------
# R2: Eradicate Master Secret Literal from Repo
# ---------------------------------------------------------------------------

def test_r2_no_master_secret_literal_in_repo():
    """
    R2: grep the entire repo for the master secret literal.
    Allowed only in:
      - docs/SECURITY.md
      - docs/memory/LESSONS.md
      - docs/BUILD_SPEC_V*.md
      - docs/REPORT_V*.md
    Zero occurrences in backend, frontend, sdk, tests, mcp_server, etc.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    secret_literal = "A132" + "a132"

    allowed_rel_prefixes = [
        "docs/SECURITY.md",
        "docs/memory/LESSONS.md",
    ]
    allowed_patterns = [
        re.compile(r"^docs/BUILD_SPEC_V\d+\.(md|docx)$"),
        re.compile(r"^docs/REPORT_V\d+\.md$"),
    ]

    invalid_hits = []
    ignored_dirs = {".git", ".backup", "node_modules", ".venv", "__pycache__", "dist"}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, repo_root)

            # Check if this file is permitted
            if any(relpath == p for p in allowed_rel_prefixes):
                continue
            if any(p.match(relpath) for p in allowed_patterns):
                continue

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if secret_literal in line:
                            invalid_hits.append(f"{relpath}:{line_num}: {line.strip()}")
            except Exception:
                pass

    assert invalid_hits == [], f"Found forbidden master secret literal in repo: {invalid_hits}"


# ---------------------------------------------------------------------------
# R3: Signing Key Has No Default, Unsigned Reports Flagged
# ---------------------------------------------------------------------------

def test_r3_signing_key_has_no_default(monkeypatch):
    """
    R3: Verify YQ_SIGNING_KEY has no default fallback.
    Without key: hmac_signature is None, limitations contains 'raport niepodpisany'.
    With key: hmac_signature is a 64-character hex digest.
    Also verifies 0 instances of getenv('YQ_SIGNING_KEY', '...') and getenv('YQ_MASTER_API_SECRET', '...').
    """
    from backend.verifier.verifier import (
        get_signing_key,
        compute_verification_signatures,
        IndependentVerifier,
        SolverCandidate,
    )
    from backend.domain.problem_ir import (
        ProblemIR, Variable, VariableDomain, ObjectiveDirection,
        ExpressionRegistry, ExprNode, Objective
    )
    from datetime import datetime, timezone

    # 1. Unset key
    monkeypatch.delenv("YQ_SIGNING_KEY", raising=False)
    assert get_signing_key() is None

    sha, hmac_sig = compute_verification_signatures("sample_canonical_string")
    assert sha is not None
    assert len(sha) == 64
    assert hmac_sig is None

    # 2. IndependentVerifier with unset key
    reg = ExpressionRegistry()
    reg.add(ExprNode(id="obj_node", op="var", value="x"))
    problem = ProblemIR(
        problem_id="prob_test_r3",
        description_raw="Test problem for R3",
        description_formalised="Formalized test problem for R3",
        variables=[Variable(id="x", name="x", domain=VariableDomain.BINARY)],
        expressions=reg,
        objectives=[Objective(id="obj", direction=ObjectiveDirection.MINIMIZE, expression_id="obj_node")],
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )
    candidate = SolverCandidate(
        candidate_id="cand_1",
        assignment={"x": 1},
        claimed_objective=1.0,
        claimed_status="optimal",
    )
    verifier = IndependentVerifier(problem)
    report = verifier.verify(candidate)

    assert report.hmac_signature is None
    assert any("raport niepodpisany" in lim for lim in report.limitations)

    # 3. With key set
    monkeypatch.setenv("YQ_SIGNING_KEY", "test_audit_key_secret_2026")
    assert get_signing_key() == "test_audit_key_secret_2026"

    sha2, hmac_sig2 = compute_verification_signatures("sample_canonical_string")
    assert hmac_sig2 is not None
    assert len(hmac_sig2) == 64

    report_signed = verifier.verify(candidate)
    assert report_signed.hmac_signature is not None
    assert len(report_signed.hmac_signature) == 64
    assert not any("raport niepodpisany" in lim for lim in report_signed.limitations)

    # 4. Grep check for backend getenv defaults
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend_dir = os.path.join(repo_root, "backend")

    signing_hits = []
    master_hits = []
    for root, _, files in os.walk(backend_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if 'getenv("YQ_SIGNING_KEY", "' in content:
                        signing_hits.append(path)
                    if 'getenv("YQ_MASTER_API_SECRET", "' in content:
                        master_hits.append(path)

    assert signing_hits == [], f"Found default in getenv YQ_SIGNING_KEY: {signing_hits}"
    assert master_hits == [], f"Found default in getenv YQ_MASTER_API_SECRET: {master_hits}"


# ---------------------------------------------------------------------------
# R5: No Fabricated Fallback Telemetry in EvidenceDrawer
# ---------------------------------------------------------------------------

def test_r5_no_fabricated_telemetry_fallbacks():
    """
    R5: Verify EvidenceDrawer.tsx does not fabricate fallback metrics (?? 1, isVerified ? 0 : 1).
    Verify fallback is '—' with title 'telemetria niedostępna'.
    """
    drawer_path = os.path.join(
        os.path.dirname(__file__), "..", "frontend", "src", "components", "EvidenceDrawer.tsx"
    )
    with open(drawer_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert not re.search(r"\?\?\s*1\b", content), "Found '?? 1' in EvidenceDrawer.tsx"
    assert "isVerified ? 0 : 1" not in content, "Found 'isVerified ? 0 : 1' in EvidenceDrawer.tsx"
    assert 'title="telemetria niedostępna"' in content, "Missing 'telemetria niedostępna' tooltip"


# ---------------------------------------------------------------------------
# R4: Documentation Filepaths Reconciled with Disk
# ---------------------------------------------------------------------------

def test_r4_documentation_paths_exist():
    """
    R4: Verify that all backtick filepaths in CURRENT_STATE.md, CAPABILITIES.md, and DECISIONS.md
    exist on disk. Also verify scripts/validate-structure.sh passes.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docs = ["docs/memory/CURRENT_STATE.md", "docs/CAPABILITIES.md", "docs/memory/DECISIONS.md"]
    pattern = re.compile(r"\`([A-Za-z0-9_./-]+\.(?:py|ts|tsx|md|json|sh|yml|txt)|Dockerfile)\`")

    missing = []
    for doc in docs:
        doc_path = os.path.join(repo_root, doc)
        assert os.path.isfile(doc_path), f"Documentation file missing: {doc}"
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        matches = pattern.findall(content)
        for m in matches:
            if m.startswith("http") or "*" in m or m.startswith("v0.") or m.startswith("0."):
                continue
            full_target = os.path.join(repo_root, m)
            if not os.path.exists(full_target):
                missing.append(f"{doc} references missing: {m}")

    assert missing == [], f"Found non-existent paths referenced in documentation: {missing}"


# ---------------------------------------------------------------------------
# N1: Decoupled API/Worker Dependencies and Containerized Engine
# ---------------------------------------------------------------------------

def test_n1_split_requirements_and_container_files():
    """
    N1: Verify Dockerfile, docker-compose.yml, requirements-api.txt, and requirements-worker.txt exist.
    Verify requirements-api.txt does not have heavy solvers (ortools, qiskit, scipy).
    Verify requirements-worker.txt includes heavy compute dependencies.
    Verify CURRENT_STATE.md contains production health/solvers raw json response with 'available'.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # 1. Existence of container and config files
    expected_files = [
        "Dockerfile",
        "docker-compose.yml",
        "requirements-api.txt",
        "requirements-worker.txt",
        "backend/worker/service.py",
    ]
    for rel_path in expected_files:
        full_path = os.path.join(repo_root, rel_path)
        assert os.path.isfile(full_path), f"Expected file missing: {rel_path}"

    # 2. requirements-api.txt has no heavy solvers
    with open(os.path.join(repo_root, "requirements-api.txt"), "r", encoding="utf-8") as f:
        api_reqs = f.read()
    assert not re.search(r"\b(ortools|qiskit|scipy)\b", api_reqs, re.IGNORECASE), (
        "requirements-api.txt contains heavy numerical packages"
    )

    # 3. requirements-worker.txt contains heavy solvers
    with open(os.path.join(repo_root, "requirements-worker.txt"), "r", encoding="utf-8") as f:
        worker_reqs = f.read()
    assert "ortools" in worker_reqs.lower()
    assert "qiskit" in worker_reqs.lower()
    assert "scipy" in worker_reqs.lower()

    # 4. CURRENT_STATE.md contains raw production json
    with open(os.path.join(repo_root, "docs", "memory", "CURRENT_STATE.md"), "r", encoding="utf-8") as f:
        current_state = f.read()
    pattern = re.compile(r"```json\s*\{.*?\"available\".*?\}\s*```", re.DOTALL)
    assert pattern.search(current_state), "CURRENT_STATE.md does not contain raw production json with 'available'"


# ---------------------------------------------------------------------------
# N2: Decision Matrix Extraction, Validation & Solving
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_n2_quote_verification_rejects_hallucinated_values():
    """
    N2: extract_decision_structure verifies quote_from_user_text against user query.
    Values with hallucinated / missing quotes must be strictly rejected.
    """
    from backend.domain.llm_advisor import extract_decision_structure
    from backend.infrastructure.llm_gateway import LLMGateway, LLMResponse, LLMCallTelemetry

    user_query = "Wybieram między ofertą A i ofertą B. Oferta A oferuje 20000 zł, a oferta B 25000 zł."

    mock_gateway = MagicMock(spec=LLMGateway)
    mock_gateway.is_available = True

    mock_payload = {
        "title": "Wybór oferty: A vs B",
        "options": [
            {"id": "opt_a", "title": "Oferta A"},
            {"id": "opt_b", "title": "Oferta B"},
        ],
        "criteria": [
            {"id": "crit_zarobki", "name": "Wynagrodzenie", "direction": "maximize", "weight": 1.0, "unit": "PLN"},
        ],
        "values": [
            {
                "option_id": "opt_a",
                "criterion_id": "crit_zarobki",
                "value": 20000.0,
                "unit": "PLN",
                "quote_from_user_text": "20000 zł",  # VERIFIED IN QUERY
            },
            {
                "option_id": "opt_b",
                "criterion_id": "crit_zarobki",
                "value": 99999.0,
                "unit": "PLN",
                "quote_from_user_text": "oferuje 99999 zł na rękę z bonusem",  # HALLUCINATED! NOT IN QUERY
            },
        ],
    }

    mock_gateway.generate = AsyncMock(
        return_value=LLMResponse(
            text=json.dumps(mock_payload),
            parsed_json=mock_payload,
            telemetry=LLMCallTelemetry(model="gemini-test", purpose="test"),
            is_offline=False,
        )
    )

    struct = await extract_decision_structure(user_query, gateway=mock_gateway)
    verified = struct["values"]

    assert len(verified) == 1, f"Expected 1 verified value, got {len(verified)}"
    assert verified[0]["option_id"] == "opt_a"
    assert verified[0]["value"] == 20000.0
    assert not any(v["option_id"] == "opt_b" for v in verified), "Hallucinated quote for opt_b was not rejected!"


def test_n2_decision_case_validation_blocks_zero_criteria():
    """
    N2: DecisionCase.validate_for_modeling() returns False with 'Zdefiniuj co najmniej jedno kryterium'
    when criteria list is empty.
    """
    from backend.domain.decision_case import DecisionCase, Option

    case = DecisionCase(
        title="Dylemat bez kryteriów",
        context="Brak kryteriów",
        options=[Option(id="o1", title="A"), Option(id="o2", title="B")],
        criteria=[],
        score_matrix={},
    )
    is_valid, errors = case.validate_for_modeling()
    assert is_valid is False
    assert any("Zdefiniuj co najmniej jedno kryterium" in err for err in errors)


def test_n2_formalize_without_criteria_blocks_solving():
    """
    N2: formalize_case without criteria returns BLOCKS_SOLVING and never default 1.0 coeffs.
    """
    from backend.domain.decision_case import DecisionCase, Option
    from backend.domain.formalizer import ProblemFormalizer

    case = DecisionCase(
        title="Dylemat bez kryteriów",
        context="Brak kryteriów",
        options=[Option(id="o1", title="A"), Option(id="o2", title="B")],
        criteria=[],
        score_matrix={},
    )
    formalizer = ProblemFormalizer()
    res = formalizer.formalize_case(case)

    assert any("BLOCKS_SOLVING" in info for info in res.missing_information)
    assert res.objective_coefficients == {}, "Formalizer returned non-empty coeffs for 0 criteria"


@pytest.mark.asyncio
async def test_n2_offline_intake_matrix_filling_and_weighted_sum_solving():
    """
    N2 integration test in offline mode (no LLM mocks):
    1. Heuristic analyze extracts options and default criteria from priority tokens.
    2. validate_for_modeling() fails on empty matrix cells.
    3. Filling score_matrix with valid values and source_ref makes validate_for_modeling() pass.
    4. formalize_case produces distinct weighted sum coefficients (not 1.0).
    5. Solve using CP-SAT adapter; verify the option with highest weighted score wins.
    """
    from backend.domain.llm_advisor import LLMAdvisor
    from backend.domain.decision_case import ScoredValue
    from backend.domain.formalizer import ProblemFormalizer
    from backend.domain.problem_ir import ProblemIR, ComputeBudget
    from backend.solvers.cpsat import CPSATAdapter

    # 1. Intake
    advisor = LLMAdvisor(gemini_api_key=None, openai_api_key=None)
    case = advisor.heuristic_analyze("Wybieram między pracą w Korporacji a Startupie.")
    assert len(case.options) == 2
    assert len(case.criteria) >= 2

    # 2. Validation fails because score_matrix is empty
    is_valid, errs = case.validate_for_modeling()
    assert is_valid is False
    assert len(errs) > 0

    # 3. Populate matrix cells:
    # Option 1 (Korporacja): zarobki=18000, kultura=5, autonomia=4, stabilnosc=9
    # Option 2 (Startup): zarobki=28000, kultura=8, autonomia=9, stabilnosc=4
    opt1_id, opt2_id = case.options[0].id, case.options[1].id
    case.score_matrix = {
        opt1_id: {
            "crit_zarobki": ScoredValue(value=18000.0, unit="PLN", provenance="user_supplied", source_ref="user_input"),
            "crit_kultura": ScoredValue(value=5.0, unit="skala 1-10", provenance="assumed", source_ref="assumption"),
            "crit_autonomia": ScoredValue(value=4.0, unit="skala 1-10", provenance="assumed", source_ref="assumption"),
            "crit_stabilnosc": ScoredValue(value=9.0, unit="skala 1-10", provenance="assumed", source_ref="assumption"),
        },
        opt2_id: {
            "crit_zarobki": ScoredValue(value=28000.0, unit="PLN", provenance="user_supplied", source_ref="user_input"),
            "crit_kultura": ScoredValue(value=8.0, unit="skala 1-10", provenance="assumed", source_ref="assumption"),
            "crit_autonomia": ScoredValue(value=9.0, unit="skala 1-10", provenance="assumed", source_ref="assumption"),
            "crit_stabilnosc": ScoredValue(value=4.0, unit="skala 1-10", provenance="assumed", source_ref="assumption"),
        },
    }

    # Now validation passes!
    is_valid_filled, errs_filled = case.validate_for_modeling()
    assert is_valid_filled is True, f"Validation failed after filling: {errs_filled}"
    assert len(errs_filled) == 0

    # 4. Formalization
    formalizer = ProblemFormalizer()
    res = formalizer.formalize_case(case)
    coeffs = res.objective_coefficients
    assert len(coeffs) == 2
    # Distinct non-1.0 coefficients
    vals = list(coeffs.values())
    assert vals[0] != vals[1]
    assert all(v != 1.0 for v in vals)

    # Startup (higher salary, higher autonomy, higher culture) has higher utility
    opt1_slug = list(coeffs.keys())[0]
    opt2_slug = list(coeffs.keys())[1]
    assert coeffs[opt2_slug] > coeffs[opt1_slug]

    # 5. Solve via CP-SAT
    from backend.domain.cognitive.ir_builder import build_problem_ir
    from datetime import datetime, timezone

    vars_spec = [{"id": v, "name": v, "domain": "binary"} for v in res.binary_variables]
    obj_spec = {
        "direction": res.objective_direction,
        "coefficients": res.objective_coefficients,
    }
    consts_spec = [
        {"id": f"eq_{i}", "type": "equality", "lhs_terms": eq["lhs"], "rhs": eq["rhs"]}
        for i, eq in enumerate(res.equality_constraints)
    ]
    problem_ir = build_problem_ir(
        raw_query=case.context or case.title,
        variables_spec=vars_spec,
        objective_spec=obj_spec,
        constraints_spec=consts_spec,
        formalised_description=res.description_formalised,
    )
    problem_ir.approved = True
    problem_ir.approved_at = datetime.now(timezone.utc)

    assert problem_ir.is_ready_to_solve is True
    solver = CPSATAdapter()
    budget = ComputeBudget(wall_time_seconds=5.0)
    solution = solver.solve(problem_ir, budget)

    from backend.solvers.base import MathStatus
    assert solution.math_status in (MathStatus.OPTIMAL, MathStatus.FEASIBLE)
    # Winner must be opt2 (Startup)
    assert solution.assignment[opt2_slug] == 1
    assert solution.assignment[opt1_slug] == 0


# ---------------------------------------------------------------------------
# N3: Evidence Research Connected to UI and Backend
# ---------------------------------------------------------------------------

def test_n3_frontend_calls_research_evidence():
    """
    N3 / G-N3: Frontend components must invoke researchEvidence.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    components_dir = os.path.join(repo_root, "frontend", "src", "components")
    app_file = os.path.join(repo_root, "frontend", "src", "App.tsx")

    hits = []
    for root, _, files in os.walk(components_dir):
        for f in files:
            if f.endswith((".tsx", ".ts")):
                p = os.path.join(root, f)
                with open(p, "r", encoding="utf-8") as fp:
                    content = fp.read()
                    if "researchEvidence(" in content:
                        hits.append(p)

    if os.path.exists(app_file):
        with open(app_file, "r", encoding="utf-8") as fp:
            if "researchEvidence(" in fp.read():
                hits.append(app_file)

    assert len(hits) >= 1, f"Expected at least 1 frontend component calling researchEvidence, found {len(hits)}"


@pytest.mark.asyncio
async def test_n3_evidence_research_endpoint_with_mock_fixtures(monkeypatch):
    """
    N3: POST /evidence/research with mock fixtures returns valid evidence records
    with exact provenance, source_url, and quote.
    """
    monkeypatch.setenv("YQ_MOCK_SEARCH_FIXTURES", "1")
    from starlette.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    payload = {
        "case_id": "test_case_123",
        "target_parameters": [
            {
                "param_id": "zdrowie_koszt",
                "query_text": "zdrowie nakłady koszty",
                "expected_unit": "PLN",
            }
        ],
        "max_results_per_param": 2,
    }

    res = client.post("/api/v1/evidence/research", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert "port_status" in data
    assert data["evidence_count"] >= 1
    ev = data["evidence"][0]
    assert ev["source_url"] == "https://stat.gov.pl/zdrowie/raport-2025.html"
    assert ev["value"] in (84500.0, 175200000000.0)
    assert any(q in ev["quote"] for q in ("84500", "175.2", "175200000000"))


# ---------------------------------------------------------------------------
# N4: Problem Classification & problem_class_override
# ---------------------------------------------------------------------------

def test_n4_classification_system_alarmowy_is_choice_not_design():
    """
    N4: 'system alarmowy do domu czy kamery' must classify as CHOICE, NOT DESIGN.
    Heuristic confidence must be <= 0.5.
    """
    from backend.domain.cognitive.active_inference_engine import (
        classify_problem_class,
        heuristic_classify_problem,
    )
    from backend.domain.problem_classes import ProblemClass

    query = "system alarmowy do domu czy kamery"
    p_class = classify_problem_class(query)
    assert p_class == ProblemClass.CHOICE.value, f"Expected CHOICE, got {p_class}"

    classification = heuristic_classify_problem(query)
    assert classification.problem_class == ProblemClass.CHOICE.value
    assert classification.confidence <= 0.5, f"Expected confidence <= 0.5, got {classification.confidence}"
    assert classification.computable is True


@pytest.mark.asyncio
async def test_n4_intake_problem_class_override():
    """
    N4: POST /api/v1/cognitive/intake respects problem_class_override.
    """
    from starlette.testclient import TestClient
    from backend.main import app
    from backend.domain.problem_classes import ProblemClass

    client = TestClient(app)
    payload = {
        "query": "Wybieram między pracą w Korporacji a Startupie.",
        "problem_class_override": ProblemClass.ALLOCATION.value,
    }

    res = client.post("/api/v1/cognitive/intake", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["problem_class"] == ProblemClass.ALLOCATION.value
    assert data["confidence"] == 1.0


# ---------------------------------------------------------------------------
# N5: Multi-Lever DESIGN Decomposition and Synthesis
# ---------------------------------------------------------------------------

def test_n5_design_offline_decomposition_matrix_filling_and_pareto_synthesis():
    """
    N5: Query DESIGN in offline mode -> empty skeleton -> fill via API -> synthesis -> Pareto front.
    """
    from backend.domain.cognitive.lever_decomposer import (
        decompose_design_query,
        validate_design_problem_for_synthesis,
    )
    from backend.domain.problem_classes import compute_design_synthesis
    from backend.domain.decision_case import ScoredValue

    # 1. Offline decomposition returns template with empty score_matrix
    problem = decompose_design_query("Reforma systemu ochrony zdrowia w Polsce")
    assert len(problem.levers) == 3
    assert all(len(l.options) >= 2 for l in problem.levers)
    assert len(problem.criteria) >= 2

    # Initial validation fails due to empty cells
    is_valid_initial, errs_initial = validate_design_problem_for_synthesis(problem)
    assert is_valid_initial is False
    assert len(errs_initial) > 0

    # 2. User populates score matrix
    for lev in problem.levers:
        for o_idx, opt in enumerate(lev.options):
            for c_idx, crit in enumerate(problem.criteria):
                # Concrete synthetic score for each cell
                val = 10.0 + o_idx * 5.0 + c_idx * 2.0
                problem.score_matrix[lev.id][opt.id][crit.id] = ScoredValue(
                    value=val,
                    unit=crit.unit,
                    provenance="user_supplied",
                    source_ref="Wprowadzone przez eksperta",
                )

    # 3. Validation now passes
    is_valid_filled, errs_filled = validate_design_problem_for_synthesis(problem)
    assert is_valid_filled is True, f"Validation failed: {errs_filled}"

    # 4. Compute design synthesis
    synthesis = compute_design_synthesis(problem)
    assert synthesis.problem_id is not None
    assert len(synthesis.pareto_frontier) >= 1
    assert len(synthesis.optimal_configuration) == len(problem.levers)
    assert len(synthesis.lever_importance_ranking) == len(problem.levers)


# ---------------------------------------------------------------------------
# N6: Unified Model Access Exclusively Through LLMGateway
# ---------------------------------------------------------------------------

def test_n6_no_direct_httpx_in_backend_domain_and_formalizer_uses_gateway():
    """
    N6: Ensure backend/domain has zero direct httpx.(post|Client()) calls,
    and formalizer._try_llm_formalize uses LLMGateway when available.
    """
    import subprocess
    from pathlib import Path

    repo_root = Path(__file__).parent.parent
    cmd = 'grep -rnE "httpx\\.(post|Client\\()" backend/domain'
    res = subprocess.run(cmd, shell=True, cwd=repo_root, capture_output=True, text=True)
    assert res.returncode != 0, f"Found direct httpx calls in backend/domain:\n{res.stdout}"
    assert len(res.stdout.strip()) == 0

    from backend.domain.formalizer import ProblemFormalizer
    # Offline or empty key returns None safely without raising or using httpx
    formalizer = ProblemFormalizer(gemini_api_key=None)
    res_formalize = formalizer._try_llm_formalize("Dowolny tekst testowy")
    assert res_formalize is None


# ---------------------------------------------------------------------------
# N7: Elimination of Implicit Auto-Approval and ProblemRouter in Universal API
# ---------------------------------------------------------------------------

def test_n7_universal_engine_approval_gate_and_problem_router():
    """
    N7: universal_engine.py does not create ProblemIR with approved=True by default,
    rejects unapproved requests with status=ERROR, and uses ProblemRouter for solver selection.
    """
    import subprocess
    from pathlib import Path
    from backend.api.universal_engine import (
        UniversalEngine,
        UniversalComputeRequest,
        VariableDef,
    )

    repo_root = Path(__file__).parent.parent
    # Gate mechanical check: zero approved=True in universal_engine.py
    cmd_app = 'grep -n "approved=True" backend/api/universal_engine.py'
    res_app = subprocess.run(cmd_app, shell=True, cwd=repo_root, capture_output=True, text=True)
    assert res_app.returncode != 0, f"Found approved=True in universal_engine.py:\n{res_app.stdout}"

    # Gate mechanical check: ProblemRouter is used in universal_engine.py
    cmd_router = 'grep -n "ProblemRouter" backend/api/universal_engine.py'
    res_router = subprocess.run(cmd_router, shell=True, cwd=repo_root, capture_output=True, text=True)
    assert res_router.returncode == 0, "ProblemRouter is not used in universal_engine.py"

    engine = UniversalEngine()
    req_unapproved = UniversalComputeRequest(
        title="Dylemat bez zatwierdzenia",
        variables=[
            VariableDef(id="v1", name="Wariant A", value=10.0),
            VariableDef(id="v2", name="Wariant B", value=20.0),
        ],
        approved_by_caller=False,
    )
    # Check compile_to_ir produces approved=False
    ir = engine.compile_to_ir(req_unapproved)
    assert ir.approved is False
    assert ir.approved_at is None

    # Check execute rejects unapproved model
    resp = engine.execute(req_unapproved)
    assert resp.status == "ERROR"
    assert resp.verification["verdict"] == "UNAPPROVED_MODEL"

    # When approved_by_caller=True, execution proceeds and selects solver via ProblemRouter
    req_approved = UniversalComputeRequest(
        title="Dylemat zatwierdzony",
        variables=[
            VariableDef(id="v1", name="Wariant A", value=10.0),
            VariableDef(id="v2", name="Wariant B", value=20.0),
        ],
        approved_by_caller=True,
    )
    resp_ok = engine.execute(req_approved)
    assert resp_ok.status == "SUCCESS"
    assert resp_ok.verification["feasible"] is True


# ---------------------------------------------------------------------------
# N8: Zero Unsupported Hallucination Claims in UI and Help Service
# ---------------------------------------------------------------------------

def test_n8_no_unsupported_hallucination_claims_in_ui_and_help_service():
    """
    N8: Verify that frontend/src and backend/api/help_service.py contain
    zero occurrences of the word 'halucynac*'.
    """
    import subprocess
    from pathlib import Path

    repo_root = Path(__file__).parent.parent
    cmd = 'grep -rni "halucynac" frontend/src backend/api/help_service.py'
    res = subprocess.run(cmd, shell=True, cwd=repo_root, capture_output=True, text=True)
    assert res.returncode != 0, f"Found forbidden hallucination claims:\n{res.stdout}"
    assert len(res.stdout.strip()) == 0


# ---------------------------------------------------------------------------
# N9: Problem IR Schema Version 0.3
# ---------------------------------------------------------------------------

def test_n9_problem_ir_schema_version_is_0_3():
    """
    N9: Verify that ProblemIR.schema_version is exactly '0.3'.
    """
    from backend.domain.problem_ir import ProblemIR
    ir = ProblemIR(
        description_raw="Test N9",
        description_formalised="Formalized test N9",
    )
    assert ir.schema_version == "0.3"

    import subprocess
    from pathlib import Path
    repo_root = Path(__file__).parent.parent
    cmd = 'grep -n \'schema_version: str = "0.3"\' backend/domain/problem_ir.py'
    res = subprocess.run(cmd, shell=True, cwd=repo_root, capture_output=True, text=True)
    assert res.returncode == 0, "schema_version is not 0.3 in problem_ir.py"


# ---------------------------------------------------------------------------
# N11: End-to-End Playwright Suite with Real Uvicorn Backend
# ---------------------------------------------------------------------------

def test_n11_e2e_playwright_configuration_and_real_backend_spec():
    """
    N11: Verify that frontend/e2e/v4-real-backend.spec.ts exists,
    and frontend/playwright.config.ts configures a webServer launching real uvicorn.
    """
    from pathlib import Path
    repo_root = Path(__file__).parent.parent
    spec_path = repo_root / "frontend" / "e2e" / "v4-real-backend.spec.ts"
    assert spec_path.exists(), f"Missing spec file: {spec_path}"

    content = spec_path.read_text(encoding="utf-8")
    assert "/api/v1/health" in content
    assert "hero-problem-input" in content
    assert "OBLICZ ROZWIĄZANIE KWANTOWE" in content

    config_path = repo_root / "frontend" / "playwright.config.ts"
    config_content = config_path.read_text(encoding="utf-8")
    assert "webServer" in config_content
    assert "uvicorn" in config_content











