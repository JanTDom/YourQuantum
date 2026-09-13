"""
YourQuantum — Cognitive Working Memory & Cybernetic Homeostasis
Prefrontal cortex model: tracks active goals, current hypothesis (ProblemIR),
focal variables, and prediction errors under strict token/cycle metabolic constraints.
"""
from __future__ import annotations

import logging
from typing import Any
from pydantic import BaseModel, Field

from backend.domain.problem_ir import ProblemIR

logger = logging.getLogger(__name__)


class EnergyBudget(BaseModel):
    """
    Metabolic budget preventing runaway API usage and infinite reflection loops.
    Tracks token consumption and inference/refinement cycles.
    """
    max_tokens: int = Field(default=8000, ge=1)
    tokens_used: int = Field(default=0, ge=0)
    max_cycles: int = Field(default=3, ge=1)
    current_cycle: int = Field(default=0, ge=0)

    def consume(self, tokens: int) -> bool:
        """
        Attempt to consume token budget.
        Returns True if consumption was allowed within budget, False if exhausted.
        """
        if tokens < 0:
            raise ValueError("Token consumption must be non-negative.")
        if self.tokens_used + tokens > self.max_tokens:
            self.tokens_used = self.max_tokens
            logger.warning("EnergyBudget exhausted: token limit reached (%d/%d).", self.tokens_used, self.max_tokens)
            return False
        self.tokens_used += tokens
        return True

    def next_cycle(self) -> bool:
        """
        Advance to next active inference cycle.
        Returns True if another cycle can be executed, False if cycle budget is exhausted.
        """
        if self.current_cycle >= self.max_cycles:
            logger.warning("EnergyBudget exhausted: max cycles reached (%d/%d).", self.current_cycle, self.max_cycles)
            return False
        self.current_cycle += 1
        return True

    def is_exhausted(self) -> bool:
        """Check whether metabolic budget (tokens or cycles) has been depleted."""
        return self.tokens_used >= self.max_tokens or self.current_cycle >= self.max_cycles

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.tokens_used)

    @property
    def remaining_cycles(self) -> int:
        return max(0, self.max_cycles - self.current_cycle)


class WorkingMemory(BaseModel):
    """
    Working Memory representation representing active cognitive state in RAM.
    """
    current_goal: str
    active_hypothesis: ProblemIR | None = None
    prediction_errors: list[str] = Field(default_factory=list)
    focus_variables: list[str] = Field(default_factory=list)
    cycle_history: list[dict[str, Any]] = Field(default_factory=list)

    def record_error(self, error: str) -> None:
        """Record a prediction error signal from the verifier or sanity check."""
        clean_err = error.strip()
        if clean_err and clean_err not in self.prediction_errors:
            self.prediction_errors.append(clean_err)

    def clear_errors(self) -> None:
        """Clear active prediction errors upon hypothesis revision."""
        self.prediction_errors.clear()

    def set_hypothesis(self, ir: ProblemIR | None) -> None:
        """Set active ProblemIR hypothesis and extract focus variables."""
        self.active_hypothesis = ir
        if ir is not None:
            self.focus_variables = [v.id for v in ir.variables]
        else:
            self.focus_variables = []


class GlobalWorkspace:
    """
    Global Workspace Theory coordinator.
    Manages working memory contents, broadcasts error signals, and maintains homeostasis.
    """

    def __init__(
        self,
        goal: str,
        budget: EnergyBudget | None = None,
        memory: WorkingMemory | None = None,
    ) -> None:
        self.energy_budget = budget or EnergyBudget()
        if memory is not None:
            memory.current_goal = goal
            self.memory = memory
        else:
            self.memory = WorkingMemory(current_goal=goal)

    def update_hypothesis(self, ir: ProblemIR | None, cycle_metadata: dict[str, Any] | None = None) -> None:
        """Update current hypothesis in working memory and log cycle telemetry."""
        self.memory.set_hypothesis(ir)
        log_entry: dict[str, Any] = {
            "cycle": self.energy_budget.current_cycle,
            "tokens_used": self.energy_budget.tokens_used,
            "has_hypothesis": ir is not None,
        }
        if cycle_metadata:
            log_entry.update(cycle_metadata)
        self.memory.cycle_history.append(log_entry)

    def register_prediction_error(self, error_message: str) -> None:
        """Broadcast prediction error into working memory."""
        self.memory.record_error(error_message)

    def format_state_for_reasoning(self) -> dict[str, Any]:
        """
        Produce structured contextual state for cognitive reasoning adapters.
        """
        hypothesis_summary: dict[str, Any] | None = None
        if self.memory.active_hypothesis is not None:
            ir = self.memory.active_hypothesis
            hypothesis_summary = {
                "problem_id": ir.problem_id,
                "variables_count": len(ir.variables),
                "constraints_count": len(ir.constraints),
                "objectives_count": len(ir.objectives),
                "variable_ids": [v.id for v in ir.variables],
            }

        return {
            "goal": self.memory.current_goal,
            "current_cycle": self.energy_budget.current_cycle,
            "tokens_used": self.energy_budget.tokens_used,
            "remaining_tokens": self.energy_budget.remaining_tokens,
            "prediction_errors": list(self.memory.prediction_errors),
            "focus_variables": list(self.memory.focus_variables),
            "active_hypothesis": hypothesis_summary,
        }
