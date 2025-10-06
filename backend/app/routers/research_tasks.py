"""
Research Task management endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TaskStatus
from app.schemas import (
    ResearchTaskCreate,
    ResearchTaskUpdate,
    ResearchTaskResponse,
    ResearchTaskListResponse,
)
from app.services.research_task_service import ResearchTaskService

router = APIRouter(prefix="/research-tasks", tags=["research-tasks"])


def get_research_task_service(db: AsyncSession = Depends(get_db)) -> ResearchTaskService:
    """Dependency to get research task service instance"""
    return ResearchTaskService(db)


@router.get("/", response_model=ResearchTaskListResponse)
async def list_research_tasks(
    skip: int = 0,
    limit: int = 50,
    status: Optional[TaskStatus] = None,
    technology_id: Optional[int] = Query(None, description="Filter by technology ID"),
    repository_id: Optional[int] = Query(None, description="Filter by repository ID"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    service: ResearchTaskService = Depends(get_research_task_service)
) -> ResearchTaskListResponse:
    """
    List research tasks with filtering and pagination

    Supports filtering by:
    - status: Task status (pending, in_progress, blocked, completed, cancelled)
    - technology_id: Associated technology
    - repository_id: Associated repository
    - assigned_to: Assignee username
    """
    tasks, total = await service.list_tasks(
        skip=skip,
        limit=limit,
        status=status,
        technology_id=technology_id,
        repository_id=repository_id,
        assigned_to=assigned_to
    )

    return ResearchTaskListResponse(
        total=total,
        items=[ResearchTaskResponse.model_validate(t) for t in tasks],
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/overdue", response_model=list[ResearchTaskResponse])
async def get_overdue_tasks(
    limit: int = Query(default=100, le=500),
    service: ResearchTaskService = Depends(get_research_task_service)
) -> list[ResearchTaskResponse]:
    """Get overdue research tasks"""
    tasks = await service.get_overdue_tasks(limit)
    return [ResearchTaskResponse.model_validate(t) for t in tasks]


@router.get("/upcoming", response_model=list[ResearchTaskResponse])
async def get_upcoming_tasks(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to look ahead"),
    limit: int = Query(default=100, le=500),
    service: ResearchTaskService = Depends(get_research_task_service)
) -> list[ResearchTaskResponse]:
    """Get upcoming research tasks due within specified days"""
    tasks = await service.get_upcoming_tasks(days, limit)
    return [ResearchTaskResponse.model_validate(t) for t in tasks]


@router.get("/statistics")
async def get_task_statistics(
    technology_id: Optional[int] = Query(None, description="Filter by technology ID"),
    repository_id: Optional[int] = Query(None, description="Filter by repository ID"),
    service: ResearchTaskService = Depends(get_research_task_service)
) -> dict:
    """
    Get research task statistics

    Returns counts by status, overdue tasks, and upcoming tasks
    """
    return await service.get_statistics(
        technology_id=technology_id,
        repository_id=repository_id
    )


@router.get("/{task_id}", response_model=ResearchTaskResponse)
async def get_research_task(
    task_id: int,
    service: ResearchTaskService = Depends(get_research_task_service)
) -> ResearchTaskResponse:
    """Get research task by ID"""
    task = await service.get_task(task_id)
    return ResearchTaskResponse.model_validate(task)


@router.post("/", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_research_task(
    task_data: ResearchTaskCreate,
    service: ResearchTaskService = Depends(get_research_task_service)
) -> ResearchTaskResponse:
    """
    Create a new research task

    Required fields:
    - title: Task title

    Optional fields:
    - description: Task description
    - status: Initial status (default: pending)
    - technology_id: Associated technology
    - repository_id: Associated repository
    - assigned_to: Assignee username
    - due_date: Due date
    - estimated_hours: Estimated hours to complete
    - user_notes: User notes
    - findings: Research findings
    """
    task = await service.create_task(task_data)
    return ResearchTaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=ResearchTaskResponse)
async def update_research_task(
    task_id: int,
    task_data: ResearchTaskUpdate,
    service: ResearchTaskService = Depends(get_research_task_service)
) -> ResearchTaskResponse:
    """
    Update research task

    All fields are optional. Only provided fields will be updated.
    """
    task = await service.update_task(task_id, task_data)
    return ResearchTaskResponse.model_validate(task)


@router.patch("/{task_id}/progress", response_model=ResearchTaskResponse)
async def update_task_progress(
    task_id: int,
    progress_percentage: int = Query(..., ge=0, le=100, description="Progress percentage (0-100)"),
    service: ResearchTaskService = Depends(get_research_task_service)
) -> ResearchTaskResponse:
    """
    Update task progress percentage

    Automatically marks task as completed when progress reaches 100%
    """
    task = await service.update_progress(task_id, progress_percentage)
    return ResearchTaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research_task(
    task_id: int,
    service: ResearchTaskService = Depends(get_research_task_service)
) -> None:
    """
    Delete research task

    Also deletes all associated uploaded documents
    """
    await service.delete_task(task_id)


@router.post("/{task_id}/documents", response_model=ResearchTaskResponse)
async def upload_task_document(
    task_id: int,
    file: UploadFile = File(..., description="Document file to upload"),
    service: ResearchTaskService = Depends(get_research_task_service)
) -> ResearchTaskResponse:
    """
    Upload document for research task

    Stores the file and updates the task with document metadata
    """
    task = await service.upload_document(task_id, file)
    return ResearchTaskResponse.model_validate(task)
