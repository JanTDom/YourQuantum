"""
YourQuantum — Episodic Memory (Hippocampal Subsystem)
Persistent storage and recall of successful problem formulations, solver selections,
penalty calibrations, and lessons learned.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import CognitiveTraceRecord, new_uuid

logger = logging.getLogger(__name__)


class EpisodicMemoryRepository:
    """
    Manages long-term episodic traces stored in SQL database.
    Analogous to hippocampal consolidation and associative retrieval.
    Enforces tenant/workspace scoping and prevents cross-user raw query leakage.
    """

    async def recall_analogies(
        self,
        session: AsyncSession,
        fingerprint: str,
        limit: int = 3,
        owner_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve highest-reward historical traces matching or structurally resembling the problem fingerprint.
        Enforces tenant isolation: only returns public traces or traces belonging to owner/workspace.
        """
        cleaned_fp = fingerprint.strip()
        analogies: list[dict[str, Any]] = []

        # Multi-tenant scoping condition
        if owner_id or workspace_id:
            tenant_condition = or_(
                CognitiveTraceRecord.is_public.is_(True),
                and_(CognitiveTraceRecord.owner_id.is_not(None), CognitiveTraceRecord.owner_id == owner_id),
                and_(CognitiveTraceRecord.workspace_id.is_not(None), CognitiveTraceRecord.workspace_id == workspace_id),
            )
        else:
            # When unauthenticated or without tenant context, only recall public exemplars
            tenant_condition = or_(
                CognitiveTraceRecord.is_public.is_(True),
                and_(CognitiveTraceRecord.owner_id.is_(None), CognitiveTraceRecord.workspace_id.is_(None)),
            )

        try:
            # 1. Exact or prefix fingerprint match with high reward
            query_exact = (
                select(CognitiveTraceRecord)
                .where(
                    and_(
                        CognitiveTraceRecord.problem_fingerprint == cleaned_fp,
                        tenant_condition,
                    )
                )
                .order_by(desc(CognitiveTraceRecord.reward_score), desc(CognitiveTraceRecord.created_at))
                .limit(limit)
            )
            result = await session.execute(query_exact)
            records = result.scalars().all()

            for rec in records:
                is_same_owner = bool(owner_id and rec.owner_id == owner_id)
                analogies.append(self._record_to_dict(rec, include_raw_query=is_same_owner))

            # 2. If no exact match found, retrieve best performing general exemplars
            if not analogies:
                query_fallback = (
                    select(CognitiveTraceRecord)
                    .where(
                        and_(
                            CognitiveTraceRecord.reward_score >= 0.8,
                            tenant_condition,
                        )
                    )
                    .order_by(desc(CognitiveTraceRecord.reward_score), desc(CognitiveTraceRecord.created_at))
                    .limit(limit)
                )
                res_fallback = await session.execute(query_fallback)
                for rec in res_fallback.scalars().all():
                    is_same_owner = bool(owner_id and rec.owner_id == owner_id)
                    analogies.append(self._record_to_dict(rec, include_raw_query=is_same_owner))

        except Exception as e:
            logger.warning("Episodic memory recall encountered error: %s", e)
            return []

        return analogies

    async def consolidate_trace(
        self,
        session: AsyncSession,
        trace_data: dict[str, Any],
    ) -> str:
        """
        Consolidate a new successful episodic trace into persistent database storage.
        """
        trace_id = trace_data.get("id") or new_uuid()
        record = CognitiveTraceRecord(
            id=trace_id,
            owner_id=trace_data.get("owner_id"),
            workspace_id=trace_data.get("workspace_id"),
            is_public=bool(trace_data.get("is_public", False)),
            problem_fingerprint=trace_data.get("problem_fingerprint", "general_problem"),
            raw_user_query=trace_data.get("raw_user_query", ""),
            successful_ir_json=trace_data.get("successful_ir_json", {}),
            winning_solver=trace_data.get("winning_solver", "unknown"),
            penalty_multipliers=trace_data.get("penalty_multipliers", {}),
            reward_score=float(trace_data.get("reward_score", 1.0)),
            lessons_learned=trace_data.get("lessons_learned", ""),
        )

        session.add(record)
        await session.commit()
        await session.refresh(record)
        logger.info("Consolidated cognitive trace %s (reward=%.2f, public=%s)", record.id, record.reward_score, record.is_public)
        return record.id

    @staticmethod
    def _record_to_dict(record: CognitiveTraceRecord, include_raw_query: bool = False) -> dict[str, Any]:
        ir_json = record.successful_ir_json or {}
        variables = ir_json.get("variables", [])
        constraints = ir_json.get("constraints", [])

        # Sanitize query to prevent prompt injection or cross-user privacy leaks
        safe_query_description = (
            record.raw_user_query
            if (include_raw_query or record.is_public)
            else f"Archetyp problemu ({len(variables)} zmiennych, {len(constraints)} ograniczeń, solver: {record.winning_solver})"
        )

        return {
            "id": record.id,
            "created_at": record.created_at.isoformat() if record.created_at else "",
            "problem_fingerprint": record.problem_fingerprint,
            "raw_user_query": safe_query_description,
            "successful_ir_json": record.successful_ir_json,
            "winning_solver": record.winning_solver,
            "penalty_multipliers": record.penalty_multipliers,
            "reward_score": record.reward_score,
            "lessons_learned": record.lessons_learned,
            "is_public": record.is_public,
            "owner_id": record.owner_id,
            "workspace_id": record.workspace_id,
        }
