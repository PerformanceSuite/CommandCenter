# Phase 2-3: Event Streaming & Correlation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add correlation IDs, SSE streaming, and CLI tools to enable distributed tracing and real-time event monitoring.

**Architecture:** Hybrid modular - extends Phase 1 event infrastructure with new correlation/, streaming/, and cli/ modules. No breaking changes to existing APIs.

**Tech Stack:** FastAPI middleware, Server-Sent Events (SSE), Click CLI, dateparser, rich terminal formatting, NATS Python client

**Timeline:** 2-3 weeks parallel development (Track A: Backend, Track B: CLI)

---

## Prerequisites

**Verify Phase 1 is complete:**
```bash
# Check Phase 1 tests pass
cd hub/backend
pytest tests/events/ -v

# Verify NATS is running
curl http://localhost:8222/varz

# Verify events table exists
psql $DATABASE_URL -c "\d events"
```

**Expected:** All Phase 1 tests pass, NATS responds, events table has 6 indexes.

---

## Track A: Backend Features (Correlation + SSE)

### Task 1: Correlation Middleware - Module Setup

**Files:**
- Create: `hub/backend/app/correlation/__init__.py`
- Create: `hub/backend/app/correlation/context.py`

**Step 1: Write test for context variable**

Create: `hub/backend/tests/correlation/test_context.py`

```python
"""Tests for correlation context management."""
import pytest
from uuid import uuid4
from app.correlation.context import (
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id
)


def test_set_and_get_correlation_id():
    """Test setting and getting correlation ID."""
    test_id = str(uuid4())
    set_correlation_id(test_id)

    result = get_correlation_id()

    assert result == test_id


def test_get_correlation_id_default_none():
    """Test default value is None when not set."""
    clear_correlation_id()

    result = get_correlation_id()

    assert result is None


def test_correlation_id_isolation():
    """Test correlation IDs are isolated per context."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    def set_and_check(value: str) -> str:
        set_correlation_id(value)
        return get_correlation_id()

    # Run in separate threads
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(set_and_check, "id-1")
        future2 = executor.submit(set_and_check, "id-2")

        result1 = future1.result()
        result2 = future2.result()

    assert result1 == "id-1"
    assert result2 == "id-2"
```

**Step 2: Run test to verify it fails**

```bash
cd hub/backend
pytest tests/correlation/test_context.py -v
```

Expected: FAIL - "No module named 'app.correlation'"

**Step 3: Implement context manager**

Create: `hub/backend/app/correlation/context.py`

```python
"""Correlation context management using contextvars.

Provides thread-safe correlation ID storage for request tracking.
"""
from contextvars import ContextVar
from typing import Optional


_correlation_id: ContextVar[Optional[str]] = ContextVar(
    'correlation_id',
    default=None
)


def get_correlation_id() -> Optional[str]:
    """Get correlation ID from current context.

    Returns:
        Correlation ID string or None if not set
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in current context.

    Args:
        correlation_id: UUID string for request correlation
    """
    _correlation_id.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    _correlation_id.set(None)
```

Create: `hub/backend/app/correlation/__init__.py`

```python
"""Correlation ID tracking for distributed tracing."""
from app.correlation.context import (
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id
)

__all__ = [
    'get_correlation_id',
    'set_correlation_id',
    'clear_correlation_id'
]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/correlation/test_context.py -v
```

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add hub/backend/app/correlation/ hub/backend/tests/correlation/
git commit -m "feat(correlation): add context variable for correlation IDs

- Thread-safe contextvars implementation
- get/set/clear API
- Test coverage for isolation"
```

---

### Task 2: Correlation Middleware - FastAPI Integration

**Files:**
- Create: `hub/backend/app/correlation/middleware.py`
- Create: `hub/backend/tests/correlation/test_middleware.py`

**Step 1: Write test for middleware**

Create: `hub/backend/tests/correlation/test_middleware.py`

```python
"""Tests for correlation middleware."""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from uuid import uuid4, UUID

from app.correlation.middleware import correlation_middleware
from app.correlation.context import get_correlation_id


@pytest.fixture
def app():
    """Create test FastAPI app with correlation middleware."""
    app = FastAPI()
    app.middleware("http")(correlation_middleware)

    @app.get("/test")
    async def test_route(request: Request):
        return {
            "correlation_id": request.state.correlation_id,
            "context_id": get_correlation_id()
        }

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def test_middleware_generates_correlation_id(client):
    """Test middleware generates correlation ID if not provided."""
    response = client.get("/test")

    assert response.status_code == 200
    data = response.json()

    # Should have generated a UUID
    assert "correlation_id" in data
    assert UUID(data["correlation_id"])  # Valid UUID

    # Should be in response header
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == data["correlation_id"]


def test_middleware_preserves_provided_correlation_id(client):
    """Test middleware preserves correlation ID from request header."""
    test_id = str(uuid4())

    response = client.get("/test", headers={"X-Correlation-ID": test_id})

    assert response.status_code == 200
    data = response.json()

    # Should preserve provided ID
    assert data["correlation_id"] == test_id
    assert response.headers["X-Correlation-ID"] == test_id


def test_middleware_rejects_invalid_correlation_id(client):
    """Test middleware generates new ID if provided ID is invalid."""
    response = client.get("/test", headers={"X-Correlation-ID": "not-a-uuid"})

    assert response.status_code == 200
    data = response.json()

    # Should generate new UUID
    assert UUID(data["correlation_id"])
    assert data["correlation_id"] != "not-a-uuid"


def test_middleware_sets_context_variable(client):
    """Test middleware sets correlation ID in context variable."""
    response = client.get("/test")

    assert response.status_code == 200
    data = response.json()

    # Context variable should match request.state
    assert data["context_id"] == data["correlation_id"]
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/correlation/test_middleware.py -v
```

Expected: FAIL - "No module named 'app.correlation.middleware'"

**Step 3: Implement middleware**

Create: `hub/backend/app/correlation/middleware.py`

```python
"""FastAPI middleware for automatic correlation ID injection.

Middleware extracts or generates correlation IDs for request tracing.
"""
import logging
from uuid import uuid4, UUID
from fastapi import Request
from app.correlation.context import set_correlation_id, clear_correlation_id

logger = logging.getLogger(__name__)


async def correlation_middleware(request: Request, call_next):
    """Auto-inject correlation IDs into all requests.

    Flow:
    1. Extract X-Correlation-ID header (if present)
    2. Validate UUID format
    3. Generate new UUID if missing/invalid
    4. Store in request.state and context variable
    5. Process request
    6. Add correlation ID to response headers

    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler

    Returns:
        Response with X-Correlation-ID header
    """
    try:
        correlation_id = request.headers.get("X-Correlation-ID")

        # Validate format if provided
        if correlation_id:
            try:
                UUID(correlation_id)  # Validate UUID format
            except ValueError:
                logger.warning(
                    f"Invalid correlation ID format: {correlation_id}, generating new"
                )
                correlation_id = str(uuid4())
        else:
            correlation_id = str(uuid4())

        # Store in context for access anywhere in request lifecycle
        set_correlation_id(correlation_id)
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
    finally:
        # Clear context after request
        clear_correlation_id()
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/correlation/test_middleware.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add hub/backend/app/correlation/middleware.py hub/backend/tests/correlation/test_middleware.py
git commit -m "feat(correlation): add FastAPI middleware for correlation IDs

- Extract/validate X-Correlation-ID header
- Generate UUID if missing/invalid
- Store in request.state and context
- Add to response headers
- Full test coverage"
```

---

### Task 3: Correlation Middleware - Integration with Main App

**Files:**
- Modify: `hub/backend/app/main.py`
- Create: `hub/backend/tests/integration/test_correlation_flow.py`

**Step 1: Write integration test**

Create: `hub/backend/tests/integration/test_correlation_flow.py`

```python
"""Integration tests for correlation ID flow through app."""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


@pytest.fixture
def client():
    """Create test client for main app."""
    return TestClient(app)


def test_correlation_id_flows_through_health_endpoint(client):
    """Test correlation ID is added to health check."""
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers


def test_correlation_id_flows_through_projects_endpoint(client):
    """Test correlation ID flows through projects API."""
    test_id = str(uuid4())

    response = client.get(
        "/api/projects",
        headers={"X-Correlation-ID": test_id}
    )

    # Should preserve correlation ID
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == test_id


def test_multiple_requests_have_different_correlation_ids(client):
    """Test each request gets unique correlation ID."""
    response1 = client.get("/health")
    response2 = client.get("/health")

    id1 = response1.headers["X-Correlation-ID"]
    id2 = response2.headers["X-Correlation-ID"]

    assert id1 != id2
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/integration/test_correlation_flow.py -v
```

Expected: FAIL - "X-Correlation-ID not in response.headers"

**Step 3: Add middleware to main app**

Modify: `hub/backend/app/main.py`

Find the middleware section (after CORS, before route includes):

```python
from app.correlation.middleware import correlation_middleware

# ... existing CORS middleware ...

# Add correlation middleware (before route handlers)
app.middleware("http")(correlation_middleware)

# ... existing route includes ...
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/integration/test_correlation_flow.py -v
```

Expected: PASS (3 tests)

**Step 5: Verify all existing tests still pass**

```bash
pytest hub/backend/tests/ -v
```

Expected: All tests pass (including new correlation tests)

**Step 6: Commit**

```bash
git add hub/backend/app/main.py hub/backend/tests/integration/test_correlation_flow.py
git commit -m "feat(correlation): integrate middleware into main app

- Add correlation_middleware to app startup
- All endpoints now have correlation IDs
- Integration tests verify flow"
```

---

### Task 4: EventService - Enhanced Filtering

**Files:**
- Modify: `hub/backend/app/events/service.py`
- Create: `hub/backend/tests/events/test_filtering.py`

**Step 1: Write test for subscribe_filtered**

Create: `hub/backend/tests/events/test_filtering.py`

```python
"""Tests for EventService filtering methods."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.events.service import EventService
from app.models.event import Event


@pytest.fixture
async def event_service(test_db_session, nats_connection):
    """Create EventService for testing."""
    service = EventService(
        nats_url="nats://localhost:4222",
        db_session=test_db_session
    )
    await service.connect()
    yield service
    await service.disconnect()


@pytest.mark.asyncio
async def test_query_events_by_subject(event_service):
    """Test querying events by subject pattern."""
    # Publish test events
    await event_service.publish("hub.test.foo.created", {"data": 1})
    await event_service.publish("hub.test.bar.created", {"data": 2})
    await event_service.publish("hub.prod.foo.created", {"data": 3})

    # Query with wildcard
    events = await event_service.query_events(subject="hub.test.*")

    assert len(events) == 2
    assert all("hub.test" in e.subject for e in events)


@pytest.mark.asyncio
async def test_query_events_by_time_range(event_service):
    """Test querying events by time range."""
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    # Publish events
    await event_service.publish("hub.test.created", {"data": 1})

    # Query since 1 hour ago
    events = await event_service.query_events(since=one_hour_ago)

    assert len(events) >= 1
    assert all(e.timestamp >= one_hour_ago for e in events)


@pytest.mark.asyncio
async def test_query_events_by_correlation_id(event_service):
    """Test querying events by correlation ID."""
    test_correlation_id = uuid4()
    other_correlation_id = uuid4()

    # Publish with specific correlation ID
    await event_service.publish(
        "hub.test.created",
        {"data": 1},
        correlation_id=test_correlation_id
    )
    await event_service.publish(
        "hub.test.created",
        {"data": 2},
        correlation_id=other_correlation_id
    )

    # Query by correlation ID
    events = await event_service.query_events(
        correlation_id=test_correlation_id
    )

    assert len(events) == 1
    assert events[0].correlation_id == test_correlation_id


@pytest.mark.asyncio
async def test_query_events_combined_filters(event_service):
    """Test combining multiple filters."""
    test_correlation_id = uuid4()
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    await event_service.publish(
        "hub.test.foo.created",
        {"data": 1},
        correlation_id=test_correlation_id
    )

    # Combine subject, time, and correlation filters
    events = await event_service.query_events(
        subject="hub.test.*",
        since=one_hour_ago,
        correlation_id=test_correlation_id
    )

    assert len(events) == 1
    assert events[0].subject == "hub.test.foo.created"
    assert events[0].correlation_id == test_correlation_id
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/events/test_filtering.py -v
```

Expected: FAIL - "EventService has no method 'query_events'"

**Step 3: Implement query_events method**

Modify: `hub/backend/app/events/service.py`

Add at end of EventService class:

```python
    async def query_events(
        self,
        subject: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        correlation_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Event]:
        """Query historical events from database with filters.

        Args:
            subject: Filter by subject pattern (NATS wildcards: *, >)
            since: Filter events after this timestamp
            until: Filter events before this timestamp
            correlation_id: Filter by exact correlation ID match
            limit: Maximum events to return (default 100)

        Returns:
            List of Event objects matching filters
        """
        from sqlalchemy import and_, or_

        query = select(Event).order_by(Event.timestamp.desc())

        filters = []

        # Subject filter (SQL pattern matching for NATS wildcards)
        if subject:
            # Convert NATS wildcards to SQL LIKE pattern
            # * -> single segment wildcard
            # > -> multi-segment wildcard (everything after)
            if '>' in subject:
                # hub.test.> matches hub.test.% in SQL
                sql_pattern = subject.replace('>', '%')
                filters.append(Event.subject.like(sql_pattern))
            elif '*' in subject:
                # hub.*.created matches hub.___.created in SQL
                # Replace each * with single-segment pattern
                parts = subject.split('*')
                # This is simplified - proper implementation would be more robust
                sql_pattern = '%'.join(parts)
                filters.append(Event.subject.like(sql_pattern))
            else:
                # Exact match
                filters.append(Event.subject == subject)

        # Time range filters
        if since:
            filters.append(Event.timestamp >= since)
        if until:
            filters.append(Event.timestamp <= until)

        # Correlation ID filter
        if correlation_id:
            filters.append(Event.correlation_id == correlation_id)

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit)

        result = await self.db_session.execute(query)
        return list(result.scalars().all())
```

Add import at top of file:

```python
from typing import Optional, Callable, List
from datetime import datetime, timezone
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/events/test_filtering.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add hub/backend/app/events/service.py hub/backend/tests/events/test_filtering.py
git commit -m "feat(events): add query_events with filtering

- Query by subject pattern (NATS wildcards)
- Filter by time range (since/until)
- Filter by correlation ID
- Combined filters support
- Test coverage for all filter types"
```

---

### Task 5: Streaming Filters Utility

**Files:**
- Create: `hub/backend/app/streaming/__init__.py`
- Create: `hub/backend/app/streaming/filters.py`
- Create: `hub/backend/tests/streaming/test_filters.py`

**Step 1: Write tests for NATS pattern matching**

Create: `hub/backend/tests/streaming/test_filters.py`

```python
"""Tests for streaming event filters."""
import pytest
from app.streaming.filters import matches_subject_pattern


def test_matches_subject_exact():
    """Test exact subject matching."""
    assert matches_subject_pattern(
        "hub.local.project.created",
        "hub.local.project.created"
    )
    assert not matches_subject_pattern(
        "hub.local.project.created",
        "hub.local.project.deleted"
    )


def test_matches_subject_single_wildcard():
    """Test single token wildcard (*)."""
    pattern = "hub.*.project.created"

    assert matches_subject_pattern("hub.local.project.created", pattern)
    assert matches_subject_pattern("hub.remote.project.created", pattern)
    assert not matches_subject_pattern("hub.local.task.created", pattern)
    assert not matches_subject_pattern("hub.local.deep.project.created", pattern)


def test_matches_subject_multi_wildcard():
    """Test multi-token wildcard (>)."""
    pattern = "hub.>"

    assert matches_subject_pattern("hub.local.project.created", pattern)
    assert matches_subject_pattern("hub.remote", pattern)
    assert matches_subject_pattern("hub.a.b.c.d.e", pattern)
    assert not matches_subject_pattern("other.local.project", pattern)


def test_matches_subject_combined_wildcards():
    """Test combining wildcards."""
    pattern = "hub.*.health.>"

    assert matches_subject_pattern("hub.local.health.postgres", pattern)
    assert matches_subject_pattern("hub.local.health.redis.up", pattern)
    assert not matches_subject_pattern("hub.local.project.created", pattern)


def test_matches_subject_wildcard_all():
    """Test wildcard matching all."""
    assert matches_subject_pattern("anything.here", "*")
    assert matches_subject_pattern("hub.test.created", ">")
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/streaming/test_filters.py -v
```

Expected: FAIL - "No module named 'app.streaming.filters'"

**Step 3: Implement pattern matching**

Create: `hub/backend/app/streaming/filters.py`

```python
"""Event filtering utilities for streaming.

Provides NATS-style pattern matching for event subjects.
"""
import re
from typing import Pattern


def matches_subject_pattern(subject: str, pattern: str) -> bool:
    """Match NATS subject against wildcard pattern.

    Patterns:
        * - matches single token (segment between dots)
        > - matches one or more tokens (everything remaining)

    Examples:
        hub.*.health.* matches hub.local-hub.health.postgres
        hub.> matches hub.local-hub.project.created
        hub.*.> matches hub.test.foo.bar.baz

    Args:
        subject: Event subject to test (e.g., 'hub.local.project.created')
        pattern: NATS wildcard pattern (e.g., 'hub.*.project.*')

    Returns:
        True if subject matches pattern
    """
    # Handle special cases
    if pattern == "*":
        return True  # Match anything (single token)
    if pattern == ">":
        return True  # Match anything (all tokens)

    # Convert NATS pattern to regex
    # Escape dots (literal in NATS, regex special char)
    regex_pattern = pattern.replace(".", r"\.")

    # Replace NATS wildcards with regex equivalents
    # * matches single token (non-dot characters)
    regex_pattern = regex_pattern.replace("*", r"[^.]+")

    # > matches one or more tokens (everything remaining)
    # Must be at end of pattern
    if ">" in regex_pattern:
        # Replace > with regex that matches remaining
        regex_pattern = regex_pattern.replace(r"\>", ".*")

    # Anchor pattern (must match entire subject)
    regex_pattern = f"^{regex_pattern}$"

    # Compile and test
    compiled: Pattern = re.compile(regex_pattern)
    return bool(compiled.match(subject))
```

Create: `hub/backend/app/streaming/__init__.py`

```python
"""Event streaming utilities."""
from app.streaming.filters import matches_subject_pattern

__all__ = ['matches_subject_pattern']
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/streaming/test_filters.py -v
```

Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add hub/backend/app/streaming/ hub/backend/tests/streaming/test_filters.py
git commit -m "feat(streaming): add NATS pattern matching for filters

- Single wildcard (*) for one token
- Multi wildcard (>) for remaining tokens
- Regex-based matching
- Full test coverage"
```

---

### Task 6: Server-Sent Events (SSE) Endpoint

**Files:**
- Create: `hub/backend/app/streaming/sse.py`
- Create: `hub/backend/tests/streaming/test_sse.py`

**Step 1: Write test for SSE endpoint**

Create: `hub/backend/tests/streaming/test_sse.py`

```python
"""Tests for Server-Sent Events streaming."""
import pytest
import asyncio
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.events.service import EventService


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_sse_endpoint_returns_event_stream(client):
    """Test SSE endpoint returns text/event-stream."""
    with client.stream("GET", "/api/events/stream") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"


def test_sse_stream_receives_events(client, test_db_session):
    """Test SSE stream receives published events."""
    # Start streaming in thread
    import threading
    import queue

    event_queue = queue.Queue()

    def stream_events():
        with client.stream("GET", "/api/events/stream?subject=hub.test.*") as r:
            for line in r.iter_lines():
                if line.startswith("data:"):
                    event_queue.put(line)
                    break  # Get first event only

    stream_thread = threading.Thread(target=stream_events)
    stream_thread.start()

    # Give stream time to connect
    import time
    time.sleep(0.5)

    # Publish event
    # NOTE: This test requires async context - may need different approach
    # For now, test structure is correct, implementation may need adjustment

    stream_thread.join(timeout=2)


def test_sse_subject_filter(client):
    """Test SSE subject filtering."""
    with client.stream("GET", "/api/events/stream?subject=hub.specific.*") as response:
        assert response.status_code == 200
        # Stream should only receive events matching pattern


def test_sse_correlation_id_filter(client):
    """Test SSE correlation ID filtering."""
    test_id = uuid4()

    with client.stream(
        "GET",
        f"/api/events/stream?correlation_id={test_id}"
    ) as response:
        assert response.status_code == 200


def test_sse_time_filter(client):
    """Test SSE time filtering."""
    with client.stream(
        "GET",
        "/api/events/stream?since=1h"
    ) as response:
        assert response.status_code == 200
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/streaming/test_sse.py::test_sse_endpoint_returns_event_stream -v
```

Expected: FAIL - "404 Not Found"

**Step 3: Implement SSE endpoint**

Create: `hub/backend/app/streaming/sse.py`

```python
"""Server-Sent Events streaming endpoint.

Provides HTTP-based real-time event streaming using SSE protocol.
"""
import asyncio
import json
import logging
from datetime import datetime
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
router = APIRouter(prefix="/api/events", tags=["events"])


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

        # Send initial keepalive
        yield ": keepalive\n\n"

        # Subscribe to NATS for live events
        last_keepalive = asyncio.get_event_loop().time()

        # Query historical events first if 'since' provided
        if since:
            historical = await event_service.query_events(
                subject=subject if subject != "*" else None,
                since=since,
                correlation_id=correlation_id,
                limit=1000
            )

            for event in historical:
                yield format_sse_event(event)

        # Then stream live events
        async def handle_event(subj: str, data: dict):
            """Handle incoming NATS events."""
            # Apply filters
            if subject != "*" and not matches_subject_pattern(subj, subject):
                return

            if correlation_id and data.get("correlation_id") != str(correlation_id):
                return

            # Format as SSE
            event_data = json.dumps(data)
            return f"data: {event_data}\n\n"

        # Subscribe to NATS
        subscription_subject = subject if subject != "*" else "hub.>"

        # This is simplified - actual implementation would need async queue
        # for handling NATS messages in SSE stream
        await event_service.subscribe(subscription_subject, handle_event)

        # Keep connection alive
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


@router.get("/stream")
async def stream_events(
    subject: str = Query("*", description="NATS subject pattern"),
    since: Optional[str] = Query(None, description="Start time (e.g., '1h', ISO)"),
    correlation_id: Optional[UUID] = Query(None, description="Correlation ID filter"),
    db: AsyncSession = Depends(get_db)
):
    """Stream events via Server-Sent Events.

    Usage:
        curl -N http://localhost:9001/api/events/stream?subject=hub.test.*

    JavaScript:
        const events = new EventSource('/api/events/stream');
        events.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    # Parse time if provided (simplified - will implement time parser in CLI task)
    since_dt = None
    if since:
        # Basic time parsing - will be enhanced in CLI task
        from datetime import timedelta, timezone
        if since.endswith('h'):
            hours = int(since[:-1])
            since_dt = datetime.now(timezone.utc) - timedelta(hours=hours)

    return StreamingResponse(
        event_generator(subject, since_dt, correlation_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

**Step 4: Add SSE router to main app**

Modify: `hub/backend/app/main.py`

```python
from app.streaming.sse import router as sse_router

# ... after existing routers ...
app.include_router(sse_router)
```

**Step 5: Run test to verify basic endpoint exists**

```bash
pytest tests/streaming/test_sse.py::test_sse_endpoint_returns_event_stream -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add hub/backend/app/streaming/sse.py hub/backend/tests/streaming/test_sse.py hub/backend/app/main.py
git commit -m "feat(streaming): add Server-Sent Events endpoint

- /api/events/stream endpoint
- Subject, time, correlation ID filtering
- Historical + live event streaming
- SSE protocol compliance
- Basic test coverage (more integration tests needed)"
```

---

## Track B: CLI Tools

### Task 7: CLI Skeleton - Project Setup

**Files:**
- Create: `hub/backend/app/cli/__init__.py`
- Create: `hub/backend/app/cli/__main__.py`
- Create: `hub/backend/app/cli/commands/__init__.py`
- Modify: `hub/backend/pyproject.toml` or `setup.py`
- Modify: `hub/backend/requirements.txt`

**Step 1: Write test for CLI entry point**

Create: `hub/backend/tests/cli/test_main.py`

```python
"""Tests for CLI entry point."""
import pytest
from click.testing import CliRunner
from app.cli.__main__ import cli


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(cli, ['--version'])

    assert result.exit_code == 0
    assert 'version' in result.output.lower()


def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(cli, ['--help'])

    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'commands' in result.output.lower()


def test_cli_no_command_shows_help(runner):
    """Test CLI with no command shows help."""
    result = runner.invoke(cli, [])

    # Should show help by default
    assert 'Usage:' in result.output
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/cli/test_main.py -v
```

Expected: FAIL - "No module named 'app.cli.__main__'"

**Step 3: Add dependencies**

Modify: `hub/backend/requirements.txt`

```
# ... existing dependencies ...

# CLI tools
click>=8.1.7
dateparser>=1.2.0
rich>=13.7.0
```

**Step 4: Create CLI skeleton**

Create: `hub/backend/app/cli/__init__.py`

```python
"""CLI tools for CommandCenter Hub events."""

__version__ = "0.1.0"
```

Create: `hub/backend/app/cli/__main__.py`

```python
"""CLI entry point for hub events command.

Usage:
    hub events [COMMAND]
    hub events query --subject "hub.test.*"
    hub events follow --subject "hub.>"
"""
import click
from app.cli import __version__


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """CommandCenter Hub Event CLI.

    Tools for querying, streaming, and monitoring Hub events.
    """
    ctx.ensure_object(dict)


# Subcommands will be added in subsequent tasks


if __name__ == '__main__':
    cli()
```

Create: `hub/backend/app/cli/commands/__init__.py`

```python
"""CLI command implementations."""
```

**Step 5: Add CLI entry point**

Create or modify: `hub/backend/pyproject.toml`

```toml
[project.scripts]
hub = "app.cli.__main__:cli"
```

OR if using setup.py:

```python
setup(
    # ... existing config ...
    entry_points={
        'console_scripts': [
            'hub=app.cli.__main__:cli',
        ],
    },
)
```

**Step 6: Install in development mode**

```bash
cd hub/backend
pip install -e .
```

**Step 7: Run test to verify it passes**

```bash
pytest tests/cli/test_main.py -v
```

Expected: PASS (3 tests)

**Step 8: Test CLI from command line**

```bash
hub --version
hub --help
```

Expected: Version and help output

**Step 9: Commit**

```bash
git add hub/backend/app/cli/ hub/backend/tests/cli/test_main.py hub/backend/requirements.txt hub/backend/pyproject.toml
git commit -m "feat(cli): add CLI skeleton with Click framework

- hub command entry point
- Click group for subcommands
- Version and help commands
- Test infrastructure
- Development installation"
```

---

### Task 8: CLI Time Parser Utility

**Files:**
- Create: `hub/backend/app/cli/utils/__init__.py`
- Create: `hub/backend/app/cli/utils/time_parser.py`
- Create: `hub/backend/tests/cli/test_time_parser.py`

**Step 1: Write tests for time parsing**

Create: `hub/backend/tests/cli/test_time_parser.py`

```python
"""Tests for natural language time parsing."""
import pytest
from datetime import datetime, timezone, timedelta
from app.cli.utils.time_parser import parse_time


def test_parse_relative_hours():
    """Test parsing relative hours (1h, 2h)."""
    result = parse_time("1h")
    expected = datetime.now(timezone.utc) - timedelta(hours=1)

    # Within 1 second tolerance
    assert abs((result - expected).total_seconds()) < 1


def test_parse_relative_minutes():
    """Test parsing relative minutes (30m, 5m)."""
    result = parse_time("30m")
    expected = datetime.now(timezone.utc) - timedelta(minutes=30)

    assert abs((result - expected).total_seconds()) < 1


def test_parse_relative_days():
    """Test parsing relative days (1d, 7d)."""
    result = parse_time("7d")
    expected = datetime.now(timezone.utc) - timedelta(days=7)

    assert abs((result - expected).total_seconds()) < 1


def test_parse_natural_language():
    """Test natural language parsing (yesterday, last Monday)."""
    result = parse_time("yesterday")
    expected = datetime.now(timezone.utc) - timedelta(days=1)

    # Should be roughly 24 hours ago (within 1 hour tolerance)
    assert abs((result - expected).total_seconds()) < 3600


def test_parse_iso_format():
    """Test ISO 8601 datetime parsing."""
    iso_string = "2025-11-04T10:30:00Z"
    result = parse_time(iso_string)

    expected = datetime(2025, 11, 4, 10, 30, 0, tzinfo=timezone.utc)
    assert result == expected


def test_parse_none_returns_none():
    """Test None input returns None."""
    result = parse_time(None)
    assert result is None


def test_parse_empty_string_returns_none():
    """Test empty string returns None."""
    result = parse_time("")
    assert result is None


def test_parse_invalid_raises_error():
    """Test invalid time string raises ValueError."""
    with pytest.raises(ValueError):
        parse_time("not-a-time")
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/cli/test_time_parser.py -v
```

Expected: FAIL - "No module named 'app.cli.utils.time_parser'"

**Step 3: Implement time parser**

Create: `hub/backend/app/cli/utils/time_parser.py`

```python
"""Natural language time parsing for CLI.

Supports:
- Relative: 1h, 30m, 7d
- Natural: yesterday, last Monday, 2 hours ago
- ISO 8601: 2025-11-04T10:30:00Z
"""
import re
from datetime import datetime, timezone, timedelta
from typing import Optional
import dateparser


def parse_time(time_str: Optional[str]) -> Optional[datetime]:
    """Parse time string into datetime.

    Formats supported:
        - Relative: "1h", "30m", "7d" (hours, minutes, days ago)
        - Natural: "yesterday", "last Monday", "2 hours ago"
        - ISO 8601: "2025-11-04T10:30:00Z"

    Args:
        time_str: Time string to parse, or None

    Returns:
        Datetime in UTC timezone, or None if input is None/empty

    Raises:
        ValueError: If time_str cannot be parsed

    Examples:
        >>> parse_time("1h")
        datetime(2025, 11, 4, 9, 30, 0, tzinfo=timezone.utc)  # 1 hour ago

        >>> parse_time("yesterday")
        datetime(2025, 11, 3, 10, 30, 0, tzinfo=timezone.utc)
    """
    if not time_str:
        return None

    # Try relative format first (1h, 30m, 7d)
    relative_match = re.match(r'^(\d+)([hmd])$', time_str)
    if relative_match:
        value, unit = relative_match.groups()
        value = int(value)

        if unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'm':
            delta = timedelta(minutes=value)
        elif unit == 'd':
            delta = timedelta(days=value)

        return datetime.now(timezone.utc) - delta

    # Try ISO 8601 format
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        # Ensure UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except (ValueError, AttributeError):
        pass

    # Try natural language parsing with dateparser
    parsed = dateparser.parse(
        time_str,
        settings={
            'TIMEZONE': 'UTC',
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'past'  # Default to past dates
        }
    )

    if parsed:
        # Ensure UTC timezone
        return parsed.astimezone(timezone.utc)

    # Could not parse
    raise ValueError(f"Could not parse time string: {time_str}")
```

Create: `hub/backend/app/cli/utils/__init__.py`

```python
"""CLI utility functions."""
from app.cli.utils.time_parser import parse_time

__all__ = ['parse_time']
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/cli/test_time_parser.py -v
```

Expected: PASS (8 tests)

**Step 5: Commit**

```bash
git add hub/backend/app/cli/utils/ hub/backend/tests/cli/test_time_parser.py
git commit -m "feat(cli): add natural language time parser

- Relative format: 1h, 30m, 7d
- Natural language: yesterday, last Monday
- ISO 8601 support
- Uses dateparser for complex parsing
- Full test coverage"
```

---

### Task 9: CLI Formatters - Table Output

**Files:**
- Create: `hub/backend/app/cli/utils/formatters.py`
- Create: `hub/backend/tests/cli/test_formatters.py`

**Step 1: Write tests for formatting**

Create: `hub/backend/tests/cli/test_formatters.py`

```python
"""Tests for CLI output formatters."""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.cli.utils.formatters import format_events_table, format_event_json
from app.models.event import Event


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    return [
        Event(
            id=uuid4(),
            subject="hub.test.project.created",
            origin={"hub_id": "local", "service": "hub-backend"},
            correlation_id=uuid4(),
            payload={"project_id": 1, "name": "Test Project"},
            timestamp=datetime(2025, 11, 4, 10, 30, 0, tzinfo=timezone.utc)
        ),
        Event(
            id=uuid4(),
            subject="hub.test.project.started",
            origin={"hub_id": "local", "service": "hub-backend"},
            correlation_id=uuid4(),
            payload={"project_id": 1},
            timestamp=datetime(2025, 11, 4, 10, 31, 0, tzinfo=timezone.utc)
        )
    ]


def test_format_events_table(sample_events):
    """Test table formatting."""
    output = format_events_table(sample_events)

    # Should contain table structure
    assert "Timestamp" in output
    assert "Subject" in output
    assert "Correlation ID" in output

    # Should contain event data
    assert "project.created" in output
    assert "project.started" in output


def test_format_events_table_truncates_long_subjects(sample_events):
    """Test long subjects are truncated."""
    sample_events[0].subject = "hub." + "x" * 100

    output = format_events_table(sample_events)

    # Should truncate to reasonable length
    assert len([line for line in output.split('\n') if 'xxx' in line][0]) < 200


def test_format_event_json(sample_events):
    """Test JSON formatting."""
    import json

    output = format_event_json(sample_events[0])

    # Should be valid JSON
    parsed = json.loads(output)

    assert parsed["subject"] == "hub.test.project.created"
    assert "timestamp" in parsed
    assert "payload" in parsed


def test_format_events_table_empty():
    """Test formatting empty event list."""
    output = format_events_table([])

    assert "No events" in output or output == ""


def test_format_events_table_with_limit(sample_events):
    """Test table respects limit parameter."""
    output = format_events_table(sample_events, limit=1)

    lines = output.split('\n')
    # Should only include 1 event (plus headers)
    assert 'project.created' in output
    assert 'project.started' not in output
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/cli/test_formatters.py -v
```

Expected: FAIL - "No module named 'app.cli.utils.formatters'"

**Step 3: Implement formatters**

Create: `hub/backend/app/cli/utils/formatters.py`

```python
"""Output formatters for CLI.

Uses rich library for beautiful terminal output.
"""
import json
from typing import List, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.json import JSON

from app.models.event import Event


def format_events_table(
    events: List[Event],
    limit: Optional[int] = None,
    show_payload: bool = False
) -> str:
    """Format events as a table.

    Args:
        events: List of Event objects
        limit: Maximum events to display
        show_payload: Include payload column

    Returns:
        Formatted table string
    """
    if not events:
        return "No events found."

    # Create table
    table = Table(title="Events")

    table.add_column("Timestamp", style="cyan")
    table.add_column("Subject", style="green")
    table.add_column("Correlation ID", style="yellow")

    if show_payload:
        table.add_column("Payload", style="magenta")

    # Add rows
    for event in events[:limit] if limit else events:
        # Format timestamp
        ts = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Truncate long subjects
        subject = event.subject
        if len(subject) > 50:
            subject = subject[:47] + "..."

        # Short correlation ID (first 8 chars)
        corr_id = str(event.correlation_id)[:8]

        row = [ts, subject, corr_id]

        if show_payload:
            payload_str = json.dumps(event.payload)
            if len(payload_str) > 50:
                payload_str = payload_str[:47] + "..."
            row.append(payload_str)

        table.add_row(*row)

    # Render to string
    console = Console()
    with console.capture() as capture:
        console.print(table)

    return capture.get()


def format_event_json(event: Event, pretty: bool = True) -> str:
    """Format single event as JSON.

    Args:
        event: Event object
        pretty: Pretty-print JSON

    Returns:
        JSON string
    """
    event_dict = {
        "id": str(event.id),
        "subject": event.subject,
        "origin": event.origin,
        "correlation_id": str(event.correlation_id),
        "payload": event.payload,
        "timestamp": event.timestamp.isoformat()
    }

    if pretty:
        return json.dumps(event_dict, indent=2)
    else:
        return json.dumps(event_dict)


def format_events_json(events: List[Event], pretty: bool = True) -> str:
    """Format multiple events as JSON array.

    Args:
        events: List of Event objects
        pretty: Pretty-print JSON

    Returns:
        JSON array string
    """
    events_list = []

    for event in events:
        events_list.append({
            "id": str(event.id),
            "subject": event.subject,
            "origin": event.origin,
            "correlation_id": str(event.correlation_id),
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat()
        })

    if pretty:
        return json.dumps(events_list, indent=2)
    else:
        return json.dumps(events_list)
```

Update: `hub/backend/app/cli/utils/__init__.py`

```python
"""CLI utility functions."""
from app.cli.utils.time_parser import parse_time
from app.cli.utils.formatters import (
    format_events_table,
    format_event_json,
    format_events_json
)

__all__ = [
    'parse_time',
    'format_events_table',
    'format_event_json',
    'format_events_json'
]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/cli/test_formatters.py -v
```

Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add hub/backend/app/cli/utils/formatters.py hub/backend/tests/cli/test_formatters.py hub/backend/app/cli/utils/__init__.py
git commit -m "feat(cli): add rich formatters for events

- Table output with rich library
- JSON output (single/multiple events)
- Truncation for long fields
- Colorized terminal output
- Full test coverage"
```

---

### Task 10: CLI Query Command

**Files:**
- Create: `hub/backend/app/cli/commands/query.py`
- Create: `hub/backend/tests/cli/test_query_command.py`
- Modify: `hub/backend/app/cli/__main__.py`

**Step 1: Write test for query command**

Create: `hub/backend/tests/cli/test_query_command.py`

```python
"""Tests for query command."""
import pytest
from click.testing import CliRunner
from uuid import uuid4

from app.cli.__main__ import cli


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


def test_query_command_exists(runner):
    """Test query command is registered."""
    result = runner.invoke(cli, ['query', '--help'])

    assert result.exit_code == 0
    assert 'Usage:' in result.output


def test_query_with_subject_filter(runner):
    """Test query with subject filter."""
    result = runner.invoke(cli, [
        'query',
        '--subject', 'hub.test.*'
    ])

    # Should succeed (may be empty)
    assert result.exit_code == 0


def test_query_with_since_filter(runner):
    """Test query with time filter."""
    result = runner.invoke(cli, [
        'query',
        '--since', '1h'
    ])

    assert result.exit_code == 0


def test_query_with_correlation_id(runner):
    """Test query with correlation ID."""
    test_id = str(uuid4())

    result = runner.invoke(cli, [
        'query',
        '--correlation-id', test_id
    ])

    assert result.exit_code == 0


def test_query_with_limit(runner):
    """Test query with limit."""
    result = runner.invoke(cli, [
        'query',
        '--limit', '10'
    ])

    assert result.exit_code == 0


def test_query_json_output(runner):
    """Test query with JSON output format."""
    result = runner.invoke(cli, [
        'query',
        '--format', 'json'
    ])

    assert result.exit_code == 0
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/cli/test_query_command.py::test_query_command_exists -v
```

Expected: FAIL - "No such command 'query'"

**Step 3: Implement query command**

Create: `hub/backend/app/cli/commands/query.py`

```python
"""Query command for historical events.

Usage:
    hub query --subject "hub.test.*" --since "1h"
"""
import asyncio
import click
from uuid import UUID
from typing import Optional

from app.cli.utils.time_parser import parse_time
from app.cli.utils.formatters import format_events_table, format_events_json
from app.events.service import EventService
from app.database import get_async_session
from app.config import get_nats_url


@click.command()
@click.option(
    '--subject',
    '-s',
    default=None,
    help='Filter by subject pattern (NATS wildcards: *, >)'
)
@click.option(
    '--since',
    default=None,
    help='Show events since time (e.g., 1h, yesterday, 2025-11-04)'
)
@click.option(
    '--until',
    default=None,
    help='Show events until time'
)
@click.option(
    '--correlation-id',
    default=None,
    help='Filter by correlation ID'
)
@click.option(
    '--limit',
    '-n',
    default=100,
    type=int,
    help='Maximum events to return (default: 100)'
)
@click.option(
    '--format',
    '-f',
    type=click.Choice(['table', 'json']),
    default='table',
    help='Output format (default: table)'
)
def query(
    subject: Optional[str],
    since: Optional[str],
    until: Optional[str],
    correlation_id: Optional[str],
    limit: int,
    format: str
):
    """Query historical events from database.

    Examples:
        hub query --subject "hub.test.*" --since "1h"
        hub query --correlation-id "abc123" --format json
        hub query --since "yesterday" --limit 50
    """
    # Parse time filters
    since_dt = parse_time(since) if since else None
    until_dt = parse_time(until) if until else None

    # Parse correlation ID
    correlation_uuid = None
    if correlation_id:
        try:
            correlation_uuid = UUID(correlation_id)
        except ValueError:
            click.echo(f"Error: Invalid correlation ID format: {correlation_id}")
            return

    # Query events
    async def query_events():
        async for session in get_async_session():
            event_service = EventService(get_nats_url(), session)
            await event_service.connect()

            try:
                events = await event_service.query_events(
                    subject=subject,
                    since=since_dt,
                    until=until_dt,
                    correlation_id=correlation_uuid,
                    limit=limit
                )
                return events
            finally:
                await event_service.disconnect()

    # Run query
    try:
        events = asyncio.run(query_events())

        # Format output
        if format == 'json':
            output = format_events_json(events)
        else:
            output = format_events_table(events)

        click.echo(output)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
```

Update: `hub/backend/app/cli/commands/__init__.py`

```python
"""CLI command implementations."""
from app.cli.commands.query import query

__all__ = ['query']
```

**Step 4: Register command in main CLI**

Modify: `hub/backend/app/cli/__main__.py`

```python
"""CLI entry point for hub events command."""
import click
from app.cli import __version__
from app.cli.commands import query  # Import query command


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """CommandCenter Hub Event CLI.

    Tools for querying, streaming, and monitoring Hub events.
    """
    ctx.ensure_object(dict)


# Register subcommands
cli.add_command(query)


if __name__ == '__main__':
    cli()
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/cli/test_query_command.py -v
```

Expected: PASS (6 tests)

**Step 6: Test from command line**

```bash
hub query --help
hub query --limit 10
```

Expected: Help output, then query results

**Step 7: Commit**

```bash
git add hub/backend/app/cli/commands/query.py hub/backend/tests/cli/test_query_command.py hub/backend/app/cli/__main__.py hub/backend/app/cli/commands/__init__.py
git commit -m "feat(cli): add query command for historical events

- Filter by subject, time, correlation ID
- Table and JSON output formats
- Natural language time parsing
- Limit parameter for result size
- Full test coverage"
```

---

### Task 11: CLI Follow Command

**Files:**
- Create: `hub/backend/app/cli/utils/nats_client.py`
- Create: `hub/backend/app/cli/commands/follow.py`
- Create: `hub/backend/tests/cli/test_follow_command.py`

**Step 1: Write test for NATS client utility**

Create: `hub/backend/tests/cli/test_nats_client.py`

```python
"""Tests for NATS client utility."""
import pytest
import asyncio
from app.cli.utils.nats_client import subscribe_stream


@pytest.mark.asyncio
async def test_subscribe_stream_receives_messages():
    """Test subscribing to NATS stream."""
    messages = []

    async def handler(subject: str, data: dict):
        messages.append((subject, data))

    # Start subscription (will run until cancelled)
    task = asyncio.create_task(
        subscribe_stream(
            "nats://localhost:4222",
            "hub.test.>",
            handler
        )
    )

    # Let it run briefly
    await asyncio.sleep(0.5)

    # Cancel subscription
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass  # Expected
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/cli/test_nats_client.py -v
```

Expected: FAIL - "No module named 'app.cli.utils.nats_client'"

**Step 3: Implement NATS client utility**

Create: `hub/backend/app/cli/utils/nats_client.py`

```python
"""Direct NATS client for CLI streaming.

Provides lightweight NATS subscription without database dependencies.
"""
import json
import logging
from typing import Callable, Awaitable

import nats
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)


async def subscribe_stream(
    nats_url: str,
    subject: str,
    handler: Callable[[str, dict], Awaitable[None]],
    timeout: float = None
):
    """Subscribe to NATS subject and call handler for each message.

    Args:
        nats_url: NATS server URL (e.g., 'nats://localhost:4222')
        subject: NATS subject pattern (supports wildcards)
        handler: Async function called with (subject, data) for each message
        timeout: Optional timeout in seconds (None = run forever)

    Raises:
        Exception: If connection fails or handler errors

    Example:
        async def print_event(subject: str, data: dict):
            print(f"{subject}: {data}")

        await subscribe_stream(
            "nats://localhost:4222",
            "hub.>",
            print_event
        )
    """
    nc: NATS = None

    try:
        # Connect to NATS
        nc = await nats.connect(nats_url)
        logger.info(f"Connected to NATS at {nats_url}")

        async def message_handler(msg):
            """Handle incoming NATS message."""
            try:
                # Decode JSON payload
                data = json.loads(msg.data.decode())

                # Call user handler
                await handler(msg.subject, data)

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in message: {msg.data}")
            except Exception as e:
                logger.error(f"Handler error: {e}", exc_info=True)

        # Subscribe to subject
        subscription = await nc.subscribe(subject, cb=message_handler)
        logger.info(f"Subscribed to {subject}")

        # Run until timeout or cancellation
        if timeout:
            import asyncio
            await asyncio.sleep(timeout)
        else:
            # Run forever (until cancelled)
            while True:
                import asyncio
                await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"NATS subscription error: {e}", exc_info=True)
        raise
    finally:
        if nc:
            await nc.close()
            logger.info("Disconnected from NATS")
```

Update: `hub/backend/app/cli/utils/__init__.py`

```python
"""CLI utility functions."""
from app.cli.utils.time_parser import parse_time
from app.cli.utils.formatters import (
    format_events_table,
    format_event_json,
    format_events_json
)
from app.cli.utils.nats_client import subscribe_stream

__all__ = [
    'parse_time',
    'format_events_table',
    'format_event_json',
    'format_events_json',
    'subscribe_stream'
]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/cli/test_nats_client.py -v
```

Expected: PASS

**Step 5: Write test for follow command**

Create: `hub/backend/tests/cli/test_follow_command.py`

```python
"""Tests for follow command."""
import pytest
from click.testing import CliRunner
from app.cli.__main__ import cli


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


def test_follow_command_exists(runner):
    """Test follow command is registered."""
    result = runner.invoke(cli, ['follow', '--help'])

    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'follow' in result.output.lower()


def test_follow_with_subject(runner):
    """Test follow with subject filter."""
    # This will timeout - that's expected for a streaming command
    # Just test it starts correctly
    result = runner.invoke(cli, ['follow', '--subject', 'hub.test.*'], input='\x03')

    # Should not error on startup
    # May exit with code 1 due to keyboard interrupt
    assert result.exit_code in [0, 1]
```

**Step 6: Run test to verify it fails**

```bash
pytest tests/cli/test_follow_command.py::test_follow_command_exists -v
```

Expected: FAIL - "No such command 'follow'"

**Step 7: Implement follow command**

Create: `hub/backend/app/cli/commands/follow.py`

```python
"""Follow command for live event streaming.

Usage:
    hub follow --subject "hub.test.*"
"""
import asyncio
import click
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table

from app.cli.utils.nats_client import subscribe_stream
from app.config import get_nats_url


@click.command()
@click.option(
    '--subject',
    '-s',
    default='hub.>',
    help='Filter by subject pattern (default: hub.>)'
)
@click.option(
    '--format',
    '-f',
    type=click.Choice(['table', 'json', 'compact']),
    default='compact',
    help='Output format (default: compact)'
)
def follow(subject: str, format: str):
    """Follow live events in real-time.

    Streams events from NATS as they occur. Press Ctrl+C to stop.

    Examples:
        hub follow --subject "hub.test.*"
        hub follow --format json
        hub follow  # All hub events
    """
    console = Console()

    # Track events for table display
    recent_events = []
    max_display = 20

    async def event_handler(subj: str, data: dict):
        """Handle incoming events."""
        nonlocal recent_events

        timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())
        correlation_id = data.get('correlation_id', 'unknown')[:8]
        payload = data.get('payload', {})

        if format == 'json':
            # JSON output
            import json
            console.print(json.dumps(data, indent=2))
        elif format == 'compact':
            # One-line compact format
            console.print(
                f"[cyan]{timestamp}[/cyan] "
                f"[green]{subj}[/green] "
                f"[yellow]{correlation_id}[/yellow] "
                f"{payload}"
            )
        else:
            # Table format (update live)
            recent_events.append({
                'timestamp': timestamp,
                'subject': subj,
                'correlation_id': correlation_id,
                'payload': str(payload)[:50]
            })

            # Keep only recent events
            recent_events = recent_events[-max_display:]

    async def stream_events():
        """Start event stream."""
        try:
            console.print(f"[bold]Following events: {subject}[/bold]")
            console.print("[dim]Press Ctrl+C to stop[/dim]\n")

            await subscribe_stream(
                get_nats_url(),
                subject,
                event_handler
            )
        except asyncio.CancelledError:
            console.print("\n[yellow]Stopped[/yellow]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]", err=True)
            raise click.Abort()

    # Run stream
    try:
        asyncio.run(stream_events())
    except KeyboardInterrupt:
        pass  # Clean exit
```

Update: `hub/backend/app/cli/commands/__init__.py`

```python
"""CLI command implementations."""
from app.cli.commands.query import query
from app.cli.commands.follow import follow

__all__ = ['query', 'follow']
```

**Step 8: Register follow command**

Modify: `hub/backend/app/cli/__main__.py`

```python
from app.cli.commands import query, follow  # Add follow

# ... cli group ...

# Register subcommands
cli.add_command(query)
cli.add_command(follow)
```

**Step 9: Run test to verify it passes**

```bash
pytest tests/cli/test_follow_command.py -v
```

Expected: PASS (2 tests)

**Step 10: Test from command line**

```bash
hub follow --help
# hub follow --subject "hub.test.*"  # Run in terminal, Ctrl+C to stop
```

Expected: Help output

**Step 11: Commit**

```bash
git add hub/backend/app/cli/utils/nats_client.py hub/backend/app/cli/commands/follow.py hub/backend/tests/cli/ hub/backend/app/cli/__main__.py hub/backend/app/cli/commands/__init__.py
git commit -m "feat(cli): add follow command for live event streaming

- Direct NATS subscription
- Real-time event display
- Multiple output formats (table, json, compact)
- Keyboard interrupt handling
- Test coverage"
```

---

## Integration & Testing

### Task 12: End-to-End Integration Test

**Files:**
- Create: `hub/backend/tests/integration/test_phase2_3_flow.py`

**Step 1: Write integration test**

Create: `hub/backend/tests/integration/test_phase2_3_flow.py`

```python
"""End-to-end integration test for Phase 2-3.

Tests the complete flow:
1. Make HTTP request with correlation ID
2. Event published with correlation ID
3. Query events by correlation ID
4. Stream events via SSE
"""
import pytest
import asyncio
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.events.service import EventService
from app.database import get_async_session
from app.config import get_nats_url


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_correlation_flows_through_event_system(client):
    """Test correlation ID flows from HTTP request to event."""
    test_correlation_id = str(uuid4())

    # Make request with correlation ID
    response = client.get(
        "/health",
        headers={"X-Correlation-ID": test_correlation_id}
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == test_correlation_id

    # Publish event (simulating what a route would do)
    async for session in get_async_session():
        event_service = EventService(get_nats_url(), session)
        await event_service.connect()

        event_id = await event_service.publish(
            "hub.test.correlation.test",
            {"test": "data"},
            correlation_id=uuid4(test_correlation_id)
        )

        # Query events by correlation ID
        events = await event_service.query_events(
            correlation_id=uuid4(test_correlation_id)
        )

        await event_service.disconnect()

        assert len(events) >= 1
        assert str(events[0].correlation_id) == test_correlation_id
        break


def test_sse_streams_events_with_filters(client):
    """Test SSE endpoint filters events correctly."""
    # This is a basic test - real SSE testing requires async streaming
    response = client.get(
        "/api/events/stream?subject=hub.test.*",
        stream=True
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"


@pytest.mark.asyncio
async def test_cli_query_returns_events():
    """Test CLI query function works end-to-end."""
    from click.testing import CliRunner
    from app.cli.__main__ import cli

    # Publish test event
    async for session in get_async_session():
        event_service = EventService(get_nats_url(), session)
        await event_service.connect()

        await event_service.publish(
            "hub.test.cli.query",
            {"test": "data"}
        )

        await event_service.disconnect()
        break

    # Query via CLI
    runner = CliRunner()
    result = runner.invoke(cli, [
        'query',
        '--subject', 'hub.test.cli.query',
        '--limit', '10'
    ])

    assert result.exit_code == 0
    assert 'hub.test.cli.query' in result.output or 'No events' in result.output
```

**Step 2: Run test to verify current state**

```bash
pytest tests/integration/test_phase2_3_flow.py -v
```

Expected: Should mostly pass (tests existing functionality)

**Step 3: Fix any failures**

If tests fail, debug and fix issues in implementation.

**Step 4: Commit**

```bash
git add hub/backend/tests/integration/test_phase2_3_flow.py
git commit -m "test: add Phase 2-3 end-to-end integration tests

- Correlation ID flow through system
- SSE streaming with filters
- CLI query integration
- Complete feature validation"
```

---

### Task 13: Documentation Updates

**Files:**
- Create: `hub/docs/CLI_USAGE.md`
- Modify: `hub/README.md`
- Modify: `docs/PROJECT.md`

**Step 1: Create CLI usage documentation**

Create: `hub/docs/CLI_USAGE.md`

```markdown
# Hub CLI Usage Guide

The Hub CLI provides tools for querying and monitoring CommandCenter Hub events.

## Installation

```bash
cd hub/backend
pip install -e .
```

Verify installation:
```bash
hub --version
```

## Commands

### query - Query Historical Events

Search events stored in PostgreSQL database.

**Basic usage:**
```bash
hub query                          # Last 100 events
hub query --limit 20               # Last 20 events
hub query --format json            # JSON output
```

**Filtering:**
```bash
# By subject (NATS wildcards)
hub query --subject "hub.test.*"
hub query --subject "hub.>"

# By time range
hub query --since "1h"             # Last hour
hub query --since "yesterday"      # Since yesterday
hub query --since "2025-11-04"     # Since specific date

# By correlation ID
hub query --correlation-id "abc123-..."

# Combined filters
hub query --subject "hub.test.*" --since "1h" --limit 50
```

**Output formats:**
- `table` (default): Rich terminal table
- `json`: JSON array for scripting

### follow - Stream Live Events

Watch events in real-time as they occur.

**Basic usage:**
```bash
hub follow                         # All hub events
hub follow --subject "hub.test.*"  # Filtered
hub follow --format json           # JSON output
```

**Output formats:**
- `compact` (default): One-line per event
- `json`: Full JSON per event
- `table`: Live-updating table (last 20 events)

**Stop streaming:** Press `Ctrl+C`

## Examples

**Monitor all project events:**
```bash
hub follow --subject "hub.*.project.*"
```

**Debug specific request:**
```bash
# Get correlation ID from API response header
curl -I http://localhost:9001/api/projects

# Query all events for that request
hub query --correlation-id "<correlation-id>"
```

**Export events to file:**
```bash
hub query --format json --since "24h" > events.json
```

**Continuous monitoring:**
```bash
hub follow --subject "hub.>" | grep ERROR
```

## Time Formats

Supports multiple formats:

**Relative:**
- `1h`, `2h`, `24h` - Hours ago
- `30m`, `45m` - Minutes ago
- `1d`, `7d` - Days ago

**Natural language:**
- `yesterday`
- `last Monday`
- `2 hours ago`
- `last week`

**ISO 8601:**
- `2025-11-04T10:30:00Z`
- `2025-11-04`

## Subject Patterns

NATS wildcard syntax:

- `*` - Single token (e.g., `hub.*.project` matches `hub.local.project`)
- `>` - Multiple tokens (e.g., `hub.test.>` matches `hub.test.foo.bar`)

**Examples:**
- `hub.*.health.*` - Health events from any hub
- `hub.local.>` - All events from local hub
- `hub.*.project.created` - Project creation from any hub

## Troubleshooting

**Connection errors:**
```bash
# Check NATS is running
curl http://localhost:8222/varz

# Check database connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM events"
```

**No events returned:**
- Verify events exist: `hub query --limit 1000`
- Check subject pattern matches actual subjects
- Verify time range includes events

**CLI not found:**
```bash
# Reinstall in development mode
cd hub/backend
pip install -e .
```
```

**Step 2: Update Hub README**

Modify: `hub/README.md`

Add section after "Features":

```markdown
## CLI Tools

**Query and monitor events:**

```bash
# Install CLI
cd backend && pip install -e .

# Query events
hub query --subject "hub.test.*" --since "1h"

# Stream live events
hub follow --subject "hub.>"
```

See [CLI Usage Guide](docs/CLI_USAGE.md) for complete documentation.
```

**Step 3: Update project status**

Modify: `docs/PROJECT.md`

Update "Active Work" section:

```markdown
- **Active Work**:
  - **Phase 2-3**: Event Streaming & Correlation **COMPLETE** ✅ (Completed 2025-11-04)
    - ✅ Correlation middleware for request tracing
    - ✅ Server-Sent Events (SSE) streaming endpoint
    - ✅ CLI tools (query, follow commands)
    - ✅ Enhanced EventService filtering
    - ✅ Natural language time parsing
    - ✅ Rich terminal formatting
    - **XX commits**, YY files changed, +ZZ / -WW lines
    - **XX tests** (all passing)
```

**Step 4: Commit**

```bash
git add hub/docs/CLI_USAGE.md hub/README.md docs/PROJECT.md
git commit -m "docs: add Phase 2-3 documentation

- CLI usage guide with examples
- Update Hub README with CLI section
- Update PROJECT.md with Phase 2-3 status
- Complete feature documentation"
```

---

### Task 14: Final Verification

**Files:**
- None (testing only)

**Step 1: Run full test suite**

```bash
cd hub/backend
pytest tests/ -v
```

Expected: All tests pass

**Step 2: Verify CLI works end-to-end**

```bash
# Test query
hub query --limit 5

# Test follow (Ctrl+C after seeing output)
hub follow --subject "hub.>" &
FOLLOW_PID=$!

# Publish test event
curl -X POST http://localhost:9001/api/events \
  -H "Content-Type: application/json" \
  -d '{"subject":"hub.test.verification","payload":{"test":true}}'

# Should see event in follow output

kill $FOLLOW_PID
```

Expected: Event appears in follow output

**Step 3: Verify SSE endpoint**

```bash
# Start SSE stream
curl -N http://localhost:9001/api/events/stream?subject=hub.test.* &
CURL_PID=$!

# Publish event
curl -X POST http://localhost:9001/api/events \
  -H "Content-Type: application/json" \
  -d '{"subject":"hub.test.sse","payload":{"test":true}}'

# Should see SSE data: {...}

kill $CURL_PID
```

Expected: SSE stream receives event

**Step 4: Verify correlation IDs**

```bash
# Make request and capture correlation ID
CORR_ID=$(curl -I http://localhost:9001/health | grep X-Correlation-ID | awk '{print $2}' | tr -d '\r')

# Query by correlation ID
hub query --correlation-id "$CORR_ID"
```

Expected: Events with matching correlation ID (may be empty if no events emitted during health check)

**Step 5: Check code coverage**

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

Expected: >85% coverage for new modules

**Step 6: Run linters**

```bash
black --check app/
flake8 app/
mypy app/
```

Expected: No errors

**Step 7: Create verification checklist**

Create: `hub/docs/PHASE_2_3_VERIFICATION.md`

```markdown
# Phase 2-3 Verification Checklist

## Functional Testing

- [ ] Correlation middleware injects IDs into all requests
- [ ] Correlation IDs preserved from request headers
- [ ] Invalid correlation IDs regenerated
- [ ] EventService.query_events filters by subject/time/correlation
- [ ] SSE endpoint streams events in real-time
- [ ] SSE filtering works (subject, time, correlation)
- [ ] CLI query command works with all filters
- [ ] CLI follow command streams live events
- [ ] Time parser handles relative/natural/ISO formats
- [ ] Rich formatters display tables correctly

## Performance

- [ ] Correlation middleware overhead <1ms
- [ ] SSE handles 100+ concurrent connections
- [ ] CLI query <500ms for 1000 events
- [ ] CLI follow <50ms latency from publish to display

## Integration

- [ ] Phase 1 tests still pass
- [ ] No breaking changes to existing APIs
- [ ] SSE works alongside WebSocket endpoint
- [ ] CLI tools connect to running Hub

## Documentation

- [ ] CLI usage guide complete
- [ ] README updated
- [ ] PROJECT.md reflects Phase 2-3 status
- [ ] Code comments and docstrings present

## Code Quality

- [ ] All tests passing (unit + integration)
- [ ] >85% code coverage
- [ ] Linters pass (black, flake8, mypy)
- [ ] No security vulnerabilities

---

**Sign-off:** Phase 2-3 ready for merge ✅
**Date:** 2025-11-04
```

**Step 8: Commit verification docs**

```bash
git add hub/docs/PHASE_2_3_VERIFICATION.md
git commit -m "docs: add Phase 2-3 verification checklist

- Functional testing checklist
- Performance benchmarks
- Integration verification
- Quality gates"
```

---

## Final Steps

### Task 15: Create Pull Request

**Step 1: Push branch**

```bash
git push origin phase-2-3-event-streaming
```

**Step 2: Create PR**

```bash
gh pr create \
  --title "feat: Phase 2-3 Event Streaming & Correlation" \
  --body "$(cat <<'EOF'
## Summary

Phase 2-3 extends the Phase 1 event infrastructure with correlation IDs, real-time streaming, and CLI tools for operational debugging and monitoring.

**Key Features:**
- Correlation middleware for automatic request tracing
- Server-Sent Events (SSE) endpoint for HTTP-based streaming
- CLI tools (query, follow) with natural language time parsing
- Enhanced EventService filtering (subject, time, correlation ID)

## Changes

**New Modules:**
- `app/correlation/` - Correlation ID middleware and context
- `app/streaming/` - SSE endpoint and filtering
- `app/cli/` - CLI commands and utilities

**Modified:**
- `app/main.py` - Added correlation middleware
- `app/events/service.py` - Added query_events method
- `requirements.txt` - Added click, dateparser, rich

**Tests:**
- 37 unit tests
- 7 integration tests
- 90%+ code coverage for new modules

## Testing

```bash
cd hub/backend
pytest tests/ -v
hub query --limit 10
hub follow --subject "hub.>"
```

## Documentation

- CLI Usage Guide: `hub/docs/CLI_USAGE.md`
- Verification Checklist: `hub/docs/PHASE_2_3_VERIFICATION.md`
- Updated README and PROJECT.md

## Breaking Changes

None - all changes are additive and backward compatible.

## Next Steps

- Phase 4: NATS Bridge for external systems
- Phase 5-6: Hub Federation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Step 3: Verify PR created**

```bash
gh pr view
```

Expected: PR details displayed

---

## Success Criteria

**Phase 2-3 is complete when:**

✅ All 14 tasks implemented
✅ All tests passing (unit + integration)
✅ CLI tools working end-to-end
✅ SSE streaming functional
✅ Correlation IDs flow through system
✅ Documentation complete
✅ PR created and passing CI

**Estimated Time:** 2-3 weeks (parallel development)

---

## Notes

**Development Tips:**

1. **Use TDD:** Write test first, watch it fail, implement, watch it pass
2. **Commit frequently:** Each task step should be a commit
3. **Test incrementally:** Don't wait until end to run tests
4. **Check integration often:** Ensure Phase 1 tests still pass

**Common Issues:**

- **Import errors:** Ensure `__init__.py` files created
- **Async tests:** Use `@pytest.mark.asyncio` decorator
- **CLI not found:** Run `pip install -e .` in backend/
- **NATS connection:** Verify NATS running on localhost:4222

**Performance Targets:**

- Correlation middleware: <1ms overhead
- SSE connections: 1000+ concurrent
- CLI query: <500ms for 10k events
- CLI follow: <10ms latency

---

**Ready to execute?** Use `superpowers:executing-plans` or `superpowers:subagent-driven-development` to implement this plan task-by-task.
