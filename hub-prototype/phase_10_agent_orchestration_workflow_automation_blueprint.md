# Phase 10 — Agent Orchestration & Workflow Automation Blueprint

**Objective:** Introduce a modular Agent Orchestration System that enables CommandCenter instances to execute automated, event-driven workflows using registered agents and defined DAG (Directed Acyclic Graph) templates. This phase transforms CommandCenter from a visualization and coordination platform into an active automation environment.

---

## 0) Overview

### Core Idea
Every CommandCenter instance (e.g., Veria, Performia, ROLLIZR) will:
- Register and manage local **Agents** (LLM-based, script-based, or API-based)
- Define reusable **Workflows** (DAGs connecting actions and agents)
- Execute **event-driven automations** triggered by code changes, health signals, or user actions.

The **Meta Hub** will later use this same mechanism for cross-project orchestration (Phase 12).

---

## 1) Agent Model

### 1.1 Agent Registry Schema (Prisma)
- `Agent(id, projectId, name, type[llm|rule|api|script], description, entryPath, version, capabilities[string[]], registeredAt)`
- `AgentRun(id, agentId, workflowId?, inputJson, outputJson, status[pending|running|success|fail], startedAt, finishedAt)`
- `AgentCapability(id, agentId, name, description)`

Agents are stored per-project. Each CommandCenter instance has its own registry under `/tools/agents/`.

### 1.2 Registration & Discovery
Agents self-register at startup by posting a manifest to the local hub:
```json
{
  "name": "code-reviewer",
  "type": "llm",
  "entryPath": "agents/code-reviewer.ts",
  "capabilities": ["review", "summarize", "score"],
  "version": "1.0.0"
}
```

Hub stores/updates this in the `Agent` table and publishes `agent.registered.<agentId>` over NATS.

---

## 2) Workflow Model

### 2.1 Schema
- `Workflow(id, projectId, name, description, yamlPath, status[active|draft|archived])`
- `WorkflowNode(id, workflowId, agentId, action, inputsJson, outputsJson, dependsOn[string[]])`
- `WorkflowRun(id, workflowId, trigger, contextJson, status, startedAt, finishedAt)`

### 2.2 YAML Template Example
```yaml
name: security-audit-deploy
trigger:
  on: [audit.result.fail]
  filters:
    severity: high
nodes:
  - id: notify
    agent: notifier
    action: sendSlack
    inputs:
      message: "Security issue detected in $project"
  - id: run_patch
    agent: patcher
    action: createFixPR
    dependsOn: [notify]
  - id: retest
    agent: test-runner
    action: runTests
    dependsOn: [run_patch]
```

### 2.3 Workflow Engine
- DAG execution runtime inside the hub (`services/workflow/runner.ts`).
- Resolves dependencies, executes sequentially or concurrently.
- Persists `WorkflowRun` + `AgentRun` states.

---

## 3) Agent Runtime & Execution Flow

### 3.1 Runtime Flow
1. Event or manual trigger → `workflow:execute` (with workflowId + context)
2. WorkflowRunner parses DAG.
3. Each node → emits `agent.request.<agentId>` with inputs.
4. Agent service consumes event, executes handler (local script or LLM call).
5. Emits `agent.result.<agentId>` → runner collects → marks node done.

### 3.2 Event Subjects
- `agent.request.*`
- `agent.result.*`
- `workflow.execute`
- `workflow.node.started`
- `workflow.node.completed`
- `workflow.run.completed`

All subjects are namespaced per-project (e.g., `veria.agent.request.*`).

---

## 4) Workflow Builder UI (VISLZR Extension)

### 4.1 UI Concept
- Visual DAG editor integrated into VISLZR.
- Drag agents into canvas; connect nodes.
- Define triggers and conditions.
- Save → YAML under `/workflows/` + auto-register in DB.

### 4.2 Runtime Visualization
- During execution, VISLZR highlights active nodes (green/yellow/red).
- Logs appear in side panel with streamed outputs.
- Can replay a run or clone as new template.

---

## 5) Action System Integration

### 5.1 Action Metadata
Agents expose actions in `capabilities` and optional manifest fields:
```json
{
  "actions": {
    "runAudit": {
      "description": "Perform static code audit",
      "inputs": {"path": "string"},
      "outputs": {"report": "string"}
    }
  }
}
```

### 5.2 Linking Actions → Workflows
- When a user clicks an action in VISLZR (e.g., “Run Security Check”), the hub checks for bound workflows (`trigger.onAction = actionId`).
- If found, executes DAG automatically.

---

## 6) Event-Driven Automation

### 6.1 Supported Triggers
- **Code Events:** `graph.file.updated`, `graph.symbol.changed`
- **Audit Events:** `audit.result.*`
- **Health Events:** `hub.health.status`
- **Schedule:** Cron-based or interval
- **Manual:** User-triggered in VISLZR or CLI

### 6.2 Example Use Cases
- Run compliance tests when a file in `/schemas` changes.
- Restart a service if health degrades.
- Deploy staging automatically when all audits pass.
- Notify MRKTZR when a partner module updates.

---

## 7) CLI Commands

Add to each project’s `package.json`:
```json
{
  "scripts": {
    "agent:list": "tsx ./scripts/agents/list.ts",
    "agent:register": "tsx ./scripts/agents/register.ts",
    "workflow:list": "tsx ./scripts/workflows/list.ts",
    "workflow:run": "tsx ./scripts/workflows/run.ts",
    "workflow:trigger": "tsx ./scripts/workflows/trigger.ts"
  }
}
```

---

## 8) Security & Sandboxing
- Agents execute in **isolated worker contexts** (Node VM, subprocess, or container sandbox).
- Memory + execution time limits.
- LLM agents restricted via provider keys in Vault.
- Audit logs for every agent run.
- Optional approval workflow for high-impact actions (e.g., deployment).

---

## 9) Observability & Telemetry
- OTel tracing per workflow node → parent span links agent run.
- Metrics:
  - total runs / success / fail
  - avg execution time per agent
  - workflow trigger frequency
- Grafana panels for top agents, workflow duration, trigger rate.

---

## 10) Implementation Steps

### 10.1 Backend
1. Prisma schema (Agent, AgentRun, Workflow, WorkflowNode, WorkflowRun).
2. Implement AgentRegistry service.
3. Implement WorkflowRunner service.
4. Integrate NATS pub/sub for agent.request/result.
5. Add CLI utilities (`agent:*`, `workflow:*`).

### 10.2 Frontend (VISLZR)
1. Add **Workflow Builder** panel.
2. Add **Execution Monitor** overlay.
3. Integrate action trigger binding UI.

### 10.3 Agents (initial set)
- `code-reviewer` (LLM)
- `security-scanner` (Snyk/Semgrep)
- `compliance-checker` (Veria rules)
- `notifier` (Slack/Email)
- `patcher` (auto PR generator)

### 10.4 Testing
- Simulate events; ensure DAG executes and all nodes resolve.
- Visual trace in VISLZR.
- Latency < 500ms for single-agent trigger chain.

---

## 11) Acceptance Criteria

- Agents can self-register and be listed in VISLZR.
- Workflows can be defined via YAML or VISLZR builder.
- Triggering events execute multi-step DAGs successfully.
- Visual playback of workflow execution works in VISLZR.
- CLI `workflow:list` and `workflow:run` operate end-to-end.

---

## 12) Deliverables Checklist
- [ ] Prisma models + migrations
- [ ] AgentRegistry + WorkflowRunner services
- [ ] NATS subjects wired
- [ ] VISLZR workflow builder UI
- [ ] 3–5 sample agents
- [ ] CLI commands
- [ ] Grafana + OTel integration
- [ ] `/docs/phase10-agents.md`

---

> Phase 10 transforms CommandCenter into an agentic automation platform capable of orchestrating intelligent, event-driven workflows within each project instance, forming the foundation for global orchestration in Phase 12.
