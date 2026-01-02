"""
ResearchTask model for tracking research activities
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.hypothesis import Hypothesis
    from app.models.project import Project
    from app.models.repository import Repository
    from app.models.research_finding import ResearchFinding
    from app.models.technology import Technology


class TaskStatus(str, enum.Enum):
    """Research task status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ResearchTask(Base):
    """Research task tracking and documentation"""

    __tablename__ = "research_tasks"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign keys
    technology_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("technologies.id", ondelete="CASCADE"), nullable=True
    )
    repository_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True
    )

    # Task details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING
    )

    # Research artifacts
    uploaded_documents: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    user_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Task metadata
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Progress tracking
    progress_percentage: Mapped[int] = mapped_column(default=0)  # 0-100
    estimated_hours: Mapped[Optional[int]] = mapped_column(nullable=True)
    actual_hours: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Additional metadata
    # Note: 'metadata_' to avoid conflict with SQLAlchemy's reserved 'metadata'
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Task type for distinguishing regular research vs ad-hoc hypothesis tasks
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="research"
    )  # "research" or "ad_hoc_hypothesis"

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="research_tasks")
    technology: Mapped[Optional["Technology"]] = relationship(
        "Technology", back_populates="research_tasks"
    )
    repository: Mapped[Optional["Repository"]] = relationship(
        "Repository", back_populates="research_tasks"
    )

    # Intelligence integration relationships
    hypotheses: Mapped[list["Hypothesis"]] = relationship(
        "Hypothesis", back_populates="research_task", cascade="all, delete-orphan"
    )
    research_findings: Mapped[list["ResearchFinding"]] = relationship(
        "ResearchFinding", back_populates="research_task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ResearchTask(id={self.id}, title='{self.title}', status='{self.status.value}')>"
