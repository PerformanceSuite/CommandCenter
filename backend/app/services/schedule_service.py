"""
Schedule service for managing recurring task execution.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from croniter import croniter
import pytz

from app.models import Schedule, ScheduleFrequency, Job
from app.services.job_service import JobService


logger = logging.getLogger(__name__)


class ScheduleService:
    """
    Service for managing schedule creation, updates, and execution.

    Features:
    - Cron expression parsing and validation
    - Next run calculation with timezone support
    - Schedule conflict detection
    - Automatic next run scheduling
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize schedule service.

        Args:
            db: Database session
        """
        self.db = db
        self.job_service = JobService(db)

    async def create_schedule(
        self,
        project_id: int,
        name: str,
        task_type: str,
        frequency: str,
        task_parameters: Optional[Dict[str, Any]] = None,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        timezone: str = "UTC",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        enabled: bool = True,
        created_by: Optional[int] = None,
        tags: Optional[Dict[str, Any]] = None,
    ) -> Schedule:
        """
        Create a new schedule.

        Args:
            project_id: Project ID
            name: Schedule name
            task_type: Type of task to execute
            frequency: Schedule frequency (hourly, daily, weekly, monthly, cron)
            task_parameters: Task-specific parameters
            cron_expression: Cron expression (required if frequency='cron')
            interval_seconds: Interval in seconds (for custom intervals)
            timezone: IANA timezone for schedule execution
            start_time: When to start executing
            end_time: When to stop executing
            description: Schedule description
            enabled: Whether schedule is enabled
            created_by: User ID who created schedule
            tags: Custom tags

        Returns:
            Created schedule

        Raises:
            ValueError: If cron expression is invalid or conflict detected
        """
        # Validate frequency
        if frequency not in [
            ScheduleFrequency.ONCE,
            ScheduleFrequency.HOURLY,
            ScheduleFrequency.DAILY,
            ScheduleFrequency.WEEKLY,
            ScheduleFrequency.MONTHLY,
            ScheduleFrequency.CRON,
        ]:
            raise ValueError(f"Invalid frequency: {frequency}")

        # Validate cron expression if frequency is cron
        if frequency == ScheduleFrequency.CRON:
            if not cron_expression:
                raise ValueError("Cron expression required for cron frequency")
            if not self._validate_cron(cron_expression):
                raise ValueError(f"Invalid cron expression: {cron_expression}")

        # Validate timezone
        if not self._validate_timezone(timezone):
            raise ValueError(f"Invalid timezone: {timezone}")

        # Check for conflicts
        conflicts = await self._check_conflicts(
            project_id=project_id,
            task_type=task_type,
            task_parameters=task_parameters,
            exclude_schedule_id=None,
        )
        if conflicts:
            conflict_names = [s.name for s in conflicts]
            logger.warning(
                f"Schedule conflicts detected with: {', '.join(conflict_names)}"
            )
            # Note: We log conflicts but don't block creation
            # Users may want overlapping schedules

        # Calculate next run
        next_run = self._calculate_next_run(
            frequency=frequency,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            timezone=timezone,
            start_time=start_time,
        )

        # Create schedule
        schedule = Schedule(
            project_id=project_id,
            name=name,
            description=description,
            task_type=task_type,
            task_parameters=task_parameters or {},
            frequency=frequency,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            timezone=timezone,
            start_time=start_time,
            end_time=end_time,
            enabled=enabled,
            next_run_at=next_run,
            created_by=created_by,
            tags=tags or {},
        )

        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)

        logger.info(
            f"Created schedule {schedule.id} ({name}) with next run at {next_run}"
        )

        return schedule

    async def update_schedule(
        self,
        schedule_id: int,
        **updates: Dict[str, Any],
    ) -> Schedule:
        """
        Update an existing schedule.

        Args:
            schedule_id: Schedule ID
            **updates: Fields to update

        Returns:
            Updated schedule

        Raises:
            ValueError: If schedule not found or validation fails
        """
        # Fetch schedule
        result = await self.db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        # Validate updates
        if "cron_expression" in updates:
            if not self._validate_cron(updates["cron_expression"]):
                raise ValueError(
                    f"Invalid cron expression: {updates['cron_expression']}"
                )

        if "timezone" in updates:
            if not self._validate_timezone(updates["timezone"]):
                raise ValueError(f"Invalid timezone: {updates['timezone']}")

        # Apply updates
        for field, value in updates.items():
            if hasattr(schedule, field):
                setattr(schedule, field, value)

        # Recalculate next run if schedule changed
        if any(
            k in updates
            for k in [
                "frequency",
                "cron_expression",
                "interval_seconds",
                "timezone",
            ]
        ):
            schedule.next_run_at = self._calculate_next_run(
                frequency=schedule.frequency,
                cron_expression=schedule.cron_expression,
                interval_seconds=schedule.interval_seconds,
                timezone=schedule.timezone,
                start_time=schedule.start_time,
            )

        await self.db.commit()
        await self.db.refresh(schedule)

        logger.info(f"Updated schedule {schedule_id}")

        return schedule

    async def delete_schedule(self, schedule_id: int) -> None:
        """
        Delete a schedule.

        Args:
            schedule_id: Schedule ID

        Raises:
            ValueError: If schedule not found
        """
        result = await self.db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        await self.db.delete(schedule)
        await self.db.commit()

        logger.info(f"Deleted schedule {schedule_id}")

    async def execute_schedule(self, schedule_id: int) -> Job:
        """
        Execute a schedule by creating and dispatching a job.

        Args:
            schedule_id: Schedule ID

        Returns:
            Created job

        Raises:
            ValueError: If schedule not found or not active
        """
        # Fetch schedule
        result = await self.db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        if not schedule.is_active:
            raise ValueError(f"Schedule {schedule_id} is not active")

        # Create job
        job = await self.job_service.create_job(
            project_id=schedule.project_id,
            job_type=schedule.task_type,
            parameters=schedule.task_parameters,
            tags={"schedule_id": schedule_id, **schedule.tags},
            created_by=schedule.created_by,
        )

        # Dispatch job
        await self.job_service.dispatch_job(job.id)

        # Update schedule stats
        schedule.last_run_at = datetime.utcnow()
        schedule.run_count += 1

        # Calculate next run
        schedule.next_run_at = self._calculate_next_run(
            frequency=schedule.frequency,
            cron_expression=schedule.cron_expression,
            interval_seconds=schedule.interval_seconds,
            timezone=schedule.timezone,
            start_time=schedule.start_time,
            from_time=datetime.utcnow(),
        )

        await self.db.commit()

        logger.info(
            f"Executed schedule {schedule_id}, created job {job.id}, "
            f"next run at {schedule.next_run_at}"
        )

        return job

    async def record_execution_result(
        self, schedule_id: int, success: bool, error: Optional[str] = None
    ) -> None:
        """
        Record the result of a schedule execution.

        Args:
            schedule_id: Schedule ID
            success: Whether execution was successful
            error: Error message if failed
        """
        result = await self.db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            logger.warning(
                f"Schedule {schedule_id} not found for result recording"
            )
            return

        if success:
            schedule.success_count += 1
            schedule.last_success_at = datetime.utcnow()
            schedule.last_error = None
        else:
            schedule.failure_count += 1
            schedule.last_failure_at = datetime.utcnow()
            schedule.last_error = error[:1000] if error else "Unknown error"

        await self.db.commit()

        logger.info(
            f"Recorded execution result for schedule {schedule_id}: "
            f"{'success' if success else 'failure'}"
        )

    async def get_due_schedules(self, limit: int = 100) -> List[Schedule]:
        """
        Get schedules that are due for execution.

        Args:
            limit: Maximum number of schedules to return

        Returns:
            List of due schedules
        """
        now = datetime.utcnow()

        result = await self.db.execute(
            select(Schedule)
            .where(
                and_(
                    Schedule.enabled == True,
                    or_(
                        Schedule.next_run_at.is_(None),
                        Schedule.next_run_at <= now,
                    ),
                    or_(
                        Schedule.start_time.is_(None),
                        Schedule.start_time <= now,
                    ),
                    or_(
                        Schedule.end_time.is_(None),
                        Schedule.end_time > now,
                    ),
                )
            )
            .order_by(Schedule.next_run_at.nulls_first())
            .limit(limit)
        )

        schedules = result.scalars().all()

        logger.debug(f"Found {len(schedules)} due schedules")

        return schedules

    async def get_schedule_statistics(
        self, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get schedule statistics.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            Statistics dictionary
        """
        query = select(Schedule)

        if project_id:
            query = query.where(Schedule.project_id == project_id)

        result = await self.db.execute(query)
        schedules = result.scalars().all()

        total = len(schedules)
        enabled = sum(1 for s in schedules if s.enabled)
        disabled = total - enabled

        total_runs = sum(s.run_count for s in schedules)
        total_successes = sum(s.success_count for s in schedules)
        total_failures = sum(s.failure_count for s in schedules)

        success_rate = (
            (total_successes / total_runs * 100) if total_runs > 0 else 0.0
        )

        # Count by frequency
        frequency_counts = {}
        for schedule in schedules:
            freq = schedule.frequency
            frequency_counts[freq] = frequency_counts.get(freq, 0) + 1

        return {
            "total_schedules": total,
            "enabled_schedules": enabled,
            "disabled_schedules": disabled,
            "total_runs": total_runs,
            "successful_runs": total_successes,
            "failed_runs": total_failures,
            "success_rate": success_rate,
            "by_frequency": frequency_counts,
        }

    def _validate_cron(self, cron_expression: str) -> bool:
        """
        Validate cron expression.

        Args:
            cron_expression: Cron expression to validate

        Returns:
            True if valid
        """
        try:
            croniter(cron_expression)
            return True
        except Exception as e:
            logger.warning(f"Invalid cron expression '{cron_expression}': {e}")
            return False

    def _validate_timezone(self, timezone: str) -> bool:
        """
        Validate timezone string.

        Args:
            timezone: IANA timezone string

        Returns:
            True if valid
        """
        try:
            pytz.timezone(timezone)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Unknown timezone: {timezone}")
            return False

    def _calculate_next_run(
        self,
        frequency: str,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        timezone: str = "UTC",
        start_time: Optional[datetime] = None,
        from_time: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """
        Calculate next run time based on schedule configuration.

        Args:
            frequency: Schedule frequency
            cron_expression: Cron expression (if frequency='cron')
            interval_seconds: Interval in seconds
            timezone: IANA timezone
            start_time: Earliest time to start
            from_time: Calculate from this time (default: now)

        Returns:
            Next run datetime in UTC, or None if schedule is 'once' and already run
        """
        if from_time is None:
            from_time = datetime.utcnow()

        tz = pytz.timezone(timezone)
        base_time = pytz.utc.localize(from_time).astimezone(tz)

        # Handle different frequencies
        if frequency == ScheduleFrequency.ONCE:
            # One-time schedule
            return (
                start_time if start_time and start_time > from_time else None
            )

        elif frequency == ScheduleFrequency.HOURLY:
            next_run = base_time + timedelta(hours=1)
            # Align to top of hour
            next_run = next_run.replace(minute=0, second=0, microsecond=0)

        elif frequency == ScheduleFrequency.DAILY:
            next_run = base_time + timedelta(days=1)
            # Align to midnight
            next_run = next_run.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        elif frequency == ScheduleFrequency.WEEKLY:
            next_run = base_time + timedelta(weeks=1)
            # Align to Monday midnight
            days_until_monday = (7 - base_time.weekday()) % 7 or 7
            next_run = base_time + timedelta(days=days_until_monday)
            next_run = next_run.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        elif frequency == ScheduleFrequency.MONTHLY:
            # Next month, first day
            if base_time.month == 12:
                next_run = base_time.replace(
                    year=base_time.year + 1,
                    month=1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            else:
                next_run = base_time.replace(
                    month=base_time.month + 1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

        elif frequency == ScheduleFrequency.CRON:
            if not cron_expression:
                raise ValueError("Cron expression required for cron frequency")

            # Use croniter for cron expression
            iter = croniter(cron_expression, base_time)
            next_run = iter.get_next(datetime)

        else:
            # Custom interval
            if interval_seconds:
                next_run = base_time + timedelta(seconds=interval_seconds)
            else:
                raise ValueError(
                    f"Invalid frequency or missing interval: {frequency}"
                )

        # Convert back to UTC
        next_run_utc = next_run.astimezone(pytz.utc).replace(tzinfo=None)

        # Respect start_time
        if start_time and next_run_utc < start_time:
            next_run_utc = start_time

        return next_run_utc

    async def _check_conflicts(
        self,
        project_id: int,
        task_type: str,
        task_parameters: Optional[Dict[str, Any]],
        exclude_schedule_id: Optional[int] = None,
    ) -> List[Schedule]:
        """
        Check for conflicting schedules.

        Two schedules conflict if they:
        1. Are in the same project
        2. Have the same task type
        3. Have overlapping task parameters (e.g., same repository_id)

        Args:
            project_id: Project ID
            task_type: Task type
            task_parameters: Task parameters
            exclude_schedule_id: Schedule ID to exclude from check

        Returns:
            List of conflicting schedules
        """
        query = select(Schedule).where(
            and_(
                Schedule.project_id == project_id,
                Schedule.task_type == task_type,
                Schedule.enabled == True,
            )
        )

        if exclude_schedule_id:
            query = query.where(Schedule.id != exclude_schedule_id)

        result = await self.db.execute(query)
        schedules = result.scalars().all()

        # Check for parameter overlap
        conflicts = []
        if task_parameters:
            for schedule in schedules:
                if self._has_parameter_overlap(
                    task_parameters, schedule.task_parameters
                ):
                    conflicts.append(schedule)

        return conflicts

    def _has_parameter_overlap(
        self, params1: Dict[str, Any], params2: Dict[str, Any]
    ) -> bool:
        """
        Check if two parameter sets overlap.

        Args:
            params1: First parameter set
            params2: Second parameter set

        Returns:
            True if there's overlap
        """
        # Check for common keys with same values
        common_keys = set(params1.keys()) & set(params2.keys())
        for key in common_keys:
            if params1[key] == params2[key]:
                return True

        return False
