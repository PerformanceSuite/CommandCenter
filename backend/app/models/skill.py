"""Skill model for self-improving AI workflows."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class Skill(Base):
    """
    A skill represents a reusable AI workflow pattern.

    Skills can be:
    - Global (project_id=None) - available across all projects
    - Project-specific - only available within a project
    """

    __tablename__ = "skills"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Identification
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)  # The SKILL.md content
    content_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # Optional: path to external file

    # Taxonomy
    category: Mapped[str] = mapped_column(
        String(50), default="workflow"
    )  # workflow, pattern, tool, methodology
    tags: Mapped[list] = mapped_column(JSON, default=list)  # ["multi-agent", "parallel", "e2b"]

    # Versioning
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    # Metadata
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Effectiveness tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    effectiveness_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Multi-tenant
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)  # Visible to other projects?

    # AI Arena validation
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    validation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="skills")
    usages: Mapped[list["SkillUsage"]] = relationship(
        "SkillUsage", back_populates="skill", cascade="all, delete-orphan"
    )

    def record_usage(self, success: Optional[bool] = None):
        """Record a usage of this skill."""
        self.usage_count += 1
        if success is True:
            self.success_count += 1
        elif success is False:
            self.failure_count += 1
        self._update_effectiveness()

    def _update_effectiveness(self):
        """Recalculate effectiveness score."""
        if self.usage_count == 0:
            self.effectiveness_score = 0.0
        else:
            # Simple success rate, can be made more sophisticated
            rated_count = self.success_count + self.failure_count
            if rated_count > 0:
                self.effectiveness_score = self.success_count / rated_count
            else:
                self.effectiveness_score = 0.5  # Unknown

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, slug='{self.slug}', name='{self.name}')>"


class SkillUsage(Base):
    """Track individual uses of skills for effectiveness measurement."""

    __tablename__ = "skill_usages"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id"), nullable=False)

    # Context
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # External session identifier

    # Outcome
    used_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    outcome: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # success, failure, neutral, pending
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="usages")

    def __repr__(self) -> str:
        return f"<SkillUsage(id={self.id}, skill_id={self.skill_id}, outcome='{self.outcome}')>"
