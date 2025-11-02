"""
Integration model for third-party service connections.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, DateTime, JSON, Text, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IntegrationType:
    """Integration type constants."""

    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    SLACK = "slack"
    DISCORD = "discord"
    JIRA = "jira"
    LINEAR = "linear"
    NOTION = "notion"
    CUSTOM_WEBHOOK = "custom_webhook"


class IntegrationStatus:
    """Integration status constants."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class Integration(Base):
    """
    Integration model for third-party service connections.

    Manages OAuth credentials, API tokens, and configuration for external services.
    Supports multiple integration types with encrypted credentials.
    """

    __tablename__ = "integrations"

    # Primary key

if TYPE_CHECKING:
    pass  # Imports added for type checking only

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Integration identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    integration_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # github, slack, jira, etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Authentication (encrypted)
    auth_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # oauth, token, api_key, basic
    credentials: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Encrypted credentials
    access_token_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Encrypted access token
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Encrypted refresh token
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Encrypted API key

    # Token expiration
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    token_refreshed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Integration-specific settings
    webhook_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )  # Webhook endpoint
    scopes: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # OAuth scopes or permissions

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=IntegrationStatus.PENDING, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Health monitoring
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0)  # Consecutive errors
    success_count: Mapped[int] = mapped_column(Integer, default=0)  # Successful operations

    # Rate limiting
    rate_limit_remaining: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rate_limit_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    tags: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # Custom tags for filtering

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="integrations")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="integrations")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_integrations_project_type", "project_id", "integration_type"),
        Index("idx_integrations_status", "status"),
        Index("idx_integrations_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<Integration(id={self.id}, name='{self.name}', type='{self.integration_type}', status='{self.status}')>"

    @property
    def is_healthy(self) -> bool:
        """
        Check if integration is healthy (active and no recent errors).

        Returns:
            bool: True if integration is healthy
        """
        if not self.enabled or self.status != IntegrationStatus.ACTIVE:
            return False
        if self.error_count > 3:  # More than 3 consecutive errors
            return False
        return True

    @property
    def is_token_expired(self) -> bool:
        """
        Check if access token is expired.

        Returns:
            bool: True if token is expired
        """
        if not self.token_expires_at:
            return False
        return datetime.utcnow() >= self.token_expires_at

    @property
    def needs_refresh(self) -> bool:
        """
        Check if token needs refreshing (expires within 1 hour).

        Returns:
            bool: True if token should be refreshed
        """
        if not self.token_expires_at:
            return False
        time_until_expiry = (self.token_expires_at - datetime.utcnow()).total_seconds()
        return time_until_expiry < 3600  # Less than 1 hour

    @property
    def success_rate(self) -> Optional[float]:
        """
        Calculate success rate as a percentage.

        Returns:
            float: Success rate (0-100), or None if no operations yet
        """
        total = self.success_count + self.error_count
        if total == 0:
            return None
        return (self.success_count / total) * 100

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert integration to dictionary for API responses.

        Args:
            include_sensitive: Whether to include sensitive fields (tokens, keys)

        Returns:
            dict: Integration data
        """
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "integration_type": self.integration_type,
            "description": self.description,
            "auth_type": self.auth_type,
            "status": self.status,
            "enabled": self.enabled,
            "is_healthy": self.is_healthy,
            "is_token_expired": self.is_token_expired,
            "needs_refresh": self.needs_refresh,
            "last_sync_at": (self.last_sync_at.isoformat() if self.last_sync_at else None),
            "last_error": self.last_error,
            "last_error_at": (self.last_error_at.isoformat() if self.last_error_at else None),
            "error_count": self.error_count,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset_at": (
                self.rate_limit_reset_at.isoformat() if self.rate_limit_reset_at else None
            ),
            "config": self.config,
            "webhook_url": self.webhook_url,
            "scopes": self.scopes,
            "created_by": self.created_by,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Only include sensitive data if explicitly requested
        if include_sensitive:
            data.update(
                {
                    "credentials": self.credentials,
                    "token_expires_at": (
                        self.token_expires_at.isoformat() if self.token_expires_at else None
                    ),
                }
            )

        return data
