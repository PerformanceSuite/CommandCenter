"""
Research task business logic service
Handles research task operations with transaction management
"""
import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ResearchTask, TaskStatus
from app.repositories import (
    ResearchTaskRepository,
    TechnologyRepository,
    RepositoryRepository,
)
from app.schemas import ResearchTaskCreate, ResearchTaskUpdate


class ResearchService:
    """Service layer for research task operations"""

    def __init__(self, db: AsyncSession):
        """
        Initialize research service

        Args:
            db: Database session
        """
        self.db = db
        self.repo = ResearchTaskRepository(db)
        self.tech_repo = TechnologyRepository(db)
        self.repo_repo = RepositoryRepository(db)

    async def list_research_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        technology_id: Optional[int] = None,
        repository_id: Optional[int] = None,
        status_filter: Optional[TaskStatus] = None,
        assigned_to: Optional[str] = None,
    ) -> List[ResearchTask]:
        """
        List research tasks with filtering

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            technology_id: Optional technology ID filter
            repository_id: Optional repository ID filter
            status_filter: Optional status filter
            assigned_to: Optional assignee filter

        Returns:
            List of research tasks
        """
        if technology_id:
            return await self.repo.list_by_technology(technology_id, skip, limit)
        elif repository_id:
            return await self.repo.list_by_repository(repository_id, skip, limit)
        elif status_filter:
            return await self.repo.list_by_status(status_filter, skip, limit)
        elif assigned_to:
            return await self.repo.list_by_assignee(assigned_to, skip, limit)
        else:
            return await self.repo.get_all(skip, limit)

    async def get_research_task(self, task_id: int) -> ResearchTask:
        """
        Get research task by ID

        Args:
            task_id: Task ID

        Returns:
            Research task

        Raises:
            HTTPException: If task not found
        """
        task = await self.repo.get_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research task {task_id} not found",
            )

        return task

    async def create_research_task(self, task_data: ResearchTaskCreate) -> ResearchTask:
        """
        Create new research task

        Args:
            task_data: Task creation data

        Returns:
            Created research task

        Raises:
            HTTPException: If referenced technology or repository not found
        """
        # Validate foreign key references
        if task_data.technology_id:
            technology = await self.tech_repo.get_by_id(task_data.technology_id)
            if not technology:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Technology {task_data.technology_id} not found",
                )

        if task_data.repository_id:
            repository = await self.repo_repo.get_by_id(task_data.repository_id)
            if not repository:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Repository {task_data.repository_id} not found",
                )

        # Create task
        task = await self.repo.create(**task_data.model_dump())

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def update_research_task(
        self, task_id: int, task_data: ResearchTaskUpdate
    ) -> ResearchTask:
        """
        Update research task

        Args:
            task_id: Task ID
            task_data: Task update data

        Returns:
            Updated research task

        Raises:
            HTTPException: If task not found
        """
        task = await self.get_research_task(task_id)

        # Validate foreign key references if being updated
        update_dict = task_data.model_dump(exclude_unset=True)

        if "technology_id" in update_dict and update_dict["technology_id"]:
            technology = await self.tech_repo.get_by_id(update_dict["technology_id"])
            if not technology:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Technology {update_dict['technology_id']} not found",
                )

        if "repository_id" in update_dict and update_dict["repository_id"]:
            repository = await self.repo_repo.get_by_id(update_dict["repository_id"])
            if not repository:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Repository {update_dict['repository_id']} not found",
                )

        # Update task
        task = await self.repo.update(task, **update_dict)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def delete_research_task(self, task_id: int) -> None:
        """
        Delete research task

        Args:
            task_id: Task ID

        Raises:
            HTTPException: If task not found
        """
        task = await self.get_research_task(task_id)
        await self.repo.delete(task)
        await self.db.commit()

    async def update_status(self, task_id: int, new_status: TaskStatus) -> ResearchTask:
        """
        Update task status

        Args:
            task_id: Task ID
            new_status: New status

        Returns:
            Updated research task

        Raises:
            HTTPException: If task not found
        """
        task = await self.get_research_task(task_id)

        # Auto-set completed_at when marking as completed
        update_data = {"status": new_status}
        if new_status == TaskStatus.COMPLETED and not task.completed_at:
            update_data["completed_at"] = datetime.utcnow()
        elif new_status != TaskStatus.COMPLETED:
            update_data["completed_at"] = None

        task = await self.repo.update(task, **update_data)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def update_progress(
        self, task_id: int, progress_percentage: int
    ) -> ResearchTask:
        """
        Update task progress

        Args:
            task_id: Task ID
            progress_percentage: Progress percentage (0-100)

        Returns:
            Updated research task

        Raises:
            HTTPException: If task not found or invalid progress
        """
        if not 0 <= progress_percentage <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Progress percentage must be between 0 and 100",
            )

        task = await self.get_research_task(task_id)

        # Auto-complete if progress reaches 100%
        update_data = {"progress_percentage": progress_percentage}
        if progress_percentage == 100 and task.status != TaskStatus.COMPLETED:
            update_data["status"] = TaskStatus.COMPLETED
            update_data["completed_at"] = datetime.utcnow()

        task = await self.repo.update(task, **update_data)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def assign_task(self, task_id: int, assigned_to: str) -> ResearchTask:
        """
        Assign task to user

        Args:
            task_id: Task ID
            assigned_to: Username to assign to

        Returns:
            Updated research task

        Raises:
            HTTPException: If task not found
        """
        task = await self.get_research_task(task_id)
        task = await self.repo.update(task, assigned_to=assigned_to)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def add_findings(self, task_id: int, findings: str) -> ResearchTask:
        """
        Add findings to task

        Args:
            task_id: Task ID
            findings: Research findings

        Returns:
            Updated research task

        Raises:
            HTTPException: If task not found
        """
        task = await self.get_research_task(task_id)
        task = await self.repo.update(task, findings=findings)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def upload_document_to_task(
        self, task_id: int, file: UploadFile
    ) -> ResearchTask:
        """
        Upload a document and associate it with a research task.

        Args:
            task_id: The ID of the research task.
            file: The file to upload.

        Returns:
            The updated research task.
        """
        task = await self.get_research_task(task_id)

        upload_dir = Path("uploads/research_tasks")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

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

        updated_task = await self.repo.update(
            task, uploaded_documents=uploaded_documents
        )
        await self.db.commit()
        await self.db.refresh(updated_task)

        return updated_task

    async def get_overdue_tasks(self, limit: int = 100) -> List[ResearchTask]:
        """
        Get overdue tasks

        Args:
            limit: Maximum number of results

        Returns:
            List of overdue tasks
        """
        return await self.repo.get_overdue(limit)

    async def get_upcoming_tasks(
        self, days: int = 7, limit: int = 100
    ) -> List[ResearchTask]:
        """
        Get upcoming tasks

        Args:
            days: Number of days to look ahead
            limit: Maximum number of results

        Returns:
            List of upcoming tasks
        """
        return await self.repo.get_upcoming(days, limit)

    async def get_statistics(
        self, technology_id: Optional[int] = None, repository_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get research task statistics

        Args:
            technology_id: Optional technology ID filter
            repository_id: Optional repository ID filter

        Returns:
            Dictionary with statistics
        """
        stats = await self.repo.get_statistics(technology_id, repository_id)
        overdue = await self.repo.get_overdue(limit=10)
        upcoming = await self.repo.get_upcoming(days=7, limit=10)

        return {
            **stats,
            "overdue_count": len(overdue),
            "upcoming_count": len(upcoming),
            "overdue_tasks": [
                {"id": t.id, "title": t.title, "due_date": t.due_date}
                for t in overdue[:5]
            ],
            "upcoming_tasks": [
                {"id": t.id, "title": t.title, "due_date": t.due_date}
                for t in upcoming[:5]
            ],
        }
