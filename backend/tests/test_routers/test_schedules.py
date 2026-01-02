"""
Tests for Schedule API endpoints.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status

from app.models import Schedule, ScheduleFrequency


@pytest.fixture
def mock_schedule_service():
    """Mock ScheduleService for testing."""
    with patch("app.routers.schedules.ScheduleService") as mock:
        service = mock.return_value
        yield service


@pytest.fixture
def sample_schedule():
    """Sample schedule object for testing."""
    return Schedule(
        id=1,
        project_id=1,
        name="Test Schedule",
        task_type="analysis",
        frequency=ScheduleFrequency.DAILY,
        timezone="UTC",
        enabled=True,
        task_parameters={},
        tags={},
        cron_expression=None,
        next_run_at=datetime.utcnow() + timedelta(hours=1),
        last_run_at=None,
        run_count=0,
        success_count=0,
        failure_count=0,
    )


class TestScheduleCreation:
    """Tests for schedule creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_schedule_success(
        self, api_client, mock_schedule_service, sample_schedule
    ):
        """Test creating a schedule successfully."""
        mock_schedule_service.create_schedule = AsyncMock(return_value=sample_schedule)

        data = {
            "project_id": 1,
            "name": "New Schedule",
            "task_type": "analysis",
            "frequency": "daily",
            "description": "Test schedule",
            "enabled": True,
            "tags": {},
            "task_parameters": {},
        }

        response = await api_client.post("/schedules", json=data)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["name"] == "Test Schedule"
        assert result["frequency"] == "daily"
        assert result["id"] is not None

    @pytest.mark.asyncio
    async def test_create_cron_schedule(self, api_client, mock_schedule_service, sample_schedule):
        """Test creating a cron-based schedule."""
        cron_schedule = sample_schedule
        cron_schedule.frequency = ScheduleFrequency.CRON
        cron_schedule.cron_expression = "0 2 * * *"
        cron_schedule.timezone = "America/New_York"
        mock_schedule_service.create_schedule = AsyncMock(return_value=cron_schedule)

        data = {
            "project_id": 1,
            "name": "Cron Schedule",
            "task_type": "export",
            "frequency": "cron",
            "cron_expression": "0 2 * * *",
            "timezone": "America/New_York",
        }

        response = await api_client.post("/schedules", json=data)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["cron_expression"] == "0 2 * * *"
        assert result["timezone"] == "America/New_York"

    @pytest.mark.asyncio
    async def test_create_schedule_invalid_frequency(self, api_client):
        """Test creating schedule with invalid frequency."""
        data = {
            "project_id": 1,
            "name": "Invalid Schedule",
            "task_type": "analysis",
            "frequency": "invalid",
        }

        response = await api_client.post("/schedules", json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_schedule_missing_cron_expression(self, api_client, mock_schedule_service):
        """Test creating cron schedule without expression."""
        mock_schedule_service.create_schedule = AsyncMock(
            side_effect=ValueError("Cron expression required for cron frequency")
        )

        data = {
            "project_id": 1,
            "name": "Cron Without Expression",
            "task_type": "analysis",
            "frequency": "cron",
        }

        response = await api_client.post("/schedules", json=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestScheduleRetrieval:
    """Tests for schedule retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_list_schedules(self, api_client, mock_schedule_service, sample_schedule):
        """Test listing schedules."""
        mock_schedule_service.list_schedules = AsyncMock(return_value=[sample_schedule])

        response = await api_client.get("/schedules")

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "schedules" in result
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_schedules_with_filters(
        self, api_client, mock_schedule_service, sample_schedule
    ):
        """Test listing schedules with filters."""
        mock_schedule_service.list_schedules = AsyncMock(return_value=[sample_schedule])

        response = await api_client.get(
            "/schedules",
            params={
                "project_id": 1,
                "enabled": True,
                "frequency": "daily",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert all(s["project_id"] == 1 for s in result["schedules"])

    @pytest.mark.asyncio
    async def test_list_schedules_pagination(
        self, api_client, mock_schedule_service, sample_schedule
    ):
        """Test schedule list pagination."""
        schedules = [sample_schedule for _ in range(3)]
        mock_schedule_service.list_schedules = AsyncMock(return_value=schedules)

        response = await api_client.get("/schedules?page=1&page_size=3")

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert len(result["schedules"]) <= 3
        assert result["page"] == 1

    @pytest.mark.asyncio
    async def test_get_schedule_by_id(self, api_client, mock_schedule_service, sample_schedule):
        """Test getting schedule by ID."""
        mock_schedule_service.get_schedule = AsyncMock(return_value=sample_schedule)

        response = await api_client.get(f"/schedules/{sample_schedule.id}")

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["id"] == sample_schedule.id
        assert result["name"] == sample_schedule.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_schedule(self, api_client, mock_schedule_service):
        """Test getting nonexistent schedule."""
        mock_schedule_service.get_schedule = AsyncMock(return_value=None)

        response = await api_client.get("/schedules/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestScheduleUpdate:
    """Tests for schedule update endpoint."""

    @pytest.mark.asyncio
    async def test_update_schedule_name(self, api_client, mock_schedule_service, sample_schedule):
        """Test updating schedule name."""
        updated_schedule = sample_schedule
        updated_schedule.name = "Updated Name"
        mock_schedule_service.update_schedule = AsyncMock(return_value=updated_schedule)

        data = {"name": "Updated Name"}

        response = await api_client.patch(f"/schedules/{sample_schedule.id}", json=data)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_schedule_frequency(
        self, api_client, mock_schedule_service, sample_schedule
    ):
        """Test updating schedule frequency."""
        updated_schedule = sample_schedule
        updated_schedule.frequency = ScheduleFrequency.WEEKLY
        mock_schedule_service.update_schedule = AsyncMock(return_value=updated_schedule)

        data = {"frequency": "weekly"}

        response = await api_client.patch(f"/schedules/{sample_schedule.id}", json=data)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["frequency"] == "weekly"

    @pytest.mark.asyncio
    async def test_update_nonexistent_schedule(self, api_client, mock_schedule_service):
        """Test updating nonexistent schedule."""
        mock_schedule_service.update_schedule = AsyncMock(return_value=None)

        data = {"name": "Should Fail"}

        response = await api_client.patch("/schedules/99999", json=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestScheduleDeletion:
    """Tests for schedule deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_schedule(self, api_client, mock_schedule_service):
        """Test deleting a schedule."""
        mock_schedule_service.delete_schedule = AsyncMock(return_value=True)

        response = await api_client.delete("/schedules/1")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_delete_nonexistent_schedule(self, api_client, mock_schedule_service):
        """Test deleting nonexistent schedule."""
        mock_schedule_service.delete_schedule = AsyncMock(return_value=False)

        response = await api_client.delete("/schedules/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestScheduleExecution:
    """Tests for schedule execution endpoint."""

    @pytest.mark.asyncio
    async def test_execute_schedule(self, api_client, mock_schedule_service, sample_schedule):
        """Test executing a schedule."""
        mock_schedule_service.execute_schedule = AsyncMock(
            return_value={"schedule_id": sample_schedule.id, "job_id": 123}
        )

        response = await api_client.post(f"/schedules/{sample_schedule.id}/execute")

        assert response.status_code == status.HTTP_202_ACCEPTED
        result = response.json()
        assert result["schedule_id"] == sample_schedule.id
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_execute_schedule_force(self, api_client, mock_schedule_service, sample_schedule):
        """Test force executing a disabled schedule."""
        mock_schedule_service.execute_schedule = AsyncMock(
            return_value={"schedule_id": sample_schedule.id, "job_id": 456}
        )

        data = {"force": True}
        response = await api_client.post(f"/schedules/{sample_schedule.id}/execute", json=data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        result = response.json()
        assert result["job_id"] is not None

    @pytest.mark.asyncio
    async def test_execute_nonexistent_schedule(self, api_client, mock_schedule_service):
        """Test executing nonexistent schedule."""
        mock_schedule_service.execute_schedule = AsyncMock(
            side_effect=ValueError("Schedule not found")
        )

        response = await api_client.post("/schedules/99999/execute")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestScheduleEnableDisable:
    """Tests for schedule enable/disable endpoints."""

    @pytest.mark.asyncio
    async def test_disable_schedule(self, api_client, mock_schedule_service, sample_schedule):
        """Test disabling a schedule."""
        disabled_schedule = sample_schedule
        disabled_schedule.enabled = False
        mock_schedule_service.disable_schedule = AsyncMock(return_value=disabled_schedule)

        response = await api_client.post(f"/schedules/{sample_schedule.id}/disable")

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["enabled"] is False

    @pytest.mark.asyncio
    async def test_enable_schedule(self, api_client, mock_schedule_service, sample_schedule):
        """Test enabling a schedule."""
        enabled_schedule = sample_schedule
        enabled_schedule.enabled = True
        mock_schedule_service.enable_schedule = AsyncMock(return_value=enabled_schedule)

        response = await api_client.post(f"/schedules/{sample_schedule.id}/enable")

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["enabled"] is True


class TestScheduleStatistics:
    """Tests for schedule statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_schedule_statistics(self, api_client, mock_schedule_service):
        """Test getting schedule statistics."""
        mock_schedule_service.get_statistics = AsyncMock(
            return_value={
                "total_schedules": 10,
                "enabled_schedules": 8,
                "by_frequency": {"daily": 5, "weekly": 3, "cron": 2},
            }
        )

        response = await api_client.get("/schedules/statistics/summary")

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "total_schedules" in result
        assert "enabled_schedules" in result
        assert "by_frequency" in result

    @pytest.mark.asyncio
    async def test_get_schedule_statistics_filtered(self, api_client, mock_schedule_service):
        """Test getting filtered schedule statistics."""
        mock_schedule_service.get_statistics = AsyncMock(
            return_value={
                "total_schedules": 5,
                "enabled_schedules": 4,
                "by_frequency": {"daily": 3, "weekly": 2},
            }
        )

        response = await api_client.get(
            "/schedules/statistics/summary",
            params={"project_id": 1},
        )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["total_schedules"] >= 1


class TestDueSchedules:
    """Tests for due schedules endpoint."""

    @pytest.mark.asyncio
    async def test_list_due_schedules(self, api_client, mock_schedule_service, sample_schedule):
        """Test listing due schedules."""
        due_schedule = sample_schedule
        due_schedule.next_run_at = datetime.utcnow() - timedelta(hours=1)
        mock_schedule_service.get_due_schedules = AsyncMock(return_value=[due_schedule])

        response = await api_client.get("/schedules/due/list")

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert isinstance(result, list)
        assert any(s["id"] == sample_schedule.id for s in result)

    @pytest.mark.asyncio
    async def test_list_due_schedules_with_limit(
        self, api_client, mock_schedule_service, sample_schedule
    ):
        """Test listing due schedules with limit."""
        mock_schedule_service.get_due_schedules = AsyncMock(return_value=[sample_schedule])

        response = await api_client.get("/schedules/due/list?limit=10")

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert len(result) <= 10
