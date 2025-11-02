"""
Tests for batch operations API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status

from app.models.job import Job


@pytest.fixture
def mock_batch_service():
    """Mock BatchService for testing."""
    with patch("app.routers.batch.BatchService") as mock:
        service = mock.return_value
        yield service


@pytest.fixture
def sample_job():
    """Sample job object for testing."""
    job = Job(
        id=1,
        project_id=1,
        job_type="batch_analysis",
        status="pending",
        progress=0,
        parameters={
            "repository_ids": [1, 2, 3],
            "notify_on_complete": True,
            "total_items": 3,
        },
        tags={},
        celery_task_id=None,
        result=None,
        error=None,
    )
    return job


class TestBatchAnalyze:
    """Tests for POST /api/v1/batch/analyze endpoint."""

    async def test_batch_analyze_success(self, client, mock_batch_service, sample_job):
        """Test successful batch analysis creation."""
        mock_batch_service.analyze_repositories = AsyncMock(return_value=sample_job)

        response = client.post(
            "/api/v1/batch/analyze",
            json={
                "repository_ids": [1, 2, 3],
                "priority": 8,
                "parameters": {"analyze_dependencies": True},
                "notify_on_complete": True,
            },
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["job_id"] == 1
        assert data["job_type"] == "batch_analysis"
        assert data["total_items"] == 3
        assert data["status"] == "pending"
        assert data["repository_ids"] == [1, 2, 3]

        mock_batch_service.analyze_repositories.assert_called_once()

    async def test_batch_analyze_empty_list(self, client):
        """Test batch analysis with empty repository list."""
        response = client.post(
            "/api/v1/batch/analyze",
            json={"repository_ids": []},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_batch_analyze_invalid_repositories(self, client, mock_batch_service):
        """Test batch analysis with invalid repository IDs."""
        mock_batch_service.analyze_repositories = AsyncMock(
            side_effect=ValueError("Repositories not found: {99}")
        )

        response = client.post(
            "/api/v1/batch/analyze",
            json={"repository_ids": [99]},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found" in response.json()["detail"]

    async def test_batch_analyze_with_defaults(self, client, mock_batch_service, sample_job):
        """Test batch analysis with default parameters."""
        mock_batch_service.analyze_repositories = AsyncMock(return_value=sample_job)

        response = client.post(
            "/api/v1/batch/analyze",
            json={"repository_ids": [1, 2, 3]},
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

        # Verify defaults were applied
        call_args = mock_batch_service.analyze_repositories.call_args
        assert call_args.kwargs["priority"] == 5  # Default priority
        assert call_args.kwargs["notify_on_complete"] is True  # Default notify

    async def test_batch_analyze_service_error(self, client, mock_batch_service):
        """Test batch analysis with service error."""
        mock_batch_service.analyze_repositories = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        response = client.post(
            "/api/v1/batch/analyze",
            json={"repository_ids": [1, 2, 3]},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create batch analysis" in response.json()["detail"]


class TestBatchExport:
    """Tests for POST /api/v1/batch/export endpoint."""

    async def test_batch_export_success(self, client, mock_batch_service):
        """Test successful batch export creation."""
        job = Job(
            id=2,
            project_id=1,
            job_type="batch_export",
            status="pending",
            progress=0,
            parameters={"analysis_ids": [10, 11, 12], "format": "sarif", "total_items": 3},
            tags={},
        )
        mock_batch_service.export_analyses = AsyncMock(return_value=job)

        response = client.post(
            "/api/v1/batch/export",
            json={
                "analysis_ids": [10, 11, 12],
                "format": "sarif",
                "parameters": {"include_metrics": True},
            },
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["job_id"] == 2
        assert data["job_type"] == "batch_export"
        assert data["format"] == "sarif"
        assert data["total_items"] == 3

    async def test_batch_export_all_formats(self, client, mock_batch_service):
        """Test batch export with all supported formats."""
        formats = ["sarif", "markdown", "html", "csv", "json"]

        for fmt in formats:
            job = Job(
                id=2,
                project_id=1,
                job_type="batch_export",
                status="pending",
                progress=0,
                parameters={"analysis_ids": [10], "format": fmt, "total_items": 1},
                tags={},
            )
            mock_batch_service.export_analyses = AsyncMock(return_value=job)

            response = client.post(
                "/api/v1/batch/export",
                json={"analysis_ids": [10], "format": fmt},
            )

            assert response.status_code == status.HTTP_202_ACCEPTED
            assert response.json()["format"] == fmt

    async def test_batch_export_invalid_format(self, client, mock_batch_service):
        """Test batch export with invalid format."""
        mock_batch_service.export_analyses = AsyncMock(
            side_effect=ValueError("Invalid export format 'invalid'")
        )

        response = client.post(
            "/api/v1/batch/export",
            json={"analysis_ids": [10], "format": "invalid"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBatchImport:
    """Tests for POST /api/v1/batch/import endpoint."""

    async def test_batch_import_success(self, client, mock_batch_service):
        """Test successful batch technology import."""
        job = Job(
            id=3,
            project_id=1,
            job_type="batch_import",
            status="pending",
            progress=0,
            parameters={
                "technologies": [
                    {"title": "React", "domain": "frontend"},
                    {"title": "FastAPI", "domain": "backend"},
                ],
                "merge_strategy": "skip",
                "total_items": 2,
            },
            tags={},
        )
        mock_batch_service.import_technologies = AsyncMock(return_value=job)

        response = client.post(
            "/api/v1/batch/import",
            json={
                "project_id": 1,
                "technologies": [
                    {"title": "React", "domain": "frontend", "vendor": "Meta"},
                    {"title": "FastAPI", "domain": "backend"},
                ],
                "merge_strategy": "skip",
            },
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["job_id"] == 3
        assert data["job_type"] == "batch_import"
        assert data["total_items"] == 2

    async def test_batch_import_all_strategies(self, client, mock_batch_service):
        """Test batch import with all merge strategies."""
        strategies = ["skip", "overwrite", "merge"]

        for strategy in strategies:
            job = Job(
                id=3,
                project_id=1,
                job_type="batch_import",
                status="pending",
                progress=0,
                parameters={
                    "technologies": [{"title": "React", "domain": "frontend"}],
                    "merge_strategy": strategy,
                    "total_items": 1,
                },
                tags={},
            )
            mock_batch_service.import_technologies = AsyncMock(return_value=job)

            response = client.post(
                "/api/v1/batch/import",
                json={
                    "project_id": 1,
                    "technologies": [{"title": "React", "domain": "frontend"}],
                    "merge_strategy": strategy,
                },
            )

            assert response.status_code == status.HTTP_202_ACCEPTED

    async def test_batch_import_invalid_strategy(self, client, mock_batch_service):
        """Test batch import with invalid merge strategy."""
        mock_batch_service.import_technologies = AsyncMock(
            side_effect=ValueError("Invalid merge strategy 'invalid'")
        )

        response = client.post(
            "/api/v1/batch/import",
            json={
                "project_id": 1,
                "technologies": [{"title": "React", "domain": "frontend"}],
                "merge_strategy": "invalid",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_batch_import_missing_required_fields(self, client, mock_batch_service):
        """Test batch import with missing required technology fields."""
        mock_batch_service.import_technologies = AsyncMock(
            side_effect=ValueError("Technology at index 0 missing required fields: {'title'}")
        )

        response = client.post(
            "/api/v1/batch/import",
            json={
                "project_id": 1,
                "technologies": [{"domain": "frontend"}],  # Missing 'title'
                "merge_strategy": "skip",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "missing required fields" in response.json()["detail"]


class TestBatchStatistics:
    """Tests for GET /api/v1/batch/statistics endpoint."""

    async def test_get_statistics_success(self, client, mock_batch_service):
        """Test successful retrieval of batch statistics."""
        mock_batch_service.get_batch_statistics = AsyncMock(
            return_value={
                "total_batches": 42,
                "active_batches": 3,
                "by_type": {
                    "batch_analysis": 25,
                    "batch_export": 12,
                    "batch_import": 5,
                },
                "by_status": {
                    "completed": 35,
                    "running": 3,
                    "failed": 4,
                },
                "average_duration_seconds": 127.5,
                "success_rate": 89.7,
            }
        )

        response = client.get("/api/v1/batch/statistics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_batches"] == 42
        assert data["active_batches"] == 3
        assert "batch_analysis" in data["by_type"]
        assert "completed" in data["by_status"]
        assert data["average_duration_seconds"] == 127.5
        assert data["success_rate"] == 89.7

    async def test_get_statistics_by_project(self, client, mock_batch_service):
        """Test retrieval of batch statistics filtered by project."""
        mock_batch_service.get_batch_statistics = AsyncMock(
            return_value={
                "total_batches": 10,
                "active_batches": 1,
                "by_type": {"batch_analysis": 10},
                "by_status": {"completed": 10},
                "average_duration_seconds": 95.0,
                "success_rate": 100.0,
            }
        )

        response = client.get("/api/v1/batch/statistics?project_id=1")

        assert response.status_code == status.HTTP_200_OK
        mock_batch_service.get_batch_statistics.assert_called_once_with(project_id=1)

    async def test_get_statistics_no_data(self, client, mock_batch_service):
        """Test statistics endpoint with no batch operations."""
        mock_batch_service.get_batch_statistics = AsyncMock(
            return_value={
                "total_batches": 0,
                "active_batches": 0,
                "by_type": {},
                "by_status": {},
                "average_duration_seconds": None,
                "success_rate": None,
            }
        )

        response = client.get("/api/v1/batch/statistics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_batches"] == 0
        assert data["success_rate"] is None


class TestGetBatchJob:
    """Tests for GET /api/v1/batch/jobs/{job_id} endpoint."""

    async def test_get_batch_job_success(self, client):
        """Test successful retrieval of batch job."""
        with patch("app.routers.batch.JobService") as mock_service_class:
            job = Job(
                id=1,
                project_id=1,
                job_type="batch_analysis",
                status="running",
                progress=50,
                parameters={"repository_ids": [1, 2, 3]},
                tags={},
            )
            mock_service = mock_service_class.return_value
            mock_service.get_job = AsyncMock(return_value=job)

            response = client.get("/api/v1/batch/jobs/1")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == 1
            assert data["job_type"] == "batch_analysis"
            assert data["status"] == "running"
            assert data["progress"] == 50

    async def test_get_batch_job_not_found(self, client):
        """Test retrieval of non-existent batch job."""
        with patch("app.routers.batch.JobService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_job = AsyncMock(return_value=None)

            response = client.get("/api/v1/batch/jobs/999")

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"]


class TestIntegration:
    """Integration tests for batch operations workflow."""

    async def test_batch_analyze_workflow(self, client, mock_batch_service, sample_job):
        """Test complete batch analyze workflow."""
        # 1. Create batch analysis
        mock_batch_service.analyze_repositories = AsyncMock(return_value=sample_job)

        create_response = client.post(
            "/api/v1/batch/analyze",
            json={"repository_ids": [1, 2, 3], "priority": 8},
        )

        assert create_response.status_code == status.HTTP_202_ACCEPTED
        job_id = create_response.json()["job_id"]

        # 2. Check batch job status
        with patch("app.routers.batch.JobService") as mock_service_class:
            running_job = Job(
                id=job_id,
                project_id=1,
                job_type="batch_analysis",
                status="running",
                progress=66,
                parameters={"repository_ids": [1, 2, 3], "total_items": 3},
                tags={},
            )
            mock_service = mock_service_class.return_value
            mock_service.get_job = AsyncMock(return_value=running_job)

            status_response = client.get(f"/api/v1/batch/jobs/{job_id}")
            assert status_response.status_code == status.HTTP_200_OK
            assert status_response.json()["progress"] == 66

    async def test_batch_export_workflow(self, client, mock_batch_service):
        """Test complete batch export workflow."""
        job = Job(
            id=5,
            project_id=1,
            job_type="batch_export",
            status="pending",
            progress=0,
            parameters={"analysis_ids": [1, 2], "format": "sarif"},
            tags={},
        )
        mock_batch_service.export_analyses = AsyncMock(return_value=job)

        response = client.post(
            "/api/v1/batch/export",
            json={"analysis_ids": [1, 2], "format": "sarif"},
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json()["format"] == "sarif"
