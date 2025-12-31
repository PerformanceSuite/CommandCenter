"""
User model for authentication and authorization
"""

import os
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base

if TYPE_CHECKING:
    from app.models.user_project import UserProject


class User(Base):
    """User account for authentication"""

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships (forward references for SQLAlchemy)
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="user")  # noqa: F821
    schedules: Mapped[list["Schedule"]] = relationship(  # noqa: F821
        "Schedule", back_populates="user"
    )
    integrations: Mapped[list["Integration"]] = relationship(  # noqa: F821
        "Integration", back_populates="user"
    )
    user_projects: Mapped[list["UserProject"]] = relationship(
        "UserProject", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def default_project_id(self) -> Optional[int]:
        """Get user's default project ID."""
        for up in self.user_projects:
            if up.is_default:
                return up.project_id
        # Return first project if no default set
        if self.user_projects:
            return self.user_projects[0].project_id
        return None

    @validates("email")
    def validate_email_format(self, key: str, email: str) -> str:
        """Validate email format."""
        try:
            # Allow test domains (example.com, test.com) in test environment
            is_test_env = os.getenv("ENVIRONMENT") == "test"
            # Validate and normalize the email (lowercase for consistency)
            validated = validate_email(email, test_environment=is_test_env)
            return validated.normalized.lower()
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {e}")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
