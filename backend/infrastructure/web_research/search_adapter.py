"""
YourQuantum — Web Search Adapter (Phase C1)
Hexagonal adapter implementing EvidenceSourcePort with multi-engine support,
strict rate budgeting, and deterministic offline fallback.
"""
from __future__ import annotations

import hashlib
import os
import logging
import httpx

from backend.domain.evidence.models import EvidenceDocument, WebSearchResult
from backend.domain.evidence.ports import EvidenceSourcePort
from backend.infrastructure.web_research.fetcher import SafeWebFetcher

logger = logging.getLogger(__name__)


class WebResearchAdapter(EvidenceSourcePort):
    """
    Production adapter implementing EvidenceSourcePort.
    Supports Gemini (native Google Search Grounding), Tavily, Serper, or generic APIs,
    with automatic offline mode and SafeWebFetcher SSRF mitigation.
    """

    def __init__(
        self,
        api_key: str | None = None,
        provider: str | None = None,
        fetcher: SafeWebFetcher | None = None,
        max_session_queries: int = 15,
        mock_fixtures: dict[str, list[dict[str, str]]] | None = None,
    ) -> None:
        self.api_key = (
            api_key
            or os.getenv("SEARCH_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("TAVILY_API_KEY")
            or os.getenv("SERPER_API_KEY")
        )
        self.provider = provider or (
            "gemini"
            if os.getenv("GEMINI_API_KEY")
            else "tavily"
            if os.getenv("TAVILY_API_KEY")
            else "serper"
            if os.getenv("SERPER_API_KEY")
            else "generic"
        )
        self.fetcher = fetcher or SafeWebFetcher()
        self.max_session_queries = max_session_queries
        self.queries_performed = 0
        self.mock_fixtures = mock_fixtures or {}
        self._cached_documents: dict[str, EvidenceDocument] = {}

    def is_available(self) -> bool:
        """True if either mock fixtures are supplied or a live API key is set within quota."""
        if bool(self.mock_fixtures):
            return True
        return bool(self.api_key) and self.queries_performed < self.max_session_queries

    def get_status(self) -> dict[str, str | int | bool]:
        return {
            "provider": self.provider if self.api_key else "offline_user_data_only",
            "is_available": self.is_available(),
            "queries_performed": self.queries_performed,
            "max_session_queries": self.max_session_queries,
            "has_mock_fixtures": bool(self.mock_fixtures),
        }

    async def search(self, query: str, max_results: int = 3) -> list[WebSearchResult]:
        # 1. Check for mock fixtures (used in testing and deterministic replay)
        normalized_q = query.strip().lower()
        for mock_key, mock_items in self.mock_fixtures.items():
            if mock_key.lower() in normalized_q or normalized_q in mock_key.lower():
                return [WebSearchResult(**item) for item in mock_items[:max_results]]

        if not self.is_available():
            logger.info("Search unavailable (queries_performed=%d, key_present=%s).", self.queries_performed, bool(self.api_key))
            return []

        self.queries_performed += 1

        # 2. Execute via configured search provider
        if self.provider == "gemini":
            return await self._search_gemini(query, max_results)
        elif self.provider == "tavily":
            return await self._search_tavily(query, max_results)
        elif self.provider == "serper":
            return await self._search_serper(query, max_results)
        else:
            return await self._search_generic(query, max_results)

    async def fetch_document(self, url: str) -> EvidenceDocument | None:
        """Safely fetch and sanitize a document via SafeWebFetcher, with cached grounding fallback."""
        if url in self._cached_documents:
            return self._cached_documents[url]
        doc = await self.fetcher.fetch(url)
        if doc:
            return doc
        return self._cached_documents.get(url)

    async def _search_gemini(self, query: str, max_results: int) -> list[WebSearchResult]:
        """Search using Google Gemini Search Grounding."""
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"Wyszukaj w sieci rzetelne i aktualne informacje na temat: {query}. "
                                "Podaj konkretne liczby, fakty i wskaż źródła."
                            )
                        }
                    ],
                }
            ],
            "tools": [{"google_search": {}}],
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    logger.warning("Gemini Search Grounding returned status %d: %s", res.status_code, res.text[:200])
                    return []
                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return []
                cand = candidates[0]
                text = cand.get("content", {}).get("parts", [{}])[0].get("text", "")
                grounding = cand.get("groundingMetadata", {})
                chunks = grounding.get("groundingChunks", [])
                results: list[WebSearchResult] = []
                for c in chunks[:max_results]:
                    w = c.get("web", {})
                    title = w.get("title") or "Google Grounded Source"
                    source_url = w.get("uri") or "https://google.com"
                    snippet = text[:300] if text else title
                    res_item = WebSearchResult(
                        title=title,
                        url=source_url,
                        snippet=snippet,
                        score=0.95,
                    )
                    results.append(res_item)

                    doc_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    self._cached_documents[source_url] = EvidenceDocument(
                        url=source_url,
                        title=title,
                        publisher=title,
                        content_hash=doc_hash,
                        page_text=text,
                    )

                if not results and text:
                    gen_url = "https://google.com/search"
                    results.append(
                        WebSearchResult(
                            title=f"Google Grounding: {query[:50]}",
                            url=gen_url,
                            snippet=text[:300],
                            score=0.90,
                        )
                    )
                    doc_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    self._cached_documents[gen_url] = EvidenceDocument(
                        url=gen_url,
                        title=f"Google Grounding: {query[:50]}",
                        publisher="Google Search",
                        content_hash=doc_hash,
                        page_text=text,
                    )
                return results
        except Exception as e:
            logger.warning("Gemini search exception for query '%s': %s", query, e)
            return []

    async def _search_tavily(self, query: str, max_results: int) -> list[WebSearchResult]:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_raw_content": False,
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    logger.warning("Tavily search failed with status %d", res.status_code)
                    return []
                data = res.json()
                results: list[WebSearchResult] = []
                for item in data.get("results", []):
                    results.append(
                        WebSearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("content", ""),
                            score=item.get("score"),
                        )
                    )
                return results
        except Exception as e:
            logger.warning("Tavily search exception for query '%s': %s", query, e)
            return []

    async def _search_serper(self, query: str, max_results: int) -> list[WebSearchResult]:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": self.api_key or "", "Content-Type": "application/json"}
        payload = {"q": query, "num": max_results}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    logger.warning("Serper search failed with status %d", res.status_code)
                    return []
                data = res.json()
                results: list[WebSearchResult] = []
                for item in data.get("organic", []):
                    results.append(
                        WebSearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                        )
                    )
                return results
        except Exception as e:
            logger.warning("Serper search exception for query '%s': %s", query, e)
            return []

    async def _search_generic(self, query: str, max_results: int) -> list[WebSearchResult]:
        """Generic fallback when no provider-specific API is configured."""
        logger.info("Generic search invoked for query '%s', no live provider configured.", query)
        return []
