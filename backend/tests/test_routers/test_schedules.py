"""
Tests for Schedule API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Schedule, ScheduleFrequency


@pytest.fixture
async def test_project(db_session: AsyncSession):
    """Create test project."""
    project = Project(name="Test Project", description="Test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_schedule(db_session: AsyncSession, test_project: Project):
    """Create test schedule."""
    schedule = Schedule(
        project_id=test_project.id,
        name="Test Schedule",
        task_type="analysis",
        frequency=ScheduleFrequency.DAILY,
        timezone="UTC",
        enabled=True,
        task_parameters={},
        tags={},
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)
    return schedule


class TestScheduleCreation:
    """Tests for schedule creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_schedule_success(self, client: AsyncClient, test_project: Project):
        """Test creating a schedule successfully."""
        data = {
            "project_id": test_project.id,
            "name": "New Schedule",
            "task_type": "analysis",
            "frequency": "daily",
            "description": "Test schedule",
            "enabled": True,
            "tags": {},
            "task_parameters": {},
        }

        response = await client.post("/api/v1/schedules", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "New Schedule"
        assert result["frequency"] == "daily"
        assert result["id"] is not None

    @pytest.mark.asyncio
    async def test_create_cron_schedule(self, client: AsyncClient, test_project: Project):
        """Test creating a cron-based schedule."""
        data = {
            "project_id": test_project.id,
            "name": "Cron Schedule",
            "task_type": "export",
            "frequency": "cron",
            "cron_expression": "0 2 * * *",
            "timezone": "America/New_York",
        }

        response = await client.post("/api/v1/schedules", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["cron_expression"] == "0 2 * * *"
        assert result["timezone"] == "America/New_York"

    @pytest.mark.asyncio
    async def test_create_schedule_invalid_frequency(
        self, client: AsyncClient, test_project: Project
    ):
        """Test creating schedule with invalid frequency."""
        data = {
            "project_id": test_project.id,
            "name": "Invalid Schedule",
            "task_type": "analysis",
            "frequency": "invalid",
        }

        response = await client.post("/api/v1/schedules", json=data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_schedule_missing_cron_expression(
        self, client: AsyncClient, test_project: Project
    ):
        """Test creating cron schedule without expression."""
        data = {
            "project_id": test_project.id,
            "name": "Cron Without Expression",
            "task_type": "analysis",
            "frequency": "cron",
        }

        response = await client.post("/api/v1/schedules", json=data)

        assert response.status_code == 400


class TestScheduleRetrieval:
    """Tests for schedule retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_list_schedules(self, client: AsyncClient, test_schedule: Schedule):
        """Test listing schedules."""
        response = await client.get("/api/v1/schedules")

        assert response.status_code == 200
        result = response.json()
        assert "schedules" in result
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_schedules_with_filters(self, client: AsyncClient, test_schedule: Schedule):
        """Test listing schedules with filters."""
        response = await client.get(
            "/api/v1/schedules",
            params={
                "project_id": test_schedule.project_id,
                "enabled": True,
                "frequency": "daily",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert all(s["project_id"] == test_schedule.project_id for s in result["schedules"])

    @pytest.mark.asyncio
    async def test_list_schedules_pagination(
        self, client: AsyncClient, test_project: Project, db_session: AsyncSession
    ):
        """Test schedule list pagination."""
        # Create multiple schedules
        for i in range(5):
            schedule = Schedule(
                project_id=test_project.id,
                name=f"Schedule {i}",
                task_type="analysis",
                frequency=ScheduleFrequency.DAILY,
                timezone="UTC",
                enabled=True,
                task_parameters={},
                tags={},
            )
            db_session.add(schedule)
        await db_session.commit()

        # Get first page
        response = await client.get("/api/v1/schedules?page=1&page_size=3")

        assert response.status_code == 200
        result = response.json()
        assert len(result["schedules"]) <= 3
        assert result["page"] == 1

    @pytest.mark.asyncio
    async def test_get_schedule_by_id(self, client: AsyncClient, test_schedule: Schedule):
        """Test getting schedule by ID."""
        response = await client.get(f"/api/v1/schedules/{test_schedule.id}")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == test_schedule.id
        assert result["name"] == test_schedule.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_schedule(self, client: AsyncClient):
        """Test getting nonexistent schedule."""
        response = await client.get("/api/v1/schedules/99999")

        assert response.status_code == 404


class TestScheduleUpdate:
    """Tests for schedule update endpoint."""

    @pytest.mark.asyncio
    async def test_update_schedule_name(self, client: AsyncClient, test_schedule: Schedule):
        """Test updating schedule name."""
        data = {"name": "Updated Name"}

        response = await client.patch(f"/api/v1/schedules/{test_schedule.id}", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_schedule_frequency(self, client: AsyncClient, test_schedule: Schedule):
        """Test updating schedule frequency."""
        data = {"frequency": "weekly"}

        response = await client.patch(f"/api/v1/schedules/{test_schedule.id}", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["frequency"] == "weekly"

    @pytest.mark.asyncio
    async def test_update_nonexistent_schedule(self, client: AsyncClient):
        """Test updating nonexistent schedule."""
        data = {"name": "Should Fail"}

        response = await client.patch("/api/v1/schedules/99999", json=data)

        assert response.status_code == 400


class TestScheduleDeletion:
    """Tests for schedule deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_schedule(self, client: AsyncClient, test_schedule: Schedule):
        """Test deleting a schedule."""
        response = await client.delete(f"/api/v1/schedules/{test_schedule.id}")

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/v1/schedules/{test_schedule.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_schedule(self, client: AsyncClient):
        """Test deleting nonexistent schedule."""
        response = await client.delete("/api/v1/schedules/99999")

        assert response.status_code == 404


class TestScheduleExecution:
    """Tests for schedule execution endpoint."""

    @pytest.mark.asyncio
    async def test_execute_schedule(self, client: AsyncClient, test_schedule: Schedule):
        """Test executing a schedule."""
        response = await client.post(f"/api/v1/schedules/{test_schedule.id}/execute")

        assert response.status_code == 202
        result = response.json()
        assert result["schedule_id"] == test_schedule.id
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_execute_schedule_force(
        self, client: AsyncClient, test_schedule: Schedule, db_session: AsyncSession
    ):
        """Test force executing a disabled schedule."""
        # Disable schedule
        test_schedule.enabled = False
        await db_session.commit()

        data = {"force": True}
        response = await client.post(f"/api/v1/schedules/{test_schedule.id}/execute", json=data)

        assert response.status_code == 202
        result = response.json()
        assert result["job_id"] is not None

    @pytest.mark.asyncio
    async def test_execute_nonexistent_schedule(self, client: AsyncClient):
        """Test executing nonexistent schedule."""
        response = await client.post("/api/v1/schedules/99999/execute")

        assert response.status_code == 404


class TestScheduleEnableDisable:
    """Tests for schedule enable/disable endpoints."""

    @pytest.mark.asyncio
    async def test_disable_schedule(self, client: AsyncClient, test_schedule: Schedule):
        """Test disabling a schedule."""
        response = await client.post(f"/api/v1/schedules/{test_schedule.id}/disable")

        assert response.status_code == 200
        result = response.json()
        assert result["enabled"] is False

    @pytest.mark.asyncio
    async def test_enable_schedule(
        self, client: AsyncClient, test_schedule: Schedule, db_session: AsyncSession
    ):
        """Test enabling a schedule."""
        # First disable it
        test_schedule.enabled = False
        await db_session.commit()

        response = await client.post(f"/api/v1/schedules/{test_schedule.id}/enable")

        assert response.status_code == 200
        result = response.json()
        assert result["enabled"] is True


class TestScheduleStatistics:
    """Tests for schedule statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_schedule_statistics(self, client: AsyncClient, test_schedule: Schedule):
        """Test getting schedule statistics."""
        response = await client.get("/api/v1/schedules/statistics/summary")

        assert response.status_code == 200
        result = response.json()
        assert "total_schedules" in result
        assert "enabled_schedules" in result
        assert "by_frequency" in result

    @pytest.mark.asyncio
    async def test_get_schedule_statistics_filtered(
        self, client: AsyncClient, test_schedule: Schedule
    ):
        """Test getting filtered schedule statistics."""
        response = await client.get(
            "/api/v1/schedules/statistics/summary",
            params={"project_id": test_schedule.project_id},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["total_schedules"] >= 1


class TestDueSchedules:
    """Tests for due schedules endpoint."""

    @pytest.mark.asyncio
    async def test_list_due_schedules(
        self, client: AsyncClient, test_schedule: Schedule, db_session: AsyncSession
    ):
        """Test listing due schedules."""
        # Set schedule to be due
        test_schedule.next_run_at = datetime.utcnow() - timedelta(hours=1)
        await db_session.commit()

        response = await client.get("/api/v1/schedules/due/list")

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert any(s["id"] == test_schedule.id for s in result)

    @pytest.mark.asyncio
    async def test_list_due_schedules_with_limit(
        self, client: AsyncClient, test_schedule: Schedule
    ):
        """Test listing due schedules with limit."""
        response = await client.get("/api/v1/schedules/due/list?limit=10")

        assert response.status_code == 200
        result = response.json()
        assert len(result) <= 10
