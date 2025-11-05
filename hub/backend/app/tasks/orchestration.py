"""Celery tasks for project orchestration operations"""
import asyncio
import logging
from typing import Any

from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.services.orchestration_service import OrchestrationService

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run async coroutine in sync Celery task"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def start_project_task(self, project_id: int) -> dict[str, Any]:
    """
    Start CommandCenter project via Dagger (background task)

    Args:
        project_id: ID of project to start

    Returns:
        dict with success, project_id, and result or error
    """
    try:
        # Update state: Initializing (only if running as Celery task)
        if self and hasattr(self, 'update_state'):
            self.update_state(
                state='BUILDING',
                meta={'step': 'Initializing Dagger client...', 'progress': 10}
            )

        async def _start():
            async with AsyncSessionLocal() as db:
                service = OrchestrationService(db)

                # Update state: Building containers
                if self and hasattr(self, 'update_state'):
                    self.update_state(
                        state='BUILDING',
                        meta={
                            'step': 'Building containers (this may take 20-30 min)...',
                            'progress': 30
                        }
                    )

                # Run Dagger orchestration
                result = await service.start_project(project_id)

                # Update state: Starting services
                if self and hasattr(self, 'update_state'):
                    self.update_state(
                        state='RUNNING',
                        meta={'step': 'Starting services...', 'progress': 80}
                    )

                return result

        result = _run_async(_start())

        return {
            "success": True,
            "project_id": project_id,
            "result": result
        }

    except Exception as e:
        logger.error(f"Failed to start project {project_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_id": project_id
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def stop_project_task(self, project_id: int) -> dict[str, Any]:
    """
    Stop CommandCenter project (background task)

    Args:
        project_id: ID of project to stop

    Returns:
        dict with success, project_id, and result or error
    """
    try:
        # Update state: Stopping
        if self and hasattr(self, 'update_state'):
            self.update_state(
                state='STOPPING',
                meta={'step': 'Stopping services...', 'progress': 50}
            )

        async def _stop():
            async with AsyncSessionLocal() as db:
                service = OrchestrationService(db)
                result = await service.stop_project(project_id)
                return result

        result = _run_async(_stop())

        return {
            "success": True,
            "project_id": project_id,
            "result": result
        }

    except Exception as e:
        logger.error(f"Failed to stop project {project_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_id": project_id
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def restart_project_task(
    self,
    project_id: int,
    service_name: str
) -> dict[str, Any]:
    """
    Restart specific service in CommandCenter project (background task)

    Args:
        project_id: ID of project
        service_name: Name of service to restart

    Returns:
        dict with success, project_id, and result or error
    """
    try:
        # Update state: Restarting
        if self and hasattr(self, 'update_state'):
            self.update_state(
                state='RESTARTING',
                meta={'step': f'Restarting {service_name}...', 'progress': 50}
            )

        async def _restart():
            async with AsyncSessionLocal() as db:
                service = OrchestrationService(db)
                result = await service.restart_service(project_id, service_name)
                return result

        result = _run_async(_restart())

        return {
            "success": True,
            "project_id": project_id,
            "result": result
        }

    except Exception as e:
        logger.error(
            f"Failed to restart service {service_name} "
            f"for project {project_id}: {e}"
        )
        return {
            "success": False,
            "error": str(e),
            "project_id": project_id
        }


@celery_app.task(bind=True)
def get_project_logs_task(
    self,
    project_id: int,
    service_name: str,
    lines: int = 100
) -> dict[str, Any]:
    """
    Retrieve service logs from CommandCenter project (background task)

    Args:
        project_id: ID of project
        service_name: Name of service
        lines: Number of log lines to retrieve (default: 100)

    Returns:
        dict with success, project_id, and logs or error
    """
    try:
        # Update state: Fetching logs
        if self and hasattr(self, 'update_state'):
            self.update_state(
                state='FETCHING',
                meta={'step': f'Fetching {lines} lines from {service_name}...', 'progress': 50}
            )

        async def _get_logs():
            async with AsyncSessionLocal() as db:
                service = OrchestrationService(db)
                logs = await service.get_service_logs(project_id, service_name, lines)
                return logs

        logs = _run_async(_get_logs())

        return {
            "success": True,
            "project_id": project_id,
            "logs": logs
        }

    except Exception as e:
        logger.error(
            f"Failed to get logs for service {service_name} "
            f"in project {project_id}: {e}"
        )
        return {
            "success": False,
            "error": str(e),
            "project_id": project_id
        }
