"""
Orchestration API - Start/stop CommandCenter instances
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import OrchestrationResponse
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


def get_orchestration_service(
    db: AsyncSession = Depends(get_db),
) -> OrchestrationService:
    """Dependency to get orchestration service"""
    return OrchestrationService(db)


@router.post("/{project_id}/start", response_model=OrchestrationResponse)
async def start_project(
    project_id: int,
    service: OrchestrationService = Depends(get_orchestration_service),
):
    """
    Start CommandCenter instance

    Runs: docker-compose up -d
    """
    try:
        result = await service.start_project(project_id)
        return OrchestrationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{project_id}/stop", response_model=OrchestrationResponse)
async def stop_project(
    project_id: int,
    service: OrchestrationService = Depends(get_orchestration_service),
):
    """
    Stop CommandCenter instance

    Runs: docker-compose down
    """
    try:
        result = await service.stop_project(project_id)
        return OrchestrationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{project_id}/restart", response_model=OrchestrationResponse)
async def restart_project(
    project_id: int,
    service: OrchestrationService = Depends(get_orchestration_service),
):
    """
    Restart CommandCenter instance

    Runs: docker-compose restart
    """
    try:
        result = await service.restart_project(project_id)
        return OrchestrationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{project_id}/status")
async def get_project_status(
    project_id: int,
    service: OrchestrationService = Depends(get_orchestration_service),
):
    """Get real-time status of CommandCenter instance"""
    try:
        return await service.get_project_status(project_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{project_id}/logs")
async def get_project_logs(
    project_id: int,
    tail: int = 100,
    service: OrchestrationService = Depends(get_orchestration_service),
):
    """Get docker-compose logs for project"""
    try:
        return await service.get_logs(project_id, tail=tail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
