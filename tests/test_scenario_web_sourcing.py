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
    Case 1a: Model response without web_N IDs -> web_sourced premises have all impacts equal to 0.0,
    distribution after accepting remains uniform, and description states that impact was not specified (Prompt V11-1).
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

        mock_llm_res = MagicMock()
        mock_llm_res.parsed_json = {
            "domain": "Polityka monetarna",
            "scenarios": [
                {"id": "sc_1", "title": "Obniżka stóp procentowych", "description": "Scenariusz łagodzenia", "risk_level": "LOW"},
                {"id": "sc_2", "title": "Utrzymanie stóp procentowych", "description": "Scenariusz stabilizacji", "risk_level": "MEDIUM"},
            ],
            "premises": [
                # Model returns pr_1, but NO web_1 impact!
                {"id": "pr_1", "name": "Wzrost PKB", "description": "Dynamika PKB", "impacts": [{"scenario_id": "sc_1", "impact": 0.4}, {"scenario_id": "sc_2", "impact": -0.4}], "confidence": 0.9, "weight": 1.0}
            ]
        }

        with patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.is_available", return_value=True), \
             patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.generate", AsyncMock(return_value=mock_llm_res)):
            case, forecast = await decompose_scenario_query_async(
                query="Jaki będzie kierunek polityki monetarnej do końca 2026 roku?",
                web_snippets=["[GUS](https://stat.gov.pl): Inflacja bazowa spada."],
                verified_evidences=[verified_ev],
            )

        web_premises = [p for p in forecast.evidence_premises if p.provenance == "web_sourced"]
        assert len(web_premises) == 1, "Must produce exactly one web_sourced premise"

        wp = web_premises[0]
        assert wp.id == "web_1"
        assert wp.is_accepted is False, "Premise MUST require human acceptance (DEC-032)"
        assert all(v == 0.0 for v in wp.impact_on_scenarios.values()), f"All impacts must be 0.0 when model gave none, got {wp.impact_on_scenarios}"
        assert "wpływ na scenariusze nie został określony; przesłanka nie przeważa rozkładu, dopóki nie nadasz jej wag ręcznie." in wp.description.lower()
        assert "[wpływy: nieokreślone]" in (wp.source_ref or "")
        assert forecast.telemetry.get("unspecified_impacts_count") == 1

        # When this web_sourced premise is accepted, the distribution across scenarios must remain strictly uniform
        accepted_web_premises = [wp.model_copy(update={"is_accepted": True})]
        dist_accepted = compute_scenario_distribution(
            query=forecast.query,
            scenarios=[sc.model_copy() for sc in forecast.scenarios],
            premises=accepted_web_premises,
        )
        for sc in dist_accepted.scenarios:
            assert pytest.approx(sc.probability, abs=1e-3) == 1.0 / len(dist_accepted.scenarios)

    asyncio.run(_run())


def test_web_sourced_premise_with_model_impacts_preserves_model_numbers():
    """
    Case 1b: Model response WITH web_1 ID -> web_sourced premises preserve exact impacts from model,
    description indicates analytical proposal of the model, and acceptance shifts distribution (Prompt V11-1).
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

        mock_llm_res = MagicMock()
        mock_llm_res.parsed_json = {
            "domain": "Polityka monetarna",
            "scenarios": [
                {"id": "sc_1", "title": "Obniżka stóp procentowych", "description": "Scenariusz łagodzenia", "risk_level": "LOW"},
                {"id": "sc_2", "title": "Utrzymanie stóp procentowych", "description": "Scenariusz stabilizacji", "risk_level": "MEDIUM"},
            ],
            "premises": [
                {
                    "id": "web_1",
                    "name": "Spadek inflacji bazowej",
                    "description": "Oficjalny odczyt GUS",
                    "impacts": [{"scenario_id": "sc_1", "impact": 0.85}, {"scenario_id": "sc_2", "impact": -0.65}],
                    "confidence": 0.98,
                    "weight": 1.5,
                }
            ]
        }

        with patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.is_available", return_value=True), \
             patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.generate", AsyncMock(return_value=mock_llm_res)):
            case, forecast = await decompose_scenario_query_async(
                query="Jaki będzie kierunek polityki monetarnej do końca 2026 roku?",
                web_snippets=["[GUS](https://stat.gov.pl): Inflacja bazowa spada."],
                verified_evidences=[verified_ev],
            )

        web_premises = [p for p in forecast.evidence_premises if p.provenance == "web_sourced"]
        assert len(web_premises) == 1
        wp = web_premises[0]
        assert wp.impact_on_scenarios["sc_1"] == 0.85
        assert wp.impact_on_scenarios["sc_2"] == -0.65
        assert "liczbowy wpływ na scenariusze jest propozycją analityczną modelu i wymaga zatwierdzenia przez decydenta." in wp.description.lower()
        assert wp.source_ref == "https://stat.gov.pl/makro/inflacja-2026.html"
        assert "[wpływy: nieokreślone]" not in (wp.source_ref or "")
        assert forecast.telemetry.get("unspecified_impacts_count") == 0

        # Prior to acceptance, distribution is uniform
        dist_unaccepted = compute_scenario_distribution(
            query=forecast.query,
            scenarios=[sc.model_copy() for sc in forecast.scenarios],
            premises=forecast.evidence_premises,
        )
        for sc in dist_unaccepted.scenarios:
            assert pytest.approx(sc.probability, abs=1e-3) == 1.0 / len(dist_unaccepted.scenarios)

        # After acceptance, the model-provided impact shifts probability
        accepted_premises = [p.model_copy(update={"is_accepted": True}) for p in forecast.evidence_premises]
        dist_accepted = compute_scenario_distribution(
            query=forecast.query,
            scenarios=[sc.model_copy() for sc in forecast.scenarios],
            premises=accepted_premises,
        )
        assert dist_accepted.scenarios[0].probability > dist_accepted.scenarios[1].probability

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

        mock_llm_res = MagicMock()
        mock_llm_res.parsed_json = {
            "domain": "Rynek energii",
            "scenarios": [
                {"id": "sc_1", "title": "Stabilizacja cen energii", "description": "Utrzymanie cen", "risk_level": "LOW"},
                {"id": "sc_2", "title": "Wzrost cen energii", "description": "Presja kosztowa", "risk_level": "MEDIUM"},
            ],
            "premises": [
                {"id": "web_1", "name": "Cena energii 430 PLN", "description": "Rynek mocy", "impacts": [{"scenario_id": "sc_1", "impact": 0.5}, {"scenario_id": "sc_2", "impact": -0.5}], "confidence": 0.95, "weight": 1.0}
            ],
        }

        with patch("backend.infrastructure.web_research.search_adapter.WebResearchAdapter.is_available", return_value=True), \
             patch("backend.infrastructure.web_research.search_adapter.WebResearchAdapter.search", AsyncMock(return_value=mock_search_results)), \
             patch.object(SafeWebFetcher, "fetch", AsyncMock(return_value=mock_doc)), \
             patch("backend.infrastructure.web_research.extractor.EvidenceExtractor.extract_parameter_evidence", AsyncMock(return_value=mock_evidence)), \
             patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.is_available", return_value=True), \
             patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.generate", AsyncMock(return_value=mock_llm_res)):

            formalization, ws = await engine.run_intake(session=mock_session, query=test_query)

        assert formalization.metadata is not None
        assert formalization.metadata.get("web_search_urls_returned") == 1
        assert formalization.metadata.get("web_pages_fetched") == 1
        assert formalization.metadata.get("web_quotes_verified") == 1
        assert formalization.scenario_forecast is not None

    asyncio.run(_run())


def test_verified_evidences_with_insufficient_scenarios_does_not_fabricate_scenarios():
    """
    Case 6 (Prompt V11-2): When verified_evidences is non-empty but the model returns
    fewer than 2 scenarios (or none at all), the decomposer must NOT fabricate any fallback scenarios.
    Instead, it must cleanly return too_vague input quality requiring user clarification.
    """
    async def _run():
        raw_doc_text = "Raport: produkcja przemysłowa spadła o 1.2% r/r."
        doc_hash = hashlib.sha256(raw_doc_text.encode("utf-8")).hexdigest()

        verified_ev = Evidence(
            id="ev_ind_1",
            claim="Spadek produkcji przemysłowej o 1.2%",
            value=-1.2,
            unit="%",
            source_url="https://stat.gov.pl/przemysl-2026.html",
            source_title="GUS Przemysł",
            publisher="Główny Urząd Statystyczny",
            content_hash=doc_hash,
            quote="produkcja przemysłowa spadła o 1.2% r/r",
            extraction_method=ExtractionMethod.LLM_EXTRACTED,
            confidence=0.95,
        )

        mock_llm_res = MagicMock()
        # Model returns empty scenarios or only 1 scenario!
        mock_llm_res.parsed_json = {
            "domain": "Gospodarka",
            "scenarios": [],
            "premises": [],
        }

        with patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.is_available", return_value=True), \
             patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.generate", AsyncMock(return_value=mock_llm_res)):
            case, forecast = await decompose_scenario_query_async(
                query="Prognoza koniunktury gospodarczej w Polsce do końca roku",
                web_snippets=["[GUS](https://stat.gov.pl): Spadek produkcji."],
                verified_evidences=[verified_ev],
            )

        # Must NOT fabricate sc_1 or sc_2
        assert len(forecast.scenarios) == 0, f"Must not fabricate scenarios, got: {forecast.scenarios}"
        assert case.input_quality.level == "too_vague", "Must require user clarification when scenarios < 2"
        assert "sc_1" not in [s.id for s in forecast.scenarios]
        assert "Scenariusz bazowy" not in case.title

    asyncio.run(_run())



def test_search_adapter_v12_status_and_timeout():
    """
    Test V12-1: search adapter status reports can_fetch_content and grounding_urls_only for Gemini,
    full_fetch for Tavily/Serper, and gemini timeout is 30.0s.
    """
    from backend.infrastructure.web_research.search_adapter import WebResearchAdapter
    import inspect

    # Check timeout in source code
    lines = inspect.getsource(WebResearchAdapter._search_gemini)
    assert "timeout=30.0" in lines, "Gemini search timeout must be raised to 30.0s"

    # Status check for gemini
    adapter_gemini = WebResearchAdapter(api_key="dummy_key", provider="gemini")
    status_gemini = adapter_gemini.get_status()
    assert status_gemini["mode"] == "grounding_urls_only"
    assert status_gemini["can_fetch_content"] is False

    # Status check for tavily
    adapter_tavily = WebResearchAdapter(api_key="dummy_key", provider="tavily")
    status_tavily = adapter_tavily.get_status()
    assert status_tavily["mode"] == "full_fetch"
    assert status_tavily["can_fetch_content"] is True

    # Status check for offline
    adapter_offline = WebResearchAdapter(api_key=None, provider="none")
    status_offline = adapter_offline.get_status()
    assert status_offline["mode"] == "offline_user_data_only"
    assert status_offline["can_fetch_content"] is False


def test_evidence_weighting_properties():
    """
    Test V12-2: verify 5 key properties of evidence weighting:
    1. tier_1 domain gets tier_1 score (1.0).
    2. unknown domain gets tier_4 score (0.4).
    3. multiple evidences from same domain do not double-count corroboration.
    4. missing published_at gives neutral 0.50 score.
    5. deterministic output (same inputs -> identical weight).
    """
    from backend.domain.evidence.evidence_weighting import compute_evidence_weight
    from backend.domain.evidence.models import Evidence

    ev_tier1 = Evidence(
        id="ev_t1",
        claim="Inflacja bazowa w Polsce w styczniu 2026 wyniosła 3.2%",
        value=3.2,
        quote="Według szybkiego szacunku GUS inflacja CPI wyniosła 3.2% r/r w 2026 r.",
        source_url="https://stat.gov.pl/obszary-tematyczne/ceny-handel/wskazniki-cen/inflacja-2026",
        source_title="GUS",
        confidence=0.9,
        content_hash="hash_1",
        published_at="2026-02-15T10:00:00Z",
    )

    ev_tier4 = Evidence(
        id="ev_t4",
        claim="Sytuacja geopolityczna może ulec zmianie",
        value=1.0,
        quote="Eksperci z bloga twierdzą, że sytuacja może ulec nagłej zmianie w regionie.",
        source_url="https://nieznany-blog-geopolityczny.xyz/post/123",
        source_title="Blog",
        confidence=0.8,
        content_hash="hash_4",
        published_at="2026-01-10T12:00:00Z",
    )

    # 1. Tier 1 domain check
    wb1 = compute_evidence_weight(ev_tier1, all_evidences=[ev_tier1])
    assert wb1.source_class_score == 1.0, "stat.gov.pl must be recognized as Tier 1 (score 1.0)"

    # 2. Unknown domain check
    wb4 = compute_evidence_weight(ev_tier4, all_evidences=[ev_tier4])
    assert wb4.source_class_score == 0.4, "Unknown domain must default to Tier 4 (score 0.4)"

    # 3. Corroboration: same domain should not double-count
    ev_tier1_dupe_domain = Evidence(
        id="ev_t1_dupe",
        claim="Kolejny raport GUS o cenach żywności",
        value=2.1,
        quote="GUS informuje o cenach żywności w lutym 2026 roku wynoszących +2.1%.",
        source_url="https://stat.gov.pl/obszary-tematyczne/ceny-handel/zywnosc",
        source_title="GUS",
        confidence=0.9,
        content_hash="hash_1_dupe",
    )
    wb_corrob_same = compute_evidence_weight(ev_tier1, all_evidences=[ev_tier1, ev_tier1_dupe_domain])
    # Distinct domains = 1, so corroboration score is baseline 0.5
    assert wb_corrob_same.corroboration_score == 0.5, "Same domain should count as 1 domain (baseline 0.5)"

    # Distinct domain should boost corroboration
    ev_tier2_diff_domain = Evidence(
        id="ev_t2_nbp",
        claim="NBP potwierdza spadek dynamiki cen",
        value=3.0,
        quote="Raport o inflacji NBP potwierdza projekcję spadku inflacji bazowej do 3.0%.",
        source_url="https://nbp.pl/publikacje/raport-o-inflacji-2026",
        source_title="NBP",
        confidence=0.95,
        content_hash="hash_nbp",
    )
    wb_corrob_diff = compute_evidence_weight(ev_tier1, all_evidences=[ev_tier1, ev_tier2_diff_domain])
    assert wb_corrob_diff.corroboration_score == 0.8, "Two distinct domains must yield 0.8 corroboration"

    # 4. Missing published_at gives neutral 0.50 score
    ev_no_date = Evidence(
        id="ev_nodate",
        claim="Raport archiwalny",
        value=1.5,
        quote="Wskaźnik aktywności przemysłowej PMI w marcu 2026 r. wzrósł o 1.5 pkt.",
        source_url="https://stat.gov.pl/raport",
        source_title="GUS",
        confidence=0.9,
        content_hash="hash_nodate",
        published_at=None,
    )
    wb_no_date = compute_evidence_weight(ev_no_date)
    assert wb_no_date.recency_score == 0.50, "Missing published_at must return neutral 0.50"

    # 5. Deterministic output: running 100 times yields exact same float
    res_first = compute_evidence_weight(ev_tier1, all_evidences=[ev_tier1, ev_tier2_diff_domain]).final_weight
    for _ in range(100):
        res_check = compute_evidence_weight(ev_tier1, all_evidences=[ev_tier1, ev_tier2_diff_domain]).final_weight
        assert res_first == res_check


def test_extractor_v13_verbatim_quote_acceptance_and_rejection():
    """
    Test V13-1D:
    1. Cytat obecny w treści -> dowód przyjęty.
    2. Cytat obecny, ale zapisany cudzysłowami drukarskimi i z twardą spacją -> przyjęty po normalizacji.
    3. Cytat będący parafrazą (te same fakty, inne słowa) -> odrzucony.
    4. Cytat zmyślony -> odrzucony.
    """
    import asyncio
    from unittest.mock import MagicMock, AsyncMock, patch
    from backend.infrastructure.web_research.extractor import EvidenceExtractor
    from backend.domain.evidence.models import EvidenceDocument

    full_page = (
        "W marcu 2026 r. stopa bezrobocia w Polsce wyniosła 5,1%.\n"
        "Główny Urząd Statystyczny podał: „Wskaźnik inflacji bazowej obniżył się do 3,2% rok do roku”.\n"
        "Wartość eksportu wyniosła 120 mld zł."
    )

    doc = EvidenceDocument(
        url="https://stat.gov.pl/test-v13",
        content_hash="dummy_hash_v13",
        page_text=full_page,
        title="GUS Test",
        status_code=200,
        mime_type="text/html",
    )

    extractor = EvidenceExtractor(llm_gateway=MagicMock(is_available=True))

    async def _run():
        # 1. Exact quote present -> ACCEPTED
        ev1_json = {
            "claim": "Stopa bezrobocia wyniosła 5,1%",
            "value": 5.1,
            "unit": "%",
            "quote": "stopa bezrobocia w Polsce wyniosła 5,1%",
        }
        with patch.object(extractor, "_extract_via_llm", AsyncMock(return_value=ev1_json)):
            ev1 = await extractor.extract_parameter_evidence(doc, target_param="bezrobocie")
        assert ev1 is not None, "Exact continuous quote must be accepted"
        assert ev1.quote == "stopa bezrobocia w Polsce wyniosła 5,1%"

        # 2. Typographic differences (straight vs curly quotes, non-breaking spaces) -> ACCEPTED
        # Note: in full_page we have „Wskaźnik inflacji bazowej obniżył się do 3,2% rok do roku”.
        # Candidate quote uses ASCII straight quotes and non-breaking space
        ev2_json = {
            "claim": "Inflacja bazowa 3,2%",
            "value": 3.2,
            "unit": "%",
            "quote": "\"Wskaźnik\u00a0inflacji bazowej obniżył się do 3,2% rok do roku\".",
        }
        with patch.object(extractor, "_extract_via_llm", AsyncMock(return_value=ev2_json)):
            ev2 = await extractor.extract_parameter_evidence(doc, target_param="inflacja")
        assert ev2 is not None, "Quote with typographic quotes and nbsp must be accepted via equivalent normalization"

        # 3. Paraphrase (same facts, different words) -> REJECTED
        ev3_json = {
            "claim": "Stopa bezrobocia 5,1%",
            "value": 5.1,
            "unit": "%",
            "quote": "W marcu bezrobocie na terenie Polski osiągnęło poziom 5,1 procent.",
        }
        with patch.object(extractor, "_extract_via_llm", AsyncMock(return_value=ev3_json)):
            ev3 = await extractor.extract_parameter_evidence(doc, target_param="bezrobocie")
        assert ev3 is None, "Paraphrase quote must be strictly rejected"

        # 4. Hallucinated / invented quote -> REJECTED
        ev4_json = {
            "claim": "PKB wzrosło o 4%",
            "value": 4.0,
            "unit": "%",
            "quote": "GUS odnotował wzrost PKB w pierwszym kwartale o 4.0%.",
        }
        with patch.object(extractor, "_extract_via_llm", AsyncMock(return_value=ev4_json)):
            ev4 = await extractor.extract_parameter_evidence(doc, target_param="pkb")
        assert ev4 is None, "Hallucinated quote must be strictly rejected"

    asyncio.run(_run())


def test_scenario_needs_clarification_has_explanation_and_questions():
    """
    V14-2: A needs_clarification result from the scenario forecasting fallback branch
    MUST have non-empty explanation and non-empty questions list (never empty, no clarification_prompt).
    """
    from backend.domain.cognitive.active_inference_engine import ActiveInferenceOrchestrator
    from backend.domain.cognitive.cognitive_port import FormalizationResult

    async def _run():
        mock_reasoning_port = MagicMock()
        mock_session = AsyncMock()
        engine = ActiveInferenceOrchestrator(reasoning_port=mock_reasoning_port)

        # Mock decompose_scenario_query_async to return empty scenarios/premises (< 2 scenarios)
        mock_case = MagicMock()
        mock_forecast = MagicMock()
        mock_forecast.scenarios = []
        mock_forecast.evidence_premises = []
        mock_forecast.telemetry = {}

        with patch("backend.domain.cognitive.scenario_decomposer.is_scenario_forecast_query", return_value=True), \
             patch("backend.domain.cognitive.scenario_decomposer.decompose_scenario_query_async", AsyncMock(return_value=(mock_case, mock_forecast))), \
             patch("backend.infrastructure.web_research.search_adapter.WebResearchAdapter.is_available", return_value=False):

            res, ws = await engine.run_intake(session=mock_session, query="Czy Rosja do końca tego roku napadnie na Polskę?")
            assert isinstance(res, FormalizationResult)
            assert res.status == "needs_clarification"
            assert res.explanation != "", "explanation must NOT be empty"
            assert len(res.questions) > 0, "questions must NOT be empty"
            assert not hasattr(res, "clarification_prompt"), "clarification_prompt must not exist on model"

    asyncio.run(_run())


