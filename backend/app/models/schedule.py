"""
Schedule model for recurring task execution.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, JSON, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScheduleFrequency:
    """Schedule frequency constants."""

    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class Schedule(Base):
    """
    Schedule model for recurring task execution.

    Supports cron-style scheduling for automated analysis, exports, and webhooks.
    Uses Celery Beat with RedBeat for distributed scheduling.
    """

    __tablename__ = "schedules"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Schedule identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Task configuration
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # analysis, export, webhook_delivery, etc.
    task_parameters: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Task-specific parameters

    # Schedule configuration
    frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ScheduleFrequency.DAILY
    )  # once, hourly, daily, weekly, monthly, cron
    cron_expression: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # For cron frequency: "0 2 * * *" = daily at 2am
    interval_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # For interval-based scheduling

    # Execution window (optional time constraints)
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # When to start executing
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # When to stop executing

    # Status tracking
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    run_count: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Total number of executions
    success_count: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Successful executions
    failure_count: Mapped[int] = mapped_column(Integer, default=0)  # Failed executions

    # Celery Beat integration
    celery_task_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Celery task name
    celery_beat_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )  # RedBeat schedule key

    # Metadata
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON, default=dict
    )  # Custom tags for filtering

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="schedules")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="schedules")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_schedules_project_enabled", "project_id", "enabled"),
        Index("idx_schedules_task_type", "task_type"),
        Index("idx_schedules_next_run", "next_run_at"),
    )

    def __repr__(self) -> str:
        return f"<Schedule(id={self.id}, name='{self.name}', frequency='{self.frequency}', enabled={self.enabled})>"

    @property
    def success_rate(self) -> Optional[float]:
        """
        Calculate success rate as a percentage.

        Returns:
            float: Success rate (0-100), or None if no runs yet
        """
        if self.run_count == 0:
            return None
        return (self.success_count / self.run_count) * 100

    @property
    def is_due(self) -> bool:
        """
        Check if schedule is due for execution.

        Returns:
            bool: True if schedule should run now
        """
        if not self.enabled:
            return False
        if self.next_run_at is None:
            return True
        return datetime.utcnow() >= self.next_run_at

    @property
    def is_active(self) -> bool:
        """
        Check if schedule is currently active (within execution window).

        Returns:
            bool: True if schedule is active
        """
        now = datetime.utcnow()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return self.enabled

    def to_dict(self) -> dict:
        """
        Convert schedule to dictionary for API responses.

        Returns:
            dict: Schedule data
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "task_parameters": self.task_parameters,
            "frequency": self.frequency,
            "cron_expression": self.cron_expression,
            "interval_seconds": self.interval_seconds,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "enabled": self.enabled,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
