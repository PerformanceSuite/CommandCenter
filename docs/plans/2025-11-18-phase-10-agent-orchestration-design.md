# Phase 10: Agent Orchestration & Workflow Automation - Design Document

**Date**: 2025-11-18
**Status**: Design Complete - Ready for Implementation
**Design Philosophy**: Dagger-Powered + Vercel-Inspired + Risk-Based Approval

---

## Executive Summary

Phase 10 introduces a **Dagger-powered agent orchestration system** that enables CommandCenter instances to execute automated, event-driven workflows. The design combines:

- **Vercel's Production Learnings**: Stateless agents, structured outputs, human-in-the-loop for critical actions
- **Dagger SDK**: Sandboxed agent execution, reproducible environments, type-safe orchestration
- **Risk-Based Safety**: Auto-execute low-risk tasks (monitoring, alerts), require approval for high-impact actions (deployments, code changes)

**Core Architecture**:
- TypeScript/Prisma orchestration service (faithful to blueprint)
- Dagger SDK for isolated agent container execution
- NATS event bridge to Python backend
- VISLZR UI for workflow building and execution monitoring

---

## 1. System Architecture

### 1.1 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CommandCenter Ecosystem                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  Python Backend  │◄───────►│ Orchestration    │             │
│  │  (FastAPI)       │  NATS   │ Service          │             │
│  │                  │         │ (TypeScript)     │             │
│  │  - Graph Service │         │  - Agent Registry│             │
│  │  - Audit Service │         │  - Workflow Runner             │
│  │  - Tech Radar    │         │  - Approval Mgmt │             │
│  └──────────────────┘         └──────────────────┘             │
│           │                            │                         │
│           │                            ▼                         │
│           │                   ┌──────────────────┐             │
│           │                   │ Dagger Execution │             │
│           │                   │ Layer (SDK)      │             │
│           │                   │                  │             │
│           │                   │  ┌────────────┐  │             │
│           │                   │  │ Agent      │  │             │
│           │                   │  │ Container  │  │             │
│           │                   │  └────────────┘  │             │
│           │                   └──────────────────┘             │
│           │                            │                         │
│           ▼                            │                         │
│  ┌──────────────────┐                 │                         │
│  │   PostgreSQL     │◄────────────────┘                         │
│  │                  │  Prisma ORM                                │
│  │  - Agents        │                                            │
│  │  - Workflows     │                                            │
│  │  - WorkflowRuns  │                                            │
│  │  - Approvals     │                                            │
│  └──────────────────┘                                            │
│                                                                  │
│  ┌──────────────────┐                                            │
│  │   VISLZR UI      │                                            │
│  │  (React)         │                                            │
│  │                  │                                            │
│  │  - Workflow Builder                                           │
│  │  - Execution Monitor                                          │
│  │  - Approval UI   │                                            │
│  └──────────────────┘                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

**Event → Workflow → Execution → Result**

1. **Trigger Event**: Code change, health alert, schedule, or manual trigger
2. **Python Backend** publishes NATS event (`workflow.trigger.*`, `graph.file.updated`, etc.)
3. **Orchestration Service** receives event, matches to workflow(s) via trigger patterns
4. **Workflow Runner** creates `WorkflowRun`, executes DAG nodes in topological order
5. **Dagger Executor** runs each agent in isolated container with resource limits
6. **Agent** processes input, returns **structured JSON output** (Zod-validated)
7. **Approval Gate** (if required): Pause workflow, request human decision via VISLZR
8. **Result Collection**: Store `AgentRun` records, update `WorkflowRun` status
9. **Completion Event**: Publish results back to NATS for Python backend consumption

---

## 2. Database Schema (Prisma)

### 2.1 Agent Registry

```prisma
model Agent {
  id            String   @id @default(cuid())
  projectId     Int      // Multi-tenant isolation
  name          String
  type          AgentType // LLM | RULE | API | SCRIPT
  description   String?
  entryPath     String   // Path to agent module
  version       String
  riskLevel     RiskLevel // AUTO | APPROVAL_REQUIRED
  registeredAt  DateTime @default(now())
  updatedAt     DateTime @updatedAt

  capabilities  AgentCapability[]
  runs          AgentRun[]
  workflowNodes WorkflowNode[]

  @@unique([projectId, name])
  @@index([projectId, type])
}

model AgentCapability {
  id          String @id @default(cuid())
  agentId     String
  name        String
  description String?
  inputSchema Json   // JSON Schema for inputs
  outputSchema Json  // JSON Schema for outputs

  agent       Agent  @relation(fields: [agentId], references: [id], onDelete: Cascade)

  @@unique([agentId, name])
}

model AgentRun {
  id          String      @id @default(cuid())
  agentId     String
  workflowRunId String?
  inputJson   Json
  outputJson  Json?
  status      RunStatus   // PENDING | RUNNING | SUCCESS | FAILED
  error       String?
  startedAt   DateTime    @default(now())
  finishedAt  DateTime?
  durationMs  Int?

  agent       Agent       @relation(fields: [agentId], references: [id])
  workflowRun WorkflowRun? @relation(fields: [workflowRunId], references: [id])

  @@index([agentId, status])
  @@index([workflowRunId])
}
```

### 2.2 Workflow System

```prisma
model Workflow {
  id          String         @id @default(cuid())
  projectId   Int
  name        String
  description String?
  trigger     Json           // Event pattern + filters
  status      WorkflowStatus // ACTIVE | DRAFT | ARCHIVED
  createdAt   DateTime       @default(now())
  updatedAt   DateTime       @updatedAt

  nodes       WorkflowNode[]
  runs        WorkflowRun[]

  @@unique([projectId, name])
  @@index([projectId, status])
}

model WorkflowNode {
  id          String   @id @default(cuid())
  workflowId  String
  agentId     String
  action      String   // Capability name
  inputsJson  Json     // Input mapping/template
  dependsOn   String[] // Array of node IDs (for DAG)
  approvalRequired Boolean @default(false)

  workflow    Workflow @relation(fields: [workflowId], references: [id], onDelete: Cascade)
  agent       Agent    @relation(fields: [agentId], references: [id])

  @@index([workflowId])
}

model WorkflowRun {
  id          String      @id @default(cuid())
  workflowId  String
  trigger     String      // Event that triggered this run
  contextJson Json        // Event context/payload
  status      RunStatus   // PENDING | RUNNING | SUCCESS | FAILED | WAITING_APPROVAL
  startedAt   DateTime    @default(now())
  finishedAt  DateTime?

  workflow    Workflow    @relation(fields: [workflowId], references: [id])
  agentRuns   AgentRun[]
  approvals   WorkflowApproval[]

  @@index([workflowId, status])
  @@index([startedAt])
}

model WorkflowApproval {
  id            String      @id @default(cuid())
  workflowRunId String
  nodeId        String
  status        ApprovalStatus // PENDING | APPROVED | REJECTED
  requestedAt   DateTime    @default(now())
  respondedAt   DateTime?
  respondedBy   String?     // User ID (future auth integration)
  notes         String?

  workflowRun   WorkflowRun @relation(fields: [workflowRunId], references: [id])

  @@index([workflowRunId, status])
}

enum AgentType {
  LLM
  RULE
  API
  SCRIPT
}

enum RiskLevel {
  AUTO              // Executes immediately
  APPROVAL_REQUIRED // Requires human approval
}

enum RunStatus {
  PENDING
  RUNNING
  SUCCESS
  FAILED
  WAITING_APPROVAL
}

enum WorkflowStatus {
  ACTIVE
  DRAFT
  ARCHIVED
}

enum ApprovalStatus {
  PENDING
  APPROVED
  REJECTED
}
```

**Design Decisions**:
- **Multi-tenant**: `projectId` enforces data isolation (aligns with P0 security fixes)
- **Structured schemas**: `inputSchema`/`outputSchema` enforce Vercel's pattern
- **Approval tracking**: Separate table for audit trail and human-in-the-loop
- **Flexible risk**: Agent-level `riskLevel` + node-level `approvalRequired`

---

## 3. Dagger-Powered Agent Execution

### 3.1 Execution Architecture

**Why Dagger?**
- ✅ **Reproducible**: Same container image → same results every time
- ✅ **Sandboxed**: Agents isolated from host and each other
- ✅ **Parallel**: Dagger handles concurrent DAG node execution
- ✅ **Cached**: Layer caching speeds up repeated executions
- ✅ **Type-safe**: Full TypeScript SDK with IDE autocomplete

### 3.2 Agent Executor Service

```typescript
// orchestration-service/src/dagger/agent-executor.ts

import { connect, Client, Container } from '@dagger.io/dagger';

export interface AgentExecutionConfig {
  maxMemoryMb: number;      // Default: 512
  timeoutSeconds: number;   // Default: 300 (5 min)
  outputSchema: object;     // JSON Schema for validation
  secrets?: Record<string, string>;
  allowNetwork?: boolean;   // Default: false
}

export interface AgentExecutionResult {
  success: boolean;
  output?: unknown;
  error?: string;
  executionTimeMs: number;
  containerLogs?: string;
}

export class DaggerAgentExecutor {
  private client: Client;

  async connect() {
    this.client = await connect();
  }

  async executeAgent(
    agentPath: string,
    input: unknown,
    config: AgentExecutionConfig
  ): Promise<AgentExecutionResult> {
    const startTime = Date.now();

    try {
      // 1. Create isolated container
      let container = this.client
        .container()
        .from('node:20-alpine')
        .withDirectory('/workspace', this.client.host().directory('.'))
        .withWorkdir('/workspace')
        .withExec(['npm', 'install']);

      // 2. Inject secrets (if needed)
      if (config.secrets) {
        for (const [key, value] of Object.entries(config.secrets)) {
          const secret = this.client.setSecret(key, value);
          container = container.withSecretVariable(key, secret);
        }
      }

      // 3. Apply resource limits
      container = container
        .withEnvVariable(
          'NODE_OPTIONS',
          `--max-old-space-size=${config.maxMemoryMb}`
        );

      // 4. Execute agent with timeout
      const result = await container
        .withExec([
          'timeout',
          config.timeoutSeconds.toString(),
          'node',
          agentPath,
          JSON.stringify(input)
        ])
        .stdout();

      // 5. Parse and validate structured output
      const output = JSON.parse(result);
      this.validateAgainstSchema(output, config.outputSchema);

      return {
        success: true,
        output,
        executionTimeMs: Date.now() - startTime
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        executionTimeMs: Date.now() - startTime,
        containerLogs: await this.getContainerLogs(container)
      };
    }
  }

  private validateAgainstSchema(data: unknown, schema: object): void {
    // Use Ajv or Zod for JSON Schema validation
    // Throws if validation fails
  }
}
```

### 3.3 Agent Definition Pattern (Vercel-style)

**Key Principle**: Structured outputs using Zod schemas

```typescript
// agents/security-scanner/index.ts

import { z } from 'zod';

// Input schema - defines what agent expects
const InputSchema = z.object({
  repositoryPath: z.string(),
  scanType: z.enum(['FULL', 'INCREMENTAL']),
  baseCommit: z.string().optional()
});

// Output schema - defines what agent returns (STRUCTURED!)
const OutputSchema = z.object({
  vulnerabilities: z.array(z.object({
    severity: z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    cve: z.string().optional(),
    file: z.string(),
    line: z.number(),
    description: z.string(),
    recommendation: z.string()
  })),
  summary: z.object({
    total: z.number(),
    critical: z.number(),
    high: z.number(),
    medium: z.number(),
    low: z.number()
  }),
  scanDurationMs: z.number()
});

// Agent manifest (registered in database)
export const manifest = {
  name: 'security-scanner',
  type: 'SCRIPT',
  riskLevel: 'AUTO', // Scanning is read-only, no approval needed
  capabilities: [{
    name: 'scanRepository',
    description: 'Run security scan on repository',
    inputSchema: InputSchema,
    outputSchema: OutputSchema
  }]
};

// Agent execution function
export async function execute(input: z.infer<typeof InputSchema>) {
  const startTime = Date.now();

  // 1. Validate input
  const validated = InputSchema.parse(input);

  // 2. Run security scan (Snyk, Semgrep, etc.)
  const vulnerabilities = await runSecurityScan(validated);

  // 3. Return structured output (validated!)
  return OutputSchema.parse({
    vulnerabilities,
    summary: calculateSummary(vulnerabilities),
    scanDurationMs: Date.now() - startTime
  });
}
```

**Other Agent Examples**:

```typescript
// agents/notifier/index.ts - Slack notifications
const OutputSchema = z.object({
  messageId: z.string(),
  channel: z.string(),
  timestamp: z.string(),
  sent: z.boolean()
});

// agents/patcher/index.ts - Auto-generate fix PRs
const OutputSchema = z.object({
  prNumber: z.number(),
  prUrl: z.string(),
  branch: z.string(),
  filesModified: z.array(z.string()),
  estimatedImpact: z.enum(['LOW', 'MEDIUM', 'HIGH'])
});
// Note: This would have riskLevel: 'APPROVAL_REQUIRED'

// agents/compliance-checker/index.ts - Check regulatory compliance
const OutputSchema = z.object({
  compliant: z.boolean(),
  violations: z.array(z.object({
    rule: z.string(),
    severity: z.enum(['WARNING', 'ERROR']),
    location: z.string(),
    remediation: z.string()
  })),
  score: z.number().min(0).max(100)
});
```

### 3.4 Resource Limits & Safety

**Default Limits**:
- **Memory**: 512MB (configurable per agent)
- **Timeout**: 5 minutes (max 30 minutes)
- **Network**: Isolated by default, explicit allow-list for external APIs
- **Filesystem**: Read-only except `/tmp`
- **CPU**: Shared (no hard limit, relies on Dagger scheduling)

**Security Features**:
- Secrets injected via Dagger Secrets API (never logged)
- Container runs as non-root user
- No host filesystem access (except explicit mounts)
- Network isolation prevents lateral movement

---

## 4. Workflow Execution Engine

### 4.1 DAG Runner

```typescript
// orchestration-service/src/workflow/runner.ts

export class WorkflowRunner {
  constructor(
    private daggerExecutor: DaggerAgentExecutor,
    private prisma: PrismaClient
  ) {}

  async executeWorkflow(workflowRun: WorkflowRun) {
    const workflow = await this.loadWorkflow(workflowRun.workflowId);
    const dag = this.buildDAG(workflow.nodes);

    // Topological sort for execution order
    const executionPlan = this.topologicalSort(dag);

    // Execute batches (nodes with no mutual dependencies run in parallel)
    for (const batch of executionPlan) {
      await Promise.all(
        batch.map(node => this.executeNode(node, workflowRun))
      );
    }

    // Mark workflow complete
    await this.prisma.workflowRun.update({
      where: { id: workflowRun.id },
      data: {
        status: 'SUCCESS',
        finishedAt: new Date()
      }
    });
  }

  async executeNode(node: WorkflowNode, workflowRun: WorkflowRun) {
    // Check if approval required
    if (node.approvalRequired) {
      await this.requestApproval(node, workflowRun);
      await this.waitForApproval(workflowRun.id, node.id);
    }

    // Resolve inputs from previous node outputs
    const inputs = this.resolveInputs(node.inputsJson, workflowRun);

    // Execute agent via Dagger
    const agent = await this.prisma.agent.findUnique({
      where: { id: node.agentId },
      include: { capabilities: true }
    });

    const capability = agent.capabilities.find(c => c.name === node.action);

    const result = await this.daggerExecutor.executeAgent(
      agent.entryPath,
      inputs,
      {
        maxMemoryMb: 512,
        timeoutSeconds: 300,
        outputSchema: capability.outputSchema
      }
    );

    // Store result
    const agentRun = await this.prisma.agentRun.create({
      data: {
        agentId: node.agentId,
        workflowRunId: workflowRun.id,
        inputJson: inputs,
        outputJson: result.output,
        status: result.success ? 'SUCCESS' : 'FAILED',
        error: result.error,
        durationMs: result.executionTimeMs
      }
    });

    return result.output;
  }

  private resolveInputs(inputTemplate: Json, workflowRun: WorkflowRun): unknown {
    // Template syntax: {{ context.repositoryPath }}, {{ nodes.scan.output.vulnerabilities }}
    // Replace placeholders with actual values from context or previous node outputs
  }

  private async requestApproval(node: WorkflowNode, workflowRun: WorkflowRun) {
    await this.prisma.workflowApproval.create({
      data: {
        workflowRunId: workflowRun.id,
        nodeId: node.id,
        status: 'PENDING'
      }
    });

    await this.prisma.workflowRun.update({
      where: { id: workflowRun.id },
      data: { status: 'WAITING_APPROVAL' }
    });

    // Publish NATS event for VISLZR UI
    await this.nats.publish('workflow.approval.requested', {
      workflowRunId: workflowRun.id,
      nodeId: node.id
    });
  }

  private async waitForApproval(workflowRunId: string, nodeId: string) {
    // Poll database until approval status changes
    while (true) {
      const approval = await this.prisma.workflowApproval.findFirst({
        where: { workflowRunId, nodeId }
      });

      if (approval.status === 'APPROVED') {
        return;
      } else if (approval.status === 'REJECTED') {
        throw new Error('Workflow approval rejected by user');
      }

      await new Promise(resolve => setTimeout(resolve, 1000)); // Poll every 1s
    }
  }
}
```

### 4.2 NATS Event Integration

```typescript
// orchestration-service/src/events/nats-bridge.ts

export class OrchestrationEventBridge {
  constructor(
    private nats: NatsConnection,
    private workflowRunner: WorkflowRunner,
    private prisma: PrismaClient
  ) {}

  async setupEventListeners() {
    // Listen for manual workflow triggers from Python backend
    await this.nats.subscribe('workflow.trigger.*', async (msg) => {
      const { workflowName, context } = JSON.parse(msg.data);

      const workflow = await this.prisma.workflow.findFirst({
        where: {
          name: workflowName,
          status: 'ACTIVE'
        }
      });

      if (workflow) {
        const workflowRun = await this.prisma.workflowRun.create({
          data: {
            workflowId: workflow.id,
            trigger: msg.subject,
            contextJson: context,
            status: 'PENDING'
          }
        });

        await this.workflowRunner.executeWorkflow(workflowRun);
      }
    });

    // Listen for code change events (from graph service)
    await this.nats.subscribe('graph.file.updated', async (msg) => {
      const { filePath, projectId, repositoryPath } = JSON.parse(msg.data);

      // Find workflows triggered by file changes
      const workflows = await this.prisma.workflow.findMany({
        where: {
          projectId,
          status: 'ACTIVE',
          trigger: {
            path: ['event'],
            equals: 'graph.file.updated'
          }
        }
      });

      for (const workflow of workflows) {
        // Check if file path matches trigger filters
        if (this.matchesTriggerFilters(workflow.trigger, { filePath })) {
          await this.triggerWorkflow(workflow, msg.data);
        }
      }
    });

    // Listen for audit results
    await this.nats.subscribe('audit.result.*', async (msg) => {
      const { severity, findings, projectId } = JSON.parse(msg.data);

      // Trigger workflows based on severity
      const workflows = await this.findWorkflowsByTrigger({
        event: 'audit.result.fail',
        projectId,
        filters: { severity }
      });

      for (const workflow of workflows) {
        await this.triggerWorkflow(workflow, msg.data);
      }
    });
  }

  async publishWorkflowComplete(workflowRun: WorkflowRun) {
    // Publish results back to Python backend
    const agentRuns = await this.prisma.agentRun.findMany({
      where: { workflowRunId: workflowRun.id }
    });

    await this.nats.publish(
      `workflow.completed.${workflowRun.workflow.name}`,
      JSON.stringify({
        workflowRunId: workflowRun.id,
        status: workflowRun.status,
        results: agentRuns.map(run => ({
          agentName: run.agent.name,
          output: run.outputJson
        }))
      })
    );
  }
}
```

**Event Subjects**:

**Incoming (Python → Orchestrator)**:
- `workflow.trigger.<workflowName>` - Manual workflow execution
- `graph.file.updated` - Code file modified
- `graph.symbol.changed` - Function/class changed
- `audit.result.*` - Security/compliance results
- `hub.health.status` - Service health changes

**Outgoing (Orchestrator → Python)**:
- `workflow.started.<workflowId>` - Workflow begins
- `workflow.completed.<workflowName>` - Workflow finished
- `workflow.approval.requested` - Human approval needed
- `agent.executed.<agentName>` - Agent completed (for monitoring)

---

## 5. Workflow Definition (YAML)

### 5.1 Example: Security Audit on PR

```yaml
# workflows/security-audit-on-pr.yaml
name: security-audit-deploy
description: Run security scan on code changes, create fix PR if needed

trigger:
  event: graph.file.updated
  filters:
    filePath: "**.{ts,tsx,js,jsx,py}"
    branch: "main"

nodes:
  - id: scan
    agent: security-scanner
    action: scanRepository
    inputs:
      repositoryPath: "{{ context.repositoryPath }}"
      scanType: "INCREMENTAL"
      baseCommit: "{{ context.previousCommit }}"
    approvalRequired: false

  - id: assess
    agent: security-assessor
    action: evaluateRisk
    inputs:
      vulnerabilities: "{{ nodes.scan.output.vulnerabilities }}"
    dependsOn: [scan]
    approvalRequired: false

  - id: notify-if-critical
    agent: notifier
    action: sendSlackAlert
    inputs:
      channel: "#security-alerts"
      message: "🚨 {{ nodes.assess.output.summary.critical }} CRITICAL vulnerabilities detected in {{ context.repositoryPath }}"
      condition: "{{ nodes.assess.output.summary.critical > 0 }}"
    dependsOn: [assess]
    approvalRequired: false

  - id: create-fix-pr
    agent: patcher
    action: generateFixPR
    inputs:
      vulnerabilities: "{{ nodes.scan.output.vulnerabilities }}"
      repositoryPath: "{{ context.repositoryPath }}"
      targetBranch: "security-fixes-{{ nodes.scan.output.scanId }}"
    dependsOn: [assess]
    approvalRequired: true  # REQUIRES APPROVAL before creating PR
```

### 5.2 Example: Automated Compliance Check

```yaml
# workflows/compliance-check-weekly.yaml
name: compliance-check-weekly
description: Weekly compliance audit with auto-remediation

trigger:
  schedule: "0 9 * * 1" # Every Monday at 9 AM

nodes:
  - id: scan-compliance
    agent: compliance-checker
    action: auditProject
    inputs:
      projectId: "{{ context.projectId }}"
      standards: ["SOC2", "GDPR", "HIPAA"]
    approvalRequired: false

  - id: generate-report
    agent: report-generator
    action: createPDF
    inputs:
      violations: "{{ nodes.scan-compliance.output.violations }}"
      score: "{{ nodes.scan-compliance.output.score }}"
      template: "compliance-report"
    dependsOn: [scan-compliance]
    approvalRequired: false

  - id: email-stakeholders
    agent: notifier
    action: sendEmail
    inputs:
      recipients: ["compliance@company.com", "security@company.com"]
      subject: "Weekly Compliance Report - Score: {{ nodes.scan-compliance.output.score }}/100"
      attachment: "{{ nodes.generate-report.output.pdfPath }}"
    dependsOn: [generate-report]
    approvalRequired: false
```

---

## 6. VISLZR UI Integration

### 6.1 Workflow Builder

**Visual DAG Editor**:
- Drag-and-drop agent nodes from palette
- Connect nodes to define dependencies
- Configure node inputs with dynamic form (based on `inputSchema`)
- Toggle approval requirements per node
- Save workflow as YAML + register in database

**Components**:
```typescript
// hub/vislzr/src/components/WorkflowBuilder/

WorkflowCanvas.tsx       // React Flow canvas
AgentPalette.tsx         // Draggable agent library
AgentNodeConfig.tsx      // Node configuration panel
WorkflowControls.tsx     // Save/Test/Deploy buttons
TriggerConfig.tsx        // Event trigger configuration
```

### 6.2 Execution Monitor

**Real-time Workflow Visualization**:
- Live DAG with color-coded node status:
  - 🟢 Green: Completed successfully
  - 🟡 Yellow: Running
  - 🔵 Blue: Waiting for approval
  - 🔴 Red: Failed
  - ⚪ Gray: Pending (not started)
- Timeline view of agent executions
- Expandable nodes showing input/output JSON
- Logs panel with container stdout/stderr

**Components**:
```typescript
// hub/vislzr/src/components/WorkflowMonitor/

ExecutionView.tsx        // Main monitor component
ExecutionTimeline.tsx    // Chronological agent runs
NodeStatusBadge.tsx      // Status indicators
AgentRunDetails.tsx      // Detailed run info
LogViewer.tsx            // Container logs
```

### 6.3 Approval UI

**Contextual Approval Request**:
- Display agent name, description, risk level
- Show input data (what agent will process)
- Show output/recommendation (what agent suggests)
- Approve/Reject buttons with optional notes
- Approval history/audit trail

**Example Approval Card**:
```
┌─────────────────────────────────────────────────┐
│ ⚠️  APPROVAL REQUIRED                           │
├─────────────────────────────────────────────────┤
│ Agent: Patcher                                  │
│ Action: Generate Fix PR                         │
│                                                 │
│ 📋 Proposed Action:                             │
│ Create pull request with security fixes        │
│ - Branch: security-fixes-abc123                │
│ - Files: auth.ts, validation.ts                │
│                                                 │
│ 🔍 Agent Analysis:                              │
│ {                                               │
│   "vulnerabilities": [                          │
│     {                                           │
│       "severity": "HIGH",                       │
│       "cve": "CVE-2024-1234",                  │
│       "file": "auth.ts",                        │
│       "fix": "Use bcrypt instead of md5"       │
│     }                                           │
│   ]                                             │
│ }                                               │
│                                                 │
│ 📝 Notes (optional):                            │
│ [________________]                              │
│                                                 │
│ [✅ Approve & Continue]  [❌ Reject & Cancel]   │
└─────────────────────────────────────────────────┘
```

---

## 7. Observability & Telemetry

### 7.1 OpenTelemetry Integration

**Trace Spans**:
- Parent span: `workflow.<workflowName>`
- Child spans: `agent.<agentName>.<action>`
- Attributes: `workflow.id`, `workflow.run_id`, `project.id`, `agent.version`

**Example Trace**:
```
workflow.security-audit-deploy (2.4s)
├─ agent.security-scanner.scanRepository (1.2s)
├─ agent.security-assessor.evaluateRisk (0.3s)
├─ agent.notifier.sendSlackAlert (0.1s)
└─ agent.patcher.generateFixPR (0.8s) [WAITING_APPROVAL]
```

### 7.2 Prometheus Metrics

```typescript
// Metrics to track
const agentExecutionDuration = new Histogram({
  name: 'agent_execution_duration_ms',
  help: 'Agent execution time in milliseconds',
  labelNames: ['agent_name', 'status']
});

const agentExecutionCount = new Counter({
  name: 'agent_execution_total',
  help: 'Total agent executions',
  labelNames: ['agent_name', 'status']
});

const workflowRunDuration = new Histogram({
  name: 'workflow_run_duration_ms',
  help: 'Workflow run time in milliseconds',
  labelNames: ['workflow_name', 'status']
});

const approvalResponseTime = new Histogram({
  name: 'approval_response_time_ms',
  help: 'Time from approval request to response',
  labelNames: ['workflow_name', 'approved']
});
```

### 7.3 Grafana Dashboards

**Workflow Overview**:
- Total runs (24h/7d/30d)
- Success rate by workflow
- Average duration by workflow
- Most triggered workflows

**Agent Performance**:
- Execution time percentiles (p50, p95, p99)
- Failure rate by agent
- Resource usage (memory, CPU)
- Most used agents

**Approval Metrics**:
- Pending approvals
- Average response time
- Approve/reject ratio
- Approval backlog over time

**Event Triggers**:
- Trigger frequency by event type
- Trigger-to-completion latency
- Failed trigger rate

---

## 8. Risk-Based Approval Framework

### 8.1 Risk Categorization

**AUTO (No Approval)**:
- Read-only operations: Scanning, monitoring, analysis
- Notifications: Slack, email, webhooks
- Reporting: Dashboards, logs, metrics
- Low-impact writes: Tagging, labeling, comments

**APPROVAL_REQUIRED (Human Gate)**:
- Code modifications: PRs, commits, merges
- Deployments: Production releases, config updates
- Resource changes: Scaling, provisioning, deletion
- External API writes: Third-party integrations

### 8.2 Override Mechanisms

**Per-Node Override**:
```yaml
nodes:
  - id: notify
    agent: notifier
    approvalRequired: false  # Override agent's riskLevel
```

**Trusted Contexts**:
- Certain workflows/triggers can bypass approval (e.g., emergency runbooks)
- Configured via `Workflow.approvalPolicy` field

---

## 9. Initial Agent Set

### 9.1 Priority Agents

1. **security-scanner** (SCRIPT, AUTO)
   - Capabilities: `scanRepository`, `scanFile`
   - Tools: Snyk, Semgrep, npm audit
   - Outputs: Structured vulnerability list

2. **compliance-checker** (RULE, AUTO)
   - Capabilities: `auditProject`, `checkPolicy`
   - Standards: SOC2, GDPR, HIPAA
   - Outputs: Violation list with remediation

3. **notifier** (API, AUTO)
   - Capabilities: `sendSlack`, `sendEmail`, `sendWebhook`
   - Integrations: Slack, SendGrid, custom webhooks
   - Outputs: Delivery confirmation

4. **patcher** (LLM, APPROVAL_REQUIRED)
   - Capabilities: `generateFixPR`, `suggestFix`
   - Model: GPT-4 or Claude Sonnet
   - Outputs: PR details (number, URL, files)

5. **code-reviewer** (LLM, AUTO for analysis, APPROVAL for actions)
   - Capabilities: `reviewPR`, `scorePR`, `suggestImprovements`
   - Model: GPT-4 or Claude Sonnet
   - Outputs: Review comments, quality score

---

## 10. Deployment Architecture

### 10.1 Service Structure

```
commandcenter/
├── backend/                 # Existing Python/FastAPI
├── frontend/                # Existing React
├── hub/
│   ├── backend/            # Existing Hub
│   ├── vislzr/             # Existing VISLZR
│   └── orchestration/      # NEW: TypeScript orchestration service
│       ├── prisma/
│       │   └── schema.prisma
│       ├── src/
│       │   ├── agents/     # Agent definitions
│       │   ├── dagger/     # Dagger executor
│       │   ├── events/     # NATS bridge
│       │   ├── workflow/   # Workflow runner
│       │   └── api/        # REST API
│       ├── package.json
│       └── tsconfig.json
└── docker-compose.yml      # Add orchestration service
```

### 10.2 Docker Compose Integration

```yaml
# docker-compose.yml (additions)
services:
  orchestration:
    build:
      context: ./hub/orchestration
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://commandcenter:${DB_PASSWORD}@postgres:5432/commandcenter
      - NATS_URL=nats://commandcenter-hub-nats:4222
      - DAGGER_ENGINE=docker
    volumes:
      - ./hub/orchestration:/app
      - /var/run/docker.sock:/var/run/docker.sock  # For Dagger
    depends_on:
      - postgres
      - commandcenter-hub-nats
    ports:
      - "9002:3000"  # Orchestration API
```

---

## 11. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- ✅ Prisma schema + migrations
- ✅ Basic orchestration service scaffolding
- ✅ Dagger executor implementation
- ✅ NATS event bridge
- ✅ Agent registry API

### Phase 2: Core Workflow Engine (Week 3-4)
- ✅ Workflow runner with DAG execution
- ✅ Input resolution (templating)
- ✅ Approval system (database + polling)
- ✅ Error handling + retries

### Phase 3: Initial Agents (Week 5)
- ✅ Security scanner agent
- ✅ Notifier agent
- ✅ Test with example workflows

### Phase 4: VISLZR Integration (Week 6-7)
- ✅ Workflow builder UI
- ✅ Execution monitor
- ✅ Approval UI
- ✅ Agent library browser

### Phase 5: Observability (Week 8)
- ✅ OpenTelemetry tracing
- ✅ Prometheus metrics
- ✅ Grafana dashboards

### Phase 6: Production Readiness (Week 9-10)
- ✅ Additional agents (compliance, patcher, code-reviewer)
- ✅ Load testing
- ✅ Documentation
- ✅ Security audit

---

## 12. Success Criteria

**Functional**:
- ✅ Agents can self-register via API
- ✅ Workflows can be defined via YAML or VISLZR builder
- ✅ Event triggers execute multi-step DAGs successfully
- ✅ Approval gates pause workflows and resume on human decision
- ✅ Agents run in isolated Dagger containers with resource limits

**Performance**:
- ✅ Single-agent workflow completes in < 10s
- ✅ 5-node DAG completes in < 30s
- ✅ System handles 10 concurrent workflows
- ✅ Approval response time < 5s (from UI click to workflow resume)

**Observability**:
- ✅ All workflows traced in Grafana/Jaeger
- ✅ Metrics dashboards show agent performance
- ✅ Logs accessible via VISLZR UI

**Safety**:
- ✅ High-risk actions require approval (tested with patcher agent)
- ✅ Agents cannot access host filesystem or other containers
- ✅ Secrets never appear in logs or outputs

---

## 13. Future Enhancements (Post-Phase 10)

### Phase 12: Cross-Project Orchestration
- Meta Hub triggers workflows across multiple CommandCenter instances
- Federated workflow execution
- Global agent registry

### Advanced Agent Features
- **Streaming outputs**: Real-time agent logs during execution
- **Agent chaining**: Agents can invoke other agents
- **Conditional execution**: Skip nodes based on previous outputs
- **Parallel batching**: Run same agent across multiple inputs

### LLM Enhancements
- **Tool use**: Agents with tool-calling (MCP integration)
- **Memory**: Agents remember previous runs (vector DB)
- **Learning**: Agents improve based on approval/rejection patterns

---

## 14. References

**External Influences**:
- [Vercel AI Agents Blog](https://vercel.com/blog/what-we-learned-building-agents-at-vercel) - Human-in-the-loop, structured outputs
- [Dagger SDK Docs](https://docs.dagger.io) - Container orchestration patterns
- [AgentFlow](https://github.com/user/agentflow) - Multi-agent patterns (inspiration)

**Internal Docs**:
- `docs/DATA_ISOLATION.md` - Multi-tenant security
- `hub-prototype/phase_10_agent_orchestration_workflow_automation_blueprint.md` - Original blueprint
- `docs/MULTI_TENANT_ISOLATION_AUDIT_2025-11-18.md` - Security baseline

---

**Design Status**: ✅ **APPROVED - Ready for Implementation**

**Next Steps**:
1. Review design document with team
2. Set up git worktree for Phase 10 development
3. Create detailed implementation plan (via `writing-plans` skill)
4. Begin Phase 1 implementation
