# VERIA Platform Integration Audit

**Date**: 2025-12-03
**Status**: Integration Points Mapped & Analyzed
**Type**: Cross-Project API Boundary Design

---

## Executive Summary

VERIA and CommandCenter are designed as **separate systems with clear API boundaries**. Rather than merging into a monorepo, they integrate at REST/NATS boundaries with distinct responsibilities:

- **CommandCenter**: Provides orchestration, knowledge management, and agent automation
- **VERIA**: Provides intelligence analysis, compliance validation, and project management

**Key Findings**:
1. ✅ Both systems ready for federation via NATS event broker
2. ✅ Clear separation of concerns enables independent scaling
3. ✅ Existing federation infrastructure supports VERIA integration
4. ✅ Authentication model requires API Key + JWT tokens
5. ⚠️ Event schema alignment needed (currently independent projects)

---

## Part 1: CommandCenter Current Architecture

### 1.1 High-Level Overview

CommandCenter is a **personal AI operating system** for knowledge work with:
- **Event-driven core**: NATS JetStream for all cross-service messaging
- **Multi-tenant support**: Per-project data isolation
- **Federated architecture**: Multiple CommandCenter instances coordinate via Federation Service
- **Agent orchestration**: Dagger-powered workflow execution with human-in-the-loop approvals
- **Knowledge management**: RAG backend (KnowledgeBeast) with PostgreSQL vector storage

```
┌──────────────────────────────────────────────────────────┐
│                   CommandCenter Hub                       │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Frontend   │  │  VISLZR UI   │  │  Graph Viz   │  │
│  │   (React)    │  │ (Workflows)  │  │  (Code Map)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                           │                               │
│  ┌────────────────────────▼─────────────────────────┐  │
│  │        Orchestration Service (9002)               │  │
│  │  ├─ Workflow Engine (Prisma + Express)           │  │
│  │  ├─ Agent Registry & Executor                     │  │
│  │  ├─ Dagger Integration (Container Isolation)     │  │
│  │  ├─ NATS Event Bridge (Pattern-based routing)    │  │
│  │  └─ OpenTelemetry Instrumentation                │  │
│  └────────────────────────────────────────────────────┘  │
│                           │                               │
│  ┌────────────────────────▼─────────────────────────┐  │
│  │      Event & State Management (NATS)             │  │
│  │  ├─ JetStream (Durable message store)            │  │
│  │  ├─ Project lifecycle events                      │  │
│  │  ├─ Workflow execution events                     │  │
│  │  ├─ Graph/analysis events                        │  │
│  │  └─ Cross-project event routing                  │  │
│  └────────────────────────────────────────────────────┘  │
│                           │                               │
│  ┌─────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │ PostgreSQL  │  │  KnowledgeBeast  │  │  Prometheus │ │
│  │  (Metadata) │  │   (RAG/Vectors)  │  │  (Metrics)  │ │
│  └─────────────┘  └──────────────────┘  └─────────────┘ │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

### 1.2 Core Services & APIs

#### Orchestration Service (Port 9002)

**Responsibility**: Agent workflow execution, task automation, human approvals

**Key Endpoints**:
```
POST   /api/agents                         # Register agent
GET    /api/agents                         # List agents
GET    /api/agents/{id}                    # Get agent details

POST   /api/workflows                      # Create workflow
GET    /api/workflows?projectId=X          # List workflows
GET    /api/workflows/{id}                 # Get workflow
PUT    /api/workflows/{id}                 # Update workflow
DELETE /api/workflows/{id}                 # Delete workflow

POST   /api/workflows/{id}/trigger         # Execute workflow
GET    /api/workflows/{id}/runs            # List execution history
GET    /api/workflows/{workflowId}/runs/{runId}   # Get execution details

GET    /api/workflows/runs/{runId}/agent-runs    # Get agent-level details
POST   /api/workflows/runs/{runId}/retry         # Retry failed workflow

POST   /api/approvals/{approvalId}/approve       # Human approval
POST   /api/approvals/{approvalId}/reject        # Human rejection
```

**Data Model**:
```typescript
// Agent Registry
Agent {
  id: string (CUID)
  projectId: number
  name: string
  type: "LLM" | "RULE" | "API" | "SCRIPT"
  description: string
  entryPath: string (Docker image path)
  version: string
  riskLevel: "AUTO" | "APPROVAL_REQUIRED"
  registeredAt: DateTime
  updatedAt: DateTime
  capabilities: AgentCapability[]
}

// Workflow Definition
Workflow {
  id: string (CUID)
  projectId: number
  name: string
  description: string
  trigger: JSON (event patterns or manual)
  status: "ACTIVE" | "DRAFT" | "ARCHIVED"
  nodes: WorkflowNode[]  // DAG structure
  createdAt: DateTime
  updatedAt: DateTime
}

// Workflow Node
WorkflowNode {
  id: string
  workflowId: string
  agentId: string
  action: string
  inputsJson: JSON (template variables like {{scan-node.output.findings}})
  dependsOn: string[]  // Other node IDs for DAG
  approvalRequired: boolean
  symbolicId: string  // User-friendly node reference
}

// Workflow Execution
WorkflowRun {
  id: string
  workflowId: string
  trigger: "manual" | "retry" | "auto"
  contextJson: JSON  // Initial workflow context
  status: "PENDING" | "RUNNING" | "SUCCESS" | "FAILED" | "WAITING_APPROVAL"
  startedAt: DateTime
  finishedAt: DateTime
  agentRuns: AgentRun[]
  approvals: WorkflowApproval[]
}
```

**Security Model**:
- ✅ Input validation (Zod schemas)
- ✅ Per-project isolation (projectId in all queries)
- ✅ Dagger container sandboxing (agents isolated from host)
- ⚠️ No explicit API authentication yet (local service only)
- ⚠️ Rate limiting at 100 req/min (middleware in place)

#### Federation Service (Port 8001)

**Responsibility**: Cross-instance coordination, project catalog, heartbeat monitoring

**Key Endpoints**:
```
GET    /health                             # Service health
GET    /health/nats                        # NATS connectivity check

GET    /api/fed/projects                   # List all projects
POST   /api/fed/projects                   # Register project
GET    /api/fed/projects/{slug}            # Get project details

GET    /metrics                            # Prometheus metrics
```

**Authentication**:
- Header: `X-API-Key` (configured in `FEDERATION_API_KEYS` env var)
- Format: JSON array of valid API keys

**Project Registration**:
```json
{
  "project_slug": "veria",
  "name": "VERIA Platform",
  "hub_url": "http://veria.example.com:9002",
  "mesh_namespace": "veria.mesh",
  "tags": ["intelligence", "compliance"]
}
```

**Heartbeat Protocol**:
- Subject: `hub.presence.{project_slug}` (NATS)
- Interval: 30 seconds
- Stale threshold: 90 seconds
- Payload: Project metadata + timestamp

### 1.3 Event-Driven Architecture (NATS JetStream)

**Event Subjects** (namespace per project):

```
hub.project.*
  ├─ hub.project.{projectId}.created
  ├─ hub.project.{projectId}.started
  ├─ hub.project.{projectId}.stopped
  └─ hub.project.{projectId}.deleted

hub.workflow.*
  ├─ hub.workflow.{projectId}.trigger
  ├─ hub.workflow.{projectId}.scheduled
  ├─ hub.workflow.{projectId}.execute
  ├─ hub.workflow.{projectId}.success
  └─ hub.workflow.{projectId}.failed

hub.agent.*
  ├─ hub.agent.{projectId}.registered
  ├─ hub.agent.{projectId}.executed
  └─ hub.agent.{projectId}.error

hub.graph.*
  ├─ hub.graph.{projectId}.file.updated
  ├─ hub.graph.{projectId}.symbol.analyzed
  └─ hub.graph.{projectId}.audit.completed

hub.presence.*
  └─ hub.presence.{projectId}  # Heartbeat signals
```

**Event Payload Structure**:
```json
{
  "event_id": "uuid",
  "timestamp": "2025-12-03T10:00:00Z",
  "project_id": 1,
  "source": "hub.orchestration",
  "subject": "hub.workflow.1.trigger",
  "payload": {
    // Event-specific data
  },
  "correlation_id": "request-uuid"
}
```

### 1.4 Database Schema (PostgreSQL)

**Orchestration Database** (`orchestration_service_db`):
- `agents` - Agent registry
- `agent_capabilities` - Agent features/inputs/outputs
- `agent_runs` - Agent execution records
- `workflows` - Workflow definitions
- `workflow_nodes` - DAG nodes
- `workflow_runs` - Execution instances
- `workflow_approvals` - Human approval records

**Federation Database** (`commandcenter_fed`):
- `projects` - Registered project metadata
- `heartbeats` - Project status history
- `health_metrics` - Per-project health data

---

## Part 2: VERIA Platform Current State

### 2.1 VERIA Project Configuration

**From hub-prototype**: `/hub-prototype/projects/veria-dev/project.json`

```json
{
  "projectId": "veria",
  "instanceId": "veria-dev",
  "name": "Veria (Dev)",
  "owner": "commandcenter",
  "env": "dev",
  "endpoints": {
    "api": "http://127.0.0.1:8082"
  },
  "health": {
    "url": "http://127.0.0.1:8082/health"
  },
  "tools": ["veria"]
}
```

**Key Characteristics**:
- ✅ Registered as separate project in CommandCenter federation
- ✅ API endpoint on port 8082 (local development)
- ✅ Health check endpoint available
- ✅ Owner: CommandCenter (organizational relationship)

### 2.2 VERIA Planned Features (From Phase Blueprints)

**Phase 11 References** (Compliance & Partner Interfaces):
- REST endpoint: `POST /veria/api/attestations`
- `veria-compliance` agent extends local compliance-checker with external validation
- Compliance check workflow: Local checks → VERIA attestation → Approval
- Integration pattern: Workflow node delegates to external VERIA agent

**Phase 12 References** (Autonomous Mesh):
- VERIA as external intelligence provider
- Event routing to VERIA for analysis
- Federated intelligence patterns

### 2.3 VERIA Architecture Assumptions

Based on integration plans and project structure:

```
┌──────────────────────────────────────────────┐
│          VERIA Platform                      │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │      Intelligence Analysis Service     │ │
│  │  ├─ Pattern recognition                │ │
│  │  ├─ Compliance validation               │ │
│  │  ├─ Risk assessment                     │ │
│  │  └─ Attestation generation              │ │
│  └────────────────────────────────────────┘ │
│                    │                         │
│  ┌─────────────────▼──────────────────────┐ │
│  │      API Layer (Port 8082)             │ │
│  │  ├─ POST /api/analyze                  │ │
│  │  ├─ POST /api/validate                 │ │
│  │  ├─ POST /api/attest                   │ │
│  │  └─ GET /api/status                    │ │
│  └────────────────────────────────────────┘ │
│                    │                         │
│  ┌─────────────────▼──────────────────────┐ │
│  │    Data & State (Project-specific)     │ │
│  │  ├─ PostgreSQL (Projects, Analysis)    │ │
│  │  ├─ Vector DB (Embeddings)             │ │
│  │  └─ Cache Layer                        │ │
│  └────────────────────────────────────────┘ │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Part 3: Integration Points & API Boundaries

### 3.1 Current Integration Points

#### Integration 1: Project Registry (Federation)

**Direction**: CommandCenter → VERIA (via Federation Service)

**Use Case**: CommandCenter discovers VERIA as a federated project

**Flow**:
```
1. VERIA publishes heartbeat to NATS
   Subject: hub.presence.veria
   Payload: {project_slug: "veria", status: "online", ...}

2. Federation Service ingests heartbeat
   Updates projects table with VERIA metadata

3. CommandCenter CLI queries federation
   GET /api/fed/projects?status=online
   Returns: [{slug: "veria", name: "VERIA Platform", ...}]

4. User can target VERIA for cross-project workflows
```

**API Contract**:
```typescript
// VERIA heartbeat
interface VERIAHeartbeat {
  project_slug: "veria"
  name: string
  hub_url: string  // http://127.0.0.1:8082
  mesh_namespace: string  // "veria.mesh"
  status: "online" | "degraded" | "offline"
  timestamp: ISO8601
  version: string
}

// Federation GET response includes VERIA
interface ProjectCatalogEntry {
  slug: "veria"
  name: string
  hub_url: string
  status: "online" | "offline"
  last_heartbeat: ISO8601
  mesh_namespace: string
}
```

#### Integration 2: Workflow → VERIA Analysis (Planned)

**Direction**: CommandCenter → VERIA (HTTP REST + Events)

**Use Case**: Workflow node delegates analysis to VERIA

**Example Workflow**:
```json
{
  "name": "scan-and-attest",
  "trigger": "manual",
  "nodes": [
    {
      "id": "scan-node",
      "agentId": "security-scanner",
      "action": "scan",
      "inputs": {"path": "/workspace"},
      "dependsOn": []
    },
    {
      "id": "attest-node",
      "agentId": "veria-compliance",  // External agent
      "action": "attest",
      "inputs": {
        "findings": "{{scan-node.output.findings}}",
        "compliance_level": "medium"
      },
      "dependsOn": ["scan-node"]
    }
  ]
}
```

**VERIA Agent Specification**:
```typescript
interface VERIAComplianceAgent {
  name: "veria-compliance"
  type: "API"
  riskLevel: "AUTO"
  endpoint: "http://127.0.0.1:8082/api/attest"

  input: {
    findings: {
      type: "object[]"
      items: {
        category: string
        severity: "critical" | "high" | "medium" | "low"
        description: string
      }
    }
    compliance_level: "high" | "medium" | "low"
  }

  output: {
    success: boolean
    attestation_id: string
    compliance_score: number  // 0-100
    details: {
      validated_count: number
      failed_count: number
      recommendations: string[]
    }
  }
}
```

**API Contract**:
```
POST http://127.0.0.1:8082/api/attest
Content-Type: application/json
X-CommandCenter-ProjectId: 1
X-CommandCenter-WorkflowRunId: uuid

{
  "findings": [...],
  "compliance_level": "medium"
}

Response 200 OK:
{
  "success": true,
  "attestation_id": "veria-attest-123",
  "compliance_score": 87,
  "details": {
    "validated_count": 23,
    "failed_count": 2,
    "recommendations": ["Fix secret detection", "Add CSP header"]
  }
}
```

#### Integration 3: Event-Driven Intelligence (Planned)

**Direction**: CommandCenter ↔ VERIA (Bidirectional Events)

**Use Case**: VERIA subscribes to workflow events for cross-project intelligence

**Subjects VERIA Listens to**:
```
hub.workflow.*.success      # Workflow completed successfully
hub.workflow.*.failed       # Workflow failed
hub.agent.*.registered      # New agent registered
hub.graph.*.file.updated    # Code graph changed
```

**Subjects VERIA Publishes**:
```
veria.intelligence.*
  ├─ veria.intelligence.analysis.completed
  ├─ veria.intelligence.anomaly.detected
  ├─ veria.intelligence.recommendation.generated
  └─ veria.intelligence.attestation.issued
```

**Event Payload Example**:
```json
{
  "event_id": "uuid",
  "timestamp": "2025-12-03T10:00:00Z",
  "source": "veria.intelligence",
  "subject": "veria.intelligence.analysis.completed",
  "correlation_id": "workflow-run-uuid",
  "payload": {
    "analysis_id": "veria-analysis-456",
    "workflow_run_id": "workflow-run-uuid",
    "status": "completed",
    "analysis_type": "compliance",
    "findings": {
      "passed": 45,
      "warnings": 3,
      "failed": 1
    },
    "recommendations": [
      "Update dependency X to latest version",
      "Add HSTS header to web server config"
    ]
  }
}
```

---

## Part 4: Authentication & Authorization Model

### 4.1 CommandCenter Internal Services (No External Auth)

**Current State**:
- Orchestration service (9002): No explicit auth (assumes trusted internal network)
- All endpoints validate `projectId` for data isolation
- Rate limiting: 100 req/min per IP (middleware)

**Limitation**: Not production-ready for external exposure

### 4.2 Federation Service (API Key Based)

**Current State**:
- Header: `X-API-Key`
- Validation: Must match one of `FEDERATION_API_KEYS` env vars
- Scope: Full access to /api/fed/projects endpoints

**Example**:
```bash
curl -H "X-API-Key: your-secret-key" \
  http://localhost:8001/api/fed/projects
```

**Limitation**: Single key per instance, no per-client scoping

### 4.3 Proposed VERIA Integration Auth

**For VERIA → CommandCenter**:

```
┌─────────────────────────────────────────────────────────┐
│          Token-Based Authentication Flow                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. VERIA (client) presents API key to Federation      │
│  2. Federation validates key and returns JWT token      │
│  3. VERIA includes JWT in Authorization header         │
│  4. Orchestration service validates JWT signature      │
│  5. Access granted with VERIA project context          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Implementation**:
```typescript
// Step 1: VERIA exchanges API key for JWT
POST /federation/token
Headers: X-API-Key: veria-secret-key

Response 200:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "project:veria workflows:read"
}

// Step 2: VERIA uses JWT for orchestration requests
POST /api/workflows
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
  X-CommandCenter-ProjectId: veria

Body:
{
  "name": "external-workflow",
  "trigger": {"type": "webhook", "path": "/webhooks/veria"},
  "nodes": [...]
}
```

**JWT Claims**:
```json
{
  "sub": "veria-project",  // Subject (project ID)
  "scope": "project:veria workflows:read workflows:write agents:read",
  "projectId": "veria",
  "aud": "commandcenter-orchestration",
  "iss": "commandcenter-federation",
  "exp": 1702646400,
  "iat": 1702642800
}
```

**Scopes**:
- `project:veria` - Access VERIA-specific resources
- `workflows:read` - Query workflows and runs
- `workflows:write` - Create/update/delete workflows
- `workflows:execute` - Trigger workflow execution
- `agents:read` - Query agent registry
- `agents:write` - Register agents

### 4.4 For CommandCenter → VERIA

**VERIA API Authentication**:

```
X-CommandCenter-ProjectId: 1              # Identifying source
X-CommandCenter-WorkflowRunId: uuid       # Traceability
Authorization: Bearer veria-api-token     # VERIA's own token
```

**VERIA Implementation Options**:
1. **Basic Auth**: `Authorization: Basic base64(client_id:client_secret)`
2. **API Key**: `X-API-Key: veria-secret` (simple, not recommended for prod)
3. **OAuth 2.0**: Full token exchange with refresh tokens (enterprise)
4. **JWT**: Mutual JWT validation with VERIA

---

## Part 5: Data Flow Examples

### 5.1 Scenario: Compliance Workflow with VERIA

```
┌─────────────────────────────────────────────────────────────────┐
│  Compliance Workflow: Security Scan → Compliance Check → Attest │
└─────────────────────────────────────────────────────────────────┘

User triggers workflow via UI
  │
  ├─> POST /api/workflows/{workflow-id}/trigger
  │   {contextJson: {repository: "github.com/project/repo"}}
  │
  └─> Orchestration Service
      │
      ├─ Create WorkflowRun (status: PENDING)
      ├─ Publish event: hub.workflow.1.trigger
      │
      ├─ Node 1: security-scanner (LOCAL)
      │  ├─ Dagger: Build + Run container
      │  ├─ Scan for vulnerabilities
      │  ├─ Create AgentRun (status: SUCCESS)
      │  └─ Output: {findings: [{severity: "high", ...}]}
      │
      ├─ Node 2: veria-compliance (EXTERNAL)
      │  ├─ HTTP POST http://127.0.0.1:8082/api/attest
      │  ├─ Include JWT token + correlation_id
      │  ├─ Payload: {findings: [...], compliance_level: "medium"}
      │  ├─ Wait for response (timeout: 30s)
      │  ├─ Create AgentRun (status: SUCCESS)
      │  └─ Output: {attestation_id: "veria-123", score: 87}
      │
      ├─ Node 3: approval (HUMAN)
      │  ├─ Create WorkflowApproval (status: PENDING)
      │  ├─ Notify user via Slack
      │  ├─ Wait for approval (timeout: 1 hour)
      │  └─ Status: APPROVED | REJECTED
      │
      ├─ Update WorkflowRun (status: SUCCESS)
      ├─ Publish event: hub.workflow.1.success
      │
      └─> UI displays execution trace with all outputs
```

### 5.2 Scenario: Cross-Project Intelligence Feed

```
┌──────────────────────────────────────────────────────┐
│  VERIA Listens to CommandCenter Workflow Events      │
└──────────────────────────────────────────────────────┘

Orchestration Service
  │
  ├─ Workflow completes: security-scanner
  ├─ Publish: hub.workflow.1.success
  │  {
  │    workflow_id: "workflow-123",
  │    findings: [{category: "secret", count: 2}, ...]
  │  }
  │
  └─> NATS JetStream
      │
      ├─ Durable consumer: veria-intelligence
      ├─ Subject: hub.workflow.*.success
      │
      └─> VERIA Intelligence Service
          │
          ├─ Receive event (NATS)
          ├─ Extract findings
          ├─ Correlate with other projects
          ├─ Generate cross-project risk assessment
          ├─ Publish: veria.intelligence.analysis.completed
          │
          └─> CommandCenter Federation
              │
              └─ Ingest for dashboard visibility
```

---

## Part 6: Potential Conflicts & Concerns

### 6.1 Data Isolation & Multi-Tenancy

**Concern**: VERIA accessing CommandCenter data with wrong project scope

**Risk Level**: HIGH

**Mitigation**:
```typescript
// ✅ REQUIRED: All queries include project filtering
const workflow = await prisma.workflow.findUnique({
  where: {
    id: workflowId,
    projectId: veria_project_id,  // MUST validate from JWT
  },
});

// ❌ VULNERABLE: No project filtering
const workflow = await prisma.workflow.findUnique({
  where: { id: workflowId }
});
```

**Recommendation**: Add middleware to validate JWT project ID before all handlers.

### 6.2 Event Loop Serialization

**Concern**: VERIA workflows triggering back to CommandCenter workflows (circular)

**Risk Level**: MEDIUM

**Example**:
```
1. CommandCenter: security-scan workflow → veria-attest
2. VERIA attestation creates new insight
3. VERIA publishes: veria.intelligence.analysis.completed
4. CommandCenter subscribes, creates new workflow
5. New workflow includes veria-attest step → back to step 2 (LOOP)
```

**Mitigation**:
- Add `max_depth` to workflow execution (depth limit)
- Add `correlation_id` tracking to detect circular dependencies
- Require explicit "allow fanout" config per project pair

**Recommendation**: Implement workflow depth limit in `workflow-runner.ts`.

### 6.3 Timeout & Reliability

**Concern**: VERIA API unavailable → CommandCenter workflows block indefinitely

**Risk Level**: MEDIUM

**Current Code**:
```typescript
// Dagger executor - no timeout for external calls
const result = await daggerExecutor.run({
  image: "veria-agent",
  command: ["curl", "http://127.0.0.1:8082/api/attest", ...]
  // ❌ No timeout configured
});
```

**Mitigation**:
```typescript
// ✅ REQUIRED: Set reasonable timeout
const result = await daggerExecutor.run({
  image: "veria-agent",
  command: ["curl", "--connect-timeout", "5", "--max-time", "30", "..."],
  timeout: 35000,  // 35 seconds
});

// ✅ Catch timeout errors
try {
  const agentOutput = await executeAgent(run);
} catch (error) {
  if (error.code === 'TIMEOUT') {
    await prisma.workflowRun.update({
      where: { id: workflowRunId },
      data: { status: 'FAILED', error: 'VERIA service timeout' }
    });
  }
}
```

**Recommendation**: Add 30-second timeout to external agent calls in `workflow-runner.ts`.

### 6.4 Secret Management

**Concern**: VERIA credentials leaked in workflow context or logs

**Risk Level**: HIGH

**Current State**:
- Secrets stored in `.env`
- No per-agent secret injection
- Logs captured in Grafana (could leak secrets)

**Mitigation**:
```typescript
// ❌ VULNERABLE: Secrets in context
const context = {
  veria_api_key: process.env.VERIA_API_KEY,  // Captured in logs!
  findings: [...]
};

// ✅ REQUIRED: Inject secrets at execution time only
const agentEnv = {
  VERIA_API_KEY: process.env.VERIA_API_KEY,
  // Only passed to Dagger container, never logged
};

daggerExecutor.run({
  image: "veria-agent",
  env: agentEnv,
  // Secrets not in context/logs
});
```

**Recommendation**: Implement per-agent secret injection in Dagger executor.

### 6.5 External API Rate Limiting

**Concern**: Bulk workflows overwhelming VERIA API

**Risk Level**: MEDIUM

**Scenario**:
```
10 concurrent workflows, each with veria-attest step
= 10 simultaneous requests to VERIA API
= Possible 429 Too Many Requests response
= Workflows fail silently
```

**Mitigation**:
```typescript
// ✅ Queue-based rate limiting
const VERIA_RATE_LIMIT = 2;  // 2 concurrent requests
const veriaSemaphore = new Semaphore(VERIA_RATE_LIMIT);

async function executeVERIAAgent(agent, input) {
  await veriaSemaphore.acquire();
  try {
    return await httpClient.post('/api/attest', input);
  } finally {
    veriaSemaphore.release();
  }
}
```

**Recommendation**: Add semaphore-based concurrency control for external agents.

### 6.6 Dependency Versioning

**Concern**: VERIA API version changes → CommandCenter workflows break

**Risk Level**: MEDIUM

**Mitigation**:
```typescript
// Pin API version in agent definition
const veriaComplianceAgent = {
  name: "veria-compliance",
  endpoint: "http://127.0.0.1:8082/api/attest",
  apiVersion: "v1",  // Explicit version pinning

  // Input validation against expected schema
  inputSchema: {
    findings: {
      type: "array",
      items: {
        category: "enum",  // Validates against known values
        severity: "enum"
      }
    }
  },

  // Output validation (catch breaking changes)
  outputSchema: {
    success: "boolean",
    attestation_id: "string",
    compliance_score: "number"
  }
};
```

**Recommendation**: Add schema versioning to agent registry.

---

## Part 7: Recommendations for API Boundary Design

### 7.1 Phase 1: Immediate (Next Sprint)

**Goal**: Enable secure federation between CommandCenter and VERIA

**Tasks**:
1. ✅ **Implement JWT Authentication** (Federation Service)
   - Add `POST /federation/token` endpoint
   - Accept `X-API-Key` from VERIA
   - Return JWT with `projectId: "veria"` scope
   - Store in Redis for revocation (optional)

2. ✅ **Add JWT Validation Middleware** (Orchestration Service)
   - Verify JWT signature (from Federation public key)
   - Extract `projectId` claim
   - Validate against `X-CommandCenter-ProjectId` header
   - Apply to all `/api/` routes

3. ✅ **Register VERIA Agents** (Manual)
   - `veria-compliance`: Type=API, RiskLevel=AUTO
   - `veria-intelligence`: Type=API, RiskLevel=AUTO
   - Endpoint: `http://127.0.0.1:8082/api/{action}`

4. ✅ **Add Timeout Protection** (Dagger Executor)
   - Set 30-second timeout for external agents
   - Return structured error on timeout
   - Log timeout events for monitoring

**Estimated Effort**: 8-12 hours

**Files to Modify**:
- `federation/app/api/auth.py` - Add token generation
- `federation/app/security.py` - Add JWT signing
- `hub/orchestration/src/middleware/auth.ts` - Add JWT validation
- `hub/orchestration/src/dagger/executor.ts` - Add timeouts
- `hub/orchestration/src/services/workflow-runner.ts` - Error handling

### 7.2 Phase 2: Hardening (Following Sprint)

**Goal**: Production-grade reliability & observability

**Tasks**:
1. **Implement Concurrency Control**
   - Add semaphore for external agent execution
   - Configurable concurrency limit per external agent
   - Queue-based execution with exponential backoff

2. **Add Circular Dependency Detection**
   - Check workflow DAG for cycles before execution
   - Validate no project A → B → A loops
   - Add depth limit (max 10 levels)

3. **Implement Secret Injection**
   - Remove secrets from context JSON
   - Inject via Dagger container env vars only
   - Rotate secrets via env var updates

4. **Schema Versioning**
   - Add `apiVersion` field to agent registry
   - Validate input/output schemas match version
   - Support multiple API versions simultaneously

**Estimated Effort**: 12-16 hours

### 7.3 Phase 3: Ecosystem Scale (Future)

**Goal**: Support multiple external integrations (not just VERIA)

**Tasks**:
1. **Agent Provider Registry**
   - Abstract external agent pattern
   - Support health checks per provider
   - Automatic fallback/retry logic

2. **Event Schema Registry**
   - Define canonical event schemas
   - Schema validation at publish/subscribe
   - Schema versioning & migration paths

3. **Observability Dashboards**
   - VERIA agent execution metrics
   - Cross-project workflow traces
   - Integration health dashboard

4. **Rate Limiting per Integration**
   - Configure per-integration rate limits
   - Backpressure handling
   - Cost tracking (if VERIA is paid)

**Estimated Effort**: 20+ hours (future)

---

## Part 8: Implementation Checklist

### Pre-Integration

- [ ] VERIA API endpoint documented (host:port, auth method)
- [ ] VERIA agent schemas defined (input & output)
- [ ] VERIA API key generated and shared securely
- [ ] Federation service credentials configured
- [ ] Network routing verified (CommandCenter → VERIA on port 8082)

### Phase 1 Implementation

- [ ] JWT generation endpoint created in Federation Service
- [ ] JWT validation middleware added to Orchestration Service
- [ ] VERIA agents registered in CommandCenter
- [ ] Timeout protection added to Dagger executor
- [ ] Integration tests written (mock VERIA API)
- [ ] End-to-end workflow test executed
- [ ] Documentation updated with VERIA endpoints

### Testing

- [ ] Unit tests: JWT validation, agent execution
- [ ] Integration tests: Full workflow with VERIA agent
- [ ] Load tests: 10 concurrent workflows with VERIA agents
- [ ] Failure tests: VERIA API timeout, 500 error, malformed response
- [ ] Security tests: Invalid JWT, wrong projectId, secret injection

### Monitoring

- [ ] Metrics: VERIA agent execution duration, success rate
- [ ] Logs: VERIA API requests/responses in workflow traces
- [ ] Alerts: VERIA API timeout threshold (> 30s)
- [ ] Dashboard: VERIA integration health

### Documentation

- [ ] Architecture diagram (CommandCenter + VERIA integration)
- [ ] API reference (VERIA endpoints + auth)
- [ ] Runbook: VERIA agent troubleshooting
- [ ] Deployment guide: VERIA in production environment

---

## Part 9: Summary & Key Takeaways

### Current State Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| Federation Support | ✅ Ready | NATS heartbeat infrastructure in place |
| API Boundaries | ⚠️ Partial | Need JWT auth for external access |
| Event Architecture | ✅ Ready | NATS JetStream subject namespacing ready |
| Secret Management | ❌ Not Ready | No per-agent secret injection |
| Timeout Protection | ❌ Not Ready | External calls may hang indefinitely |
| Observability | ✅ Good | OpenTelemetry + Grafana dashboards ready |

### VERIA Integration Readiness

**Overall**: 70% ready for integration

**Blockers** (Must Fix Before Production):
1. JWT authentication framework
2. Timeout protection for external calls
3. Secret injection mechanism
4. Circular dependency detection

**Nice-to-Have** (Can Implement Later):
1. Advanced rate limiting
2. Automatic retry with exponential backoff
3. Schema versioning

### Success Criteria

Integration is successful when:
1. ✅ VERIA agents executable within CommandCenter workflows
2. ✅ All external API calls timeout after 30 seconds
3. ✅ Secrets never exposed in logs or context
4. ✅ Circular workflows detected and blocked
5. ✅ 99% workflow success rate in load tests (10 concurrent)
6. ✅ Latency p95 < 5 seconds for local agents

---

## Appendix A: VERIA API Contracts (Proposed)

### Attestation Endpoint

```
POST /api/attest
Authorization: X-API-Key: veria-secret-key
X-CommandCenter-ProjectId: 1
X-CommandCenter-WorkflowRunId: uuid
Content-Type: application/json

Request:
{
  "findings": [
    {
      "category": "secret",
      "severity": "critical",
      "file": "src/config.ts",
      "line": 42,
      "description": "Database password found in code"
    }
  ],
  "compliance_level": "medium",
  "project_context": {
    "name": "my-app",
    "language": "typescript"
  }
}

Response 200 OK:
{
  "success": true,
  "attestation_id": "veria-attest-20251203-001",
  "compliance_score": 78,
  "timestamp": "2025-12-03T10:30:00Z",
  "details": {
    "validated_findings": 23,
    "failed_findings": 2,
    "recommendations": [
      "Move secrets to environment variables",
      "Add .env to .gitignore"
    ]
  }
}

Response 400 Bad Request:
{
  "error": "invalid_request",
  "message": "Missing required field: findings"
}

Response 401 Unauthorized:
{
  "error": "unauthorized",
  "message": "Invalid API key"
}

Response 503 Service Unavailable:
{
  "error": "service_unavailable",
  "message": "VERIA is temporarily unavailable"
}
```

### Analysis Endpoint

```
POST /api/analyze
Authorization: X-API-Key: veria-secret-key
Content-Type: application/json

Request:
{
  "type": "dependency_risk",
  "scope": "repository",
  "target": {
    "repository_url": "https://github.com/example/repo",
    "commit_sha": "abc123..."
  }
}

Response 200 OK:
{
  "analysis_id": "veria-analysis-20251203-001",
  "status": "completed",
  "type": "dependency_risk",
  "timestamp": "2025-12-03T10:35:00Z",
  "findings": {
    "high_risk_dependencies": 3,
    "known_vulnerabilities": 2,
    "unmaintained_packages": 1
  }
}
```

---

## Appendix B: NATS Subject Hierarchy (Proposed)

```
hub/
  project/
    {projectId}/
      created
      started
      stopped
      deleted

  workflow/
    {projectId}/
      trigger
      scheduled
      execute
      success
      failed

  agent/
    {projectId}/
      registered
      executed
      error

  graph/
    {projectId}/
      file.updated
      symbol.analyzed
      audit.completed

  approval/
    {projectId}/
      requested
      approved
      rejected

  presence/
    {projectId}  (heartbeat)

veria/
  intelligence/
    analysis.completed
    anomaly.detected
    recommendation.generated
    attestation.issued

  compliance/
    validation.completed
    report.generated
```

---

**Document Status**: Complete
**Last Updated**: 2025-12-03
**Next Review**: After Phase 1 JWT implementation
**Owned By**: @danielconnolly
