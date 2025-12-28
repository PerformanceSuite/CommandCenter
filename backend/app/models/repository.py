"""
Repository model for tracking GitHub repositories
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.crypto import decrypt_token, encrypt_token


class Repository(Base):
    """GitHub repository tracking"""

    __tablename__ = "repositories"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Repository identification
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)

    # GitHub metadata
    github_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    clone_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")

    # Access control (encrypted)
    _encrypted_access_token: Mapped[Optional[str]] = mapped_column(
        "access_token", String(1024), nullable=True
    )
    is_private: Mapped[bool] = mapped_column(default=False)

    @hybrid_property
    def access_token(self) -> Optional[str]:
        """Get decrypted access token"""
        if self._encrypted_access_token:
            try:
                return decrypt_token(self._encrypted_access_token)
            except Exception:
                # If decryption fails, return None
                return None
        return None

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        """Set access token (will be encrypted)"""
        if value:
            self._encrypted_access_token = encrypt_token(value)
        else:
            self._encrypted_access_token = None

    # Last sync information
    last_commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    last_commit_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_commit_author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_commit_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Repository stats
    stars: Mapped[int] = mapped_column(default=0)
    forks: Mapped[int] = mapped_column(default=0)
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Additional metadata (JSON field for flexibility)
    # Note: 'metadata_' to avoid conflict with SQLAlchemy's reserved 'metadata'
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships (forward references for SQLAlchemy)
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="repositories"
    )
    research_tasks: Mapped[list["ResearchTask"]] = relationship(  # noqa: F821
        "ResearchTask", back_populates="repository", cascade="all, delete-orphan"
    )
    webhook_configs: Mapped[list["WebhookConfig"]] = relationship(  # noqa: F821
        "WebhookConfig", back_populates="repository", cascade="all, delete-orphan"
    )
    technologies: Mapped[list["Technology"]] = relationship(  # noqa: F821
        "Technology",
        secondary="technology_repositories",
        back_populates="repositories",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, full_name='{self.full_name}')>"
