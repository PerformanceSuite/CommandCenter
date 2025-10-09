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
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships (CASCADE DELETE for complete isolation)
    repositories: Mapped[list["Repository"]] = relationship(
        "Repository",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    technologies: Mapped[list["Technology"]] = relationship(
        "Technology",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    research_tasks: Mapped[list["ResearchTask"]] = relationship(
        "ResearchTask",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    knowledge_entries: Mapped[list["KnowledgeEntry"]] = relationship(
        "KnowledgeEntry",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    webhook_configs: Mapped[list["WebhookConfig"]] = relationship(
        "WebhookConfig",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    webhook_events: Mapped[list["WebhookEvent"]] = relationship(
        "WebhookEvent",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    github_rate_limits: Mapped[list["GitHubRateLimit"]] = relationship(
        "GitHubRateLimit",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    # Unique constraint: owner + name must be unique
    __table_args__ = (
        UniqueConstraint('owner', 'name', name='uq_project_owner_name'),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', owner='{self.owner}')>"
