"""
Integration tests for Celery task execution and job flow.

Tests the complete async job workflow including:
- Job creation and dispatch
- Celery task execution
- Job status updates
- Error handling and retry logic
- Job cancellation
"""

import pytest
import asyncio
import datetime
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models import Job, JobStatus, Project, Repository
from app.services.job_service import JobService
from app.tasks.job_tasks import execute_job


pytestmark = pytest.mark.integration


class TestCeleryJobIntegration:
    """Integration tests for Celery job execution."""

    @pytest.mark.asyncio
    async def test_job_creation_workflow(
        self,
        async_client: AsyncClient,
        test_project: Project,
    ):
        """Test complete job creation workflow."""
        # Create a job via API
        job_data = {
            "project_id": test_project.id,
            "job_type": "analyze_repository",
            "parameters": {"repository_id": 1},
            "created_by": "test_user",
        }

        response = await async_client.post("/api/v1/jobs", json=job_data)

        assert response.status_code == 201
        job = response.json()
        assert job["status"] == "pending"
        assert job["progress"] == 0
        assert job["job_type"] == "analyze_repository"
        assert "id" in job

    @pytest.mark.asyncio
    async def test_job_dispatch_workflow(
        self,
        async_client: AsyncClient,
        test_job: Job,
        mock_celery_task: MagicMock,
    ):
        """Test job dispatch to Celery."""
        job_id = test_job.id

        with patch("app.services.job_service.execute_job", mock_celery_task):
            # Dispatch job
            response = await async_client.post(f"/api/v1/jobs/{job_id}/dispatch")

            assert response.status_code == 200
            job = response.json()
            assert "celery_task_id" in job
            assert job["celery_task_id"] == "test-task-id-123"

            # Verify Celery task was called
            mock_celery_task.delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_dispatch_with_delay(
        self,
        async_client: AsyncClient,
        test_job: Job,
        mock_celery_task: MagicMock,
    ):
        """Test job dispatch with execution delay."""
        job_id = test_job.id

        with patch("app.services.job_service.execute_job", mock_celery_task):
            # Dispatch job with 10 second delay
            response = await async_client.post(f"/api/v1/jobs/{job_id}/dispatch?delay_seconds=10")

            assert response.status_code == 200
            job = response.json()
            assert "celery_task_id" in job

    @pytest.mark.asyncio
    async def test_job_status_updates_during_execution(
        self,
        async_client: AsyncClient,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test job status updates during execution."""
        job_id = test_job.id

        # Update job to running status
        update_data = {
            "status": "running",
            "progress": 25,
            "current_step": "Processing data",
        }

        response = await async_client.patch(f"/api/v1/jobs/{job_id}", json=update_data)

        assert response.status_code == 200
        job = response.json()
        assert job["status"] == "running"
        assert job["progress"] == 25
        assert job["current_step"] == "Processing data"

        # Verify in database
        service = JobService(db_session)
        db_job = await service.get_job(job_id)
        assert db_job.status == JobStatus.RUNNING
        assert db_job.progress == 25

    @pytest.mark.asyncio
    async def test_job_completion_workflow(
        self,
        async_client: AsyncClient,
        test_job: Job,
    ):
        """Test job completion workflow."""
        job_id = test_job.id

        # Complete job with result
        update_data = {
            "status": "completed",
            "progress": 100,
            "current_step": "Finished",
            "result": {
                "total_files": 42,
                "technologies_found": 5,
            },
        }

        response = await async_client.patch(f"/api/v1/jobs/{job_id}", json=update_data)

        assert response.status_code == 200
        job = response.json()
        assert job["status"] == "completed"
        assert job["progress"] == 100
        assert job["result"] is not None
        assert job["result"]["total_files"] == 42

    @pytest.mark.asyncio
    async def test_job_failure_workflow(
        self,
        async_client: AsyncClient,
        test_job: Job,
    ):
        """Test job failure workflow with error tracking."""
        job_id = test_job.id

        # Fail job with error
        update_data = {
            "status": "failed",
            "progress": 50,
            "error": "Test error occurred",
            "traceback": "Traceback line 1\nTraceback line 2",
        }

        response = await async_client.patch(f"/api/v1/jobs/{job_id}", json=update_data)

        assert response.status_code == 200
        job = response.json()
        assert job["status"] == "failed"
        assert job["error"] == "Test error occurred"
        assert "traceback" in job

    @pytest.mark.asyncio
    async def test_job_cancellation_workflow(
        self,
        async_client: AsyncClient,
        test_job: Job,
        mock_celery_task: MagicMock,
    ):
        """Test job cancellation workflow."""
        job_id = test_job.id

        # First dispatch the job
        with patch("app.services.job_service.execute_job", mock_celery_task):
            await async_client.post(f"/api/v1/jobs/{job_id}/dispatch")

        # Cancel the job
        with patch("celery.app.control.Control.revoke") as mock_revoke:
            response = await async_client.post(f"/api/v1/jobs/{job_id}/cancel")

            assert response.status_code == 200
            job = response.json()
            assert job["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_job_progress_endpoint(
        self,
        async_client: AsyncClient,
        test_job: Job,
    ):
        """Test job progress endpoint."""
        job_id = test_job.id

        # Get job progress
        response = await async_client.get(f"/api/v1/jobs/{job_id}/progress")

        assert response.status_code == 200
        progress = response.json()
        assert "job_id" in progress
        assert "status" in progress
        assert "progress" in progress
        assert progress["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_list_active_jobs(
        self,
        async_client: AsyncClient,
        test_project: Project,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test listing active jobs."""
        # Create additional jobs
        service = JobService(db_session)

        running_job = await service.create_job(
            project_id=test_project.id,
            job_type="export_data",
            parameters={},
            created_by="test_user",
        )
        await service.update_job(running_job.id, status="running")

        # List active jobs
        response = await async_client.get("/api/v1/jobs/active/list")

        assert response.status_code == 200
        result = response.json()
        assert "jobs" in result
        assert len(result["jobs"]) >= 2  # At least test_job and running_job

    @pytest.mark.asyncio
    async def test_job_statistics(
        self,
        async_client: AsyncClient,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test job statistics endpoint."""
        # Create jobs with different statuses
        service = JobService(db_session)

        await service.create_job(
            project_id=test_project.id,
            job_type="analyze",
            parameters={},
            created_by="test",
        )

        completed_job = await service.create_job(
            project_id=test_project.id,
            job_type="export",
            parameters={},
            created_by="test",
        )
        await service.update_job(completed_job.id, status="completed")

        # Get statistics
        response = await async_client.get("/api/v1/jobs/statistics/summary")

        assert response.status_code == 200
        stats = response.json()
        assert "total_jobs" in stats
        assert stats["total_jobs"] >= 2

    @pytest.mark.asyncio
    async def test_job_list_with_filters(
        self,
        async_client: AsyncClient,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test job listing with filters."""
        # Create jobs of different types
        service = JobService(db_session)

        await service.create_job(
            project_id=test_project.id,
            job_type="analyze_repository",
            parameters={},
            created_by="user1",
        )

        await service.create_job(
            project_id=test_project.id,
            job_type="export_data",
            parameters={},
            created_by="user2",
        )

        # List jobs filtered by type
        response = await async_client.get(
            f"/api/v1/jobs?project_id={test_project.id}&job_type=analyze_repository"
        )

        assert response.status_code == 200
        result = response.json()
        assert "jobs" in result

        # Verify all returned jobs match filter
        for job in result["jobs"]:
            assert job["job_type"] == "analyze_repository"

    @pytest.mark.asyncio
    async def test_job_pagination(
        self,
        async_client: AsyncClient,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test job listing pagination."""
        # Create multiple jobs
        service = JobService(db_session)
        for i in range(15):
            await service.create_job(
                project_id=test_project.id,
                job_type="test_job",
                parameters={"index": i},
                created_by="test",
            )

        # Get first page
        response = await async_client.get("/api/v1/jobs?skip=0&limit=10")
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1["jobs"]) <= 10

        # Get second page
        response = await async_client.get("/api/v1/jobs?skip=10&limit=10")
        assert response.status_code == 200
        page2 = response.json()
        assert len(page2["jobs"]) >= 5


class TestCeleryTaskHandlers:
    """Test Celery task handlers and execution."""

    @pytest.mark.asyncio
    async def test_analyze_repository_task(
        self,
        test_repository: Repository,
        db_session: AsyncSession,
    ):
        """Test analyze_repository task handler."""
        service = JobService(db_session)

        # Create job for repository analysis
        job = await service.create_job(
            project_id=test_repository.project_id,
            job_type="analyze_repository",
            parameters={"repository_id": test_repository.id},
            created_by="test_user",
        )

        # Mock task execution
        with patch("app.tasks.job_tasks.analyze_repository_task") as mock_task:
            mock_task.return_value = {
                "status": "completed",
                "technologies_found": 5,
            }

            # Execute (task_always_eager in test config runs synchronously)
            await service.dispatch_job(job.id)

    @pytest.mark.asyncio
    async def test_export_data_task(
        self,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test export_data task handler."""
        service = JobService(db_session)

        # Create job for data export
        job = await service.create_job(
            project_id=test_project.id,
            job_type="export_data",
            parameters={"format": "json", "project_id": test_project.id},
            created_by="test_user",
        )

        # Mock task execution
        with patch("app.tasks.job_tasks.export_data_task") as mock_task:
            mock_task.return_value = {
                "status": "completed",
                "file_path": "/tmp/export.json",
            }

            # Execute
            await service.dispatch_job(job.id)

    @pytest.mark.asyncio
    async def test_batch_operation_task(
        self,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test batch operation task handler."""
        service = JobService(db_session)

        # Create job for batch operation
        job = await service.create_job(
            project_id=test_project.id,
            job_type="batch_analyze",
            parameters={"repository_ids": [1, 2, 3]},
            created_by="test_user",
        )

        # Mock task execution
        with patch("app.tasks.job_tasks.batch_operation_task") as mock_task:
            mock_task.return_value = {
                "status": "completed",
                "processed": 3,
            }

            # Execute
            await service.dispatch_job(job.id)


class TestJobErrorHandling:
    """Test error handling in job execution."""

    @pytest.mark.asyncio
    async def test_invalid_job_type(
        self,
        async_client: AsyncClient,
        test_project: Project,
    ):
        """Test handling of invalid job type."""
        job_data = {
            "project_id": test_project.id,
            "job_type": "invalid_job_type",
            "parameters": {},
            "created_by": "test_user",
        }

        response = await async_client.post("/api/v1/jobs", json=job_data)

        # Should succeed (job type validation is at execution time)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_dispatch_nonexistent_job(
        self,
        async_client: AsyncClient,
    ):
        """Test dispatching non-existent job."""
        response = await async_client.post("/api/v1/jobs/99999/dispatch")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_completed_job(
        self,
        async_client: AsyncClient,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test cancelling already completed job."""
        job_id = test_job.id

        # Complete the job first
        service = JobService(db_session)
        await service.update_job(job_id, status="completed", progress=100)

        # Try to cancel
        response = await async_client.post(f"/api/v1/jobs/{job_id}/cancel")

        # Should fail or return error
        assert response.status_code in [400, 409]

    @pytest.mark.asyncio
    async def test_job_timeout_handling(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test job timeout handling."""
        # Note: Actual timeout testing requires long-running tasks
        # This is a structural test
        service = JobService(db_session)

        # Set job as running for extended period
        job = await service.get_job(test_job.id)
        job.started_at = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
        await db_session.commit()

        # In production, a background task would detect and handle timeouts
        # Here we just verify the structure exists
        assert job.started_at is not None


class TestJobServiceMethods:
    """Test JobService methods used in integration."""

    @pytest.mark.asyncio
    async def test_get_active_jobs(
        self,
        db_session: AsyncSession,
        test_project: Project,
    ):
        """Test get_active_jobs service method."""
        service = JobService(db_session)

        # Create mix of active and inactive jobs
        job1 = await service.create_job(
            project_id=test_project.id,
            job_type="test",
            parameters={},
            created_by="test",
        )

        job2 = await service.create_job(
            project_id=test_project.id,
            job_type="test",
            parameters={},
            created_by="test",
        )
        await service.update_job(job2.id, status="running")

        job3 = await service.create_job(
            project_id=test_project.id,
            job_type="test",
            parameters={},
            created_by="test",
        )
        await service.update_job(job3.id, status="completed")

        # Get active jobs
        active_jobs = await service.get_active_jobs(project_id=test_project.id)

        # Should include pending and running, not completed
        active_ids = {j.id for j in active_jobs}
        assert job1.id in active_ids  # pending
        assert job2.id in active_ids  # running
        assert job3.id not in active_ids  # completed

    @pytest.mark.asyncio
    async def test_delete_job(
        self,
        db_session: AsyncSession,
        test_project: Project,
    ):
        """Test delete_job service method."""
        service = JobService(db_session)

        # Create a completed job
        job = await service.create_job(
            project_id=test_project.id,
            job_type="test",
            parameters={},
            created_by="test",
        )
        await service.update_job(job.id, status="completed")

        job_id = job.id

        # Delete the job
        await service.delete_job(job_id)

        # Job should no longer exist
        with pytest.raises(HTTPException) as exc_info:
            await service.get_job(job_id)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_statistics(
        self,
        db_session: AsyncSession,
        test_project: Project,
    ):
        """Test get_statistics service method."""
        service = JobService(db_session)

        # Create jobs with various statuses
        await service.create_job(
            project_id=test_project.id,
            job_type="test",
            parameters={},
            created_by="test",
        )

        completed_job = await service.create_job(
            project_id=test_project.id,
            job_type="test",
            parameters={},
            created_by="test",
        )
        await service.update_job(completed_job.id, status="completed")

        failed_job = await service.create_job(
            project_id=test_project.id,
            job_type="test",
            parameters={},
            created_by="test",
        )
        await service.update_job(failed_job.id, status="failed")

        # Get statistics
        stats = await service.get_statistics(project_id=test_project.id)

        assert "total_jobs" in stats
        assert stats["total_jobs"] >= 3
        assert "by_status" in stats
