"""
Webhook models for GitHub events
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, JSON, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.repository import Repository


class WebhookConfig(Base):
    """GitHub webhook configuration"""

    __tablename__ = "webhook_configs"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Repository reference
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )

    # Webhook details
    webhook_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # GitHub webhook ID
    webhook_url: Mapped[str] = mapped_column(String(512), nullable=False)
    secret: Mapped[str] = mapped_column(
        String(512), nullable=False
    )  # Webhook secret for verification

    # Event types
    events: Mapped[dict] = mapped_column(JSON, default=list)  # List of subscribed events

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_delivery_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="webhook_configs")
    events_received: Mapped[list["WebhookEvent"]] = relationship(
        "WebhookEvent", back_populates="config", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WebhookConfig(id={self.id}, repository_id={self.repository_id})>"


class WebhookEvent(Base):
    """Stored GitHub webhook events"""

    __tablename__ = "webhook_events"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Webhook config reference
    config_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("webhook_configs.id", ondelete="SET NULL"), nullable=True
    )

    # Event details
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # push, pull_request, issue, etc.
    delivery_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )  # GitHub delivery ID

    # Event payload
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Repository info (denormalized for easier querying)
    repository_full_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    config: Mapped[Optional["WebhookConfig"]] = relationship(
        "WebhookConfig", back_populates="events_received"
    )

    def __repr__(self) -> str:
        return (
            f"<WebhookEvent(id={self.id}, "
            f"event_type='{self.event_type}', "
            f"delivery_id='{self.delivery_id}')>"
        )


class GitHubRateLimit(Base):
    """Track GitHub API rate limit status"""

    __tablename__ = "github_rate_limits"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Rate limit type (core, search, graphql)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Rate limit details
    limit: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    reset_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Used for (optional user/token tracking)
    token_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Timestamps
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<GitHubRateLimit(resource_type='{self.resource_type}', "
            f"remaining={self.remaining}/{self.limit})>"
        )
