"""
Webhook models for GitHub events
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, JSON, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WebhookConfig(Base):
    """GitHub webhook configuration"""

    __tablename__ = "webhook_configs"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Repository reference
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )

    # Webhook details
    webhook_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # GitHub webhook ID
    webhook_url: Mapped[str] = mapped_column(String(512), nullable=False)
    secret: Mapped[str] = mapped_column(
        String(512), nullable=False
    )  # Webhook secret for verification

    # Event types
    events: Mapped[dict] = mapped_column(
        JSON, default=list
    )  # List of subscribed events

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_delivery_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Delivery configuration (Phase 2 enhancements)
    delivery_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="async"
    )  # async, sync, batch
    retry_count: Mapped[int] = mapped_column(
        Integer, default=3
    )  # Number of retry attempts
    retry_delay_seconds: Mapped[int] = mapped_column(
        Integer, default=300
    )  # Delay between retries (5 minutes)
    max_delivery_time_seconds: Mapped[int] = mapped_column(
        Integer, default=3600
    )  # Max time for delivery (1 hour)

    # Statistics
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    successful_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="webhook_configs"
    )
    repository: Mapped["Repository"] = relationship(
        "Repository", back_populates="webhook_configs"
    )
    events_received: Mapped[list["WebhookEvent"]] = relationship(
        "WebhookEvent", back_populates="config", cascade="all, delete-orphan"
    )
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="config", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WebhookConfig(id={self.id}, repository_id={self.repository_id})>"


class WebhookEvent(Base):
    """Stored GitHub webhook events"""

    __tablename__ = "webhook_events"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

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
    repository_full_name: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )

    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="webhook_events"
    )
    config: Mapped[Optional["WebhookConfig"]] = relationship(
        "WebhookConfig", back_populates="events_received"
    )

    def __repr__(self) -> str:
        return f"<WebhookEvent(id={self.id}, event_type='{self.event_type}', delivery_id='{self.delivery_id}')>"


class WebhookDelivery(Base):
    """Track individual webhook delivery attempts"""

    __tablename__ = "webhook_deliveries"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Webhook config reference
    config_id: Mapped[int] = mapped_column(
        ForeignKey("webhook_configs.id", ondelete="CASCADE"), nullable=False
    )

    # Event details
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # analysis.complete, export.complete, etc.
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Delivery details
    target_url: Mapped[str] = mapped_column(
        String(512), nullable=False
    )  # URL to deliver to
    attempt_number: Mapped[int] = mapped_column(
        Integer, default=1
    )  # Retry attempt (1-based)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # pending, delivered, failed, retrying
    http_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timing
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )  # When to attempt delivery
    attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Request duration in milliseconds

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="webhook_deliveries"
    )
    config: Mapped["WebhookConfig"] = relationship(
        "WebhookConfig", back_populates="deliveries"
    )

    def __repr__(self) -> str:
        return f"<WebhookDelivery(id={self.id}, event_type='{self.event_type}', status='{self.status}', attempt={self.attempt_number})>"


class GitHubRateLimit(Base):
    """Track GitHub API rate limit status"""

    __tablename__ = "github_rate_limits"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

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

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="github_rate_limits"
    )

    def __repr__(self) -> str:
        return f"<GitHubRateLimit(resource_type='{self.resource_type}', remaining={self.remaining}/{self.limit})>"
