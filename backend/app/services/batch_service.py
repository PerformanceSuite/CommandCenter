"""
Batch service for bulk operations on repositories, technologies, and analyses.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.repository import Repository
from app.services.job_service import JobService


class BatchService:
    """
    Service for handling batch operations including:
    - Batch repository analysis
    - Batch technology import/export
    - Bulk data operations
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_service = JobService(db)

    async def analyze_repositories(
        self,
        project_id: int,
        repository_ids: List[int],
        priority: int = 5,
        parameters: Optional[Dict[str, Any]] = None,
        notify_on_complete: bool = True,
        tags: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None,
    ) -> Job:
        """
        Create a batch analysis job for multiple repositories.

        Args:
            project_id: Project ID
            repository_ids: List of repository IDs to analyze
            priority: Job priority (1-10)
            parameters: Additional analysis parameters
            notify_on_complete: Send notification when complete
            tags: Custom tags for filtering
            created_by: User ID who created the batch

        Returns:
            Job object for the batch operation
        """
        # Validate repositories exist and belong to project
        stmt = select(Repository).where(
            and_(Repository.id.in_(repository_ids), Repository.project_id == project_id)
        )
        result = await self.db.execute(stmt)
        repositories = result.scalars().all()

        if len(repositories) != len(repository_ids):
            found_ids = {r.id for r in repositories}
            missing_ids = set(repository_ids) - found_ids
            raise ValueError(f"Repositories not found: {missing_ids}")

        # Prepare batch parameters
        batch_params = {
            "repository_ids": repository_ids,
            "notify_on_complete": notify_on_complete,
            "total_items": len(repository_ids),
            **(parameters or {}),
        }

        # Create batch job
        job = await self.job_service.create_job(
            project_id=project_id,
            job_type="batch_analysis",
            parameters=batch_params,
            priority=priority,
            tags=tags or {},
            created_by=created_by,
        )

        return job

    async def export_analyses(
        self,
        project_id: int,
        analysis_ids: List[int],
        format: str,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None,
    ) -> Job:
        """
        Create a batch export job for multiple analyses.

        Args:
            project_id: Project ID
            analysis_ids: List of analysis IDs to export
            format: Export format (sarif, markdown, html, csv, json)
            parameters: Format-specific parameters
            tags: Custom tags for filtering
            created_by: User ID who created the batch

        Returns:
            Job object for the batch export operation
        """
        # Validate format
        valid_formats = {"sarif", "markdown", "html", "csv", "json"}
        if format not in valid_formats:
            raise ValueError(f"Invalid export format '{format}'. Must be one of: {valid_formats}")

        # Prepare batch parameters
        batch_params = {
            "analysis_ids": analysis_ids,
            "format": format,
            "total_items": len(analysis_ids),
            **(parameters or {}),
        }

        # Create batch job
        job = await self.job_service.create_job(
            project_id=project_id,
            job_type="batch_export",
            parameters=batch_params,
            priority=5,
            tags=tags or {},
            created_by=created_by,
        )

        return job

    async def import_technologies(
        self,
        project_id: int,
        technologies: List[Dict[str, Any]],
        merge_strategy: str = "skip",
        tags: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None,
    ) -> Job:
        """
        Create a batch import job for technologies.

        Args:
            project_id: Project ID
            technologies: List of technology dictionaries to import
            merge_strategy: Conflict resolution (skip, overwrite, merge)
            tags: Custom tags for filtering
            created_by: User ID who created the batch

        Returns:
            Job object for the batch import operation
        """
        # Validate merge strategy
        valid_strategies = {"skip", "overwrite", "merge"}
        if merge_strategy not in valid_strategies:
            raise ValueError(
                f"Invalid merge strategy '{merge_strategy}'. " f"Must be one of: {valid_strategies}"
            )

        # Validate technology data (basic validation)
        required_fields = {"title", "domain"}
        for i, tech in enumerate(technologies):
            missing = required_fields - set(tech.keys())
            if missing:
                raise ValueError(f"Technology at index {i} missing required fields: {missing}")

        # Prepare batch parameters
        batch_params = {
            "technologies": technologies,
            "merge_strategy": merge_strategy,
            "total_items": len(technologies),
        }

        # Create batch job
        job = await self.job_service.create_job(
            project_id=project_id,
            job_type="batch_import",
            parameters=batch_params,
            priority=5,
            tags=tags or {},
            created_by=created_by,
        )

        return job

    async def get_batch_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics for batch operations.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            Dictionary with batch statistics
        """
        # Build query
        stmt = select(Job).where(
            Job.job_type.in_(["batch_analysis", "batch_export", "batch_import"])
        )
        if project_id:
            stmt = stmt.where(Job.project_id == project_id)

        result = await self.db.execute(stmt)
        jobs = result.scalars().all()

        # Calculate statistics
        total_batches = len(jobs)
        active_batches = len([j for j in jobs if j.status in ["pending", "running"]])

        by_type = {}
        by_status = {}
        durations = []

        for job in jobs:
            # Count by type
            by_type[job.job_type] = by_type.get(job.job_type, 0) + 1

            # Count by status
            by_status[job.status] = by_status.get(job.status, 0) + 1

            # Collect durations
            if job.duration_seconds is not None:
                durations.append(job.duration_seconds)

        # Calculate averages and rates
        avg_duration = sum(durations) / len(durations) if durations else None
        completed = by_status.get("completed", 0)
        failed = by_status.get("failed", 0)
        success_rate = (
            (completed / (completed + failed)) * 100 if (completed + failed) > 0 else None
        )

        return {
            "total_batches": total_batches,
            "active_batches": active_batches,
            "by_type": by_type,
            "by_status": by_status,
            "average_duration_seconds": avg_duration,
            "success_rate": success_rate,
        }
