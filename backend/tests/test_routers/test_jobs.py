"""
Tests for Jobs API router.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status

from app.models import Job, JobStatus, JobType


@pytest.mark.asyncio
class TestJobsRouter:
    """Test cases for Jobs API endpoints."""

    async def test_list_jobs_empty(self, client, mock_db):
        """Test listing jobs when none exist."""
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.list_jobs = AsyncMock(return_value=[])

            response = client.get("/api/v1/jobs")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["jobs"] == []
            assert data["total"] == 0
            assert data["skip"] == 0
            assert data["limit"] == 100

    async def test_list_jobs_with_data(self, client, mock_db, sample_job):
        """Test listing jobs with data."""
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.list_jobs = AsyncMock(return_value=[sample_job])

            response = client.get("/api/v1/jobs")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["jobs"]) == 1
            assert data["jobs"][0]["id"] == sample_job.id
            assert data["jobs"][0]["job_type"] == sample_job.job_type
            assert data["jobs"][0]["status"] == sample_job.status

    async def test_list_jobs_with_filters(self, client, mock_db, sample_job):
        """Test listing jobs with filters."""
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.list_jobs = AsyncMock(return_value=[sample_job])

            response = client.get(
                "/api/v1/jobs",
                params={
                    "project_id": 1,
                    "status_filter": "running",
                    "job_type": "analysis",
                },
            )

            assert response.status_code == status.HTTP_200_OK
            mock_service.return_value.list_jobs.assert_called_with(
                project_id=1,
                status_filter="running",
                job_type="analysis",
                skip=0,
                limit=100,
            )

    async def test_list_jobs_pagination(self, client, mock_db, sample_job):
        """Test listing jobs with pagination."""
        jobs = [sample_job for _ in range(5)]
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.list_jobs = AsyncMock(return_value=jobs)

            response = client.get("/api/v1/jobs", params={"skip": 10, "limit": 50})

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["skip"] == 10
            assert data["limit"] == 50

    async def test_create_job(self, client, mock_db, sample_job):
        """Test creating a new job."""
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.create_job = AsyncMock(return_value=sample_job)

            job_data = {
                "project_id": 1,
                "job_type": "analysis",
                "parameters": {"repo_url": "https://github.com/test/repo"},
                "tags": {"priority": "high"},
            }

            response = client.post("/api/v1/jobs", json=job_data)

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["id"] == sample_job.id
            assert data["job_type"] == sample_job.job_type
            assert data["status"] == sample_job.status

    async def test_create_job_minimal(self, client, mock_db, sample_job):
        """Test creating a job with minimal data."""
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.create_job = AsyncMock(return_value=sample_job)

            job_data = {"project_id": 1, "job_type": "analysis"}

            response = client.post("/api/v1/jobs", json=job_data)

            assert response.status_code == status.HTTP_201_CREATED

    async def test_get_job_found(self, client, mock_db, sample_job):
        """Test getting a job by ID."""
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.get_job = AsyncMock(return_value=sample_job)

            response = client.get(f"/api/v1/jobs/{sample_job.id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == sample_job.id
            assert data["job_type"] == sample_job.job_type

    async def test_get_job_not_found(self, client, mock_db):
        """Test getting a non-existent job."""
        from fastapi import HTTPException

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.get_job = AsyncMock(
                side_effect=HTTPException(status_code=404, detail="Job not found")
            )

            response = client.get("/api/v1/jobs/999")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_job_status(self, client, mock_db, sample_job):
        """Test updating job status."""
        updated_job = sample_job
        updated_job.status = JobStatus.RUNNING
        updated_job.progress = 50

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.update_job = AsyncMock(return_value=updated_job)

            update_data = {"status": "running", "progress": 50}

            response = client.patch(f"/api/v1/jobs/{sample_job.id}", json=update_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "running"
            assert data["progress"] == 50

    async def test_update_job_progress(self, client, mock_db, sample_job):
        """Test updating job progress."""
        updated_job = sample_job
        updated_job.progress = 75
        updated_job.current_step = "Processing files"

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.update_job = AsyncMock(return_value=updated_job)

            update_data = {"progress": 75, "current_step": "Processing files"}

            response = client.patch(f"/api/v1/jobs/{sample_job.id}", json=update_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["progress"] == 75
            assert data["current_step"] == "Processing files"

    async def test_update_job_result(self, client, mock_db, sample_job):
        """Test updating job with result."""
        updated_job = sample_job
        updated_job.status = JobStatus.COMPLETED
        updated_job.progress = 100
        updated_job.result = {"files_processed": 42}

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.update_job = AsyncMock(return_value=updated_job)

            update_data = {
                "status": "completed",
                "progress": 100,
                "result": {"files_processed": 42},
            }

            response = client.patch(f"/api/v1/jobs/{sample_job.id}", json=update_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"
            assert data["result"]["files_processed"] == 42

    async def test_update_job_error(self, client, mock_db, sample_job):
        """Test updating job with error."""
        updated_job = sample_job
        updated_job.status = JobStatus.FAILED
        updated_job.error = "Connection timeout"

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.update_job = AsyncMock(return_value=updated_job)

            update_data = {"status": "failed", "error": "Connection timeout"}

            response = client.patch(f"/api/v1/jobs/{sample_job.id}", json=update_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "failed"
            assert data["error"] == "Connection timeout"

    async def test_delete_job(self, client, mock_db):
        """Test deleting a job."""
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.delete_job = AsyncMock()

            response = client.delete("/api/v1/jobs/1")

            assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_job_not_found(self, client, mock_db):
        """Test deleting a non-existent job."""
        from fastapi import HTTPException

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.delete_job = AsyncMock(
                side_effect=HTTPException(status_code=404, detail="Job not found")
            )

            response = client.delete("/api/v1/jobs/999")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_cancel_job(self, client, mock_db, sample_job):
        """Test cancelling a job."""
        cancelled_job = sample_job
        cancelled_job.status = JobStatus.CANCELLED

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.cancel_job = AsyncMock(return_value=cancelled_job)

            response = client.post(f"/api/v1/jobs/{sample_job.id}/cancel")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "cancelled"

    async def test_cancel_completed_job(self, client, mock_db, sample_job):
        """Test cancelling an already completed job."""
        from fastapi import HTTPException

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.cancel_job = AsyncMock(
                side_effect=HTTPException(status_code=400, detail="Cannot cancel completed job")
            )

            response = client.post(f"/api/v1/jobs/{sample_job.id}/cancel")

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_job_progress(self, client, mock_db):
        """Test getting job progress information."""
        progress_data = {
            "job_id": 1,
            "status": "running",
            "progress": 65,
            "current_step": "Analyzing dependencies",
            "is_terminal": False,
            "is_active": True,
            "created_at": "2024-01-01T10:00:00",
            "started_at": "2024-01-01T10:01:00",
            "completed_at": None,
            "duration_seconds": None,
        }

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.get_job_progress = AsyncMock(return_value=progress_data)

            response = client.get("/api/v1/jobs/1/progress")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["job_id"] == 1
            assert data["progress"] == 65
            assert data["is_active"] is True

    async def test_list_active_jobs(self, client, mock_db, sample_job):
        """Test listing active jobs."""
        active_job = sample_job
        active_job.status = JobStatus.RUNNING

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.get_active_jobs = AsyncMock(return_value=[active_job])

            response = client.get("/api/v1/jobs/active/list")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["jobs"]) == 1
            assert data["jobs"][0]["status"] in ["pending", "running"]

    async def test_list_active_jobs_with_project_filter(self, client, mock_db, sample_job):
        """Test listing active jobs filtered by project."""
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.get_active_jobs = AsyncMock(return_value=[sample_job])

            response = client.get("/api/v1/jobs/active/list", params={"project_id": 1})

            assert response.status_code == status.HTTP_200_OK
            mock_service.return_value.get_active_jobs.assert_called_with(project_id=1)

    async def test_get_job_statistics(self, client, mock_db):
        """Test getting job statistics."""
        stats_data = {
            "total": 100,
            "by_status": {
                "pending": 5,
                "running": 3,
                "completed": 80,
                "failed": 10,
                "cancelled": 2,
            },
            "success_rate": 88.89,
            "average_duration_seconds": 125.5,
            "active_jobs": 8,
        }

        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.get_statistics = AsyncMock(return_value=stats_data)

            response = client.get("/api/v1/jobs/statistics/summary")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total"] == 100
            assert data["success_rate"] == 88.89
            assert data["active_jobs"] == 8

    async def test_get_job_statistics_with_project_filter(self, client, mock_db):
        """Test getting job statistics filtered by project."""
        with patch("app.routers.jobs.JobService") as mock_service:
            mock_service.return_value.get_statistics = AsyncMock(
                return_value={"total": 10, "by_status": {}, "active_jobs": 2}
            )

            response = client.get("/api/v1/jobs/statistics/summary", params={"project_id": 1})

            assert response.status_code == status.HTTP_200_OK
            mock_service.return_value.get_statistics.assert_called_with(project_id=1)


# Fixtures
@pytest.fixture
def sample_job():
    """Create a sample job for testing."""
    return Job(
        id=1,
        project_id=1,
        celery_task_id="abc-123-def",
        job_type=JobType.ANALYSIS,
        status=JobStatus.PENDING,
        progress=0,
        current_step=None,
        parameters={"repo_url": "https://github.com/test/repo"},
        result=None,
        error=None,
        traceback=None,
        created_by=1,
        tags={"priority": "high"},
        created_at=datetime.utcnow(),
        started_at=None,
        completed_at=None,
    )


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()
