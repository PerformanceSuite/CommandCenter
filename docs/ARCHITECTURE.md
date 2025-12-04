# CommandCenter Architecture

**Version:** 3.0
**Last Updated:** 2025-12-03
**Status:** Production-Ready (Phase 10 Complete)

This document provides the definitive architecture overview of CommandCenter - a Personal AI Operating System for Knowledge Work.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Diagrams](#2-architecture-diagrams)
3. [Directory Structure](#3-directory-structure)
4. [Core Components](#4-core-components)
5. [Data Flow](#5-data-flow)
6. [Technology Stack](#6-technology-stack)
7. [Security Model](#7-security-model)
8. [Integration Points](#8-integration-points)
9. [Deployment](#9-deployment)
10. [Future Roadmap](#10-future-roadmap)

---

## 1. System Overview

CommandCenter is a full-stack platform for AI-driven knowledge work, combining:

- **Agent Orchestration** - Dagger-powered workflow execution with human-in-the-loop approvals
- **Code Intelligence** - Graph-based code analysis with symbol tracking
- **Knowledge Base** - RAG-powered search using KnowledgeBeast + pgvector
- **Federation** - Cross-project coordination via NATS JetStream
- **Observability** - Grafana/Prometheus/Loki/Tempo stack

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        External Services                              │
│   GitHub API │ NATS JetStream │ PostgreSQL │ Redis │ Dagger Engine  │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│                         Hub Application                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  Frontend   │  │Orchestration│  │   Backend   │  │ Federation │ │
│  │  (React)    │  │ (TypeScript)│  │  (FastAPI)  │  │  (Python)  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                      Agent Pool (Dagger Containers)              │ │
│  │  security-scanner │ notifier │ compliance │ patcher │ reviewer  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│                      Observability Stack                              │
│        Grafana │ Prometheus │ Loki │ Tempo │ AlertManager            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Diagrams

Visual diagrams are available in `docs/diagrams/`:

| Diagram | Description | File |
|---------|-------------|------|
| System Architecture | Full component overview | `commandcenter-architecture.mmd` |
| Hub Modules | Directory structure map | `hub-modules.mmd` |
| Data Flow | Workflow execution sequence | `data-flow.mmd` |

### Rendering Diagrams

```bash
# Using Mermaid CLI
npx mmdc -i docs/diagrams/commandcenter-architecture.mmd -o docs/diagrams/commandcenter-architecture.png

# Or view in GitHub (auto-renders .mmd files)
# Or use VS Code Mermaid extension
```

---

## 3. Directory Structure

```
CommandCenter/
├── hub/                          # Main Application
│   ├── frontend/                 # React UI (TypeScript)
│   │   ├── src/
│   │   │   ├── components/       # UI components
│   │   │   ├── pages/            # Route pages
│   │   │   ├── hooks/            # Custom React hooks
│   │   │   └── services/         # API client
│   │   └── package.json
│   │
│   ├── orchestration/            # Agent Workflow Engine (TypeScript)
│   │   ├── agents/               # Agent implementations
│   │   │   ├── security-scanner/
│   │   │   ├── notifier/
│   │   │   ├── compliance-checker/
│   │   │   ├── patcher/
│   │   │   └── code-reviewer/
│   │   ├── src/
│   │   │   ├── api/              # REST API routes
│   │   │   ├── services/         # Business logic
│   │   │   └── dagger/           # Dagger executor
│   │   ├── prisma/               # Database schema
│   │   └── package.json
│   │
│   ├── backend/                  # Hub Backend (FastAPI)
│   │   ├── app/
│   │   │   ├── routers/          # API endpoints
│   │   │   ├── services/         # Business logic
│   │   │   ├── models/           # SQLAlchemy models
│   │   │   └── dagger_modules/   # Dagger stack definitions
│   │   └── requirements.txt
│   │
│   ├── observability/            # Monitoring Stack
│   │   ├── grafana/              # Dashboards
│   │   ├── prometheus/           # Metrics config
│   │   └── alertmanager/         # Alert rules
│   │
│   └── vislzr/                   # Visualization Module
│       └── docs/
│
├── federation/                   # Cross-Project Service (Python)
│   ├── app/
│   │   ├── api/                  # REST endpoints
│   │   ├── services/             # Catalog, health
│   │   └── workers/              # NATS subscribers
│   └── docker-compose.yml
│
├── backend/                      # Legacy Backend (migrating to hub/)
├── frontend/                     # Legacy Frontend (migrating to hub/)
│
├── libs/                         # Shared Libraries
│   └── knowledgebeast/           # RAG Engine
│       ├── knowledgebeast/
│       │   ├── backends/         # PostgresBackend
│       │   └── retriever.py      # Hybrid search
│       └── pyproject.toml
│
├── tools/                        # External Tools
│   ├── agent-sandboxes/          # E2B Integration
│   └── graphvis/                 # Graph Visualization
│
├── docs/                         # Documentation
│   ├── diagrams/                 # Mermaid diagrams
│   ├── plans/                    # Implementation plans
│   └── *.md                      # Various docs
│
└── monitoring/                   # Global Grafana Dashboards
```

---

## 4. Core Components

### 4.1 Hub Frontend (React + TypeScript)

**Port:** 3000

The main user interface providing:

- **Workflow Management** - Create, edit, trigger workflows
- **Workflow Builder** - Drag-and-drop agent orchestration (React Flow)
- **Execution Monitor** - Real-time workflow run tracking
- **Approval Interface** - Human-in-the-loop decision points
- **Dashboard** - Project overview and metrics

**Key Technologies:**
- React 18 + TypeScript 5
- Vite 5 (build tool)
- TailwindCSS (styling)
- React Flow (graph visualization)
- React Query (data fetching)

### 4.2 Orchestration Service (TypeScript)

**Port:** 9002

The workflow engine that executes agent DAGs:

- **Agent Registry** - CRUD for agent definitions
- **Workflow Engine** - DAG execution with template resolution
- **Dagger Executor** - Container orchestration via Dagger SDK
- **Approval System** - Risk-based workflow pausing (AUTO vs APPROVAL_REQUIRED)
- **Event Bridge** - NATS integration for triggers

**Key Technologies:**
- Node.js + TypeScript
- Express.js (API)
- Prisma (ORM)
- Dagger SDK (container execution)
- Zod (schema validation)

### 4.3 Hub Backend (FastAPI)

**Port:** 9001

Core backend services:

- **Event Service** - NATS pub/sub + event replay
- **Graph Service** - Code symbol management + indexing
- **RAG Service** - KnowledgeBeast integration
- **Federation Bridge** - Cross-project coordination

**Key Technologies:**
- Python 3.11 + FastAPI
- SQLAlchemy 2.0 (async ORM)
- Alembic (migrations)
- NATS.py (messaging)
- Dagger SDK (orchestration)

### 4.4 Federation Service (Python)

**Port:** 8001

Cross-project coordination:

- **Catalog Service** - Project registration + discovery
- **Health Aggregation** - Cross-project health summaries
- **NATS Workers** - Heartbeat processing
- **Prometheus Metrics** - Federation observability

**Key Technologies:**
- Python 3.11 + FastAPI
- PostgreSQL (separate database)
- NATS JetStream
- Prometheus client

### 4.5 Agent Pool

Five production agents executing in Dagger containers:

| Agent | Risk Level | Purpose |
|-------|------------|---------|
| `security-scanner` | AUTO | Scan for secrets, SQL injection, XSS |
| `notifier` | AUTO | Send alerts (Slack, Discord, console) |
| `compliance-checker` | AUTO | License + security header validation |
| `patcher` | APPROVAL_REQUIRED | Dependency updates, code patches |
| `code-reviewer` | AUTO | Quality + complexity analysis |

### 4.6 KnowledgeBeast (RAG Engine)

**Location:** `libs/knowledgebeast/`

Hybrid search combining vector + keyword retrieval:

- **PostgresBackend** - pgvector for embeddings
- **Hybrid Search** - Vector + BM25 with RRF fusion
- **Multi-tenant** - Project-scoped collections
- **Document Processing** - Docling integration

---

## 5. Data Flow

### 5.1 Workflow Execution

```
User triggers workflow via UI
        │
        ▼
Orchestration Service receives request
        │
        ├── Creates WorkflowRun record (PostgreSQL)
        ├── Publishes workflow.started (NATS)
        │
        ▼
For each agent in DAG order:
        │
        ├── Resolve input templates ({{node.output.field}})
        ├── Execute agent via Dagger
        │   └── Container runs with inputs
        │       └── Returns structured output
        │
        ├── If APPROVAL_REQUIRED:
        │   ├── Pause execution
        │   ├── Create approval request
        │   ├── Wait for human decision
        │   └── Continue or abort
        │
        └── Update AgentRun status
        │
        ▼
Complete workflow, publish workflow.completed
```

### 5.2 Event Flow (NATS)

```
Hub Backend                    Federation Service
     │                              │
     ├── Publishes events ─────────►│
     │   • project.created          │
     │   • graph.file.updated       │
     │   • workflow.triggered       │
     │                              │
     │◄───────── Heartbeats ────────┤
     │   • heartbeat.{project}      │
     │                              │
Orchestration Service              │
     │                              │
     ├── Publishes events ─────────►│
     │   • workflow.started         │
     │   • workflow.completed       │
     │   • approval.required        │
```

---

## 6. Technology Stack

### Backend

| Component | Technology | Version |
|-----------|------------|---------|
| API Framework | FastAPI | 0.109+ |
| ORM | SQLAlchemy | 2.0 |
| Migrations | Alembic | 1.13+ |
| Validation | Pydantic | 2.0 |
| Task Queue | Celery | 5.3+ |
| Messaging | NATS.py | 2.6+ |
| Container Orchestration | Dagger SDK | 0.9+ |

### Frontend

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 18.2 |
| Language | TypeScript | 5.0 |
| Build Tool | Vite | 5.0 |
| Styling | TailwindCSS | 3.4 |
| State | React Query | 5.0 |
| Visualization | React Flow | 11.0 |

### Data Layer

| Component | Technology | Version |
|-----------|------------|---------|
| Primary Database | PostgreSQL | 16 |
| Vector Store | pgvector | 0.7+ |
| Cache | Redis | 7 |
| Message Broker | NATS JetStream | 2.10 |

### Observability

| Component | Technology | Version |
|-----------|------------|---------|
| Metrics | Prometheus | 2.48 |
| Dashboards | Grafana | 10.2 |
| Logs | Loki | 2.9 |
| Traces | Tempo | 2.3 |
| Alerts | AlertManager | 0.26 |

---

## 7. Security Model

### 7.1 Multi-Tenant Isolation

**Critical Principle:** Data isolation enforced at service layer.

- All queries filter by `project_id`
- No hardcoded project references
- Service methods require explicit project_id parameter
- Audit report: `docs/MULTI_TENANT_ISOLATION_AUDIT_2025-11-18.md`

### 7.2 Agent Sandboxing

Dagger containers provide isolation:

- Agents run in ephemeral containers
- No host filesystem access
- No inter-container communication
- Resource limits enforced
- Secrets injected via environment variables

### 7.3 Authentication

| Component | Method | Status |
|-----------|--------|--------|
| Orchestration API | API Key | ✅ Implemented |
| Federation API | API Key + JWT | ✅ Implemented |
| Hub Backend | Session-based | ⚠️ Needs hardening |
| VERIA Integration | JWT | 📋 Planned |

### 7.4 Secrets Management

- Environment variables for configuration
- No secrets in logs (redaction enforced)
- Per-agent secret injection via Dagger
- GitHub tokens encrypted at rest (Fernet)

---

## 8. Integration Points

### 8.1 VERIA Platform

See `docs/VERIA_INTEGRATION.md` for complete specification.

**Integration Model:**
- Separate projects with clear API boundaries
- Federation Service for discovery
- NATS for event-driven coupling
- JWT authentication (planned)

**API Contracts:**

```yaml
commandcenter_provides:
  - /api/v1/knowledge/query      # RAG search
  - /api/v1/workflows/trigger    # Workflow execution
  - /api/v1/graph/symbols        # Code symbol lookup

veria_provides:
  - /api/v1/intelligence/analyze # Analysis API
  - /api/v1/projects             # Project management

shared_events:
  - project.created
  - analysis.completed
  - workflow.finished
```

### 8.2 GitHub

- Repository syncing via PyGithub
- Webhook processing for events
- Per-repository access tokens
- Graph indexing on push events

### 8.3 External Tools (E2B)

See `tools/agent-sandboxes/` for E2B integration:

- Parallel sandbox execution
- Claude Code agents in isolation
- Safe experimentation environment

---

## 9. Deployment

### 9.1 Development

```bash
# Start all services
docker-compose up -d

# Or use Makefile
make dev
```

### 9.2 Production

```bash
# Federation stack
cd federation && docker-compose up -d

# Hub services
cd hub && docker-compose -f docker-compose.prod.yml up -d
```

### 9.3 Service Ports

| Service | Port | Protocol |
|---------|------|----------|
| Hub Frontend | 3000 | HTTP |
| Hub Backend | 9001 | HTTP |
| Orchestration | 9002 | HTTP |
| Federation | 8001 | HTTP |
| PostgreSQL | 5432 | TCP |
| Redis | 6379 | TCP |
| NATS | 4222 | TCP |
| NATS HTTP | 8222 | HTTP |
| Prometheus | 9090 | HTTP |
| Grafana | 3001 | HTTP |

---

## 10. Future Roadmap

### Completed Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1-6 | ✅ | Event System + Health + Service Discovery |
| 7 | ✅ | Graph Service (3/4 weeks) |
| 9 | ✅ | Federation + Ecosystem Mode |
| 10 | ✅ | Agent Orchestration (6 phases) |

### Planned

| Phase | Status | Description |
|-------|--------|-------------|
| 8 | 📋 | VISLZR Frontend (React Flow integration) |
| 11 | 📋 | Compliance & Security Hardening |
| 12 | 📋 | Autonomous Mesh + Predictive Intelligence |

### Technical Debt (from CODE_HEALTH_REPORT.md)

**Critical (P0):**
- Fix npm security vulnerabilities
- Dagger container security hardening

**High (P1):**
- Implement authentication context (remove hardcoded IDs)
- Fix TypeScript test errors (50 failures)
- Increase test coverage (currently 35%)

**Medium (P2):**
- Job task implementations (6 placeholders)
- Python linting re-enablement
- TODO comment cleanup (500+ items)

---

## Appendix: Related Documentation

| Document | Description |
|----------|-------------|
| `CLAUDE.md` | Claude Code development guide |
| `CODE_HEALTH_REPORT.md` | Technical debt inventory |
| `VERIA_INTEGRATION.md` | VERIA integration specification |
| `LEGACY_ANALYSIS.md` | Historical context from XML exports |
| `DAGGER_ARCHITECTURE.md` | Dagger orchestration details |
| `DATA_ISOLATION.md` | Multi-tenant security |
| `plans/` | Implementation plans by phase |

---

*Architecture v3.0 - December 2025*
*CommandCenter: Your Personal AI Operating System for Knowledge Work*
