"""Health check service for monitoring service health status."""
import asyncio
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from enum import Enum

import httpx
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal as async_session_maker
from app.models.service import (
    Service, HealthCheck, HealthStatus,
    HealthMethod, ServiceType
)
from app.events.service import EventService
from app.config import get_hub_id
import logging

logger = logging.getLogger(__name__)


class HealthTransition(str, Enum):
    """Health status transitions."""
    UP_TO_DEGRADED = "up_to_degraded"
    UP_TO_DOWN = "up_to_down"
    DEGRADED_TO_UP = "degraded_to_up"
    DEGRADED_TO_DOWN = "degraded_to_down"
    DOWN_TO_UP = "down_to_up"
    UNKNOWN_TO_UP = "unknown_to_up"
    UNKNOWN_TO_DOWN = "unknown_to_down"


class HealthService:
    """Service for performing health checks on registered services."""

    def __init__(self, event_service: Optional[EventService] = None):
        """Initialize health service.

        Args:
            event_service: Optional event service for publishing health events
        """
        self.event_service = event_service
        self.hub_id = get_hub_id()
        self._health_checkers: Dict[HealthMethod, callable] = {
            HealthMethod.HTTP: self._check_http_health,
            HealthMethod.TCP: self._check_tcp_health,
            HealthMethod.POSTGRES: self._check_postgres_health,
            HealthMethod.REDIS: self._check_redis_health,
            HealthMethod.EXEC: self._check_exec_health,
        }

    async def check_service_health(
        self,
        service: Service,
        db: AsyncSession
    ) -> HealthCheck:
        """Perform a health check on a service.

        Args:
            service: Service to check
            db: Database session

        Returns:
            HealthCheck record
        """
        start_time = time.time()
        status = HealthStatus.UNKNOWN
        error_message = None
        details = {}

        try:
            # Get the appropriate health checker
            checker = self._health_checkers.get(service.health_method)
            if not checker:
                raise ValueError(f"Unknown health method: {service.health_method}")

            # Perform the health check
            is_healthy, check_details = await checker(service)

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Determine status based on health and latency
            if is_healthy:
                if latency_ms > service.health_threshold:
                    status = HealthStatus.DEGRADED
                    details["reason"] = "High latency"
                else:
                    status = HealthStatus.UP
            else:
                status = HealthStatus.DOWN

            details.update(check_details)

        except asyncio.TimeoutError:
            status = HealthStatus.DOWN
            error_message = "Health check timed out"
            latency_ms = service.health_timeout * 1000
        except Exception as e:
            status = HealthStatus.DOWN
            error_message = str(e)
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check failed for {service.name}: {e}")

        # Update service status
        old_status = service.health_status
        service.health_status = status
        service.last_health_check = datetime.now(timezone.utc)
        service.total_checks += 1

        # Update consecutive counters
        if status in [HealthStatus.UP, HealthStatus.DEGRADED]:
            service.consecutive_successes += 1
            service.consecutive_failures = 0
        else:
            service.consecutive_failures += 1
            service.consecutive_successes = 0
            service.failed_checks += 1
            service.last_error = error_message

        # Update average latency
        if service.average_latency is None:
            service.average_latency = latency_ms
        else:
            # Exponential moving average
            service.average_latency = (
                0.9 * service.average_latency + 0.1 * latency_ms
            )

        # Update health details
        service.health_details = details

        # Create health check record
        health_check = HealthCheck(
            service_id=service.id,
            status=status,
            latency_ms=latency_ms,
            error_message=error_message,
            details=details
        )

        db.add(health_check)

        # Publish status change event if needed
        if old_status != status and self.event_service:
            await self._publish_status_change(
                service, old_status, status
            )

        return health_check

    async def _check_http_health(
        self,
        service: Service
    ) -> tuple[bool, Dict[str, Any]]:
        """Check HTTP endpoint health.

        Args:
            service: Service to check

        Returns:
            Tuple of (is_healthy, details)
        """
        details = {}

        async with httpx.AsyncClient(timeout=service.health_timeout) as client:
            try:
                response = await client.get(service.health_url)
                details["status_code"] = response.status_code

                # Check for successful status code
                is_healthy = 200 <= response.status_code < 300

                # Try to parse JSON response
                try:
                    json_data = response.json()
                    if isinstance(json_data, dict):
                        details.update(json_data)
                except:
                    details["response"] = response.text[:200]

                return is_healthy, details

            except httpx.ConnectError:
                details["error"] = "Connection refused"
                return False, details
            except httpx.TimeoutException:
                details["error"] = "Request timed out"
                return False, details

    async def _check_tcp_health(
        self,
        service: Service
    ) -> tuple[bool, Dict[str, Any]]:
        """Check TCP port health.

        Args:
            service: Service to check

        Returns:
            Tuple of (is_healthy, details)
        """
        details = {}

        try:
            # Parse host and port from health_url
            if ":" in service.health_url:
                host, port_str = service.health_url.rsplit(":", 1)
                port = int(port_str)
            else:
                host = service.health_url
                port = service.port

            # Try to connect
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=service.health_timeout
            )

            writer.close()
            await writer.wait_closed()

            details["port"] = port
            return True, details

        except asyncio.TimeoutError:
            details["error"] = "Connection timed out"
            return False, details
        except ConnectionRefusedError:
            details["error"] = "Connection refused"
            return False, details
        except Exception as e:
            details["error"] = str(e)
            return False, details

    async def _check_postgres_health(
        self,
        service: Service
    ) -> tuple[bool, Dict[str, Any]]:
        """Check PostgreSQL health using pg_isready.

        Args:
            service: Service to check

        Returns:
            Tuple of (is_healthy, details)
        """
        details = {"method": "pg_isready"}

        try:
            # Use container exec if container_id is available
            if service.container_id:
                proc = await asyncio.create_subprocess_exec(
                    "docker", "exec", service.container_id,
                    "pg_isready", "-U", "commandcenter",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                # Use direct pg_isready with connection info
                proc = await asyncio.create_subprocess_exec(
                    "pg_isready",
                    "-h", "localhost",
                    "-p", str(service.port or 5432),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=service.health_timeout
            )

            is_healthy = proc.returncode == 0
            details["output"] = stdout.decode().strip() if stdout else None

            if not is_healthy:
                details["error"] = stderr.decode().strip() if stderr else "pg_isready failed"

            return is_healthy, details

        except asyncio.TimeoutError:
            details["error"] = "Health check timed out"
            return False, details
        except Exception as e:
            details["error"] = str(e)
            return False, details

    async def _check_redis_health(
        self,
        service: Service
    ) -> tuple[bool, Dict[str, Any]]:
        """Check Redis health using PING command.

        Args:
            service: Service to check

        Returns:
            Tuple of (is_healthy, details)
        """
        details = {"method": "redis-cli ping"}

        try:
            # Use container exec if container_id is available
            if service.container_id:
                proc = await asyncio.create_subprocess_exec(
                    "docker", "exec", service.container_id,
                    "redis-cli", "ping",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                # Use direct redis-cli with connection info
                proc = await asyncio.create_subprocess_exec(
                    "redis-cli",
                    "-h", "localhost",
                    "-p", str(service.port or 6379),
                    "ping",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=service.health_timeout
            )

            output = stdout.decode().strip()
            is_healthy = output == "PONG"
            details["response"] = output

            if not is_healthy:
                details["error"] = stderr.decode().strip() if stderr else "Redis ping failed"

            return is_healthy, details

        except asyncio.TimeoutError:
            details["error"] = "Health check timed out"
            return False, details
        except Exception as e:
            details["error"] = str(e)
            return False, details

    async def _check_exec_health(
        self,
        service: Service
    ) -> tuple[bool, Dict[str, Any]]:
        """Execute a custom health check command.

        Args:
            service: Service to check

        Returns:
            Tuple of (is_healthy, details)
        """
        details = {"method": "exec"}

        try:
            # Parse command from health_url
            cmd_parts = service.health_url.split()

            proc = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=service.health_timeout
            )

            is_healthy = proc.returncode == 0
            details["exit_code"] = proc.returncode
            details["output"] = stdout.decode().strip()[:200] if stdout else None

            if not is_healthy:
                details["error"] = stderr.decode().strip()[:200] if stderr else f"Exit code {proc.returncode}"

            return is_healthy, details

        except asyncio.TimeoutError:
            details["error"] = "Health check timed out"
            return False, details
        except Exception as e:
            details["error"] = str(e)
            return False, details

    async def _publish_status_change(
        self,
        service: Service,
        old_status: HealthStatus,
        new_status: HealthStatus
    ):
        """Publish health status change event.

        Args:
            service: Service that changed
            old_status: Previous health status
            new_status: New health status
        """
        transition = self._get_transition(old_status, new_status)

        await self.event_service.publish(
            subject=f"hub.{self.hub_id}.health.{service.name}",
            category="health",
            event_type="health_status_changed",
            payload={
                "service_id": service.id,
                "service_name": service.name,
                "project_id": service.project_id,
                "old_status": old_status.value if old_status else None,
                "new_status": new_status.value,
                "transition": transition.value if transition else None,
                "consecutive_failures": service.consecutive_failures,
                "average_latency": service.average_latency,
            }
        )

    def _get_transition(
        self,
        old_status: Optional[HealthStatus],
        new_status: HealthStatus
    ) -> Optional[HealthTransition]:
        """Get the health transition type.

        Args:
            old_status: Previous status
            new_status: New status

        Returns:
            HealthTransition or None
        """
        if not old_status or old_status == new_status:
            return None

        transition_map = {
            (HealthStatus.UP, HealthStatus.DEGRADED): HealthTransition.UP_TO_DEGRADED,
            (HealthStatus.UP, HealthStatus.DOWN): HealthTransition.UP_TO_DOWN,
            (HealthStatus.DEGRADED, HealthStatus.UP): HealthTransition.DEGRADED_TO_UP,
            (HealthStatus.DEGRADED, HealthStatus.DOWN): HealthTransition.DEGRADED_TO_DOWN,
            (HealthStatus.DOWN, HealthStatus.UP): HealthTransition.DOWN_TO_UP,
            (HealthStatus.UNKNOWN, HealthStatus.UP): HealthTransition.UNKNOWN_TO_UP,
            (HealthStatus.UNKNOWN, HealthStatus.DOWN): HealthTransition.UNKNOWN_TO_DOWN,
        }

        return transition_map.get((old_status, new_status))

    async def get_service_health_history(
        self,
        service_id: int,
        db: AsyncSession,
        hours: int = 24
    ) -> List[HealthCheck]:
        """Get health check history for a service.

        Args:
            service_id: Service ID
            hours: Number of hours of history
            db: Database session

        Returns:
            List of health checks
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        result = await db.execute(
            select(HealthCheck)
            .where(
                and_(
                    HealthCheck.service_id == service_id,
                    HealthCheck.checked_at >= since
                )
            )
            .order_by(HealthCheck.checked_at.desc())
        )

        return result.scalars().all()

    async def calculate_uptime(
        self,
        service_id: int,
        db: AsyncSession,
        hours: int = 24
    ) -> float:
        """Calculate service uptime percentage.

        Args:
            service_id: Service ID
            hours: Number of hours to calculate
            db: Database session

        Returns:
            Uptime percentage (0-100)
        """
        checks = await self.get_service_health_history(
            service_id, db, hours
        )

        if not checks:
            return 0.0

        healthy_checks = sum(
            1 for check in checks
            if check.status in [HealthStatus.UP, HealthStatus.DEGRADED]
        )

        return (healthy_checks / len(checks)) * 100
