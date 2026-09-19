"""
YourQuantum — Cognitive Working Memory & Cybernetic Homeostasis
Prefrontal cortex model: tracks active goals, current hypothesis (ProblemIR),
focal variables, and prediction errors under strict token/cycle/search metabolic constraints.
"""
from __future__ import annotations

import logging
import os
from typing import Any
from pydantic import BaseModel, Field

from backend.domain.problem_ir import ProblemIR

logger = logging.getLogger(__name__)


class EnergyBudget(BaseModel):
    """
    Metabolic budget preventing runaway API usage, excessive web search, and infinite reflection loops.
    Tracks token consumption, search queries, solver execution time, and inference cycles.
    """
    max_tokens: int = Field(default=10000, ge=1)
    tokens_used: int = Field(default=0, ge=0)
    max_cycles: int = Field(default=3, ge=1)
    current_cycle: int = Field(default=0, ge=0)
    max_search_queries: int = Field(default=10, ge=1)
    search_queries_used: int = Field(default=0, ge=0)
    max_solver_seconds: float = Field(default=60.0, ge=1.0)
    solver_seconds_used: float = Field(default=0.0, ge=0.0)
    daily_token_limit: int = Field(default=50000, ge=1)
    daily_tokens_used: int = Field(default=0, ge=0)

    def consume_tokens(self, tokens: int) -> bool:
        """
        Attempt to consume token budget.
        Returns True if consumption was allowed within budget, False if exhausted.
        """
        if tokens < 0:
            raise ValueError("Token consumption must be non-negative.")
        if self.tokens_used + tokens > self.max_tokens or self.daily_tokens_used + tokens > self.daily_token_limit:
            self.tokens_used = min(self.max_tokens, self.tokens_used + tokens)
            self.daily_tokens_used = min(self.daily_token_limit, self.daily_tokens_used + tokens)
            logger.warning("EnergyBudget exhausted: token limit reached (%d/%d, daily %d/%d).",
                           self.tokens_used, self.max_tokens, self.daily_tokens_used, self.daily_token_limit)
            return False
        self.tokens_used += tokens
        self.daily_tokens_used += tokens
        return True

    def consume(self, tokens: int) -> bool:
        """Backward-compatible alias for consume_tokens."""
        return self.consume_tokens(tokens)

    def consume_search(self, count: int = 1) -> bool:
        """
        Attempt to consume web research query budget.
        """
        if count < 0:
            raise ValueError("Search count must be non-negative.")
        if self.search_queries_used + count > self.max_search_queries:
            self.search_queries_used = self.max_search_queries
            logger.warning("EnergyBudget exhausted: search query limit reached (%d/%d).",
                           self.search_queries_used, self.max_search_queries)
            return False
        self.search_queries_used += count
        return True

    def consume_solver_time(self, seconds: float) -> bool:
        """
        Track solver execution duration.
        """
        if seconds < 0:
            raise ValueError("Solver time must be non-negative.")
        self.solver_seconds_used += seconds
        if self.solver_seconds_used > self.max_solver_seconds:
            logger.warning("EnergyBudget exhausted: solver time limit exceeded (%.1fs/%.1fs).",
                           self.solver_seconds_used, self.max_solver_seconds)
            return False
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
        """Check whether metabolic budget has been depleted in any dimension."""
        return (
            self.tokens_used >= self.max_tokens
            or self.daily_tokens_used >= self.daily_token_limit
            or self.current_cycle >= self.max_cycles
            or self.search_queries_used >= self.max_search_queries
            or self.solver_seconds_used >= self.max_solver_seconds
        )

    def get_exhaustion_reason(self) -> str | None:
        """Return human-readable explanation if metabolic budget is depleted."""
        if self.tokens_used >= self.max_tokens:
            return f"Wyczerpano limit tokenów sesji ({self.tokens_used}/{self.max_tokens})."
        if self.daily_tokens_used >= self.daily_token_limit:
            return f"Wyczerpano dobowy limit tokenów ({self.daily_tokens_used}/{self.daily_token_limit})."
        if self.current_cycle >= self.max_cycles:
            return f"Wyczerpano maksymalną liczbę cykli autorefleksji ({self.current_cycle}/{self.max_cycles})."
        if self.search_queries_used >= self.max_search_queries:
            return f"Wyczerpano limit zapytań badawczych do sieci ({self.search_queries_used}/{self.max_search_queries})."
        if self.solver_seconds_used >= self.max_solver_seconds:
            return f"Wyczerpano limit czasu obliczeń solvera ({self.solver_seconds_used:.1f}s/{self.max_solver_seconds:.1f}s)."
        return None

    def suggest_simplifications(self) -> list[str]:
        """Provide concrete advice on how to reduce computational overhead."""
        suggestions: list[str] = []
        if self.current_cycle >= self.max_cycles:
            suggestions.append("Zmniejsz liczbę wariantów lub kryteriów wyboru, aby ułatwić zbieżność modelu.")
        if self.search_queries_used >= self.max_search_queries:
            suggestions.append("Podaj brakujące liczby i parametry bezpośrednio, zamiast szukać ich w sieci.")
        if self.tokens_used >= self.max_tokens:
            suggestions.append("Sformułuj dylemat w bardziej zwięzły sposób, skupiając się na kluczowych liczbach.")
        if self.solver_seconds_used >= self.max_solver_seconds:
            suggestions.append("Ogranicz liczbę zmiennych decyzyjnych lub wybierz szybszy solver (CP-SAT).")
        if not suggestions:
            suggestions.append("Zatwierdź bieżący model lub podaj konkretne ograniczenia.")
        return suggestions

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.tokens_used)

    @property
    def remaining_cycles(self) -> int:
        return max(0, self.max_cycles - self.current_cycle)

    @property
    def remaining_search_queries(self) -> int:
        return max(0, self.max_search_queries - self.search_queries_used)


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
        session_id: str | None = None,
    ) -> None:
        self.session_id = session_id
        self.energy_budget = budget or EnergyBudget()
        # Mutable telemetry bag — populated by callers (e.g. DESIGN path in
        # active_inference_engine) to accumulate per-run counters without
        # coupling the workspace class to any specific execution strategy.
        self.telemetry: dict[str, Any] = {}
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
            "search_queries_used": self.energy_budget.search_queries_used,
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
            "session_id": self.session_id,
            "goal": self.memory.current_goal,
            "current_cycle": self.energy_budget.current_cycle,
            "tokens_used": self.energy_budget.tokens_used,
            "remaining_tokens": self.energy_budget.remaining_tokens,
            "search_queries_used": self.energy_budget.search_queries_used,
            "remaining_search_queries": self.energy_budget.remaining_search_queries,
            "prediction_errors": list(self.memory.prediction_errors),
            "focus_variables": list(self.memory.focus_variables),
            "active_hypothesis": hypothesis_summary,
        }
