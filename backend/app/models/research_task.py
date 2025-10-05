"""
ResearchTask model for tracking research activities
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Enum as SQLEnum, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


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

    # Foreign keys
    technology_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("technologies.id", ondelete="CASCADE"),
        nullable=True
    )
    repository_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=True
    )

    # Task details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING
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
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    technology: Mapped[Optional["Technology"]] = relationship(
        "Technology",
        back_populates="research_tasks"
    )
    repository: Mapped[Optional["Repository"]] = relationship(
        "Repository",
        back_populates="research_tasks"
    )

    def __repr__(self) -> str:
        return f"<ResearchTask(id={self.id}, title='{self.title}', status='{self.status.value}')>"
