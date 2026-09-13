"""
YourQuantum — SQLAlchemy ORM Models
Database: SQLite (async via aiosqlite) for MVP.
PostgreSQL in production.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class ProblemRecord(Base):
    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    schema_version: Mapped[str] = mapped_column(String(10), default="0.2")
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    description_raw: Mapped[str] = mapped_column(Text)
    description_formalised: Mapped[str] = mapped_column(Text, default="")
    mode: Mapped[str] = mapped_column(String(20), default="optimize")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Full ProblemIR stored as JSON
    ir_json: Mapped[dict] = mapped_column(JSON, default=dict)


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    problem_id: Mapped[str] = mapped_column(String(36))
    solver_name: Mapped[str] = mapped_column(String(50))
    execution_status: Mapped[str] = mapped_column(String(20), default="QUEUED")
    math_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source: Mapped[str | None] = mapped_column(String(40), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    solve_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    objective_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Publication gate: PENDING_VERIFICATION | PUBLISHED_VERIFIED | REJECTED_UNVERIFIED | UNVERIFIED
    publication_status: Mapped[str] = mapped_column(String(30), default="PENDING_VERIFICATION")

    # Full solver result stored as JSON
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Verification report stored as JSON
    verification_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    budget_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class CaseRecord(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(255))
    context: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="intake")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    problem_ir_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    case_json: Mapped[dict] = mapped_column(JSON, default=dict)


class CognitiveTraceRecord(Base):
    __tablename__ = "cognitive_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    problem_fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    raw_user_query: Mapped[str] = mapped_column(Text)
    successful_ir_json: Mapped[dict] = mapped_column(JSON, default=dict)
    winning_solver: Mapped[str] = mapped_column(String(50), default="unknown")
    penalty_multipliers: Mapped[dict] = mapped_column(JSON, default=dict)
    reward_score: Mapped[float] = mapped_column(Float, default=1.0)
    lessons_learned: Mapped[str] = mapped_column(Text, default="")


class CognitiveSessionRecord(Base):
    __tablename__ = "cognitive_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Serialized WorkingMemory state
    working_memory_json: Mapped[dict] = mapped_column(JSON, default=dict)
    # Serialized EnergyBudget state
    energy_budget_json: Mapped[dict] = mapped_column(JSON, default=dict)
    # List of interaction history turns / formalizations
    history_json: Mapped[list] = mapped_column(JSON, default=list)

