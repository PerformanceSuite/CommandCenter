# CommandCenter Architecture Diagrams

This directory contains Mermaid diagrams documenting the CommandCenter architecture.

## Diagrams

### 1. CommandCenter High-Level Architecture
**File**: `commandcenter-architecture.mmd`

**Overview**: Complete system architecture showing all major components, services, and integrations.

**Key Components**:
- **External Systems**: GitHub API, AI APIs (Anthropic, OpenAI), Web Sources (RSS, ArXiv, HackerNews)
- **CommandCenter Hub**: Multi-project orchestration layer (Ports 9000-9002)
  - Hub Frontend (React + TypeScript)
  - Hub Backend (FastAPI + Python 3.11)
  - Orchestration Service (Node.js + Dagger SDK)
- **Message Bus**: NATS JetStream for event streaming
- **CommandCenter Instance**: Single project instance (Ports 3000, 8000)
  - Frontend (React + Vite)
  - Backend (FastAPI)
  - Background Workers (Celery, Celery Beat, Flower)
  - Data Layer (PostgreSQL 16 + pgvector, Redis 7)
- **Knowledge Layer**: KnowledgeBeast v3.0 with local embeddings
- **Federation Service**: Cross-project catalog and synchronization
- **Observability Stack**: Prometheus, Grafana (5 dashboards), AlertManager, OpenTelemetry, Tempo
- **Hub Modules**: MRKTZR (AI Marketing), VISLZR (Code Visualization)
- **Tools**: Agent Sandboxes (E2B), GraphVis

**Data Flow**:
- GitHub → Backend (repository syncing)
- AI APIs → Backend (LLM queries)
- Backend → NATS (event publishing)
- Hub Orchestration → Docker (container management via Dagger)
- Backend → PostgreSQL + pgvector (vector search)
- Celery → Redis (job queue)

---

### 2. Hub Internal Architecture
**File**: `hub-internal-architecture.mmd`

**Overview**: Detailed view of the CommandCenter Hub internal structure, showing all modules, services, and their relationships.

**Key Components**:

#### Hub Frontend (React)
- **Pages**: Dashboard, Project Detail, Create Project, Monitoring
- **Components**: ProjectCard, Task Monitor, Log Viewer, Event Stream

#### Hub Backend (FastAPI)
- **API Routers**:
  - `/api/projects` - Project CRUD
  - `/api/orchestration` - Start/Stop/Status
  - `/api/events` - Event query & streaming
  - `/api/health` - Service health checks
  - `/api/tasks` - Background job management
  - `/api/logs` - Container logs
  - `/api/filesystem` - Directory browser

- **Core Services**:
  - ProjectService - Project management
  - OrchestrationService - Dagger integration
  - EventService - NATS publisher/subscriber
  - TaskService - Celery job management
  - HealthService - Service discovery

- **Background Workers**:
  - Celery Worker - Async operations
  - Celery Beat - Health checks
  - Flower - Task dashboard

#### Hub Orchestration (Node.js)
- **Workflow Engine**:
  - WorkflowRunner - Execute workflows
  - Workflow API - REST endpoints
  - Workflow DB - Prisma + PostgreSQL

- **Template System**:
  - TemplateResolver - Mustache templates
  - Template Store - Workflow definitions

- **Agent Integration**:
  - Dagger Client - Container orchestration
  - Agent Executor - Sandbox management

#### Hub Modules
- **MRKTZR** (Marketing Intelligence):
  - MRKTZR UI (Port 3003)
  - MRKTZR API (Genkit + Gemini)
  - Content Generator (AI social posts)

- **VISLZR** (Visualization - Planned):
  - Next.js App
  - Graph Service

- **Observability Module**:
  - Prometheus Config
  - Grafana Dashboards (5 dashboards)
  - AlertManager Rules (5 rules)
  - OpenTelemetry Collector

#### Data Storage
- Hub Database (SQLite/PostgreSQL) - Projects registry
- Orchestration DB (PostgreSQL) - Workflows & agents
- Redis - Celery broker & cache
- NATS JetStream - Event bus

#### External Integrations
- Docker Engine - Container runtime
- E2B Sandboxes - Agent execution
- Gemini API - AI generation

---

## Viewing the Diagrams

### In VS Code
1. Install the "Markdown Preview Mermaid Support" extension
2. Open any `.mmd` file
3. Right-click → "Open Preview" or press `Ctrl+Shift+V` (Windows/Linux) / `Cmd+Shift+V` (Mac)

### In GitHub
GitHub automatically renders Mermaid diagrams in Markdown files. Include them like this:

\`\`\`mermaid
{{< include commandcenter-architecture.mmd >}}
\`\`\`

### Online Mermaid Editor
1. Visit https://mermaid.live
2. Copy the contents of any `.mmd` file
3. Paste into the editor to view and edit

### Export to PNG/SVG
Using Mermaid CLI:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i commandcenter-architecture.mmd -o commandcenter-architecture.png
mmdc -i hub-internal-architecture.mmd -o hub-internal-architecture.svg
```

---

## Architecture Highlights

### Multi-Project Isolation
- Each CommandCenter instance is isolated with unique:
  - Docker volumes
  - Ports
  - Secrets (DB passwords, API keys)
  - COMPOSE_PROJECT_NAME

### Event-Driven Architecture
- NATS JetStream for publish/subscribe
- Event correlation for request tracing
- Server-Sent Events (SSE) for real-time streaming
- WebSocket support for live updates

### Container Orchestration
- Dagger SDK (Python/TypeScript) instead of docker-compose
- Type-safe container management
- No template cloning required
- Programmatic control with error handling

### Knowledge Management
- KnowledgeBeast v3.0 (vendored library)
- PostgreSQL + pgvector for vector search
- Sentence Transformers for local embeddings (no API costs)
- Hybrid search: Vector similarity + keyword with RRF
- Docling for document processing

### Observability
- 5 Grafana dashboards
- 5 AlertManager rules
- Prometheus metrics collection
- OpenTelemetry traces
- Tempo for trace storage

---

## Technology Stack Summary

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Router v6
- Axios (HTTP client)
- Chart.js (visualizations)

### Backend
- Python 3.11
- FastAPI (API framework)
- SQLAlchemy (ORM)
- Pydantic (validation)
- Alembic (migrations)
- Celery (background tasks)

### Hub Orchestration
- Node.js + TypeScript
- Dagger SDK (@dagger.io/dagger)
- Prisma ORM
- Express (API)
- Mustache (templates)
- NATS client

### Databases
- PostgreSQL 16 + pgvector
- Redis 7
- SQLite (Hub registry)

### Message Bus
- NATS 2.10 with JetStream

### Monitoring
- Prometheus
- Grafana
- AlertManager
- OpenTelemetry Collector
- Tempo

### Containers
- Docker Engine
- Dagger SDK (orchestration)

---

## Related Documentation

- [CommandCenter README](../../README.md) - Project overview
- [Hub Design](../HUB_DESIGN.md) - Hub architecture details
- [Dagger Architecture](../DAGGER_ARCHITECTURE.md) - Dagger integration
- [Event System](../../hub/docs/EVENT_SYSTEM.md) - Event infrastructure
- [Observability](../../hub/observability/README.md) - Monitoring setup

---

**Last Updated**: 2025-12-04
**Generated By**: CommandCenter Architecture Analysis
**Diagrams**: Mermaid v10+
