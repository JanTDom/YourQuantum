"""
YourQuantum — Cognitive Intake & Telemetry API Routes
Unified brain-inspired problem intake, working memory session inspection, and consent-gated consolidation.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_session
from backend.db.models import CognitiveSessionRecord, new_uuid
from backend.domain.cognitive.active_inference_engine import (
    ActiveInferenceOrchestrator,
    compute_problem_fingerprint,
)
from backend.domain.cognitive.cognitive_port import FormalizationResult
from backend.domain.cognitive.episodic_memory import EpisodicMemoryRepository
from backend.domain.cognitive.workspace import EnergyBudget, GlobalWorkspace, WorkingMemory
from backend.infrastructure.gemini_cognitive_adapter import GeminiCognitiveAdapter
from backend.api.security_guard import verify_security_limits

logger = logging.getLogger(__name__)

cognitive_router = APIRouter(tags=["cognitive"])


class CognitiveIntakeRequest(BaseModel):
    query: str = Field(min_length=1, description="Opis problemu lub dylematu decyzyjnego w języku naturalnym")
    session_id: str | None = Field(default=None, description="Identyfikator aktywnej sesji użytkownika")
    owner_id: str | None = Field(default=None, description="Identyfikator właściciela/użytkownika dla multi-tenant workspace")
    workspace_id: str | None = Field(default=None, description="Identyfikator przestrzeni roboczej")
    problem_class_override: str | None = Field(default=None, description="Ręczne nadpisanie klasy problemu przez użytkownika (CHOICE, ALLOCATION, DESIGN, PARAMETER)")


class ConsolidateTraceRequest(BaseModel):
    session_id: str = Field(description="Identyfikator sesji kognitywnej")
    consent: bool = Field(default=False, description="Świadoma zgoda użytkownika na anonimizację i zapamiętanie struktury")


class CognitiveSessionTelemetry(BaseModel):
    session_id: str
    goal: str
    current_cycle: int
    energy_budget: dict[str, Any]
    prediction_errors: list[str]
    focus_variables: list[str]
    cycle_history: list[dict[str, Any]]
    has_active_hypothesis: bool
    active_problem_id: str | None = None
    interaction_history: list[dict[str, Any]]
    created_at: str
    updated_at: str


@cognitive_router.post(
    "/cognitive/intake",
    response_model=FormalizationResult,
    status_code=status.HTTP_200_OK,
    summary="Jedna ścieżka intake dla problemów i dylematów (E1)",
)
async def cognitive_intake(
    req: CognitiveIntakeRequest,
    session: AsyncSession = Depends(get_session),
    client_key: str = Depends(verify_security_limits),
) -> FormalizationResult:
    """
    Główny punkt wejściowy systemu (Phase E1).
    Percepcja -> Klasyfikacja ProblemClass -> Episodic Recall -> DecisionCase ->
    Quality Gate -> Plan Badawczy -> Decision Matrix -> ProblemIR -> Sanity Check.
    """
    try:
        # 1. Retrieve or create CognitiveSessionRecord
        session_rec: CognitiveSessionRecord | None = None
        session_id = req.session_id or new_uuid()
        if req.session_id:
            try:
                session_rec = await session.get(CognitiveSessionRecord, req.session_id)
            except Exception as get_err:
                logger.warning("Nie udało się odczytać sesji kognitywnej z bazy: %s", get_err)
                session_rec = None

        if session_rec is None:
            session_rec = CognitiveSessionRecord(
                id=session_id,
                owner_id=req.owner_id,
                workspace_id=req.workspace_id,
                working_memory_json={},
                energy_budget_json={},
                history_json=[],
            )
            try:
                session.add(session_rec)
                await session.commit()
                await session.refresh(session_rec)
            except Exception as add_err:
                logger.warning("Nie udało się utrwalić sesji kognitywnej w bazie: %s", add_err)
                try:
                    await session.rollback()
                except Exception:
                    pass

        # 2. Restore GlobalWorkspace and EnergyBudget from session
        workspace: GlobalWorkspace | None = None
        budget: EnergyBudget | None = None
        if session_rec.energy_budget_json:
            try:
                budget = EnergyBudget.model_validate(session_rec.energy_budget_json)
            except Exception as b_err:
                logger.warning("Nie udało się odtworzyć energy budget: %s", b_err)

        if session_rec.working_memory_json:
            try:
                mem = WorkingMemory.model_validate(session_rec.working_memory_json)
                workspace = GlobalWorkspace(goal=req.query, budget=budget, memory=mem, session_id=session_rec.id)
            except Exception as w_err:
                logger.warning("Nie udało się odtworzyć working memory: %s", w_err)

        if workspace is None:
            workspace = GlobalWorkspace(goal=req.query, budget=budget, session_id=session_rec.id)

        # 3. Execute Active Inference cycle
        adapter = GeminiCognitiveAdapter()
        orchestrator = ActiveInferenceOrchestrator(reasoning_port=adapter)
        formalization, ws = await orchestrator.run_intake(
            session=session,
            query=req.query,
            workspace=workspace,
            owner_id=session_rec.owner_id,
            workspace_id=session_rec.workspace_id,
            problem_class_override=req.problem_class_override,
        )

        # 4. Save updated working memory, energy budget, and history
        session_rec.working_memory_json = ws.memory.model_dump(mode="json")
        session_rec.energy_budget_json = ws.energy_budget.model_dump(mode="json")
        history = list(session_rec.history_json or [])
        history.append({
            "query": req.query,
            "formalization_status": formalization.status,
            "problem_class": formalization.problem_class,
            "fingerprint": formalization.fingerprint,
            "cycle": ws.energy_budget.current_cycle,
            "tokens_used": ws.energy_budget.tokens_used,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        session_rec.history_json = history
        try:
            session.add(session_rec)
            await session.commit()
        except Exception as save_err:
            logger.warning("Nie udało się zaktualizować sesji kognitywnej w bazie: %s", save_err)
            try:
                await session.rollback()
            except Exception:
                pass

        # 5. Populate session_id in response
        formalization.session_id = session_rec.id
        return formalization

    except Exception as e:
        logger.exception("Błąd w endpointzie cognitive_intake: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd orkiestracji kognitywnej: {str(e)}",
        )


@cognitive_router.get(
    "/cognitive/session/{session_id}",
    response_model=CognitiveSessionTelemetry,
    status_code=status.HTTP_200_OK,
    summary="Telemetria Cognitive Inspector dla sesji (E6)",
)
async def get_cognitive_session_telemetry(
    session_id: str,
    session: AsyncSession = Depends(get_session),
) -> CognitiveSessionTelemetry:
    """
    Zwraca rzeczywisty stan pamięci roboczej, budżetu metabolicznego i historii cykli bez metafor.
    """
    session_rec = await session.get(CognitiveSessionRecord, session_id)
    if session_rec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesja kognitywna {session_id} nie istnieje.",
        )

    working_mem = session_rec.working_memory_json or {}
    budget_dict = session_rec.energy_budget_json or {}
    budget = EnergyBudget.model_validate(budget_dict) if budget_dict else EnergyBudget()

    active_hyp = working_mem.get("active_hypothesis")
    active_prob_id = active_hyp.get("problem_id") if isinstance(active_hyp, dict) else None

    return CognitiveSessionTelemetry(
        session_id=session_rec.id,
        goal=working_mem.get("current_goal", ""),
        current_cycle=budget.current_cycle,
        energy_budget={
            "tokens_used": budget.tokens_used,
            "max_tokens": budget.max_tokens,
            "search_queries_used": budget.search_queries_used,
            "max_search_queries": budget.max_search_queries,
            "solver_seconds_used": budget.solver_seconds_used,
            "max_solver_seconds": budget.max_solver_seconds,
            "is_exhausted": budget.is_exhausted(),
            "exhaustion_reason": budget.get_exhaustion_reason(),
            "simplification_suggestions": budget.suggest_simplifications(),
        },
        prediction_errors=working_mem.get("prediction_errors", []),
        focus_variables=working_mem.get("focus_variables", []),
        cycle_history=working_mem.get("cycle_history", []),
        has_active_hypothesis=active_hyp is not None,
        active_problem_id=active_prob_id,
        interaction_history=session_rec.history_json or [],
        created_at=session_rec.created_at.isoformat() if session_rec.created_at else "",
        updated_at=session_rec.updated_at.isoformat() if session_rec.updated_at else "",
    )


@cognitive_router.delete(
    "/cognitive/session/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Kasowanie sesji kognitywnej i zwolnienie pamięci roboczej (E2)",
)
async def delete_cognitive_session(
    session_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """
    Usuwa sesję kognitywną użytkownika zgodnie z prawem do zapomnienia i zwalniania zasobów.
    """
    session_rec = await session.get(CognitiveSessionRecord, session_id)
    if session_rec is not None:
        await session.delete(session_rec)
        await session.commit()
    return {"status": "deleted", "session_id": session_id}


@cognitive_router.post(
    "/cognitive/consolidate",
    status_code=status.HTTP_200_OK,
    summary="Anonimizowana konsolidacja epizodyczna za zgodą (E5)",
)
async def consolidate_trace(
    req: ConsolidateTraceRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    Zapisuje zanonimizowaną strukturę problemu do bazy śladów epizodycznych (cognitive_traces)
    wyłącznie pod warunkiem jawnej zgody użytkownika (E5).
    """
    if not req.consent:
        return {
            "status": "skipped",
            "message": "Zgoda nie została udzielona. Żaden ślad pamięciowy nie został zapisany.",
        }

    session_rec = await session.get(CognitiveSessionRecord, req.session_id)
    if session_rec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesja kognitywna {req.session_id} nie istnieje.",
        )

    working_mem = session_rec.working_memory_json or {}
    active_hyp = working_mem.get("active_hypothesis") or {}
    goal = working_mem.get("current_goal", "")

    fp = compute_problem_fingerprint(goal)
    episodic_repo = EpisodicMemoryRepository()

    trace_id = await episodic_repo.consolidate_trace(
        session=session,
        trace_data={
            "problem_fingerprint": fp,
            "raw_user_query": "[ANONYMIZED_STRUCTURAL_QUERY]",
            "successful_ir_json": active_hyp,
            "winning_solver": "router_selected",
            "penalty_multipliers": {},
            "reward_score": 1.0,
            "lessons_learned": "Zanonimizowany wzorzec strukturalny zachowany za zgodą użytkownika.",
            "owner_id": session_rec.owner_id,
            "workspace_id": session_rec.workspace_id,
            "is_public": False,
        },
    )

    return {
        "status": "consolidated",
        "trace_id": trace_id,
        "message": "Zanonimizowana struktura problemu została zachowana.",
    }
