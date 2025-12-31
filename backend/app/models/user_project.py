"""User-Project association for multi-tenant isolation."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class UserProject(Base):
    """Many-to-many association between users and projects with role."""

    __tablename__ = "user_projects"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    # Association metadata
    role: Mapped[str] = mapped_column(String(20), default="member")  # owner, admin, member, viewer
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_projects")
    project: Mapped["Project"] = relationship("Project", back_populates="user_projects")

    # Constraints
    __table_args__ = (UniqueConstraint("user_id", "project_id", name="uq_user_project"),)

    def __repr__(self) -> str:
        return f"<UserProject(user_id={self.user_id}, project_id={self.project_id}, role='{self.role}')>"
