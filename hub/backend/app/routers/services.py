"""Service health and discovery API endpoints."""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_async_db
from app.models.service import Service, HealthCheck, HealthStatus, ServiceType
from app.models.project import Project
from app.services.health_service import HealthService
from app.workers.health_worker import get_health_worker
from app.schemas import Response
from pydantic import BaseModel
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/services", tags=["services"])


class ServiceResponse(BaseModel):
    """Service information response."""
    id: int
    project_id: int
    project_name: str
    name: str
    service_type: Optional[str]
    health_status: Optional[str]
    health_method: Optional[str]
    port: Optional[int]
    version: Optional[str]
    average_latency: Optional[float]
    uptime_seconds: Optional[int]
    last_health_check: Optional[datetime]
    consecutive_failures: int
    is_required: bool


class ServiceHealthResponse(BaseModel):
    """Detailed service health response."""
    service: ServiceResponse
    current_status: str
    last_check: Optional[datetime]
    average_latency: Optional[float]
    consecutive_failures: int
    consecutive_successes: int
    total_checks: int
    failed_checks: int
    uptime_percentage: float
    health_details: dict
    last_error: Optional[str]


class ProjectHealthResponse(BaseModel):
    """Project health summary response."""
    project_id: int
    project_name: str
    project_status: str
    overall_health: str
    services: List[ServiceResponse]
    healthy_services: int
    total_services: int
    last_check: Optional[datetime]


class HealthCheckResponse(BaseModel):
    """Health check history response."""
    id: int
    service_id: int
    status: str
    latency_ms: Optional[float]
    error_message: Optional[str]
    details: dict
    checked_at: datetime


@router.get("", response_model=List[ServiceResponse])
async def list_services(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
) -> List[ServiceResponse]:
    """List all registered services.

    Args:
        project_id: Optional filter by project
        status: Optional filter by health status
        db: Database session

    Returns:
        List of services
    """
    query = select(Service).join(Project).options(selectinload(Service.project))

    conditions = []
    if project_id:
        conditions.append(Service.project_id == project_id)
    if status:
        try:
            health_status = HealthStatus(status)
            conditions.append(Service.health_status == health_status)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")

    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    services = result.scalars().all()

    return [
        ServiceResponse(
            id=s.id,
            project_id=s.project_id,
            project_name=s.project.name,
            name=s.name,
            service_type=s.service_type.value if s.service_type else None,
            health_status=s.health_status.value if s.health_status else None,
            health_method=s.health_method.value if s.health_method else None,
            port=s.port,
            version=s.version,
            average_latency=s.average_latency,
            uptime_seconds=s.uptime_seconds,
            last_health_check=s.last_health_check,
            consecutive_failures=s.consecutive_failures,
            is_required=s.is_required
        )
        for s in services
    ]


@router.get("/{service_id}/health", response_model=ServiceHealthResponse)
async def get_service_health(
    service_id: int,
    db: AsyncSession = Depends(get_async_db)
) -> ServiceHealthResponse:
    """Get detailed health information for a service.

    Args:
        service_id: Service ID
        db: Database session

    Returns:
        Detailed health information
    """
    result = await db.execute(
        select(Service)
        .options(selectinload(Service.project))
        .where(Service.id == service_id)
    )
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(404, "Service not found")

    # Calculate uptime percentage
    uptime_percentage = 0.0
    if service.total_checks > 0:
        uptime_percentage = ((service.total_checks - service.failed_checks) / service.total_checks) * 100

    return ServiceHealthResponse(
        service=ServiceResponse(
            id=service.id,
            project_id=service.project_id,
            project_name=service.project.name,
            name=service.name,
            service_type=service.service_type.value if service.service_type else None,
            health_status=service.health_status.value if service.health_status else None,
            health_method=service.health_method.value if service.health_method else None,
            port=service.port,
            version=service.version,
            average_latency=service.average_latency,
            uptime_seconds=service.uptime_seconds,
            last_health_check=service.last_health_check,
            consecutive_failures=service.consecutive_failures,
            is_required=service.is_required
        ),
        current_status=service.health_status.value if service.health_status else "unknown",
        last_check=service.last_health_check,
        average_latency=service.average_latency,
        consecutive_failures=service.consecutive_failures,
        consecutive_successes=service.consecutive_successes,
        total_checks=service.total_checks,
        failed_checks=service.failed_checks,
        uptime_percentage=uptime_percentage,
        health_details=service.health_details or {},
        last_error=service.last_error
    )


@router.get("/{service_id}/health/history", response_model=List[HealthCheckResponse])
async def get_health_history(
    service_id: int,
    hours: int = 24,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
) -> List[HealthCheckResponse]:
    """Get health check history for a service.

    Args:
        service_id: Service ID
        hours: Number of hours of history
        limit: Maximum number of records
        db: Database session

    Returns:
        List of health check records
    """
    health_service = HealthService()
    checks = await health_service.get_service_health_history(
        service_id, db, hours
    )

    # Limit results
    checks = checks[:limit]

    return [
        HealthCheckResponse(
            id=c.id,
            service_id=c.service_id,
            status=c.status.value,
            latency_ms=c.latency_ms,
            error_message=c.error_message,
            details=c.details or {},
            checked_at=c.checked_at
        )
        for c in checks
    ]


@router.post("/{service_id}/health/check", response_model=Response)
async def trigger_health_check(
    service_id: int,
    db: AsyncSession = Depends(get_async_db)
) -> Response:
    """Trigger an immediate health check for a service.

    Args:
        service_id: Service ID
        db: Database session

    Returns:
        Success response
    """
    worker = get_health_worker()
    triggered = await worker.trigger_immediate_check(service_id)

    if not triggered:
        raise HTTPException(404, "Service not found")

    return Response(
        success=True,
        message=f"Health check triggered for service {service_id}"
    )


@router.get("/projects/{project_id}/health", response_model=ProjectHealthResponse)
async def get_project_health(
    project_id: int,
    db: AsyncSession = Depends(get_async_db)
) -> ProjectHealthResponse:
    """Get health summary for all services in a project.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Project health summary
    """
    # Get project with services
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.services))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(404, "Project not found")

    # Determine overall health
    overall_health = "healthy"
    healthy_count = 0
    last_check = None

    service_responses = []
    for service in project.services:
        if service.health_status in [HealthStatus.UP, HealthStatus.DEGRADED]:
            healthy_count += 1

        if service.is_required and service.health_status == HealthStatus.DOWN:
            overall_health = "unhealthy"
        elif service.health_status == HealthStatus.DEGRADED and overall_health == "healthy":
            overall_health = "degraded"

        if service.last_health_check:
            if not last_check or service.last_health_check > last_check:
                last_check = service.last_health_check

        service_responses.append(
            ServiceResponse(
                id=service.id,
                project_id=service.project_id,
                project_name=project.name,
                name=service.name,
                service_type=service.service_type.value if service.service_type else None,
                health_status=service.health_status.value if service.health_status else None,
                health_method=service.health_method.value if service.health_method else None,
                port=service.port,
                version=service.version,
                average_latency=service.average_latency,
                uptime_seconds=service.uptime_seconds,
                last_health_check=service.last_health_check,
                consecutive_failures=service.consecutive_failures,
                is_required=service.is_required
            )
        )

    return ProjectHealthResponse(
        project_id=project.id,
        project_name=project.name,
        project_status=project.status,
        overall_health=overall_health,
        services=service_responses,
        healthy_services=healthy_count,
        total_services=len(project.services),
        last_check=last_check
    )


@router.websocket("/ws/health")
async def health_websocket(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_async_db)
):
    """WebSocket endpoint for real-time health updates.

    Sends health status updates as services change.
    """
    await websocket.accept()
    logger.info("Health WebSocket connection established")

    try:
        while True:
            # Send current health status
            result = await db.execute(
                select(Service)
                .join(Project)
                .options(selectinload(Service.project))
                .where(Project.status == "running")
            )
            services = result.scalars().all()

            health_data = {
                "type": "health_update",
                "timestamp": datetime.utcnow().isoformat(),
                "services": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "project": s.project.name,
                        "status": s.health_status.value if s.health_status else "unknown",
                        "latency": s.average_latency,
                        "last_check": s.last_health_check.isoformat() if s.last_health_check else None
                    }
                    for s in services
                ],
                "summary": {
                    "total": len(services),
                    "healthy": sum(
                        1 for s in services
                        if s.health_status in [HealthStatus.UP, HealthStatus.DEGRADED]
                    ),
                    "down": sum(
                        1 for s in services
                        if s.health_status == HealthStatus.DOWN
                    )
                }
            }

            await websocket.send_json(health_data)

            # Wait before next update (or could subscribe to events)
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("Health WebSocket disconnected")
    except Exception as e:
        logger.error(f"Health WebSocket error: {e}")
        await websocket.close()
