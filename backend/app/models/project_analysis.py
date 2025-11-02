"""
Project Analysis model for caching analysis results
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProjectAnalysis(Base):
    """
    Project analysis results cache.

    Stores complete analysis results to avoid re-scanning projects.
    Analysis version enables cache invalidation when logic changes.
    """

    __tablename__ = "project_analyses"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Project identification
    project_path: Mapped[str] = mapped_column(
        String(1024), nullable=False, index=True, unique=True
    )

    # Analysis results (stored as JSONB for flexibility)
    detected_technologies: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, doc="List of detected technologies with metadata"
    )
    dependencies: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        doc="List of dependencies with version information",
    )
    code_metrics: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, doc="Code structure and complexity metrics"
    )
    research_gaps: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        doc="Identified research gaps and upgrade opportunities",
    )

    # Analysis metadata
    analysis_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0.0",
        doc="Analysis logic version for cache invalidation",
    )
    analysis_duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Analysis duration in milliseconds",
    )

    # Timestamps
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ProjectAnalysis(id={self.id}, project_path='{self.project_path}', analyzed_at='{self.analyzed_at}')>"
