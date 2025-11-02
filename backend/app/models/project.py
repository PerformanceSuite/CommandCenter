"""
Project model for multi-tenant isolation
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
    repositories: Mapped[list["Repository"]] = relationship(  # noqa: F821
        "Repository", back_populates="project", cascade="all, delete-orphan"  # noqa: F821
    )
    technologies: Mapped[list["Technology"]] = relationship(  # noqa: F821
        "Technology", back_populates="project", cascade="all, delete-orphan"  # noqa: F821
    )
    research_tasks: Mapped[list["ResearchTask"]] = relationship(  # noqa: F821
        "ResearchTask", back_populates="project", cascade="all, delete-orphan"  # noqa: F821
    )
    knowledge_entries: Mapped[list["KnowledgeEntry"]] = relationship(  # noqa: F821
        "KnowledgeEntry",
        back_populates="project",  # noqa: F821
        cascade="all, delete-orphan",
    )
    webhook_configs: Mapped[list["WebhookConfig"]] = relationship(  # noqa: F821
        "WebhookConfig", back_populates="project", cascade="all, delete-orphan"  # noqa: F821
    )
    webhook_events: Mapped[list["WebhookEvent"]] = relationship(  # noqa: F821
        "WebhookEvent", back_populates="project", cascade="all, delete-orphan"  # noqa: F821
    )
    webhook_deliveries: Mapped[list["WebhookDelivery"]] = relationship(  # noqa: F821
        "WebhookDelivery",
        back_populates="project",  # noqa: F821
        cascade="all, delete-orphan",
    )
    github_rate_limits: Mapped[list["GitHubRateLimit"]] = relationship(  # noqa: F821
        "GitHubRateLimit",
        back_populates="project",  # noqa: F821
        cascade="all, delete-orphan",
    )
    jobs: Mapped[list["Job"]] = relationship(  # noqa: F821
        "Job", back_populates="project", cascade="all, delete-orphan"  # noqa: F821
    )
    schedules: Mapped[list["Schedule"]] = relationship(  # noqa: F821
        "Schedule", back_populates="project", cascade="all, delete-orphan"  # noqa: F821
    )
    integrations: Mapped[list["Integration"]] = relationship(  # noqa: F821
        "Integration", back_populates="project", cascade="all, delete-orphan"  # noqa: F821
    )

    # Unique constraint: owner + name must be unique
    __table_args__ = (UniqueConstraint("owner", "name", name="uq_project_owner_name"),)

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', owner='{self.owner}')>"
