"""
YourQuantum — Phase C Regression and Verification Test Suite
Tests for Web Research, Evidence Layer, SSRF Security, Verbatim Quote Verification,
Conflict Detection, and ProblemIR Integration (C1–C7).
"""
import hashlib
import os
import pytest
from fastapi.testclient import TestClient

from backend.domain.decision_case import (
    Criterion,
    DecisionCase,
    Option,
    ScoredValue,
)
DecisionOption = Option
from backend.domain.evidence.models import (
    Evidence,
    EvidenceConflict,
    EvidenceDocument,
    ExtractionMethod,
    ResearchQuery,
)
from backend.domain.evidence.planner import ResearchPlanner
from backend.domain.problem_ir import ProblemIR, Provenance, Variable, VariableDomain, ExpressionRegistry
from backend.infrastructure.web_research.extractor import EvidenceExtractor
from backend.infrastructure.web_research.fetcher import SafeWebFetcher, validate_url_security
from backend.infrastructure.web_research.search_adapter import WebResearchAdapter
from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# C1: Evidence Models & Data Integrity
# ---------------------------------------------------------------------------

def test_c1_evidence_models_and_hash_integrity():
    """C1 & C2: Evidence record creation, SHA-256 content hash, and extraction methods."""
    sample_text = "Średni koszt łóżka szpitalnego w Polsce wynosi 84500 PLN rocznie."
    doc_hash = hashlib.sha256(sample_text.encode("utf-8")).hexdigest()

    ev = Evidence(
        id="ev_test_1",
        claim="Średni koszt łóżka internistycznego",
        value=84500.0,
        unit="PLN",
        source_url="https://stat.gov.pl/zdrowie.html",
        source_title="GUS Raport Zdrowie",
        publisher="stat.gov.pl",
        content_hash=doc_hash,
        quote="Średni koszt łóżka szpitalnego w Polsce wynosi 84500 PLN rocznie.",
        extraction_method=ExtractionMethod.LLM_EXTRACTED,
        confidence=0.95,
        target_param="szpital.koszt_lozka",
    )

    assert ev.id == "ev_test_1"
    assert ev.value == 84500.0
    assert ev.content_hash == doc_hash
    assert len(ev.quote) <= 300
    assert ev.extraction_method == ExtractionMethod.LLM_EXTRACTED


# ---------------------------------------------------------------------------
# C2: SSRF Security Defenses
# ---------------------------------------------------------------------------

def test_c2_safe_web_fetcher_ssrf_blocking():
    """C5: SSRF prevention strictly rejects cloud metadata, loopback, private ranges, and non-http schemes."""
    # 1. Cloud metadata
    is_safe, reason = validate_url_security("http://169.254.169.254/latest/meta-data/")
    assert not is_safe
    assert "Cloud metadata" in reason or "Link-local" in reason or "Forbidden host" in reason

    # 2. Localhost / Loopback
    is_safe_lh, reason_lh = validate_url_security("http://localhost:8000/admin")
    assert not is_safe_lh

    is_safe_ip, reason_ip = validate_url_security("http://127.0.0.1:8080/")
    assert not is_safe_ip
    assert "Loopback" in reason_ip or "Forbidden host" in reason_ip

    # 3. Disallowed scheme
    is_safe_file, reason_file = validate_url_security("file:///etc/passwd")
    assert not is_safe_file
    assert "Scheme" in reason_file


# ---------------------------------------------------------------------------
# C3: Verbatim Quote Verification (Zero Hallucination Guarantee)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_c3_verbatim_quote_verification_drops_hallucinated_evidence():
    """C3: EvidenceExtractor drops any candidate whose quote is not found in the actual document text."""
    real_text = (
        "Wydatki publiczne na ochronę zdrowia w 2025 roku wyniosły 175.2 miliarda złotych, "
        "co odpowiada 6.8% PKB."
    )
    doc_hash = hashlib.sha256(real_text.encode("utf-8")).hexdigest()
    doc = EvidenceDocument(
        url="https://stat.gov.pl/raport.html",
        content_hash=doc_hash,
        page_text=real_text,
        title="GUS Zdrowie",
        publisher="GUS",
    )

    extractor = EvidenceExtractor()

    # 1. Legitimate extraction with verbatim quote
    assert extractor._verify_quote_in_text("wyniosły 175.2 miliarda złotych", real_text)

    # 2. Hallucinated quote NOT present in document text must be rejected
    fake_quote = "Rząd przewiduje 250 miliardów złotych na szpitale w 2030 roku."
    assert not extractor._verify_quote_in_text(fake_quote, real_text)

    # Deterministic heuristic extraction extracts only real text and quotes
    heuristic_ev = await extractor.extract_parameter_evidence(
        document=doc,
        target_param="wydatki_zdrowie",
        expected_unit="mld PLN",
    )
    assert heuristic_ev is not None
    assert heuristic_ev.value == 175.2
    assert heuristic_ev.quote in real_text


# ---------------------------------------------------------------------------
# C4: Multi-Source Conflict Detection & Median Resolution
# ---------------------------------------------------------------------------

def test_c4_conflict_detection_and_spread_calculation():
    """C4: Conflicting values across sources trigger EvidenceConflict with spread and median."""
    ev1 = Evidence(
        id="ev_src_1",
        claim="Raport rządowy",
        value=175.2,
        unit="mld PLN",
        source_url="https://stat.gov.pl/1",
        source_title="GUS",
        content_hash="hash1",
        quote="175.2 miliarda",
        target_param="naklady.zdrowie",
    )
    ev2 = Evidence(
        id="ev_src_2",
        claim="Raport think-tanku",
        value=182.0,
        unit="mld PLN",
        source_url="https://nos.org.pl/2",
        source_title="NOS",
        content_hash="hash2",
        quote="182.0 miliarda",
        target_param="naklady.zdrowie",
    )

    adapter = WebResearchAdapter()
    planner = ResearchPlanner(evidence_port=adapter)

    conflict = planner._detect_conflict("naklady.zdrowie", [ev1, ev2])
    assert conflict is not None
    assert conflict.target_param == "naklady.zdrowie"
    assert len(conflict.evidence_ids) == 2
    assert conflict.spread_min == 175.2
    assert conflict.spread_max == 182.0
    assert abs(float(conflict.resolved_value) - 178.6) < 1e-4
    assert conflict.resolution_method == "median"
    # Verify cross-referenced conflict markers
    assert "ev_src_2" in ev1.conflicts_with
    assert "ev_src_1" in ev2.conflicts_with


# ---------------------------------------------------------------------------
# C5: ResearchPlanner on DecisionCase with Missing Data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_c5_research_planner_decision_case_integration():
    """C3 & C5: Scanner identifies missing parameters and plans targeted privacy-preserving queries."""
    case = DecisionCase(
        id="case_health_test",
        title="Wybór modelu finansowania ochrony zdrowia",
        context="Analiza porównawcza modeli",
        options=[
            DecisionOption(id="opt_ubezp", title="Model składkowy"),
            DecisionOption(id="opt_budzet", title="Model budżetowy"),
        ],
        criteria=[
            Criterion(id="crit_koszt", name="Roczny koszt systemu", direction="minimize", unit="mld PLN", weight=0.6),
            Criterion(id="crit_jakosc", name="Dostępność świadczeń", direction="maximize", unit="pkt", weight=0.4),
        ],
        score_matrix={
            "opt_ubezp": {
                # Already user-supplied
                "crit_jakosc": ScoredValue(value=75.0, unit="pkt", provenance=Provenance.USER_SUPPLIED, source_ref="ankieta"),
            }
        },
    )

    adapter = WebResearchAdapter()
    planner = ResearchPlanner(evidence_port=adapter)

    queries = planner.identify_missing_parameters(case)
    # Total cells: 2 options * 2 criteria = 4. 1 is supplied, so 3 missing.
    assert len(queries) == 3

    # Ensure queries do NOT leak the whole user case context
    for q in queries:
        assert case.context not in q.query_text
        assert ("Model składkowy" in q.query_text or "Model budżetowy" in q.query_text)

    # Test applying evidence to case
    ev = Evidence(
        id="ev_koszt_ubezp",
        claim="Koszt modelu składkowego",
        value=175.2,
        unit="mld PLN",
        source_url="https://stat.gov.pl/raport.html",
        source_title="GUS",
        content_hash="abc123hash",
        quote="175.2 miliarda złotych",
        target_param="opt_ubezp.crit_koszt",
    )

    updated_case = planner.apply_evidence_to_case(case, [ev])
    cell = updated_case.score_matrix["opt_ubezp"]["crit_koszt"]
    assert cell.value == 175.2
    assert cell.provenance == Provenance.WEB_SOURCED
    assert cell.source_ref == "ev_koszt_ubezp"


# ---------------------------------------------------------------------------
# C6: Attach Evidence to ProblemIR DataSources
# ---------------------------------------------------------------------------

def test_c6_attach_evidence_to_problem_ir():
    """C2: Attaching evidence registers DataSource with URL and SHA-256 hash in ProblemIR."""
    ir = ProblemIR(
        description_raw="Optymalizacja sieci placówek",
        description_formalised="Formalny opis",
        variables=[
            Variable(id="x_wawa", name="Placówka Warszawa", domain=VariableDomain.BINARY),
        ],
        expressions=ExpressionRegistry(),
    )

    ev = Evidence(
        id="ev_placowka",
        claim="Koszt placówki Warszawa",
        value=120000.0,
        unit="PLN",
        source_url="https://nfz.gov.pl/placowki.html",
        source_title="Biuletyn NFZ",
        content_hash="sha256_mock_hash_for_nfz",
        quote="Koszt kontraktu wynosi 120000 PLN",
        target_param="x_wawa",
    )

    planner = ResearchPlanner(evidence_port=WebResearchAdapter())
    updated_ir = planner.attach_evidence_to_ir(ir, [ev])

    assert len(updated_ir.data_sources) == 1
    ds = updated_ir.data_sources[0]
    assert ds.content_hash == "sha256_mock_hash_for_nfz"
    assert ds.source_description == "https://nfz.gov.pl/placowki.html"
    assert updated_ir.variables[0].provenance == Provenance.WEB_SOURCED


# ---------------------------------------------------------------------------
# C7: Evidence API Endpoints
# ---------------------------------------------------------------------------

def test_c7_evidence_api_endpoints():
    """C1 & C6: REST endpoints for evidence research and retrieval."""
    # 1. Conduct research endpoint
    resp = client.post(
        "/api/v1/evidence/research",
        json={
            "target_parameters": [
                {
                    "param_id": "test_cost",
                    "query_text": "zdrowie koszty",
                    "expected_unit": "PLN",
                    "rationale": "Szacunek kosztów",
                }
            ],
            "max_results_per_param": 1,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert "evidence_count" in data
    assert "port_status" in data

    # 2. Get evidence record 404 on nonexistent
    resp_404 = client.get("/api/v1/evidence/ev_nonexistent_xyz")
    assert resp_404.status_code == 404
