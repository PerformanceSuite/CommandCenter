"""
Job business logic service.
Handles async job operations with Celery integration.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models import Job, JobStatus, JobType
from celery.result import AsyncResult


class JobService:
    """Service layer for job operations with Celery integration."""

    def __init__(self, db: AsyncSession):
        """
        Initialize job service.

        Args:
            db: Database session
        """
        self.db = db

    async def list_jobs(
        self,
        project_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        job_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Job]:
        """
        List jobs with optional filters.

        Args:
            project_id: Optional project ID filter
            status_filter: Optional status filter
            job_type: Optional job type filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of jobs
        """
        query = select(Job)

        # Apply filters
        filters = []
        if project_id:
            filters.append(Job.project_id == project_id)
        if status_filter:
            filters.append(Job.status == status_filter)
        if job_type:
            filters.append(Job.job_type == job_type)

        if filters:
            query = query.where(and_(*filters))

        # Order by created_at descending (newest first)
        query = query.order_by(Job.created_at.desc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_job(self, job_id: int) -> Job:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job

        Raises:
            HTTPException: If job not found
        """
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        return job

    async def get_job_by_celery_task_id(self, celery_task_id: str) -> Optional[Job]:
        """
        Get job by Celery task ID.

        Args:
            celery_task_id: Celery task UUID

        Returns:
            Job or None if not found
        """
        result = await self.db.execute(
            select(Job).where(Job.celery_task_id == celery_task_id)
        )
        return result.scalar_one_or_none()

    async def create_job(
        self,
        project_id: int,
        job_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None,
        celery_task_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """
        Create new job.

        Args:
            project_id: Project ID
            job_type: Job type (analysis, export, etc.)
            parameters: Job parameters
            created_by: User ID who created the job
            celery_task_id: Optional Celery task UUID
            tags: Optional custom tags

        Returns:
            Created job
        """
        job = Job(
            project_id=project_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            progress=0,
            parameters=parameters or {},
            created_by=created_by,
            celery_task_id=celery_task_id,
            tags=tags or {},
            created_at=datetime.utcnow(),
        )

        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def update_job(
        self,
        job_id: int,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        traceback: Optional[str] = None,
    ) -> Job:
        """
        Update job status and progress.

        Args:
            job_id: Job ID
            status: Optional new status
            progress: Optional progress (0-100)
            current_step: Optional current step description
            result: Optional result data
            error: Optional error message
            traceback: Optional error traceback

        Returns:
            Updated job

        Raises:
            HTTPException: If job not found
        """
        job = await self.get_job(job_id)

        # Update fields
        if status is not None:
            job.status = status

            # Set timestamps based on status
            if status == JobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in [
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            ]:
                job.completed_at = datetime.utcnow()

        if progress is not None:
            job.progress = max(0, min(100, progress))  # Clamp to 0-100

        if current_step is not None:
            job.current_step = current_step

        if result is not None:
            job.result = result

        if error is not None:
            job.error = error

        if traceback is not None:
            job.traceback = traceback

        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def cancel_job(self, job_id: int) -> Job:
        """
        Cancel a running or pending job.

        Args:
            job_id: Job ID

        Returns:
            Cancelled job

        Raises:
            HTTPException: If job not found or already completed
        """
        job = await self.get_job(job_id)

        # Check if job can be cancelled
        if job.is_terminal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is already in terminal state: {job.status}",
            )

        # Cancel Celery task if it exists
        if job.celery_task_id:
            try:
                from app.tasks import celery_app

                celery_app.control.revoke(job.celery_task_id, terminate=True)
            except Exception as e:
                # Log error but don't fail the cancellation
                print(f"Failed to revoke Celery task {job.celery_task_id}: {e}")

        # Update job status
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def delete_job(self, job_id: int) -> None:
        """
        Delete job.

        Args:
            job_id: Job ID

        Raises:
            HTTPException: If job not found
        """
        job = await self.get_job(job_id)

        # Don't delete running jobs
        if job.status == JobStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete running job {job_id}. Cancel it first.",
            )

        await self.db.delete(job)
        await self.db.commit()

    async def get_job_progress(self, job_id: int) -> Dict[str, Any]:
        """
        Get job progress information.

        Args:
            job_id: Job ID

        Returns:
            Progress information

        Raises:
            HTTPException: If job not found
        """
        job = await self.get_job(job_id)

        progress_info = {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step,
            "is_terminal": job.is_terminal,
            "is_active": job.is_active,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
        }

        # Try to get Celery task status if available
        if job.celery_task_id:
            try:
                async_result = AsyncResult(job.celery_task_id)
                progress_info["celery_status"] = async_result.status
                progress_info["celery_info"] = async_result.info
            except Exception:
                # Celery task not found or error - ignore
                pass

        return progress_info

    async def get_active_jobs(
        self, project_id: Optional[int] = None
    ) -> List[Job]:
        """
        Get all active (pending or running) jobs.

        Args:
            project_id: Optional project ID filter

        Returns:
            List of active jobs
        """
        query = select(Job).where(
            or_(Job.status == JobStatus.PENDING, Job.status == JobStatus.RUNNING)
        )

        if project_id:
            query = query.where(Job.project_id == project_id)

        query = query.order_by(Job.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get job statistics.

        Args:
            project_id: Optional project ID filter

        Returns:
            Dictionary with statistics
        """
        # Build base query
        query = select(Job)
        if project_id:
            query = query.where(Job.project_id == project_id)

        result = await self.db.execute(query)
        all_jobs = list(result.scalars().all())

        # Calculate statistics
        total = len(all_jobs)
        pending = sum(1 for j in all_jobs if j.status == JobStatus.PENDING)
        running = sum(1 for j in all_jobs if j.status == JobStatus.RUNNING)
        completed = sum(1 for j in all_jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in all_jobs if j.status == JobStatus.FAILED)
        cancelled = sum(1 for j in all_jobs if j.status == JobStatus.CANCELLED)

        # Calculate average duration for completed jobs
        completed_jobs = [j for j in all_jobs if j.duration_seconds is not None]
        avg_duration = (
            sum(j.duration_seconds for j in completed_jobs) / len(completed_jobs)
            if completed_jobs
            else None
        )

        return {
            "total": total,
            "by_status": {
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "cancelled": cancelled,
            },
            "success_rate": (
                (completed / (completed + failed) * 100)
                if (completed + failed) > 0
                else None
            ),
            "average_duration_seconds": avg_duration,
            "active_jobs": pending + running,
        }

    async def dispatch_job(
        self,
        job_id: int,
        delay_seconds: int = 0,
    ) -> str:
        """
        Dispatch a job to Celery for async execution.

        Args:
            job_id: Job ID to execute
            delay_seconds: Optional delay before execution (default: 0)

        Returns:
            str: Celery task ID

        Raises:
            HTTPException: If job not found or cannot be dispatched
        """
        job = await self.get_job(job_id)

        # Check if job is in pending status
        if job.status != JobStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} cannot be dispatched (status: {job.status})",
            )

        # Import Celery task
        from app.tasks.job_tasks import execute_job

        # Dispatch job to Celery
        if delay_seconds > 0:
            # Schedule for future execution
            task = execute_job.apply_async(
                args=[job_id, job.job_type, job.parameters],
                countdown=delay_seconds,
            )
        else:
            # Execute immediately
            task = execute_job.delay(job_id, job.job_type, job.parameters)

        # Update job with Celery task ID
        job.celery_task_id = task.id
        await self.db.commit()
        await self.db.refresh(job)

        return task.id
