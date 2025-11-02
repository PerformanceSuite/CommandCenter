"""
IngestionSource model for automated knowledge ingestion
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Dict, Any
from enum import Enum
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class SourceType(str, Enum):
    """Types of ingestion sources"""

    RSS = "rss"
    DOCUMENTATION = "documentation"
    WEBHOOK = "webhook"
    FILE_WATCHER = "file_watcher"


class SourceStatus(str, Enum):
    """Status of ingestion source"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    DISABLED = "disabled"


class IngestionSource(Base):
    """Configuration for automated knowledge ingestion sources"""

    __tablename__ = "ingestion_sources"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source configuration
    type: Mapped[SourceType] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # URL or path
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Scheduling (cron expression)
    schedule: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Priority (1-10, higher = more important)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # Enable/disable
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Additional configuration (JSON)
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Status tracking
    status: Mapped[SourceStatus] = mapped_column(
        String(50), default=SourceStatus.PENDING, nullable=False
    )
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_success: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metrics
    documents_ingested: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="ingestion_sources")

    def __repr__(self) -> str:
        return f"<IngestionSource(id={self.id}, name='{self.name}', type='{self.type}')>"



