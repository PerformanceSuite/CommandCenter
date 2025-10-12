"""
Health check service for production monitoring.

Provides comprehensive health status for all system components:
- PostgreSQL database connectivity
- Redis cache availability
- Celery worker status
- Application metrics
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.redis_service import redis_service
from app.tasks import celery_app

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status constants"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthService:
    """Service for comprehensive health checks"""

    @staticmethod
    async def check_database(db: AsyncSession) -> Dict[str, Any]:
        """
        Check PostgreSQL database connectivity and responsiveness.

        Args:
            db: Database session

        Returns:
            Health check result with status and metrics
        """
        start_time = datetime.utcnow()

        try:
            # Simple connectivity test
            result = await db.execute(text("SELECT 1"))
            result.scalar()

            # Get database stats
            pool_status = db.get_bind().pool.status() if hasattr(db.get_bind(), "pool") else "N/A"

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "status": HealthStatus.HEALTHY,
                "response_time_ms": round(response_time, 2),
                "pool_status": pool_status,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    @staticmethod
    async def check_redis() -> Dict[str, Any]:
        """
        Check Redis cache availability and responsiveness.

        Returns:
            Health check result with status and metrics
        """
        start_time = datetime.utcnow()

        try:
            if not redis_service.enabled or not redis_service.redis_client:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Redis is disabled",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }

            # Ping test
            await redis_service.redis_client.ping()

            # Get Redis info
            info = await redis_service.redis_client.info("stats")
            total_commands = info.get("total_commands_processed", 0)
            keyspace = await redis_service.redis_client.info("keyspace")

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "status": HealthStatus.HEALTHY,
                "response_time_ms": round(response_time, 2),
                "total_commands": total_commands,
                "databases": len(keyspace),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    @staticmethod
    async def check_celery() -> Dict[str, Any]:
        """
        Check Celery worker availability and queue status.

        Returns:
            Health check result with status and metrics
        """
        start_time = datetime.utcnow()

        try:
            # Get active workers using inspect
            inspector = celery_app.control.inspect()

            # Timeout for worker inspection (2 seconds)
            stats = await asyncio.wait_for(
                asyncio.to_thread(inspector.stats), timeout=2.0
            )
            active_tasks = await asyncio.wait_for(
                asyncio.to_thread(inspector.active), timeout=2.0
            )
            registered_tasks = await asyncio.wait_for(
                asyncio.to_thread(inspector.registered), timeout=2.0
            )

            if not stats:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "error": "No Celery workers available",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }

            # Calculate metrics
            worker_count = len(stats) if stats else 0
            total_active_tasks = sum(len(tasks) for tasks in (active_tasks or {}).values())
            total_registered_tasks = sum(len(tasks) for tasks in (registered_tasks or {}).values())

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "status": HealthStatus.HEALTHY,
                "response_time_ms": round(response_time, 2),
                "workers": worker_count,
                "active_tasks": total_active_tasks,
                "registered_tasks": total_registered_tasks,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except asyncio.TimeoutError:
            logger.error("Celery health check timed out")
            return {
                "status": HealthStatus.DEGRADED,
                "error": "Celery inspection timeout",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    @staticmethod
    async def get_overall_health(db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Get comprehensive health status for all components.

        Args:
            db: Optional database session (if None, DB check is skipped)

        Returns:
            Overall health status with component details
        """
        start_time = datetime.utcnow()

        # Run all health checks in parallel
        checks = {}

        if db:
            checks["database"] = HealthService.check_database(db)

        checks["redis"] = HealthService.check_redis()
        checks["celery"] = HealthService.check_celery()

        # Await all checks
        results = {}
        for name, check in checks.items():
            results[name] = await check

        # Determine overall status
        statuses = [result["status"] for result in results.values()]

        if all(status == HealthStatus.HEALTHY for status in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        total_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "response_time_ms": round(total_time, 2),
            "components": results,
        }


# Singleton instance
health_service = HealthService()
