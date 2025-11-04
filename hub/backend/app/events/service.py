"""EventService for publishing, subscribing, and replaying events."""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, List
from uuid import UUID, uuid4

import nats
from nats.js import JetStreamContext
from nats.aio.client import Client as NATS
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.config import get_hub_id

logger = logging.getLogger(__name__)


class EventService:
    """Service for event publishing, subscription, and replay.

    EventService provides a unified interface for:
    - Publishing events to NATS and persisting to PostgreSQL
    - Subscribing to NATS subjects with async handlers
    - Replaying historical events from database

    Events follow the pattern: hub.<hub_id>.<domain>.<action>
    Example: hub.local-hub.project.created
    """

    def __init__(
        self,
        nats_url: str,
        db_session: AsyncSession,
        hub_id: Optional[str] = None
    ):
        """Initialize EventService.

        Args:
            nats_url: NATS server URL (e.g., 'nats://localhost:4222')
            db_session: SQLAlchemy async session for event persistence
            hub_id: Unique Hub identifier (defaults to config)
        """
        self.nats_url = nats_url
        self.db_session = db_session
        self.hub_id = hub_id or get_hub_id()

        self.nc: Optional[NATS] = None
        self.js: Optional[JetStreamContext] = None

    async def connect(self) -> None:
        """Connect to NATS server and initialize JetStream."""
        try:
            self.nc = await nats.connect(self.nats_url)
            self.js = self.nc.jetstream()
            logger.info(f"Connected to NATS at {self.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from NATS server."""
        if self.nc:
            await self.nc.close()
            logger.info("Disconnected from NATS")

    async def publish(
        self,
        subject: str,
        payload: dict,
        correlation_id: Optional[UUID] = None,
        origin: Optional[dict] = None
    ) -> UUID:
        """Publish event to NATS and persist to database.

        Args:
            subject: NATS subject (e.g., 'hub.local-hub.project.created')
            payload: Event data as dictionary
            correlation_id: Request correlation UUID (generated if not provided)
            origin: Source metadata (hub_id, service, user)

        Returns:
            UUID of created event

        Raises:
            Exception: If NATS publish or database insert fails
        """
        # Generate IDs
        event_id = uuid4()
        correlation_id = correlation_id or uuid4()

        # Build origin metadata
        if origin is None:
            origin = {
                "hub_id": self.hub_id,
                "service": "hub-backend",
                "user": None
            }

        # Create event record
        event = Event(
            id=event_id,
            subject=subject,
            origin=origin,
            correlation_id=correlation_id,
            payload=payload,
            timestamp=datetime.now(timezone.utc)
        )

        # Persist to database first (source of truth)
        self.db_session.add(event)
        await self.db_session.commit()
        await self.db_session.refresh(event)

        # Publish to NATS (best effort)
        try:
            if self.nc:
                message = json.dumps({
                    "id": str(event.id),
                    "subject": event.subject,
                    "origin": event.origin,
                    "correlation_id": str(event.correlation_id),
                    "payload": event.payload,
                    "timestamp": event.timestamp.isoformat()
                })
                await self.nc.publish(subject, message.encode())
                logger.debug(f"Published event {event_id} to {subject}")
        except Exception as e:
            logger.error(f"Failed to publish to NATS (persisted to DB): {e}")

        return event_id

    async def subscribe(
        self,
        subject: str,
        handler: Callable[[str, dict], None]
    ) -> None:
        """Subscribe to NATS subject with async handler.

        Args:
            subject: NATS subject pattern (supports wildcards: *, >)
            handler: Async function called with (subject, data) on each message

        Example:
            async def handle_project_events(subject: str, data: dict):
                print(f"Received: {subject} -> {data}")

            await event_service.subscribe("hub.*.project.*", handle_project_events)
        """
        if not self.nc:
            raise RuntimeError("Not connected to NATS. Call connect() first.")

        async def message_handler(msg):
            try:
                data = json.loads(msg.data.decode())
                await handler(msg.subject, data)
            except Exception as e:
                logger.error(f"Error in message handler for {msg.subject}: {e}")

        await self.nc.subscribe(subject, cb=message_handler)
        logger.info(f"Subscribed to {subject}")

    async def replay(
        self,
        subject_filter: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        correlation_id: Optional[UUID] = None,
        limit: int = 1000
    ) -> List[Event]:
        """Replay events from database.

        Args:
            subject_filter: Filter by subject pattern (SQL LIKE, use % for wildcard)
            since: Filter events after this timestamp (inclusive)
            until: Filter events before this timestamp (inclusive)
            correlation_id: Filter by correlation ID
            limit: Maximum events to return (default 1000)

        Returns:
            List of Event objects ordered by timestamp ascending

        Example:
            # Get all project events from last hour
            events = await event_service.replay(
                subject_filter="hub.%.project.%",
                since=datetime.now(timezone.utc) - timedelta(hours=1)
            )
        """
        query = select(Event)

        # Apply filters
        if subject_filter:
            # Convert NATS wildcard (*) to SQL wildcard (%)
            sql_pattern = subject_filter.replace("*", "%")
            query = query.where(Event.subject.like(sql_pattern))

        if since:
            query = query.where(Event.timestamp >= since)

        if until:
            query = query.where(Event.timestamp <= until)

        if correlation_id:
            query = query.where(Event.correlation_id == correlation_id)

        # Order by timestamp and apply limit
        query = query.order_by(Event.timestamp.asc()).limit(limit)

        # Execute query
        result = await self.db_session.execute(query)
        events = result.scalars().all()

        logger.debug(f"Replayed {len(events)} events (filters: subject={subject_filter}, since={since})")
        return list(events)
