"""
YourQuantum — Async Job Runner
Executes solver jobs as asyncio background tasks with:
- Time limits (enforced via asyncio.wait_for)
- Status tracking in the database
- Independent verification after each solver run
- Honest result recording
"""
from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import async_session_factory
from backend.db.models import JobRecord, ProblemRecord
from backend.domain.problem_ir import ComputeBudget, ProblemIR
from backend.solvers.base import ExecutionStatus, SolverAdapter, SolverResult
from backend.solvers.cpsat import CPSATAdapter
from backend.solvers.quantum.qaoa import QAOAAdapter
from backend.verifier.verifier import IndependentVerifier, SolverCandidate

logger = logging.getLogger(__name__)

# Registry of available solver adapters
SOLVER_REGISTRY: list[SolverAdapter] = [
    CPSATAdapter(),
    QAOAAdapter(),
]


def _solver_result_to_json(result: SolverResult) -> dict:
    """Convert SolverResult dataclass to a JSON-serialisable dict."""
    import enum
    raw = dataclasses.asdict(result)

    def _make_serialisable(obj: object) -> object:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, enum.Enum):
            return obj.value
        if isinstance(obj, dict):
            return {k: _make_serialisable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_make_serialisable(item) for item in obj]
        return obj

    return _make_serialisable(raw)  # type: ignore[return-value]


def get_adapter_by_name(name: str) -> SolverAdapter | None:
    return next((a for a in SOLVER_REGISTRY if a.name == name), None)


async def enqueue_job(
    problem_id: str,
    solver_name: str,
    budget: ComputeBudget,
) -> str:
    """Create a job record and schedule it for background execution."""
    job_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        job = JobRecord(
            id=job_id,
            problem_id=problem_id,
            solver_name=solver_name,
            execution_status=ExecutionStatus.QUEUED.value,
            budget_json=budget.model_dump(),
        )
        session.add(job)
        await session.commit()

    # Schedule as background task (fire-and-forget from caller's perspective)
    asyncio.create_task(_run_job(job_id), name=f"job-{job_id[:8]}")
    return job_id


async def _run_job(job_id: str) -> None:
    """Execute a solver job with status tracking and verification."""
    async with async_session_factory() as session:
        job = await session.get(JobRecord, job_id)
        if job is None:
            logger.error(f"Job {job_id} not found.")
            return

        problem_rec = await session.get(ProblemRecord, job.problem_id)
        if problem_rec is None:
            await _fail_job(session, job, "Problem record not found.")
            return

        # Mark as running
        job.execution_status = ExecutionStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

    try:
        ir_data = await _get_problem_ir_json(job.problem_id)
        if problem_rec.approved:
            ir_data["approved"] = True
            if problem_rec.approved_at:
                ir_data["approved_at"] = problem_rec.approved_at.isoformat()
        problem = ProblemIR.model_validate(ir_data)
        budget = ComputeBudget.model_validate(job.budget_json or {})
    except Exception as e:
        async with async_session_factory() as session:
            job = await session.get(JobRecord, job_id)
            await _fail_job(session, job, f"Failed to deserialise problem: {e}")
        return

    adapter = get_adapter_by_name(job.solver_name)
    if adapter is None:
        async with async_session_factory() as session:
            job = await session.get(JobRecord, job_id)
            await _fail_job(session, job, f"Unknown solver: {job.solver_name!r}")
        return

    # Run solver in thread pool to avoid blocking event loop
    loop = asyncio.get_event_loop()
    try:
        result: SolverResult = await asyncio.wait_for(
            loop.run_in_executor(None, adapter.solve, problem, budget),
            timeout=budget.wall_time_seconds + 5,  # small grace period
        )
    except asyncio.TimeoutError:
        async with async_session_factory() as session:
            job = await session.get(JobRecord, job_id)
            await _fail_job(session, job, "Job exceeded wall time budget.")
        return
    except Exception as e:
        async with async_session_factory() as session:
            job = await session.get(JobRecord, job_id)
            await _fail_job(session, job, f"Solver raised: {e}")
        return

    # Independent verification
    verification_json: dict | None = None
    publication_status = "UNVERIFIED"

    if result.assignment:
        try:
            verifier = IndependentVerifier(problem)
            candidate = SolverCandidate(
                candidate_id=result.candidate_id,
                assignment=result.assignment,
                claimed_objective=result.objective_value,
                claimed_status=result.math_status.value.lower(),
            )
            report = verifier.verify(candidate)
            verification_json = report.model_dump(mode="json")
            if report.verdict.value.upper() == "PASS":
                publication_status = "PUBLISHED_VERIFIED"
            else:
                publication_status = "REJECTED_UNVERIFIED"
        except Exception as e:
            logger.warning(f"Verification failed for job {job_id}: {e}")
            publication_status = "REJECTED_UNVERIFIED"
    elif result.execution_status == ExecutionStatus.FAILED:
        publication_status = "REJECTED_UNVERIFIED"

    # Persist result
    async with async_session_factory() as session:
        job = await session.get(JobRecord, job_id)
        if job is None:
            return
        job.execution_status = result.execution_status.value
        job.math_status = result.math_status.value
        job.source = result.source.value
        job.completed_at = datetime.now(timezone.utc)
        job.solve_time_seconds = result.solve_time_seconds
        job.objective_value = result.objective_value
        job.error_message = result.error_message
        job.publication_status = publication_status
        job.result_json = _solver_result_to_json(result)
        job.verification_json = verification_json
        await session.commit()

    logger.info(
        f"Job {job_id} completed: {result.execution_status.value} / "
        f"{result.math_status.value}"
    )


async def _get_problem_ir_json(problem_id: str) -> dict:
    async with async_session_factory() as session:
        rec = await session.get(ProblemRecord, problem_id)
        if rec is None:
            raise ValueError(f"Problem {problem_id} not found.")
        return rec.ir_json


async def _fail_job(session: AsyncSession, job: JobRecord, reason: str) -> None:
    job.execution_status = ExecutionStatus.FAILED.value
    job.completed_at = datetime.now(timezone.utc)
    job.error_message = reason
    await session.commit()
    logger.error(f"Job {job.id} failed: {reason}")
