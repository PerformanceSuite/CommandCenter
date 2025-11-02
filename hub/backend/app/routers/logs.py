"""
Logs API Router

Endpoints for retrieving container logs from managed projects.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Project
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/api/v1/projects", tags=["logs"])


@router.get("/{project_id}/logs/{service_name}")
async def get_service_logs(
    project_id: int,
    service_name: str,
    tail: int = Query(default=100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve logs from a specific service container.

    **SECURITY WARNING**: Logs may contain sensitive data (credentials, tokens,
    stack traces with internal paths). This endpoint should only be exposed on
    localhost (127.0.0.1) for development. Add authentication before deploying
    the Hub to a shared network.

    Args:
        project_id: Project ID
        service_name: Service name (postgres, redis, backend, frontend)
        tail: Number of log lines to retrieve (default 100, max 10000)

    Returns:
        JSON with logs and metadata

    Raises:
        404: Project not found
        400: Invalid service name
        500: Failed to retrieve logs
    """
    # Get project from database
    result = await db.execute(
        Project.__table__.select().where(Project.id == project_id)
    )
    project = result.fetchone()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Validate service name
    valid_services = ["postgres", "redis", "backend", "frontend"]
    if service_name not in valid_services:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service name: {service_name}. Must be one of {valid_services}"
        )

    # Retrieve logs via orchestration service
    try:
        orchestration = OrchestrationService(db)
        logs = await orchestration.get_project_logs(project_id, service_name, tail)

        return {
            "project_id": project_id,
            "service": service_name,
            "logs": logs,
            "lines": len(logs.split('\n')) if logs else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve logs: {str(e)}"
        )
