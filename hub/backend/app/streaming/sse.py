"""Server-Sent Events streaming endpoint.

Provides HTTP-based real-time event streaming using SSE protocol.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.events.service import EventService
from app.config import get_nats_url
from app.streaming.filters import matches_subject_pattern
from app.models.event import Event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/events", tags=["events", "streaming"])


async def event_generator(
    subject: str,
    since: Optional[datetime],
    correlation_id: Optional[UUID],
    db: AsyncSession
) -> AsyncIterator[str]:
    """Generate SSE-formatted event stream.

    Yields:
        SSE-formatted strings (data: {...})
    """
    event_service = EventService(get_nats_url(), db)

    try:
        await event_service.connect()
    except Exception as e:
        logger.warning(f"Failed to connect to NATS: {e}. Only historical events will be streamed.")

    try:
        # Send initial keepalive
        yield ": keepalive\n\n"

        # Query historical events first if 'since' provided
        if since:
            try:
                historical = await event_service.query_events(
                    subject=subject if subject != "*" else None,
                    since=since,
                    correlation_id=correlation_id,
                    limit=1000
                )

                for event in historical:
                    yield format_sse_event(event)
            except Exception as e:
                logger.error(f"Error querying historical events: {e}")

        # Stream live events via NATS (if connected)
        if event_service.nc:
            # Use a queue to handle NATS messages in SSE context
            message_queue: asyncio.Queue = asyncio.Queue()

            async def handle_event(subj: str, data: dict):
                """Handle incoming NATS events."""
                # Apply filters
                if subject != "*" and not matches_subject_pattern(subj, subject):
                    return

                if correlation_id and data.get("correlation_id") != str(correlation_id):
                    return

                # Put in queue for SSE stream
                await message_queue.put(data)

            # Subscribe to NATS
            subscription_subject = subject if subject != "*" else "hub.>"
            await event_service.subscribe(subscription_subject, handle_event)

            # Stream messages with keepalive
            while True:
                try:
                    # Wait for message with timeout for keepalive
                    data = await asyncio.wait_for(message_queue.get(), timeout=30.0)
                    event_data = json.dumps(data)
                    yield f"data: {event_data}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
                except asyncio.CancelledError:
                    break
        else:
            # If NATS not connected, just keep connection alive with keepalives
            while True:
                await asyncio.sleep(30)
                yield ": keepalive\n\n"

    except asyncio.CancelledError:
        logger.info("SSE client disconnected")
    except Exception as e:
        logger.error(f"SSE stream error: {e}", exc_info=True)
        error_data = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_data}\n\n"
    finally:
        await event_service.disconnect()


def format_sse_event(event: Event) -> str:
    """Format Event as SSE data line.

    Args:
        event: Event model instance

    Returns:
        SSE-formatted string
    """
    event_dict = {
        "id": str(event.id),
        "subject": event.subject,
        "origin": event.origin,
        "correlation_id": str(event.correlation_id),
        "payload": event.payload,
        "timestamp": event.timestamp.isoformat()
    }
    data = json.dumps(event_dict)
    return f"data: {data}\n\n"


@router.get("/sse")
async def stream_events_sse(
    subject: str = Query("*", description="NATS subject pattern"),
    since: Optional[str] = Query(None, description="Start time (e.g., '1h', ISO)"),
    correlation_id: Optional[UUID] = Query(None, description="Correlation ID filter"),
    db: AsyncSession = Depends(get_db)
):
    """Stream events via Server-Sent Events.

    Usage:
        curl -N http://localhost:9001/api/events/sse?subject=hub.test.*

    JavaScript:
        const events = new EventSource('/api/events/sse');
        events.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    # Parse time if provided (basic time parsing)
    since_dt = None
    if since:
        # Basic time parsing - supports formats like "1h", "2d"
        if since.endswith('h'):
            hours = int(since[:-1])
            since_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
        elif since.endswith('d'):
            days = int(since[:-1])
            since_dt = datetime.now(timezone.utc) - timedelta(days=days)
        elif since.endswith('m'):
            minutes = int(since[:-1])
            since_dt = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        else:
            # Try parsing as ISO format
            try:
                since_dt = datetime.fromisoformat(since)
            except ValueError:
                logger.warning(f"Invalid time format: {since}")

    return StreamingResponse(
        event_generator(subject, since_dt, correlation_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
