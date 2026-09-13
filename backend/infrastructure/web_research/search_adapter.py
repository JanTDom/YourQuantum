"""
YourQuantum — Web Search Adapter (Phase C1)
Hexagonal adapter implementing EvidenceSourcePort with multi-engine support,
strict rate budgeting, and deterministic offline fallback.
"""
from __future__ import annotations

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
    Supports Tavily, Serper, or generic JSON search APIs, with automatic offline mode
    and SafeWebFetcher SSRF mitigation.
    """

    def __init__(
        self,
        api_key: str | None = None,
        provider: str | None = None,
        fetcher: SafeWebFetcher | None = None,
        max_session_queries: int = 15,
        mock_fixtures: dict[str, list[dict[str, str]]] | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("SEARCH_API_KEY") or os.getenv("TAVILY_API_KEY") or os.getenv("SERPER_API_KEY")
        self.provider = provider or ("tavily" if os.getenv("TAVILY_API_KEY") else "serper" if os.getenv("SERPER_API_KEY") else "generic")
        self.fetcher = fetcher or SafeWebFetcher()
        self.max_session_queries = max_session_queries
        self.queries_performed = 0
        self.mock_fixtures = mock_fixtures or {}

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
        if self.provider == "tavily":
            return await self._search_tavily(query, max_results)
        elif self.provider == "serper":
            return await self._search_serper(query, max_results)
        else:
            return await self._search_generic(query, max_results)

    async def fetch_document(self, url: str) -> EvidenceDocument | None:
        """Safely fetch and sanitize a document via SafeWebFetcher."""
        return await self.fetcher.fetch(url)

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
