"""
YourQuantum — Human Decision Case Model
Represents the human-centric dilemma, explicit facts, realistic options,
evaluation criteria, unknowns/clarification questions, and trade-offs
BEFORE or IN PARALLEL with mathematical compilation into ProblemIR.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field


class Fact(BaseModel):
    """An explicit fact or constraint extracted directly from user text."""
    id: str = Field(default_factory=lambda: f"fact_{uuid.uuid4().hex[:8]}")
    label: str
    value: Any
    unit: str | None = None
    source_text: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Option(BaseModel):
    """A realistic choice or pathway available to the decision maker."""
    id: str = Field(default_factory=lambda: f"opt_{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    attributes: dict[str, float | str | int | bool] = Field(default_factory=dict)


class Criterion(BaseModel):
    """Evaluation criterion or preference for comparing options."""
    id: str = Field(default_factory=lambda: f"crit_{uuid.uuid4().hex[:8]}")
    name: str
    direction: Literal["maximize", "minimize"] = "maximize"
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    unit: str | None = None
    is_mandatory: bool = False
    threshold: float | None = None


class Unknown(BaseModel):
    """Missing piece of information or ambiguity that requires clarification."""
    id: str = Field(default_factory=lambda: f"unk_{uuid.uuid4().hex[:8]}")
    question: str
    impact_description: str
    default_assumption: str | None = None
    answer: str | None = None
    is_resolved: bool = False


class Tradeoff(BaseModel):
    """Explicit compromise between two options."""
    option_a_id: str
    option_b_id: str
    description: str
    gain: str
    sacrifice: str


class InputQuality(BaseModel):
    """Assessment of whether the user's input is specific enough to analyse."""
    level: Literal["sufficient", "too_vague", "needs_options", "needs_numbers"] = "sufficient"
    # Human-readable explanation of WHY the input is insufficient
    reason: str = ""
    # Concrete suggestions shown to the user (max 3 bullet points)
    suggestions: list[str] = Field(default_factory=list)


class ScoredValue(BaseModel):
    """
    A single cell in the multi-criteria decision matrix.
    Provenance and source reference are strictly tracked to eliminate hallucinations.
    """
    value: float
    unit: str | None = None
    provenance: Literal["user_supplied", "derived", "assumed", "web_sourced", "llm_extracted", "llm_suggested"] = "user_supplied"
    source_ref: str | None = None  # fact_id | evidence_id | "assumption" | "user_input"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class DecisionCase(BaseModel):
    """
    Primary human-centric problem representation.
    Decoupled from mathematical solvers and binary variables.
    """
    id: str = Field(default_factory=lambda: f"case_{uuid.uuid4().hex[:8]}")
    title: str
    context: str
    status: Literal[
        "intake",
        "clarification",
        "ready_for_modeling",
        "modeled",
        "evaluated"
    ] = "intake"
    facts: list[Fact] = Field(default_factory=list)
    options: list[Option] = Field(default_factory=list)
    criteria: list[Criterion] = Field(default_factory=list)
    unknowns: list[Unknown] = Field(default_factory=list)
    tradeoffs: list[Tradeoff] = Field(default_factory=list)
    priority_tokens: list[str] = Field(default_factory=list)
    selected_priority_tokens: list[str] = Field(default_factory=list)
    score_matrix: dict[str, dict[str, ScoredValue]] = Field(default_factory=dict)
    break_even_point: str | None = None
    # Quality gate: populated by LLMAdvisor before any solver work starts
    input_quality: InputQuality = Field(default_factory=InputQuality)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    problem_ir_id: str | None = None

    def validate_for_modeling(self) -> tuple[bool, list[str]]:
        """
        Validates whether all option-criterion pairs have a valid ScoredValue with source_ref.
        Returns (is_valid, missing_errors).
        """
        missing_errors: list[str] = []
        if len(self.criteria) == 0:
            missing_errors.append("Zdefiniuj co najmniej jedno kryterium.")
        if len(self.options) < 2:
            missing_errors.append("Zdefiniuj co najmniej dwie opcje decyzyjne.")
        for opt in self.options:
            for crit in self.criteria:
                cell = self.score_matrix.get(opt.id, {}).get(crit.id)
                if cell is None:
                    missing_errors.append(f"Brak wartości w macierzy dla opcji '{opt.title}' i kryterium '{crit.name}'.")
                elif not cell.source_ref:
                    missing_errors.append(f"Wartość dla opcji '{opt.title}' i kryterium '{crit.name}' nie posiada przypisanego źródła (source_ref).")
        return len(missing_errors) == 0, missing_errors

