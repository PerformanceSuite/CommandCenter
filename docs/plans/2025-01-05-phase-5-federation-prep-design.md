# Phase 5: Federation Prep - Design Document

**Date:** 2025-01-05
**Phase:** 5 of 12
**Status:** Design Complete, Ready for Implementation

---

## Overview

Phase 5 implements the foundation for Hub federation: presence heartbeats, Hub discovery, and basic metrics publishing. This enables multiple CommandCenter instances to discover each other and share operational state.

**Key Deliverables:**
1. Hub registry metadata model
2. Presence heartbeat publisher (5s interval)
3. Hub discovery subscriber
4. Metrics publishing (30s interval)

---

## Design Constraints

### Deployment Model
- **Primary:** Local-first (single developer, multiple projects on localhost)
- **Future:** Network-capable architecture for team collaboration
- **NATS:** Shared NATS instance on localhost for local federation

### Hub Identity
- **Method:** Derived from machine hostname + project path
- **Format:** `hub-<12-char-hash>` (e.g., `hub-abc123def456`)
- **Collision Resistance:** SHA256 hash of `commandcenter:{hostname}:{absolute_path}`
- **Stability:** Same ID across restarts, changes only if machine or path changes

### Metrics Scope
- **Phase 5:** Minimal basics (project count, service count, uptime)
- **Phase 6+:** Extended metrics (health, throughput, storage)

### Registry Management
- **Strategy:** Active-only (prune stale Hubs)
- **Timeout:** 30 seconds without heartbeat
- **Pruning:** Every 60 seconds

---

## Architecture

### Component Structure

```
FederationService (hub/backend/app/services/federation_service.py)
├── PresencePublisher (heartbeat every 5s)
├── DiscoverySubscriber (handles hub.global.presence)
├── MetricsPublisher (publishes every 30s)
└── PruningWorker (prunes stale Hubs every 60s)

HubRegistry (hub/backend/app/models/hub_registry.py)
└── SQLAlchemy model for discovered Hubs

API Endpoints (hub/backend/app/routers/federation.py)
└── GET /api/federation/hubs (debugging/monitoring)
```

### Background Tasks

| Task | Interval | Subject | Purpose |
|------|----------|---------|---------|
| Heartbeat | 5s | `hub.global.presence` | Announce this Hub's presence |
| Metrics | 30s | `hub.global.metrics.<hub_id>` | Publish operational metrics |
| Pruning | 60s | N/A (database cleanup) | Remove stale Hubs (>30s) |

---

## Detailed Design

### 1. Hub Identity Generation

**Implementation:** `hub/backend/app/config.py`

```python
import hashlib
import socket
from pathlib import Path

def generate_hub_id() -> str:
    """
    Generate collision-resistant Hub ID from machine + project path.
    Format: hub-<short-hash>

    To prevent collisions when projects move:
    - Include hostname (machine identity)
    - Include absolute project path
    - Include a namespace identifier ('commandcenter')
    - Use SHA256 for cryptographic collision resistance
    """
    hostname = socket.gethostname()
    project_path = str(Path.cwd().resolve())
    namespace = "commandcenter"

    # Combine all identifiers
    identity_string = f"{namespace}:{hostname}:{project_path}"

    # SHA256 hash (first 12 chars provides ~68 bits of entropy)
    hash_digest = hashlib.sha256(identity_string.encode()).hexdigest()[:12]

    return f"hub-{hash_digest}"

class Settings(BaseSettings):
    HUB_ID: str = Field(default_factory=generate_hub_id)
    HUB_NAME: str = Field(default="CommandCenter Hub")
    VERSION: str = "1.0.0"
```

**Why This Works:**
- Stable across restarts (same machine + path = same ID)
- Collision-resistant even if project moves (includes hostname)
- Automatic (no manual configuration required)
- Human-readable prefix (`hub-`)
- 68 bits of entropy (collision probability: ~1 in 300 trillion)

---

### 2. Database Model

**Implementation:** `hub/backend/app/models/hub_registry.py`

```python
from sqlalchemy import Column, String, DateTime, JSON, Integer
from app.db.base_class import Base
from datetime import datetime

class HubRegistry(Base):
    __tablename__ = "hub_registry"

    # Identity
    id = Column(String, primary_key=True)  # hub-abc123def456
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)

    # Discovery metadata
    hostname = Column(String, nullable=True)  # Machine hostname
    project_path = Column(String, nullable=True)  # Project directory

    # Hub state
    projects = Column(JSON, default=list)  # List of project IDs
    services = Column(JSON, default=list)  # List of service names

    # Metrics (minimal for Phase 5)
    project_count = Column(Integer, default=0)
    service_count = Column(Integer, default=0)
    uptime_seconds = Column(Integer, default=0)

    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata extension point
    metadata = Column(JSON, default=dict)
```

**Migration:**
```bash
alembic revision --autogenerate -m "Add hub_registry table"
# Includes index: CREATE INDEX ix_hub_registry_last_seen ON hub_registry (last_seen DESC);
```

**Design Rationale:**
- `id` as primary key (hub-xxx format)
- Tracks `first_seen` + `last_seen` for lifecycle management
- Minimal metrics (project_count, service_count, uptime)
- JSON fields for flexible extension (projects, services, metadata)
- Index on `last_seen` enables fast pruning queries

---

### 3. FederationService Core

**Implementation:** `hub/backend/app/services/federation_service.py`

```python
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.hub_registry import HubRegistry
from app.events.bridge import NATSBridge
from app.config import settings
import asyncio
import json
import socket
from pathlib import Path

class FederationService:
    """
    Manages Hub federation: presence heartbeats, discovery, and metrics.
    """

    def __init__(self, db: Session, nats_bridge: NATSBridge):
        self.db = db
        self.nats_bridge = nats_bridge
        self.hub_id = settings.HUB_ID
        self.hub_name = settings.HUB_NAME
        self.version = settings.VERSION
        self.start_time = datetime.utcnow()
        self._heartbeat_task = None
        self._metrics_task = None
        self._pruning_task = None

    async def start(self):
        """Start federation services (called on app startup)"""
        # Subscribe to presence announcements from other Hubs
        await self.nats_bridge.subscribe_nats_to_internal(
            subject="hub.global.presence",
            handler=self._handle_presence_announcement
        )

        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._metrics_task = asyncio.create_task(self._metrics_loop())
        self._pruning_task = asyncio.create_task(self._pruning_loop())

    async def stop(self):
        """Stop federation services (called on app shutdown)"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._metrics_task:
            self._metrics_task.cancel()
        if self._pruning_task:
            self._pruning_task.cancel()
```

**Design Principles:**
- Encapsulates all federation logic in one service
- Uses NATSBridge from Phase 4 (no direct NATS dependency)
- Three background tasks with independent error handling
- Lifecycle management via `start()`/`stop()` methods
- Follows existing service patterns (EventService, GitHubService)

---

### 4. Presence Heartbeat & Discovery

**Heartbeat Publisher:**

```python
async def _heartbeat_loop(self):
    """Publish presence heartbeat every 5 seconds"""
    while True:
        try:
            await self._publish_presence()
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            break
        except Exception as e:
            # Log error but continue heartbeat
            print(f"Heartbeat error: {e}")
            await asyncio.sleep(5)

async def _publish_presence(self):
    """Publish presence announcement to NATS"""
    payload = {
        "hub_id": self.hub_id,
        "name": self.hub_name,
        "version": self.version,
        "hostname": socket.gethostname(),
        "project_path": str(Path.cwd().resolve()),
        "timestamp": datetime.utcnow().isoformat()
    }

    # Publish to global federation subject
    await self.nats_bridge.publish_internal_to_nats(
        topic="hub.global.presence",
        payload=payload
    )
```

**Discovery Subscriber:**

```python
async def _handle_presence_announcement(self, event_data: dict):
    """Handle presence announcement from another Hub"""
    hub_id = event_data.get("hub_id")

    # Don't register self
    if hub_id == self.hub_id:
        return

    # Upsert Hub registry entry
    hub_entry = self.db.query(HubRegistry).filter_by(id=hub_id).first()

    if hub_entry:
        # Update existing entry
        hub_entry.last_seen = datetime.utcnow()
        hub_entry.name = event_data.get("name")
        hub_entry.version = event_data.get("version")
        hub_entry.hostname = event_data.get("hostname")
        hub_entry.project_path = event_data.get("project_path")
    else:
        # Create new entry
        hub_entry = HubRegistry(
            id=hub_id,
            name=event_data.get("name"),
            version=event_data.get("version"),
            hostname=event_data.get("hostname"),
            project_path=event_data.get("project_path"),
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        self.db.add(hub_entry)

    self.db.commit()
```

**Design Rationale:**
- Heartbeat every 5s keeps registry fresh
- Graceful error handling (log & continue, never crash)
- Discovery uses upsert pattern (idempotent)
- Filters out self-announcements
- Uses `NATSBridge.publish_internal_to_nats()` from Phase 4

---

### 5. Metrics Publishing & Pruning

**Metrics Publisher:**

```python
async def _metrics_loop(self):
    """Publish metrics every 30 seconds"""
    while True:
        try:
            await self._publish_metrics()
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Metrics error: {e}")
            await asyncio.sleep(30)

async def _publish_metrics(self):
    """Publish minimal metrics to NATS"""
    # Calculate uptime
    uptime_seconds = int((datetime.utcnow() - self.start_time).total_seconds())

    # Get basic counts (adjust based on your models)
    from app.models.project import Project
    from app.models.service import Service

    project_count = self.db.query(Project).count()
    service_count = self.db.query(Service).count()

    payload = {
        "hub_id": self.hub_id,
        "project_count": project_count,
        "service_count": service_count,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Publish to hub-specific metrics subject
    await self.nats_bridge.publish_internal_to_nats(
        topic=f"hub.global.metrics.{self.hub_id}",
        payload=payload
    )
```

**Stale Hub Pruning:**

```python
async def _pruning_loop(self):
    """Prune stale Hubs every 60 seconds"""
    while True:
        try:
            await self._prune_stale_hubs()
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Pruning error: {e}")
            await asyncio.sleep(60)

async def _prune_stale_hubs(self):
    """Remove Hubs not seen in last 30 seconds"""
    stale_threshold = datetime.utcnow() - timedelta(seconds=30)

    deleted_count = self.db.query(HubRegistry).filter(
        HubRegistry.last_seen < stale_threshold
    ).delete()

    self.db.commit()

    if deleted_count > 0:
        print(f"Pruned {deleted_count} stale Hub(s)")
```

**Design Rationale:**
- Metrics every 30s (roadmap requirement)
- Minimal metrics: project_count, service_count, uptime
- Pruning every 60s with 30s timeout (2x heartbeat interval for safety)
- Hub-specific metrics subject: `hub.global.metrics.<hub_id>`
- Clean registry maintenance

---

### 6. FastAPI Integration

**Startup/Shutdown Lifecycle:**

```python
# hub/backend/app/main.py

from contextlib import asynccontextmanager
from app.services.federation_service import FederationService
from app.events.bridge import NATSBridge
from app.db.session import SessionLocal

federation_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan for startup/shutdown events"""
    global federation_service

    # Startup
    db = SessionLocal()
    nats_bridge = app.state.nats_bridge  # Assuming NATSBridge is in app.state

    federation_service = FederationService(db=db, nats_bridge=nats_bridge)
    await federation_service.start()

    print(f"✅ Federation started - Hub ID: {federation_service.hub_id}")

    yield

    # Shutdown
    await federation_service.stop()
    db.close()
    print("✅ Federation stopped")

app = FastAPI(lifespan=lifespan)
```

**API Endpoints (Optional - Debugging):**

```python
# hub/backend/app/routers/federation.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.hub_registry import HubRegistry

router = APIRouter(prefix="/api/federation", tags=["federation"])

@router.get("/hubs")
async def list_discovered_hubs(db: Session = Depends(get_db)):
    """List all discovered Hubs"""
    hubs = db.query(HubRegistry).all()
    return {
        "count": len(hubs),
        "hubs": [
            {
                "id": hub.id,
                "name": hub.name,
                "version": hub.version,
                "hostname": hub.hostname,
                "first_seen": hub.first_seen.isoformat(),
                "last_seen": hub.last_seen.isoformat(),
                "project_count": hub.project_count,
                "service_count": hub.service_count
            }
            for hub in hubs
        ]
    }
```

**Design Rationale:**
- Uses FastAPI lifespan context manager (modern pattern)
- Federation starts automatically with app
- Graceful shutdown cancels background tasks
- Optional API endpoint for debugging/monitoring
- Minimal changes to existing `main.py`

---

## Testing Strategy

**Test File:** `hub/backend/tests/services/test_federation_service.py`

### Test Coverage

1. **Hub ID Generation:**
   - Collision resistance (same machine + path = same ID)
   - Stability across calls
   - Format validation (`hub-<12-char-hash>`)

2. **Presence Publishing:**
   - Heartbeat publishes to correct subject
   - Payload contains required fields
   - Error handling (continues on failure)

3. **Discovery Subscriber:**
   - Creates new Hub entries
   - Updates existing Hub entries
   - Filters self-announcements
   - Upsert idempotency

4. **Metrics Publishing:**
   - Publishes to hub-specific subject
   - Includes project/service counts
   - Calculates uptime correctly

5. **Stale Hub Pruning:**
   - Removes Hubs older than 30s
   - Preserves active Hubs
   - Handles empty registry

### Example Test

```python
# hub/backend/tests/services/test_federation_service.py

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from app.services.federation_service import FederationService
from app.models.hub_registry import HubRegistry

@pytest.mark.asyncio
class TestFederationService:

    async def test_publish_presence(self, db_session, mock_nats_bridge):
        """Test presence heartbeat publishing"""
        service = FederationService(db=db_session, nats_bridge=mock_nats_bridge)

        await service._publish_presence()

        # Verify NATS publish called
        mock_nats_bridge.publish_internal_to_nats.assert_called_once()
        call_args = mock_nats_bridge.publish_internal_to_nats.call_args
        assert call_args[1]["topic"] == "hub.global.presence"
        assert "hub_id" in call_args[1]["payload"]

    async def test_handle_presence_creates_new_hub(self, db_session, mock_nats_bridge):
        """Test discovery subscriber creates new Hub entry"""
        service = FederationService(db=db_session, nats_bridge=mock_nats_bridge)

        event_data = {
            "hub_id": "hub-other123",
            "name": "Other Hub",
            "version": "1.0.0",
            "hostname": "other-machine",
            "project_path": "/path/to/project"
        }

        await service._handle_presence_announcement(event_data)

        # Verify Hub registered
        hub = db_session.query(HubRegistry).filter_by(id="hub-other123").first()
        assert hub is not None
        assert hub.name == "Other Hub"

    async def test_prune_stale_hubs(self, db_session, mock_nats_bridge):
        """Test pruning of stale Hubs"""
        service = FederationService(db=db_session, nats_bridge=mock_nats_bridge)

        # Create stale Hub (last seen 60s ago)
        stale_hub = HubRegistry(
            id="hub-stale",
            name="Stale Hub",
            version="1.0.0",
            last_seen=datetime.utcnow() - timedelta(seconds=60)
        )
        db_session.add(stale_hub)
        db_session.commit()

        await service._prune_stale_hubs()

        # Verify stale Hub pruned
        hub = db_session.query(HubRegistry).filter_by(id="hub-stale").first()
        assert hub is None
```

---

## NATS Subject Design

### Global Federation Subjects

| Subject | Publisher | Subscriber | Payload | Frequency |
|---------|-----------|------------|---------|-----------|
| `hub.global.presence` | All Hubs | All Hubs | Hub metadata | 5s |
| `hub.global.metrics.<hub_id>` | Each Hub | Monitoring tools | Metrics | 30s |

### Subject Patterns

**Presence Announcement:**
```
Subject: hub.global.presence
Payload: {
  "hub_id": "hub-abc123def456",
  "name": "CommandCenter Hub",
  "version": "1.0.0",
  "hostname": "macbook-pro.local",
  "project_path": "/Users/user/Projects/CommandCenter",
  "timestamp": "2025-01-05T12:34:56.789Z"
}
```

**Metrics Publication:**
```
Subject: hub.global.metrics.hub-abc123def456
Payload: {
  "hub_id": "hub-abc123def456",
  "project_count": 3,
  "service_count": 12,
  "uptime_seconds": 3600,
  "timestamp": "2025-01-05T12:34:56.789Z"
}
```

---

## Success Criteria

From roadmap Phase 5:

- [ ] Presence heartbeat publishes every 5s
- [ ] Other Hubs discovered and tracked in `hub_registry` table
- [ ] Metrics published every 30s to hub-specific subject
- [ ] Stale Hubs pruned after 30s timeout

**Additional Validation:**

- [ ] Hub ID stable across restarts
- [ ] Self-announcements filtered (Hub doesn't register itself)
- [ ] Multiple Hubs on localhost discover each other
- [ ] API endpoint returns discovered Hubs
- [ ] All tests pass

---

## File Checklist

**New Files (5):**
1. `hub/backend/app/services/federation_service.py` - Core service
2. `hub/backend/app/models/hub_registry.py` - Database model
3. `hub/backend/app/routers/federation.py` - API endpoints
4. `hub/backend/tests/services/test_federation_service.py` - Tests
5. `hub/backend/alembic/versions/XXXX_add_hub_registry_table.py` - Migration

**Modified Files (2):**
1. `hub/backend/app/main.py` - Add lifespan integration
2. `hub/backend/app/config.py` - Add Hub ID generation

**Updated Files (1):**
1. `docs/CURRENT_SESSION.md` - Document Phase 5 completion

---

## Dependencies

**Phase 4 (Required):**
- `NATSBridge` service for publish/subscribe
- NATS connection in `app.state.nats_bridge`

**Existing Infrastructure:**
- `Project` and `Service` models (for metrics counts)
- FastAPI lifespan pattern
- SQLAlchemy session management

---

## Future Extensions (Phase 6+)

This design supports future enhancements:

1. **Network Federation:**
   - Change NATS URL from `localhost:4222` to network address
   - Add authentication/TLS for NATS connections
   - No code changes needed

2. **Enhanced Metrics:**
   - Add health status from Phase 6
   - Add event throughput from EventService
   - Extend `metrics` JSON field

3. **Hub Registry UI:**
   - Frontend visualization of discovered Hubs
   - Network topology graph
   - Real-time health dashboard

4. **Federation Topology:**
   - Hub-to-Hub direct communication
   - Leader election for coordinated tasks
   - Distributed state synchronization

---

## Implementation Notes

### Error Handling

All background tasks use try/except with logging:
- Log errors but never crash
- Continue operation after transient failures
- Use exponential backoff if needed (future)

### Database Sessions

- FederationService receives `db: Session` in constructor
- Long-lived session for background tasks
- Consider session refresh for long-running loops (if needed)

### Testing Without NATS

- Use mock `NATSBridge` in tests
- No actual NATS connection required for unit tests
- Integration tests can use real NATS (optional)

### Performance Considerations

- Heartbeat: Minimal payload (~200 bytes), 5s interval = 40 bytes/s per Hub
- Metrics: ~500 bytes, 30s interval = 17 bytes/s per Hub
- Pruning: Single DELETE query, 60s interval, negligible impact

**For 10 Hubs:** ~570 bytes/s total network traffic (negligible)

---

## Related Documentation

- **Phase 4:** `hub/backend/docs/NATS_BRIDGE.md` - NATS Bridge architecture
- **Roadmap:** `docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md`
- **Event System:** `hub/backend/docs/EVENT_SYSTEM.md` - Event infrastructure

---

*Design approved: 2025-01-05*
