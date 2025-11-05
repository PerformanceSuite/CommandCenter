# Event System Architecture

**Status:** Phase 1 Complete ✅
**Version:** 1.0
**Last Updated:** 2025-11-03

## Overview

The CommandCenter Hub uses an event-driven architecture with NATS as the message bus and PostgreSQL for event persistence. This enables:

- **Observability:** All state changes are auditable via event log
- **Integration:** External tools can subscribe to events
- **Replay:** Historical events can be queried and replayed
- **Federation:** Foundation for multi-Hub communication (Phase 6)

## Architecture

```
┌─────────────┐         ┌──────────┐         ┌────────────┐
│   Routers   │────────>│  Events  │────────>│    NATS    │
│  (FastAPI)  │         │  Service │         │ (JetStream)│
└─────────────┘         └──────────┘         └────────────┘
                             │
                             │ (persist)
                             v
                        ┌──────────┐
                        │PostgreSQL│
                        │  events  │
                        └──────────┘
```

## Event Model

**Schema:**
```python
Event(
    id=UUID,
    subject="hub.<hub_id>.<domain>.<action>",
    origin={"hub_id": "...", "service": "...", "user": "..."},
    correlation_id=UUID,
    payload={...},
    timestamp=datetime
)
```

**Subject Namespace:**
```
hub.<hub_id>.<domain>.<action>

Examples:
  hub.local-hub.project.created
  hub.local-hub.project.started
  hub.local-hub.project.stopped
  hub.local-hub.audit.security.completed
```

## API Endpoints

### Publish Event
```bash
POST /api/events
Content-Type: application/json

{
  "subject": "hub.local-hub.project.created",
  "payload": {"project_id": "123", "name": "test"}
}

Response: 201 Created
{
  "event_id": "...",
  "correlation_id": "...",
  "timestamp": "2025-11-03T12:00:00Z"
}
```

### Query Events
```bash
GET /api/events?subject=hub.%.project.%&limit=10

Response: 200 OK
[
  {
    "id": "...",
    "subject": "hub.local-hub.project.created",
    "origin": {...},
    "correlation_id": "...",
    "payload": {...},
    "timestamp": "..."
  }
]
```

### Stream Events (WebSocket)
```bash
websocat ws://localhost:9001/api/events/stream?subject=hub.>

# Receives real-time events:
{"subject": "hub.local-hub.project.started", "data": {...}}
```

## EventService Usage

```python
from app.events.service import EventService

# Initialize
event_service = EventService(
    nats_url="nats://localhost:4222",
    db_session=db
)
await event_service.connect()

# Publish
event_id = await event_service.publish(
    subject="hub.local-hub.project.created",
    payload={"project_id": "123"}
)

# Subscribe
async def handler(subject: str, data: dict):
    print(f"Received: {subject}")

await event_service.subscribe("hub.*.project.*", handler)

# Replay
events = await event_service.replay(
    subject_filter="hub.%.project.%",
    since=datetime.now(timezone.utc) - timedelta(hours=1)
)
```

## Configuration

**Environment Variables:**
```bash
NATS_URL=nats://nats:4222   # NATS server URL
HUB_ID=local-hub            # Unique Hub identifier
```

**Docker Compose:**
```yaml
nats:
  image: nats:2.10-alpine
  ports:
    - "4222:4222"  # Client
    - "8222:8222"  # Monitoring
  command: ["-js", "-m", "8222"]
```

## Monitoring

**NATS Monitoring:** http://localhost:8222/varz
**Health Check:** http://localhost:9001/health/nats

**Grafana Dashboard:** (Coming in Phase 3)

## Next Steps (Roadmap)

- **Phase 2-3:** Correlation middleware, CLI tools, temporal replay
- **Phase 4:** NATS bridge for external integrations
- **Phase 5-6:** Hub federation and service discovery

## Testing

**Unit Tests:**
```bash
pytest tests/events/test_service.py -v
```

**Integration Tests:**
```bash
docker-compose up -d nats
pytest tests/events/test_service_integration.py -v -m integration
```

**Manual Testing:**
```bash
# Stream events
websocat ws://localhost:9001/api/events/stream?subject=hub.>

# Publish test event
curl -X POST http://localhost:9001/api/events \
  -H "Content-Type: application/json" \
  -d '{"subject": "hub.test.manual", "payload": {"test": "data"}}'
```
