"""
User model for authentication and authorization
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from email_validator import validate_email, EmailNotValidError

from app.database import Base


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

    # Relationships
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="user")
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="user")
    integrations: Mapped[list["Integration"]] = relationship("Integration", back_populates="user")

    @validates("email")
    def validate_email_format(self, key: str, email: str) -> str:
        """Validate email format."""
        try:
            # Validate and normalize the email
            validated = validate_email(email)
            return validated.normalized
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {e}")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
