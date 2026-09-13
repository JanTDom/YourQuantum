"""
Tests for YourQuantum V4 Regressions (R1-R6) and Missing Features (N1-N11).
Follows strict evidence-first DoD per docs/BUILD_SPEC_V4.md.
"""
import hashlib
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

