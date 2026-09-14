"""
YourQuantum — Cognitive Reasoning Port
Defines contract-first interfaces and domain models for cognitive reasoning,
ensuring clean hexagonal separation between pure domain logic and external LLM adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal
from pydantic import BaseModel, Field

from backend.domain.problem_ir import ProblemIR


from backend.domain.decision_case import DecisionCase, InputQuality


class FormalizationResult(BaseModel):
    """
    Standardized result of cognitive problem formalization.
    Validated boundary model consumable by frontends, workers, and active inference loops.
    """
    status: Literal["ready_for_review", "needs_clarification", "not_computable"] = "ready_for_review"
    problem_ir: ProblemIR | None = None
    decision_case: DecisionCase | None = None
    problem_class: str = "CHOICE"
    input_quality: InputQuality | None = None
    not_computable_report: dict[str, Any] | None = None
    research_queries: list[dict[str, Any]] = Field(default_factory=list)
    break_even_point: str | None = None
    questions: list[str] = Field(default_factory=list)
    explanation: str = ""
    raw_query: str = ""
    fingerprint: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    penalty_multipliers: dict[str, float] = Field(default_factory=dict)
    session_id: str | None = None
    formalized: dict[str, Any] | None = None
    design_problem: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)



class CognitiveReasoningPort(ABC):
    """
    Hexagonal Port for cognitive reasoning engines (Gemini API, rule heuristics, local neural models).
    """

    @abstractmethod
    async def formalize_query(
        self,
        query: str,
        analogies: list[dict[str, Any]] | None = None,
        error_context: list[str] | None = None,
    ) -> FormalizationResult:
        """
        Formalize natural language query into a structured ProblemIR or set of clarifying questions.

        Args:
            query: Raw user input dilemma or requirements.
            analogies: Historical exemplar traces recalled from episodic memory.
            error_context: Prediction error signals from verifier if in a reflection loop.

        Returns:
            FormalizationResult: Validated Pydantic model containing ProblemIR or clarification request.
        """
        pass
