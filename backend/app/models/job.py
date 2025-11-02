"""
Job model for tracking async task execution.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, JSON, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobStatus:
    """Job status constants."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType:
    """Job type constants."""

    ANALYSIS = "analysis"
    EXPORT = "export"
    BATCH_ANALYSIS = "batch_analysis"
    BATCH_EXPORT = "batch_export"
    WEBHOOK_DELIVERY = "webhook_delivery"
    SCHEDULED_ANALYSIS = "scheduled_analysis"


class Job(Base):
    """
    Job model for tracking async task execution.

    Tracks Celery tasks with progress, results, and metadata.
    """

    __tablename__ = "jobs"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job identification
    celery_task_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )  # Celery task UUID

    # Job details
    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # analysis, export, etc.
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=JobStatus.PENDING, index=True
    )

    # Progress tracking
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100 percentage
    current_step: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Current operation description

    # Input parameters
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Job input parameters

    # Results
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Job result data
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Error message if failed
    traceback: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Full traceback for debugging

    # Metadata
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # User who created the job
    tags: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # Custom tags for filtering

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="jobs")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="jobs")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_jobs_project_status", "project_id", "status"),
        Index("idx_jobs_type_status", "job_type", "status"),
        Index("idx_jobs_created", "created_at"),
        Index("idx_jobs_celery_task", "celery_task_id"),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type='{self.job_type}', status='{self.status}')>"

    @property
    def duration_seconds(self) -> Optional[float]:
        """
        Calculate job duration in seconds.

        Returns:
            float: Duration in seconds, or None if not completed
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_terminal(self) -> bool:
        """
        Check if job is in a terminal state (completed, failed, cancelled).

        Returns:
            bool: True if job is finished
        """
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        ]

    @property
    def is_active(self) -> bool:
        """
        Check if job is actively running.

        Returns:
            bool: True if job is pending or running
        """
        return self.status in [JobStatus.PENDING, JobStatus.RUNNING]

    def to_dict(self) -> dict:
        """
        Convert job to dictionary for API responses.

        Returns:
            dict: Job data
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "celery_task_id": self.celery_task_id,
            "job_type": self.job_type,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
            "tags": self.tags,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
            "duration_seconds": self.duration_seconds,
        }
