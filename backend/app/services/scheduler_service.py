"""
Scheduler Service - APScheduler Integration

Provides scheduling functionality for automated agent task execution.
Uses APScheduler with PostgreSQL datastore for persistent job storage.

Features:
- Schedule tasks to run at specific datetime
- Persistent job storage (survives restarts)
- Task cancellation
- Background execution via FastAPI lifespan
"""

import logging
import os
import ssl
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs

from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncScheduler] = None
_scheduler_started = False


def _prepare_async_url(database_url: str) -> tuple[str, dict]:
    """
    Prepare database URL for asyncpg.

    Removes query parameters that asyncpg doesn't support (like sslmode)
    and returns the clean URL with appropriate connect_args.

    Args:
        database_url: Original database URL

    Returns:
        Tuple of (clean_url, connect_args)
    """
    # Parse URL
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query) if parsed.query else {}

    # Remove query parameters from URL for asyncpg
    base_url = database_url.split("?")[0] if "?" in database_url else database_url

    # Build connect_args based on SSL settings
    connect_args = {}

    # Check for SSL mode
    sslmode = query_params.get("sslmode", [None])[0]
    if sslmode and sslmode != "disable":
        # For asyncpg, use ssl=True or ssl context
        connect_args["ssl"] = True

    return base_url, connect_args


class SchedulerService:
    """
    Manages APScheduler for scheduled task execution.

    Uses PostgreSQL as datastore for persistent job storage.
    Jobs survive application restarts.
    """

    def __init__(self, database_url: str):
        """
        Initialize scheduler with PostgreSQL datastore.

        Args:
            database_url: PostgreSQL connection string (async format)
        """
        self.database_url = database_url
        self._engine: Optional[AsyncEngine] = None
        self._scheduler: Optional[AsyncScheduler] = None
        self._started = False

        logger.info(f"[Scheduler] Initialized with database URL: {database_url[:50]}...")

    async def start(self) -> None:
        """Start the scheduler in background mode."""
        if self._started:
            logger.warning("[Scheduler] Already started, skipping...")
            return

        try:
            # Prepare URL for asyncpg (remove sslmode query param)
            clean_url, connect_args = _prepare_async_url(self.database_url)

            # Create async engine for APScheduler
            # Use same database as main app
            self._engine = create_async_engine(
                clean_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                connect_args=connect_args,
            )

            # Create SQLAlchemy datastore
            data_store = SQLAlchemyDataStore(self._engine)

            # Create scheduler
            self._scheduler = AsyncScheduler(data_store)

            # Enter async context and start in background
            await self._scheduler.__aenter__()
            await self._scheduler.start_in_background()

            self._started = True
            logger.info("[Scheduler] Started successfully in background mode")

        except Exception as e:
            logger.error(f"[Scheduler] Failed to start: {e}", exc_info=True)
            raise

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if not self._started or not self._scheduler:
            return

        try:
            await self._scheduler.__aexit__(None, None, None)
            self._started = False
            logger.info("[Scheduler] Stopped successfully")
        except Exception as e:
            logger.error(f"[Scheduler] Error stopping: {e}")

    async def schedule_task(
        self,
        task_id: str,
        run_time: datetime,
        task_func: Any,
        **kwargs
    ) -> str:
        """
        Schedule a task to run at a specific time.

        Args:
            task_id: Unique task identifier
            run_time: When to execute the task
            task_func: Async function to execute
            **kwargs: Additional arguments for the task function

        Returns:
            APScheduler job ID
        """
        if not self._scheduler or not self._started:
            raise RuntimeError("Scheduler not started")

        job_id = f"scheduled_task_{task_id}"

        # Ensure run_time is timezone-aware
        if run_time.tzinfo is None:
            run_time = run_time.replace(tzinfo=timezone.utc)

        logger.info(f"[Scheduler] Scheduling task {task_id} for {run_time}")

        await self._scheduler.add_schedule(
            task_func,
            DateTrigger(run_time=run_time),
            id=job_id,
            args=[task_id],  # Pass task_id to executor
            kwargs=kwargs,
        )

        logger.info(f"[Scheduler] Task {task_id} scheduled with job_id: {job_id}")
        return job_id

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending scheduled task.

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled, False if not found
        """
        if not self._scheduler or not self._started:
            raise RuntimeError("Scheduler not started")

        job_id = f"scheduled_task_{task_id}"

        try:
            await self._scheduler.remove_schedule(job_id)
            logger.info(f"[Scheduler] Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.warning(f"[Scheduler] Could not cancel task {task_id}: {e}")
            return False

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._started


# ============================================================================
# Global Scheduler Instance Management
# ============================================================================

def get_scheduler() -> Optional[SchedulerService]:
    """Get the global scheduler instance."""
    global _scheduler
    return _scheduler


async def initialize_scheduler(database_url: str) -> SchedulerService:
    """
    Initialize and start the global scheduler.

    Should be called during FastAPI startup.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        SchedulerService instance
    """
    global _scheduler, _scheduler_started

    if _scheduler is not None and _scheduler_started:
        logger.info("[Scheduler] Already initialized, returning existing instance")
        return _scheduler

    # Convert sync URL to async if needed
    async_url = database_url
    if database_url.startswith("postgresql://"):
        async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        async_url = database_url.replace("postgres://", "postgresql+asyncpg://")

    _scheduler = SchedulerService(async_url)
    await _scheduler.start()
    _scheduler_started = True

    return _scheduler


async def shutdown_scheduler() -> None:
    """
    Shutdown the global scheduler.

    Should be called during FastAPI shutdown.
    """
    global _scheduler, _scheduler_started

    if _scheduler:
        await _scheduler.stop()
        _scheduler = None
        _scheduler_started = False
        logger.info("[Scheduler] Global scheduler shutdown complete")
