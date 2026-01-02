# Composable CommandCenter Execution Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform CommandCenter from isolated project containers into a unified composable operating surface where projects are zoom levels, not boundaries.

**Architecture:** Build on existing Phase 7 Graph-Service foundation. Add WebSocket subscriptions, intent parsing, and primitive composition. The unified surface queries a federated data spine and renders via schema-driven primitives.

**Tech Stack:** FastAPI, PostgreSQL, NATS, React 18, React Flow, TypeScript, WebSocket

**Current State:** Phase 7 complete (Graph-Service with federation-ready `GraphLink`). Orchestration service production-ready. All smoke tests passing.

---

## Phase 1: Foundation (Weeks 1-2)

### Task 1.1: Cross-Project Links Table Migration

**Files:**
- Create: `backend/alembic/versions/xxxx_add_cross_project_links.py`
- Modify: `backend/app/models/graph.py:680-708`

**Step 1: Create the migration file**

```bash
cd backend && alembic revision --autogenerate -m "add cross_project_links table"
```

**Step 2: Edit the migration to add the table**

```python
def upgrade():
    op.create_table(
        'cross_project_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('source_project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('source_entity_type', sa.String(50), nullable=False),
        sa.Column('source_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('target_entity_type', sa.String(50), nullable=False),
        sa.Column('target_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('discovered_at', sa.DateTime, default=datetime.utcnow),
    )
    op.create_index('ix_cross_project_links_source', 'cross_project_links', ['source_project_id', 'source_entity_id'])
    op.create_index('ix_cross_project_links_target', 'cross_project_links', ['target_project_id', 'target_entity_id'])
```

**Step 3: Run migration**

```bash
docker-compose exec backend alembic upgrade head
```

**Step 4: Verify**

```bash
docker-compose exec postgres psql -U commandcenter -d commandcenter -c "\d cross_project_links"
```

**Step 5: Commit**

```bash
git add backend/alembic/versions/ backend/app/models/graph.py
git commit -m "feat(graph): add cross_project_links table for federation"
```

---

### Task 1.2: CrossProjectLink SQLAlchemy Model

**Files:**
- Modify: `backend/app/models/graph.py`
- Test: `backend/tests/test_models/test_cross_project_link.py`

**Step 1: Write failing test**

```python
# backend/tests/test_models/test_cross_project_link.py
import pytest
from app.models.graph import CrossProjectLink
from uuid import uuid4

def test_cross_project_link_creation(db_session):
    link = CrossProjectLink(
        source_project_id=uuid4(),
        source_entity_type="symbol",
        source_entity_id=uuid4(),
        target_project_id=uuid4(),
        target_entity_type="symbol",
        target_entity_id=uuid4(),
        relationship_type="calls",
    )
    db_session.add(link)
    db_session.commit()

    assert link.id is not None
    assert link.relationship_type == "calls"
```

**Step 2: Run test to verify it fails**

```bash
docker-compose exec backend pytest tests/test_models/test_cross_project_link.py -v
```

Expected: FAIL with "cannot import name 'CrossProjectLink'"

**Step 3: Add model to graph.py**

```python
# Add after GraphLink class in backend/app/models/graph.py

class CrossProjectLink(Base):
    """Cross-project entity relationships for federation queries."""
    __tablename__ = "cross_project_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    source_entity_type = Column(String(50), nullable=False)
    source_entity_id = Column(UUID(as_uuid=True), nullable=False)
    target_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    target_entity_type = Column(String(50), nullable=False)
    target_entity_id = Column(UUID(as_uuid=True), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    metadata = Column(JSONB, default={})
    discovered_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_cross_project_links_source', 'source_project_id', 'source_entity_id'),
        Index('ix_cross_project_links_target', 'target_project_id', 'target_entity_id'),
    )
```

**Step 4: Run test to verify it passes**

```bash
docker-compose exec backend pytest tests/test_models/test_cross_project_link.py -v
```

**Step 5: Commit**

```bash
git add backend/app/models/graph.py backend/tests/test_models/
git commit -m "feat(graph): add CrossProjectLink model"
```

---

### Task 1.3: Federation Query Service Methods

**Files:**
- Modify: `backend/app/services/graph_service.py`
- Test: `backend/tests/test_services/test_graph_federation.py`

**Step 1: Write failing test**

```python
# backend/tests/test_services/test_graph_federation.py
import pytest
from app.services.graph_service import GraphService
from uuid import uuid4

@pytest.fixture
def graph_service(db_session):
    return GraphService(db_session)

def test_query_ecosystem_links(graph_service, sample_cross_project_links):
    """Query all cross-project links in ecosystem."""
    result = graph_service.query_ecosystem_links(
        entity_types=["symbol"],
        relationship_types=["calls", "imports"]
    )
    assert len(result) >= 1
    assert all(link.source_project_id != link.target_project_id for link in result)
```

**Step 2: Run test to verify it fails**

```bash
docker-compose exec backend pytest tests/test_services/test_graph_federation.py::test_query_ecosystem_links -v
```

**Step 3: Implement query_ecosystem_links**

```python
# Add to backend/app/services/graph_service.py

def query_ecosystem_links(
    self,
    entity_types: list[str] | None = None,
    relationship_types: list[str] | None = None,
    source_project_ids: list[UUID] | None = None,
    target_project_ids: list[UUID] | None = None,
    limit: int = 1000
) -> list[CrossProjectLink]:
    """Query cross-project links across the ecosystem."""
    query = self.db.query(CrossProjectLink)

    if entity_types:
        query = query.filter(
            or_(
                CrossProjectLink.source_entity_type.in_(entity_types),
                CrossProjectLink.target_entity_type.in_(entity_types)
            )
        )
    if relationship_types:
        query = query.filter(CrossProjectLink.relationship_type.in_(relationship_types))
    if source_project_ids:
        query = query.filter(CrossProjectLink.source_project_id.in_(source_project_ids))
    if target_project_ids:
        query = query.filter(CrossProjectLink.target_project_id.in_(target_project_ids))

    return query.limit(limit).all()
```

**Step 4: Run test to verify it passes**

```bash
docker-compose exec backend pytest tests/test_services/test_graph_federation.py -v
```

**Step 5: Commit**

```bash
git add backend/app/services/graph_service.py backend/tests/test_services/
git commit -m "feat(graph): add query_ecosystem_links for federation"
```

---

### Task 1.4: WebSocket Subscription Infrastructure

**Files:**
- Create: `backend/app/websocket/__init__.py`
- Create: `backend/app/websocket/manager.py`
- Create: `backend/app/websocket/subscriptions.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_websocket/test_subscriptions.py`

**Step 1: Create websocket package**

```bash
mkdir -p backend/app/websocket backend/tests/test_websocket
touch backend/app/websocket/__init__.py backend/tests/test_websocket/__init__.py
```

**Step 2: Write failing test**

```python
# backend/tests/test_websocket/test_subscriptions.py
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

def test_websocket_connect(client):
    with client.websocket_connect("/ws/graph") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert "session_id" in data
```

**Step 3: Implement ConnectionManager**

```python
# backend/app/websocket/manager.py
from fastapi import WebSocket
from typing import Dict, Set
from uuid import uuid4
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # session_id -> set of topics

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = str(uuid4())
        self.active_connections[session_id] = websocket
        self.subscriptions[session_id] = set()
        await websocket.send_json({"type": "connected", "session_id": session_id})
        return session_id

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.subscriptions:
            del self.subscriptions[session_id]

    def subscribe(self, session_id: str, topic: str):
        if session_id in self.subscriptions:
            self.subscriptions[session_id].add(topic)

    async def broadcast_to_topic(self, topic: str, message: dict):
        for session_id, topics in self.subscriptions.items():
            if topic in topics:
                websocket = self.active_connections.get(session_id)
                if websocket:
                    await websocket.send_json(message)

manager = ConnectionManager()
```

**Step 4: Add WebSocket route to main.py**

```python
# Add to backend/app/main.py
from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.manager import manager

@app.websocket("/ws/graph")
async def websocket_endpoint(websocket: WebSocket):
    session_id = await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "subscribe":
                manager.subscribe(session_id, data["topic"])
                await websocket.send_json({"type": "subscribed", "topic": data["topic"]})
    except WebSocketDisconnect:
        manager.disconnect(session_id)
```

**Step 5: Run test**

```bash
docker-compose exec backend pytest tests/test_websocket/test_subscriptions.py -v
```

**Step 6: Commit**

```bash
git add backend/app/websocket/ backend/app/main.py backend/tests/test_websocket/
git commit -m "feat(ws): add WebSocket subscription infrastructure"
```

---

### Task 1.5: NATS-to-WebSocket Bridge

**Files:**
- Create: `backend/app/websocket/nats_bridge.py`
- Modify: `backend/app/websocket/manager.py`
- Test: `backend/tests/test_websocket/test_nats_bridge.py`

**Step 1: Write failing test**

```python
# backend/tests/test_websocket/test_nats_bridge.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.websocket.nats_bridge import NATSBridge

@pytest.mark.asyncio
async def test_nats_bridge_forwards_messages():
    mock_manager = MagicMock()
    mock_manager.broadcast_to_topic = AsyncMock()

    bridge = NATSBridge(mock_manager)
    await bridge.handle_nats_message(
        subject="graph.entity.updated.proj123.symbol",
        data={"entity_id": "sym456", "change": "updated"}
    )

    mock_manager.broadcast_to_topic.assert_called_once()
```

**Step 2: Implement NATSBridge**

```python
# backend/app/websocket/nats_bridge.py
from typing import TYPE_CHECKING
import json

if TYPE_CHECKING:
    from app.websocket.manager import ConnectionManager

class NATSBridge:
    """Bridges NATS events to WebSocket subscriptions."""

    NATS_TO_WS_TOPIC_MAP = {
        "graph.entity.created": "entity:created",
        "graph.entity.updated": "entity:updated",
        "graph.entity.deleted": "entity:deleted",
        "graph.health.changed": "health:changed",
        "graph.audit.completed": "audit:completed",
    }

    def __init__(self, manager: "ConnectionManager"):
        self.manager = manager

    async def handle_nats_message(self, subject: str, data: dict):
        """Convert NATS subject to WS topic and broadcast."""
        # Extract base subject (e.g., graph.entity.updated)
        parts = subject.split(".")
        base_subject = ".".join(parts[:3])

        ws_topic = self.NATS_TO_WS_TOPIC_MAP.get(base_subject)
        if ws_topic:
            # Include project context in topic
            project_id = parts[3] if len(parts) > 3 else None
            full_topic = f"{ws_topic}:{project_id}" if project_id else ws_topic

            await self.manager.broadcast_to_topic(full_topic, {
                "type": "event",
                "topic": full_topic,
                "data": data
            })
```

**Step 3: Run test**

```bash
docker-compose exec backend pytest tests/test_websocket/test_nats_bridge.py -v
```

**Step 4: Commit**

```bash
git add backend/app/websocket/nats_bridge.py backend/tests/test_websocket/
git commit -m "feat(ws): add NATS-to-WebSocket bridge"
```

---

### Task 1.6: Frontend WebSocket Hook

**Files:**
- Create: `frontend/src/hooks/useGraphSubscription.ts`
- Create: `frontend/src/services/websocket.ts`
- Test: `frontend/src/hooks/__tests__/useGraphSubscription.test.ts`

**Step 1: Create WebSocket service**

```typescript
// frontend/src/services/websocket.ts
type MessageHandler = (data: any) => void;

class GraphWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(url: string = `ws://${window.location.host}/ws/graph`) {
    this.ws = new WebSocket(url);

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'connected') {
        this.sessionId = message.session_id;
        this.reconnectAttempts = 0;
      } else if (message.type === 'event') {
        const handlers = this.handlers.get(message.topic);
        handlers?.forEach(handler => handler(message.data));
      }
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect(url);
        }, 1000 * Math.pow(2, this.reconnectAttempts));
      }
    };
  }

  subscribe(topic: string, handler: MessageHandler) {
    if (!this.handlers.has(topic)) {
      this.handlers.set(topic, new Set());
      this.ws?.send(JSON.stringify({ action: 'subscribe', topic }));
    }
    this.handlers.get(topic)!.add(handler);

    return () => {
      this.handlers.get(topic)?.delete(handler);
    };
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
    this.sessionId = null;
  }
}

export const graphWebSocket = new GraphWebSocket();
```

**Step 2: Create useGraphSubscription hook**

```typescript
// frontend/src/hooks/useGraphSubscription.ts
import { useEffect, useCallback, useState } from 'react';
import { graphWebSocket } from '../services/websocket';

export function useGraphSubscription<T>(
  topic: string,
  onMessage?: (data: T) => void
) {
  const [lastMessage, setLastMessage] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    graphWebSocket.connect();
    setIsConnected(true);

    return () => {
      // Don't disconnect - shared connection
    };
  }, []);

  useEffect(() => {
    if (!topic) return;

    const handler = (data: T) => {
      setLastMessage(data);
      onMessage?.(data);
    };

    return graphWebSocket.subscribe(topic, handler);
  }, [topic, onMessage]);

  return { lastMessage, isConnected };
}
```

**Step 3: Write test**

```typescript
// frontend/src/hooks/__tests__/useGraphSubscription.test.ts
import { renderHook, act } from '@testing-library/react';
import { useGraphSubscription } from '../useGraphSubscription';

// Mock WebSocket
class MockWebSocket {
  onmessage: ((event: any) => void) | null = null;
  send = jest.fn();
  close = jest.fn();
}

describe('useGraphSubscription', () => {
  beforeEach(() => {
    (global as any).WebSocket = MockWebSocket;
  });

  it('subscribes to topic on mount', () => {
    const { result } = renderHook(() =>
      useGraphSubscription('entity:updated:proj123')
    );

    expect(result.current.isConnected).toBe(true);
  });
});
```

**Step 4: Run test**

```bash
cd frontend && npm test -- --testPathPattern=useGraphSubscription
```

**Step 5: Commit**

```bash
git add frontend/src/hooks/ frontend/src/services/websocket.ts
git commit -m "feat(frontend): add WebSocket subscription hook"
```

---

### Task 1.7: Extend GraphCanvas with Real-Time Updates

**Files:**
- Modify: `frontend/src/components/Graph/GraphCanvas.tsx`
- Test: `frontend/src/components/Graph/__tests__/GraphCanvas.realtime.test.tsx`

**Step 1: Write failing test**

```typescript
// frontend/src/components/Graph/__tests__/GraphCanvas.realtime.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { GraphCanvas } from '../GraphCanvas';

describe('GraphCanvas real-time updates', () => {
  it('updates node when receiving entity:updated event', async () => {
    const nodes = [{ id: 'node1', label: 'Original', type: 'symbol' }];
    const { rerender } = render(
      <GraphCanvas
        nodes={nodes}
        edges={[]}
        enableRealTime={true}
        projectId="proj123"
      />
    );

    // Simulate WebSocket message
    // ... test implementation
  });
});
```

**Step 2: Add real-time props to GraphCanvas**

```typescript
// Add to frontend/src/components/Graph/GraphCanvas.tsx props
interface GraphCanvasProps {
  // ... existing props
  enableRealTime?: boolean;
  projectId?: string;
  onNodeUpdate?: (nodeId: string, data: any) => void;
}
```

**Step 3: Integrate useGraphSubscription**

```typescript
// Add to GraphCanvas component
import { useGraphSubscription } from '../../hooks/useGraphSubscription';

// Inside component:
const handleEntityUpdate = useCallback((data: any) => {
  onNodeUpdate?.(data.entity_id, data);
}, [onNodeUpdate]);

useGraphSubscription(
  enableRealTime && projectId ? `entity:updated:${projectId}` : '',
  handleEntityUpdate
);
```

**Step 4: Run test**

```bash
cd frontend && npm test -- --testPathPattern=GraphCanvas.realtime
```

**Step 5: Commit**

```bash
git add frontend/src/components/Graph/
git commit -m "feat(graph): add real-time subscription support to GraphCanvas"
```

---

## Phase 2: Query Layer (Weeks 3-4)

### Task 2.1: ComposedQuery Schema

**Files:**
- Create: `backend/app/schemas/query.py`
- Test: `backend/tests/test_schemas/test_query.py`

**Step 1: Write failing test**

```python
# backend/tests/test_schemas/test_query.py
import pytest
from pydantic import ValidationError
from app.schemas.query import ComposedQuery, EntitySelector, Filter

def test_composed_query_from_structured():
    query = ComposedQuery(
        entities=[EntitySelector(type="symbol", scope="project:abc")],
        filters=[Filter(field="health", operator="lt", value=100)],
        presentation={"layout": "graph", "depth": 2}
    )
    assert len(query.entities) == 1
    assert query.entities[0].type == "symbol"
```

**Step 2: Create schema**

```python
# backend/app/schemas/query.py
from pydantic import BaseModel
from typing import Optional, List, Any, Literal
from datetime import datetime

class EntitySelector(BaseModel):
    type: str  # symbol, file, service, project, etc.
    scope: Optional[str] = None  # project:id, ecosystem, or specific entity ref
    constraints: Optional[dict] = None

class Filter(BaseModel):
    field: str
    operator: Literal["eq", "ne", "lt", "gt", "lte", "gte", "in", "contains"]
    value: Any

class RelationshipSpec(BaseModel):
    type: str  # calls, imports, depends_on
    direction: Literal["inbound", "outbound", "both"] = "both"
    depth: int = 1

class TimeRange(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None

class ComposedQuery(BaseModel):
    entities: List[EntitySelector]
    filters: Optional[List[Filter]] = None
    relationships: Optional[List[RelationshipSpec]] = None
    presentation: Optional[dict] = None
    time_range: Optional[TimeRange] = None
```

**Step 3: Run test**

```bash
docker-compose exec backend pytest tests/test_schemas/test_query.py -v
```

**Step 4: Commit**

```bash
git add backend/app/schemas/query.py backend/tests/test_schemas/
git commit -m "feat(query): add ComposedQuery schema"
```

---

### Task 2.2: Intent Parser Service

**Files:**
- Create: `backend/app/services/intent_parser.py`
- Test: `backend/tests/test_services/test_intent_parser.py`

**Step 1: Write failing test**

```python
# backend/tests/test_services/test_intent_parser.py
import pytest
from app.services.intent_parser import IntentParser

def test_parse_structured_query():
    parser = IntentParser()
    result = parser.parse({
        "entity": "symbol:graph_service.get_project",
        "context": ["dependencies", "callers"],
        "depth": 2
    })

    assert result.entities[0].type == "symbol"
    assert "dependencies" in [r.type for r in result.relationships]

def test_parse_natural_language():
    parser = IntentParser()
    result = parser.parse("Show me all services with health below 100%")

    assert result.entities[0].type == "service"
    assert any(f.field == "health" for f in result.filters)
```

**Step 2: Implement IntentParser**

```python
# backend/app/services/intent_parser.py
import re
from typing import Union
from app.schemas.query import ComposedQuery, EntitySelector, Filter, RelationshipSpec

class IntentParser:
    """Parse structured or natural language queries into ComposedQuery."""

    # NL patterns for entity types
    ENTITY_PATTERNS = {
        "service": r"\bservices?\b",
        "symbol": r"\bfunctions?\b|\bsymbols?\b|\bmethods?\b",
        "file": r"\bfiles?\b",
        "project": r"\bprojects?\b",
    }

    # NL patterns for filters
    FILTER_PATTERNS = [
        (r"health\s*(below|under|<)\s*(\d+)", "health", "lt"),
        (r"health\s*(above|over|>)\s*(\d+)", "health", "gt"),
        (r"status\s*=\s*(\w+)", "status", "eq"),
    ]

    def parse(self, query: Union[dict, str]) -> ComposedQuery:
        if isinstance(query, dict):
            return self._parse_structured(query)
        return self._parse_natural_language(query)

    def _parse_structured(self, query: dict) -> ComposedQuery:
        entities = []
        relationships = []

        # Parse entity reference
        if "entity" in query:
            entity_ref = query["entity"]
            entity_type, entity_id = entity_ref.split(":", 1) if ":" in entity_ref else (entity_ref, None)
            entities.append(EntitySelector(
                type=entity_type,
                scope=f"entity:{entity_id}" if entity_id else None
            ))

        # Parse context as relationships
        for ctx in query.get("context", []):
            if ctx in ("dependencies", "callers", "imports"):
                relationships.append(RelationshipSpec(
                    type=ctx.rstrip("s"),  # callers -> caller
                    direction="inbound" if ctx == "callers" else "outbound",
                    depth=query.get("depth", 1)
                ))

        return ComposedQuery(entities=entities, relationships=relationships)

    def _parse_natural_language(self, query: str) -> ComposedQuery:
        entities = []
        filters = []

        # Detect entity types
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            if re.search(pattern, query, re.IGNORECASE):
                entities.append(EntitySelector(type=entity_type))
                break

        # Detect filters
        for pattern, field, operator in self.FILTER_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = match.group(2) if len(match.groups()) > 1 else match.group(1)
                filters.append(Filter(field=field, operator=operator, value=int(value) if value.isdigit() else value))

        return ComposedQuery(entities=entities or [EntitySelector(type="any")], filters=filters or None)
```

**Step 3: Run test**

```bash
docker-compose exec backend pytest tests/test_services/test_intent_parser.py -v
```

**Step 4: Commit**

```bash
git add backend/app/services/intent_parser.py backend/tests/test_services/
git commit -m "feat(query): add IntentParser service"
```

---

### Task 2.3: Query Execution Service

**Files:**
- Create: `backend/app/services/query_executor.py`
- Test: `backend/tests/test_services/test_query_executor.py`

**Step 1: Write failing test**

```python
# backend/tests/test_services/test_query_executor.py
import pytest
from app.services.query_executor import QueryExecutor
from app.schemas.query import ComposedQuery, EntitySelector

def test_execute_symbol_query(db_session, sample_graph_data):
    executor = QueryExecutor(db_session)
    query = ComposedQuery(
        entities=[EntitySelector(type="symbol", scope="project:proj123")]
    )

    result = executor.execute(query)

    assert "entities" in result
    assert "relationships" in result
    assert len(result["entities"]) > 0
```

**Step 2: Implement QueryExecutor**

```python
# backend/app/services/query_executor.py
from sqlalchemy.orm import Session
from app.schemas.query import ComposedQuery
from app.models.graph import GraphSymbol, GraphFile, GraphService, GraphDependency
from typing import Dict, Any, List

class QueryExecutor:
    """Execute ComposedQuery against the graph database."""

    ENTITY_MODEL_MAP = {
        "symbol": GraphSymbol,
        "file": GraphFile,
        "service": GraphService,
    }

    def __init__(self, db: Session):
        self.db = db

    def execute(self, query: ComposedQuery) -> Dict[str, Any]:
        entities = []
        relationships = []

        for selector in query.entities:
            model = self.ENTITY_MODEL_MAP.get(selector.type)
            if not model:
                continue

            db_query = self.db.query(model)

            # Apply scope
            if selector.scope and selector.scope.startswith("project:"):
                project_id = selector.scope.split(":")[1]
                db_query = db_query.filter(model.project_id == project_id)

            # Apply filters
            if query.filters:
                for f in query.filters:
                    if hasattr(model, f.field):
                        col = getattr(model, f.field)
                        if f.operator == "lt":
                            db_query = db_query.filter(col < f.value)
                        elif f.operator == "gt":
                            db_query = db_query.filter(col > f.value)
                        elif f.operator == "eq":
                            db_query = db_query.filter(col == f.value)

            entities.extend([self._serialize_entity(e) for e in db_query.limit(100).all()])

        # Fetch relationships if requested
        if query.relationships and entities:
            entity_ids = [e["id"] for e in entities]
            for rel_spec in query.relationships:
                rels = self._fetch_relationships(entity_ids, rel_spec)
                relationships.extend(rels)

        return {"entities": entities, "relationships": relationships}

    def _serialize_entity(self, entity) -> dict:
        return {
            "id": str(entity.id),
            "type": entity.__tablename__.replace("graph_", "").rstrip("s"),
            "label": getattr(entity, "name", getattr(entity, "path", str(entity.id))),
            "metadata": getattr(entity, "metadata", {}) or {}
        }

    def _fetch_relationships(self, entity_ids: List[str], rel_spec) -> List[dict]:
        # Simplified - would need more logic for different relationship types
        deps = self.db.query(GraphDependency).filter(
            GraphDependency.source_symbol_id.in_(entity_ids)
        ).limit(100).all()

        return [
            {"source": str(d.source_symbol_id), "target": str(d.target_symbol_id), "type": d.dependency_type}
            for d in deps
        ]
```

**Step 3: Run test**

```bash
docker-compose exec backend pytest tests/test_services/test_query_executor.py -v
```

**Step 4: Commit**

```bash
git add backend/app/services/query_executor.py backend/tests/test_services/
git commit -m "feat(query): add QueryExecutor service"
```

---

### Task 2.4: Query API Endpoint

**Files:**
- Modify: `backend/app/routers/graph.py`
- Test: `backend/tests/test_routers/test_graph_query.py`

**Step 1: Write failing test**

```python
# backend/tests/test_routers/test_graph_query.py
import pytest
from fastapi.testclient import TestClient

def test_query_endpoint(client, sample_graph_data):
    response = client.post("/api/v1/graph/query", json={
        "entities": [{"type": "symbol", "scope": "project:proj123"}],
        "filters": [{"field": "name", "operator": "contains", "value": "auth"}]
    })

    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert "relationships" in data
```

**Step 2: Add endpoint**

```python
# Add to backend/app/routers/graph.py
from app.schemas.query import ComposedQuery
from app.services.query_executor import QueryExecutor

@router.post("/query")
def execute_query(
    query: ComposedQuery,
    db: Session = Depends(get_db)
):
    """Execute a composed query against the graph."""
    executor = QueryExecutor(db)
    return executor.execute(query)
```

**Step 3: Run test**

```bash
docker-compose exec backend pytest tests/test_routers/test_graph_query.py -v
```

**Step 4: Commit**

```bash
git add backend/app/routers/graph.py backend/tests/test_routers/
git commit -m "feat(api): add /query endpoint for composed queries"
```

---

### Task 2.5: Frontend QueryBar Component

**Files:**
- Modify: `frontend/src/components/Graph/QueryBar.tsx`
- Create: `frontend/src/services/queryApi.ts`
- Test: `frontend/src/components/Graph/__tests__/QueryBar.test.tsx`

**Step 1: Create query API service**

```typescript
// frontend/src/services/queryApi.ts
import { api } from './api';

export interface EntitySelector {
  type: string;
  scope?: string;
  constraints?: Record<string, any>;
}

export interface Filter {
  field: string;
  operator: 'eq' | 'ne' | 'lt' | 'gt' | 'lte' | 'gte' | 'in' | 'contains';
  value: any;
}

export interface ComposedQuery {
  entities: EntitySelector[];
  filters?: Filter[];
  relationships?: { type: string; direction: string; depth: number }[];
  presentation?: Record<string, any>;
}

export interface QueryResult {
  entities: any[];
  relationships: any[];
}

export async function executeQuery(query: ComposedQuery): Promise<QueryResult> {
  const response = await api.post('/api/v1/graph/query', query);
  return response.data;
}
```

**Step 2: Enhance QueryBar with structured query support**

```typescript
// frontend/src/components/Graph/QueryBar.tsx
import React, { useState, useCallback } from 'react';
import { executeQuery, ComposedQuery } from '../../services/queryApi';

interface QueryBarProps {
  onQueryResult: (result: any) => void;
  projectId?: string;
}

export const QueryBar: React.FC<QueryBarProps> = ({ onQueryResult, projectId }) => {
  const [queryText, setQueryText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Simple parsing - expand later
      const query: ComposedQuery = {
        entities: [{ type: 'symbol', scope: projectId ? `project:${projectId}` : undefined }],
        filters: queryText ? [{ field: 'name', operator: 'contains', value: queryText }] : undefined
      };

      const result = await executeQuery(query);
      onQueryResult(result);
    } finally {
      setIsLoading(false);
    }
  }, [queryText, projectId, onQueryResult]);

  return (
    <form onSubmit={handleSubmit} className="query-bar">
      <input
        type="text"
        value={queryText}
        onChange={(e) => setQueryText(e.target.value)}
        placeholder="Search symbols, files, services..."
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
};
```

**Step 3: Run test**

```bash
cd frontend && npm test -- --testPathPattern=QueryBar
```

**Step 4: Commit**

```bash
git add frontend/src/components/Graph/QueryBar.tsx frontend/src/services/queryApi.ts
git commit -m "feat(frontend): enhance QueryBar with composed query support"
```

---

## Phase 3: Agent Parity (Weeks 5-6)

### Task 3.1: Affordance Schema

**Files:**
- Modify: `backend/app/schemas/query.py`
- Test: `backend/tests/test_schemas/test_affordances.py`

**Step 1: Write test**

```python
# backend/tests/test_schemas/test_affordances.py
from app.schemas.query import Affordance, QueryResult

def test_affordance_schema():
    affordance = Affordance(
        action="trigger_audit",
        target={"type": "symbol", "id": "sym123"},
        description="Run security audit on this function",
        parameters={"audit_type": "security"}
    )
    assert affordance.action == "trigger_audit"
```

**Step 2: Add to schema**

```python
# Add to backend/app/schemas/query.py
from typing import Literal

class EntityRef(BaseModel):
    type: str
    id: str

class Affordance(BaseModel):
    action: Literal["trigger_audit", "create_task", "open_in_editor", "drill_down", "run_indexer"]
    target: EntityRef
    description: str
    parameters: Optional[dict] = None

class QueryResult(BaseModel):
    entities: List[dict]
    relationships: List[dict]
    affordances: Optional[List[Affordance]] = None
    summary: Optional[str] = None
```

**Step 3: Run test**

```bash
docker-compose exec backend pytest tests/test_schemas/test_affordances.py -v
```

**Step 4: Commit**

```bash
git add backend/app/schemas/query.py backend/tests/test_schemas/
git commit -m "feat(query): add Affordance schema for agent actions"
```

---

### Task 3.2: Affordance Generator

**Files:**
- Create: `backend/app/services/affordance_generator.py`
- Test: `backend/tests/test_services/test_affordance_generator.py`

**Step 1: Write failing test**

```python
# backend/tests/test_services/test_affordance_generator.py
from app.services.affordance_generator import AffordanceGenerator

def test_generates_audit_affordance_for_symbol():
    generator = AffordanceGenerator()
    entity = {"id": "sym123", "type": "symbol", "label": "validateToken"}

    affordances = generator.generate(entity)

    actions = [a.action for a in affordances]
    assert "trigger_audit" in actions
    assert "drill_down" in actions
```

**Step 2: Implement generator**

```python
# backend/app/services/affordance_generator.py
from app.schemas.query import Affordance, EntityRef
from typing import List

class AffordanceGenerator:
    """Generate available actions for entities."""

    ENTITY_AFFORDANCES = {
        "symbol": ["trigger_audit", "drill_down", "open_in_editor", "create_task"],
        "file": ["trigger_audit", "drill_down", "open_in_editor"],
        "service": ["trigger_audit", "drill_down"],
        "project": ["drill_down", "run_indexer"],
    }

    ACTION_DESCRIPTIONS = {
        "trigger_audit": "Run code analysis on this {type}",
        "drill_down": "Explore {label} in detail",
        "open_in_editor": "Open {label} in your editor",
        "create_task": "Create a task related to {label}",
        "run_indexer": "Re-index this {type}",
    }

    def generate(self, entity: dict) -> List[Affordance]:
        entity_type = entity.get("type", "unknown")
        actions = self.ENTITY_AFFORDANCES.get(entity_type, ["drill_down"])

        return [
            Affordance(
                action=action,
                target=EntityRef(type=entity_type, id=entity["id"]),
                description=self.ACTION_DESCRIPTIONS[action].format(
                    type=entity_type,
                    label=entity.get("label", entity["id"])
                )
            )
            for action in actions
        ]
```

**Step 3: Run test**

```bash
docker-compose exec backend pytest tests/test_services/test_affordance_generator.py -v
```

**Step 4: Commit**

```bash
git add backend/app/services/affordance_generator.py backend/tests/test_services/
git commit -m "feat(agent): add AffordanceGenerator for agent actions"
```

---

### Task 3.3: Integrate Affordances into Query Results

**Files:**
- Modify: `backend/app/services/query_executor.py`
- Modify: `backend/app/routers/graph.py`
- Test: `backend/tests/test_routers/test_query_affordances.py`

**Step 1: Update QueryExecutor**

```python
# Modify backend/app/services/query_executor.py
from app.services.affordance_generator import AffordanceGenerator

class QueryExecutor:
    def __init__(self, db: Session):
        self.db = db
        self.affordance_generator = AffordanceGenerator()

    def execute(self, query: ComposedQuery, include_affordances: bool = False) -> Dict[str, Any]:
        # ... existing code ...

        result = {"entities": entities, "relationships": relationships}

        if include_affordances:
            all_affordances = []
            for entity in entities[:10]:  # Limit to first 10 to avoid bloat
                all_affordances.extend(self.affordance_generator.generate(entity))
            result["affordances"] = [a.dict() for a in all_affordances]

        return result
```

**Step 2: Update endpoint**

```python
# Modify backend/app/routers/graph.py
@router.post("/query")
def execute_query(
    query: ComposedQuery,
    include_affordances: bool = Query(False, description="Include agent affordances"),
    db: Session = Depends(get_db)
):
    executor = QueryExecutor(db)
    return executor.execute(query, include_affordances=include_affordances)
```

**Step 3: Run test**

```bash
docker-compose exec backend pytest tests/test_routers/test_query_affordances.py -v
```

**Step 4: Commit**

```bash
git add backend/app/services/query_executor.py backend/app/routers/graph.py
git commit -m "feat(agent): integrate affordances into query results"
```

---

### Task 3.4: Action Execution Endpoint

**Files:**
- Create: `backend/app/routers/actions.py`
- Create: `backend/app/services/action_executor.py`
- Test: `backend/tests/test_routers/test_actions.py`

**Step 1: Write failing test**

```python
# backend/tests/test_routers/test_actions.py
def test_execute_trigger_audit_action(client, sample_symbol):
    response = client.post("/api/v1/actions/execute", json={
        "action": "trigger_audit",
        "target": {"type": "symbol", "id": str(sample_symbol.id)},
        "parameters": {"audit_type": "security"}
    })

    assert response.status_code == 200
    assert response.json()["status"] in ["queued", "completed"]
```

**Step 2: Implement action executor**

```python
# backend/app/services/action_executor.py
from app.schemas.query import Affordance
from typing import Dict, Any
import uuid

class ActionExecutor:
    """Execute actions triggered by agents or users."""

    async def execute(self, affordance: Affordance) -> Dict[str, Any]:
        handler = getattr(self, f"_handle_{affordance.action}", None)
        if not handler:
            return {"status": "error", "message": f"Unknown action: {affordance.action}"}

        return await handler(affordance)

    async def _handle_trigger_audit(self, affordance: Affordance) -> Dict[str, Any]:
        # Queue audit job - would integrate with actual audit service
        job_id = str(uuid.uuid4())
        return {
            "status": "queued",
            "job_id": job_id,
            "message": f"Audit queued for {affordance.target.type} {affordance.target.id}"
        }

    async def _handle_drill_down(self, affordance: Affordance) -> Dict[str, Any]:
        # Return query for drilling down
        return {
            "status": "completed",
            "redirect_query": {
                "entities": [{"type": affordance.target.type, "scope": f"entity:{affordance.target.id}"}],
                "relationships": [{"type": "all", "direction": "both", "depth": 1}]
            }
        }
```

**Step 3: Create router**

```python
# backend/app/routers/actions.py
from fastapi import APIRouter, Depends
from app.schemas.query import Affordance
from app.services.action_executor import ActionExecutor

router = APIRouter(prefix="/api/v1/actions", tags=["actions"])

@router.post("/execute")
async def execute_action(affordance: Affordance):
    executor = ActionExecutor()
    return await executor.execute(affordance)
```

**Step 4: Register router in main.py**

```python
# Add to backend/app/main.py
from app.routers import actions
app.include_router(actions.router)
```

**Step 5: Run test**

```bash
docker-compose exec backend pytest tests/test_routers/test_actions.py -v
```

**Step 6: Commit**

```bash
git add backend/app/routers/actions.py backend/app/services/action_executor.py backend/app/main.py
git commit -m "feat(agent): add action execution endpoint"
```

---

## Phase 4: Advanced Features (Weeks 7-8)

### Task 4.1: Temporal Query Support

**Files:**
- Modify: `backend/app/services/query_executor.py`
- Modify: `backend/app/schemas/query.py`
- Test: `backend/tests/test_services/test_temporal_queries.py`

*(Implementation follows same TDD pattern)*

---

### Task 4.2: Semantic Search Integration

**Files:**
- Create: `backend/app/services/semantic_search.py`
- Test: `backend/tests/test_services/test_semantic_search.py`

*(Integrates with existing KnowledgeBeast/RAG service)*

---

### Task 4.3: Computed Properties

**Files:**
- Create: `backend/app/services/computed_properties.py`
- Test: `backend/tests/test_services/test_computed_properties.py`

*(Adds symbolCount, allDependencies, projectHealth computed at query time)*

---

## Verification Checklist

After each phase, verify:

- [ ] All tests pass: `make test`
- [ ] No linting errors: `make lint`
- [ ] API docs updated: Check `/docs` endpoint
- [ ] WebSocket connections stable: Manual test with browser dev tools
- [ ] Cross-project queries work: Test with 2+ projects in database

---

## Rollback Plan

Each task is independently committable. To rollback:

```bash
git revert <commit-hash>
docker-compose exec backend alembic downgrade -1  # If migration involved
docker-compose restart
```

---

## Dependencies

**Python packages to add:**
```
# Already in requirements.txt or add:
# websockets (if not using Starlette's built-in)
```

**No new npm packages required** - React Flow and existing deps sufficient.

---

## Success Metrics

1. **Query latency**: < 200ms for ecosystem-wide queries (up to 10 projects)
2. **WebSocket reliability**: < 1% dropped connections over 24h
3. **Agent adoption**: Affordances used in 50%+ of agent interactions
4. **Cross-project queries**: Support 100+ cross-project links without degradation
