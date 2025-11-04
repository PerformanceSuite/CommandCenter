# CommandCenter Phases 1-12: Comprehensive Roadmap & Design

**Date:** 2025-11-03
**Status:** Design Approved
**Architecture:** Hybrid Modular Monolith
**Timeline:** 32 weeks (8 months)

---

## Executive Summary

This document outlines the complete evolution of CommandCenter Hub from its current state (Dagger-based multi-project orchestration) to a fully autonomous, federated AI operating system with predictive intelligence, compliance automation, and interactive visualization.

**Vision:** Transform CommandCenter into a self-healing, AI-driven mesh that federates multiple project instances, visualizes code graphs in real-time, orchestrates agents for automation, ensures continuous compliance, and predicts failures before they occur.

**Current State (Baseline):**
- ✅ Hub: Python/FastAPI backend with Dagger SDK for container orchestration
- ✅ Database: PostgreSQL with project/service models
- ✅ Frontend: React app for project management
- ✅ Infrastructure: 90% complete (Celery, RAG, Observability)

**Target State (Phase 12 Complete):**
- Federated mesh connecting unlimited CommandCenter instances
- Real-time interactive visualization (VISLZR) of code graphs
- Agent orchestration with workflow automation
- Continuous compliance and security monitoring
- Predictive intelligence with auto-remediation
- Partner API for external integrations

---

## Architecture Overview

### Hybrid Modular Monolith

The Hub evolves into a modular Python application with clear internal boundaries. Each module can be extracted to a microservice later without rewriting logic.

```
hub/backend/app/
├── core/              # Existing: Dagger orchestration, project management
├── events/            # NEW: NATS integration, event streaming, correlation
├── graph/             # NEW: Code graph, dependencies, knowledge representation
├── agents/            # NEW: Agent registry, workflow orchestration
├── vislzr/            # NEW: GraphQL API for visualization frontend
├── compliance/        # NEW: Policy engine, audit management
├── intelligence/      # NEW: Predictive models, auto-remediation
├── shared/            # Cross-cutting: auth, monitoring, utilities
└── main.py           # FastAPI app with all module routers
```

### Infrastructure Stack

```yaml
services:
  hub-backend:        # FastAPI (all modules)
  hub-frontend:       # React (existing project management UI)
  vislzr:             # Next.js 14 (NEW: graph visualization)
  postgres-hub:       # Existing database
  postgres-graph:     # NEW: Graph data with Prisma
  redis:              # Existing (cache, queues)
  nats:               # NEW: Message bus for events
  prometheus:         # Existing (metrics)
  grafana:            # Existing (dashboards)
```

### Communication Patterns

**Internal (within Hub backend):**
- Modules publish events to NATS subjects
- Shared database for transactional consistency
- Internal APIs via Python imports

**External (cross-Hub federation):**
- NATS subjects: `hub.global.*`
- GraphQL federation for unified queries
- REST API for partner integrations

---

## Phase 1-6: Foundation & Event Infrastructure

**Timeline:** Weeks 1-8
**Goal:** Build event-driven foundation with NATS, correlation tracking, and federation prep

### Phase 1: Event System Bootstrap (Week 1)

**Deliverables:**
- `events/` module in Hub backend
- NATS server in Docker Compose
- Event model: `Event(id, subject, origin, correlationId, payload, timestamp)`
- `EventService` with `publish()`, `subscribe()`, `replay()` methods
- Event persistence to PostgreSQL (hub database)

**Database Schema:**
```python
class Event(Base):
    __tablename__ = "events"
    id = Column(UUID, primary_key=True)
    subject = Column(String, index=True)  # NATS subject
    origin = Column(JSON)  # {hub_id, service, user}
    correlation_id = Column(UUID, index=True)
    payload = Column(JSON)
    timestamp = Column(DateTime, index=True)
```

**API Endpoints:**
- `POST /api/events/publish` → emit event
- `GET /api/events?subject=&since=&until=` → query events
- `WS /api/events/stream?subject=` → real-time stream

**NATS Configuration:**
```yaml
# docker-compose.yml addition
nats:
  image: nats:2.10-alpine
  ports:
    - "4222:4222"  # Client connections
    - "8222:8222"  # Monitoring
  command: ["-js", "-m", "8222"]  # Enable JetStream
```

**Success Criteria:**
- [ ] Events persist to database
- [ ] NATS subjects publish/subscribe works
- [ ] Real-time WebSocket streaming functional

---

### Phase 2-3: Event Streaming & Correlation (Weeks 2-3)

**Deliverables:**
- Correlation middleware for FastAPI (auto-inject `X-Correlation-ID` headers)
- `EventStreamer` for real-time subscriptions
- Temporal replay API: query events by time range
- CLI tools: `hub events --since --until --subject`

**Correlation Middleware:**
```python
@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
```

**EventStreamer Implementation:**
- Subscribe to NATS subjects
- Emit Server-Sent Events (SSE) or WebSocket
- Filter by subject, time range, correlation ID

**CLI Commands:**
```bash
# Replay last hour
hub events --since "1h ago" --subject "hub.*.audit.*"

# Follow live events
hub events --follow --subject "hub.project.*.health"

# Export to JSON
hub events --since "2025-11-01" --format json > events.json
```

**Success Criteria:**
- [ ] All HTTP requests have correlation IDs
- [ ] Events linked by correlation ID queryable
- [ ] Real-time event streaming functional
- [ ] CLI tools working

---

### Phase 4: NATS Bridge (Week 4)

**Deliverables:**
- Bidirectional NATS bridge
- Subject namespace design
- JSON-RPC endpoint for external tools
- Event routing rules

**Subject Namespace:**
```
hub.<hub_id>.<domain>.<action>

Examples:
  hub.local-hub.project.veria.created
  hub.local-hub.audit.security.completed
  hub.local-hub.health.postgres.degraded
  hub.global.presence.announced
  hub.global.sync.registry-update
```

**NATS Bridge Service:**
```python
class NATSBridge:
    async def connect(self):
        self.nc = await nats.connect(os.getenv("NATS_URL"))
        self.js = self.nc.jetstream()

    async def publish_internal_to_nats(self, event: Event):
        subject = f"hub.{HUB_ID}.{event.subject}"
        await self.nc.publish(subject, event.payload_json.encode())

    async def subscribe_nats_to_internal(self, subject_filter: str):
        async def handler(msg):
            await event_service.emit(
                subject=msg.subject,
                payload=json.loads(msg.data),
                correlation_id=msg.headers.get("Correlation-ID")
            )
        await self.nc.subscribe(subject_filter, cb=handler)
```

**JSON-RPC Endpoint:**
```python
# POST /rpc
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "bus.publish",
  "params": {
    "topic": "hub.local-hub.project.veria.startup",
    "payload": {"pid": 1234}
  }
}
```

**Success Criteria:**
- [ ] Internal events auto-publish to NATS
- [ ] NATS events trigger internal handlers
- [ ] JSON-RPC endpoint functional
- [ ] Subject routing rules enforced

---

### Phase 5: Federation Prep (Week 5)

**Deliverables:**
- Hub registry metadata model
- Presence heartbeat publisher
- Hub discovery subscriber
- Metrics publishing

**Hub Registry Model:**
```python
class HubInfo(Base):
    __tablename__ = "hub_registry"
    id = Column(String, primary_key=True)  # hub-id
    name = Column(String)
    version = Column(String)
    projects = Column(JSON)  # List of project IDs
    services = Column(JSON)  # List of services
    last_seen = Column(DateTime)
    metadata = Column(JSON)
```

**Presence Heartbeat:**
```python
async def publish_presence():
    while True:
        await nats_bridge.publish(
            subject="hub.global.presence",
            payload={
                "hub_id": HUB_ID,
                "name": HUB_NAME,
                "version": VERSION,
                "projects": [p.id for p in get_projects()],
                "services": get_service_status(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        await asyncio.sleep(5)  # Every 5 seconds
```

**Discovery Subscriber:**
```python
async def handle_presence(msg):
    hub_info = json.loads(msg.data)
    await db.upsert_hub_registry(
        id=hub_info["hub_id"],
        last_seen=datetime.utcnow(),
        **hub_info
    )

await nats.subscribe("hub.global.presence", cb=handle_presence)
```

**Metrics Publishing:**
- Publish to `hub.global.metrics.<hub_id>` every 30s
- Metrics: project count, service health, event throughput, storage usage

**Success Criteria:**
- [ ] Presence heartbeat publishes every 5s
- [ ] Other Hubs discovered and tracked
- [ ] Metrics published and queryable
- [ ] Stale Hubs pruned after timeout (30s)

---

### Phase 6: Health & Service Discovery (Weeks 6-8)

**Deliverables:**
- Enhanced service model with health checks
- Health summary publisher
- Service discovery registry
- Federation dashboard

**Enhanced Service Model:**
```python
class Service(Base):
    # ... existing fields ...
    health_url = Column(String)  # HTTP health check endpoint
    health_interval = Column(Integer, default=30)  # seconds
    health_status = Column(Enum("up", "down", "degraded"))
    last_health_check = Column(DateTime)
    health_details = Column(JSON)  # latency, errors, etc.
```

**Health Check Worker:**
```python
async def health_check_loop():
    while True:
        services = await db.get_all_services()
        for service in services:
            status = await probe_health(service.health_url)
            await db.update_service_health(service.id, status)
            await nats.publish(
                f"hub.{HUB_ID}.health.{service.name}",
                status
            )
        await asyncio.sleep(15)
```

**Health Summary Publisher:**
```python
async def publish_health_summary():
    while True:
        summary = {
            "hub_id": HUB_ID,
            "timestamp": datetime.utcnow().isoformat(),
            "services": [
                {
                    "name": s.name,
                    "status": s.health_status,
                    "latency_ms": s.health_details.get("latency_ms")
                }
                for s in await db.get_all_services()
            ]
        }
        await nats.publish("hub.global.health", summary)
        await asyncio.sleep(15)
```

**Federation Dashboard API:**
```python
# GET /api/federation/hubs
{
  "hubs": [
    {
      "id": "hub-1",
      "name": "Main Hub",
      "projects": ["veria", "mrktzr"],
      "services": [
        {"name": "postgres", "status": "up"},
        {"name": "redis", "status": "up"}
      ],
      "last_seen": "2025-11-03T10:00:00Z"
    }
  ]
}
```

**Success Criteria:**
- [ ] Service health checks run automatically
- [ ] Health summaries published every 15s
- [ ] Federation dashboard shows all Hubs
- [ ] Service discovery functional

---

## Phase 7-8: Graph Service & Visualization

**Timeline:** Weeks 9-16
**Goal:** Build code graph representation and interactive visualization

### Phase 7: Graph-Service Implementation (Weeks 9-12)

**Deliverables:**
- Separate PostgreSQL database: `commandcenter_graph`
- Prisma schema with graph entities
- Ingestion pipelines for code parsing
- GraphQL API

**Prisma Schema (graph/schema.prisma):**
```prisma
model Project {
  id        String   @id @default(uuid())
  name      String
  rootPath  String
  repoUrl   String?
  status    String   // active, archived
  repos     Repo[]
  services  Service[]
  tasks     Task[]
  createdAt DateTime @default(now())
}

model Repo {
  id            String   @id @default(uuid())
  projectId     String
  project       Project  @relation(fields: [projectId], references: [id])
  provider      String   // github, gitlab, local
  url           String
  defaultBranch String   @default("main")
  files         File[]
}

model File {
  id            String   @id @default(uuid())
  repoId        String
  repo          Repo     @relation(fields: [repoId], references: [id])
  path          String
  lang          String   // ts, py, go, rs, etc.
  hash          String   // SHA-256 for change detection
  size          Int
  lastIndexedAt DateTime
  symbols       Symbol[]

  @@unique([repoId, path])
  @@index([lang])
}

model Symbol {
  id            String       @id @default(uuid())
  fileId        String
  file          File         @relation(fields: [fileId], references: [id])
  kind          String       // Module, Class, Function, Type, Var, Test
  name          String
  signature     String?      // function signature, type definition
  rangeStart    Int          // line number
  rangeEnd      Int
  exports       Boolean      @default(false)
  dependencies  Dependency[] @relation("from")
  dependents    Dependency[] @relation("to")

  @@index([name, kind])
}

model Dependency {
  id           String @id @default(uuid())
  fromSymbolId String
  fromSymbol   Symbol @relation("from", fields: [fromSymbolId], references: [id])
  toSymbolId   String
  toSymbol     Symbol @relation("to", fields: [toSymbolId], references: [id])
  type         String // import, call, extends, uses

  @@unique([fromSymbolId, toSymbolId, type])
}

model Service {
  id           String         @id @default(uuid())
  projectId    String
  project      Project        @relation(fields: [projectId], references: [id])
  name         String
  type         String         // api, job, db, queue, mcp, mesh
  endpoint     String?
  healthUrl    String?
  healthSamples HealthSample[]
}

model SpecItem {
  id          String   @id @default(uuid())
  projectId   String
  source      String   // file, doc, canvas
  ref         String   // file path or doc ID
  title       String
  description String?
  priority    String   // high, medium, low
  status      String   // planned, inProgress, done, blocked
  tasks       Task[]
}

model Task {
  id          String    @id @default(uuid())
  projectId   String
  specItemId  String?
  specItem    SpecItem? @relation(fields: [specItemId], references: [id])
  title       String
  description String?
  status      String    // todo, inProgress, done, blocked
  assignee    String?
  kind        String    // feature, bug, chore, review, security
  labels      String[]
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt
}

model Link {
  id         String @id @default(uuid())
  fromEntity String // File, Symbol, Service, Task, SpecItem
  fromId     String
  toEntity   String
  toId       String
  type       String // implements, tests, documents, depends_on

  @@unique([fromEntity, fromId, toEntity, toId, type])
}

model HealthSample {
  id         String   @id @default(uuid())
  serviceId  String
  service    Service  @relation(fields: [serviceId], references: [id])
  status     String   // up, down, degraded
  latencyMs  Int?
  details    Json?
  observedAt DateTime @default(now())

  @@index([serviceId, observedAt])
}

model Audit {
  id           String   @id @default(uuid())
  targetEntity String   // File, Symbol, Service, Project
  targetId     String
  kind         String   // codeReview, security, license, compliance
  status       String   // pending, ok, warn, fail
  summary      String?
  reportPath   String?  // Path to detailed report
  createdAt    DateTime @default(now())

  @@index([targetEntity, targetId])
}

model Event {
  id            String   @id @default(uuid())
  subject       String
  payloadJson   Json
  correlationId String?
  createdAt     DateTime @default(now())

  @@index([subject, createdAt])
  @@index([correlationId])
}
```

**Ingestion Pipeline Architecture:**

```python
# graph/ingest/base.py
class LanguageParser(ABC):
    @abstractmethod
    async def parse_file(self, file_path: str) -> ParseResult:
        """Parse file and extract symbols, dependencies"""
        pass

# graph/ingest/typescript_parser.py
class TypeScriptParser(LanguageParser):
    async def parse_file(self, file_path: str) -> ParseResult:
        # Use ts-morph via Node.js subprocess or pyright
        # Extract: classes, functions, interfaces, imports
        pass

# graph/ingest/python_parser.py
class PythonParser(LanguageParser):
    async def parse_file(self, file_path: str) -> ParseResult:
        tree = ast.parse(file_path.read_text())
        symbols = []
        dependencies = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append(Symbol(
                    kind="Function",
                    name=node.name,
                    rangeStart=node.lineno,
                    rangeEnd=node.end_lineno
                ))
            elif isinstance(node, ast.Import):
                # Track import dependencies
                pass

        return ParseResult(symbols, dependencies)

# graph/ingest/service.py
class IngestionService:
    async def ingest_project(self, project_id: str, incremental: bool = True):
        project = await prisma.project.find_unique(where={"id": project_id})
        repos = await prisma.repo.find_many(where={"projectId": project_id})

        for repo in repos:
            files = scan_repo_files(repo.rootPath)
            for file_path in files:
                if incremental:
                    existing = await prisma.file.find_unique(
                        where={"repoId_path": {"repoId": repo.id, "path": file_path}}
                    )
                    if existing and existing.hash == compute_hash(file_path):
                        continue  # Skip unchanged files

                parser = get_parser_for_language(file_path)
                result = await parser.parse_file(file_path)

                # Upsert file, symbols, dependencies
                await prisma.file.upsert(
                    where={"repoId_path": {"repoId": repo.id, "path": file_path}},
                    create={...},
                    update={...}
                )
```

**CLI Commands:**
```bash
# Ingest entire project
hub graph:ingest --project veria

# Incremental ingest (only changed files)
hub graph:ingest --project veria --incremental

# Specific languages
hub graph:ingest --project veria --lang ts,py

# Since git ref
hub graph:ingest --project veria --since main~10
```

**GraphQL API (graph/api.py):**
```python
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Node:
    id: str
    entity: str  # File, Symbol, Service, Task
    label: str
    metadata: strawberry.scalars.JSON

@strawberry.type
class Edge:
    from_id: str
    to_id: str
    type: str  # import, call, implements

@strawberry.type
class Graph:
    nodes: list[Node]
    edges: list[Edge]

@strawberry.type
class Query:
    @strawberry.field
    async def project_graph(
        self,
        project_id: str,
        depth: int = 2,
        filters: Optional[strawberry.scalars.JSON] = None
    ) -> Graph:
        # Fetch nodes and edges from Prisma
        files = await prisma.file.find_many(
            where={"repo": {"projectId": project_id}}
        )
        symbols = await prisma.symbol.find_many(
            where={"file": {"repo": {"projectId": project_id}}}
        )
        dependencies = await prisma.dependency.find_many(...)

        nodes = [Node(id=f.id, entity="File", label=f.path) for f in files]
        nodes += [Node(id=s.id, entity="Symbol", label=s.name) for s in symbols]

        edges = [
            Edge(from_id=d.fromSymbolId, to_id=d.toSymbolId, type=d.type)
            for d in dependencies
        ]

        return Graph(nodes=nodes, edges=edges)

    @strawberry.field
    async def symbol_dependencies(
        self,
        symbol_id: str,
        direction: str = "outgoing",  # outgoing, incoming, both
        depth: int = 1
    ) -> list[Node]:
        # Recursive query for dependencies
        pass

    @strawberry.field
    async def search(
        self,
        query: str,
        scope: list[str] = ["symbols", "files", "tasks"]
    ) -> list[Node]:
        # Full-text search across entities
        pass

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_task(
        self,
        project_id: str,
        spec_item_id: Optional[str],
        title: str,
        kind: str,
        labels: list[str] = []
    ) -> Task:
        task = await prisma.task.create(
            data={
                "projectId": project_id,
                "specItemId": spec_item_id,
                "title": title,
                "kind": kind,
                "labels": labels,
                "status": "todo"
            }
        )

        # Publish event
        await event_service.publish(
            subject=f"hub.{HUB_ID}.task.created",
            payload={"task_id": task.id, "title": title}
        )

        return task

    @strawberry.mutation
    async def trigger_audit(
        self,
        target_entity: str,
        target_id: str,
        kind: str
    ) -> Audit:
        audit = await prisma.audit.create(
            data={
                "targetEntity": target_entity,
                "targetId": target_id,
                "kind": kind,
                "status": "pending"
            }
        )

        # Publish to NATS for agent processing
        await nats.publish(
            f"agent.request.audit-{kind}",
            {
                "audit_id": audit.id,
                "target_entity": target_entity,
                "target_id": target_id
            }
        )

        return audit

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

# In main.py
app.include_router(graphql_app, prefix="/graphql")
```

**Success Criteria:**
- [ ] Graph database schema deployed
- [ ] Ingestion pipelines parse TS, Python, Go files
- [ ] GraphQL API returns project graphs
- [ ] Symbol dependencies queryable
- [ ] Search works across all entities

---

### Phase 8: VISLZR Frontend (Weeks 13-16)

**Deliverables:**
- Next.js 14 app with App Router
- Interactive graph visualization
- Real-time updates via WebSocket
- Node action system

**Project Structure:**
```
hub/vislzr/
├── app/
│   ├── layout.tsx
│   ├── page.tsx              # Home: project selector
│   ├── project/[id]/
│   │   ├── page.tsx          # Project graph view
│   │   └── layout.tsx
│   ├── ecosystem/
│   │   └── page.tsx          # Multi-project federation view
│   └── workflows/
│       └── page.tsx          # Workflow visualization (Phase 10)
├── components/
│   ├── graph/
│   │   ├── GraphCanvas.tsx   # Main visualization component
│   │   ├── NodeRenderer.tsx  # Custom node shapes
│   │   ├── EdgeRenderer.tsx  # Custom edge styles
│   │   └── ControlPanel.tsx  # Zoom, filter, layout controls
│   ├── nodes/
│   │   ├── FileNode.tsx
│   │   ├── SymbolNode.tsx
│   │   ├── ServiceNode.tsx
│   │   └── TaskNode.tsx
│   ├── panels/
│   │   ├── NodeDetailPanel.tsx
│   │   ├── ActionMenu.tsx
│   │   └── FilterPanel.tsx
│   └── layout/
│       ├── Header.tsx
│       └── Sidebar.tsx
├── lib/
│   ├── graphql/
│   │   ├── client.ts         # Apollo client setup
│   │   ├── queries.ts        # GraphQL queries
│   │   └── mutations.ts      # GraphQL mutations
│   ├── websocket/
│   │   └── events.ts         # Real-time event subscription
│   └── graph-layout/
│       ├── force-directed.ts # D3 force layout
│       ├── hierarchical.ts   # Dagre layout
│       └── circular.ts       # Circular layout
└── styles/
    └── globals.css
```

**Core Components:**

```tsx
// components/graph/GraphCanvas.tsx
'use client'

import { useEffect, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useGraphQuery } from '@/lib/graphql/queries'
import { useEventStream } from '@/lib/websocket/events'

export function GraphCanvas({ projectId }: { projectId: string }) {
  const { data, loading } = useGraphQuery(projectId)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  // Initialize graph from GraphQL
  useEffect(() => {
    if (data?.projectGraph) {
      const graphNodes = data.projectGraph.nodes.map(n => ({
        id: n.id,
        type: n.entity.toLowerCase(),
        position: { x: 0, y: 0 }, // Layout algorithm will position
        data: { label: n.label, metadata: n.metadata }
      }))

      const graphEdges = data.projectGraph.edges.map((e, idx) => ({
        id: `${e.fromId}-${e.toId}-${idx}`,
        source: e.fromId,
        target: e.toId,
        label: e.type,
        animated: e.type === 'call'
      }))

      setNodes(graphNodes)
      setEdges(graphEdges)
    }
  }, [data])

  // Real-time updates from NATS events
  useEventStream(`hub.*.${projectId}.*`, (event) => {
    if (event.subject.includes('.task.created')) {
      // Add new task node
      const newNode = {
        id: event.payload.task_id,
        type: 'task',
        position: { x: Math.random() * 500, y: Math.random() * 500 },
        data: { label: event.payload.title }
      }
      setNodes(nodes => [...nodes, newNode])
    }
  })

  const onNodeClick = (event: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }

  return (
    <div className="h-screen w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background />
      </ReactFlow>

      {selectedNode && (
        <NodeDetailPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  )
}
```

```tsx
// components/panels/NodeDetailPanel.tsx
'use client'

import { useState } from 'react'
import { Node } from 'reactflow'
import { useMutation } from '@apollo/client'
import { TRIGGER_AUDIT } from '@/lib/graphql/mutations'

export function NodeDetailPanel({ node, onClose }: { node: Node, onClose: () => void }) {
  const [triggerAudit] = useMutation(TRIGGER_AUDIT)

  const handleCodeReview = async () => {
    await triggerAudit({
      variables: {
        targetEntity: node.type,
        targetId: node.id,
        kind: 'codeReview'
      }
    })
  }

  const handleSecurityScan = async () => {
    await triggerAudit({
      variables: {
        targetEntity: node.type,
        targetId: node.id,
        kind: 'security'
      }
    })
  }

  return (
    <div className="absolute right-0 top-0 h-full w-96 bg-white shadow-lg p-6 overflow-y-auto">
      <div className="flex justify-between items-start mb-4">
        <h2 className="text-xl font-bold">{node.data.label}</h2>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
      </div>

      <div className="mb-6">
        <span className="text-sm text-gray-500 uppercase">{node.type}</span>
        <p className="text-sm text-gray-700 mt-2">{node.data.metadata?.description}</p>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-700">Actions</h3>

        {node.type === 'symbol' && (
          <>
            <button
              onClick={handleCodeReview}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              🔍 Code Review
            </button>
            <button
              onClick={handleSecurityScan}
              className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              🔒 Security Scan
            </button>
          </>
        )}

        {node.type === 'service' && (
          <button className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
            💚 Health Check
          </button>
        )}

        {node.type === 'task' && (
          <button className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600">
            ▶️ Execute Workflow
          </button>
        )}
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Metadata</h3>
        <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
          {JSON.stringify(node.data.metadata, null, 2)}
        </pre>
      </div>
    </div>
  )
}
```

```tsx
// app/project/[id]/page.tsx
import { GraphCanvas } from '@/components/graph/GraphCanvas'
import { FilterPanel } from '@/components/panels/FilterPanel'

export default function ProjectPage({ params }: { params: { id: string } }) {
  return (
    <div className="flex h-screen">
      <FilterPanel projectId={params.id} />
      <GraphCanvas projectId={params.id} />
    </div>
  )
}
```

**Real-time Event Integration:**
```typescript
// lib/websocket/events.ts
import { useEffect } from 'react'

export function useEventStream(subjectFilter: string, onEvent: (event: any) => void) {
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/events/stream?subject=${subjectFilter}`)

    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data)
      onEvent(event)
    }

    return () => ws.close()
  }, [subjectFilter])
}
```

**GraphQL Queries:**
```typescript
// lib/graphql/queries.ts
import { gql, useQuery } from '@apollo/client'

export const PROJECT_GRAPH = gql`
  query ProjectGraph($projectId: String!, $depth: Int, $filters: JSON) {
    projectGraph(projectId: $projectId, depth: $depth, filters: $filters) {
      nodes {
        id
        entity
        label
        metadata
      }
      edges {
        fromId
        toId
        type
      }
    }
  }
`

export function useGraphQuery(projectId: string, depth = 2) {
  return useQuery(PROJECT_GRAPH, {
    variables: { projectId, depth }
  })
}
```

**Success Criteria:**
- [ ] VISLZR app renders project graphs
- [ ] Interactive node selection works
- [ ] Real-time updates via WebSocket
- [ ] Node actions trigger audits/scans
- [ ] Multiple layout algorithms available
- [ ] Filter panel functional

---

## Phase 9-10: Federation & Agent Orchestration

**Timeline:** Weeks 17-24
**Goal:** Multi-Hub federation and agent-driven automation

### Phase 9: Federation & Cross-Project Intelligence (Weeks 17-20)

**Deliverables:**
- Federation graph schema extensions
- GraphQL federation stitching
- Global NATS subjects
- Insights engine
- VISLZR ecosystem mode

**Federation Schema Extensions:**
```prisma
model ProjectLink {
  id            String  @id @default(uuid())
  fromProjectId String
  toProjectId   String
  type          String  // dependency, integration, shared_service
  metadata      Json?

  @@unique([fromProjectId, toProjectId, type])
}

model IntegrationEdge {
  id             String @id @default(uuid())
  fromServiceId  String
  toServiceId    String
  protocol       String // http, grpc, nats, db
  endpoint       String?
  metadata       Json?
}

model GlobalMetrics {
  id            String   @id @default(uuid())
  metricType    String   // coverage, compliance, security, freshness
  projectId     String?  // null = ecosystem-wide
  value         Float
  unit          String
  timestamp     DateTime @default(now())

  @@index([metricType, timestamp])
}
```

**GraphQL Federation:**
```python
# graph/federation.py
@strawberry.type
class FederatedGraph:
    projects: list[Project]
    cross_links: list[ProjectLink]
    services: list[Service]
    integrations: list[IntegrationEdge]

@strawberry.type
class Query:
    @strawberry.field
    async def ecosystem_graph(self) -> FederatedGraph:
        # Query all Hubs via NATS
        hub_registry = await prisma.hub_info.find_many()

        all_projects = []
        all_services = []
        cross_links = []

        for hub in hub_registry:
            # Query each Hub's GraphQL endpoint
            hub_graph = await fetch_hub_graph(hub.id)
            all_projects.extend(hub_graph.projects)
            all_services.extend(hub_graph.services)

        # Discover cross-project links
        cross_links = await prisma.project_link.find_many()
        integrations = await prisma.integration_edge.find_many()

        return FederatedGraph(
            projects=all_projects,
            cross_links=cross_links,
            services=all_services,
            integrations=integrations
        )

    @strawberry.field
    async def cross_project_dependencies(
        self,
        project_id: str
    ) -> list[ProjectLink]:
        return await prisma.project_link.find_many(
            where={
                "OR": [
                    {"fromProjectId": project_id},
                    {"toProjectId": project_id}
                ]
            }
        )
```

**Global NATS Subjects:**
```python
# Standard subjects
GLOBAL_PRESENCE = "hub.global.presence"
GLOBAL_SYNC = "hub.global.sync.*"
GLOBAL_AUDIT = "hub.global.audit.*"
GLOBAL_METRICS = "hub.global.metrics.*"

# Subscribe to all Hubs
await nats.subscribe("hub.*.global.*", cb=handle_global_event)

# Publish ecosystem-wide events
async def publish_global_sync():
    await nats.publish(
        "hub.global.sync.registry",
        {
            "hub_id": HUB_ID,
            "projects": await get_project_ids(),
            "services": await get_service_ids(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

**Global Insights Engine:**
```python
# intelligence/insights/aggregator.py
class InsightsAggregator:
    async def compute_ecosystem_kpis(self) -> dict:
        hubs = await prisma.hub_info.find_many()

        total_projects = sum(len(h.projects) for h in hubs)

        # Code coverage
        coverage_metrics = await prisma.global_metrics.find_many(
            where={"metricType": "coverage"}
        )
        avg_coverage = sum(m.value for m in coverage_metrics) / len(coverage_metrics)

        # Compliance ratio
        audits = await prisma.audit.find_many(where={"kind": "compliance"})
        compliance_ratio = len([a for a in audits if a.status == "ok"]) / len(audits)

        # Security posture
        security_audits = await prisma.audit.find_many(where={"kind": "security"})
        open_vulns = len([a for a in security_audits if a.status == "fail"])

        return {
            "total_projects": total_projects,
            "total_hubs": len(hubs),
            "avg_coverage": avg_coverage,
            "compliance_ratio": compliance_ratio,
            "open_vulnerabilities": open_vulns,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def publish_insights(self):
        kpis = await self.compute_ecosystem_kpis()

        # Publish to NATS
        await nats.publish("hub.global.insights", kpis)

        # Store in database
        for metric_name, value in kpis.items():
            if isinstance(value, (int, float)):
                await prisma.global_metrics.create(
                    data={
                        "metricType": metric_name,
                        "value": float(value),
                        "unit": "count" if isinstance(value, int) else "percent"
                    }
                )

# Run every 5 minutes
async def insights_loop():
    aggregator = InsightsAggregator()
    while True:
        await aggregator.publish_insights()
        await asyncio.sleep(300)
```

**VISLZR Ecosystem View:**
```tsx
// app/ecosystem/page.tsx
'use client'

import { useQuery } from '@apollo/client'
import { ECOSYSTEM_GRAPH } from '@/lib/graphql/queries'
import ReactFlow, { Node, Edge } from 'reactflow'

export default function EcosystemPage() {
  const { data } = useQuery(ECOSYSTEM_GRAPH)

  const nodes: Node[] = data?.ecosystemGraph.projects.map(p => ({
    id: p.id,
    type: 'project',
    position: { x: 0, y: 0 },
    data: {
      label: p.name,
      services: data.ecosystemGraph.services.filter(s => s.projectId === p.id)
    }
  })) || []

  const edges: Edge[] = data?.ecosystemGraph.crossLinks.map(link => ({
    id: link.id,
    source: link.fromProjectId,
    target: link.toProjectId,
    label: link.type,
    style: { stroke: '#f97316', strokeWidth: 2 }
  })) || []

  return (
    <div className="h-screen">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
      />
    </div>
  )
}
```

**Success Criteria:**
- [ ] Ecosystem graph queries all Hubs
- [ ] Cross-project links visualized
- [ ] Global insights computed and published
- [ ] VISLZR ecosystem toggle works
- [ ] Real-time federation updates

---

### Phase 10: Agent Orchestration & Workflow Automation (Weeks 21-24)

**Deliverables:**
- Agent registry
- Workflow engine with YAML definitions
- Agent-to-agent protocol
- VISLZR workflow view

**Agent Model:**
```prisma
model Agent {
  id           String   @id @default(uuid())
  name         String   @unique
  type         String   // llm, rule_based, api_tool, human
  capabilities String[] // code_review, security_scan, deploy, test
  endpoint     String?  // HTTP endpoint or NATS subject
  apiKey       String?  // Encrypted
  config       Json?    // Agent-specific configuration
  active       Boolean  @default(true)
  createdAt    DateTime @default(now())
}

model Workflow {
  id          String          @id @default(uuid())
  name        String
  description String?
  trigger     Json            // Event filter
  steps       WorkflowStep[]
  status      String          // draft, active, paused
}

model WorkflowStep {
  id           String   @id @default(uuid())
  workflowId   String
  workflow     Workflow @relation(fields: [workflowId], references: [id])
  order        Int
  agentId      String
  agent        Agent    @relation(fields: [agentId], references: [id])
  condition    String?  // CEL expression
  onFail       String   // block, warn, continue
  parallel     Boolean  @default(false)
  config       Json?
}

model WorkflowExecution {
  id          String   @id @default(uuid())
  workflowId  String
  status      String   // running, completed, failed
  currentStep Int?
  context     Json     // Shared context between steps
  startedAt   DateTime @default(now())
  completedAt DateTime?
  logs        ExecutionLog[]
}

model ExecutionLog {
  id          String            @id @default(uuid())
  executionId String
  execution   WorkflowExecution @relation(fields: [executionId], references: [id])
  step        Int
  level       String            // info, warn, error
  message     String
  timestamp   DateTime          @default(now())
}
```

**Agent Registry API:**
```python
# agents/registry.py
@router.post("/api/agents/register")
async def register_agent(agent: AgentCreate):
    encrypted_key = encrypt_api_key(agent.api_key) if agent.api_key else None

    db_agent = await prisma.agent.create(
        data={
            "name": agent.name,
            "type": agent.type,
            "capabilities": agent.capabilities,
            "endpoint": agent.endpoint,
            "apiKey": encrypted_key,
            "config": agent.config
        }
    )

    # Publish registration event
    await nats.publish(
        f"hub.{HUB_ID}.agent.registered",
        {"agent_id": db_agent.id, "name": db_agent.name}
    )

    return db_agent

@router.get("/api/agents")
async def list_agents(capability: Optional[str] = None):
    where = {}
    if capability:
        where["capabilities"] = {"has": capability}

    return await prisma.agent.find_many(where=where)

@router.post("/api/agents/{agent_id}/invoke")
async def invoke_agent(agent_id: str, payload: dict):
    agent = await prisma.agent.find_unique(where={"id": agent_id})
    correlation_id = str(uuid.uuid4())

    # Publish to agent's NATS subject
    await nats.publish(
        f"agent.request.{agent.name}",
        {
            "correlation_id": correlation_id,
            "payload": payload
        }
    )

    # Wait for result (with timeout)
    result = await nats.request(
        f"agent.result.{correlation_id}",
        timeout=30
    )

    return json.loads(result.data)
```

**Workflow YAML Example:**
```yaml
# workflows/ci-pipeline.yaml
name: ci-pipeline
description: Continuous integration pipeline
trigger:
  event: hub.*.code.pushed
  condition: branch == 'main'

steps:
  - agent: linter
    on_fail: block

  - agent: test-runner
    parallel: true
    on_fail: block

  - agent: security-scan
    on_fail: warn

  - agent: deploy-staging
    condition: tests_passed && branch == 'main'
    on_fail: block
```

**Workflow Engine:**
```python
# agents/workflow_engine.py
class WorkflowEngine:
    async def execute_workflow(self, workflow_id: str, context: dict):
        workflow = await prisma.workflow.find_unique(
            where={"id": workflow_id},
            include={"steps": {"include": {"agent": True}}}
        )

        execution = await prisma.workflow_execution.create(
            data={
                "workflowId": workflow_id,
                "status": "running",
                "context": context
            }
        )

        try:
            steps = sorted(workflow.steps, key=lambda s: s.order)

            for step in steps:
                # Check condition
                if step.condition and not eval_condition(step.condition, context):
                    continue

                # Execute agent
                await self.log(execution.id, step.order, "info", f"Executing {step.agent.name}")

                try:
                    result = await self.invoke_agent(step.agent, context)
                    context.update(result)
                    await self.log(execution.id, step.order, "info", "Step completed")

                except Exception as e:
                    await self.log(execution.id, step.order, "error", str(e))

                    if step.onFail == "block":
                        raise
                    elif step.onFail == "warn":
                        await nats.publish(
                            f"hub.{HUB_ID}.workflow.warning",
                            {"execution_id": execution.id, "step": step.order, "error": str(e)}
                        )

            await prisma.workflow_execution.update(
                where={"id": execution.id},
                data={"status": "completed", "completedAt": datetime.utcnow()}
            )

        except Exception as e:
            await prisma.workflow_execution.update(
                where={"id": execution.id},
                data={"status": "failed", "completedAt": datetime.utcnow()}
            )
            raise

    async def invoke_agent(self, agent: Agent, context: dict) -> dict:
        if agent.endpoint:
            # HTTP agent
            response = await httpx.post(agent.endpoint, json=context)
            return response.json()
        else:
            # NATS agent
            correlation_id = str(uuid.uuid4())
            await nats.publish(f"agent.request.{agent.name}", {
                "correlation_id": correlation_id,
                "context": context
            })

            result = await nats.request(f"agent.result.{correlation_id}", timeout=60)
            return json.loads(result.data)

    async def log(self, execution_id: str, step: int, level: str, message: str):
        await prisma.execution_log.create(
            data={
                "executionId": execution_id,
                "step": step,
                "level": level,
                "message": message
            }
        )

        # Also publish to NATS for real-time monitoring
        await nats.publish(
            f"hub.{HUB_ID}.workflow.log",
            {
                "execution_id": execution_id,
                "step": step,
                "level": level,
                "message": message
            }
        )
```

**Event-Driven Trigger:**
```python
# agents/triggers.py
async def handle_event_triggers(event: Event):
    # Find workflows triggered by this event
    workflows = await prisma.workflow.find_many(
        where={"status": "active"}
    )

    for workflow in workflows:
        trigger = workflow.trigger

        # Check if event matches trigger
        if event.subject.startswith(trigger.get("event", "").replace("*", "")):
            condition = trigger.get("condition")

            if not condition or eval_condition(condition, event.payload):
                # Execute workflow
                engine = WorkflowEngine()
                await engine.execute_workflow(
                    workflow.id,
                    context={"event": event.payload, "correlation_id": event.correlation_id}
                )

# Subscribe to all events
await nats.subscribe("hub.>", cb=handle_event_triggers)
```

**Agent-to-Agent Negotiation:**
```python
# agents/coordination.py
async def agent_negotiate(task_id: str, primary_agent: str, secondary_agent: str):
    """
    Allow agents to coordinate on task execution.
    Example: Security agent defers to compliance agent for regulatory checks.
    """
    negotiation_id = str(uuid.uuid4())

    # Primary agent proposes approach
    await nats.publish(
        f"agent.negotiate.{negotiation_id}",
        {
            "task_id": task_id,
            "primary": primary_agent,
            "secondary": secondary_agent,
            "proposal": "I'll handle SAST, you handle compliance mapping"
        }
    )

    # Secondary agent responds
    response = await nats.request(
        f"agent.negotiate.{negotiation_id}.response",
        timeout=10
    )

    agreement = json.loads(response.data)

    # Store shared context in Redis
    await redis.set(
        f"agent:context:{task_id}",
        json.dumps(agreement),
        ex=3600  # 1 hour TTL
    )

    return agreement
```

**VISLZR Workflow View:**
```tsx
// app/workflows/page.tsx
'use client'

import { useQuery, useSubscription } from '@apollo/client'
import { WORKFLOW_EXECUTION } from '@/lib/graphql/queries'
import ReactFlow, { Node, Edge } from 'reactflow'

export default function WorkflowPage({ executionId }: { executionId: string }) {
  const { data } = useQuery(WORKFLOW_EXECUTION, {
    variables: { executionId }
  })

  // Subscribe to real-time logs
  useSubscription(WORKFLOW_LOGS, {
    variables: { executionId },
    onData: ({ data: logData }) => {
      // Update node status based on logs
    }
  })

  const nodes: Node[] = data?.workflowExecution.workflow.steps.map((step, idx) => ({
    id: step.id,
    type: 'workflow-step',
    position: { x: idx * 200, y: 100 },
    data: {
      label: step.agent.name,
      status: getStepStatus(step.order, data.workflowExecution.currentStep),
      logs: data.workflowExecution.logs.filter(l => l.step === step.order)
    }
  })) || []

  const edges: Edge[] = nodes.slice(0, -1).map((node, idx) => ({
    id: `${node.id}-${nodes[idx + 1].id}`,
    source: node.id,
    target: nodes[idx + 1].id,
    animated: data?.workflowExecution.status === 'running'
  }))

  return (
    <div className="h-screen">
      <ReactFlow nodes={nodes} edges={edges} fitView />
    </div>
  )
}

function getStepStatus(stepOrder: number, currentStep?: number) {
  if (!currentStep) return 'pending'
  if (stepOrder < currentStep) return 'success'
  if (stepOrder === currentStep) return 'running'
  return 'pending'
}
```

**Success Criteria:**
- [ ] Agent registry API functional
- [ ] Workflows execute from YAML definitions
- [ ] Event-driven triggers work
- [ ] Agent-to-agent coordination implemented
- [ ] VISLZR shows live workflow progress
- [ ] Workflow logs visible in real-time

---

## Phase 11-12: Compliance & Autonomous Intelligence

**Timeline:** Weeks 25-32
**Goal:** Continuous compliance, security automation, and predictive self-healing

### Phase 11: Compliance, Security & Partner Interfaces (Weeks 25-27)

**Deliverables:**
- Compliance policy engine
- Security command surface
- Partner API gateway
- Continuous attestation system
- VISLZR compliance view

**Compliance Model:**
```prisma
model Policy {
  id          String       @id @default(uuid())
  name        String       @unique
  category    String       // regulatory, security, privacy, licensing
  rules       PolicyRule[]
  severity    String       // critical, high, medium, low
  active      Boolean      @default(true)
  description String?
}

model PolicyRule {
  id          String  @id @default(uuid())
  policyId    String
  policy      Policy  @relation(fields: [policyId], references: [id])
  expression  String  // CEL expression or Python predicate
  message     String  // Violation message
  remediation String? // Suggested fix
}

model ComplianceCheck {
  id          String   @id @default(uuid())
  policyId    String
  targetEntity String  // File, Symbol, Service, Project
  targetId    String
  status      String   // pass, fail, warn
  violations  Json[]   // List of rule violations
  checkedAt   DateTime @default(now())

  @@index([targetEntity, targetId])
}

model Attestation {
  id          String   @id @default(uuid())
  projectId   String
  type        String   // compliance, security, audit
  status      String   // passed, failed, partial
  summary     Json     // Overview of checks
  signature   String   // Cryptographic signature
  ipfsHash    String?  // Optional IPFS storage
  createdAt   DateTime @default(now())
  expiresAt   DateTime
}
```

**Policy Engine:**
```python
# compliance/policy_engine.py
class PolicyEngine:
    async def check_compliance(
        self,
        target_entity: str,
        target_id: str,
        category: Optional[str] = None
    ) -> ComplianceCheck:
        # Get applicable policies
        where = {"active": True}
        if category:
            where["category"] = category

        policies = await prisma.policy.find_many(
            where=where,
            include={"rules": True}
        )

        violations = []

        for policy in policies:
            for rule in policy.rules:
                # Evaluate rule
                passed = await self.evaluate_rule(
                    rule,
                    target_entity,
                    target_id
                )

                if not passed:
                    violations.append({
                        "policy": policy.name,
                        "rule": rule.id,
                        "message": rule.message,
                        "severity": policy.severity,
                        "remediation": rule.remediation
                    })

        status = "pass" if not violations else "fail"

        check = await prisma.compliance_check.create(
            data={
                "policyId": policies[0].id,
                "targetEntity": target_entity,
                "targetId": target_id,
                "status": status,
                "violations": violations
            }
        )

        # Publish event
        await nats.publish(
            f"hub.{HUB_ID}.compliance.checked",
            {
                "check_id": check.id,
                "target": f"{target_entity}:{target_id}",
                "status": status,
                "violations_count": len(violations)
            }
        )

        return check

    async def evaluate_rule(
        self,
        rule: PolicyRule,
        target_entity: str,
        target_id: str
    ) -> bool:
        # Fetch target data
        target = await self.get_target(target_entity, target_id)

        # Evaluate CEL expression or Python predicate
        if rule.expression.startswith("cel:"):
            return eval_cel(rule.expression[4:], target)
        else:
            # Python expression
            return eval(rule.expression, {"target": target})

    async def get_target(self, entity: str, id: str):
        if entity == "File":
            return await prisma.file.find_unique(where={"id": id})
        elif entity == "Symbol":
            return await prisma.symbol.find_unique(where={"id": id})
        # ... other entities
```

**Predefined Policies (Example):**
```python
# compliance/policies/regulatory.py
MICA_COMPLIANCE = {
    "name": "MiCA Compliance",
    "category": "regulatory",
    "severity": "critical",
    "rules": [
        {
            "expression": "cel:target.kind == 'Class' && 'crypto' in target.name.lower() && !has(target.metadata.license)",
            "message": "Crypto-related code requires explicit licensing per MiCA Article 5",
            "remediation": "Add license header and update metadata"
        },
        {
            "expression": "target.file.path.contains('transaction') && not target.metadata.get('audit_trail')",
            "message": "Transaction handling requires audit trail per MiCA Article 12",
            "remediation": "Implement audit logging for all transaction operations"
        }
    ]
}

GDPR_PRIVACY = {
    "name": "GDPR Privacy",
    "category": "privacy",
    "severity": "high",
    "rules": [
        {
            "expression": "any(target.dependencies, d.toSymbol.name in ['email', 'phone', 'address']) && !target.metadata.get('pii_handling')",
            "message": "PII handling requires privacy controls per GDPR Article 25",
            "remediation": "Implement data minimization and purpose limitation"
        }
    ]
}
```

**Security Command Surface:**
```python
# compliance/security.py
@router.get("/api/security/overview")
async def security_overview():
    # Aggregate security audits
    audits = await prisma.audit.find_many(
        where={"kind": "security"},
        order_by={"createdAt": "desc"}
    )

    # Group by severity
    by_severity = defaultdict(list)
    for audit in audits:
        severity = audit.summary.get("severity", "unknown")
        by_severity[severity].append(audit)

    # CVE tracking
    cves = []
    for audit in audits:
        if "cve" in audit.summary:
            cves.extend(audit.summary["cve"])

    # License compliance
    license_audits = await prisma.audit.find_many(
        where={"kind": "license"}
    )

    return {
        "vulnerabilities": {
            "critical": len(by_severity["critical"]),
            "high": len(by_severity["high"]),
            "medium": len(by_severity["medium"]),
            "low": len(by_severity["low"])
        },
        "open_cves": cves,
        "license_issues": [
            a for a in license_audits if a.status == "fail"
        ],
        "last_scan": max(a.createdAt for a in audits) if audits else None
    }

@router.post("/api/security/scan")
async def trigger_security_scan(project_id: str):
    """Trigger comprehensive security scan"""

    # SAST scan
    await nats.publish(
        "agent.request.sast-scanner",
        {"project_id": project_id}
    )

    # SCA scan
    await nats.publish(
        "agent.request.sca-scanner",
        {"project_id": project_id}
    )

    # Container scan
    await nats.publish(
        "agent.request.container-scanner",
        {"project_id": project_id}
    )

    return {"status": "scans_triggered", "project_id": project_id}
```

**Partner API Gateway:**
```python
# compliance/partner_api.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/partner/v1")
security = HTTPBearer()

async def verify_partner_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> PartnerKey:
    # Verify HMAC signature
    key = await prisma.partner_key.find_unique(
        where={"key_hash": hash_api_key(credentials.credentials)}
    )

    if not key or not key.active:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return key

@router.get("/projects/{project_id}/metrics")
async def get_project_metrics(
    project_id: str,
    key: PartnerKey = Depends(verify_partner_key)
):
    # Verify access
    if not has_project_access(key, project_id):
        raise HTTPException(status_code=403, detail="Access denied")

    metrics = await prisma.global_metrics.find_many(
        where={"projectId": project_id}
    )

    return {
        "project_id": project_id,
        "metrics": [
            {
                "type": m.metricType,
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp
            }
            for m in metrics
        ]
    }

@router.get("/projects/{project_id}/audits")
async def get_project_audits(
    project_id: str,
    kind: Optional[str] = None,
    key: PartnerKey = Depends(verify_partner_key)
):
    if not has_project_access(key, project_id):
        raise HTTPException(status_code=403, detail="Access denied")

    where = {"targetEntity": "Project", "targetId": project_id}
    if kind:
        where["kind"] = kind

    audits = await prisma.audit.find_many(where=where)

    return {
        "project_id": project_id,
        "audits": [
            {
                "id": a.id,
                "kind": a.kind,
                "status": a.status,
                "summary": a.summary,
                "created_at": a.createdAt
            }
            for a in audits
        ]
    }

@router.get("/attestations/{attestation_id}")
async def get_attestation(
    attestation_id: str,
    key: PartnerKey = Depends(verify_partner_key)
):
    attestation = await prisma.attestation.find_unique(
        where={"id": attestation_id}
    )

    if not attestation:
        raise HTTPException(status_code=404, detail="Attestation not found")

    # Verify signature
    is_valid = verify_signature(
        attestation.summary,
        attestation.signature,
        get_hub_public_key()
    )

    return {
        "id": attestation.id,
        "project_id": attestation.projectId,
        "type": attestation.type,
        "status": attestation.status,
        "summary": attestation.summary,
        "signature": attestation.signature,
        "signature_valid": is_valid,
        "ipfs_hash": attestation.ipfsHash,
        "created_at": attestation.createdAt,
        "expires_at": attestation.expiresAt
    }
```

**Continuous Attestation:**
```python
# compliance/attestation.py
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import ipfshttpclient

class AttestationService:
    def __init__(self):
        self.private_key = load_hub_private_key()

    async def generate_attestation(
        self,
        project_id: str,
        attestation_type: str = "compliance"
    ) -> Attestation:
        # Gather audit data
        audits = await prisma.audit.find_many(
            where={
                "targetEntity": "Project",
                "targetId": project_id
            }
        )

        # Compute compliance status
        compliance_checks = await prisma.compliance_check.find_many(
            where={"targetEntity": "Project", "targetId": project_id}
        )

        total_checks = len(compliance_checks)
        passed_checks = len([c for c in compliance_checks if c.status == "pass"])

        summary = {
            "project_id": project_id,
            "type": attestation_type,
            "total_audits": len(audits),
            "passed_audits": len([a for a in audits if a.status == "ok"]),
            "compliance_ratio": passed_checks / total_checks if total_checks > 0 else 0,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Sign summary
        signature = self.sign_data(summary)

        # Optional: Publish to IPFS
        ipfs_hash = None
        if os.getenv("ENABLE_IPFS") == "true":
            ipfs_hash = await self.publish_to_ipfs(summary, signature)

        # Store attestation
        attestation = await prisma.attestation.create(
            data={
                "projectId": project_id,
                "type": attestation_type,
                "status": "passed" if summary["compliance_ratio"] >= 0.9 else "failed",
                "summary": summary,
                "signature": signature,
                "ipfsHash": ipfs_hash,
                "expiresAt": datetime.utcnow() + timedelta(days=90)
            }
        )

        # Publish event
        await nats.publish(
            f"hub.{HUB_ID}.attestation.generated",
            {
                "attestation_id": attestation.id,
                "project_id": project_id,
                "status": attestation.status
            }
        )

        return attestation

    def sign_data(self, data: dict) -> str:
        data_bytes = json.dumps(data, sort_keys=True).encode()
        signature = self.private_key.sign(
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()

    async def publish_to_ipfs(self, summary: dict, signature: str) -> str:
        client = ipfshttpclient.connect()

        attestation_doc = {
            "summary": summary,
            "signature": signature,
            "hub_id": HUB_ID,
            "timestamp": datetime.utcnow().isoformat()
        }

        result = client.add_json(attestation_doc)
        return result

# CLI command
# hub attestation:generate --project veria --publish
```

**VISLZR Compliance View:**
```tsx
// components/compliance/ComplianceOverlay.tsx
'use client'

import { useQuery } from '@apollo/client'
import { COMPLIANCE_STATUS } from '@/lib/graphql/queries'

export function ComplianceOverlay({ projectId }: { projectId: string }) {
  const { data } = useQuery(COMPLIANCE_STATUS, {
    variables: { projectId }
  })

  // Color-code nodes by compliance status
  const getNodeColor = (nodeId: string, entity: string) => {
    const checks = data?.complianceChecks.filter(
      c => c.targetId === nodeId && c.targetEntity === entity
    ) || []

    if (checks.length === 0) return 'gray'
    if (checks.every(c => c.status === 'pass')) return 'green'
    if (checks.some(c => c.status === 'fail')) return 'red'
    return 'yellow'
  }

  return (
    <div className="compliance-overlay">
      {/* Render compliance badges on nodes */}
    </div>
  )
}
```

**Success Criteria:**
- [ ] Policy engine evaluates compliance rules
- [ ] Security dashboard aggregates vulnerabilities
- [ ] Partner API authenticated and functional
- [ ] Attestations generated and signed
- [ ] VISLZR shows compliance status overlay

---

### Phase 12: Autonomous Mesh & Predictive Intelligence (Weeks 28-32)

**Deliverables:**
- Predictive health & risk models
- Auto-remediation framework
- Adaptive load balancing
- Knowledge evolution loop
- VISLZR autonomy view

**Predictive Models Schema:**
```prisma
model Prediction {
  id            String   @id @default(uuid())
  modelType     String   // failure_risk, regression_risk, compliance_drift
  targetEntity  String
  targetId      String
  probability   Float    // 0.0 - 1.0
  confidence    Float    // 0.0 - 1.0
  features      Json     // Input features used
  recommendation String? // Suggested action
  createdAt     DateTime @default(now())

  @@index([targetEntity, targetId, createdAt])
}

model RemediationAction {
  id           String   @id @default(uuid())
  predictionId String
  action       String   // restart_service, create_task, trigger_audit, auto_pr
  status       String   // pending_approval, approved, executed, failed
  approvedBy   String?  // User ID if manual approval
  executedAt   DateTime?
  result       Json?
}

model ModelTraining {
  id           String   @id @default(uuid())
  modelType    String
  version      String
  trainedAt    DateTime @default(now())
  metrics      Json     // accuracy, precision, recall, f1
  featureSet   String[]
  datasetSize  Int
}
```

**Predictive Models:**
```python
# intelligence/models/failure_predictor.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

class FailurePredictor:
    def __init__(self):
        self.model = None
        self.feature_columns = [
            'health_samples_last_hour',
            'avg_latency_ms',
            'error_rate',
            'days_since_deploy',
            'dependency_updates_pending',
            'audit_failures_last_week'
        ]

    async def train(self):
        # Fetch historical data
        services = await prisma.service.find_many()
        health_samples = await prisma.health_sample.find_many()

        # Build training dataset
        data = []
        for service in services:
            samples = [s for s in health_samples if s.serviceId == service.id]

            # Extract features
            features = self.extract_features(service, samples)

            # Label: 1 if service went down in next 24 hours, 0 otherwise
            label = self.check_failure_occurred(service, samples)

            data.append({**features, 'failed': label})

        df = pd.DataFrame(data)

        X = df[self.feature_columns]
        y = df['failed']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        # Train model
        self.model = RandomForestClassifier(n_estimators=100)
        self.model.fit(X_train, y_train)

        # Evaluate
        accuracy = self.model.score(X_test, y_test)

        # Save model
        joblib.dump(self.model, 'models/failure_predictor.pkl')

        # Record training
        await prisma.model_training.create(
            data={
                "modelType": "failure_risk",
                "version": "1.0",
                "metrics": {"accuracy": accuracy},
                "featureSet": self.feature_columns,
                "datasetSize": len(df)
            }
        )

        return accuracy

    def extract_features(self, service, samples):
        recent_samples = [
            s for s in samples
            if s.observedAt > datetime.utcnow() - timedelta(hours=1)
        ]

        return {
            'health_samples_last_hour': len(recent_samples),
            'avg_latency_ms': sum(s.latencyMs or 0 for s in recent_samples) / max(len(recent_samples), 1),
            'error_rate': len([s for s in recent_samples if s.status == 'down']) / max(len(recent_samples), 1),
            'days_since_deploy': 7,  # TODO: Get from deployment history
            'dependency_updates_pending': 0,  # TODO: Get from package manager
            'audit_failures_last_week': 0  # TODO: Get from audits
        }

    async def predict(self, service_id: str) -> Prediction:
        service = await prisma.service.find_unique(where={"id": service_id})
        samples = await prisma.health_sample.find_many(
            where={"serviceId": service_id}
        )

        features = self.extract_features(service, samples)
        X = pd.DataFrame([features])[self.feature_columns]

        probability = self.model.predict_proba(X)[0][1]  # Probability of failure
        confidence = max(self.model.predict_proba(X)[0])

        recommendation = None
        if probability > 0.7:
            recommendation = "trigger_preventive_health_check"
        elif probability > 0.5:
            recommendation = "monitor_closely"

        prediction = await prisma.prediction.create(
            data={
                "modelType": "failure_risk",
                "targetEntity": "Service",
                "targetId": service_id,
                "probability": probability,
                "confidence": confidence,
                "features": features,
                "recommendation": recommendation
            }
        )

        # Publish event
        await nats.publish(
            f"hub.{HUB_ID}.prediction.generated",
            {
                "prediction_id": prediction.id,
                "target": f"Service:{service_id}",
                "probability": probability,
                "recommendation": recommendation
            }
        )

        return prediction

# Run predictions every 15 minutes
async def prediction_loop():
    predictor = FailurePredictor()
    await predictor.train()  # Initial training

    while True:
        services = await prisma.service.find_many()

        for service in services:
            await predictor.predict(service.id)

        await asyncio.sleep(900)  # 15 minutes
```

**Auto-Remediation Framework:**
```python
# intelligence/remediation/auto_remediate.py
class AutoRemediationEngine:
    async def handle_prediction(self, prediction: Prediction):
        if not prediction.recommendation:
            return

        # Check confidence threshold
        if prediction.confidence < 0.9:
            # Require human approval
            await self.request_approval(prediction)
            return

        # Execute remediation automatically
        action = await self.execute_remediation(prediction)

        await prisma.remediation_action.update(
            where={"id": action.id},
            data={"status": "executed", "executedAt": datetime.utcnow()}
        )

    async def request_approval(self, prediction: Prediction):
        action = await prisma.remediation_action.create(
            data={
                "predictionId": prediction.id,
                "action": prediction.recommendation,
                "status": "pending_approval"
            }
        )

        # Publish approval request
        await nats.publish(
            "agent.approval.required",
            {
                "action_id": action.id,
                "prediction": {
                    "target": f"{prediction.targetEntity}:{prediction.targetId}",
                    "probability": prediction.probability,
                    "confidence": prediction.confidence
                },
                "recommendation": prediction.recommendation
            }
        )

        # Set timeout for approval (24 hours)
        await asyncio.create_task(self.approval_timeout(action.id))

    async def approval_timeout(self, action_id: str):
        await asyncio.sleep(86400)  # 24 hours

        action = await prisma.remediation_action.find_unique(
            where={"id": action_id}
        )

        if action.status == "pending_approval":
            # Escalate or abort
            await nats.publish(
                "hub.global.escalation",
                {
                    "action_id": action_id,
                    "reason": "approval_timeout"
                }
            )

    async def execute_remediation(self, prediction: Prediction) -> RemediationAction:
        action = await prisma.remediation_action.create(
            data={
                "predictionId": prediction.id,
                "action": prediction.recommendation,
                "status": "approved"
            }
        )

        if prediction.recommendation == "trigger_preventive_health_check":
            # Execute health check
            await nats.publish(
                f"agent.request.health-checker",
                {
                    "target_entity": prediction.targetEntity,
                    "target_id": prediction.targetId
                }
            )

        elif prediction.recommendation == "auto_pr_patch":
            # Create PR with fix
            await nats.publish(
                "agent.request.auto-patcher",
                {
                    "target_entity": prediction.targetEntity,
                    "target_id": prediction.targetId,
                    "prediction_id": prediction.id
                }
            )

        elif prediction.recommendation == "restart_service":
            # Restart service
            service_id = prediction.targetId
            await orchestration_service.restart_service(service_id)

        return action

# Subscribe to prediction events
async def handle_prediction_event(msg):
    prediction_id = json.loads(msg.data)["prediction_id"]
    prediction = await prisma.prediction.find_unique(where={"id": prediction_id})

    engine = AutoRemediationEngine()
    await engine.handle_prediction(prediction)

await nats.subscribe("hub.*.prediction.generated", cb=handle_prediction_event)
```

**Adaptive Load Balancing:**
```python
# intelligence/scheduler/adaptive_scheduler.py
class AdaptiveScheduler:
    async def schedule_task(self, task_id: str):
        task = await prisma.task.find_unique(where={"id": task_id})

        # Compute priority score
        priority_score = self.compute_priority(task)

        # Find available agents
        agents = await prisma.agent.find_many(
            where={
                "active": True,
                "capabilities": {"has": task.kind}
            }
        )

        # Get agent workloads
        workloads = await self.get_agent_workloads(agents)

        # Assign to least loaded agent
        selected_agent = min(workloads, key=lambda x: x["load"])

        # Execute task
        await nats.publish(
            f"agent.request.{selected_agent['name']}",
            {
                "task_id": task_id,
                "priority": priority_score
            }
        )

        # Update task
        await prisma.task.update(
            where={"id": task_id},
            data={"assignee": selected_agent["id"], "status": "inProgress"}
        )

    def compute_priority(self, task: Task) -> float:
        # Factors: urgency, impact, dependencies
        urgency = 1.0  # TODO: Based on SLA or deadline
        impact = 0.5   # TODO: Based on affected users/systems

        return urgency * 0.7 + impact * 0.3

    async def get_agent_workloads(self, agents: list[Agent]) -> list[dict]:
        workloads = []

        for agent in agents:
            # Count in-progress tasks
            tasks = await prisma.task.count(
                where={
                    "assignee": agent.id,
                    "status": "inProgress"
                }
            )

            workloads.append({
                "id": agent.id,
                "name": agent.name,
                "load": tasks
            })

        return workloads
```

**Knowledge Evolution Loop:**
```python
# intelligence/learning/knowledge_loop.py
class KnowledgeEvolutionLoop:
    async def record_experience(
        self,
        agent_id: str,
        context: dict,
        action: str,
        outcome: dict
    ):
        # Store in vector memory (using KnowledgeBeast)
        from knowledgebeast import KnowledgeBeast

        kb = KnowledgeBeast(collection=f"agent-memory-{agent_id}")

        experience = {
            "context": context,
            "action": action,
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat()
        }

        await kb.add_document(
            content=json.dumps(experience),
            metadata={
                "agent_id": agent_id,
                "action": action,
                "success": outcome.get("success", False)
            }
        )

    async def learn_optimal_action(
        self,
        agent_id: str,
        context: dict
    ) -> str:
        # Query similar experiences
        kb = KnowledgeBeast(collection=f"agent-memory-{agent_id}")

        results = await kb.query(
            query=json.dumps(context),
            top_k=10
        )

        # Find most successful action
        action_scores = defaultdict(list)

        for result in results:
            exp = json.loads(result["content"])
            action = exp["action"]
            success = exp["outcome"].get("success", False)

            action_scores[action].append(1.0 if success else 0.0)

        # Return action with highest average success rate
        best_action = max(
            action_scores.items(),
            key=lambda x: sum(x[1]) / len(x[1])
        )[0]

        return best_action

    async def retrain_models(self):
        # Periodic retraining of all predictive models
        predictor = FailurePredictor()
        accuracy = await predictor.train()

        logger.info(f"Retrained failure predictor: accuracy={accuracy}")

        # TODO: Add more model types
        # - Regression risk predictor
        # - Compliance drift predictor
        # - Performance degradation predictor

# Run retraining weekly
async def retraining_loop():
    loop = KnowledgeEvolutionLoop()

    while True:
        await loop.retrain_models()
        await asyncio.sleep(604800)  # 1 week
```

**VISLZR Autonomy View:**
```tsx
// app/autonomy/page.tsx
'use client'

import { useQuery } from '@apollo/client'
import { PREDICTIONS, REMEDIATION_ACTIONS } from '@/lib/graphql/queries'
import { HeatMap } from '@/components/autonomy/HeatMap'
import { PredictionTimeline } from '@/components/autonomy/PredictionTimeline'

export default function AutonomyPage({ projectId }: { projectId: string }) {
  const { data: predictions } = useQuery(PREDICTIONS, {
    variables: { projectId }
  })

  const { data: actions } = useQuery(REMEDIATION_ACTIONS, {
    variables: { projectId }
  })

  return (
    <div className="h-screen p-6">
      <h1 className="text-2xl font-bold mb-6">Autonomous Intelligence</h1>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Risk Heat Map</h2>
          <HeatMap predictions={predictions} />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Prediction Timeline</h2>
          <PredictionTimeline predictions={predictions} actions={actions} />
        </div>
      </div>
    </div>
  )
}
```

```tsx
// components/autonomy/HeatMap.tsx
'use client'

import { useMemo } from 'react'

export function HeatMap({ predictions }: { predictions: any[] }) {
  const heatmapData = useMemo(() => {
    // Group predictions by target
    const groups = predictions.reduce((acc, p) => {
      const key = `${p.targetEntity}:${p.targetId}`
      if (!acc[key]) acc[key] = []
      acc[key].push(p)
      return acc
    }, {})

    // Compute risk score per target
    return Object.entries(groups).map(([target, preds]: [string, any[]]) => {
      const avgProbability = preds.reduce((sum, p) => sum + p.probability, 0) / preds.length
      const avgConfidence = preds.reduce((sum, p) => sum + p.confidence, 0) / preds.length

      return {
        target,
        risk: avgProbability,
        confidence: avgConfidence,
        color: getRiskColor(avgProbability)
      }
    })
  }, [predictions])

  return (
    <div className="grid grid-cols-5 gap-2">
      {heatmapData.map(item => (
        <div
          key={item.target}
          className="h-20 rounded flex items-center justify-center text-white text-sm"
          style={{ backgroundColor: item.color }}
          title={`Risk: ${(item.risk * 100).toFixed(1)}%`}
        >
          {item.target.split(':')[1].slice(0, 8)}
        </div>
      ))}
    </div>
  )
}

function getRiskColor(risk: number): string {
  if (risk > 0.7) return '#ef4444'      // red
  if (risk > 0.5) return '#f97316'      // orange
  if (risk > 0.3) return '#eab308'      // yellow
  return '#22c55e'                       // green
}
```

**Success Criteria:**
- [ ] Predictive models trained and running
- [ ] Predictions generated every 15 minutes
- [ ] Auto-remediation executes for high-confidence predictions
- [ ] Human approval required for low-confidence
- [ ] Adaptive scheduling balances agent workloads
- [ ] Knowledge loop records and learns from experiences
- [ ] VISLZR autonomy view shows risk heat map

---

## Implementation Timeline

| Weeks | Phase | Key Deliverables | Success Metrics |
|-------|-------|------------------|-----------------|
| 1 | Phase 1 | Event system, NATS integration | Events persist, pub/sub works |
| 2-3 | Phases 2-3 | Correlation, streaming, replay | All requests correlated, CLI functional |
| 4 | Phase 4 | NATS bridge, JSON-RPC | Bidirectional sync working |
| 5 | Phase 5 | Federation prep, presence | Hubs discovered automatically |
| 6-8 | Phase 6 | Health checks, service discovery | Dashboard shows all Hubs |
| 9-12 | Phase 7 | Graph-Service, ingestion | Code parsed, GraphQL queries work |
| 13-16 | Phase 8 | VISLZR frontend | Interactive visualization live |
| 17-20 | Phase 9 | Federation, global insights | Ecosystem graph rendered |
| 21-24 | Phase 10 | Agent orchestration, workflows | Workflows execute from YAML |
| 25-27 | Phase 11 | Compliance, partner API | Attestations generated |
| 28-32 | Phase 12 | Predictive intelligence, auto-remediation | Predictions accurate, remediation works |

**Total Duration:** 32 weeks (~8 months)

---

## Testing Strategy

### Unit Tests
- All services, models, and utilities
- Target: 80%+ code coverage
- Framework: pytest (backend), Jest (frontend)

### Integration Tests
- End-to-end flows across modules
- NATS message handling
- GraphQL queries
- Workflow execution

### Performance Tests
- Graph query performance (< 2s for 1000 nodes)
- Event streaming throughput (> 1000 events/sec)
- Prediction latency (< 5s per prediction)

### Security Tests
- API authentication/authorization
- Partner API key validation
- Signature verification
- Input validation

---

## Migration Strategy

### Phase-by-Phase Rollout
1. Deploy new modules alongside existing Hub
2. Feature flags for gradual enablement
3. Shadow mode for testing (predictions run but don't remediate)
4. Progressive rollout per project

### Data Migration
- Graph ingestion runs in background
- Existing projects indexed incrementally
- No disruption to current Hub operations

### Rollback Plan
- Each phase independently deployable
- Feature flags allow instant disable
- Database migrations reversible (Alembic downgrade)

---

## Monitoring & Observability

### Key Metrics
- Event throughput (events/sec)
- Graph query latency (p50, p95, p99)
- Prediction accuracy (precision, recall)
- Remediation success rate
- Agent task completion time

### Dashboards
- Existing Grafana dashboards extended
- New dashboards:
  - Event bus health
  - Graph ingestion progress
  - Prediction model performance
  - Compliance status overview

### Alerts
- High prediction error rate
- Graph ingestion failures
- NATS connection lost
- Compliance violations

---

## Success Criteria

**Phase 1-6 Complete:**
- ✅ Event-driven architecture operational
- ✅ Multiple Hubs federated and discovering each other
- ✅ Health monitoring automatic

**Phase 7-8 Complete:**
- ✅ Code graphs visualized for all projects
- ✅ Interactive VISLZR with real-time updates
- ✅ Node actions trigger audits/scans

**Phase 9-10 Complete:**
- ✅ Ecosystem-wide intelligence aggregated
- ✅ Agents orchestrated via workflows
- ✅ Event-driven automation functional

**Phase 11-12 Complete:**
- ✅ Continuous compliance attestation
- ✅ Predictive models accurate (>80%)
- ✅ Auto-remediation reducing incidents
- ✅ Full autonomous mesh operational

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| NATS learning curve | Delayed Phase 4 | Medium | Prototype early, use examples |
| Prisma Python maturity | Graph-Service complexity | Medium | Fallback to SQLAlchemy + raw SQL |
| Prediction accuracy | Low trust in auto-remediation | High | Start with shadow mode, human-in-loop |
| Performance at scale | Slow graph queries | Medium | Indexing strategy, caching, pagination |
| Scope creep | Timeline slips | High | Strict phase boundaries, MVP focus |

---

## Next Steps

1. **Approval:** Review and approve this design document
2. **Worktree Setup:** Create isolated development environment
3. **Implementation Plan:** Generate detailed task breakdown with `/write-plan`
4. **Phase 1 Kickoff:** Begin event system implementation

---

**End of Design Document**
