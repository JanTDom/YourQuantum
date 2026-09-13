"""
YourQuantum — Cognitive Intake API Route
Endpoints for brain-inspired problem intake and formalization.
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
from backend.domain.cognitive.active_inference_engine import ActiveInferenceOrchestrator
from backend.domain.cognitive.cognitive_port import FormalizationResult
from backend.domain.cognitive.workspace import GlobalWorkspace, WorkingMemory
from backend.infrastructure.gemini_cognitive_adapter import GeminiCognitiveAdapter

logger = logging.getLogger(__name__)

cognitive_router = APIRouter(tags=["cognitive"])


class CognitiveIntakeRequest(BaseModel):
    query: str = Field(min_length=1, description="Opis problemu lub dylematu decyzyjnego w języku naturalnym")
    session_id: str | None = Field(default=None, description="Identyfikator aktywnej sesji użytkownika")
    owner_id: str | None = Field(default=None, description="Identyfikator właściciela/użytkownika dla multi-tenant workspace")
    workspace_id: str | None = Field(default=None, description="Identyfikator przestrzeni roboczej")


@cognitive_router.post(
    "/cognitive/intake",
    response_model=FormalizationResult,
    status_code=status.HTTP_200_OK,
    summary="Kognitywny intake problemu decyzyjnego",
)
async def cognitive_intake(
    req: CognitiveIntakeRequest,
    session: AsyncSession = Depends(get_session),
) -> FormalizationResult:
    """
    Kognitywny punkt wejściowy (Stage 4).
    Przekształca opis w języku naturalnym w sformalizowany model ProblemIR
    z wykorzystaniem architektury inspirowanej mózgiem (working memory, episodic memory, active inference).
    Wiąże zapytania z sesją kognitywną (CognitiveSessionRecord) z zachowaniem izolacji wielodostępowej.
    """
    try:
        # 1. Retrieve or create CognitiveSessionRecord
        session_rec: CognitiveSessionRecord | None = None
        if req.session_id:
            session_rec = await session.get(CognitiveSessionRecord, req.session_id)

        if session_rec is None:
            session_id = req.session_id or new_uuid()
            session_rec = CognitiveSessionRecord(
                id=session_id,
                owner_id=req.owner_id,
                workspace_id=req.workspace_id,
                working_memory_json={},
                history_json=[],
            )
            session.add(session_rec)
            await session.commit()
            await session.refresh(session_rec)

        # 2. Restore GlobalWorkspace from working memory if available
        workspace: GlobalWorkspace | None = None
        if session_rec.working_memory_json:
            try:
                mem = WorkingMemory.model_validate(session_rec.working_memory_json)
                workspace = GlobalWorkspace(goal=req.query, memory=mem)
            except Exception as w_err:
                logger.warning("Nie udało się odtworzyć working memory: %s", w_err)

        # 3. Execute Active Inference cycle
        adapter = GeminiCognitiveAdapter()
        orchestrator = ActiveInferenceOrchestrator(reasoning_port=adapter)
        formalization, ws = await orchestrator.run_intake(
            session=session,
            query=req.query,
            workspace=workspace,
            owner_id=session_rec.owner_id,
            workspace_id=session_rec.workspace_id,
        )

        # 4. Save updated working memory and interaction history in session
        session_rec.working_memory_json = ws.memory.model_dump(mode="json")
        history = list(session_rec.history_json or [])
        history.append({
            "query": req.query,
            "formalization_status": formalization.status,
            "fingerprint": formalization.fingerprint,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        session_rec.history_json = history
        await session.commit()

        # 5. Populate session_id in response
        formalization.session_id = session_rec.id
        return formalization

    except Exception as e:
        logger.exception("Błąd w endpointzie cognitive_intake: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd orkiestracji kognitywnej: {str(e)}",
        )
