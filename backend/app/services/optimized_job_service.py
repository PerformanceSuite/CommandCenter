"""
Optimized Job Service with performance improvements.
Fixes N+1 query pattern and adds efficient pagination.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, Integer
import sqlalchemy as sa
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.models import Job, JobStatus


class OptimizedJobService:
    """Optimized service layer for job operations with performance improvements."""

    # Thread pool for blocking operations
    _executor = ThreadPoolExecutor(max_workers=4)

    def __init__(self, db: AsyncSession):
        """
        Initialize optimized job service.

        Args:
            db: Database session
        """
        self.db = db

    async def list_jobs_with_count(
        self,
        project_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        job_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Job], int]:
        """
        List jobs with total count in a single query.
        Fixes N+1 query pattern.

        Args:
            project_id: Optional project ID filter
            status_filter: Optional status filter
            job_type: Optional job type filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            Tuple of (list of jobs, total count)
        """
        # Build base query with window function for count
        count_window = func.count().over()

        base_query = select(Job, count_window.label("total_count"))

        # Apply filters
        filters = []
        if project_id:
            filters.append(Job.project_id == project_id)
        if status_filter:
            filters.append(Job.status == status_filter)
        if job_type:
            filters.append(Job.job_type == job_type)

        if filters:
            base_query = base_query.where(and_(*filters))

        # Order by created_at descending (newest first)
        base_query = base_query.order_by(Job.created_at.desc())

        # Apply pagination
        query = base_query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        rows = result.all()

        # Extract jobs and total count
        if rows:
            jobs = [row[0] for row in rows]
            total = rows[0][1]  # Total count is same in all rows
        else:
            jobs = []
            # If no rows, need separate count query
            count_query = select(func.count()).select_from(Job)
            if filters:
                count_query = count_query.where(and_(*filters))
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0

        return jobs, total

    async def list_jobs_cursor_based(
        self,
        cursor: Optional[datetime] = None,
        project_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        List jobs using cursor-based pagination for better performance.
        More efficient than offset-based pagination for large datasets.

        Args:
            cursor: DateTime cursor for pagination
            project_id: Optional project ID filter
            status_filter: Optional status filter
            job_type: Optional job type filter
            limit: Maximum number of records

        Returns:
            Dictionary with items, next_cursor, and has_next
        """
        query = select(Job)

        # Apply filters
        filters = []
        if cursor:
            filters.append(Job.created_at < cursor)
        if project_id:
            filters.append(Job.project_id == project_id)
        if status_filter:
            filters.append(Job.status == status_filter)
        if job_type:
            filters.append(Job.job_type == job_type)

        if filters:
            query = query.where(and_(*filters))

        # Order by created_at descending
        query = query.order_by(Job.created_at.desc())

        # Fetch limit + 1 to determine if there are more results
        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        jobs = list(result.scalars().all())

        # Check if there are more results
        has_next = len(jobs) > limit
        jobs = jobs[:limit]

        # Determine next cursor
        next_cursor = jobs[-1].created_at if has_next and jobs else None

        return {
            "items": jobs,
            "next_cursor": next_cursor.isoformat() if next_cursor else None,
            "has_next": has_next,
            "count": len(jobs),
        }

    async def get_statistics_optimized(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get job statistics with optimized query.
        Uses aggregation functions instead of loading all records.

        Args:
            project_id: Optional project ID filter

        Returns:
            Dictionary with statistics
        """
        # Build base filter
        base_filter = Job.project_id == project_id if project_id else True

        # Single query for all counts using conditional aggregation
        query = select(
            func.count(Job.id).label("total"),
            func.sum(func.cast(Job.status == JobStatus.PENDING, Integer)).label("pending"),
            func.sum(func.cast(Job.status == JobStatus.RUNNING, Integer)).label("running"),
            func.sum(func.cast(Job.status == JobStatus.COMPLETED, Integer)).label("completed"),
            func.sum(func.cast(Job.status == JobStatus.FAILED, Integer)).label("failed"),
            func.sum(func.cast(Job.status == JobStatus.CANCELLED, Integer)).label("cancelled"),
            func.avg(
                func.case(
                    (
                        Job.status == JobStatus.COMPLETED,
                        func.extract("epoch", Job.completed_at - Job.started_at),
                    ),
                    else_=None,
                )
            ).label("avg_duration"),
        ).where(base_filter)

        result = await self.db.execute(query)
        stats = result.one()

        # Calculate success rate
        completed = stats.completed or 0
        failed = stats.failed or 0
        success_rate = (
            (completed / (completed + failed) * 100) if (completed + failed) > 0 else None
        )

        return {
            "total": stats.total or 0,
            "by_status": {
                "pending": stats.pending or 0,
                "running": stats.running or 0,
                "completed": completed,
                "failed": failed,
                "cancelled": stats.cancelled or 0,
            },
            "success_rate": success_rate,
            "average_duration_seconds": stats.avg_duration,
            "active_jobs": (stats.pending or 0) + (stats.running or 0),
        }

    async def cancel_job_async(self, job_id: int) -> Job:
        """
        Cancel a job with non-blocking Celery operation.

        Args:
            job_id: Job ID

        Returns:
            Cancelled job

        Raises:
            HTTPException: If job not found or already completed
        """
        # Get job (reuse existing method)
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Check if job can be cancelled
        if job.is_terminal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is already in terminal state: {job.status}",
            )

        # Cancel Celery task asynchronously if it exists
        if job.celery_task_id:
            try:
                from app.tasks import celery_app

                # Run blocking operation in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self._executor,
                    lambda: celery_app.control.revoke(job.celery_task_id, terminate=True),
                )
            except Exception as e:
                # Log error but don't fail the cancellation
                print(f"Failed to revoke Celery task {job.celery_task_id}: {e}")

        # Update job status
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def batch_update_status(self, job_ids: List[int], status: str) -> int:
        """
        Batch update job statuses for efficiency.

        Args:
            job_ids: List of job IDs
            status: New status

        Returns:
            Number of jobs updated
        """
        if not job_ids:
            return 0

        # Build update query
        stmt = (
            sa.update(Job)
            .where(Job.id.in_(job_ids))
            .values(
                status=status,
                completed_at=(
                    datetime.utcnow()
                    if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
                    else None
                ),
            )
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount

    async def get_jobs_by_celery_ids(self, celery_task_ids: List[str]) -> Dict[str, Job]:
        """
        Get multiple jobs by their Celery task IDs in a single query.

        Args:
            celery_task_ids: List of Celery task UUIDs

        Returns:
            Dictionary mapping Celery task ID to Job
        """
        if not celery_task_ids:
            return {}

        result = await self.db.execute(select(Job).where(Job.celery_task_id.in_(celery_task_ids)))
        jobs = result.scalars().all()

        return {job.celery_task_id: job for job in jobs}
