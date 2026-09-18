"""
YourQuantum — Evidence Domain Models (Phase C2)
Represents verifiable real-world web and document evidence with SHA-256 content hashes,
verbatim quotes, and conflict tracking.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ExtractionMethod(str, Enum):
    LLM_EXTRACTED = "llm_extracted"
    API_FIELD = "api_field"
    TABLE_CELL = "table_cell"
    USER_VERIFIED = "user_verified"
    SENTENCE_SELECTION = "sentence_selection"


class Evidence(BaseModel):
    """
    A single piece of empirical evidence supporting a parameter, variable, or claim.
    Honesty requirement: 'quote' must literally exist in the fetched document.
    """
    id: str
    claim: str
    value: float | str | None = None
    unit: str | None = None
    source_url: str
    source_title: str
    publisher: str | None = None
    published_at: datetime | str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str  # SHA-256 of downloaded document
    quote: str  # <= 300 chars, verbatim quote from source
    extraction_method: ExtractionMethod = ExtractionMethod.LLM_EXTRACTED
    confidence: float = 1.0  # 0.0 to 1.0
    conflicts_with: list[str] = Field(default_factory=list)
    target_param: str | None = None  # e.g., "option_a.cost" or "v_1"
    char_start: int | None = None
    char_end: int | None = None
    impact_on_scenarios: dict[str, float] = Field(default_factory=dict)
    impact_justification: dict[str, Any] = Field(default_factory=dict)


class EvidenceConflict(BaseModel):
    """
    Represents conflicting evidence across multiple sources for the same parameter.
    Never resolved silently; exposed to user or resolved via median with stress-testing.
    """
    id: str
    target_param: str
    evidence_ids: list[str]
    divergent_values: list[float | str]
    spread_min: float | None = None
    spread_max: float | None = None
    resolution_method: str = "unresolved"  # "unresolved" | "median" | "user_selected"
    resolved_value: float | str | None = None
    notes: str = ""


class ResearchQuery(BaseModel):
    """
    A privacy-preserving query generated for a missing parameter.
    Never contains raw user dilemma text.
    """
    id: str
    target_param: str
    query_text: str
    expected_unit: str | None = None
    rationale: str = ""


class WebSearchResult(BaseModel):
    """
    A single search result item returned by search adapters.
    """
    title: str
    url: str
    snippet: str
    snippet_origin: str = "web"  # "web" | "llm"
    publisher: str | None = None
    published_date: str | None = None
    score: float | None = None


class EvidenceDocument(BaseModel):
    """
    Cached, sanitized document fetched from the web.
    """
    url: str
    content_hash: str
    page_text: str
    title: str = ""
    publisher: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_code: int = 200
    mime_type: str = "text/html"
