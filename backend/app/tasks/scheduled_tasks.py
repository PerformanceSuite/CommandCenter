"""
Schedule dispatcher tasks for Celery Beat integration.

This module provides tasks for automatically executing scheduled jobs including:
- Schedule dispatcher (finds and executes due schedules)
- Schedule cleanup (disables expired schedules)
- Schedule monitoring (tracks execution health)
"""

import logging
from datetime import datetime
from typing import Dict, Any

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.scheduled_tasks.dispatch_due_schedules")
def dispatch_due_schedules(self, limit: int = 100) -> Dict[str, Any]:
    """
    Find and execute all schedules that are due for execution.

    This task should be called periodically by Celery Beat (e.g., every minute).
    It finds all enabled schedules that are due for execution and dispatches them.

    Args:
        self: Celery task instance (bound)
        limit: Maximum number of schedules to process

    Returns:
        dict: Summary of dispatched schedules
    """
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        async_sessionmaker,
        AsyncSession,
    )
    from app.config import settings
    from app.services.schedule_service import ScheduleService
    import asyncio

    # Create async database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def run_dispatcher():
        """Inner async function to run the dispatcher."""
        async with async_session() as session:
            service = ScheduleService(session)

            try:
                # Get due schedules
                logger.info(f"Checking for due schedules (limit={limit})")
                due_schedules = await service.get_due_schedules(limit=limit)

                dispatched = []
                failed = []

                # Execute each due schedule
                for schedule in due_schedules:
                    try:
                        logger.info(
                            f"Executing schedule {schedule.id} ({schedule.name})"
                        )
                        job = await service.execute_schedule(schedule.id)

                        dispatched.append(
                            {
                                "schedule_id": schedule.id,
                                "schedule_name": schedule.name,
                                "job_id": job.id,
                                "task_type": schedule.task_type,
                                "next_run": (
                                    schedule.next_run_at.isoformat()
                                    if schedule.next_run_at
                                    else None
                                ),
                            }
                        )

                        # Record success
                        await service.record_execution_result(
                            schedule_id=schedule.id,
                            success=True,
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to execute schedule {schedule.id}: {e}",
                            exc_info=True,
                        )
                        failed.append(
                            {
                                "schedule_id": schedule.id,
                                "schedule_name": schedule.name,
                                "error": str(e),
                            }
                        )

                        # Record failure
                        await service.record_execution_result(
                            schedule_id=schedule.id,
                            success=False,
                            error=str(e),
                        )

                result = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_due": len(due_schedules),
                    "dispatched": len(dispatched),
                    "failed": len(failed),
                    "schedules": dispatched,
                    "errors": failed,
                }

                logger.info(
                    f"Schedule dispatcher completed: {len(dispatched)} dispatched, "
                    f"{len(failed)} failed"
                )

                return result

            except Exception as e:
                logger.error(f"Schedule dispatcher failed: {e}", exc_info=True)
                raise

    # Run the async dispatcher
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(run_dispatcher())


@celery_app.task(bind=True, name="app.tasks.scheduled_tasks.cleanup_expired_schedules")
def cleanup_expired_schedules(self) -> Dict[str, Any]:
    """
    Disable schedules that have passed their end_time.

    This task should be run periodically (e.g., daily) to clean up
    expired schedules and keep the database tidy.

    Args:
        self: Celery task instance (bound)

    Returns:
        dict: Summary of cleaned up schedules
    """
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        async_sessionmaker,
        AsyncSession,
    )
    from sqlalchemy import select, and_
    from app.config import settings
    from app.models import Schedule
    import asyncio

    # Create async database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def run_cleanup():
        """Inner async function to run the cleanup."""
        async with async_session() as session:
            try:
                now = datetime.utcnow()

                # Find expired schedules
                result = await session.execute(
                    select(Schedule).where(
                        and_(
                            Schedule.enabled == True,
                            Schedule.end_time.isnot(None),
                            Schedule.end_time <= now,
                        )
                    )
                )
                expired_schedules = result.scalars().all()

                disabled_count = 0
                disabled_schedules = []

                # Disable each expired schedule
                for schedule in expired_schedules:
                    schedule.enabled = False
                    disabled_count += 1

                    disabled_schedules.append(
                        {
                            "schedule_id": schedule.id,
                            "schedule_name": schedule.name,
                            "end_time": schedule.end_time.isoformat(),
                        }
                    )

                    logger.info(
                        f"Disabled expired schedule {schedule.id} ({schedule.name})"
                    )

                await session.commit()

                result = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "disabled_count": disabled_count,
                    "schedules": disabled_schedules,
                }

                logger.info(
                    f"Schedule cleanup completed: {disabled_count} schedules disabled"
                )

                return result

            except Exception as e:
                logger.error(f"Schedule cleanup failed: {e}", exc_info=True)
                raise

    # Run the async cleanup
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(run_cleanup())


@celery_app.task(bind=True, name="app.tasks.scheduled_tasks.monitor_schedule_health")
def monitor_schedule_health(self) -> Dict[str, Any]:
    """
    Monitor schedule execution health and alert on issues.

    This task checks for:
    - Schedules with high failure rates
    - Schedules that haven't run in a long time
    - Schedules with consecutive failures

    Args:
        self: Celery task instance (bound)

    Returns:
        dict: Health report with any issues found
    """
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        async_sessionmaker,
        AsyncSession,
    )
    from sqlalchemy import select
    from app.config import settings
    from app.models import Schedule
    from datetime import timedelta
    import asyncio

    # Create async database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def run_monitor():
        """Inner async function to run the monitor."""
        async with async_session() as session:
            try:
                now = datetime.utcnow()
                issues = []

                # Get all enabled schedules
                result = await session.execute(
                    select(Schedule).where(Schedule.enabled == True)
                )
                schedules = result.scalars().all()

                for schedule in schedules:
                    # Check failure rate
                    if (
                        schedule.run_count > 10
                        and schedule.success_rate
                        and schedule.success_rate < 50
                    ):
                        issues.append(
                            {
                                "schedule_id": schedule.id,
                                "schedule_name": schedule.name,
                                "issue_type": "high_failure_rate",
                                "details": f"Success rate: {schedule.success_rate:.1f}%",
                                "severity": "warning",
                            }
                        )

                    # Check if schedule hasn't run recently
                    if schedule.last_run_at:
                        time_since_run = now - schedule.last_run_at
                        # Alert if hasn't run in 7 days (for non-once schedules)
                        if schedule.frequency != "once" and time_since_run > timedelta(
                            days=7
                        ):
                            issues.append(
                                {
                                    "schedule_id": schedule.id,
                                    "schedule_name": schedule.name,
                                    "issue_type": "stale_schedule",
                                    "details": f"Last run: {schedule.last_run_at.isoformat()}",
                                    "severity": "info",
                                }
                            )

                    # Check consecutive failures (last 3 runs all failed)
                    if (
                        schedule.run_count >= 3
                        and schedule.last_failure_at
                        and schedule.last_success_at
                        and schedule.last_failure_at > schedule.last_success_at
                    ):
                        # Check if multiple recent failures
                        recent_failure_threshold = schedule.run_count - 3
                        if schedule.success_count <= recent_failure_threshold:
                            issues.append(
                                {
                                    "schedule_id": schedule.id,
                                    "schedule_name": schedule.name,
                                    "issue_type": "consecutive_failures",
                                    "details": f"Last error: {schedule.last_error[:100] if schedule.last_error else 'Unknown'}",
                                    "severity": "critical",
                                }
                            )

                # Group issues by severity
                critical = [i for i in issues if i["severity"] == "critical"]
                warnings = [i for i in issues if i["severity"] == "warning"]
                info = [i for i in issues if i["severity"] == "info"]

                result = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_schedules": len(schedules),
                    "total_issues": len(issues),
                    "critical_issues": len(critical),
                    "warnings": len(warnings),
                    "info": len(info),
                    "issues": {
                        "critical": critical,
                        "warning": warnings,
                        "info": info,
                    },
                }

                if critical:
                    logger.warning(f"Found {len(critical)} critical schedule issues")
                elif warnings:
                    logger.info(f"Found {len(warnings)} schedule warnings")

                logger.info(
                    f"Schedule health monitoring completed: {len(issues)} total issues"
                )

                return result

            except Exception as e:
                logger.error(f"Schedule health monitoring failed: {e}", exc_info=True)
                raise

    # Run the async monitor
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(run_monitor())


@celery_app.task(bind=True, name="app.tasks.scheduled_tasks.execute_single_schedule")
def execute_single_schedule(self, schedule_id: int) -> Dict[str, Any]:
    """
    Execute a single schedule manually or via Celery Beat.

    This task can be used for:
    - Manual schedule execution
    - Celery Beat periodic task entry points
    - Testing schedule execution

    Args:
        self: Celery task instance (bound)
        schedule_id: Schedule ID to execute

    Returns:
        dict: Execution result
    """
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        async_sessionmaker,
        AsyncSession,
    )
    from sqlalchemy import select
    from app.config import settings
    from app.services.schedule_service import ScheduleService
    from app.models import Schedule
    import asyncio

    # Create async database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def run_execution():
        """Inner async function to run the execution."""
        async with async_session() as session:
            service = ScheduleService(session)

            try:
                logger.info(f"Executing schedule {schedule_id}")
                job = await service.execute_schedule(schedule_id)

                # Get updated schedule for stats
                result = await session.execute(
                    select(Schedule).where(Schedule.id == schedule_id)
                )
                schedule = result.scalar_one_or_none()

                # Record success
                await service.record_execution_result(
                    schedule_id=schedule_id,
                    success=True,
                )

                result_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "schedule_id": schedule_id,
                    "schedule_name": schedule.name if schedule else None,
                    "job_id": job.id,
                    "status": "success",
                    "next_run": (
                        schedule.next_run_at.isoformat()
                        if schedule and schedule.next_run_at
                        else None
                    ),
                }

                logger.info(
                    f"Successfully executed schedule {schedule_id}, created job {job.id}"
                )

                return result_data

            except Exception as e:
                logger.error(
                    f"Failed to execute schedule {schedule_id}: {e}", exc_info=True
                )

                # Record failure
                await service.record_execution_result(
                    schedule_id=schedule_id,
                    success=False,
                    error=str(e),
                )

                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "schedule_id": schedule_id,
                    "status": "failed",
                    "error": str(e),
                }

    # Run the async execution
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(run_execution())
