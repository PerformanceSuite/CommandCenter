# NATS Bridge Architecture

**Phase 4 Implementation** - Bidirectional Event Routing

**Date:** 2025-11-05
**Status:** Complete ✅

---

## Overview

The NATS Bridge provides bidirectional event routing between the CommandCenter Hub's internal event system and the NATS message bus. It enables:

- **Internal → NATS**: Automatically publish internal events to NATS subjects
- **NATS → Internal**: Subscribe to external NATS events and route to internal handlers
- **Event Filtering**: Subject-based routing rules with wildcard support
- **External Integration**: JSON-RPC endpoint for external tools to publish/query events

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    CommandCenter Hub                         │
│                                                              │
│  ┌─────────────┐      ┌──────────────┐     ┌──────────┐   │
│  │ EventService│◄────►│  NATSBridge  │◄───►│ NATS     │   │
│  │ (Phase 1-3) │      │  (Phase 4)   │     │ Server   │   │
│  └─────────────┘      └──────────────┘     └──────────┘   │
│         │                     │                             │
│         │                     │                             │
│  ┌──────▼─────────────────────▼──────────┐                │
│  │     PostgreSQL Event Store             │                │
│  └────────────────────────────────────────┘                │
│                                                              │
│  ┌──────────────────────────────────────┐                  │
│  │     JSON-RPC Endpoint (/rpc)         │                  │
│  └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                         ▲
                         │
              ┌──────────┴──────────┐
              │                     │
        External Tools      Other Hub Instances
        (CLI, Scripts)      (Federation)
```

### Subject Namespace

Events follow a hierarchical namespace pattern:

```
hub.<hub_id>.<domain>.<action>
```

**Examples:**
- `hub.local-hub.project.created` - Local project creation
- `hub.local-hub.audit.security.completed` - Local security audit
- `hub.local-hub.health.postgres.degraded` - Local health alert
- `hub.global.presence.announced` - Cross-hub presence announcement
- `hub.global.sync.registry-update` - Cross-hub registry sync

**Patterns:**
- `hub.*.project.*` - All project events from any hub
- `hub.global.>` - All global federation events
- `hub.local-hub.>` - All events from local hub

### Data Flow

#### Internal → NATS (Publish)

1. Service emits internal event via `EventService.publish()`
2. Event persisted to PostgreSQL (source of truth)
3. `NATSBridge.publish_internal_to_nats()` forwards to NATS
4. Auto-prefixes subject with `hub.<hub_id>` if not present
5. Adds correlation ID to NATS headers

#### NATS → Internal (Subscribe)

1. `NATSBridge.subscribe_nats_to_internal()` listens to NATS subjects
2. Incoming messages parsed and validated
3. Correlation ID extracted from headers
4. Routed to internal handler function
5. Optional: Persisted via `EventService` for audit trail

#### Routing Rules

1. Register routing rules with subject patterns
2. Incoming events matched against all enabled rules
3. Multiple handlers can match same event
4. Errors in handlers are isolated and logged

---

## API Reference

### NATSBridge Class

```python
from app.events.bridge import NATSBridge

bridge = NATSBridge(nats_url="nats://localhost:4222")
await bridge.connect()
```

#### Methods

**`connect()`**
- Connect to NATS server and initialize JetStream
- Raises exception if connection fails

**`disconnect()`**
- Close NATS connection and unsubscribe from all subjects
- Cleanup subscriptions automatically

**`publish_internal_to_nats(subject, payload, correlation_id=None)`**
- Publish internal event to NATS
- Auto-prefixes subject with `hub.<hub_id>` if not present
- Adds correlation headers

**Example:**
```python
await bridge.publish_internal_to_nats(
    subject="project.created",
    payload={"project_id": "123", "name": "MyProject"},
    correlation_id=uuid4()
)
# Publishes to: hub.local-hub.project.created
```

**`subscribe_nats_to_internal(subject_filter, handler)`**
- Subscribe to NATS subject pattern
- Call handler for each matching message
- Supports wildcards: `*` (single segment), `>` (remaining segments)

**Example:**
```python
async def handle_global_events(subject: str, data: dict):
    print(f"Global event: {subject}")

await bridge.subscribe_nats_to_internal(
    "hub.global.>",
    handle_global_events
)
```

**`add_routing_rule(subject_pattern, handler, enabled=True, description=None)`**
- Add event routing rule
- Returns `RoutingRule` instance
- Multiple rules can match same event

**Example:**
```python
async def log_project_events(subject: str, data: dict):
    logger.info(f"Project event: {subject}")

rule = bridge.add_routing_rule(
    "hub.*.project.*",
    log_project_events,
    description="Log all project events"
)
```

**`remove_routing_rule(rule)`**
- Remove routing rule

**`route_event(subject, data)`**
- Manually route event to matching handlers
- Returns count of handlers that matched

**`get_routing_rules()`**
- Get list of all routing rules
- Returns dictionaries with pattern, enabled, description

---

## JSON-RPC Endpoint

External tools can interact with the event bus via JSON-RPC 2.0.

**Endpoint:** `POST /rpc`

### Available Methods

#### `bus.publish`

Publish event to NATS bus.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "bus.publish",
  "params": {
    "topic": "hub.local-hub.project.started",
    "payload": {
      "project_id": "abc123",
      "status": "running"
    },
    "correlation_id": "optional-uuid"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "published": true,
    "subject": "hub.local-hub.project.started",
    "correlation_id": "generated-or-provided-uuid"
  }
}
```

#### `bus.subscribe`

Query recent events by subject pattern.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "bus.subscribe",
  "params": {
    "subject": "hub.*.project.>",
    "limit": 50
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "events": [
      {
        "id": "event-uuid",
        "subject": "hub.local-hub.project.created",
        "origin": {"hub_id": "local-hub", "service": "hub-backend"},
        "correlation_id": "corr-uuid",
        "payload": {"project_id": "123"},
        "timestamp": "2025-11-05T12:00:00Z"
      }
    ],
    "count": 1
  }
}
```

#### `hub.info`

Get Hub metadata.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "hub.info",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "hub_id": "local-hub",
    "version": "1.0.0",
    "status": "running"
  }
}
```

#### `hub.health`

Get Hub health status.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "hub.health",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "status": "healthy",
    "services": {
      "nats": "healthy",
      "database": "healthy"
    }
  }
}
```

### Error Handling

JSON-RPC 2.0 error codes:

- `-32700`: Parse error (invalid JSON)
- `-32600`: Invalid request (wrong JSON-RPC version)
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "error": {
    "code": -32601,
    "message": "Method not found: invalid.method",
    "data": {
      "available_methods": ["bus.publish", "bus.subscribe", "hub.info", "hub.health"]
    }
  }
}
```

---

## Usage Examples

### Publishing Events

```python
from app.events.bridge import NATSBridge
from app.config import get_nats_url

bridge = NATSBridge(nats_url=get_nats_url())
await bridge.connect()

# Publish project event
await bridge.publish_internal_to_nats(
    subject="project.started",
    payload={
        "project_id": "my-project",
        "status": "running",
        "pid": 12345
    }
)

await bridge.disconnect()
```

### Subscribing to Events

```python
from app.events.bridge import NATSBridge

bridge = NATSBridge(nats_url="nats://localhost:4222")
await bridge.connect()

# Handler function
async def on_project_event(subject: str, data: dict):
    print(f"Project event received: {subject}")
    print(f"Data: {data}")

# Subscribe to all project events from any hub
await bridge.subscribe_nats_to_internal(
    "hub.*.project.>",
    on_project_event
)

# Keep bridge alive
# ... await some condition or signal ...

await bridge.disconnect()
```

### Routing Rules

```python
from app.events.bridge import NATSBridge

bridge = NATSBridge(nats_url="nats://localhost:4222")
await bridge.connect()

# Add routing rules
async def audit_logger(subject: str, data: dict):
    # Log to audit system
    pass

async def alert_handler(subject: str, data: dict):
    # Send alerts for critical events
    pass

# Route security events to audit
bridge.add_routing_rule(
    "hub.*.audit.>",
    audit_logger,
    description="Audit trail logger"
)

# Route health alerts
bridge.add_routing_rule(
    "hub.*.health.*.degraded",
    alert_handler,
    description="Health alert handler"
)

# Get all rules
rules = bridge.get_routing_rules()
for rule in rules:
    print(f"{rule['description']}: {rule['subject_pattern']}")
```

### External Tool Integration (curl)

```bash
# Publish event via JSON-RPC
curl -X POST http://localhost:9001/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "bus.publish",
    "params": {
      "topic": "hub.local-hub.deployment.started",
      "payload": {
        "service": "api",
        "version": "1.2.3"
      }
    }
  }'

# Query events
curl -X POST http://localhost:9001/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "bus.subscribe",
    "params": {
      "subject": "hub.*.deployment.>",
      "limit": 10
    }
  }'

# Get Hub health
curl -X POST http://localhost:9001/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "hub.health"
  }'
```

### Python External Client

```python
import httpx
import json

async def publish_event(topic: str, payload: dict):
    """Publish event via JSON-RPC."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:9001/rpc",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "bus.publish",
                "params": {
                    "topic": topic,
                    "payload": payload
                }
            }
        )
        result = response.json()

        if "error" in result:
            raise Exception(f"RPC Error: {result['error']}")

        return result["result"]

# Usage
await publish_event(
    "hub.local-hub.task.completed",
    {"task_id": "task-123", "duration_ms": 1500}
)
```

---

## Configuration

### Environment Variables

```bash
# NATS connection URL
NATS_URL=nats://localhost:4222

# Hub identifier (used in subject namespace)
HUB_ID=local-hub

# Database URL (for event persistence)
DATABASE_URL=sqlite+aiosqlite:////app/data/hub.db
```

### Docker Compose

```yaml
services:
  nats:
    image: nats:2.10-alpine
    ports:
      - "4222:4222"  # Client connections
      - "8222:8222"  # Monitoring
    command: ["-js", "-m", "8222"]  # Enable JetStream + monitoring

  hub-backend:
    environment:
      - NATS_URL=nats://nats:4222
      - HUB_ID=local-hub
    depends_on:
      - nats
```

---

## Testing

Tests are located in `tests/events/test_bridge.py` and `tests/routers/test_rpc.py`.

### Run Bridge Tests

```bash
cd hub/backend
pytest tests/events/test_bridge.py -v
```

### Run RPC Tests

```bash
pytest tests/routers/test_rpc.py -v
```

### Manual Testing

```bash
# Start NATS server
docker-compose up nats

# Start Hub backend
cd hub/backend
uvicorn app.main:app --reload --port 9001

# In another terminal, test RPC endpoint
curl -X POST http://localhost:9001/rpc/methods
```

---

## Phase 4 Success Criteria

- ✅ Internal events auto-publish to NATS
- ✅ NATS events trigger internal handlers
- ✅ JSON-RPC endpoint functional
- ✅ Subject routing rules enforced
- ✅ Bidirectional routing tested
- ✅ Documentation complete

## Next Steps: Phase 5

**Federation Prep (Week 5)** will build on this foundation:

- Hub registry metadata model
- Presence heartbeat publisher (using NATSBridge)
- Hub discovery subscriber (using routing rules)
- Metrics publishing to `hub.global.>` subjects

See `docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md` for details.
