# Composable CommandCenter: Unified Operating Surface Design

**Date:** 2025-01-01
**Status:** Draft
**Authors:** Daniel Connolly, Claude
**Related:**
- `hub-prototype/phase_7_8_graph_service_vislzr_integration_plan_command_center.md`
- Composability principles document

---

## Executive Summary

This document proposes a fundamental architectural shift for CommandCenter: from isolated project containers to a **unified composable operating surface**. Instead of launching separate interfaces per project, users and agents interact with a single surface that can compose any view, across any project, at any level of detail—from ecosystem overview down to individual lines of code.

The design applies front-end composability principles where:
- **AI agents are the primary consumers** (projected 99% of traffic)
- **The UI is a query box**, not a static page
- **Primitives enforce brand/UX contracts** across infinite compositions
- **The project boundary becomes a zoom level**, not a container

---

## The Problem with Current Architecture

### Fragmented Experience

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Project A      │  │  Project B      │  │  Project C      │
│  Container      │  │  Container      │  │  Container      │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │ Own UI    │  │  │  │ Own UI    │  │  │  │ Own UI    │  │
│  │ Own State │  │  │  │ Own State │  │  │  │ Own State │  │
│  │ Own View  │  │  │  │ Own View  │  │  │  │ Own View  │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Limitations:**
- Cannot see cross-project dependencies
- Cannot query "all failing health checks across everything"
- Context switching between projects loses state
- Agents must know which container to target
- Duplicated UI code across containers

---

## The Composable Architecture

### Unified Surface

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPOSABLE SURFACE                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    QUERY / INTENT                        ││
│  │  "Show me all services with degraded health"            ││
│  │  "Show dependencies between Veria and CommandCenter"    ││
│  │  "Zoom into the auth module of Project A"               ││
│  └─────────────────────────────────────────────────────────┘│
│                            ↓                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              SCHEMA-DRIVEN RENDERER                      ││
│  │  Composes primitives based on query + graph data        ││
│  └─────────────────────────────────────────────────────────┘│
│                            ↓                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Node    │ │ Edge    │ │ Panel   │ │ List    │  ...      │
│  │ Prim.   │ │ Prim.   │ │ Prim.   │ │ Prim.   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    UNIFIED DATA SPINE                        │
│  Graph-Service (all projects) + NATS Mesh (all events)      │
└─────────────────────────────────────────────────────────────┘
```

### Key Insight

**The "project" becomes just another zoom level, not a container boundary.**

```
Ecosystem
  └── Project
        └── Service
              └── Module
                    └── File
                          └── Symbol
                                └── Line of code
```

Users can enter at any level, zoom in/out fluidly, and the surface composes the right view.

---

## Part A: The Query/Intent Layer

### Three Modes of Intent Expression

#### 1. Natural Language Query (Primary for Agents + Power Users)

```
"Show me all Python files that import the auth module"
"What services are unhealthy right now?"
"Trace the data flow from user signup to database write"
"Compare the dependency graphs of Project A and Project B"
```

**Parse Result Structure:**

```typescript
interface ComposedQuery {
  // What entities to fetch
  entities: EntitySelector[]

  // How to filter them
  filters: Filter[]

  // How to relate them
  relationships: RelationshipSpec[]

  // How to present them
  presentation: PresentationHint

  // Temporal scope
  timeRange?: TimeRange
}
```

#### 2. Structured Navigation (Primary for Humans)

Click-to-zoom, breadcrumb navigation, faceted filtering. The URL is the query:

```
/view?entity=symbol:graph_service.get_project_graph
      &context=dependencies,callers
      &depth=2
      &timeRange=7d
```

#### 3. Saved Recipes / Dashboards

```yaml
name: "Security Overview"
query:
  entities:
    - type: audit
      constraints:
        kind: [security, license]
        status: [warn, fail]
  presentation:
    layout: dashboard
    panels:
      - type: severity-heatmap
      - type: list
      - type: timeline
```

### Intent Resolution Pipeline

```
USER INTENT
     ↓
INTENT PARSER (NLP / structured → ComposedQuery)
     ↓
QUERY OPTIMIZER (batch, cache, fetch strategy)
     ↓
DATA FETCHER (Graph-Service + NATS enrichment)
     ↓
PRESENTATION COMPOSER (select primitives, assemble layout)
     ↓
RENDERED OUTPUT
  - Human: Interactive React component tree
  - Agent: Structured JSON + action affordances
```

### Agent-Native Query Interface

```typescript
interface QueryResult {
  // The data
  entities: Entity[]
  relationships: Relationship[]

  // What the agent can do next
  affordances: Affordance[]

  // Natural language summary
  summary: string

  // If clarification needed
  clarifications?: ClarificationRequest[]
}

interface Affordance {
  action: 'trigger_audit' | 'create_task' | 'open_in_editor' | 'drill_down'
  target: EntityRef
  description: string
  parameters?: Record<string, unknown>
}
```

---

## Part B: The Primitive Library

### Design Philosophy

Each primitive is:
1. **Self-contained** - Knows how to render itself given data
2. **Schema-aware** - Adapts to the shape of data it receives
3. **Composable** - Can be nested, combined, laid out flexibly
4. **Brand-compliant** - Enforces UX contracts (accessibility, responsiveness)
5. **Agent-readable** - Exposes its state and affordances programmatically

### Primitive Taxonomy

#### Layer 1: Atomic Primitives

```typescript
Icon, Badge, Text, Indicator, Button, Link, Toggle
```

#### Layer 2: Entity Primitives

```typescript
ProjectNode, ServiceNode, FileNode, SymbolNode, AuditNode, TaskNode
```

Each adapts to context:
```typescript
<SymbolNode entity={fn} size="compact" />   // Just icon + name
<SymbolNode entity={fn} size="standard" />  // + signature + badges
<SymbolNode entity={fn} size="expanded" />  // + docstring + callers inline
```

#### Layer 3: Relationship Primitives

```typescript
interface EdgePrimitive {
  from: EntityRef
  to: EntityRef
  relationship: RelationshipType
  presentation: {
    style: 'solid' | 'dashed' | 'dotted'
    weight: number
    color: string
    animated: boolean
    direction: 'forward' | 'backward' | 'bidirectional'
  }
}

// Visual defaults by relationship type
'imports'    → solid blue
'calls'      → solid green
'extends'    → dashed purple
'depends_on' → solid gray (thick)
'violates'   → solid red (thick)
```

#### Layer 4: Container Primitives

```typescript
GraphCanvas   // Main visualization with layout algorithms
EntityList    // Flat/grouped lists with virtualization
DetailPanel   // Entity detail view with sections
Dashboard     // Grid of panels
```

#### Layer 5: Composite Primitives

```typescript
DependencyExplorer  // GraphCanvas + Edges + DetailPanel
HealthDashboard     // StatusGrid + AlertList + Timeline
CodeReviewSurface   // CodeViewer + AuditList + Comments
SearchResults       // EntityList + FacetSidebar + Preview
```

### Composition Rules

```typescript
function compose(data: EntityGraph, context: CompositionContext): ComposedView {
  // Few entities + relationships → Graph
  if (entityCount < 100 && hasRelationships) return composeGraph(data)

  // Many entities, no relationships → List
  if (entityCount >= 100 && !hasRelationships) return composeList(data)

  // Single entity → Detail panel
  if (entityCount === 1) return composeDetail(data.entities[0])

  // Mixed/complex → Dashboard
  return composeDashboard(data)
}
```

---

## Part C: The Data Spine Requirements

### Current State (Graph-Service Phase 7)

**What exists:**
- ✅ Entity models (Project, File, Symbol, Service, Task, Audit)
- ✅ Single-project queries
- ✅ Dependency traversal within project
- ✅ REST API
- ✅ NATS integration

### Required Enhancements

#### 1. Cross-Project Federation

```typescript
interface FederatedQuery {
  scope: 'ecosystem' | ProjectRef[]
  query: GraphQuery
  merge: {
    deduplication: 'by_id' | 'by_content'
    conflictResolution: 'newest' | 'highest_priority'
  }
}
```

```sql
CREATE TABLE cross_project_links (
  id UUID PRIMARY KEY,
  source_project_id UUID,
  source_entity_type VARCHAR(50),
  source_entity_id UUID,
  target_project_id UUID,
  target_entity_type VARCHAR(50),
  target_entity_id UUID,
  relationship_type VARCHAR(50),
  metadata JSONB,
  discovered_at TIMESTAMP
);
```

#### 2. Real-Time Subscriptions

```typescript
interface GraphSubscription {
  scope: EntitySelector
  events: ('created' | 'updated' | 'deleted' | 'health_changed')[]
  delivery: 'websocket' | 'sse' | 'nats'
}
```

NATS subjects:
```
graph.entity.created.{project_id}.{entity_type}
graph.entity.updated.{project_id}.{entity_type}.{entity_id}
graph.health.changed.{project_id}.{service_id}
graph.audit.completed.{project_id}.{audit_id}
```

#### 3. Temporal Queries

```typescript
interface TemporalQuery {
  query: GraphQuery
  asOf?: Timestamp           // Point-in-time snapshot
  changes?: {                // Or: changes over range
    from: Timestamp
    to: Timestamp
    granularity: 'minute' | 'hour' | 'day'
  }
}
```

#### 4. Semantic Search

```typescript
interface SemanticQuery {
  text: string                           // "authentication logic"
  entityTypes?: EntityType[]
  ranking: 'relevance' | 'recency' | 'importance'
}
```

Implementation: Vector embeddings of symbols/files + LLM query expansion.

#### 5. Computed Properties

```typescript
const computedProperties = {
  symbolCount: { on: 'file', computation: 'aggregate' },
  allDependencies: { on: 'symbol', computation: 'traversal' },
  complexity: { on: 'symbol', computation: 'ml_inference' },
  projectHealth: { on: 'project', computation: 'aggregate' }
}
```

#### 6. Action Execution Layer

```typescript
interface GraphAction {
  type: 'trigger_audit' | 'create_task' | 'run_indexer' | 'deploy'
  target: EntityRef
  params: Record<string, unknown>
  actor: string  // 'user:daniel' | 'agent:security-scanner'
  execution: 'sync' | 'async'
}
```

---

## Full Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPOSABLE SURFACE (VISLZR)                   │
│  Query Layer → Primitive Composer → Rendered View               │
└─────────────────────────────────────────────────────────────────┘
                              ↕ WebSocket / SSE
┌─────────────────────────────────────────────────────────────────┐
│                         API GATEWAY                              │
│  REST + GraphQL + Subscriptions + Actions                       │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                     GRAPH-SERVICE (Enhanced)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ Federation  │ │  Temporal   │ │  Semantic   │               │
│  │   Queries   │ │   Queries   │ │   Search    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  Computed   │ │   Action    │ │Subscription │               │
│  │ Properties  │ │  Executor   │ │  Manager    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL (Graph Tables)                   │   │
│  │  Projects │ Files │ Symbols │ Services │ Relationships   │   │
│  │  Audits   │ Tasks │ Events  │ CrossProjectLinks          │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              NATS (Real-Time Events)                     │   │
│  │  graph.* │ health.* │ audit.* │ action.*                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Vector DB (Semantic Search)                 │   │
│  │  Embeddings for symbols, files, documentation            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## What This Enables

| Query | Result |
|-------|--------|
| "Everything" | Ecosystem map with cross-project dependencies |
| "Project A" | Zoomed to project's internal structure |
| "Project A → auth → validateToken()" | Single function with callers across ALL projects |
| "All services with health < 100%" | Cross-project degraded services |
| "What depends on this API endpoint?" | Traces consumers across boundaries |
| "Show me what changed since yesterday" | Time-filtered view across everything |

---

## Implementation Priority

### Phase 1: Foundation
1. Cross-project links table + federation queries
2. WebSocket subscription infrastructure
3. Basic primitive library (Node, Edge, GraphCanvas)

### Phase 2: Query Layer
1. Intent parser (structured queries first, NLP later)
2. Composition engine
3. URL-as-query routing

### Phase 3: Agent Parity
1. Agent-facing API with affordances
2. Recipe/dashboard persistence
3. Action execution layer

### Phase 4: Advanced
1. Temporal queries
2. Semantic search (vector DB integration)
3. Computed properties

---

## Relationship to VISLZR

VISLZR is **not** just a visualization tool—it becomes **the** interface for CommandCenter. The original Phase 7-8 plan described a "mind map for code exploration." This design elevates that to a composable operating surface where:

- The mind map is one possible composition
- Lists, dashboards, detail views are other compositions
- All share the same primitives and data spine
- All are equally accessible to humans and agents

---

## References

- Freeplane reference implementation: `hub/vislzr/reference/freeplane/`
- Original Phase 7-8 plan: `hub-prototype/phase_7_8_graph_service_vislzr_integration_plan_command_center.md`
- Composability principles: Desktop/Composability.rtf
