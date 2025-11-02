"""
ResearchTask business logic service
Handles research task operations with transaction management
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ResearchTask, TaskStatus
from app.repositories import ResearchTaskRepository
from app.schemas import ResearchTaskCreate, ResearchTaskUpdate


class ResearchTaskService:
    """Service layer for research task operations"""

    def __init__(self, db: AsyncSession):
        """
        Initialize research task service

        Args:
            db: Database session
        """
        self.db = db
        self.repo = ResearchTaskRepository(db)
        self.upload_dir = Path("./uploads/research_tasks")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def list_tasks(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[TaskStatus] = None,
        technology_id: Optional[int] = None,
        repository_id: Optional[int] = None,
        assigned_to: Optional[str] = None,
    ) -> tuple[List[ResearchTask], int]:
        """
        List research tasks with filtering and pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            status: Optional status filter
            technology_id: Optional technology ID filter
            repository_id: Optional repository ID filter
            assigned_to: Optional assignee filter

        Returns:
            Tuple of (list of tasks, total count)
        """
        # Apply filters
        if technology_id:
            tasks = await self.repo.list_by_technology(technology_id, skip, limit)
            total = await self.repo.count(technology_id=technology_id)
        elif repository_id:
            tasks = await self.repo.list_by_repository(repository_id, skip, limit)
            total = await self.repo.count(repository_id=repository_id)
        elif status:
            tasks = await self.repo.list_by_status(status, skip, limit)
            total = await self.repo.count(status=status)
        elif assigned_to:
            tasks = await self.repo.list_by_assignee(assigned_to, skip, limit)
            total = await self.repo.count(assigned_to=assigned_to)
        else:
            tasks = await self.repo.get_all(skip, limit)
            total = await self.repo.count()

        return tasks, total

    async def get_task(self, task_id: int) -> ResearchTask:
        """
        Get research task by ID

        Args:
            task_id: Task ID

        Returns:
            ResearchTask

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

    async def create_task(self, task_data: ResearchTaskCreate) -> ResearchTask:
        """
        Create new research task

        Args:
            task_data: Task creation data

        Returns:
            Created research task

        Raises:
            HTTPException: If validation fails
        """
        # Validate foreign keys exist if provided
        if task_data.technology_id:
            # Note: In production, you would validate that the technology exists
            pass

        if task_data.repository_id:
            # Note: In production, you would validate that the repository exists
            pass

        # Create task
        task = await self.repo.create(**task_data.model_dump())

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def update_task(self, task_id: int, task_data: ResearchTaskUpdate) -> ResearchTask:
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
        task = await self.get_task(task_id)

        # Update fields
        update_data = task_data.model_dump(exclude_unset=True)

        # Handle status change to completed
        if (
            update_data.get("status") == TaskStatus.COMPLETED
            and task.status != TaskStatus.COMPLETED
        ):
            update_data["completed_at"] = datetime.utcnow()

        # Clear completed_at if status changed from completed
        if (
            "status" in update_data
            and update_data["status"] != TaskStatus.COMPLETED
            and task.status == TaskStatus.COMPLETED
        ):
            update_data["completed_at"] = None

        task = await self.repo.update(task, **update_data)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def delete_task(self, task_id: int) -> None:
        """
        Delete research task

        Args:
            task_id: Task ID

        Raises:
            HTTPException: If task not found
        """
        task = await self.get_task(task_id)

        # Delete associated uploaded files
        if task.uploaded_documents:
            for doc_info in task.uploaded_documents:
                if isinstance(doc_info, dict) and "path" in doc_info:
                    file_path = Path(doc_info["path"])
                    if file_path.exists():
                        try:
                            file_path.unlink()
                        except Exception:
                            pass  # Ignore file deletion errors

        await self.repo.delete(task)
        await self.db.commit()

    async def upload_document(self, task_id: int, file: UploadFile) -> ResearchTask:
        """
        Upload document for research task

        Args:
            task_id: Task ID
            file: Uploaded file

        Returns:
            Updated research task with document info

        Raises:
            HTTPException: If task not found or upload fails
        """
        task = await self.get_task(task_id)

        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
            )

        # Create task-specific directory
        task_dir = self.upload_dir / str(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)

        # Save file with unique name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = task_dir / safe_filename

        try:
            # Save file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # Update task with document info
            uploaded_docs = task.uploaded_documents or []
            doc_info = {
                "filename": file.filename,
                "path": str(file_path),
                "uploaded_at": datetime.utcnow().isoformat(),
                "size": len(content),
                "content_type": file.content_type,
            }
            uploaded_docs.append(doc_info)

            task = await self.repo.update(task, uploaded_documents=uploaded_docs)
            await self.db.commit()
            await self.db.refresh(task)

            return task

        except Exception as e:
            # Clean up file on error
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document: {str(e)}",
            )

    async def get_overdue_tasks(self, limit: int = 100) -> List[ResearchTask]:
        """
        Get overdue tasks

        Args:
            limit: Maximum number of results

        Returns:
            List of overdue tasks
        """
        return await self.repo.get_overdue(limit)

    async def get_upcoming_tasks(self, days: int = 7, limit: int = 100) -> List[ResearchTask]:
        """
        Get upcoming tasks due within specified days

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
        Get task statistics

        Args:
            technology_id: Optional technology ID filter
            repository_id: Optional repository ID filter

        Returns:
            Dictionary with statistics
        """
        stats = await self.repo.get_statistics(
            technology_id=technology_id, repository_id=repository_id
        )

        # Add additional statistics
        overdue = await self.repo.get_overdue(limit=1000)
        upcoming = await self.repo.get_upcoming(days=7, limit=1000)

        stats["overdue_count"] = len(overdue)
        stats["upcoming_count"] = len(upcoming)

        return stats

    async def update_progress(self, task_id: int, progress_percentage: int) -> ResearchTask:
        """
        Update task progress percentage

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

        task = await self.get_task(task_id)
        task = await self.repo.update(task, progress_percentage=progress_percentage)

        # Auto-update status if progress reaches 100%
        if progress_percentage == 100 and task.status != TaskStatus.COMPLETED:
            task = await self.repo.update(
                task, status=TaskStatus.COMPLETED, completed_at=datetime.utcnow()
            )

        await self.db.commit()
        await self.db.refresh(task)

        return task
