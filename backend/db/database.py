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


async def init_db() -> None:
    """Create tables if they don't exist and ensure schema migrations."""
    if DATABASE_URL.startswith("sqlite"):
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE jobs ADD COLUMN publication_status VARCHAR(30) DEFAULT 'PENDING_VERIFICATION'"))
        except Exception:
            pass  # Already exists

        for col, col_type in [
            ("owner_id", "VARCHAR(36)"),
            ("workspace_id", "VARCHAR(36)"),
            ("is_public", "BOOLEAN DEFAULT 0"),
        ]:
            try:
                await conn.execute(text(f"ALTER TABLE cognitive_traces ADD COLUMN {col} {col_type}"))
            except Exception:
                pass

        try:
            await conn.execute(text("ALTER TABLE cognitive_sessions ADD COLUMN energy_budget_json JSON DEFAULT '{}'"))
        except Exception:
            pass



async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

