# Sprint 4: Real-time Subscriptions

**Status:** In Progress
**Start Date:** January 1, 2026
**Approach:** SSE with delta updates (individual node/edge changes applied incrementally)

## Overview

Enable real-time graph updates via Server-Sent Events (SSE) bridged from NATS. The frontend will receive live updates when graph entities change, applying them incrementally for smooth UX.

## Architecture Decision: SSE over WebSocket

**Why SSE?**
- Graph updates are server→client (one-way) - SSE is designed for this
- Works through HTTP proxies and load balancers without special config
- Simpler implementation - no connection handshake protocol
- Auto-reconnect built into EventSource API
- Hub already has SSE pattern we can follow (`hub/backend/app/streaming/sse.py`)

**WebSocket reserved for:**
- Future bidirectional needs (e.g., collaborative editing)
- `useWebSocket.ts` hook already exists for this

## Tasks

| # | Task | Files | Status |
|---|------|-------|--------|
| 1 | Backend SSE Endpoint | `backend/app/routers/sse.py`, `main.py` | ✅ |
| 2 | Graph Event Publisher | `backend/app/services/graph_service.py`, `schemas/graph_events.py` | ✅ |
| 3 | Frontend SSE Hook | `frontend/src/hooks/useGraphSubscription.ts`, `types/graphEvents.ts` | ✅ |
| 4 | Graph State Manager | `frontend/src/hooks/useRealtimeGraph.ts` | ❌ |
| 5 | UI Integration | `frontend/src/pages/GraphPage.tsx` | ❌ |
| 6 | Subscription Manager | `backend/app/services/subscription_manager.py` | ❌ |

## Task Details

### Task 1: Backend SSE Endpoint

**Endpoint:** `GET /api/v1/events/stream`

**Query params:**
- `project_id` (required) - Filter events by project
- `subjects` (optional) - Comma-separated NATS subject patterns (default: `graph.*`)

**Features:**
- Bridge NATS events to HTTP SSE stream
- Project-scoped filtering
- 30-second keepalive messages
- Graceful cleanup on disconnect

### Task 2: Graph Event Publisher

**Events to emit:**

| Operation | Subject | Payload |
|-----------|---------|---------|
| Node created | `graph.node.created` | `{project_id, node_type, node_id, label}` |
| Node updated | `graph.node.updated` | `{project_id, node_type, node_id, changes}` |
| Node deleted | `graph.node.deleted` | `{project_id, node_type, node_id}` |
| Edge created | `graph.edge.created` | `{project_id, from_node, to_node, type}` |
| Edge deleted | `graph.edge.deleted` | `{project_id, from_node, to_node}` |
| Bulk update | `graph.invalidated` | `{project_id, reason}` |

### Task 3: Frontend SSE Hook

**Hook:** `useGraphSubscription(projectId, onEvent)`

- Connect to SSE endpoint
- Parse incoming events
- Call handler with typed events
- Auto-reconnect on disconnect
- Cleanup on unmount

### Task 4: Graph State Manager

**Hook:** `useRealtimeGraph(projectId)`

- Initialize from HTTP fetch
- Apply delta updates from SSE
- Track stale state for bulk invalidations
- Expose refresh function

### Task 5: UI Integration

- Replace `useProjectGraph` with `useRealtimeGraph`
- Show stale indicator when needed
- Auto-apply incremental updates
- Optional: Toast notifications for changes

### Task 6: Subscription Manager

- Track active SSE connections by project
- Metrics: active_connections, events_sent
- Graceful cleanup on disconnect
- Rate limiting (optional)

## Verification

```bash
# Test SSE endpoint
curl -N "http://localhost:8000/api/v1/events/stream?project_id=1"

# Should see:
# event: connected
# data: {"project_id": 1}
#
# : keepalive (every 30s)
```

## Commit Plan

1. `feat(sse): add SSE endpoint for graph events`
2. `feat(graph): emit NATS events on graph mutations`
3. `feat(frontend): add useGraphSubscription hook`
4. `feat(frontend): add useRealtimeGraph state manager`
5. `feat(ui): integrate real-time updates in graph page`
6. `feat(sse): add subscription manager for monitoring`
