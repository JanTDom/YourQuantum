"""
YourQuantum — Active Inference Engine & Cognitive Orchestrator
Coordinates the cybernetic perception-hypothesis-action-verification loop based on
Karl Friston's Free Energy Principle and neurobiological global workspace theory.
"""
from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Callable, Literal
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.cognitive.cognitive_port import CognitiveReasoningPort, FormalizationResult
from backend.domain.cognitive.constraint_sanity import check_constraints_sanity
from backend.domain.cognitive.episodic_memory import EpisodicMemoryRepository
from backend.domain.cognitive.workspace import EnergyBudget, GlobalWorkspace
from backend.domain.problem_ir import ProblemIR
from backend.verifier.verifier import Verdict, VerificationReport

logger = logging.getLogger(__name__)


import unicodedata

POLISH_STOPWORDS = {
    "i", "w", "z", "ze", "o", "a", "oraz", "na", "do", "od", "po", "dla",
    "czy", "się", "sie", "jest", "to", "nie", "jak", "co", "albo", "lub",
    "że", "ze", "by", "aby", "jaki", "jaka", "jakie", "mam", "między",
    "miedzy", "który", "ktora", "ktore", "które", "ten", "ta", "tych", "tym",
    "bardzo", "tylko", "może", "moze", "gdy", "przy"
}

POLISH_SUFFIXES = tuple(sorted([
    "owych", "owego", "acjami", "eniem", "ności",
    "acja", "acje", "acji", "acją",
    "ami", "ach", "ych", "ego", "emu", "iej", "owi", "em", "ie", "om",
    "am", "ą", "ę", "y", "e", "a", "u", "i", "ć", "ów", "ow"
], key=len, reverse=True))


def _stem_polish(word: str) -> str:
    for sfx in POLISH_SUFFIXES:
        if word.endswith(sfx) and len(word) - len(sfx) >= 3:
            return word[: -len(sfx)]
    return word


def compute_problem_fingerprint(query: str) -> str:
    """
    Generate a structural fingerprint hash for associative episodic recall.
    Uses NFKC normalization, Polish stopwords filtering, and stemming.
    """
    normalized = unicodedata.normalize("NFKC", query.lower())
    words = re.findall(r"\b[^\W\d_]{3,}\b", normalized, flags=re.UNICODE)
    meaningful = [w for w in words if w not in POLISH_STOPWORDS]
    stems = [_stem_polish(w) for w in meaningful]
    sorted_unique = sorted(set(stems))
    token_repr = "_".join(sorted_unique[:10]) if sorted_unique else "empty_query"
    fp_hash = hashlib.sha256(token_repr.encode("utf-8")).hexdigest()[:16]
    return f"fp_{fp_hash}_{len(sorted_unique)}"


class ActiveInferenceOutcome(BaseModel):
    """Result of an active inference evaluation cycle."""
    status: Literal["PASS", "FAIL", "EXHAUSTED", "CLARIFICATION_REQUIRED"]
    reward_score: float = 0.0
    current_cycle: int = 0
    trace_id: str | None = None
    prediction_errors: list[str] = Field(default_factory=list)
    active_problem_ir: ProblemIR | None = None
    explanation: str = ""


class ActiveInferenceOrchestrator:
    """
    Brain-inspired cognitive engine coordinating Working Memory, Episodic Memory,
    Gemini/Fallback Reasoning Port, and the Independent Verifier.
    """

    def __init__(
        self,
        reasoning_port: CognitiveReasoningPort,
        episodic_repo: EpisodicMemoryRepository | None = None,
        budget: EnergyBudget | None = None,
    ) -> None:
        self.reasoning_port = reasoning_port
        self.episodic_repo = episodic_repo or EpisodicMemoryRepository()
        self.default_budget = budget or EnergyBudget()

    async def run_intake(
        self,
        session: AsyncSession,
        query: str,
        workspace: GlobalWorkspace | None = None,
        owner_id: str | None = None,
        workspace_id: str | None = None,
    ) -> tuple[FormalizationResult, GlobalWorkspace]:
        """
        Execute Stage 1-4 of Cognitive Perception:
        Perception -> Episodic Recall -> Hypothesis Generation -> Sanity Check.
        """
        ws = workspace or GlobalWorkspace(goal=query, budget=self.default_budget.model_copy())
        fp = compute_problem_fingerprint(query)

        # 1. Hippocampal recall of historical analogies with tenant isolation
        analogies = await self.episodic_repo.recall_analogies(
            session,
            fingerprint=fp,
            limit=3,
            owner_id=owner_id,
            workspace_id=workspace_id,
        )

        # 2. Hypothesis formulation via CognitiveReasoningPort
        formalization = await self.reasoning_port.formalize_query(
            query=query,
            analogies=analogies,
            error_context=ws.memory.prediction_errors if ws.memory.prediction_errors else None,
        )

        # Consume token budget estimation (~300 tokens per cognitive query pass)
        token_cost = 350
        ws.energy_budget.consume(token_cost)

        if formalization.status == "needs_clarification" or formalization.problem_ir is None:
            ws.update_hypothesis(None, {"status": "needs_clarification"})
            return formalization, ws

        # 3. Pre-solver constraint sanity check
        sanity = check_constraints_sanity(formalization.problem_ir)
        if not sanity.passed:
            for err in sanity.errors:
                ws.register_prediction_error(f"Sanity Check Failure: {err}")

            # If we still have budget cycles, attempt self-correction reflexion
            if not ws.energy_budget.is_exhausted() and ws.energy_budget.next_cycle():
                logger.info(
                    "Sanity check caught contradictions. Entering internal reflection cycle %d.",
                    ws.energy_budget.current_cycle,
                )
                return await self.run_intake(
                    session=session,
                    query=query,
                    workspace=ws,
                    owner_id=owner_id,
                    workspace_id=workspace_id,
                )
            else:
                formalization.questions.extend(sanity.errors)
                formalization.status = "needs_clarification"
                formalization.explanation += " Wykryto wewnętrzne sprzeczności w ograniczeniach."

        ws.update_hypothesis(formalization.problem_ir, {"status": formalization.status})
        return formalization, ws

    async def process_verification_feedback(
        self,
        session: AsyncSession,
        workspace: GlobalWorkspace,
        verifier_report: VerificationReport,
        raw_query: str,
        winning_solver: str = "cpsat",
    ) -> ActiveInferenceOutcome:
        """
        Active Inference Error Minimization Loop (Stage 5-6):
        - If Verifier passes (PASS): consolidates trace, emits reward (1.0 or decayed).
        - If Verifier fails (FAIL): treats violations as Prediction Errors, consumes cycle,
          and adapts hypothesis.
        """
        is_pass = verifier_report.verdict == Verdict.PASS or (
            verifier_report.feasible and verifier_report.verdict != Verdict.FAIL
        )

        if is_pass:
            # Calculate reward score: immediate pass = 1.0, decayed if required reflexion
            cycle = workspace.energy_budget.current_cycle
            reward = 1.0 if cycle == 0 else max(0.5, 1.0 - (cycle * 0.15))

            fp = compute_problem_fingerprint(raw_query)
            ir_dict = (
                workspace.memory.active_hypothesis.model_dump(mode="json")
                if workspace.memory.active_hypothesis
                else {}
            )

            trace_id = await self.episodic_repo.consolidate_trace(
                session=session,
                trace_data={
                    "problem_fingerprint": fp,
                    "raw_user_query": raw_query,
                    "successful_ir_json": ir_dict,
                    "winning_solver": winning_solver,
                    "penalty_multipliers": {},
                    "reward_score": reward,
                    "lessons_learned": f"Zbieżność osiągnięta w cyklu {cycle} przy weryfikacji {verifier_report.verdict.value}.",
                },
            )

            return ActiveInferenceOutcome(
                status="PASS",
                reward_score=reward,
                current_cycle=cycle,
                trace_id=trace_id,
                active_problem_ir=workspace.memory.active_hypothesis,
                explanation="Model pomyślnie zweryfikowany przez niezależny weryfikator.",
            )

        # Verification Failed: compute prediction errors
        error_signals: list[str] = [f"Verifier Verdict: {verifier_report.verdict.value} ({verifier_report.verdict_reason})"]
        for cr in verifier_report.constraint_results:
            if not cr.satisfied:
                error_signals.append(
                    f"Naruszone ograniczenie {cr.constraint_id} (mag={cr.violation_magnitude}, note={cr.note})"
                )
        for dv in verifier_report.domain_violations:
            error_signals.append(f"Naruszenie dziedziny zmiennej {dv}")

        for sig in error_signals:
            workspace.register_prediction_error(sig)

        # Check energy exhaustion
        if workspace.energy_budget.is_exhausted() or not workspace.energy_budget.next_cycle():
            logger.warning("Active inference metabolic budget depleted after %d cycles.", workspace.energy_budget.current_cycle)
            return ActiveInferenceOutcome(
                status="EXHAUSTED",
                reward_score=0.0,
                current_cycle=workspace.energy_budget.current_cycle,
                prediction_errors=workspace.memory.prediction_errors,
                active_problem_ir=workspace.memory.active_hypothesis,
                explanation="Przekroczono limit energii/cykli autorefleksji bez osiągnięcia zbieżności.",
            )

        # Free Energy Minimization: generate refined hypothesis with error context
        fp = compute_problem_fingerprint(raw_query)
        analogies = await self.episodic_repo.recall_analogies(session, fingerprint=fp, limit=2)
        revised_res = await self.reasoning_port.formalize_query(
            query=raw_query,
            analogies=analogies,
            error_context=workspace.memory.prediction_errors,
        )
        workspace.energy_budget.consume(300)

        if revised_res.problem_ir is not None:
            workspace.update_hypothesis(revised_res.problem_ir, {"status": "revised_hypothesis"})
            return ActiveInferenceOutcome(
                status="FAIL",
                reward_score=0.2,
                current_cycle=workspace.energy_budget.current_cycle,
                prediction_errors=workspace.memory.prediction_errors,
                active_problem_ir=revised_res.problem_ir,
                explanation="Zarejestrowano błąd predykcji. Wygenerowano zaktualizowaną hipotezę ProblemIR.",
            )

        return ActiveInferenceOutcome(
            status="CLARIFICATION_REQUIRED",
            reward_score=0.0,
            current_cycle=workspace.energy_budget.current_cycle,
            prediction_errors=workspace.memory.prediction_errors,
            active_problem_ir=None,
            explanation="Autorefleksja wymaga doprecyzowania od użytkownika.",
        )
