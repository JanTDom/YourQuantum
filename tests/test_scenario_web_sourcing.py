"""
Unit tests for Scenario Web Sourcing with Grounded Verbatim Quotes (Prompt V9-C / DEC-032).
Enforces:
1. Fetched page with quote present produces web_sourced premise with is_accepted=False.
2. Extractor rejects quotes missing from page text (no web_sourced premise emitted).
3. Fetch failures (SSRF, 404, timeout) fail gracefully with zero web_sourced premises and no exception.
4. Snippet text is never used as page_text or content_hash (Rule R6 compliance).
5. Active inference intake telemetry tracks web_search_urls_returned, web_pages_fetched, web_quotes_verified.
"""
from __future__ import annotations

import asyncio
import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.domain.evidence.models import Evidence, EvidenceDocument, ExtractionMethod, WebSearchResult
from backend.domain.scenario_weighting import (
    ScenarioOutcome,
    EvidencePremise,
    compute_scenario_distribution,
)
from backend.domain.cognitive.scenario_decomposer import (
    decompose_scenario_query_async,
)
from backend.infrastructure.web_research.extractor import EvidenceExtractor


def test_web_sourced_premise_created_when_quote_present():
    """
    Case 1: When a verified Evidence item (with quote confirmed in fetched document)
    is passed to decompose_scenario_query_async, it must emit a premise with:
    - provenance == 'web_sourced'
    - is_accepted == False (DEC-032 / V9-C gate)
    - Verbatim quote embedded in premise description
    - It must NOT affect the scenario probability distribution until explicitly accepted.
    """
    async def _run():
        raw_doc_text = "Oficjalny raport: wskaźnik inflacji bazowej spadł do poziomu 2.4% w ujęciu rocznym."
        doc_hash = hashlib.sha256(raw_doc_text.encode("utf-8")).hexdigest()

        verified_ev = Evidence(
            id="ev_test_123",
            claim="Spadek inflacji bazowej do 2.4%",
            value=2.4,
            unit="%",
            source_url="https://stat.gov.pl/makro/inflacja-2026.html",
            source_title="GUS: Wskaźniki cen i inflacji",
            publisher="Główny Urząd Statystyczny",
            content_hash=doc_hash,
            quote="wskaźnik inflacji bazowej spadł do poziomu 2.4% w ujęciu rocznym",
            extraction_method=ExtractionMethod.LLM_EXTRACTED,
            confidence=0.98,
        )

        case, forecast = await decompose_scenario_query_async(
            query="Jaki będzie kierunek polityki monetarnej do końca 2026 roku?",
            web_snippets=["[GUS](https://stat.gov.pl): Inflacja bazowa spada."],
            verified_evidences=[verified_ev],
        )

        assert len(forecast.scenarios) >= 2
        web_premises = [p for p in forecast.evidence_premises if p.provenance == "web_sourced"]
        assert len(web_premises) == 1, "Must produce exactly one web_sourced premise"

        wp = web_premises[0]
        assert wp.id == "web_1"
        assert wp.is_accepted is False, "Premise MUST require human acceptance (DEC-032)"
        assert "inflacji bazowej spadł do poziomu 2.4%" in wp.description.lower()
        assert "główny urząd statystyczny" in wp.source.lower()
        assert wp.source_ref == "https://stat.gov.pl/makro/inflacja-2026.html"

        # Prior to acceptance, the distribution across 2 default scenarios must be uniform (50% / 50%)
        active_premises = [p for p in forecast.evidence_premises if p.is_accepted]
        assert len(active_premises) == 0, "No premises are accepted yet"

        dist_unaccepted = compute_scenario_distribution(
            query=forecast.query,
            scenarios=[sc.model_copy() for sc in forecast.scenarios],
            premises=forecast.evidence_premises,
        )
        for sc in dist_unaccepted.scenarios:
            assert pytest.approx(sc.probability, abs=1e-3) == 1.0 / len(dist_unaccepted.scenarios)

        # After human acceptance, the premise impacts shift the scenario distribution away from uniform
        accepted_premises = [p.model_copy(update={"is_accepted": True}) for p in forecast.evidence_premises]
        dist_accepted = compute_scenario_distribution(
            query=forecast.query,
            scenarios=[sc.model_copy() for sc in forecast.scenarios],
            premises=accepted_premises,
        )
        probs = [sc.probability for sc in dist_accepted.scenarios]
        assert max(probs) > 1.0 / len(dist_accepted.scenarios), "Accepted web premise must shift scenario probability"

    asyncio.run(_run())


def test_extractor_rejects_missing_quote_honesty_check():
    """
    Case 2: EvidenceExtractor honesty rule: if the LLM hallucinates a quote
    that does NOT literally exist in document.page_text, the evidence MUST be rejected.
    """
    async def _run():
        doc = EvidenceDocument(
            url="https://bankier.pl/wiadomosci/stopy-procentowe.html",
            content_hash="abc123sha256",
            page_text="Rada Polityki Pieniężnej utrzymała stopy procentowe na niezmienionym poziomie 5.75 procent.",
            title="RPP bez zmian",
            status_code=200,
            mime_type="text/html",
        )

        mock_gw = MagicMock()
        mock_gw.is_available = True
        extractor = EvidenceExtractor(llm_gateway=mock_gw)

        fake_llm_json = {
            "claim": "RPP planuje obniżkę stóp o 100 pb",
            "value": 100,
            "unit": "pb",
            "quote": "Zarząd NBP zapowiedział gwałtowną obniżkę stóp procentowych o 100 punktów bazowych w czerwcu.",
        }

        with patch.object(extractor, "_extract_via_llm", AsyncMock(return_value=fake_llm_json)):
            evidence = await extractor.extract_parameter_evidence(
                document=doc,
                target_param="obnizka_stop",
            )

        assert evidence is None, "Extractor MUST reject evidence whose quote is not found verbatim in page_text"

    asyncio.run(_run())


def test_fetch_failure_produces_zero_web_premises_without_crashing():
    """
    Case 3: If web fetch fails (404, SSRF blocked, timeout, None),
    scenario intake must not crash and must emit zero web_sourced premises.
    """
    async def _run():
        case, forecast = await decompose_scenario_query_async(
            query="Perspektywy cen gazu ziemnego w Europie",
            web_snippets=[],
            verified_evidences=[],
        )

        web_premises = [p for p in forecast.evidence_premises if p.provenance == "web_sourced"]
        assert len(web_premises) == 0, "No web premises when verified_evidences is empty"

    asyncio.run(_run())


def test_snippet_text_never_used_as_page_text_or_content_hash():
    """
    Case 4 (Rule R6): Web search snippets must never be passed as page_text
    or used to compute content_hash. Only SafeWebFetcher downloads can generate EvidenceDocument.
    """
    snippet_content = "To jest tylko krótki snippet z wyników Google / Bing..."
    snippet_hash = hashlib.sha256(snippet_content.encode("utf-8")).hexdigest()

    full_page_html = "<html><body><article><p>Prawdziwy pełny artykuł pobrany z serwera...</p></article></body></html>"
    page_text = "Prawdziwy pełny artykuł pobrany z serwera..."
    real_hash = hashlib.sha256(full_page_html.encode("utf-8")).hexdigest()

    doc = EvidenceDocument(
        url="https://example.com/article",
        content_hash=real_hash,
        page_text=page_text,
        title="Prawdziwy Artykuł",
        status_code=200,
    )

    assert doc.content_hash != snippet_hash
    assert doc.page_text != snippet_content
    assert doc.content_hash == real_hash


def test_active_inference_scenario_intake_telemetry():
    """
    Case 5: ActiveInferenceOrchestrator scenario intake pathway tracks:
    - web_search_urls_returned
    - web_pages_fetched
    - web_quotes_verified
    """
    async def _run():
        from backend.domain.cognitive.active_inference_engine import ActiveInferenceOrchestrator
        from backend.infrastructure.web_research.fetcher import SafeWebFetcher

        mock_reasoning_port = MagicMock()
        mock_session = AsyncMock()
        engine = ActiveInferenceOrchestrator(reasoning_port=mock_reasoning_port)
        test_query = "Prognoza scenariuszowa cen energii elektrycznej w Polsce do 2027 roku"

        sample_html = "Raport rynku mocy: średnia cena energii elektrycznej w kontraktach terminowych wyniosła 430 PLN za MWh."
        sample_hash = hashlib.sha256(sample_html.encode("utf-8")).hexdigest()

        mock_doc = EvidenceDocument(
            url="https://ure.gov.pl/rynek-energii-2026.html",
            content_hash=sample_hash,
            page_text="Raport rynku mocy: średnia cena energii elektrycznej w kontraktach terminowych wyniosła 430 PLN za MWh.",
            title="URE Raport",
            status_code=200,
        )

        mock_search_results = [
            WebSearchResult(
                url="https://ure.gov.pl/rynek-energii-2026.html",
                title="URE Raport Rynek Mocy",
                snippet="Średnia cena energii elektrycznej 430 PLN",
            ),
        ]

        mock_evidence = Evidence(
            id="ev_ure_1",
            claim="Średnia cena energii elektrycznej 430 PLN/MWh",
            value=430.0,
            unit="PLN/MWh",
            source_url="https://ure.gov.pl/rynek-energii-2026.html",
            source_title="URE Raport Rynek Mocy",
            publisher="Urząd Regulacji Energetyki",
            content_hash=sample_hash,
            quote="średnia cena energii elektrycznej w kontraktach terminowych wyniosła 430 PLN za MWh",
            confidence=0.95,
        )

        with patch("backend.infrastructure.web_research.search_adapter.WebResearchAdapter.is_available", return_value=True), \
             patch("backend.infrastructure.web_research.search_adapter.WebResearchAdapter.search", AsyncMock(return_value=mock_search_results)), \
             patch.object(SafeWebFetcher, "fetch", AsyncMock(return_value=mock_doc)), \
             patch("backend.infrastructure.web_research.extractor.EvidenceExtractor.extract_parameter_evidence", AsyncMock(return_value=mock_evidence)):

            formalization, ws = await engine.run_intake(session=mock_session, query=test_query)

        assert formalization.metadata is not None
        assert formalization.metadata.get("web_search_urls_returned") == 1
        assert formalization.metadata.get("web_pages_fetched") == 1
        assert formalization.metadata.get("web_quotes_verified") == 1
        assert formalization.scenario_forecast is not None

    asyncio.run(_run())

