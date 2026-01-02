"""
Project model for multi-tenant isolation
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base

if TYPE_CHECKING:
    from app.models.hypothesis import Hypothesis
    from app.models.ingestion_source import IngestionSource
    from app.models.skill import Skill
    from app.models.user_project import UserProject


class Project(Base):
    """Project model for multi-tenant isolation

    Each project represents an isolated workspace with its own:
    - Repositories
    - Technologies
    - Research tasks
    - Knowledge entries
    - Webhooks
    - Rate limits

    This ensures complete data isolation between different projects.
    """

    __tablename__ = "projects"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Project identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships (CASCADE DELETE for complete isolation)
    repositories: Mapped[list["Repository"]] = relationship(
        "Repository", back_populates="project", cascade="all, delete-orphan"
    )
    technologies: Mapped[list["Technology"]] = relationship(
        "Technology", back_populates="project", cascade="all, delete-orphan"
    )
    research_tasks: Mapped[list["ResearchTask"]] = relationship(
        "ResearchTask", back_populates="project", cascade="all, delete-orphan"
    )
    knowledge_entries: Mapped[list["KnowledgeEntry"]] = relationship(
        "KnowledgeEntry", back_populates="project", cascade="all, delete-orphan"
    )
    webhook_configs: Mapped[list["WebhookConfig"]] = relationship(
        "WebhookConfig", back_populates="project", cascade="all, delete-orphan"
    )
    webhook_events: Mapped[list["WebhookEvent"]] = relationship(
        "WebhookEvent", back_populates="project", cascade="all, delete-orphan"
    )
    webhook_deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="project", cascade="all, delete-orphan"
    )
    github_rate_limits: Mapped[list["GitHubRateLimit"]] = relationship(
        "GitHubRateLimit", back_populates="project", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(
        "Job", back_populates="project", cascade="all, delete-orphan"
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule", back_populates="project", cascade="all, delete-orphan"
    )
    integrations: Mapped[list["Integration"]] = relationship(
        "Integration", back_populates="project", cascade="all, delete-orphan"
    )
    ingestion_sources: Mapped[list["IngestionSource"]] = relationship(
        "IngestionSource", back_populates="project", cascade="all, delete-orphan"
    )

    # Intelligence integration
    hypotheses: Mapped[list["Hypothesis"]] = relationship(
        "Hypothesis", back_populates="project", cascade="all, delete-orphan"
    )

    # User-Project associations
    user_projects: Mapped[list["UserProject"]] = relationship(
        "UserProject", back_populates="project", cascade="all, delete-orphan"
    )

    # Skills
    skills: Mapped[list["Skill"]] = relationship(
        "Skill", back_populates="project", cascade="all, delete-orphan"
    )

    # Unique constraint: owner + name must be unique
    __table_args__ = (UniqueConstraint("owner", "name", name="uq_project_owner_name"),)

    @validates("name")
    def validate_name(self, key: str, name: str) -> str:
        """Validate project name is not empty and not too long."""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        # Raise error if name is too long
        max_length = 255
        if len(name) > max_length:
            raise ValueError(f"Project name cannot exceed {max_length} characters")
        return name

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', owner='{self.owner}')>"
