# Plan: Full E2B Integration into CommandCenter

**Created**: 2025-12-31
**Status**: 🟡 In Progress

## Goal

Enable CommandCenter to spawn, manage, monitor, and orchestrate E2B agent sandboxes through unified UI and API, treating sandboxes as first-class compute resources for research and hypothesis workflows.

## Approach

Leverage the existing `tools/agent-sandboxes/` infrastructure (CLI, MCP server, obox workflows) as the foundation. Build a backend service layer that wraps these capabilities, expose via REST API, and create React components for sandbox management. Integrate with the newly deployed AlertManager for sandbox health monitoring.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CommandCenter Frontend                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │  Sandbox    │ │  Workflow   │ │   Logs &    │ │ Monitoring │ │
│  │  Manager    │ │ Orchestrator│ │   Output    │ │ Dashboard  │ │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬──────┘ │
└─────────┼───────────────┼───────────────┼──────────────┼────────┘
          │               │               │              │
┌─────────┴───────────────┴───────────────┴──────────────┴────────┐
│                    CommandCenter Backend API                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    /api/v1/sandboxes                        ││
│  │  POST /create  GET /list  POST /{id}/exec  DELETE /{id}    ││
│  │  POST /{id}/pause  POST /{id}/resume  GET /{id}/logs       ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    SandboxService                            ││
│  │  create_sandbox() | execute_command() | get_logs()          ││
│  │  spawn_agent_fork() | aggregate_results()                   ││
│  └──────────────────────────┬──────────────────────────────────┘│
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│              Existing E2B Infrastructure                         │
│  tools/agent-sandboxes/                                          │
│  ├── sandbox_cli/      (CLI wrapper)                            │
│  ├── sandbox_mcp/      (MCP server)                             │
│  ├── sandbox_workflows/ (obox - parallel forks)                 │
│  └── E2B SDK                                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Phases

### Phase 1: Backend API Layer
Foundation - expose E2B operations through CommandCenter's FastAPI backend.

- [ ] Create `backend/app/models/sandbox.py` - Sandbox, SandboxExecution, SandboxLog models
- [ ] Create `backend/app/schemas/sandbox.py` - Pydantic schemas for API
- [ ] Create `backend/app/services/sandbox_service.py` - E2B SDK wrapper service
- [ ] Create `backend/app/routers/sandboxes.py` - REST endpoints
- [ ] Create `backend/app/repositories/sandbox_repository.py` - DB operations
- [ ] Add migration for sandbox tables
- [ ] Register router in `main.py`
- [ ] Add E2B_API_KEY to environment config

### Phase 2: Workflow Orchestration
Enable research/hypothesis workflows to spawn sandbox agents.

- [ ] Create `backend/app/services/sandbox_orchestration_service.py`
- [ ] Add `spawn_sandbox_agent()` method to research orchestration
- [ ] Create Celery task `backend/app/tasks/sandbox_tasks.py` for async execution
- [ ] Add sandbox trigger to hypothesis workflow
- [ ] Create `/api/v1/sandboxes/fork` endpoint for parallel agent spawning
- [ ] Integrate with existing `ResearchTask` model for tracking
- [ ] Add webhook callback for sandbox completion

### Phase 3: Log & Output Aggregation
Centralize sandbox outputs for analysis.

- [ ] Create `SandboxOutput` model for structured results
- [ ] Implement real-time log streaming via WebSocket
- [ ] Create `backend/app/services/sandbox_log_aggregator.py`
- [ ] Add `/api/v1/sandboxes/{id}/stream` SSE endpoint
- [ ] Store execution artifacts (files, diffs, PRs created)
- [ ] Link sandbox outputs to research findings
- [ ] Add search/filter capabilities for logs

### Phase 4: Frontend UI
React components for sandbox management.

- [ ] Create `hub/frontend/src/pages/Sandboxes.tsx` - Main sandbox dashboard
- [ ] Create `hub/frontend/src/components/sandbox/SandboxList.tsx`
- [ ] Create `hub/frontend/src/components/sandbox/SandboxDetail.tsx`
- [ ] Create `hub/frontend/src/components/sandbox/SandboxTerminal.tsx` - Live output
- [ ] Create `hub/frontend/src/components/sandbox/SandboxSpawner.tsx` - Create form
- [ ] Create `hub/frontend/src/components/sandbox/ForkManager.tsx` - Parallel agents
- [ ] Add `hub/frontend/src/services/sandboxApi.ts` - API client
- [ ] Add sandbox navigation to sidebar
- [ ] Create sandbox status indicators/badges

### Phase 5: Monitoring Integration
Leverage AlertManager for sandbox health.

- [ ] Add Prometheus metrics for sandbox operations
  - `sandbox_active_count` gauge
  - `sandbox_execution_duration_seconds` histogram
  - `sandbox_spawn_total` counter
  - `sandbox_error_total` counter
- [ ] Create sandbox alert rules in `monitoring/alerts/sandbox.yml`
  - Alert on sandbox timeout
  - Alert on high error rate
  - Alert on cost threshold exceeded
- [ ] Add sandbox cost tracking (E2B billing integration)
- [ ] Create Grafana dashboard for sandbox metrics
- [ ] Add sandbox health to main dashboard

## Dependencies

- E2B SDK (`e2b` Python package)
- E2B API Key
- Existing `tools/agent-sandboxes/` infrastructure
- AlertManager (PR #117 - merged)
- Multi-tenant isolation (PR #116 - merged)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| E2B API rate limits | Implement request queuing and backoff |
| Sandbox costs accumulate | Add budget alerts, auto-terminate idle sandboxes |
| Long-running sandboxes timeout | Implement checkpoint/resume capability |
| Secret exposure in sandboxes | Use E2B's secure env injection, never log secrets |
| Orphaned sandboxes | Scheduled cleanup job, max lifetime limits |

## Definition of Done

- [ ] Can create/list/delete sandboxes from UI
- [ ] Can spawn parallel agent forks from hypothesis workflow
- [ ] Live log streaming works in terminal component
- [ ] Sandbox metrics visible in Grafana
- [ ] AlertManager fires on sandbox errors
- [ ] All endpoints have OpenAPI documentation
- [ ] Integration tests passing
- [ ] Multi-tenant isolation enforced (sandboxes scoped to projects)

## API Design

### Endpoints

```
POST   /api/v1/sandboxes              - Create sandbox
GET    /api/v1/sandboxes              - List sandboxes
GET    /api/v1/sandboxes/{id}         - Get sandbox details
DELETE /api/v1/sandboxes/{id}         - Terminate sandbox
POST   /api/v1/sandboxes/{id}/exec    - Execute command
POST   /api/v1/sandboxes/{id}/pause   - Pause sandbox
POST   /api/v1/sandboxes/{id}/resume  - Resume sandbox
GET    /api/v1/sandboxes/{id}/logs    - Get logs
GET    /api/v1/sandboxes/{id}/stream  - SSE log stream
GET    /api/v1/sandboxes/{id}/files   - List files
GET    /api/v1/sandboxes/{id}/files/{path} - Download file
POST   /api/v1/sandboxes/fork         - Spawn parallel agents
GET    /api/v1/sandboxes/fork/{id}    - Get fork status
```

### Models

```python
class Sandbox(Base):
    id: UUID
    project_id: int  # Multi-tenant
    e2b_sandbox_id: str
    template: str
    status: SandboxStatus  # CREATING, RUNNING, PAUSED, TERMINATED
    created_at: datetime
    last_activity: datetime
    metadata: JSON

class SandboxExecution(Base):
    id: UUID
    sandbox_id: UUID
    command: str
    exit_code: int
    stdout: Text
    stderr: Text
    started_at: datetime
    completed_at: datetime

class SandboxFork(Base):
    id: UUID
    parent_sandbox_id: UUID
    research_task_id: int
    prompt: str
    model: str
    status: ForkStatus
    result_summary: Text
```

## Notes

- Reuse existing `tools/agent-sandboxes/sandbox_cli` patterns
- Consider MCP server integration for Claude Desktop users
- E2B templates: use `agent-sandbox-dev-node22` as default
- Max parallel forks per project: configurable (default 5)
- Sandbox TTL: 1 hour default, configurable per spawn
