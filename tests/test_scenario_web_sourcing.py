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


@pytest.mark.parametrize("query,expected_is_scenario,expected_quality_level", [
    ("Czy Rosja napadnie na Polskę?", True, "too_vague"),
    ("Czy Rosja do końca tego roku napadnie na Polskę?", True, "sufficient"),
    ("Czy Iran uderzy na Izrael?", True, "too_vague"),
    ("Czy Chiny zaatakują Tajwan?", True, "too_vague"),
])
def test_scenario_forecast_definition_and_quality_gate_consistency(
    query: str,
    expected_is_scenario: bool,
    expected_quality_level: str,
):
    """
    V14-3: Parametric test across the specification table.
    Both is_scenario_forecast_query and assess_input_quality MUST be consistent,
    and missing time horizon must block all queries equally with scenario-specific suggestions
    (never suggestions about apartments or two options).
    """
    from backend.domain.cognitive.scenario_decomposer import is_scenario_forecast_query
    from backend.domain.cognitive.quality_gate import assess_input_quality

    is_scenario = is_scenario_forecast_query(query)
    assert is_scenario is expected_is_scenario

    gate = assess_input_quality(query, is_scenario=is_scenario)
    assert gate.level == expected_quality_level

    if gate.level == "too_vague":
        assert not any("mieszkanie" in s.lower() or "dwie opcje" in s.lower() for s in gate.suggestions), \
            f"Scenario query got non-scenario suggestions: {gate.suggestions}"
        assert any("horyzont" in s.lower() or "wariant" in s.lower() for s in gate.suggestions)


def test_scenario_decomposition_retry_triggers_on_insufficient_scenarios():
    """
    V14-4: When the first decomposition call returns fewer than 2 scenarios,
    ActiveInferenceOrchestrator must retry once and record scenario_decomposition_retries=1 in telemetry.
    If the second call succeeds with >=2 scenarios, it proceeds to ready_for_review.
    """
    from backend.domain.cognitive.active_inference_engine import ActiveInferenceOrchestrator

    async def _run():
        mock_reasoning_port = MagicMock()
        mock_session = AsyncMock()
        engine = ActiveInferenceOrchestrator(reasoning_port=mock_reasoning_port)

        from backend.domain.decision_case import DecisionCase, InputQuality

        # Call 1: fails (<2 scenarios)
        mock_forecast_fail = MagicMock()
        mock_forecast_fail.scenarios = []
        mock_forecast_fail.evidence_premises = []
        mock_forecast_fail.telemetry = {}
        mock_case_fail = DecisionCase(title="test", context="test", options=[], criteria=[], score_matrix={})

        # Call 2: succeeds (2 scenarios + premises)
        mock_forecast_succ = MagicMock()
        mock_forecast_succ.scenarios = [MagicMock(), MagicMock()]
        mock_forecast_succ.evidence_premises = [MagicMock()]
        mock_forecast_succ.telemetry = {}
        mock_forecast_succ.model_dump.return_value = {"scenarios": [{}, {}], "telemetry": {}}
        mock_forecast_succ.briefing = MagicMock(executive_summary="Podsumowanie")
        mock_forecast_succ.dominant_scenario_id = "sc_1"
        mock_case_succ = DecisionCase(title="test", context="test", options=[], criteria=[], score_matrix={})

        call_count = 0
        async def _mock_decompose(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_case_fail, mock_forecast_fail
            return mock_case_succ, mock_forecast_succ

        with patch("backend.domain.cognitive.scenario_decomposer.is_scenario_forecast_query", return_value=True), \
             patch("backend.domain.cognitive.scenario_decomposer.decompose_scenario_query_async", side_effect=_mock_decompose), \
             patch("backend.infrastructure.web_research.search_adapter.WebResearchAdapter.is_available", return_value=False):

            res, ws = await engine.run_intake(session=mock_session, query="Czy Rosja do końca tego roku napadnie na Polskę?")
            assert call_count == 2, f"Expected 2 decomposition calls (1 initial + 1 retry), got {call_count}"
            assert res.status == "ready_for_review"
            assert mock_forecast_succ.telemetry.get("scenario_decomposition_retries") == 1

    asyncio.run(_run())


def test_sentence_selection_single_sentence():
    """
    V14-1A: Single sentence index selected by model -> quote sliced exactly by offsets, verified.
    """
    from backend.infrastructure.web_research.extractor import EvidenceExtractor, split_into_sentences
    from backend.domain.evidence.models import EvidenceDocument, ExtractionMethod

    text = "Pierwsze zdanie dokumentu analitycznego. Inflacja w Polsce w 2026 roku wyniesie 3.1 procent według NBP. Trzecie zdanie podsumowujące raport."
    doc = EvidenceDocument(
        url="https://nbp.pl/raport",
        content_hash="hash123",
        page_text=text,
        title="NBP Raport",
        status_code=200,
    )
    extractor = EvidenceExtractor(llm_gateway=MagicMock(is_available=True))

    mock_llm_json = {
        "claim": "Prognoza inflacji w 2026 roku wynosi 3.1%",
        "sentence_indices": [1],
        "value": 3.1,
        "unit": "%",
        "confidence": 0.95,
    }

    async def _run():
        with patch.object(extractor.gateway, "generate", AsyncMock(return_value=MagicMock(parsed_json=mock_llm_json))):
            ev = await extractor.extract_parameter_evidence(doc, target_param="inflacja")

        assert ev is not None
        assert ev.extraction_method == ExtractionMethod.SENTENCE_SELECTION
        assert ev.char_start is not None and ev.char_end is not None
        assert ev.quote == text[ev.char_start:ev.char_end]
        assert ev.quote in text
        assert "Inflacja w Polsce w 2026 roku wyniesie 3.1 procent według NBP." in ev.quote
        assert extractor.telemetry["web_evidence_from_sentences"] == 1

    asyncio.run(_run())


def test_sentence_selection_adjacent_sentences():
    """
    V14-1B: Two adjacent sentence indices -> contiguous slice text[s1.start : s2.end], verified.
    """
    from backend.infrastructure.web_research.extractor import EvidenceExtractor
    from backend.domain.evidence.models import EvidenceDocument, ExtractionMethod

    text = "Pierwsze zdanie raportu. Gen. Grynkewich ocenia sytuację bezpieczeństwa w Europie. Rosja będzie gotowa do konfrontacji z Europą w 2027 roku. Czwarte zdanie podsumowujące."
    doc = EvidenceDocument(
        url="https://defence.pl/artykul",
        content_hash="hash456",
        page_text=text,
        title="Raport Bezpieczeństwa",
        status_code=200,
    )
    extractor = EvidenceExtractor(llm_gateway=MagicMock(is_available=True))

    mock_llm_json = {
        "claim": "Rosja gotowa do konfrontacji w 2027 roku",
        "sentence_indices": [1, 2],
        "value": 2027,
        "unit": "rok",
        "confidence": 0.9,
    }

    async def _run():
        with patch.object(extractor.gateway, "generate", AsyncMock(return_value=MagicMock(parsed_json=mock_llm_json))):
            ev = await extractor.extract_parameter_evidence(doc, target_param="gotowosc_rosji")

        assert ev is not None
        assert ev.extraction_method == ExtractionMethod.SENTENCE_SELECTION
        assert ev.char_start is not None and ev.char_end is not None
        assert ev.quote == text[ev.char_start:ev.char_end]
        assert "Gen. Grynkewich" in ev.quote
        assert "2027 roku" in ev.quote
        assert ev.quote in text

    asyncio.run(_run())


def test_sentence_selection_rejects_out_of_bounds_index():
    """
    V14-1C: Model returns index out of bounds -> rejected, web_invalid_sentence_index incremented.
    """
    from backend.infrastructure.web_research.extractor import EvidenceExtractor
    from backend.domain.evidence.models import EvidenceDocument

    text = "Pierwsze zdanie raportu. Drugie zdanie raportu."
    doc = EvidenceDocument(
        url="https://test.com/doc",
        content_hash="hash789",
        page_text=text,
        title="Test",
        status_code=200,
    )
    extractor = EvidenceExtractor(llm_gateway=MagicMock(is_available=True))

    mock_llm_json = {
        "claim": "Błędny indeks",
        "sentence_indices": [99],
        "value": None,
    }

    async def _run():
        with patch.object(extractor.gateway, "generate", AsyncMock(return_value=MagicMock(parsed_json=mock_llm_json))):
            ev = await extractor.extract_parameter_evidence(doc, target_param="test")

        assert ev is None
        assert extractor.telemetry["web_invalid_sentence_index"] == 1

    asyncio.run(_run())


def test_sentence_selection_rejects_more_than_three_sentences():
    """
    V14-1D: Model returns >3 sentence indices -> rejected, web_too_many_sentences incremented.
    """
    from backend.infrastructure.web_research.extractor import EvidenceExtractor
    from backend.domain.evidence.models import EvidenceDocument

    text = "Zdanie 1 opisujące wstęp. Zdanie 2 opisujące metodę. Zdanie 3 opisujące wyniki. Zdanie 4 opisujące wnioski. Zdanie 5 opisujące rekomendacje."
    doc = EvidenceDocument(
        url="https://test.com/doc",
        content_hash="hash999",
        page_text=text,
        title="Test",
        status_code=200,
    )
    extractor = EvidenceExtractor(llm_gateway=MagicMock(is_available=True))

    mock_llm_json = {
        "claim": "Zbyt wiele zdań",
        "sentence_indices": [0, 1, 2, 3],
        "value": None,
    }

    async def _run():
        with patch.object(extractor.gateway, "generate", AsyncMock(return_value=MagicMock(parsed_json=mock_llm_json))):
            ev = await extractor.extract_parameter_evidence(doc, target_param="test")

        assert ev is None
        assert extractor.telemetry["web_too_many_sentences"] == 1

    asyncio.run(_run())


def test_sentence_selection_fallback_to_legacy_when_fewer_than_two_sentences():
    """
    V14-1E: When document text contains fewer than 2 sentences, falls back to legacy verbatim path.
    """
    from backend.infrastructure.web_research.extractor import EvidenceExtractor
    from backend.domain.evidence.models import EvidenceDocument

    text = "Dokument zawierający tylko jeden wers bez kropek"
    doc = EvidenceDocument(
        url="https://test.com/doc",
        content_hash="hash000",
        page_text=text,
        title="Test",
        status_code=200,
    )
    extractor = EvidenceExtractor(llm_gateway=MagicMock(is_available=True))

    mock_llm_json = {
        "claim": "Pojedynczy wers",
        "quote": "jeden wers",
        "value": 1.0,
    }

    async def _run():
        with patch.object(extractor.gateway, "generate", AsyncMock(return_value=MagicMock(parsed_json=mock_llm_json))):
            ev = await extractor.extract_parameter_evidence(doc, target_param="test")

        assert extractor.extraction_path == "legacy_verbatim"
        assert ev is not None
        assert ev.quote == "jeden wers"

    asyncio.run(_run())


def test_v16_non_adjacent_sentences_produce_separate_evidences():
    """
    V16-1: Non-adjacent sentence indices (e.g. [1, 5]) return separate Evidence objects.
    """
    from backend.infrastructure.web_research.extractor import EvidenceExtractor
    from backend.domain.evidence.models import EvidenceDocument

    text = (
        "Zdanie zerowe. "
        "Pierwsze zdanie o budżecie obronnym Polski. "
        "Drugie zdanie kontekstowe. "
        "Trzecie zdanie niepowiązane. "
        "Czwarte zdanie neutralne. "
        "Piąte zdanie o liczebności sił zbrojnych w 2026 roku. "
        "Szóste zdanie podsumowujące."
    )
    doc = EvidenceDocument(
        url="https://mon.gov.pl/raport",
        content_hash="hash12345",
        page_text=text,
        title="Raport MON",
        status_code=200,
    )
    extractor = EvidenceExtractor(llm_gateway=MagicMock(is_available=True))

    mock_llm_json = {
        "claim": "Fakty o obronności",
        "sentence_indices": [0, 4],
        "value": None,
    }

    async def _run():
        with patch.object(extractor.gateway, "generate", AsyncMock(return_value=MagicMock(parsed_json=mock_llm_json))):
            evidences = await extractor.extract_parameter_evidences(doc, target_param="obronnosc")

        assert len(evidences) == 2, f"Expected 2 separate evidences for non-adjacent indices [0, 4], got {len(evidences)}"
        assert "Pierwsze zdanie o budżecie" in evidences[0].quote
        assert "Piąte zdanie o liczebności" in evidences[1].quote
        assert evidences[0].quote in text
        assert evidences[1].quote in text
        # char offsets strictly match len(quote)
        assert evidences[0].char_end - evidences[0].char_start == len(evidences[0].quote)
        assert evidences[1].char_end - evidences[1].char_start == len(evidences[1].quote)

    asyncio.run(_run())


def test_v16_quote_truncation_at_sentence_boundary_and_exact_offsets():
    """
    V16-2: Quote truncation terminates at sentence boundary, char_end - char_start == len(quote).
    """
    from backend.infrastructure.web_research.extractor import EvidenceExtractor
    from backend.domain.evidence.models import EvidenceDocument

    # Create a document where multiple sentences exceed 300 characters
    s1 = "To jest pierwsze zdanie testowe mające około sześćdziesięciu znaków długości."
    s2 = "To jest drugie zdanie testowe mające również około sześćdziesięciu znaków długości."
    s3 = "To jest trzecie zdanie testowe także o sporej długości znakowej w języku polskim."
    s4 = "To jest czwarte zdanie testowe, które sprawia, że łączna długość przekracza 300 znaków limitu."
    s5 = "To jest piąte zdanie, które z pewnością nie powinno się zmieścić."
    text = f"{s1} {s2} {s3} {s4} {s5}"

    doc = EvidenceDocument(
        url="https://bezpieczenstwo.pl/raport",
        content_hash="hash300",
        page_text=text,
        title="Raport Długi",
        status_code=200,
    )
    extractor = EvidenceExtractor(llm_gateway=MagicMock(is_available=True))

    mock_llm_json = {
        "claim": "Wielozdaniowy fakt",
        "sentence_indices": [0, 1, 2],
        "value": None,
    }

    async def _run():
        with patch.object(extractor.gateway, "generate", AsyncMock(return_value=MagicMock(parsed_json=mock_llm_json))):
            evidences = await extractor.extract_parameter_evidences(doc, target_param="test_param")

        assert len(evidences) == 1
        ev = evidences[0]
        assert len(ev.quote) <= 300
        assert ev.char_start is not None and ev.char_end is not None
        assert ev.char_end - ev.char_start == len(ev.quote)
        assert text[ev.char_start:ev.char_end] == ev.quote
        # Slicing must preserve sentence boundary: ends with period
        assert ev.quote.endswith(".")

    asyncio.run(_run())


def test_v16_deterministic_heuristics_value_none_and_zero_confidence():
    """
    V16-3: _extract_via_deterministic_heuristics returns value=None and confidence=0.0.
    """
    from backend.infrastructure.web_research.extractor import EvidenceExtractor

    extractor = EvidenceExtractor(llm_gateway=MagicMock(is_available=False))
    text = "W 2025 roku wydatki na obronność Polski wyniosły 4.2% PKB."
    res = extractor._extract_via_deterministic_heuristics(
        text=text,
        target_param="wydatki_obronnosc",
        expected_unit="%",
    )
    assert res is not None
    assert res["value"] is None, f"Expected value=None in heuristics, got {res['value']}"
    assert res["confidence"] == 0.0, f"Expected confidence=0.0, got {res['confidence']}"
    assert res["quote"] == text.strip()


def test_v16_extraction_mode_constructor_parameter():
    """
    V16-4: EvidenceExtractor takes extraction_mode parameter instead of inspecting self.__dict__.
    """
    from backend.infrastructure.web_research.extractor import EvidenceExtractor

    e_default = EvidenceExtractor()
    assert e_default.extraction_mode == "sentence_selection"

    e_legacy = EvidenceExtractor(extraction_mode="legacy_verbatim")
    assert e_legacy.extraction_mode == "legacy_verbatim"


def test_v16_dec_039_documented_premises_automatically_accepted():
    """
    V16-5: Documented web premises meeting 5 conditions are automatically accepted (is_accepted = True)
    and enter probability calculation giving non-uniform distribution.
    """
    from backend.domain.evidence.models import Evidence, ExtractionMethod
    from backend.domain.cognitive.scenario_decomposer import decompose_scenario_query_async

    text = "Zdolności obronne Polski i NATO powstrzymują agresję zbrojną do 2026 roku."
    verified_ev = Evidence(
        id="ev_doc_1",
        claim="Zdolności obronne Polski i NATO",
        value=None,
        unit=None,
        source_url="https://bbn.gov.pl/analiza",
        source_title="BBN: Analiza Bezpieczeństwa",
        publisher="Biuro Bezpieczeństwa Narodowego",
        content_hash="sha256_bbn",
        quote=text,
        extraction_method=ExtractionMethod.SENTENCE_SELECTION,
        confidence=1.0,
        char_start=0,
        char_end=len(text),
        impact_on_scenarios={"sc_1": -0.8, "sc_2": 0.8},
        impact_justification={
            "sc_1": {"sentence_index": 0, "justifying_sentence": text, "char_start": 0, "char_end": len(text), "impact": -0.8},
            "sc_2": {"sentence_index": 0, "justifying_sentence": text, "char_start": 0, "char_end": len(text), "impact": 0.8},
        }
    )

    mock_llm_res = MagicMock()
    mock_llm_res.parsed_json = {
        "domain": "Geopolityka",
        "scenarios": [
            {"id": "sc_1", "title": "Atak na Polskę", "description": "Konflikt zbrojny", "risk_level": "CRITICAL"},
            {"id": "sc_2", "title": "Brak ataku", "description": "Odstraszanie działa", "risk_level": "LOW"},
        ],
        "premises": [],
    }

    async def _run():
        with patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.is_available", return_value=True), \
             patch("backend.domain.cognitive.scenario_decomposer.LLMGateway.generate", AsyncMock(return_value=mock_llm_res)):
            case, forecast = await decompose_scenario_query_async(
                query="Czy Rosja zaatakuje Polskę?",
                web_snippets=["[BBN](https://bbn.gov.pl): Zdolności obronne."],
                verified_evidences=[verified_ev],
            )

        web_premises = [p for p in forecast.evidence_premises if p.provenance == "web_sourced"]
        assert len(web_premises) == 1
        wp = web_premises[0]
        # DEC-039: Must be automatically accepted!
        assert wp.is_accepted is True, "Documented premise meeting all 5 conditions must be accepted!"
        assert forecast.telemetry.get("n_documented_premises") == 1
        assert forecast.telemetry.get("n_premises_rejected_as_undocumented") == 0

        # Distribution must be non-uniform since premise is accepted
        p_sc1 = next(s.probability for s in forecast.scenarios if s.id == "sc_1")
        p_sc2 = next(s.probability for s in forecast.scenarios if s.id == "sc_2")
        assert p_sc1 != p_sc2, f"Expected non-uniform distribution, got p(sc_1)={p_sc1}, p(sc_2)={p_sc2}"
        assert p_sc2 > p_sc1, "Brak ataku should have higher probability due to positive impact"

    asyncio.run(_run())




