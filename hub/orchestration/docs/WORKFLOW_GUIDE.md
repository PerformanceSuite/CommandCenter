# Workflow Creation Guide

Complete guide to designing and creating workflows in the CommandCenter orchestration system.

---

## Quick Start

### Simple 1-Agent Workflow

```typescript
const workflow = {
  name: "security-scan",
  trigger: "MANUAL",
  nodes: [
    {
      id: "scan",
      agentName: "security-scanner",
      input: {
        repositoryPath: "/workspace",
        scanType: "all"
      }
    }
  ],
  edges: []
};
```

### Sequential 2-Agent Workflow

```typescript
const workflow = {
  name: "scan-and-notify",
  trigger: "MANUAL",
  nodes: [
    {
      id: "scan",
      agentName: "security-scanner",
      input: { repositoryPath: "/workspace", scanType: "all" }
    },
    {
      id: "notify",
      agentName: "notifier",
      input: {
        channel: "slack",
        message: "{{scan.output.summary.critical}} critical issues found",
        severity: "critical"
      }
    }
  ],
  edges: [
    { from: "scan", to: "notify" }  // notify runs after scan
  ]
};
```

---

## Workflow Structure

### Core Fields

```typescript
interface Workflow {
  name: string;                    // Workflow identifier
  trigger: "MANUAL" | "EVENT";     // How workflow starts
  nodes: WorkflowNode[];           // Agent executions
  edges: WorkflowEdge[];           // Dependencies (DAG)
}

interface WorkflowNode {
  id: string;                      // Unique node ID
  agentName: string;               // Registered agent name
  input: Record<string, any>;      // Agent input (validated by agent schema)
}

interface WorkflowEdge {
  from: string;                    // Source node ID
  to: string;                      // Target node ID
}
```

---

## DAG (Directed Acyclic Graph)

Workflows are DAGs where:
- **Nodes** = Agent executions
- **Edges** = Dependencies (order of execution)
- **Acyclic** = No circular dependencies

### Linear Workflow

```
scan → notify
```

```typescript
{
  nodes: [
    { id: "scan", agentName: "security-scanner", input: {...} },
    { id: "notify", agentName: "notifier", input: {...} }
  ],
  edges: [
    { from: "scan", to: "notify" }
  ]
}
```

### Parallel Workflow

```
      ┌─> compliance
scan ─┤
      └─> review
```

```typescript
{
  nodes: [
    { id: "scan", agentName: "security-scanner", input: {...} },
    { id: "compliance", agentName: "compliance-checker", input: {...} },
    { id: "review", agentName: "code-reviewer", input: {...} }
  ],
  edges: [
    { from: "scan", to: "compliance" },
    { from: "scan", to: "review" }
  ]
}
```

### Diamond Workflow

```
      ┌─> compliance ─┐
scan ─┤               ├─> notify
      └─> review ─────┘
```

```typescript
{
  nodes: [
    { id: "scan", agentName: "security-scanner", input: {...} },
    { id: "compliance", agentName: "compliance-checker", input: {...} },
    { id: "review", agentName: "code-reviewer", input: {...} },
    { id: "notify", agentName: "notifier", input: {...} }
  ],
  edges: [
    { from: "scan", to: "compliance" },
    { from: "scan", to: "review" },
    { from: "compliance", to: "notify" },
    { from: "review", to: "notify" }
  ]
}
```

---

## Template Resolution

### Basic Templates

Use `{{nodeId.output.field}}` to reference previous node outputs:

```typescript
{
  id: "notify",
  agentName: "notifier",
  input: {
    message: "Found {{scan.output.summary.critical}} critical issues"
  }
}
```

At runtime:
- `scan` node executes, returns `{ summary: { critical: 5 } }`
- Template resolves: `"Found 5 critical issues"`

### Nested Fields

```typescript
{
  message: "Repository: {{scan.output.metadata.repository.name}}"
}
```

### Multiple Templates

```typescript
{
  message: "Scanned {{scan.output.filesScanned}} files, found {{scan.output.summary.total}} issues"
}
```

---

## Approval Workflows

Workflows can require human approval before continuing:

```typescript
const workflow = {
  name: "apply-security-patch",
  trigger: "MANUAL",
  nodes: [
    {
      id: "scan",
      agentName: "security-scanner",
      input: { repositoryPath: "/workspace", scanType: "all" }
    },
    {
      id: "patch",
      agentName: "patcher",  // Risk level: APPROVAL_REQUIRED
      input: {
        repositoryPath: "/workspace",
        patchType: "security-patch",
        target: "{{scan.output.findings[0].file}}",
        changes: {
          oldValue: "{{scan.output.findings[0].code}}",
          newValue: "// FIXED"
        }
      }
    },
    {
      id: "notify",
      agentName: "notifier",
      input: {
        channel: "slack",
        message: "Security patch applied successfully"
      }
    }
  ],
  edges: [
    { from: "scan", to: "patch" },
    { from: "patch", to: "notify" }
  ]
};
```

**Execution Flow**:
1. `scan` runs → completes
2. Workflow detects `patcher` has `APPROVAL_REQUIRED`
3. Workflow pauses at `PENDING_APPROVAL` state
4. User reviews patch details
5. User approves → workflow resumes
6. `patch` runs → completes
7. `notify` runs → workflow complete

---

## Error Handling

### Agent Failure

If an agent fails (exit code 1), the workflow stops:

```
scan (SUCCESS) → patch (FAILED) → notify (SKIPPED)
```

Final workflow status: `FAILED`

### Retry Logic

Currently not supported - agents run once per workflow execution.

**Workaround**: Create a new workflow run.

---

## Workflow Patterns

### Pattern 1: Analysis Pipeline

**Use Case**: Multi-stage code analysis

```typescript
{
  name: "full-analysis",
  nodes: [
    { id: "scan", agentName: "security-scanner", input: {...} },
    { id: "compliance", agentName: "compliance-checker", input: {...} },
    { id: "review", agentName: "code-reviewer", input: {...} },
    { id: "report", agentName: "report-generator", input: {
      security: "{{scan.output}}",
      compliance: "{{compliance.output}}",
      quality: "{{review.output}}"
    }}
  ],
  edges: [
    { from: "scan", to: "report" },
    { from: "compliance", to: "report" },
    { from: "review", to: "report" }
  ]
}
```

### Pattern 2: Conditional Execution (via Template Logic)

**Use Case**: Only notify if critical issues found

```typescript
{
  name: "scan-with-conditional-notify",
  nodes: [
    { id: "scan", agentName: "security-scanner", input: {...} },
    { id: "check", agentName: "condition-evaluator", input: {
      condition: "{{scan.output.summary.critical}} > 0"
    }},
    { id: "notify", agentName: "notifier", input: {
      message: "{{scan.output.summary.critical}} critical issues!"
    }}
  ],
  edges: [
    { from: "scan", to: "check" },
    { from: "check", to: "notify" }  // Only runs if check passes
  ]
}
```

### Pattern 3: Fan-Out / Fan-In

**Use Case**: Parallel processing with aggregation

```typescript
{
  name: "parallel-scan-aggregate",
  nodes: [
    { id: "scan-security", agentName: "security-scanner", input: {...} },
    { id: "scan-quality", agentName: "code-reviewer", input: {...} },
    { id: "scan-compliance", agentName: "compliance-checker", input: {...} },
    { id: "aggregate", agentName: "aggregator", input: {
      results: [
        "{{scan-security.output}}",
        "{{scan-quality.output}}",
        "{{scan-compliance.output}}"
      ]
    }}
  ],
  edges: [
    // All scans run in parallel, aggregate waits for all
    { from: "scan-security", to: "aggregate" },
    { from: "scan-quality", to: "aggregate" },
    { from: "scan-compliance", to: "aggregate" }
  ]
}
```

---

## Best Practices

### 1. Node IDs

✅ **DO**: Use descriptive, kebab-case IDs
```typescript
{ id: "scan-security", agentName: "security-scanner", ... }
{ id: "notify-slack", agentName: "notifier", ... }
```

❌ **DON'T**: Use ambiguous or numbered IDs
```typescript
{ id: "node1", ... }
{ id: "step", ... }
```

### 2. Input Validation

✅ **DO**: Provide all required fields
```typescript
{
  id: "scan",
  agentName: "security-scanner",
  input: {
    repositoryPath: "/workspace",  // Required
    scanType: "all"                // Required
  }
}
```

❌ **DON'T**: Omit required fields (will fail validation)
```typescript
{
  id: "scan",
  agentName: "security-scanner",
  input: {} // Missing required fields
}
```

### 3. Template Syntax

✅ **DO**: Use correct template syntax
```typescript
"{{scan.output.summary.total}}"  // Correct
```

❌ **DON'T**: Use invalid syntax
```typescript
"${scan.output}"  // Wrong - use {{}}
"{scan.output}"   // Wrong - missing second {}
```

### 4. Edge Definition

✅ **DO**: Define edges for dependencies
```typescript
edges: [
  { from: "scan", to: "notify" }
]
```

❌ **DON'T**: Create circular dependencies
```typescript
edges: [
  { from: "scan", to: "notify" },
  { from: "notify", to: "scan" }  // Circular!
]
```

---

## Workflow Examples

See `orchestration/examples/` for complete examples:
- `simple-scan.json` - Single-agent workflow
- `scan-and-notify.json` - Sequential workflow with templates
- `parallel-analysis.json` - Parallel execution
- `approval-workflow.json` - Human-in-the-loop approval

---

*Last updated: 2025-11-20*
