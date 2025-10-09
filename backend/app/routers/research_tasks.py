"""
Research Task management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TaskStatus
from app.schemas import (
    ResearchTaskCreate,
    ResearchTaskUpdate,
    ResearchTaskResponse,
)
from app.services import ResearchService

router = APIRouter(prefix="/research-tasks", tags=["research-tasks"])


def get_research_service(db: AsyncSession = Depends(get_db)) -> ResearchService:
    """Dependency to get research service instance"""
    return ResearchService(db)


@router.get("/", response_model=List[ResearchTaskResponse])
async def list_research_tasks(
    skip: int = 0,
    limit: int = 100,
    technology_id: Optional[int] = None,
    repository_id: Optional[int] = None,
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    assigned_to: Optional[str] = None,
    service: ResearchService = Depends(get_research_service),
) -> List[ResearchTaskResponse]:
    """List research tasks with filtering"""
    tasks = await service.list_research_tasks(
        skip=skip,
        limit=limit,
        technology_id=technology_id,
        repository_id=repository_id,
        status_filter=status_filter,
        assigned_to=assigned_to,
    )

    return [ResearchTaskResponse.model_validate(t) for t in tasks]


@router.get("/{task_id}", response_model=ResearchTaskResponse)
async def get_research_task(
    task_id: int, service: ResearchService = Depends(get_research_service)
) -> ResearchTaskResponse:
    """Get research task by ID"""
    task = await service.get_research_task(task_id)
    return ResearchTaskResponse.model_validate(task)


@router.post(
    "/", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED
)
async def create_research_task(
    task_data: ResearchTaskCreate,
    service: ResearchService = Depends(get_research_service),
) -> ResearchTaskResponse:
    """Create a new research task"""
    task = await service.create_research_task(task_data)
    return ResearchTaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=ResearchTaskResponse)
async def update_research_task(
    task_id: int,
    task_data: ResearchTaskUpdate,
    service: ResearchService = Depends(get_research_service),
) -> ResearchTaskResponse:
    """Update research task"""
    task = await service.update_research_task(task_id, task_data)
    return ResearchTaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research_task(
    task_id: int, service: ResearchService = Depends(get_research_service)
) -> None:
    """Delete research task"""
    await service.delete_research_task(task_id)


@router.patch("/{task_id}/status", response_model=ResearchTaskResponse)
async def update_task_status(
    task_id: int,
    new_status: TaskStatus,
    service: ResearchService = Depends(get_research_service),
) -> ResearchTaskResponse:
    """Update task status"""
    task = await service.update_status(task_id, new_status)
    return ResearchTaskResponse.model_validate(task)


@router.patch("/{task_id}/progress", response_model=ResearchTaskResponse)
async def update_task_progress(
    task_id: int,
    progress_percentage: int = Query(..., ge=0, le=100),
    service: ResearchService = Depends(get_research_service),
) -> ResearchTaskResponse:
    """Update task progress"""
    task = await service.update_progress(task_id, progress_percentage)
    return ResearchTaskResponse.model_validate(task)


@router.post("/{task_id}/documents", response_model=ResearchTaskResponse)
async def upload_document(
    task_id: int,
    file: UploadFile = File(...),
    service: ResearchService = Depends(get_research_service),
) -> ResearchTaskResponse:
    """Upload a document to a research task"""
    import os
    import uuid
    from datetime import datetime
    from pathlib import Path

    # Get the task to ensure it exists
    task = await service.get_research_task(task_id)

    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/research_tasks")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename

    # Save the file
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Update task's uploaded_documents list
    uploaded_documents = task.uploaded_documents or []
    uploaded_documents.append(
        {
            "filename": file.filename,
            "stored_filename": unique_filename,
            "file_path": str(file_path),
            "content_type": file.content_type,
            "size": len(contents),
            "uploaded_at": str(datetime.utcnow()),
        }
    )

    # Update via repository directly since we need to update uploaded_documents
    from app.repositories import ResearchTaskRepository

    repo = ResearchTaskRepository(service.db)
    updated_task = await repo.update(task, uploaded_documents=uploaded_documents)
    await service.db.commit()
    await service.db.refresh(updated_task)

    return ResearchTaskResponse.model_validate(updated_task)


@router.get("/{task_id}/documents")
async def list_documents(
    task_id: int, service: ResearchService = Depends(get_research_service)
):
    """List documents for a research task"""
    task = await service.get_research_task(task_id)
    return {"documents": task.uploaded_documents or []}


@router.get("/statistics/overview")
async def get_task_statistics(
    technology_id: Optional[int] = None,
    repository_id: Optional[int] = None,
    service: ResearchService = Depends(get_research_service),
):
    """Get research task statistics"""
    return await service.get_statistics(technology_id, repository_id)


@router.get("/upcoming/list", response_model=List[ResearchTaskResponse])
async def get_upcoming_tasks(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
    service: ResearchService = Depends(get_research_service),
) -> List[ResearchTaskResponse]:
    """Get upcoming tasks"""
    tasks = await service.get_upcoming_tasks(days, limit)
    return [ResearchTaskResponse.model_validate(t) for t in tasks]


@router.get("/overdue/list", response_model=List[ResearchTaskResponse])
async def get_overdue_tasks(
    limit: int = Query(100, ge=1, le=500),
    service: ResearchService = Depends(get_research_service),
) -> List[ResearchTaskResponse]:
    """Get overdue tasks"""
    tasks = await service.get_overdue_tasks(limit)
    return [ResearchTaskResponse.model_validate(t) for t in tasks]
