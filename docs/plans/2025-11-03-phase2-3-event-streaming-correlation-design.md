# Phase 2-3: Event Streaming & Correlation Design

**Date:** 2025-11-03
**Status:** Design Approved
**Phase:** Event Streaming & Correlation (Weeks 2-3)
**Timeline:** 2-3 weeks (parallel development)
**Dependencies:** Phase 1 Event System Bootstrap (Complete ✅)

---

## Executive Summary

Phase 2-3 extends the Phase 1 event infrastructure with request correlation, real-time streaming, and CLI tools for operational debugging and monitoring. This enables distributed tracing, live event monitoring, and rich querying capabilities essential for production observability.

**Key Deliverables:**
- Correlation middleware for automatic request tracing
- Server-Sent Events (SSE) endpoint for HTTP-based streaming
- Python Click CLI with natural language time parsing
- Enhanced EventService filtering (subject, time, correlation ID)

**Architecture:** Hybrid modular approach - core events in Phase 1 module, new features in dedicated modules (correlation, streaming, cli).

**Development Strategy:** Parallel tracks - Track A (backend: middleware + SSE), Track B (CLI tools), converge at integration.

---

## Architecture Overview

### Module Structure

```
hub/backend/
├── app/
│   ├── events/              # Phase 1 (existing) ✅
│   │   ├── service.py       # Enhanced with filters
│   │   └── models.py        # Event model
│   ├── correlation/         # NEW - Phase 2
│   │   ├── __init__.py
│   │   ├── middleware.py    # FastAPI middleware
│   │   └── context.py       # Correlation context manager
│   ├── streaming/           # NEW - Phase 2
│   │   ├── __init__.py
│   │   ├── sse.py          # Server-Sent Events router
│   │   └── filters.py       # Event filtering logic
│   └── cli/                 # NEW - Phase 2-3
│       ├── __init__.py
│       ├── __main__.py      # Entry point (hub events)
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── query.py     # hub events (default)
│       │   ├── follow.py    # hub events follow
│       │   └── export.py    # hub events export
│       └── utils/
│           ├── __init__.py
│           ├── time_parser.py  # Natural language dates
│           ├── formatters.py   # Output formatting
│           └── nats_client.py  # Direct NATS connection
```

### Parallel Development Tracks

**Track A - Backend Features:**
1. Correlation middleware (Week 1, Day 1-2)
2. SSE streaming endpoint (Week 1, Day 3-5)
3. Enhanced EventService filters (Week 2, Day 1-2)
4. Integration testing (Week 2, Day 3)

**Track B - CLI Tools:**
1. CLI skeleton with Click (Week 1, Day 1-2)
2. Time parsing with dateparser (Week 1, Day 3-4)
3. Query command + formatters (Week 1, Day 5 - Week 2, Day 2)
4. Follow command + NATS client (Week 2, Day 3-5)

**Integration:** Week 2, Day 4-5 + Week 3 (testing, docs, polish)

---

## Component Design

### 1. Correlation Middleware

**Purpose:** Automatically inject correlation IDs into all HTTP requests for distributed tracing.

**Location:** `app/correlation/middleware.py`

**Implementation:**
```python
from fastapi import Request
from uuid import uuid4, UUID
import contextvars
import logging

logger = logging.getLogger(__name__)

# Context variable for correlation ID (thread-safe)
correlation_id_var = contextvars.ContextVar('correlation_id', default=None)

async def correlation_middleware(request: Request, call_next):
    """Auto-inject correlation IDs into all requests

    Flow:
    1. Extract X-Correlation-ID header (if present)
    2. Validate UUID format
    3. Generate new UUID if missing/invalid
    4. Store in request.state and context variable
    5. Process request
    6. Add correlation ID to response headers
    """
    try:
        correlation_id = request.headers.get("X-Correlation-ID")

        # Validate format if provided
        if correlation_id:
            try:
                UUID(correlation_id)  # Validate UUID format
            except ValueError:
                logger.warning(f"Invalid correlation ID format: {correlation_id}")
                correlation_id = str(uuid4())
        else:
            correlation_id = str(uuid4())

        # Store in context for access anywhere in request lifecycle
        correlation_id_var.set(correlation_id)
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    except Exception as e:
        # Middleware should never break request - log and continue
        logger.error(f"Correlation middleware error: {e}", exc_info=True)
        return await call_next(request)

def get_correlation_id() -> str:
    """Get current correlation ID from context"""
    return correlation_id_var.get() or "unknown"
```

**Context Manager:**
```python
# app/correlation/context.py

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

def get_correlation_id() -> Optional[str]:
    """Get correlation ID from current context"""
    return _correlation_id.get()

def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in current context"""
    _correlation_id.set(correlation_id)
```

**Integration (app/main.py):**
```python
from app.correlation.middleware import correlation_middleware

# Add before route handlers, after CORS
app.add_middleware(correlation_middleware)
```

**Testing:**
- Unit: Validate ID generation, preservation, header injection
- Integration: Verify correlation flows through routes to events
- Load: Test context isolation under concurrent requests

---

### 2. Server-Sent Events (SSE) Endpoint

**Purpose:** HTTP-based real-time event streaming for browser clients and external tools.

**Location:** `app/streaming/sse.py`

**Implementation:**
```python
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from datetime import datetime
import asyncio
import json
import logging

from app.database import get_db
from app.events.service import EventService
from app.config import get_nats_url
from app.streaming.filters import apply_filters
from app.cli.utils.time_parser import parse_time

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/events", tags=["events"])

async def event_stream(
    subject: str = "*",
    since: Optional[datetime] = None,
    correlation_id: Optional[UUID] = None,
    db: AsyncSession = None
):
    """SSE generator for real-time events

    Yields events as Server-Sent Events format:
    data: {"id": "...", "subject": "...", ...}

    Handles:
    - NATS subscription for live events
    - Filtering by subject, time, correlation ID
    - Keepalive messages every 30s
    - Graceful error handling
    """
    event_service = EventService(get_nats_url(), db)

    try:
        await event_service.connect()

        # Send initial keepalive
        yield ": keepalive\n\n"

        # Subscribe to filtered events
        last_keepalive = asyncio.get_event_loop().time()

        async for event in event_service.subscribe_filtered(
            subject=subject,
            since=since,
            correlation_id=correlation_id
        ):
            try:
                # Serialize event
                event_dict = {
                    "id": str(event.id),
                    "subject": event.subject,
                    "origin": event.origin,
                    "correlation_id": str(event.correlation_id),
                    "payload": event.payload,
                    "timestamp": event.timestamp.isoformat()
                }
                data = json.dumps(event_dict)
                yield f"data: {data}\n\n"

                # Send keepalive every 30s
                now = asyncio.get_event_loop().time()
                if now - last_keepalive > 30:
                    yield ": keepalive\n\n"
                    last_keepalive = now

                await asyncio.sleep(0)  # Yield control

            except Exception as e:
                logger.error(f"Event serialization error: {e}", exc_info=True)
                error_data = json.dumps({"error": "Event serialization failed"})
                yield f"event: error\ndata: {error_data}\n\n"

    except asyncio.CancelledError:
        logger.info("SSE client disconnected")
        raise
    except Exception as e:
        logger.error(f"SSE stream error: {e}", exc_info=True)
        error_data = json.dumps({"error": "Stream error"})
        yield f"event: error\ndata: {error_data}\n\n"
    finally:
        await event_service.disconnect()

@router.get("/stream")
async def stream_events(
    subject: str = Query("*", description="NATS subject pattern (e.g., 'hub.*.health.*')"),
    since: Optional[str] = Query(None, description="Start time: '1h ago', 'last Monday', ISO 8601"),
    correlation_id: Optional[UUID] = Query(None, description="Filter by correlation ID"),
    db: AsyncSession = Depends(get_db)
):
    """Stream events in real-time via Server-Sent Events

    Usage:
        curl -N http://localhost:9001/api/events/stream?subject=hub.test.*

    JavaScript:
        const events = new EventSource('/api/events/stream?subject=hub.*');
        events.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    since_dt = parse_time(since) if since else None

    return StreamingResponse(
        event_stream(subject, since_dt, correlation_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

**Filter Logic:**
```python
# app/streaming/filters.py

from typing import Optional, AsyncIterator
from datetime import datetime
from uuid import UUID
from app.models.event import Event

async def apply_filters(
    events: AsyncIterator[Event],
    subject: str = "*",
    since: Optional[datetime] = None,
    correlation_id: Optional[UUID] = None
) -> AsyncIterator[Event]:
    """Apply filters to event stream

    Filters:
    - Subject: NATS wildcard matching (* for any segment)
    - Time: Events after 'since' timestamp
    - Correlation ID: Exact match
    """
    async for event in events:
        # Subject filter (wildcard matching)
        if subject != "*":
            if not matches_subject_pattern(event.subject, subject):
                continue

        # Time filter
        if since and event.timestamp < since:
            continue

        # Correlation ID filter
        if correlation_id and event.correlation_id != correlation_id:
            continue

        yield event

def matches_subject_pattern(subject: str, pattern: str) -> bool:
    """Match NATS subject against wildcard pattern

    Patterns:
        * - matches single token
        > - matches one or more tokens

    Examples:
        hub.*.health.* matches hub.local-hub.health.postgres
        hub.> matches hub.local-hub.project.created
    """
    if pattern == "*" or pattern == ">":
        return True

    subject_parts = subject.split(".")
    pattern_parts = pattern.split(".")

    if ">" in pattern:
        # Greedy match - pattern can be shorter
        idx = pattern_parts.index(">")
        prefix = pattern_parts[:idx]
        if len(subject_parts) < len(prefix):
            return False
        for i, part in enumerate(prefix):
            if part != "*" and part != subject_parts[i]:
                return False
        return True
    else:
        # Exact length match with wildcards
        if len(subject_parts) != len(pattern_parts):
            return False
        for s, p in zip(subject_parts, pattern_parts):
            if p != "*" and p != s:
                return False
        return True
```

**Testing:**
- Unit: Filter logic with various patterns
- Integration: SSE connection lifecycle, event delivery
- Performance: 1000+ concurrent SSE connections

---

### 3. Enhanced EventService Filtering

**Purpose:** Add filtering capabilities to Phase 1 EventService for real-time subscriptions.

**Location:** `app/events/service.py` (extend existing)

**Implementation:**
```python
# Add to existing EventService class

async def subscribe_filtered(
    self,
    subject: str = "*",
    since: Optional[datetime] = None,
    correlation_id: Optional[UUID] = None
) -> AsyncIterator[Event]:
    """Subscribe to NATS with filters applied

    Returns:
        AsyncIterator yielding Event objects matching filters

    Note: Filters applied in-memory after NATS delivery.
    For high-volume streams, use specific NATS subjects.
    """
    if not self.nc or not self.nc.is_connected:
        raise RuntimeError("NATS not connected. Call connect() first.")

    # Map wildcard pattern to NATS subject
    nats_subject = subject if subject != "*" else "hub.>"

    # Create async queue for events
    queue = asyncio.Queue(maxsize=1000)

    async def handler(msg):
        try:
            # Parse NATS message to Event
            data = json.loads(msg.data.decode())
            event = Event(**data)

            # Apply filters
            if since and event.timestamp < since:
                return
            if correlation_id and event.correlation_id != correlation_id:
                return

            # Queue event for yielding
            await queue.put(event)

        except Exception as e:
            logger.error(f"Event handler error: {e}", exc_info=True)

    # Subscribe to NATS
    sub = await self.nc.subscribe(nats_subject, cb=handler)

    try:
        while True:
            # Yield events from queue
            event = await asyncio.wait_for(queue.get(), timeout=1.0)
            yield event
    except asyncio.TimeoutError:
        # No events in 1s - continue
        pass
    except asyncio.CancelledError:
        # Client disconnected - cleanup
        await sub.unsubscribe()
        raise
```

**Graceful Degradation:**
```python
async def subscribe_filtered_with_fallback(
    self,
    subject: str = "*",
    since: Optional[datetime] = None,
    correlation_id: Optional[UUID] = None
) -> AsyncIterator[Event]:
    """Subscribe with graceful degradation to DB polling if NATS unavailable"""

    if self.nc and self.nc.is_connected:
        # Normal path - NATS streaming
        async for event in self.subscribe_filtered(subject, since, correlation_id):
            yield event
    else:
        # Degraded mode - poll database
        logger.warning("NATS unavailable, using database polling (degraded mode)")
        async for event in self._poll_database(subject, since, correlation_id):
            yield event
            await asyncio.sleep(1)  # Poll interval

async def _poll_database(
    self,
    subject: str,
    since: Optional[datetime],
    correlation_id: Optional[UUID]
) -> AsyncIterator[Event]:
    """Poll database for events (fallback mode)"""
    from sqlalchemy import select

    last_timestamp = since or datetime.now(timezone.utc)

    while True:
        stmt = select(Event).where(Event.timestamp > last_timestamp)

        if subject != "*":
            stmt = stmt.where(Event.subject.like(subject.replace("*", "%")))
        if correlation_id:
            stmt = stmt.where(Event.correlation_id == correlation_id)

        stmt = stmt.order_by(Event.timestamp.asc())

        result = await self.db_session.execute(stmt)
        events = result.scalars().all()

        for event in events:
            yield event
            last_timestamp = event.timestamp

        await asyncio.sleep(1)  # Poll interval
```

---

### 4. CLI Tools

**Purpose:** Command-line interface for querying, following, and exporting events.

**Tech Stack:** Python Click, dateparser, rich (terminal formatting), nats-py

#### 4.1 CLI Entry Point

**Location:** `app/cli/__main__.py`

**Implementation:**
```python
import click
import asyncio
from app.cli.commands import query, follow, export

@click.group()
@click.version_option(version="1.0.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """CommandCenter Hub event management CLI

    Examples:
        hub events --since "1h ago"
        hub events follow --subject "hub.*.health.*"
        hub events export --format json > events.json
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose

    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

# Default command (hub events = hub events query)
@cli.command(default=True)
@click.option('--since', help='Time range: "1h ago", "last Monday", ISO 8601')
@click.option('--until', help='End time (default: now)')
@click.option('--subject', default='*', help='NATS subject pattern')
@click.option('--correlation-id', help='Filter by correlation ID')
@click.option('--format', type=click.Choice(['table', 'json', 'compact']), default='table')
@click.option('--limit', type=int, default=100, help='Max events to return')
@click.pass_context
def events(ctx, since, until, subject, correlation_id, format, limit):
    """Query historical events (default command)"""
    from app.cli.commands.query import query_cmd
    asyncio.run(query_cmd(since, until, subject, correlation_id, format, limit, ctx.obj['verbose']))

# Subcommands
cli.add_command(follow.follow_cmd, name="follow")
cli.add_command(export.export_cmd, name="export")

if __name__ == '__main__':
    cli()
```

**Setup (pyproject.toml or setup.py):**
```toml
[project.scripts]
hub = "app.cli.__main__:cli"
```

#### 4.2 Time Parser

**Location:** `app/cli/utils/time_parser.py`

**Implementation:**
```python
from datetime import datetime, timezone
from dateparser import parse as dateparse
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def parse_time(time_str: Optional[str]) -> Optional[datetime]:
    """Parse natural language time strings to datetime

    Supports:
    - Relative: "1h ago", "30m ago", "2d ago", "1w ago"
    - Natural: "last Monday", "yesterday at 3pm", "Jan 1"
    - ISO 8601: "2025-11-03T10:00:00Z"

    Returns:
        datetime in UTC timezone, or None if time_str is None

    Raises:
        ValueError: If time string cannot be parsed

    Examples:
        >>> parse_time("1h ago")
        datetime(2025, 11, 3, 9, 0, 0, tzinfo=timezone.utc)

        >>> parse_time("last Monday")
        datetime(2025, 10, 28, 0, 0, 0, tzinfo=timezone.utc)

        >>> parse_time("2025-11-03T10:00:00Z")
        datetime(2025, 11, 3, 10, 0, 0, tzinfo=timezone.utc)
    """
    if not time_str:
        return None

    # Use dateparser for natural language parsing
    dt = dateparse(
        time_str,
        settings={
            'TIMEZONE': 'UTC',
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'past',  # "Monday" = last Monday
            'RELATIVE_BASE': datetime.now(timezone.utc)
        }
    )

    if not dt:
        raise ValueError(f"Could not parse time: {time_str}")

    # Ensure UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)

    logger.debug(f"Parsed '{time_str}' -> {dt.isoformat()}")
    return dt
```

**Dependencies:**
```
dateparser>=1.2.0
python-dateutil>=2.8.0
```

#### 4.3 Query Command

**Location:** `app/cli/commands/query.py`

**Implementation:**
```python
import click
import asyncio
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from datetime import datetime

from app.database import async_session
from app.models.event import Event
from app.cli.utils.time_parser import parse_time
from app.cli.utils.formatters import format_events

async def query_cmd(
    since: Optional[str],
    until: Optional[str],
    subject: str,
    correlation_id: Optional[str],
    format: str,
    limit: int,
    verbose: bool
):
    """Query historical events from database

    Queries PostgreSQL events table with filters, formats output.
    """
    try:
        # Parse time ranges
        try:
            since_dt = parse_time(since) if since else None
            until_dt = parse_time(until) if until else None
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            click.echo("\nExamples:", err=True)
            click.echo("  hub events --since '1h ago'", err=True)
            click.echo("  hub events --since 'last Monday' --until 'yesterday'", err=True)
            click.echo("  hub events --since '2025-11-03T10:00:00Z'", err=True)
            raise click.Abort()

        # Parse correlation ID
        corr_uuid = None
        if correlation_id:
            try:
                corr_uuid = UUID(correlation_id)
            except ValueError:
                click.echo(f"Error: Invalid correlation ID format: {correlation_id}", err=True)
                raise click.Abort()

        # Build query
        async with async_session() as session:
            stmt = select(Event)

            if since_dt:
                stmt = stmt.where(Event.timestamp >= since_dt)
            if until_dt:
                stmt = stmt.where(Event.timestamp <= until_dt)
            if subject != '*':
                # Convert NATS wildcard to SQL LIKE pattern
                sql_pattern = subject.replace('*', '%').replace('>', '%')
                stmt = stmt.where(Event.subject.like(sql_pattern))
            if corr_uuid:
                stmt = stmt.where(Event.correlation_id == corr_uuid)

            stmt = stmt.order_by(Event.timestamp.desc()).limit(limit)

            if verbose:
                click.echo(f"Executing query: {stmt}", err=True)

            result = await session.execute(stmt)
            events = result.scalars().all()

        # Handle empty results
        if not events:
            click.echo("No events found matching filters")
            if since or until or subject != '*' or correlation_id:
                click.echo("\nFilters applied:", err=True)
                if since_dt:
                    click.echo(f"  Since: {since_dt.isoformat()}", err=True)
                if until_dt:
                    click.echo(f"  Until: {until_dt.isoformat()}", err=True)
                if subject != '*':
                    click.echo(f"  Subject: {subject}", err=True)
                if correlation_id:
                    click.echo(f"  Correlation ID: {correlation_id}", err=True)
            return

        # Format and display
        output = format_events(events, format=format)
        click.echo(output)

        # Show count
        if verbose or len(events) == limit:
            click.echo(f"\n{len(events)} events shown", err=True)
            if len(events) == limit:
                click.echo(f"(limited to {limit}, use --limit to increase)", err=True)

    except click.Abort:
        raise
    except Exception as e:
        click.echo(f"Error: Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
```

#### 4.4 Follow Command

**Location:** `app/cli/commands/follow.py`

**Implementation:**
```python
import click
import asyncio
import nats
import json
import signal
from datetime import datetime
from typing import Optional

from app.config import get_nats_url
from app.cli.utils.formatters import format_event_compact

# Global flag for graceful shutdown
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM gracefully"""
    shutdown_event.set()

@click.command()
@click.option('--subject', default='hub.*', help='Subject pattern to follow')
@click.option('--since', help='Only show events after this time')
@click.pass_context
def follow_cmd(ctx, subject: str, since: Optional[str]):
    """Follow live events in real-time (like tail -f)

    Connects directly to NATS for maximum performance.
    Press Ctrl+C to stop.

    Examples:
        hub events follow --subject "hub.*.health.*"
        hub events follow --subject "hub.local-hub.project.*"
    """
    verbose = ctx.obj.get('verbose', False)
    asyncio.run(_follow(subject, since, verbose))

async def _follow(subject: str, since: Optional[str], verbose: bool):
    """Async follow implementation"""
    from app.cli.utils.time_parser import parse_time

    # Parse time filter
    since_dt = None
    if since:
        try:
            since_dt = parse_time(since)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    nc = None
    try:
        # Connect to NATS
        nats_url = get_nats_url()
        if verbose:
            click.echo(f"Connecting to NATS at {nats_url}...", err=True)

        nc = await nats.connect(nats_url)

        click.echo(f"Following events: {subject}", err=True)
        if since_dt:
            click.echo(f"Since: {since_dt.isoformat()}", err=True)
        click.echo("Press Ctrl+C to stop\n", err=True)

        # NATS message handler
        async def handler(msg):
            try:
                # Parse event
                data = json.loads(msg.data.decode())

                # Apply time filter
                if since_dt:
                    event_time = datetime.fromisoformat(data.get('timestamp'))
                    if event_time < since_dt:
                        return

                # Format and print
                output = format_event_compact(data)
                click.echo(output)

            except Exception as e:
                if verbose:
                    click.echo(f"Error processing event: {e}", err=True)

        # Subscribe
        await nc.subscribe(subject, cb=handler)

        # Wait for shutdown signal
        while not shutdown_event.is_set():
            await asyncio.sleep(0.1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
    finally:
        if nc:
            click.echo("\n\nStopped following events", err=True)
            await nc.close()
```

#### 4.5 Output Formatters

**Location:** `app/cli/utils/formatters.py`

**Implementation:**
```python
from typing import List
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

def format_events(events: List, format: str = 'table') -> str:
    """Format events for CLI output

    Formats:
    - table: Rich table with colors (default)
    - json: JSON array
    - compact: One line per event
    """
    if format == 'json':
        return format_events_json(events)
    elif format == 'compact':
        return format_events_compact(events)
    else:
        return format_events_table(events)

def format_events_table(events: List) -> str:
    """Format as rich table"""
    table = Table(
        title=f"Events ({len(events)} total)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Time", style="dim", width=19)
    table.add_column("Subject", style="yellow", no_wrap=False)
    table.add_column("Correlation", style="magenta", width=36)
    table.add_column("Payload", style="green")

    for event in events:
        # Format timestamp
        ts = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Truncate subject if too long
        subject = event.subject
        if len(subject) > 40:
            subject = subject[:37] + "..."

        # Format correlation ID
        corr_id = str(event.correlation_id)

        # Format payload (truncate if large)
        payload_str = json.dumps(event.payload)
        if len(payload_str) > 50:
            payload_str = payload_str[:47] + "..."

        table.add_row(ts, subject, corr_id, payload_str)

    # Render to string
    from io import StringIO
    string_io = StringIO()
    temp_console = Console(file=string_io, force_terminal=True)
    temp_console.print(table)
    return string_io.getvalue()

def format_events_compact(events: List) -> str:
    """Format as compact one-line-per-event"""
    lines = []
    for event in events:
        ts = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        subject = event.subject
        payload = json.dumps(event.payload, separators=(',', ':'))
        lines.append(f"{ts} | {subject} | {payload}")
    return "\n".join(lines)

def format_event_compact(event_data: dict) -> str:
    """Format single event (compact) - for live streaming"""
    ts = datetime.fromisoformat(event_data['timestamp']).strftime("%H:%M:%S")
    subject = event_data['subject']
    payload = json.dumps(event_data['payload'], separators=(',', ':'))
    return f"{ts} | {subject} | {payload}"

def format_events_json(events: List) -> str:
    """Format as JSON array"""
    events_json = [
        {
            "id": str(event.id),
            "subject": event.subject,
            "origin": event.origin,
            "correlation_id": str(event.correlation_id),
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat()
        }
        for event in events
    ]
    return json.dumps(events_json, indent=2)
```

**Dependencies:**
```
rich>=13.0.0  # Terminal formatting
```

---

## Data Flow & Integration

### End-to-End Flow: Debugging with Correlation

**Scenario:** User creates a project, something fails, needs to trace the request.

```
1. HTTP Request arrives at Hub
   POST /api/projects {"name": "myproject"}

2. Correlation Middleware intercepts
   → Generates: correlation_id = "abc-123"
   → Sets request.state.correlation_id = "abc-123"
   → Adds header: X-Correlation-ID: abc-123

3. Project creation logic runs
   → Access correlation ID: request.state.correlation_id
   → Emits event: hub.local-hub.project.created
   → Event includes correlation_id = "abc-123"

4. Something fails downstream (e.g., Dagger container start)
   → Emits event: hub.local-hub.project.failed
   → Same correlation_id = "abc-123"

5. User debugs with CLI
   $ hub events --correlation-id abc-123

   Output (table format):
   ┌──────────┬─────────────────────────────┬────────────┬──────────┐
   │ Time     │ Subject                     │ Corr ID    │ Payload  │
   ├──────────┼─────────────────────────────┼────────────┼──────────┤
   │ 10:30:01 │ hub.local-hub.project.cr... │ abc-123    │ {name:...│
   │ 10:30:05 │ hub.local-hub.dagger.sta... │ abc-123    │ {conta...│
   │ 10:30:12 │ hub.local-hub.project.fa... │ abc-123    │ {error...│
   └──────────┴─────────────────────────────┴────────────┴──────────┘

   Result: User sees complete request flow, identifies Dagger startup as failure point
```

### Real-Time Monitoring Flow

**Scenario:** Ops team monitors health events in real-time.

```
Terminal 1 - Follow health events:
$ hub events follow --subject "hub.*.health.*"

2025-11-03 10:45:12 | hub.local-hub.health.postgres | {status: "healthy"}
2025-11-03 10:45:42 | hub.local-hub.health.nats     | {status: "healthy"}
2025-11-03 10:46:12 | hub.local-hub.health.postgres | {status: "degraded", latency: 250ms}
2025-11-03 10:46:14 | hub.local-hub.health.postgres | {status: "healthy"}

Terminal 2 - Query historical pattern:
$ hub events --since "last hour" --subject "hub.*.health.postgres"
[Shows 60 health checks, 1 degraded event at 10:46:12]

Result: Ops identifies transient postgres latency spike
```

### Integration Architecture

```
┌─────────────────────────────────────────────────────┐
│                   HTTP Clients                      │
│  (Browser, Postman, External Tools)                 │
└────────────┬────────────────────────────────────────┘
             │
             │ X-Correlation-ID header
             ▼
┌─────────────────────────────────────────────────────┐
│         Correlation Middleware                      │
│  - Generate/extract correlation ID                  │
│  - Set request.state.correlation_id                 │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│         FastAPI Route Handlers                      │
│  - Create project, start services, etc.             │
│  - Access correlation ID from request.state         │
└────────────┬────────────────────────────────────────┘
             │
             │ event.publish(correlation_id=...)
             ▼
┌─────────────────────────────────────────────────────┐
│            EventService (Phase 1)                   │
│  - Persist event to PostgreSQL                      │
│  - Publish to NATS subject                          │
└────┬────────────────────────────────┬───────────────┘
     │                                │
     │ DB write                       │ NATS publish
     ▼                                ▼
┌─────────────┐              ┌────────────────────────┐
│ PostgreSQL  │              │      NATS Server       │
│  events     │              │  (JetStream enabled)   │
└─────────────┘              └───┬────────────────┬───┘
                                 │                │
                 ┌───────────────┘                └──────────────┐
                 │                                               │
                 ▼                                               ▼
       ┌──────────────────┐                           ┌──────────────────┐
       │  SSE Endpoint    │                           │   CLI Tool       │
       │  /events/stream  │                           │  (Direct NATS)   │
       │  (HTTP clients)  │                           │  hub events      │
       └──────────────────┘                           └──────────────────┘
```

**Key Integration Points:**
1. Correlation middleware is transparent - routes don't need changes
2. EventService already supports correlation_id parameter (Phase 1)
3. CLI uses either DB queries (historical) or NATS streaming (live)
4. SSE endpoint bridges HTTP and NATS for browser/external clients

---

## Error Handling & Edge Cases

### Error Handling Strategy

| Component | Error Type | Handling | Recovery |
|-----------|-----------|----------|----------|
| **Correlation Middleware** | Invalid UUID format | Log warning, generate new ID | Continue with valid ID |
| | Middleware exception | Log error, continue without correlation | Request succeeds, no correlation |
| **SSE Endpoint** | NATS disconnection | Send error event, close stream | Client reconnects |
| | Event serialization error | Log error, skip event | Stream continues |
| | Client disconnect | Clean shutdown, unsubscribe | No action needed |
| **CLI Query** | Invalid time format | Show error + examples, abort | User corrects input |
| | Database connection error | Show error, abort | User checks DB status |
| | Empty results | Show message + filters applied | User adjusts filters |
| **CLI Follow** | NATS connection error | Show error, abort | User checks NATS status |
| | SIGINT/SIGTERM | Graceful shutdown, close connection | Clean exit |
| **EventService** | NATS unavailable | Fall back to DB polling (degraded mode) | Auto-reconnect on NATS recovery |

### Edge Cases

| Edge Case | Handling |
|-----------|----------|
| **NATS disconnection during stream** | EventService auto-reconnect with exponential backoff (Phase 1 logic) |
| **Database connection pool exhausted** | CLI uses separate connection pool, configurable max_connections |
| **Time zone ambiguity** | dateparser always returns UTC, CLI displays in UTC (future: --local flag) |
| **Large result sets** | CLI limits to 100 events by default, --limit to override, pagination for API |
| **Invalid NATS subject patterns** | Validate format (no spaces, valid wildcards), return clear error message |
| **Concurrent SSE connections** | FastAPI handles concurrency, monitor with Prometheus (connection count metric) |
| **Malformed event JSON in NATS** | Log error, skip event, continue stream (don't break entire flow) |
| **CLI killed mid-stream (follow)** | NATS client auto-cleanup, graceful SIGINT/SIGTERM handlers |
| **Correlation ID collision** | Extremely rare with UUIDv4 (2^-64 probability), no special handling needed |
| **SSE keepalive timeout** | Send keepalive every 30s, nginx/proxy timeout should be >60s |

### Graceful Degradation Example

```python
# EventService - fallback to DB polling if NATS unavailable

async def subscribe_filtered_with_fallback(self, subject, since, correlation_id):
    """Subscribe with graceful degradation"""

    if self.nc and self.nc.is_connected:
        # Normal path - NATS streaming
        logger.info("Using NATS for real-time streaming")
        async for event in self.subscribe_filtered(subject, since, correlation_id):
            yield event
    else:
        # Degraded mode - poll database
        logger.warning("NATS unavailable, using database polling (degraded mode)")
        logger.warning("Performance degraded - events delayed by up to 1 second")

        async for event in self._poll_database(subject, since, correlation_id):
            yield event
            await asyncio.sleep(1)  # Poll interval
```

---

## Testing Strategy

### Unit Tests

**Coverage Goals:**
- Correlation middleware: 100% (critical path)
- Time parser: 95% (handle edge cases)
- CLI commands: 90% (cover main flows)
- SSE streaming: 85% (focus on filtering logic)
- Formatters: 80% (visual output, less critical)

**Key Test Cases:**

```python
# Correlation Middleware
async def test_correlation_middleware_generates_id()
async def test_correlation_middleware_preserves_existing()
async def test_correlation_middleware_validates_uuid_format()
async def test_correlation_middleware_handles_exceptions()

# Time Parser
def test_parse_relative_time()  # "1h ago", "30m ago"
def test_parse_natural_language()  # "last Monday", "yesterday"
def test_parse_iso8601()  # "2025-11-03T10:00:00Z"
def test_parse_invalid_format_raises_error()
def test_parse_timezone_conversion()

# EventService Filtering
async def test_subscribe_filtered_subject_wildcard()
async def test_subscribe_filtered_time_range()
async def test_subscribe_filtered_correlation_id()
async def test_subscribe_filtered_combined_filters()
async def test_subscribe_filtered_graceful_degradation()

# SSE Endpoint
async def test_sse_streams_events()
async def test_sse_applies_filters()
async def test_sse_sends_keepalive()
async def test_sse_handles_client_disconnect()
async def test_sse_error_handling()

# CLI Commands
def test_cli_query_basic()
def test_cli_query_with_time_filter()
def test_cli_query_with_correlation_filter()
def test_cli_query_empty_results()
def test_cli_follow_receives_live_events()
def test_cli_follow_graceful_shutdown()
```

### Integration Tests

**Focus Areas:**
1. End-to-end correlation flow (HTTP → Event → Database → CLI)
2. SSE streaming with real NATS connection
3. CLI integration with database and NATS
4. Error propagation and recovery

**Example Integration Tests:**

```python
# End-to-End Correlation
async def test_correlation_propagates_through_events(client, db_session):
    """Correlation ID flows from HTTP request → event → database → CLI query"""
    correlation_id = str(uuid4())

    # Make HTTP request with correlation ID
    response = await client.post(
        "/api/projects",
        json={"name": "test-project", "path": "/tmp/test"},
        headers={"X-Correlation-ID": correlation_id}
    )
    assert response.headers["X-Correlation-ID"] == correlation_id

    # Verify events in database have same correlation ID
    events = await db_session.execute(
        select(Event).where(Event.correlation_id == correlation_id)
    )
    events = events.scalars().all()
    assert len(events) > 0
    assert all(e.correlation_id == UUID(correlation_id) for e in events)

    # Query via CLI
    result = cli_runner.invoke(cli, ["events", "--correlation-id", correlation_id])
    assert result.exit_code == 0
    assert correlation_id in result.output

# SSE Streaming
async def test_sse_streams_filtered_events(client, event_service):
    """SSE endpoint streams events matching filters"""
    async with client.stream("GET", "/api/events/stream?subject=hub.test.*") as response:
        # Publish test event
        await event_service.publish(subject="hub.test.example", payload={"msg": "test"})

        # Read from SSE stream
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                event_data = json.loads(line[6:])
                assert event_data["subject"] == "hub.test.example"
                break

# CLI Integration
def test_cli_query_with_time_filter(cli_runner, db_session):
    """CLI query filters events by natural language time"""
    # Create historical events
    old_event = Event(subject="hub.old", timestamp=datetime.now() - timedelta(days=2))
    new_event = Event(subject="hub.new", timestamp=datetime.now())
    db_session.add_all([old_event, new_event])
    await db_session.commit()

    # Query with natural language time
    result = cli_runner.invoke(cli, ["events", "--since", "1 day ago"])

    assert result.exit_code == 0
    assert "hub.new" in result.output
    assert "hub.old" not in result.output

def test_cli_follow_receives_live_events(cli_runner, event_service):
    """CLI follow mode receives real-time events from NATS"""
    # Start follow in background
    proc = subprocess.Popen(
        ["hub", "events", "follow", "--subject", "hub.test.*"],
        stdout=subprocess.PIPE
    )
    time.sleep(1)  # Wait for NATS subscription

    # Publish event
    await event_service.publish(subject="hub.test.live", payload={"id": 123})

    # Verify output
    output = proc.stdout.readline().decode()
    assert "hub.test.live" in output
    assert "123" in output

    proc.terminate()
```

### Performance Tests

**Metrics to Validate:**
- SSE: 1000+ concurrent connections
- CLI query: <500ms for 10k events
- CLI follow: <10ms latency from NATS publish to CLI output
- Correlation middleware: <1ms overhead per request

---

## Dependencies

### New Python Packages

Add to `hub/backend/requirements.txt`:

```
# Phase 2-3 Dependencies
dateparser>=1.2.0          # Natural language time parsing
python-dateutil>=2.8.0     # Date utilities (dateparser dependency)
rich>=13.0.0               # Terminal formatting for CLI
click>=8.1.0               # CLI framework
nats-py>=2.6.0             # NATS client (already in Phase 1)
```

### CLI Installation

Add to `hub/backend/pyproject.toml` (or setup.py):

```toml
[project.scripts]
hub = "app.cli.__main__:cli"
```

**Installation:**
```bash
cd hub/backend
pip install -e .  # Editable install, registers 'hub' command
```

**Verification:**
```bash
hub --version  # Should show: 1.0.0
hub events --help  # Should show command help
```

---

## Implementation Timeline

### Week 1: Foundation & Core Features

**Track A - Backend (3 days):**
- Day 1-2: Correlation middleware + tests + integration in main.py
- Day 3-4: SSE endpoint + filtering logic + tests
- Day 5: Enhanced EventService.subscribe_filtered() + graceful degradation

**Track B - CLI (3 days):**
- Day 1-2: CLI skeleton, Click setup, entry point
- Day 3-4: Time parser with dateparser + comprehensive tests
- Day 5: Basic query command + formatters (table, JSON)

### Week 2: Advanced Features & Integration

**Track A - Backend (2 days):**
- Day 1-2: Subject pattern matching, filter optimization
- Day 3: Integration testing (SSE, correlation, filters)

**Track B - CLI (3 days):**
- Day 1-2: Follow command with direct NATS connection
- Day 3: Export command + output formatters (compact, rich)
- Day 4: CLI integration tests

**Integration (2 days):**
- Day 4-5: End-to-end testing, documentation updates

### Week 3: Polish & Documentation

**All Tracks:**
- Day 1-2: Error handling hardening, edge case testing
- Day 3: Performance testing (SSE concurrency, CLI query speed)
- Day 4: Documentation (README, examples, API docs)
- Day 5: Final validation, commit implementation plan

**Total:** 15-17 working days (~2-3 weeks)

---

## Success Criteria

### Functional Requirements

- [ ] **Correlation Middleware**
  - [ ] All HTTP requests have X-Correlation-ID header in response
  - [ ] Correlation IDs propagate to all emitted events
  - [ ] Invalid correlation IDs are rejected and regenerated
  - [ ] Middleware errors don't break requests

- [ ] **SSE Streaming**
  - [ ] `/api/events/stream` endpoint functional
  - [ ] Filtering by subject, time, correlation ID works
  - [ ] Keepalive messages sent every 30s
  - [ ] Graceful handling of NATS disconnection
  - [ ] 1000+ concurrent connections supported

- [ ] **CLI Tools**
  - [ ] `hub events` queries historical events
  - [ ] `hub events follow` streams live events
  - [ ] Natural language time parsing works ("1h ago", "last Monday")
  - [ ] Output formats (table, JSON, compact) all work
  - [ ] Graceful shutdown on SIGINT/SIGTERM

- [ ] **Enhanced EventService**
  - [ ] `subscribe_filtered()` applies all filters correctly
  - [ ] Graceful degradation to DB polling if NATS unavailable
  - [ ] NATS wildcard patterns (* and >) work correctly

### Non-Functional Requirements

- [ ] **Performance**
  - [ ] Correlation middleware: <1ms overhead
  - [ ] SSE: 1000+ concurrent connections
  - [ ] CLI query: <500ms for 10k events
  - [ ] CLI follow: <10ms latency from publish to output

- [ ] **Reliability**
  - [ ] SSE auto-reconnects on NATS disconnection
  - [ ] CLI handles database connection errors gracefully
  - [ ] No data loss during NATS unavailability (DB fallback)

- [ ] **Testing**
  - [ ] 90%+ code coverage for new modules
  - [ ] Integration tests for end-to-end flows
  - [ ] Performance tests validate benchmarks

- [ ] **Documentation**
  - [ ] README updated with Phase 2-3 features
  - [ ] CLI usage examples in docs/
  - [ ] API documentation for SSE endpoint
  - [ ] Docstrings for all public functions

---

## Migration & Rollout

### Phase 1 Compatibility

**No breaking changes to Phase 1:**
- EventService API remains backward compatible
- Existing WebSocket endpoint unchanged
- Database schema unchanged (uses existing events table)

**Additive changes only:**
- New middleware added to main.py
- New SSE endpoint at `/api/events/stream`
- New CLI tools (separate entry point)
- Enhanced EventService methods (opt-in)

### Deployment Steps

1. **Install dependencies**
   ```bash
   cd hub/backend
   pip install -r requirements.txt
   pip install -e .  # Register CLI
   ```

2. **Add correlation middleware**
   ```python
   # app/main.py
   from app.correlation.middleware import correlation_middleware
   app.add_middleware(correlation_middleware)  # After CORS
   ```

3. **Restart Hub backend**
   ```bash
   docker-compose restart hub-backend
   ```

4. **Verify installation**
   ```bash
   hub --version
   curl -N http://localhost:9001/api/events/stream
   ```

### Rollback Plan

**If issues arise:**
1. Remove correlation middleware from main.py
2. Restart hub-backend
3. Phase 1 functionality fully intact

**No database migrations needed** - all features use existing schema.

---

## Next Steps

### Immediate (Post Phase 2-3)

**Phase 4: NATS Bridge (Week 4)**
- Bidirectional NATS bridge for external systems
- JSON-RPC endpoint for non-Python tools
- Event routing rules and transformation pipelines

**Phase 5-6: Hub Federation (Weeks 5-6)**
- Multi-Hub event routing via NATS
- Service discovery and presence announcements
- Cross-Hub correlation tracking

### Future Enhancements

**CLI Improvements:**
- `--local` flag for local timezone display
- `--watch` mode with auto-refresh (like watch command)
- Colorization customization (--no-color, themes)
- Shell completion (bash, zsh, fish)

**Streaming Enhancements:**
- WebSocket protocol (in addition to SSE)
- Event aggregation (count, group by subject)
- Subscription management (pause, resume)

**Monitoring & Metrics:**
- Prometheus metrics for SSE connections, event rates
- Grafana dashboard for event visualization
- AlertManager integration for event-based alerts

---

## Appendix

### A. File Checklist

**New Files Created:**

Backend:
- [ ] `app/correlation/__init__.py`
- [ ] `app/correlation/middleware.py`
- [ ] `app/correlation/context.py`
- [ ] `app/streaming/__init__.py`
- [ ] `app/streaming/sse.py`
- [ ] `app/streaming/filters.py`
- [ ] `app/cli/__init__.py`
- [ ] `app/cli/__main__.py`
- [ ] `app/cli/commands/__init__.py`
- [ ] `app/cli/commands/query.py`
- [ ] `app/cli/commands/follow.py`
- [ ] `app/cli/commands/export.py`
- [ ] `app/cli/utils/__init__.py`
- [ ] `app/cli/utils/time_parser.py`
- [ ] `app/cli/utils/formatters.py`
- [ ] `app/cli/utils/nats_client.py`

Tests:
- [ ] `tests/correlation/test_middleware.py`
- [ ] `tests/streaming/test_sse.py`
- [ ] `tests/streaming/test_filters.py`
- [ ] `tests/cli/test_time_parser.py`
- [ ] `tests/cli/test_formatters.py`
- [ ] `tests/cli/test_query_command.py`
- [ ] `tests/cli/test_follow_command.py`
- [ ] `tests/integration/test_correlation_flow.py`
- [ ] `tests/integration/test_sse_streaming.py`
- [ ] `tests/integration/test_cli_integration.py`

Documentation:
- [ ] `docs/plans/2025-11-03-phase2-3-event-streaming-correlation-design.md` (this file)
- [ ] Update `hub/README.md` with Phase 2-3 features
- [ ] Update `docs/PROJECT.md` with Phase 2-3 status

**Modified Files:**
- [ ] `app/main.py` (add correlation middleware)
- [ ] `app/events/service.py` (add subscribe_filtered)
- [ ] `requirements.txt` (add dependencies)
- [ ] `pyproject.toml` or `setup.py` (add CLI entry point)

### B. Testing Matrix

| Component | Unit Tests | Integration Tests | Performance Tests |
|-----------|-----------|------------------|------------------|
| Correlation Middleware | ✅ 4 tests | ✅ 1 test (E2E flow) | ✅ 1 test (overhead) |
| SSE Endpoint | ✅ 5 tests | ✅ 2 tests (streaming, filters) | ✅ 1 test (1000 connections) |
| EventService Filters | ✅ 6 tests | ✅ 1 test (NATS integration) | ✅ 1 test (filter performance) |
| Time Parser | ✅ 8 tests | N/A | N/A |
| CLI Query | ✅ 5 tests | ✅ 2 tests (DB, output) | ✅ 1 test (10k events) |
| CLI Follow | ✅ 3 tests | ✅ 1 test (live streaming) | ✅ 1 test (latency) |
| Formatters | ✅ 6 tests | N/A | N/A |
| **Total** | **37 unit** | **7 integration** | **5 performance** |

### C. Dependencies Rationale

| Package | Purpose | Alternatives Considered | Decision |
|---------|---------|------------------------|----------|
| `click` | CLI framework | argparse, typer | Click: mature, widely used, good docs |
| `dateparser` | Natural language time | python-dateutil only, parsedatetime | dateparser: best NLP support, active development |
| `rich` | Terminal formatting | colorama, tabulate | rich: modern, powerful, great tables |
| `nats-py` | NATS client | asyncio-nats (older name) | nats-py: official client, async support |

### D. Monitoring & Observability

**Metrics to Track (Future):**
```python
# Prometheus metrics (for Phase C observability integration)

correlation_requests_total = Counter('correlation_requests_total', 'Total requests with correlation IDs')
correlation_invalid_total = Counter('correlation_invalid_total', 'Invalid correlation ID formats')

sse_connections_active = Gauge('sse_connections_active', 'Active SSE connections')
sse_events_sent_total = Counter('sse_events_sent_total', 'Total events sent via SSE', ['subject'])
sse_errors_total = Counter('sse_errors_total', 'SSE errors', ['error_type'])

cli_queries_total = Counter('cli_queries_total', 'CLI queries executed', ['command'])
cli_query_duration_seconds = Histogram('cli_query_duration_seconds', 'CLI query duration')
```

**Grafana Dashboard Ideas:**
- Event rate by subject (line graph)
- SSE connection count over time
- Correlation ID usage (requests with/without correlation)
- CLI query latency percentiles (p50, p95, p99)

---

## Conclusion

Phase 2-3 builds on the solid foundation of Phase 1 Event System Bootstrap to deliver production-ready observability features. The hybrid modular architecture ensures clean separation of concerns while maintaining simplicity. Parallel development tracks maximize velocity, and comprehensive testing ensures reliability.

**Key Outcomes:**
- **Debugging:** Correlation IDs enable distributed tracing across all Hub operations
- **Monitoring:** Real-time SSE streaming and CLI tools provide operational visibility
- **Flexibility:** Multiple streaming options (SSE, WebSocket, direct NATS) serve different use cases
- **Foundation:** Architecture ready for Phase 4+ (federation, compliance, intelligence)

**Ready for Implementation:** All designs validated, timeline clear, success criteria defined.
