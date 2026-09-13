"""
Unit tests for Episodic Memory (Hippocampal Subsystem).
Tests async database persistence and associative recall with SQLite.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.models import Base
from backend.domain.cognitive.episodic_memory import EpisodicMemoryRepository


@pytest_asyncio.fixture
async def async_test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_episodic_memory_consolidation_and_recall(async_test_session: AsyncSession):
    repo = EpisodicMemoryRepository()

    # 1. Consolidate high-reward trace
    trace_id_1 = await repo.consolidate_trace(
        session=async_test_session,
        trace_data={
            "problem_fingerprint": "fp_knapsack_logistics",
            "raw_user_query": "Pakowanie paczek do ciezarowki z limitem wagi",
            "successful_ir_json": {"variables": ["item_1", "item_2"], "budget": 100},
            "winning_solver": "cpsat",
            "penalty_multipliers": {"c1": 50.0},
            "reward_score": 1.0,
            "lessons_learned": "Solver CP-SAT znalazl optimum w 0.02s",
        },
    )
    assert trace_id_1 is not None

    # 2. Consolidate second trace with lower reward
    trace_id_2 = await repo.consolidate_trace(
        session=async_test_session,
        trace_data={
            "problem_fingerprint": "fp_knapsack_logistics",
            "raw_user_query": "Druga instancja pakowania paczek",
            "successful_ir_json": {"variables": ["item_a"], "budget": 50},
            "winning_solver": "qaoa_aer",
            "penalty_multipliers": {},
            "reward_score": 0.85,
            "lessons_learned": "Wymagalo 2 cykli refleksji",
        },
    )
    assert trace_id_2 is not None

    # 3. Consolidate a different domain trace
    await repo.consolidate_trace(
        session=async_test_session,
        trace_data={
            "problem_fingerprint": "fp_portfolio_finance",
            "raw_user_query": "Alokacja portfela akcji",
            "successful_ir_json": {"variables": ["stock_x", "stock_y"]},
            "winning_solver": "cpsat",
            "reward_score": 0.95,
        },
    )

    # 4. Recall exact fingerprint match: should return 2 records sorted by reward_score DESC
    recalled = await repo.recall_analogies(async_test_session, fingerprint="fp_knapsack_logistics", limit=3)
    assert len(recalled) == 2
    assert recalled[0]["id"] == trace_id_1
    assert recalled[0]["reward_score"] == 1.0
    assert recalled[1]["id"] == trace_id_2
    assert recalled[1]["reward_score"] == 0.85

    # 5. Recall with limit=1
    recalled_limit = await repo.recall_analogies(async_test_session, fingerprint="fp_knapsack_logistics", limit=1)
    assert len(recalled_limit) == 1
    assert recalled_limit[0]["id"] == trace_id_1

    # 6. Fallback recall for unseen fingerprint
    fallback_recalled = await repo.recall_analogies(async_test_session, fingerprint="fp_unseen_domain", limit=2)
    assert len(fallback_recalled) == 2
    # Should recall high-reward traces as general exemplars
    assert fallback_recalled[0]["reward_score"] >= 0.8
