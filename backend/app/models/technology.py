"""
Technology model for tracking research areas and technologies
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Enum as SQLEnum,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    JSON,
)
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


class IntegrationDifficulty(str, enum.Enum):
    """Integration complexity level"""

    TRIVIAL = "trivial"  # < 1 day
    EASY = "easy"  # 1-3 days
    MODERATE = "moderate"  # 1-2 weeks
    COMPLEX = "complex"  # 2-4 weeks
    VERY_COMPLEX = "very_complex"  # > 1 month


class MaturityLevel(str, enum.Enum):
    """Technology maturity level"""

    ALPHA = "alpha"  # Experimental, unstable API
    BETA = "beta"  # Feature-complete, stabilizing
    STABLE = "stable"  # Production-ready, stable API
    MATURE = "mature"  # Battle-tested, widely adopted
    LEGACY = "legacy"  # Maintained but declining


class CostTier(str, enum.Enum):
    """Cost category"""

    FREE = "free"  # Open source, no cost
    FREEMIUM = "freemium"  # Free tier + paid plans
    AFFORDABLE = "affordable"  # < $100/month
    MODERATE = "moderate"  # $100-$500/month
    EXPENSIVE = "expensive"  # > $500/month
    ENTERPRISE = "enterprise"  # Custom pricing


class Technology(Base):
    """Technology tracking and research management"""

    __tablename__ = "technologies"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Technology identification
    title: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    domain: Mapped[TechnologyDomain] = mapped_column(
        SQLEnum(TechnologyDomain), nullable=False, default=TechnologyDomain.OTHER
    )

    # Status and priority
    status: Mapped[TechnologyStatus] = mapped_column(
        SQLEnum(TechnologyStatus), nullable=False, default=TechnologyStatus.DISCOVERY
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

    # Technology Radar v2 - Enhanced Evaluation Fields
    # Performance characteristics
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # P99 latency
    throughput_qps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Queries/sec

    # Integration assessment
    integration_difficulty: Mapped[Optional[IntegrationDifficulty]] = mapped_column(
        SQLEnum(IntegrationDifficulty), nullable=True
    )
    integration_time_estimate_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Maturity and stability
    maturity_level: Mapped[Optional[MaturityLevel]] = mapped_column(
        SQLEnum(MaturityLevel), nullable=True
    )
    stability_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100

    # Cost analysis
    cost_tier: Mapped[Optional[CostTier]] = mapped_column(SQLEnum(CostTier), nullable=True)
    cost_monthly_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dependencies and relationships
    dependencies: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {"tech_id": "relationship"}
    alternatives: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Comma-separated tech IDs

    # Monitoring and alerts
    last_hn_mention: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    hn_score_avg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    github_stars: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    github_last_commit: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="technologies")
    research_tasks: Mapped[list["ResearchTask"]] = relationship(
        "ResearchTask", back_populates="technology", cascade="all, delete-orphan"
    )
    knowledge_entries: Mapped[list["KnowledgeEntry"]] = relationship(
        "KnowledgeEntry", back_populates="technology", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Technology(id={self.id}, title='{self.title}', status='{self.status.value}')>"
