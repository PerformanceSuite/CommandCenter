"""Event API endpoints for Hub backend."""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.events.service import EventService
from app.models.event import Event
from app.config import get_nats_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])


# Schemas
class PublishEventRequest(BaseModel):
    """Request schema for publishing an event."""
    subject: str = Field(..., description="NATS subject (e.g., 'hub.local-hub.project.created')")
    payload: dict = Field(..., description="Event data as JSON")
    correlation_id: Optional[UUID] = Field(None, description="Request correlation ID")


class PublishEventResponse(BaseModel):
    """Response schema for published event."""
    event_id: UUID
    correlation_id: UUID
    timestamp: datetime


class EventResponse(BaseModel):
    """Response schema for event query."""
    id: UUID
    subject: str
    origin: dict
    correlation_id: UUID
    payload: dict
    timestamp: datetime

    class Config:
        from_attributes = True


# Dependency for EventService
async def get_event_service(db: AsyncSession = Depends(get_db)):
    """Create EventService instance with database session."""
    service = EventService(nats_url=get_nats_url(), db_session=db)
    try:
        await service.connect()
    except Exception as e:
        logger.warning(f"Failed to connect to NATS: {e}. Events will be persisted to DB only.")
    try:
        yield service
    finally:
        await service.disconnect()


# Endpoints
@router.post("", response_model=PublishEventResponse, status_code=201)
async def publish_event(
    request: PublishEventRequest,
    event_service: EventService = Depends(get_event_service)
) -> PublishEventResponse:
    """Publish event to NATS and persist to database.

    Args:
        request: Event data (subject, payload, optional correlation_id)
        event_service: EventService instance

    Returns:
        Published event metadata (event_id, correlation_id, timestamp)
    """
    try:
        event_id = await event_service.publish(
            subject=request.subject,
            payload=request.payload,
            correlation_id=request.correlation_id
        )

        # Get created event for response
        result = await event_service.db_session.execute(
            select(Event).where(Event.id == event_id)
        )
        event = result.scalar_one()

        return PublishEventResponse(
            event_id=event.id,
            correlation_id=event.correlation_id,
            timestamp=event.timestamp
        )
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[EventResponse])
async def query_events(
    subject: Optional[str] = Query(None, description="Subject filter (supports SQL LIKE with %)"),
    since: Optional[datetime] = Query(None, description="Events after this timestamp"),
    until: Optional[datetime] = Query(None, description="Events before this timestamp"),
    correlation_id: Optional[UUID] = Query(None, description="Filter by correlation ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum events to return"),
    event_service: EventService = Depends(get_event_service)
) -> List[EventResponse]:
    """Query events from database with filters.

    Args:
        subject: Subject filter (SQL LIKE pattern, use % for wildcard)
        since: Events after this timestamp (inclusive)
        until: Events before this timestamp (inclusive)
        correlation_id: Filter by correlation ID
        limit: Maximum events to return (1-1000)
        event_service: EventService instance

    Returns:
        List of events matching filters
    """
    try:
        events = await event_service.replay(
            subject_filter=subject,
            since=since,
            until=until,
            correlation_id=correlation_id,
            limit=limit
        )
        return [EventResponse.from_orm(event) for event in events]
    except Exception as e:
        logger.error(f"Failed to query events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """Get specific event by ID.

    Args:
        event_id: Event UUID
        db: Database session

    Returns:
        Event details

    Raises:
        HTTPException: 404 if event not found
    """
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return EventResponse.from_orm(event)


@router.websocket("/stream")
async def stream_events(
    websocket: WebSocket,
    subject: str = Query("hub.>", description="NATS subject pattern to stream")
):
    """Stream events via WebSocket.

    Args:
        websocket: WebSocket connection
        subject: NATS subject pattern (supports wildcards: *, >)

    Example:
        ws://localhost:9001/api/events/stream?subject=hub.*.project.*
    """
    await websocket.accept()

    # Create event service
    async for db in get_db():
        event_service = EventService(nats_url=get_nats_url(), db_session=db)
        try:
            await event_service.connect()
        except Exception as e:
            await websocket.send_json({"error": f"Failed to connect to NATS: {e}"})
            await websocket.close()
            return

        try:
            # Subscribe to NATS subject
            async def handler(msg_subject: str, data: dict):
                await websocket.send_json({
                    "subject": msg_subject,
                    "data": data
                })

            await event_service.subscribe(subject, handler)

            # Keep connection alive
            while True:
                try:
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break

        finally:
            await event_service.disconnect()
        break
