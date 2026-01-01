# Sprint 4 Execution Plan: Real-time Subscriptions

**Created:** 2025-12-31
**Source:** `docs/plans/2026-01-01-sprint4-realtime-subscriptions.md`

## Execution Order

Tasks are ordered by dependency - each builds on the previous:

```
Task 1 (SSE Endpoint) → Task 2 (Event Publisher) → Task 6 (Subscription Manager)
                                                          ↓
Task 3 (SSE Hook) ←─────────────────────────────────────────
         ↓
Task 4 (State Manager) → Task 5 (UI Integration)
```

---

## Task 1: Backend SSE Endpoint

**Goal:** Create SSE endpoint that bridges NATS events to HTTP stream

**Reference Pattern:** `hub/backend/app/streaming/sse.py`

### Steps

1. **Create router file** `backend/app/routers/sse.py`
   - Import from `sse_starlette` (add to requirements.txt)
   - Create `GET /api/v1/events/stream` endpoint
   - Accept query params: `project_id` (required), `subjects` (optional)

2. **Implement SSE generator**
   ```python
   async def event_generator(project_id: int, subjects: list[str]):
       # Connect to NATS
       # Subscribe to subjects with project_id filter
       # Yield SSE events
       # Send keepalive every 30s
   ```

3. **Register router in `main.py`**
   ```python
   from app.routers import sse
   app.include_router(sse.router, prefix="/api/v1/events", tags=["events"])
   ```

4. **Add dependencies**
   ```bash
   # backend/requirements.txt
   sse-starlette>=1.6.0
   ```

### Verification
```bash
curl -N "http://localhost:8000/api/v1/events/stream?project_id=1"
# Should see: event: connected\ndata: {"project_id": 1}
```

### Files to Create/Modify
- `backend/app/routers/sse.py` (new)
- `backend/app/main.py` (add router)
- `backend/requirements.txt` (add sse-starlette)

---

## Task 2: Graph Event Publisher

**Goal:** Emit NATS events when graph entities change

**Reference:** `hub/backend/app/events/service.py` for NATS publishing

### Steps

1. **Create event schemas** `backend/app/schemas/graph_events.py`
   ```python
   class GraphNodeEvent(BaseModel):
       event_type: Literal["created", "updated", "deleted"]
       project_id: int
       node_type: str
       node_id: str
       label: str | None = None
       changes: dict | None = None  # For updates

   class GraphEdgeEvent(BaseModel):
       event_type: Literal["created", "deleted"]
       project_id: int
       from_node: str
       to_node: str
       edge_type: str

   class GraphInvalidatedEvent(BaseModel):
       project_id: int
       reason: str
   ```

2. **Add event publisher to graph service** `backend/app/services/graph_service.py`
   ```python
   async def publish_node_event(event: GraphNodeEvent):
       subject = f"graph.node.{event.event_type}"
       await nats_client.publish(subject, event.model_dump_json())
   ```

3. **Inject publishing into CRUD operations**
   - After node creation → `publish_node_event("created", ...)`
   - After node update → `publish_node_event("updated", ...)`
   - After node deletion → `publish_node_event("deleted", ...)`
   - Same pattern for edges

### Event Subjects
| Operation | Subject | Payload |
|-----------|---------|---------|
| Node created | `graph.node.created` | `{project_id, node_type, node_id, label}` |
| Node updated | `graph.node.updated` | `{project_id, node_type, node_id, changes}` |
| Node deleted | `graph.node.deleted` | `{project_id, node_type, node_id}` |
| Edge created | `graph.edge.created` | `{project_id, from_node, to_node, type}` |
| Edge deleted | `graph.edge.deleted` | `{project_id, from_node, to_node}` |
| Bulk update | `graph.invalidated` | `{project_id, reason}` |

### Files to Create/Modify
- `backend/app/schemas/graph_events.py` (new)
- `backend/app/services/graph_service.py` (modify)

---

## Task 3: Frontend SSE Hook

**Goal:** Create hook that connects to SSE endpoint and delivers typed events

**Reference Pattern:** `frontend/src/hooks/useWebSocket.ts`

### Steps

1. **Create SSE hook** `frontend/src/hooks/useGraphSubscription.ts`
   ```typescript
   interface UseGraphSubscriptionOptions {
     onEvent: (event: GraphEvent) => void;
     onError?: (error: Error) => void;
     subjects?: string[];
   }

   export function useGraphSubscription(
     projectId: number | null,
     options: UseGraphSubscriptionOptions
   ) {
     // Create EventSource connection
     // Parse SSE events to typed GraphEvent
     // Handle reconnection (EventSource does this automatically)
     // Cleanup on unmount
   }
   ```

2. **Create event types** `frontend/src/types/graphEvents.ts`
   ```typescript
   export type GraphEventType =
     | 'node.created' | 'node.updated' | 'node.deleted'
     | 'edge.created' | 'edge.deleted'
     | 'invalidated';

   export interface GraphNodeEvent {
     type: 'node.created' | 'node.updated' | 'node.deleted';
     project_id: number;
     node_type: string;
     node_id: string;
     label?: string;
     changes?: Record<string, unknown>;
   }

   export interface GraphEdgeEvent {
     type: 'edge.created' | 'edge.deleted';
     project_id: number;
     from_node: string;
     to_node: string;
     edge_type: string;
   }

   export interface GraphInvalidatedEvent {
     type: 'invalidated';
     project_id: number;
     reason: string;
   }

   export type GraphEvent = GraphNodeEvent | GraphEdgeEvent | GraphInvalidatedEvent;
   ```

3. **Return connection state**
   ```typescript
   return {
     isConnected: boolean;
     lastEvent: GraphEvent | null;
     error: Error | null;
     reconnect: () => void;
   };
   ```

### Files to Create
- `frontend/src/hooks/useGraphSubscription.ts` (new)
- `frontend/src/types/graphEvents.ts` (new)

---

## Task 4: Graph State Manager

**Goal:** Create hook that manages graph state with real-time updates

**Reference:** `frontend/src/hooks/useGraph.ts` (`useProjectGraph`)

### Steps

1. **Create state manager hook** `frontend/src/hooks/useRealtimeGraph.ts`
   ```typescript
   export function useRealtimeGraph(projectId: number | null) {
     // Initialize state from useProjectGraph
     const { data: initialData, isLoading, error, refetch } = useProjectGraph(projectId);

     // Local state for live updates
     const [nodes, setNodes] = useState<GraphNode[]>([]);
     const [edges, setEdges] = useState<GraphEdge[]>([]);
     const [isStale, setIsStale] = useState(false);

     // Handle SSE events
     const handleEvent = useCallback((event: GraphEvent) => {
       switch (event.type) {
         case 'node.created':
           setNodes(prev => [...prev, eventToNode(event)]);
           break;
         case 'node.updated':
           setNodes(prev => prev.map(n =>
             n.id === event.node_id ? applyChanges(n, event.changes) : n
           ));
           break;
         case 'node.deleted':
           setNodes(prev => prev.filter(n => n.id !== event.node_id));
           break;
         // ... similar for edges
         case 'invalidated':
           setIsStale(true);
           break;
       }
     }, []);

     // Connect to SSE
     useGraphSubscription(projectId, { onEvent: handleEvent });

     return {
       nodes,
       edges,
       isLoading,
       error,
       isStale,
       refresh: refetch,
     };
   }
   ```

2. **Add helper functions**
   - `eventToNode()`: Convert event payload to GraphNode
   - `eventToEdge()`: Convert event payload to GraphEdge
   - `applyChanges()`: Apply partial updates to existing nodes

### Files to Create
- `frontend/src/hooks/useRealtimeGraph.ts` (new)

---

## Task 5: UI Integration

**Goal:** Integrate real-time graph in the Graph page

**Reference:** `frontend/src/components/Graph/GraphCanvas.tsx`

### Steps

1. **Update GraphPage to use real-time hook**
   - Replace `useProjectGraph` with `useRealtimeGraph`
   - Pass nodes/edges to GraphCanvas

2. **Add stale state indicator**
   ```tsx
   {isStale && (
     <div className="stale-banner">
       Graph data may be outdated.
       <button onClick={refresh}>Refresh</button>
     </div>
   )}
   ```

3. **Optional: Add toast notifications**
   ```tsx
   useGraphSubscription(projectId, {
     onEvent: (event) => {
       handleEvent(event);
       if (event.type === 'node.created') {
         toast.info(`New ${event.node_type}: ${event.label}`);
       }
     }
   });
   ```

4. **Add connection status indicator**
   ```tsx
   <div className="connection-status">
     {isConnected ? '🟢 Live' : '🔴 Disconnected'}
   </div>
   ```

### Files to Modify
- `frontend/src/pages/GraphPage.tsx` (or equivalent graph view)
- Potentially create `frontend/src/components/Graph/ConnectionStatus.tsx`

---

## Task 6: Subscription Manager

**Goal:** Track active SSE connections for monitoring

### Steps

1. **Create subscription manager** `backend/app/services/subscription_manager.py`
   ```python
   class SubscriptionManager:
       def __init__(self):
           self._connections: dict[str, ConnectionInfo] = {}
           self._metrics = SubscriptionMetrics()

       async def register(self, connection_id: str, project_id: int):
           self._connections[connection_id] = ConnectionInfo(
               project_id=project_id,
               connected_at=datetime.utcnow()
           )
           self._metrics.active_connections += 1

       async def unregister(self, connection_id: str):
           if connection_id in self._connections:
               del self._connections[connection_id]
               self._metrics.active_connections -= 1

       async def record_event(self, connection_id: str):
           self._metrics.events_sent += 1

       def get_metrics(self) -> SubscriptionMetrics:
           return self._metrics
   ```

2. **Integrate with SSE endpoint**
   - Register connection on connect
   - Unregister on disconnect
   - Track events sent

3. **Add metrics endpoint** (optional)
   ```python
   @router.get("/metrics")
   async def get_subscription_metrics():
       return subscription_manager.get_metrics()
   ```

### Files to Create/Modify
- `backend/app/services/subscription_manager.py` (new)
- `backend/app/routers/sse.py` (integrate manager)

---

## Commit Sequence

Execute in order, each commit is a working increment:

```
1. feat(sse): add SSE endpoint for graph events
   - backend/app/routers/sse.py
   - backend/app/main.py
   - backend/requirements.txt

2. feat(graph): emit NATS events on graph mutations
   - backend/app/schemas/graph_events.py
   - backend/app/services/graph_service.py

3. feat(frontend): add useGraphSubscription hook
   - frontend/src/hooks/useGraphSubscription.ts
   - frontend/src/types/graphEvents.ts

4. feat(frontend): add useRealtimeGraph state manager
   - frontend/src/hooks/useRealtimeGraph.ts

5. feat(ui): integrate real-time updates in graph page
   - frontend/src/pages/GraphPage.tsx
   - frontend/src/components/Graph/ConnectionStatus.tsx

6. feat(sse): add subscription manager for monitoring
   - backend/app/services/subscription_manager.py
   - backend/app/routers/sse.py (update)
```

---

## Testing Strategy

### Backend Tests
```python
# test_sse_endpoint.py
async def test_sse_connection():
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", "/api/v1/events/stream?project_id=1") as r:
            # Verify connected event
            line = await r.aiter_lines().__anext__()
            assert "connected" in line

# test_graph_events.py
async def test_node_event_published():
    # Create node via API
    # Verify NATS event received
```

### Frontend Tests
```typescript
// useGraphSubscription.test.ts
it('connects to SSE endpoint', () => {
  const { result } = renderHook(() =>
    useGraphSubscription(1, { onEvent: jest.fn() })
  );
  expect(result.current.isConnected).toBe(true);
});

// useRealtimeGraph.test.ts
it('applies node created event', () => {
  // Simulate SSE event
  // Verify node appears in state
});
```

### E2E Test
```bash
# Terminal 1: Connect to SSE
curl -N "http://localhost:8000/api/v1/events/stream?project_id=1"

# Terminal 2: Create a node via API
curl -X POST "http://localhost:8000/api/v1/graph/nodes" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1, "type": "file", "label": "test.py"}'

# Terminal 1 should show:
# event: graph.node.created
# data: {"project_id": 1, "node_type": "file", "node_id": "...", "label": "test.py"}
```

---

## Definition of Done

- [ ] SSE endpoint responds with `event: connected` on connection
- [ ] Keepalive messages sent every 30 seconds
- [ ] Graph mutations trigger NATS events
- [ ] Frontend receives and applies incremental updates
- [ ] Stale indicator shows when `graph.invalidated` received
- [ ] Connection status visible in UI
- [ ] All tests passing
- [ ] Documentation updated
