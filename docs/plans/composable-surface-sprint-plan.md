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
| 4 | Real-time Subscriptions | ✅ Complete | Dec 31, 2025 | [Sprint 4 Plan](./2026-01-01-sprint4-realtime-subscriptions.md) |
| 5 | Advanced Features | 📋 Future | TBD | — |
| 6 | Document Intelligence | 🔄 In Progress | Jan 2026 | [Doc Intel Agents](./2026-01-01-document-intelligence-agents.md) |
| 7 | Agent Observability | 📋 Future | Q1 2026 | — |
| 8 | Automated QA Pipeline | 📋 Future | Q1 2026 | — |
| 9 | Task Inbox | 📋 Future | Q1 2026 | — |

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

### Sprint 4: Real-time Subscriptions ✅

**Goal:** Enable live graph updates via SSE bridged from NATS

**Documented:** [`2026-01-01-sprint4-realtime-subscriptions.md`](./2026-01-01-sprint4-realtime-subscriptions.md)

**Execution Plan:** [`2026-01-01-sprint4-execution-plan.md`](./2026-01-01-sprint4-execution-plan.md)

**Deliverables:**
- [x] Backend SSE Endpoint - `GET /api/v1/events/stream`
- [x] Graph Event Publisher - NATS events on graph mutations
- [x] Frontend SSE Hook - `useGraphSubscription()`
- [x] Graph State Manager - `useRealtimeGraph()` with delta updates
- [x] UI Integration - Live updates in GraphDemoView
- [x] Subscription Manager - Connection tracking and metrics

**Key Files Created:**
- `backend/app/routers/sse.py` - SSE streaming endpoint
- `backend/app/schemas/graph_events.py` - Event schemas
- `backend/app/services/subscription_manager.py` - Connection tracking
- `frontend/src/hooks/useGraphSubscription.ts` - SSE hook
- `frontend/src/hooks/useRealtimeGraph.ts` - Real-time state manager
- `frontend/src/types/graphEvents.ts` - Event types

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

### Sprint 7: Agent Observability 📋

**Goal:** Enable monitoring and intervention for long-running agent tasks

**Source:** [2026 Agentic Shift White Paper](./2026-01-01-agentic-shift-analysis.md) - "If an agent working on a week-long task goes 'off the rails' on day three, managers will need tools to detect that deviation and intervene."

**Planned Deliverables:**
- [ ] Agent execution dashboard (progress timeline, checkpoints)
- [ ] Drift detection indicators (output divergence, repeated failures, stuck detection)
- [ ] Resource burn tracking (tokens consumed, time elapsed, cost accumulation)
- [ ] Intervention triggers (configurable alerts for stuck/drifting agents)
- [ ] One-click course correction (pause, redirect, rollback)
- [ ] Execution replay/audit trail

**Key Entity Types:**
- `checkpoint` - Agent progress markers
- `intervention` - Human corrections to agent work
- `drift_event` - Detected deviations from expected behavior

**NATS Subjects:**
```
agent.checkpoint.created  → {execution_id, checkpoint_type, progress_pct}
agent.drift.detected      → {execution_id, drift_type, severity}
agent.intervention.needed → {execution_id, reason, suggested_action}
agent.stuck.detected      → {execution_id, stuck_duration, last_activity}
```

**Dependencies:**
- Sprint 4 (real-time subscriptions)
- Sprint 3 (agent execution tracking)

---

### Sprint 8: Automated QA Pipeline 📋

**Goal:** AI reviews AI - automated quality assurance for agent output

**Source:** [2026 Agentic Shift White Paper](./2026-01-01-agentic-shift-analysis.md) - "The most significant productivity gain in 2026 will shift from 'AI can do the drafts' to 'AI can audit the drafts.'"

**Planned Deliverables:**
- [ ] Judge model infrastructure (invoke reviewer models on output)
- [ ] Policy checker (compliance with business rules)
- [ ] Factuality checker (verify claims against sources)
- [ ] Completeness checker (did output address all requirements?)
- [ ] Domain-specific linters (reasoning quality, logical consistency)
- [ ] QA report aggregation (unified score, issue summary)
- [ ] Human escalation workflow (only surface issues needing attention)

**Architecture:**
```
Agent Output → QA Pipeline → Judge Models → QA Report
                    │
                    ├─ PolicyChecker
                    ├─ FactualityChecker
                    ├─ CompletenessChecker
                    └─ DomainLinter
                            │
                            ↓
                    Pass → Auto-approve
                    Fail → Human review queue
```

**Synergy with AI Arena:**
- AI Arena currently debates hypotheses
- Extend to debate output quality
- Multi-model consensus on correctness

**Key Entity Types:**
- `qa_report` - Aggregated quality assessment
- `qa_issue` - Individual finding from checker
- `qa_approval` - Human sign-off on reviewed output

**Dependencies:**
- Sprint 7 (agent observability for integration)
- AI Arena infrastructure

---

### Sprint 9: Task Inbox 📋

**Goal:** Async task queue where users can submit work and agents pick up/execute

**Source:** [2026 Agentic Shift White Paper](./2026-01-01-agentic-shift-analysis.md) - "Rumors of an Anthropic 'inbox' where a user can simply email tasks to their agent."

**Planned Deliverables:**
- [ ] Task entity type and schema
- [ ] Task queue service (priority, SLA tracking)
- [ ] Email integration (`task@commandcenter.io` → new task)
- [ ] Slack integration (`/cc-task "description"` → new task)
- [ ] API endpoint (`POST /api/v1/tasks`)
- [ ] Task assignment (manual or auto-assign to available agent)
- [ ] Task lifecycle (pending → assigned → running → review → complete)
- [ ] VISLZR integration (tasks as queryable graph entities)

**Architecture:**
```
┌───────────┐   ┌───────────┐   ┌───────────┐
│   Email   │   │   Slack   │   │    API    │
└─────┬─────┘   └─────┬─────┘   └─────┬─────┘
      │             │             │
      └─────────────┬─────────────┘
                    │
            ┌───────┴───────┐
            │  Task Queue   │
            │  (Priority)   │
            └───────┬───────┘
                    │
            ┌───────┴───────┐
            │ Agent Pool    │
            │ (Assignment)  │
            └───────┬───────┘
                    │
            ┌───────┴───────┐
            │  Execution    │
            │  + QA (S8)    │
            └───────┬───────┘
                    │
            ┌───────┴───────┐
            │   Result      │
            │   + Graph     │
            └───────────────┘
```

**Key Entity Types:**
- `task` - Work item in queue
- `task_assignment` - Agent assigned to task
- `task_result` - Output from completed task

**NATS Subjects:**
```
task.created    → {task_id, priority, description}
task.assigned   → {task_id, agent_id}
task.completed  → {task_id, result_summary}
task.failed     → {task_id, error}
```

**Dependencies:**
- Sprint 7 (agent observability)
- Sprint 8 (QA pipeline for output review)

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
| `checkpoint` | Sprint 7 | Agent progress marker |
| `intervention` | Sprint 7 | Human correction to agent work |
| `drift_event` | Sprint 7 | Detected deviation from expected behavior |
| `qa_report` | Sprint 8 | Aggregated quality assessment |
| `qa_issue` | Sprint 8 | Individual finding from checker |
| `task` | Sprint 9 | Work item in queue |
| `task_result` | Sprint 9 | Output from completed task |

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

**Agent Observability Complete When:**
- [ ] Long-running agent progress visible in dashboard
- [ ] Drift detection alerts fire within 30 minutes of deviation
- [ ] Intervention workflow allows pause/redirect/rollback
- [ ] Cost tracking accurate within 5%

**Automated QA Complete When:**
- [ ] Agent output automatically reviewed before human sees it
- [ ] Policy/factuality/completeness checks run on all outputs
- [ ] Human review queue only contains flagged items
- [ ] QA reports visible in VISLZR as graph entities

**Task Inbox Complete When:**
- [ ] Tasks submittable via API, email, and Slack
- [ ] Priority queue with SLA tracking operational
- [ ] Agents auto-assigned based on availability/specialty
- [ ] Task lifecycle visible in VISLZR

---

## PersonalAgent / Mini-Me Pillar Additions

These items support the PersonalAgent pillar and can be implemented incrementally:

### Proactivity Preferences (Low Effort)

**Goal:** Let users configure how proactively agents interrupt them

**Source:** [2026 Agentic Shift White Paper](./2026-01-01-agentic-shift-analysis.md) - "Proactivity will become a new product battleground, as companies compete to build systems with 'good proactive taste'."

**Deliverables:**
- [ ] User proactivity profile schema
- [ ] Interrupt threshold settings (low/medium/high)
- [ ] Preferred notification channels (slack, email, in-app)
- [ ] Quiet hours configuration
- [ ] Domain-specific rules (compliance=immediate, docs=digest)

**Schema:**
```yaml
proactivity_profile:
  interrupt_threshold: high  # low/medium/high
  preferred_channels: [slack, email]
  quiet_hours: ["22:00", "07:00"]
  domains:
    compliance: immediate
    documentation: daily_digest
    code_review: when_blocked
```

---

### Learning Capture Infrastructure (Low Effort)

**Goal:** Capture patterns for future skill improvement and potential fine-tuning

**Source:** [2026 Agentic Shift White Paper](./2026-01-01-agentic-shift-analysis.md) - Models with continual learning capability becoming available.

**Reality:** Only Anthropic/OpenAI can make models learn. BUT we can build infrastructure to:
- Track what works → feed back to skills
- Store correction patterns → inform future prompts
- Build domain-specific fine-tuning datasets

**Deliverables:**
- [ ] Correction capture API (`POST /api/v1/corrections`)
- [ ] Pattern extraction from corrections
- [ ] Skill update suggestions based on patterns
- [ ] Fine-tuning dataset export (future use)

**Schema:**
```python
class LearningCapture:
    original_output: str
    human_correction: str
    context: dict  # task, domain, agent persona
    pattern_extracted: Optional[str]
    skill_update_suggested: Optional[str]
```

---

## References

- [Composable Design Doc](./2025-01-01-composable-commandcenter-design.md) - Full architecture
- [2026 Agentic Shift Analysis](./2026-01-01-agentic-shift-analysis.md) - Source for Sprints 7-9
- [Phase 7-8 Blueprint](../../hub-prototype/phase_7_8_graph_service_vislzr_integration_plan_command_center.md) - Original VISLZR plan
- [Comprehensive Roadmap](./2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md) - 12-phase overview
- [Hub SSE Pattern](../../hub/backend/app/streaming/sse.py) - Reference implementation
