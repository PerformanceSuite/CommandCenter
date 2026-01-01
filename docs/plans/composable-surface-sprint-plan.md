# Composable Surface Sprint Plan

**Parent Design:** [`2025-01-01-composable-commandcenter-design.md`](./2025-01-01-composable-commandcenter-design.md)
**Roadmap Context:** Phase 7-8 of the [12-Phase Comprehensive Roadmap](./2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md)
**Last Updated:** 2025-12-31

---

## Overview

This document tracks the sprint breakdown for implementing the **Composable CommandCenter** unified operating surface (VISLZR). The goal is to transform CommandCenter from isolated project containers into a single composable surface where users and agents can query, visualize, and act on any entity at any zoom level.

### Vision

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPOSABLE SURFACE                        │
│  Query Layer → Primitive Composer → Rendered View           │
│                                                              │
│  • AI agents are primary consumers (99% of traffic)         │
│  • UI is a query box, not static pages                      │
│  • Project boundary = zoom level, not container             │
└─────────────────────────────────────────────────────────────┘
```

---

## Sprint Progress

| Sprint | Name | Status | Dates | Plan |
|--------|------|--------|-------|------|
| 1 | Foundation | ✅ Complete | Pre-Dec 2025 | (Undocumented) |
| 2 | Query Layer | ✅ Complete | Pre-Dec 2025 | (Undocumented) |
| 3 | Agent Parity | ✅ Complete | Dec 31 - Jan 1 | [Sprint 3 Completion](./2025-12-31-sprint3-completion.md) |
| 4 | Real-time Subscriptions | 📋 Planned | Jan 2026 | [Sprint 4 Plan](./2026-01-01-sprint4-realtime-subscriptions.md) |
| 5 | Advanced Features | 📋 Future | TBD | — |
| 6 | Document Intelligence | 🔄 In Progress | Jan 2026 | [Doc Intel Agents](./2026-01-01-document-intelligence-agents.md) |

---

## Sprint Details

### Sprint 1: Foundation ✅

**Goal:** Establish core data infrastructure and basic visualization

**Inferred Deliverables** (based on design doc Phase 1):
- [x] Cross-project links table (`cross_project_links`)
- [x] Federation query infrastructure
- [x] Basic primitive library (Node, Edge, GraphCanvas)
- [x] Graph API endpoints (`/api/v1/graph/*`)
- [x] React Flow integration for visualization

**Key Files Created:**
- `backend/app/models/graph.py`
- `backend/app/services/graph_service.py`
- `backend/app/routers/graph.py`
- `frontend/src/services/graphApi.ts`
- `frontend/src/components/Graph/GraphCanvas.tsx`
- `frontend/src/types/graph.ts`

---

### Sprint 2: Query Layer ✅

**Goal:** Enable structured queries and URL-as-query routing

**Inferred Deliverables** (based on design doc Phase 2):
- [x] Intent parser (structured queries)
- [x] Composition engine
- [x] URL-as-query routing
- [x] Query presets infrastructure
- [x] Graph search endpoints

**Key Files Created:**
- `frontend/src/hooks/useGraph.ts` (useProjectGraph, useGraphSearch, useFederationQuery)
- `frontend/src/components/Graph/QueryBar.tsx`
- `backend/app/schemas/graph.py` (GraphSearchRequest, etc.)

---

### Sprint 3: Agent Parity ✅

**Goal:** Enable agents to query, save, and execute through the same APIs as UI

**Documented:** [`2025-12-31-sprint3-completion.md`](./2025-12-31-sprint3-completion.md)

**Deliverables:**
- [x] Agent Query Endpoint - Agents can query graph with affordances
- [x] Recipe Persistence - Save/load query presets
- [x] Action Execution + NATS - Execute actions via API with event emission
- [x] Frontend Recipe UI - Save/load preset dropdown in QueryBar
- [x] Affordance Wiring - `useAffordances` hook for action execution
- [x] Agent Graph Integration - `AgentExecution` model tracks agent runs
- [x] Composable Entity Types - Added `persona`, `workflow`, `execution` types

**Key Files Created:**
- `frontend/src/services/presetApi.ts`
- `frontend/src/services/actionApi.ts`
- `frontend/src/hooks/usePresets.ts`
- `frontend/src/hooks/useAffordances.ts`
- `backend/app/models/agent_execution.py`

**Database Migration:** `fd12cd853b12` - Added `agent_executions`, `agent_personas` tables

**Cost:** $4.58 (parallel sandbox agents)

---

### Sprint 4: Real-time Subscriptions 📋

**Goal:** Enable live graph updates via SSE bridged from NATS

**Documented:** [`2026-01-01-sprint4-realtime-subscriptions.md`](./2026-01-01-sprint4-realtime-subscriptions.md)

**Execution Plan:** [`2026-01-01-sprint4-execution-plan.md`](./2026-01-01-sprint4-execution-plan.md)

**Deliverables:**
- [ ] Backend SSE Endpoint - `GET /api/v1/events/stream`
- [ ] Graph Event Publisher - NATS events on graph mutations
- [ ] Frontend SSE Hook - `useGraphSubscription()`
- [ ] Graph State Manager - `useRealtimeGraph()` with delta updates
- [ ] UI Integration - Live updates in GraphPage
- [ ] Subscription Manager - Connection tracking and metrics

**Architecture Decision:** SSE over WebSocket (one-way, simpler, auto-reconnect)

**Reference Pattern:** `hub/backend/app/streaming/sse.py`

---

### Sprint 5: Advanced Features 📋

**Goal:** Temporal queries, semantic search, computed properties

**Planned Deliverables** (from design doc Phase 4):
- [ ] Temporal queries (`asOf`, `changes` over time range)
- [ ] Semantic search (vector embeddings for symbols/files)
- [ ] Computed properties (symbolCount, complexity, projectHealth)
- [ ] NLP intent parser (natural language → structured query)

**Dependencies:**
- Sprint 4 complete (real-time infrastructure)
- Vector DB integration (pgvector or dedicated)

---

### Sprint 6: Document Intelligence 🔄

**Goal:** Extract structured knowledge from documentation corpus using specialized agents

**Documented:** [`2026-01-01-document-intelligence-agents.md`](./2026-01-01-document-intelligence-agents.md)

**Phase 6a: Extraction (Current)**
- [x] Design 5 agent personas (concept-extractor, requirement-miner, relationship-mapper, staleness-detector, classifier)
- [x] Pilot extraction on 10 documents (37 concepts, 78 requirements extracted)
- [ ] Create consolidated concept database schema
- [ ] Run agents on remaining ~144 documents
- [ ] Generate master concept/requirement database

**Phase 6b: Integration**
- [ ] Add `concept`, `requirement`, `document` entity types to Graph-Service
- [ ] Index extracted content in KnowledgeBeast
- [ ] Enable VISLZR queries like "show concepts from Veria.md"
- [ ] Build document relationship visualization

**Phase 6c: Affordances**
- [ ] "Find related concepts" action
- [ ] "Show requirement chain" action
- [ ] "Visualize document relationships" action
- [ ] "List stale documents" query

**Key Files:**
- `docs/plans/2026-01-01-document-intelligence-agents.md` - Agent personas
- `docs/cleanup/2026-01-01-document-extraction-*.md` - Extraction results
- `docs/plans/2026-01-01-custom-model-training-roadmap.md` - Future: custom models

**Progress:** 10/154 documents analyzed (6.5%)

---

## Architecture Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPOSABLE SURFACE (VISLZR)                   │
│  Query Layer → Primitive Composer → Rendered View               │
└─────────────────────────────────────────────────────────────────┘
                              ↕ SSE (Sprint 4)
┌─────────────────────────────────────────────────────────────────┐
│                         API GATEWAY                              │
│  REST + Subscriptions + Actions                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                     GRAPH-SERVICE                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ Federation  │ │   Action    │ │Subscription │               │
│  │   Queries   │ │  Executor   │ │  Manager    │               │
│  │  Sprint 1   │ │  Sprint 3   │ │  Sprint 4   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│  PostgreSQL (Graph Tables) + NATS (Real-Time Events)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Entity Types

Extended through sprints to support full composability:

| Type | Added In | Description |
|------|----------|-------------|
| `repo` | Sprint 1 | Git repository |
| `file` | Sprint 1 | Source file |
| `symbol` | Sprint 1 | Function, class, variable |
| `service` | Sprint 1 | Microservice/container |
| `task` | Sprint 1 | Research/work item |
| `spec` | Sprint 1 | Specification document |
| `project` | Sprint 1 | CommandCenter project |
| `persona` | Sprint 3 | Agent persona definition |
| `workflow` | Sprint 3 | Agent workflow/DAG |
| `execution` | Sprint 3 | Agent execution instance |
| `concept` | Sprint 6 | Extracted business/technical concept |
| `requirement` | Sprint 6 | Extracted requirement (must/should/could) |
| `document` | Sprint 6 | Analyzed documentation file |

---

## Key Patterns

### SSE Pattern (Sprint 4)

Reference implementation exists at `hub/backend/app/streaming/sse.py`:
- NATS → HTTP SSE bridge
- 30-second keepalives
- Subject filtering
- Graceful cleanup

### Hook Pattern

Frontend hooks follow consistent patterns:
- `useProjectGraph(projectId)` - Fetch graph data
- `useGraphSearch()` - Search entities
- `useGraphSubscription(projectId, onEvent)` - Real-time updates (Sprint 4)
- `useRealtimeGraph(projectId)` - Graph with live updates (Sprint 4)

### Event Subjects

NATS subjects for graph events:
```
graph.node.created   → {project_id, node_type, node_id, label}
graph.node.updated   → {project_id, node_type, node_id, changes}
graph.node.deleted   → {project_id, node_type, node_id}
graph.edge.created   → {project_id, from_node, to_node, type}
graph.edge.deleted   → {project_id, from_node, to_node}
graph.invalidated    → {project_id, reason}
```

---

## Success Criteria

**Composable Surface Complete When:**
- [ ] Any query returns consistent view (human or agent)
- [ ] Real-time updates flow from backend to frontend
- [ ] Agent can: query → receive affordances → execute action → see result
- [ ] Cross-project queries work seamlessly
- [ ] URL encodes full query state (shareable/bookmarkable)

**Document Intelligence Complete When:**
- [ ] All 154 documents analyzed and concepts extracted
- [ ] Consolidated concept database queryable via VISLZR
- [ ] Requirements traceable to source documents
- [ ] Stale document detection automated

---

## References

- [Composable Design Doc](./2025-01-01-composable-commandcenter-design.md) - Full architecture
- [Phase 7-8 Blueprint](../../hub-prototype/phase_7_8_graph_service_vislzr_integration_plan_command_center.md) - Original VISLZR plan
- [Comprehensive Roadmap](./2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md) - 12-phase overview
- [Hub SSE Pattern](../../hub/backend/app/streaming/sse.py) - Reference implementation
