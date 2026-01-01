"""Server-Sent Events streaming endpoint for graph updates.

Sprint 4: Real-time Subscriptions
Bridges NATS events to HTTP SSE stream for live graph updates.

Reference: hub/backend/app/streaming/sse.py
"""

import asyncio
import json
import logging
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.nats_client import NATSClient, get_nats_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/events", tags=["events", "streaming"])


def matches_subject_pattern(subject: str, pattern: str) -> bool:
    """Check if a NATS subject matches a pattern.

    Supports wildcards:
    - '*' matches a single token
    - '>' matches one or more tokens (must be at end)

    Args:
        subject: Actual subject (e.g., 'graph.node.created')
        pattern: Pattern to match (e.g., 'graph.*', 'graph.>')

    Returns:
        True if subject matches pattern
    """
    if pattern == "*" or pattern == ">":
        return True

    subject_parts = subject.split(".")
    pattern_parts = pattern.split(".")

    for i, pat in enumerate(pattern_parts):
        if pat == ">":
            # '>' matches rest of subject
            return True
        if i >= len(subject_parts):
            return False
        if pat == "*":
            # '*' matches single token
            continue
        if pat != subject_parts[i]:
            return False

    # Pattern fully matched, check subject has no extra parts
    return len(subject_parts) == len(pattern_parts)


async def graph_event_generator(
    project_id: int,
    subjects: list[str],
    nats_client: NATSClient,
) -> AsyncIterator[str]:
    """Generate SSE-formatted event stream from NATS.

    Args:
        project_id: Project ID to filter events
        subjects: List of NATS subject patterns to subscribe
        nats_client: Connected NATS client

    Yields:
        SSE-formatted strings
    """
    # Send initial connection event
    connected_data = json.dumps({"project_id": project_id, "subjects": subjects})
    yield f"event: connected\ndata: {connected_data}\n\n"

    # Create message queue for async handling
    message_queue: asyncio.Queue = asyncio.Queue()

    async def handle_event(subject: str, data: dict):
        """Handle incoming NATS events."""
        # Filter by project_id if present in payload
        event_project_id = data.get("project_id")
        if event_project_id is not None and event_project_id != project_id:
            return

        # Check if subject matches any of our patterns
        if subjects != ["graph.*"]:  # Default pattern matches all graph events
            matched = any(matches_subject_pattern(subject, pat) for pat in subjects)
            if not matched:
                return

        # Add subject to data for frontend
        data["_subject"] = subject

        await message_queue.put(data)

    # Subscribe to graph events
    subscription_pattern = "graph.>"  # All graph events
    try:
        await nats_client.subscribe(subscription_pattern, handle_event)
        logger.info(f"SSE: Subscribed to {subscription_pattern} for project {project_id}")
    except Exception as e:
        logger.error(f"SSE: Failed to subscribe to NATS: {e}")
        error_data = json.dumps({"error": f"Failed to subscribe: {e}"})
        yield f"event: error\ndata: {error_data}\n\n"
        return

    try:
        while True:
            try:
                # Wait for message with timeout for keepalive
                data = await asyncio.wait_for(message_queue.get(), timeout=30.0)
                event_data = json.dumps(data)
                subject = data.get("_subject", "graph.event")
                yield f"event: {subject}\ndata: {event_data}\n\n"
            except asyncio.TimeoutError:
                # Send keepalive comment
                yield ": keepalive\n\n"
            except asyncio.CancelledError:
                logger.info(f"SSE: Client disconnected (project {project_id})")
                break
    except Exception as e:
        logger.error(f"SSE: Stream error: {e}", exc_info=True)
        error_data = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_data}\n\n"


async def fallback_generator(project_id: int) -> AsyncIterator[str]:
    """Fallback generator when NATS is not available.

    Sends keepalives to maintain connection.
    """
    connected_data = json.dumps(
        {"project_id": project_id, "warning": "NATS not connected - no live updates available"}
    )
    yield f"event: connected\ndata: {connected_data}\n\n"

    try:
        while True:
            await asyncio.sleep(30)
            yield ": keepalive\n\n"
    except asyncio.CancelledError:
        logger.info(f"SSE: Fallback client disconnected (project {project_id})")


@router.get("/stream")
async def stream_graph_events(
    project_id: int = Query(..., description="Project ID to filter events"),
    subjects: Optional[str] = Query(
        "graph.*", description="Comma-separated NATS subject patterns (default: graph.*)"
    ),
):
    """Stream graph events via Server-Sent Events.

    Connects to NATS and bridges graph mutation events to the client.
    Events are filtered by project_id to ensure data isolation.

    Args:
        project_id: Required project ID for filtering
        subjects: Optional comma-separated subject patterns

    Returns:
        StreamingResponse with SSE events

    Usage:
        curl -N "http://localhost:8000/api/v1/events/stream?project_id=1"

    JavaScript:
        const events = new EventSource('/api/v1/events/stream?project_id=1');
        events.addEventListener('connected', (e) => console.log('Connected:', e.data));
        events.addEventListener('graph.node.created', (e) => console.log('Node created:', e.data));
        events.onmessage = (e) => console.log('Event:', e.data);
    """
    # Parse subjects
    subject_list = [s.strip() for s in subjects.split(",")] if subjects else ["graph.*"]

    # Get NATS client
    nats_client = await get_nats_client()

    if nats_client and nats_client.nc:
        generator = graph_event_generator(project_id, subject_list, nats_client)
    else:
        logger.warning(f"SSE: NATS not available, using fallback for project {project_id}")
        generator = fallback_generator(project_id)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/health")
async def events_health():
    """Check SSE endpoint health and NATS connectivity."""
    nats_client = await get_nats_client()

    nats_connected = bool(nats_client and nats_client.nc)

    return {
        "status": "healthy" if nats_connected else "degraded",
        "nats_connected": nats_connected,
        "supported_subjects": [
            "graph.node.created",
            "graph.node.updated",
            "graph.node.deleted",
            "graph.edge.created",
            "graph.edge.deleted",
            "graph.invalidated",
        ],
    }
