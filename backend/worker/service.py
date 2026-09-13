"""
YourQuantum — Dedicated Compute Worker Service (DEC-022)
Pulls jobs in QUEUED status from the database, runs the full solver suite,
and updates job status with verification certificates.
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from sqlalchemy import select

from backend.db import async_session_factory, init_db
from backend.models import JobRecord, ExecutionStatus
from backend.worker.runner import _run_job

logger = logging.getLogger("yq_worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class WorkerService:
    def __init__(self, poll_interval: float = 1.0) -> None:
        self.poll_interval = poll_interval
        self._running = True

    def stop(self) -> None:
        logger.info("Worker shutting down gracefully...")
        self._running = False

    async def fetch_next_queued_job_id(self) -> str | None:
        async with async_session_factory() as session:
            stmt = (
                select(JobRecord.id)
                .where(JobRecord.execution_status == ExecutionStatus.QUEUED.value)
                .order_by(JobRecord.created_at.asc())
                .limit(1)
            )
            result = await session.execute(stmt)
            row = result.first()
            return row[0] if row else None

    async def run(self) -> None:
        logger.info("Starting YourQuantum Dedicated Compute Worker Service...")
        await init_db()
        while self._running:
            try:
                job_id = await self.fetch_next_queued_job_id()
                if job_id:
                    logger.info(f"Worker picked up job {job_id}")
                    await _run_job(job_id)
                else:
                    await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing jobs in worker loop: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)


async def main() -> None:
    service = WorkerService()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, service.stop)
        except (NotImplementedError, RuntimeError):
            pass
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
