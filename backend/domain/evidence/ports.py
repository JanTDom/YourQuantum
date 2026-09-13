"""
YourQuantum — Evidence Source Port (Phase C1)
Hexagonal port definition for external web research and document ingestion.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.domain.evidence.models import EvidenceDocument, WebSearchResult


@runtime_checkable
class EvidenceSourcePort(Protocol):
    """
    Contract for web searching and document fetching adapters.
    Domain code relies exclusively on this interface, not concrete network drivers.
    """

    async def search(
        self,
        query: str,
        max_results: int = 3,
    ) -> list[WebSearchResult]:
        """
        Execute an external web search query.
        Must respect privacy and never send user identifying prompts.
        """
        ...

    async def fetch_document(
        self,
        url: str,
    ) -> EvidenceDocument | None:
        """
        Fetch, sanitize, and return a document with its SHA-256 content hash.
        Must enforce strict SSRF guards, size limits, and timeout protection.
        """
        ...

    def is_available(self) -> bool:
        """
        Check if external search capabilities are configured and within budget limits.
        """
        ...

    def get_status(self) -> dict[str, str | int | bool]:
        """
        Return status telemetry (provider, remaining budget, query count).
        """
        ...
