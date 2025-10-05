"""
Technology model for tracking research areas and technologies
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class TechnologyDomain(str, enum.Enum):
    """Technology domain categories"""
    AUDIO_DSP = "audio-dsp"
    AI_ML = "ai-ml"
    MUSIC_THEORY = "music-theory"
    PERFORMANCE = "performance"
    UI_UX = "ui-ux"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


class TechnologyStatus(str, enum.Enum):
    """Technology research/implementation status"""
    DISCOVERY = "discovery"
    RESEARCH = "research"
    EVALUATION = "evaluation"
    IMPLEMENTATION = "implementation"
    INTEGRATED = "integrated"
    ARCHIVED = "archived"


class Technology(Base):
    """Technology tracking and research management"""

    __tablename__ = "technologies"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Technology identification
    title: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    domain: Mapped[TechnologyDomain] = mapped_column(
        SQLEnum(TechnologyDomain),
        nullable=False,
        default=TechnologyDomain.OTHER
    )

    # Status and priority
    status: Mapped[TechnologyStatus] = mapped_column(
        SQLEnum(TechnologyStatus),
        nullable=False,
        default=TechnologyStatus.DISCOVERY
    )
    relevance_score: Mapped[int] = mapped_column(default=50)  # 0-100
    priority: Mapped[int] = mapped_column(default=3)  # 1-5 (5=highest)

    # Description and notes
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    use_cases: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # External links
    documentation_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    repository_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Tags for filtering
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Comma-separated

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    research_tasks: Mapped[list["ResearchTask"]] = relationship(
        "ResearchTask",
        back_populates="technology",
        cascade="all, delete-orphan"
    )
    knowledge_entries: Mapped[list["KnowledgeEntry"]] = relationship(
        "KnowledgeEntry",
        back_populates="technology",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Technology(id={self.id}, title='{self.title}', status='{self.status.value}')>"
