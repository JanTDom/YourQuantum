"""YourQuantum — database setup (async SQLite for local dev, PostgreSQL for Supabase/production)."""
from __future__ import annotations

import os
from pathlib import Path

from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.models import Base

DB_PATH = os.environ.get("YQ_DB_PATH", str(Path(__file__).parent.parent.parent / "data" / "yourquantum.db"))

raw_url = os.environ.get("DATABASE_URL")
if not raw_url:
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
else:
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+asyncpg://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Clean query string parameters not supported directly by asyncpg (like pgbouncer=true)
    if "?" in raw_url:
        base_part, query_part = raw_url.split("?", 1)
        params = [p for p in query_part.split("&") if not p.startswith("pgbouncer=")]
        raw_url = base_part + ("?" + "&".join(params) if params else "")
    DATABASE_URL = raw_url

connect_args: dict[str, Any] = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "postgresql" in DATABASE_URL:
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

import asyncio

_db_initialized = False
_db_init_lock: asyncio.Lock | None = None


def _get_init_lock() -> asyncio.Lock:
    global _db_init_lock
    if _db_init_lock is None:
        _db_init_lock = asyncio.Lock()
    return _db_init_lock


async def ensure_db_initialized() -> None:
    """Ensure tables exist, especially in serverless runtimes where lifespan does not run."""
    global _db_initialized
    if not _db_initialized:
        async with _get_init_lock():
            if not _db_initialized:
                await init_db()
                _db_initialized = True


async def init_db() -> None:
    """Create tables if they don't exist and ensure schema migrations."""
    if DATABASE_URL.startswith("sqlite"):
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass

    # Explicit DDL fallback to guarantee tables exist even if catalog reflection behaves unexpectedly
    table_ddls = [
        """CREATE TABLE IF NOT EXISTS problems (
            id VARCHAR(36) PRIMARY KEY,
            schema_version VARCHAR(10) DEFAULT '0.2',
            version INTEGER DEFAULT 1,
            parent_id VARCHAR(36),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            description_raw TEXT,
            description_formalised TEXT DEFAULT '',
            mode VARCHAR(20) DEFAULT 'optimize',
            approved BOOLEAN DEFAULT FALSE,
            approved_at TIMESTAMP WITH TIME ZONE,
            ir_json JSON DEFAULT '{}'
        )""",
        """CREATE TABLE IF NOT EXISTS jobs (
            id VARCHAR(36) PRIMARY KEY,
            problem_id VARCHAR(36),
            solver_name VARCHAR(50),
            execution_status VARCHAR(20) DEFAULT 'QUEUED',
            math_status VARCHAR(20),
            source VARCHAR(40),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            solve_time_seconds FLOAT,
            objective_value FLOAT,
            error_message TEXT,
            publication_status VARCHAR(30) DEFAULT 'PENDING_VERIFICATION',
            result_json JSON,
            verification_json JSON,
            budget_json JSON,
            metadata_json JSON DEFAULT '{}'
        )""",
        """CREATE TABLE IF NOT EXISTS cases (
            id VARCHAR(36) PRIMARY KEY,
            title VARCHAR(255),
            context TEXT,
            status VARCHAR(30) DEFAULT 'intake',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            problem_ir_id VARCHAR(36),
            case_json JSON DEFAULT '{}'
        )""",
        """CREATE TABLE IF NOT EXISTS cognitive_traces (
            id VARCHAR(36) PRIMARY KEY,
            owner_id VARCHAR(36),
            workspace_id VARCHAR(36),
            is_public BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            problem_fingerprint VARCHAR(128),
            raw_user_query TEXT,
            successful_ir_json JSON DEFAULT '{}',
            winning_solver VARCHAR(50) DEFAULT 'unknown',
            penalty_multipliers JSON DEFAULT '{}',
            reward_score FLOAT DEFAULT 1.0,
            lessons_learned TEXT DEFAULT ''
        )""",
        """CREATE TABLE IF NOT EXISTS cognitive_sessions (
            id VARCHAR(36) PRIMARY KEY,
            owner_id VARCHAR(36),
            workspace_id VARCHAR(36),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            working_memory_json JSON DEFAULT '{}',
            energy_budget_json JSON DEFAULT '{}',
            history_json JSON DEFAULT '[]'
        )""",
    ]
    for ddl in table_ddls:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(ddl))
        except Exception:
            pass

    # In PostgreSQL, execute each ALTER TABLE in its own transaction so one failure doesn't abort the entire block
    migrations = [
        "ALTER TABLE jobs ADD COLUMN publication_status VARCHAR(30) DEFAULT 'PENDING_VERIFICATION'",
        "ALTER TABLE cognitive_traces ADD COLUMN owner_id VARCHAR(36)",
        "ALTER TABLE cognitive_traces ADD COLUMN workspace_id VARCHAR(36)",
        "ALTER TABLE cognitive_traces ADD COLUMN is_public BOOLEAN DEFAULT FALSE",
        "ALTER TABLE cognitive_sessions ADD COLUMN energy_budget_json JSON DEFAULT '{}'",
    ]
    for sql in migrations:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(sql))
        except Exception:
            pass


async def get_session() -> AsyncSession:
    await ensure_db_initialized()
    async with async_session_factory() as session:
        yield session


