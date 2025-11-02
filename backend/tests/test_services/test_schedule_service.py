"""
Tests for Schedule Service.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.schedule_service import ScheduleService
from app.models import Schedule, Project, User, ScheduleFrequency


@pytest.fixture
async def schedule_service(db_session: AsyncSession):
    """Create schedule service instance."""
    return ScheduleService(db_session)


@pytest.fixture
async def test_project(db_session: AsyncSession):
    """Create test project."""
    project = Project(name="Test Project", description="Test")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create test user."""
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestScheduleCreation:
    """Tests for schedule creation."""

    @pytest.mark.asyncio
    async def test_create_daily_schedule(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test creating a daily schedule."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Daily Analysis",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
            description="Run analysis daily",
        )

        assert schedule.id is not None
        assert schedule.name == "Daily Analysis"
        assert schedule.frequency == ScheduleFrequency.DAILY
        assert schedule.enabled is True
        assert schedule.next_run_at is not None

    @pytest.mark.asyncio
    async def test_create_cron_schedule(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test creating a cron-based schedule."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Cron Schedule",
            task_type="export",
            frequency=ScheduleFrequency.CRON,
            cron_expression="0 2 * * *",  # Daily at 2 AM
            description="Export at 2 AM",
        )

        assert schedule.id is not None
        assert schedule.cron_expression == "0 2 * * *"
        assert schedule.next_run_at is not None

    @pytest.mark.asyncio
    async def test_create_schedule_with_timezone(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test creating a schedule with timezone."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Timezone Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
            timezone="America/New_York",
        )

        assert schedule.timezone == "America/New_York"
        assert schedule.next_run_at is not None

    @pytest.mark.asyncio
    async def test_create_schedule_with_execution_window(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test creating a schedule with start/end times."""
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = datetime.utcnow() + timedelta(days=30)

        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Windowed Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.HOURLY,
            start_time=start_time,
            end_time=end_time,
        )

        assert schedule.start_time == start_time
        assert schedule.end_time == end_time

    @pytest.mark.asyncio
    async def test_create_schedule_invalid_frequency(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test creating schedule with invalid frequency."""
        with pytest.raises(ValueError, match="Invalid frequency"):
            await schedule_service.create_schedule(
                project_id=test_project.id,
                name="Invalid Schedule",
                task_type="analysis",
                frequency="invalid",
            )

    @pytest.mark.asyncio
    async def test_create_cron_schedule_missing_expression(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test creating cron schedule without expression."""
        with pytest.raises(ValueError, match="Cron expression required"):
            await schedule_service.create_schedule(
                project_id=test_project.id,
                name="Cron Without Expression",
                task_type="analysis",
                frequency=ScheduleFrequency.CRON,
            )

    @pytest.mark.asyncio
    async def test_create_schedule_invalid_cron_expression(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test creating schedule with invalid cron expression."""
        with pytest.raises(ValueError, match="Invalid cron expression"):
            await schedule_service.create_schedule(
                project_id=test_project.id,
                name="Invalid Cron",
                task_type="analysis",
                frequency=ScheduleFrequency.CRON,
                cron_expression="invalid cron",
            )

    @pytest.mark.asyncio
    async def test_create_schedule_invalid_timezone(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test creating schedule with invalid timezone."""
        with pytest.raises(ValueError, match="Invalid timezone"):
            await schedule_service.create_schedule(
                project_id=test_project.id,
                name="Invalid Timezone",
                task_type="analysis",
                frequency=ScheduleFrequency.DAILY,
                timezone="Invalid/Timezone",
            )


class TestScheduleUpdate:
    """Tests for schedule updates."""

    @pytest.mark.asyncio
    async def test_update_schedule_name(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test updating schedule name."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Original Name",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
        )

        updated = await schedule_service.update_schedule(
            schedule_id=schedule.id, name="Updated Name"
        )

        assert updated.name == "Updated Name"
        assert updated.id == schedule.id

    @pytest.mark.asyncio
    async def test_update_schedule_frequency_recalculates_next_run(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test that updating frequency recalculates next run."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Test Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
        )
        original_next_run = schedule.next_run_at

        updated = await schedule_service.update_schedule(
            schedule_id=schedule.id, frequency=ScheduleFrequency.WEEKLY
        )

        assert updated.frequency == ScheduleFrequency.WEEKLY
        assert updated.next_run_at != original_next_run

    @pytest.mark.asyncio
    async def test_update_nonexistent_schedule(self, schedule_service: ScheduleService):
        """Test updating nonexistent schedule."""
        with pytest.raises(ValueError, match="not found"):
            await schedule_service.update_schedule(schedule_id=99999, name="Should Fail")


class TestScheduleExecution:
    """Tests for schedule execution."""

    @pytest.mark.asyncio
    async def test_execute_schedule(
        self, schedule_service: ScheduleService, test_project: Project, db_session: AsyncSession
    ):
        """Test executing a schedule creates a job."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Test Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
            task_parameters={"test": "value"},
        )

        job = await schedule_service.execute_schedule(schedule.id)

        assert job.id is not None
        assert job.job_type == "analysis"
        assert job.parameters == {"test": "value"}

        # Refresh schedule
        await db_session.refresh(schedule)
        assert schedule.run_count == 1
        assert schedule.last_run_at is not None

    @pytest.mark.asyncio
    async def test_execute_disabled_schedule(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test executing disabled schedule fails."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Disabled Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
            enabled=False,
        )

        with pytest.raises(ValueError, match="not active"):
            await schedule_service.execute_schedule(schedule.id)

    @pytest.mark.asyncio
    async def test_record_execution_result_success(
        self, schedule_service: ScheduleService, test_project: Project, db_session: AsyncSession
    ):
        """Test recording successful execution."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Test Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
        )

        await schedule_service.record_execution_result(schedule_id=schedule.id, success=True)

        await db_session.refresh(schedule)
        assert schedule.success_count == 1
        assert schedule.last_success_at is not None
        assert schedule.last_error is None

    @pytest.mark.asyncio
    async def test_record_execution_result_failure(
        self, schedule_service: ScheduleService, test_project: Project, db_session: AsyncSession
    ):
        """Test recording failed execution."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Test Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
        )

        await schedule_service.record_execution_result(
            schedule_id=schedule.id, success=False, error="Test error"
        )

        await db_session.refresh(schedule)
        assert schedule.failure_count == 1
        assert schedule.last_failure_at is not None
        assert schedule.last_error == "Test error"


class TestScheduleQueries:
    """Tests for schedule queries."""

    @pytest.mark.asyncio
    async def test_get_due_schedules(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test getting due schedules."""
        # Create schedule with past next_run
        past_time = datetime.utcnow() - timedelta(hours=1)
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Past Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
        )
        schedule.next_run_at = past_time
        await schedule_service.db.commit()

        due_schedules = await schedule_service.get_due_schedules()

        assert len(due_schedules) >= 1
        assert any(s.id == schedule.id for s in due_schedules)

    @pytest.mark.asyncio
    async def test_get_due_schedules_ignores_disabled(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test that disabled schedules are not returned."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Disabled Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
            enabled=False,
        )
        schedule.next_run_at = past_time
        await schedule_service.db.commit()

        due_schedules = await schedule_service.get_due_schedules()

        assert not any(s.id == schedule.id for s in due_schedules)

    @pytest.mark.asyncio
    async def test_get_schedule_statistics(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test getting schedule statistics."""
        # Create several schedules
        for i in range(3):
            await schedule_service.create_schedule(
                project_id=test_project.id,
                name=f"Schedule {i}",
                task_type="analysis",
                frequency=ScheduleFrequency.DAILY if i % 2 == 0 else ScheduleFrequency.HOURLY,
            )

        stats = await schedule_service.get_schedule_statistics(project_id=test_project.id)

        assert stats["total_schedules"] == 3
        assert stats["enabled_schedules"] == 3
        assert "by_frequency" in stats


class TestScheduleDeletion:
    """Tests for schedule deletion."""

    @pytest.mark.asyncio
    async def test_delete_schedule(self, schedule_service: ScheduleService, test_project: Project):
        """Test deleting a schedule."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="To Delete",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
        )

        await schedule_service.delete_schedule(schedule.id)

        # Verify deletion
        with pytest.raises(ValueError, match="not found"):
            await schedule_service.update_schedule(schedule_id=schedule.id, name="Should Fail")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_schedule(self, schedule_service: ScheduleService):
        """Test deleting nonexistent schedule."""
        with pytest.raises(ValueError, match="not found"):
            await schedule_service.delete_schedule(99999)


class TestNextRunCalculation:
    """Tests for next run calculation."""

    @pytest.mark.asyncio
    async def test_once_frequency_next_run(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test once frequency sets next run to start_time."""
        start_time = datetime.utcnow() + timedelta(hours=2)
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Once Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.ONCE,
            start_time=start_time,
        )

        # next_run_at should be set to start_time
        assert schedule.next_run_at == start_time

    @pytest.mark.asyncio
    async def test_hourly_frequency_aligns_to_hour(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test hourly frequency aligns to top of hour."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Hourly Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.HOURLY,
        )

        # next_run_at should be aligned to top of hour
        assert schedule.next_run_at.minute == 0
        assert schedule.next_run_at.second == 0

    @pytest.mark.asyncio
    async def test_daily_frequency_aligns_to_midnight(
        self, schedule_service: ScheduleService, test_project: Project
    ):
        """Test daily frequency aligns to midnight."""
        schedule = await schedule_service.create_schedule(
            project_id=test_project.id,
            name="Daily Schedule",
            task_type="analysis",
            frequency=ScheduleFrequency.DAILY,
        )

        # next_run_at should be aligned to midnight
        assert schedule.next_run_at.hour == 0
        assert schedule.next_run_at.minute == 0
        assert schedule.next_run_at.second == 0
