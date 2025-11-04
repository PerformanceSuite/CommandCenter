"""Event model for event sourcing and audit trail."""
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, String, JSON, DateTime, Index, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.engine import Dialect

from app.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as
    stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Optional[UUID], dialect: Dialect) -> Optional[str]:
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value) if isinstance(value, UUID) else value
        else:
            if isinstance(value, UUID):
                return str(value)
            else:
                return value

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[UUID]:
        if value is None:
            return value
        else:
            if isinstance(value, UUID):
                return value
            else:
                return UUID(value) if value else None


class Event(Base):
    """Event model for NATS-based event sourcing.

    Events are the source of truth for all state changes in the Hub.
    They are published to NATS subjects and persisted to PostgreSQL.

    Attributes:
        id: Unique event identifier (UUID)
        subject: NATS subject (e.g., 'hub.local-hub.project.created')
        origin: Source metadata (hub_id, service, user)
        correlation_id: Request correlation UUID for tracing
        payload: Event data as JSON
        timestamp: Event creation time (UTC)
    """

    __tablename__ = "events"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)

    # Event metadata
    subject = Column(String, nullable=False, index=True)
    origin = Column(JSON, nullable=False)
    correlation_id = Column(GUID(), nullable=False, index=True)

    # Event content
    payload = Column(JSON, nullable=False)

    # Temporal
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_events_subject_timestamp", "subject", "timestamp"),
        Index("ix_events_correlation_timestamp", "correlation_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, subject={self.subject}, timestamp={self.timestamp})>"
