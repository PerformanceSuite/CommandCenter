"""Background worker for periodic health checks."""
import asyncio
import logging
from typing import Optional, Dict, Set, TYPE_CHECKING
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.service import Service, HealthStatus
from app.models.project import Project
from app.services.health_service import HealthService
from app.config import get_hub_id

if TYPE_CHECKING:
    from app.services.event_service import EventService

logger = logging.getLogger(__name__)


class HealthCheckWorker:
    """Background worker that performs periodic health checks on services."""

    def __init__(
        self,
        health_service: Optional[HealthService] = None,
        event_service: Optional["EventService"] = None
    ):
        """Initialize the health check worker.

        Args:
            health_service: Optional health service instance
            event_service: Optional event service instance
        """
        self.health_service = health_service or HealthService(event_service)
        self.event_service = event_service
        self.hub_id = get_hub_id()
        self._running = False
        self._tasks: Dict[int, asyncio.Task] = {}
        self._check_intervals: Dict[int, int] = {}  # service_id -> interval
        self._last_summary = datetime.now(timezone.utc)
        self.summary_interval = 15  # seconds
        self._last_cleanup = datetime.now(timezone.utc)
        self.cleanup_interval = 3600  # 1 hour
        self.retention_days = 7  # Keep 7 days of history

    async def start(self):
        """Start the health check worker."""
        if self._running:
            logger.warning("Health worker already running")
            return

        self._running = True
        logger.info("Starting health check worker")

        # Start the main loop
        asyncio.create_task(self._run_loop())

        # Start the health summary publisher
        asyncio.create_task(self._publish_health_summaries())

        # Start the cleanup task
        asyncio.create_task(self._cleanup_old_records())

    async def stop(self):
        """Stop the health check worker."""
        logger.info("Stopping health check worker")
        self._running = False

        # Cancel all health check tasks
        for task in self._tasks.values():
            task.cancel()

        # Wait for all tasks to complete
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    async def _run_loop(self):
        """Main loop that manages health check tasks."""
        while self._running:
            try:
                # Get all active services that need health checks
                async with async_session_maker() as db:
                    result = await db.execute(
                        select(Service)
                        .join(Project)
                        .where(
                            and_(
                                Project.status == "running",
                                Service.health_method != None
                            )
                        )
                    )
                    services = result.scalars().all()

                # Update health check tasks
                active_service_ids = {s.id for s in services}
                await self._update_health_tasks(services, active_service_ids)

                # Sleep before next check
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in health worker loop: {e}")
                await asyncio.sleep(5)

    async def _update_health_tasks(
        self,
        services: list[Service],
        active_ids: Set[int]
    ):
        """Update health check tasks based on active services.

        Args:
            services: List of active services
            active_ids: Set of active service IDs
        """
        # Cancel tasks for services that are no longer active
        for service_id in list(self._tasks.keys()):
            if service_id not in active_ids:
                logger.info(f"Cancelling health checks for service {service_id}")
                task = self._tasks.pop(service_id, None)
                if task:
                    task.cancel()
                self._check_intervals.pop(service_id, None)

        # Start tasks for new services or update intervals
        for service in services:
            if service.id not in self._tasks:
                # Start new health check task
                logger.info(
                    f"Starting health checks for {service.name} "
                    f"(interval: {service.health_interval}s)"
                )
                task = asyncio.create_task(
                    self._health_check_loop(service.id)
                )
                self._tasks[service.id] = task
                self._check_intervals[service.id] = service.health_interval

            elif self._check_intervals[service.id] != service.health_interval:
                # Interval changed, restart task
                logger.info(
                    f"Updating health check interval for {service.name} "
                    f"({self._check_intervals[service.id]}s -> {service.health_interval}s)"
                )
                self._tasks[service.id].cancel()
                task = asyncio.create_task(
                    self._health_check_loop(service.id)
                )
                self._tasks[service.id] = task
                self._check_intervals[service.id] = service.health_interval

    async def _health_check_loop(self, service_id: int):
        """Run health checks for a specific service.

        Args:
            service_id: Service ID to check
        """
        # Add some jitter to prevent all checks happening at once
        await asyncio.sleep(service_id % 5)

        while self._running:
            try:
                async with async_session_maker() as db:
                    # Get the service
                    result = await db.execute(
                        select(Service).where(Service.id == service_id)
                    )
                    service = result.scalar_one_or_none()

                    if not service:
                        logger.warning(f"Service {service_id} not found")
                        break

                    # Perform health check
                    logger.debug(f"Checking health of {service.name}")
                    health_check = await self.health_service.check_service_health(
                        service, db
                    )

                    await db.commit()

                    # Log status changes
                    if health_check.status != HealthStatus.UP:
                        logger.warning(
                            f"Service {service.name} is {health_check.status.value}: "
                            f"{health_check.error_message or 'No error message'}"
                        )

                # Wait for next check
                interval = self._check_intervals.get(service_id, 30)
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.debug(f"Health check cancelled for service {service_id}")
                break
            except Exception as e:
                logger.error(f"Error checking health of service {service_id}: {e}")
                await asyncio.sleep(30)

    async def _publish_health_summaries(self):
        """Periodically publish health summaries to NATS."""
        while self._running:
            try:
                await asyncio.sleep(self.summary_interval)

                # Get all services with their current health
                async with async_session_maker() as db:
                    result = await db.execute(
                        select(Service, Project)
                        .join(Project)
                        .where(Project.status == "running")
                    )
                    services_with_projects = result.all()

                    # Group services by project
                    projects_health = {}
                    for service, project in services_with_projects:
                        if project.id not in projects_health:
                            projects_health[project.id] = {
                                "id": project.id,
                                "name": project.name,
                                "slug": project.slug,
                                "status": project.status,
                                "health": "healthy",
                                "services": []
                            }

                        service_info = {
                            "id": service.id,
                            "name": service.name,
                            "type": service.service_type.value if service.service_type else None,
                            "status": service.health_status.value if service.health_status else "unknown",
                            "latency_ms": service.average_latency,
                            "uptime_seconds": service.uptime_seconds,
                            "last_check": service.last_health_check.isoformat() if service.last_health_check else None
                        }

                        projects_health[project.id]["services"].append(service_info)

                        # Update project health based on required services
                        if service.is_required and service.health_status == HealthStatus.DOWN:
                            projects_health[project.id]["health"] = "unhealthy"
                        elif service.health_status == HealthStatus.DEGRADED:
                            if projects_health[project.id]["health"] == "healthy":
                                projects_health[project.id]["health"] = "degraded"

                    # Publish health summary
                    summary = {
                        "hub_id": self.hub_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "projects": list(projects_health.values()),
                        "total_services": sum(len(p["services"]) for p in projects_health.values()),
                        "healthy_services": sum(
                            1 for p in projects_health.values()
                            for s in p["services"]
                            if s["status"] in ["up", "degraded"]
                        )
                    }

                    if self.event_service:
                        await self.event_service.publish(
                            subject=f"hub.{self.hub_id}.health.summary",
                            category="health",
                            event_type="health_summary",
                            payload=summary
                        )

                        # Also publish to global topic for federation
                        await self.event_service.publish(
                            subject="hub.global.health",
                            category="health",
                            event_type="hub_health_summary",
                            payload=summary
                        )

                    logger.debug(
                        f"Published health summary: "
                        f"{summary['total_services']} services, "
                        f"{summary['healthy_services']} healthy"
                    )

            except Exception as e:
                logger.error(f"Error publishing health summary: {e}")

    async def _cleanup_old_records(self):
        """Periodically clean up old health check records."""
        while self._running:
            try:
                # Check if it's time for cleanup
                now = datetime.now(timezone.utc)
                if (now - self._last_cleanup).total_seconds() >= self.cleanup_interval:
                    # Perform cleanup
                    count = await self.health_service.cleanup_old_health_checks(
                        retention_days=self.retention_days
                    )
                    if count > 0:
                        logger.info(f"Cleaned up {count} old health check records")
                    self._last_cleanup = now

                # Sleep for 60 seconds before checking again
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error during health check cleanup: {e}")
                await asyncio.sleep(60)

    async def trigger_immediate_check(self, service_id: int) -> bool:
        """Trigger an immediate health check for a service.

        Args:
            service_id: Service ID to check

        Returns:
            True if check was triggered
        """
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(Service).where(Service.id == service_id)
                )
                service = result.scalar_one_or_none()

                if not service:
                    return False

                # Perform health check
                await self.health_service.check_service_health(service, db)
                await db.commit()

                return True

        except Exception as e:
            logger.error(f"Error triggering immediate health check: {e}")
            return False


# Global worker instance
_health_worker: Optional[HealthCheckWorker] = None


def get_health_worker() -> HealthCheckWorker:
    """Get or create the global health worker instance."""
    global _health_worker
    if _health_worker is None:
        _health_worker = HealthCheckWorker()
    return _health_worker
