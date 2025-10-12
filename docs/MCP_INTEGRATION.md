# MCP Integration Guide

**Model Context Protocol (MCP) Integration for CommandCenter**

This document describes the MCP server implementation in CommandCenter, integration patterns, and best practices for building AI-powered applications.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Provider Types](#provider-types)
4. [Context Management](#context-management)
5. [Session Lifecycle](#session-lifecycle)
6. [Integration Patterns](#integration-patterns)
7. [API Reference](#api-reference)
8. [Examples](#examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

CommandCenter implements the Model Context Protocol (MCP), enabling AI assistants to:
- **Read CommandCenter data** via resources (projects, technologies, research tasks, repositories, schedules, jobs)
- **Execute actions** via tools (create tasks, manage schedules, run jobs)
- **Get guided prompts** for common workflows (analysis, evaluation, planning, review)
- **Maintain stateful sessions** with context management

### Key Features

- **14 Resource Types**: Read-only access to CommandCenter entities
- **10 Action Tools**: Create and manage CommandCenter data
- **7 Prompt Templates**: AI guidance for common workflows
- **Stateful Sessions**: Context management for multi-step interactions
- **Multiple Transports**: HTTP, WebSocket, and stdio support
- **JSON-RPC 2.0**: Standard protocol for client-server communication

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────┐
│           MCP Client (AI Assistant)         │
└────────────┬────────────────────────────────┘
             │ JSON-RPC 2.0
             │
┌────────────▼────────────────────────────────┐
│         MCP Server (CommandCenter)          │
│  ┌───────────────────────────────────────┐  │
│  │     Connection Manager                │  │
│  │  - Session management                 │  │
│  │  - Request routing                    │  │
│  │  - Context storage                    │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │     Protocol Handler                  │  │
│  │  - JSON-RPC parsing                   │  │
│  │  - Response formatting                │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │     Provider Registry                 │  │
│  │  - Resource providers                 │  │
│  │  - Tool providers                     │  │
│  │  - Prompt providers                   │  │
│  └───────────────────────────────────────┘  │
└─────────────┬───────────────────────────────┘
              │
┌─────────────▼───────────────────────────────┐
│      CommandCenter Services & Database      │
└─────────────────────────────────────────────┘
```

### Directory Structure

```
backend/app/mcp/
├── __init__.py
├── server.py              # Core MCP server
├── config.py              # Server configuration
├── connection.py          # Session and connection management
├── protocol.py            # JSON-RPC protocol handler
├── utils.py               # Utilities and error handling
├── providers/
│   ├── base.py            # Base provider classes
│   ├── commandcenter_resources.py  # Resource provider
│   ├── commandcenter_tools.py      # Tool provider
│   └── commandcenter_prompts.py    # Prompt provider
└── transports/
    ├── http.py            # HTTP transport
    ├── websocket.py       # WebSocket transport
    └── stdio.py           # Stdio transport
```

---

## Provider Types

### 1. Resource Providers

**Purpose**: Expose read-only data for AI assistants to understand system state.

**CommandCenter Resources** (14 types):

| URI Pattern | Description | Example |
|------------|-------------|---------|
| `commandcenter://projects` | List all projects | View all tracked projects |
| `commandcenter://projects/{id}` | Project details | Get specific project info |
| `commandcenter://technologies` | List all technologies | Technology radar view |
| `commandcenter://technologies/{id}` | Technology details | Specific tech evaluation |
| `commandcenter://research/tasks` | List research tasks | All research items |
| `commandcenter://research/tasks/{id}` | Task details | Specific task info |
| `commandcenter://repositories` | List repositories | All GitHub repos |
| `commandcenter://repositories/{id}` | Repository details | Specific repo info |
| `commandcenter://schedules` | All schedules | Complete schedule list |
| `commandcenter://schedules/active` | Active schedules | Currently enabled schedules |
| `commandcenter://jobs` | All jobs | Complete job list |
| `commandcenter://jobs/active` | Active jobs | Running/pending jobs |
| `commandcenter://jobs/{id}` | Job details | Specific job status |
| `commandcenter://overview` | System overview | High-level status summary |

**Example Usage**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {}
}

{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/read",
  "params": {
    "uri": "commandcenter://projects"
  }
}
```

### 2. Tool Providers

**Purpose**: Execute actions that modify CommandCenter state.

**CommandCenter Tools** (10 actions):

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `create_research_task` | Create new research task | title, description, status, priority, project_id, technology_id |
| `update_research_task` | Update existing task | task_id, + optional fields |
| `add_technology` | Add new technology | title, domain, vendor, status, relevance, project_id |
| `create_schedule` | Create analysis schedule | name, frequency, parameters, timezone, enabled |
| `execute_schedule` | Manually trigger schedule | schedule_id |
| `enable_schedule` | Enable automated schedule | schedule_id |
| `disable_schedule` | Disable automated schedule | schedule_id |
| `create_job` | Create async job | job_type, parameters, priority, delay |
| `get_job_status` | Check job progress | job_id |
| `cancel_job` | Cancel running job | job_id |

**Example Usage**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "create_research_task",
    "arguments": {
      "title": "Evaluate Kubernetes for microservices",
      "description": "Research Kubernetes orchestration capabilities",
      "status": "todo",
      "priority": "high",
      "project_id": 1
    }
  }
}
```

### 3. Prompt Providers

**Purpose**: Provide AI assistants with structured guidance for complex workflows.

**CommandCenter Prompts** (7 templates):

| Prompt Name | Description | Use Case |
|-------------|-------------|----------|
| `analyze_project` | Project analysis framework | Assess project health and metrics |
| `evaluate_technology` | Technology evaluation guide | Structured tech assessment |
| `plan_research` | Research planning template | Break down research tasks |
| `review_code` | Code review guidance | Systematic code review |
| `generate_report` | Report generation template | Create comprehensive reports |
| `prioritize_tasks` | Task prioritization framework | Rank and organize tasks |
| `architecture_review` | Architecture review guide | System design assessment |

**Example Usage**:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "prompts/get",
  "params": {
    "name": "evaluate_technology",
    "arguments": {
      "technology_name": "Kubernetes",
      "domain": "Infrastructure"
    }
  }
}
```

---

## Context Management

### Overview

Context management enables **stateful interactions** across multiple requests within the same MCP session. This is essential for:
- Multi-step workflows (analysis → planning → execution)
- Maintaining user preferences
- Tracking conversation state
- Caching frequently accessed data

### Context API

**Available Methods**:

| Method | Description | Parameters |
|--------|-------------|------------|
| `context/set` | Set context key-value | `{key: string, value: any}` |
| `context/get` | Get context value | `{key: string, default?: any}` |
| `context/has` | Check if key exists | `{key: string}` |
| `context/delete` | Delete context key | `{key: string}` |
| `context/clear` | Clear all context | `{}` |
| `context/list` | List all context | `{}` |

### Context Lifecycle

```
Session Start
     │
     ▼
Initialize Session
     │
     ▼
Set Context ──────────► context/set {key: "project_id", value: 1}
     │
     ▼
Use Context ──────────► context/get {key: "project_id"}
     │                   Returns: {value: 1, exists: true}
     ▼
Update Context ───────► context/set {key: "step", value: 2}
     │
     ▼
Clear Context ────────► context/clear {}
     │
     ▼
Session End
(Context automatically destroyed)
```

### Usage Examples

#### Example 1: Multi-Step Analysis Workflow

```javascript
// Step 1: Initialize context with project
await ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: 1,
  method: "context/set",
  params: {
    key: "current_project_id",
    value: 1
  }
}));

// Step 2: Store analysis configuration
await ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: 2,
  method: "context/set",
  params: {
    key: "analysis_config",
    value: {
      depth: "comprehensive",
      include_dependencies: true,
      generate_report: true
    }
  }
}));

// Step 3: Retrieve context in later requests
await ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: 3,
  method: "context/get",
  params: {
    key: "current_project_id"
  }
}));
// Returns: {key: "current_project_id", value: 1, exists: true}

// Step 4: Use context to filter resources
const projectId = contextValue;
await ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: 4,
  method: "resources/read",
  params: {
    uri: `commandcenter://projects/${projectId}`
  }
}));
```

#### Example 2: User Preferences

```python
import asyncio
import websockets
import json

async def maintain_preferences():
    uri = "ws://localhost:8000/api/v1/mcp/ws"

    async with websockets.connect(uri) as ws:
        # Set user preferences
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "context/set",
            "params": {
                "key": "user_preferences",
                "value": {
                    "notification_level": "high_priority_only",
                    "default_project": 1,
                    "timezone": "America/New_York"
                }
            }
        }))

        # Later: Retrieve preferences
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "context/get",
            "params": {
                "key": "user_preferences"
            }
        }))

        response = await ws.recv()
        prefs = json.loads(response)["result"]["value"]
        print(f"User timezone: {prefs['timezone']}")
```

#### Example 3: Conversation State Tracking

```javascript
// Track conversation flow
const states = [
  { step: 1, action: "project_selection", data: {project_id: 1} },
  { step: 2, action: "analysis_type", data: {type: "full"} },
  { step: 3, action: "confirm_execution", data: {confirmed: true} }
];

for (const state of states) {
  await ws.send(JSON.stringify({
    jsonrpc: "2.0",
    id: state.step,
    method: "context/set",
    params: {
      key: `step_${state.step}`,
      value: state
    }
  }));
}

// Retrieve entire conversation state
await ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: 10,
  method: "context/list",
  params: {}
}));
// Returns all step_* context entries
```

### Context Best Practices

1. **Use Descriptive Keys**: Use namespaced keys like `workflow:current_step` or `user:preferences`
2. **Clean Up**: Delete temporary context with `context/delete` when no longer needed
3. **Size Limits**: Keep context values reasonably sized (< 1MB per value)
4. **JSON Serializable**: All context values must be JSON serializable
5. **Session Scope**: Context is session-specific and not shared across sessions
6. **Automatic Cleanup**: Context is destroyed when session closes

---

## Session Lifecycle

### Session States

```
┌─────────────┐
│   Created   │  Session initialized
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Uninitialized│  Awaiting initialize() call
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Initialized │  Ready to accept requests
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Active    │  Processing requests, managing context
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Closed    │  Session ended, context destroyed
└─────────────┘
```

### Transport-Specific Behavior

#### HTTP (Ephemeral Sessions)

```python
# Each HTTP request creates and destroys a session
POST /api/v1/mcp/rpc
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {}
}

# Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {...}
}
# Session destroyed after response
```

**Characteristics**:
- **Stateless**: No context preservation between requests
- **Fast**: No session overhead
- **Use Case**: One-off queries, stateless operations

#### WebSocket (Persistent Sessions)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/mcp/ws');

ws.onopen = () => {
  // Session created and persists until disconnect
  ws.send(JSON.stringify({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      client_info: {name: "MyAI", version: "1.0.0"}
    }
  }));
};

// Session remains active for multiple requests
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: 2,
  method: "context/set",
  params: {key: "state", value: "step1"}
}));

// Context preserved
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: 3,
  method: "context/get",
  params: {key: "state"}
}));
// Returns: {value: "step1", exists: true}

ws.close(); // Session destroyed, context cleared
```

**Characteristics**:
- **Stateful**: Context preserved across requests
- **Efficient**: Single connection for multiple operations
- **Use Case**: Interactive workflows, real-time updates

---

## Integration Patterns

### Pattern 1: Read-Only Dashboard

**Use Case**: AI assistant displays CommandCenter status

```javascript
async function buildDashboard() {
  // 1. Get system overview
  const overview = await mcpCall("resources/read", {
    uri: "commandcenter://overview"
  });

  console.log(`Projects: ${overview.counts.projects}`);
  console.log(`Technologies: ${overview.counts.technologies}`);
  console.log(`Active Jobs: ${overview.counts.jobs.active}`);

  // 2. Get active schedules
  const schedules = await mcpCall("resources/read", {
    uri: "commandcenter://schedules/active"
  });

  console.log(`Active Schedules: ${schedules.length}`);

  // 3. List running jobs
  const jobs = await mcpCall("resources/read", {
    uri: "commandcenter://jobs/active"
  });

  for (const job of jobs) {
    console.log(`Job ${job.id}: ${job.status} (${job.progress}%)`);
  }
}
```

### Pattern 2: Guided Workflow

**Use Case**: AI guides user through technology evaluation

```python
async def evaluate_technology_workflow(ws):
    # Step 1: Get prompt template
    await ws.send(json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "prompts/get",
        "params": {
            "name": "evaluate_technology",
            "arguments": {
                "technology_name": "Kubernetes",
                "domain": "Infrastructure"
            }
        }
    }))

    prompt = await ws.recv()
    # AI uses prompt to guide conversation

    # Step 2: Create research task based on evaluation
    await ws.send(json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "create_research_task",
            "arguments": {
                "title": "Kubernetes Production Readiness",
                "description": "Evaluate K8s for production deployment",
                "status": "in_progress",
                "priority": "high",
                "project_id": 1
            }
        }
    }))

    # Step 3: Add technology to radar
    await ws.send(json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "add_technology",
            "arguments": {
                "title": "Kubernetes",
                "domain": "Infrastructure",
                "vendor": "CNCF",
                "status": "assess",
                "relevance": "high",
                "project_id": 1
            }
        }
    }))
```

### Pattern 3: Automated Analysis

**Use Case**: Schedule recurring repository analysis

```javascript
async function setupAutomatedAnalysis() {
  // 1. List repositories to analyze
  const repos = await mcpCall("resources/read", {
    uri: "commandcenter://repositories"
  });

  // 2. Create schedule for each repository
  for (const repo of repos) {
    await mcpCall("tools/call", {
      name: "create_schedule",
      arguments: {
        name: `Weekly Analysis - ${repo.name}`,
        frequency: "weekly",
        parameters: {
          job_type: "repository_analysis",
          repository_id: repo.id,
          depth: "comprehensive"
        },
        timezone: "UTC",
        enabled: true
      }
    });
  }

  // 3. Verify schedules created
  const schedules = await mcpCall("resources/read", {
    uri: "commandcenter://schedules/active"
  });

  console.log(`Created ${schedules.length} analysis schedules`);
}
```

### Pattern 4: Stateful Project Management

**Use Case**: Multi-step project setup with context

```python
async def setup_new_project(ws):
    # Store project context
    await ws.send(json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "context/set",
        "params": {
            "key": "setup_state",
            "value": {
                "project_id": 2,
                "technologies": ["Docker", "PostgreSQL", "FastAPI"],
                "repositories": ["backend", "frontend"],
                "step": "technologies"
            }
        }
    }))

    # Add technologies
    for tech in ["Docker", "PostgreSQL", "FastAPI"]:
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": next_id(),
            "method": "tools/call",
            "params": {
                "name": "add_technology",
                "arguments": {
                    "title": tech,
                    "domain": "Backend",
                    "status": "adopt",
                    "project_id": 2
                }
            }
        }))

    # Update context
    await ws.send(json.dumps({
        "jsonrpc": "2.0",
        "id": next_id(),
        "method": "context/set",
        "params": {
            "key": "setup_state",
            "value": {
                "project_id": 2,
                "step": "repositories"
            }
        }
    }))

    # Continue with repository setup...
```

---

## API Reference

### Endpoints

#### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/mcp/rpc` | POST | JSON-RPC endpoint (ephemeral sessions) |
| `/api/v1/mcp/health` | GET | Health check |
| `/api/v1/mcp/info` | GET | Server info and capabilities |
| `/api/v1/mcp/resources` | GET | List resources (convenience) |
| `/api/v1/mcp/tools` | GET | List tools (convenience) |
| `/api/v1/mcp/prompts` | GET | List prompts (convenience) |

#### WebSocket Endpoint

| Endpoint | Description |
|----------|-------------|
| `/api/v1/mcp/ws` | WebSocket for persistent sessions |

### JSON-RPC Methods

#### Core Methods

```
initialize              - Initialize client session
resources/list          - List available resources
resources/read          - Read resource by URI
tools/list             - List available tools
tools/call             - Execute tool
prompts/list           - List available prompts
prompts/get            - Get rendered prompt
```

#### Context Methods

```
context/set            - Set context key-value
context/get            - Get context value
context/has            - Check if key exists
context/delete         - Delete context key
context/clear          - Clear all context
context/list           - List all context
```

---

## Examples

### Complete WebSocket Session

```javascript
const WebSocket = require('ws');

async function completeWorkflow() {
  const ws = new WebSocket('ws://localhost:8000/api/v1/mcp/ws');

  ws.on('open', async () => {
    console.log('Connected to MCP server');

    // 1. Initialize
    ws.send(JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        client_info: {
          name: "WorkflowBot",
          version: "1.0.0"
        }
      }
    }));
  });

  ws.on('message', async (data) => {
    const response = JSON.parse(data);
    console.log('Received:', response);

    if (response.id === 1) {
      // 2. Set context
      ws.send(JSON.stringify({
        jsonrpc: "2.0",
        id: 2,
        method: "context/set",
        params: {
          key: "workflow_id",
          value: "tech-evaluation-001"
        }
      }));
    }

    if (response.id === 2) {
      // 3. List technologies
      ws.send(JSON.stringify({
        jsonrpc: "2.0",
        id: 3,
        method: "resources/read",
        params: {
          uri: "commandcenter://technologies"
        }
      }));
    }

    if (response.id === 3) {
      // 4. Create research task
      ws.send(JSON.stringify({
        jsonrpc: "2.0",
        id: 4,
        method: "tools/call",
        params: {
          name: "create_research_task",
          arguments: {
            title: "Evaluate New Framework",
            description: "Research and document findings",
            status: "todo",
            priority: "medium",
            project_id: 1
          }
        }
      }));
    }

    if (response.id === 4) {
      console.log('Workflow complete!');
      ws.close();
    }
  });
}

completeWorkflow();
```

### Python Client with Context

```python
import asyncio
import websockets
import json

async def stateful_analysis():
    uri = "ws://localhost:8000/api/v1/mcp/ws"

    async with websockets.connect(uri) as ws:
        # Initialize
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "client_info": {
                    "name": "AnalysisBot",
                    "version": "2.0.0"
                }
            }
        }))

        response = await ws.recv()
        print(f"Initialized: {json.loads(response)}")

        # Set analysis context
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "context/set",
            "params": {
                "key": "analysis_phase",
                "value": {
                    "phase": "discovery",
                    "started_at": "2025-10-12T10:00:00Z",
                    "items_analyzed": 0
                }
            }
        }))

        await ws.recv()

        # Get repositories
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/read",
            "params": {
                "uri": "commandcenter://repositories"
            }
        }))

        repos_response = await ws.recv()
        repos = json.loads(repos_response)["result"]

        # Update context with progress
        for i, repo in enumerate(repos):
            await ws.send(json.dumps({
                "jsonrpc": "2.0",
                "id": 100 + i,
                "method": "context/set",
                "params": {
                    "key": "analysis_phase",
                    "value": {
                        "phase": "analyzing",
                        "current_repo": repo["name"],
                        "items_analyzed": i + 1,
                        "total_items": len(repos)
                    }
                }
            }))

            await ws.recv()

        # Retrieve final context
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 999,
            "method": "context/list",
            "params": {}
        }))

        final_context = await ws.recv()
        print(f"Final context: {json.loads(final_context)}")

asyncio.run(stateful_analysis())
```

---

## Best Practices

### 1. Session Management

**Do**:
- Use WebSocket for stateful workflows
- Use HTTP for one-off queries
- Always call `initialize` for new sessions
- Close sessions when done

**Don't**:
- Share sessions across users
- Keep sessions open indefinitely
- Store sensitive data in context without encryption

### 2. Error Handling

```javascript
ws.on('message', (data) => {
  const response = JSON.parse(data);

  if (response.error) {
    console.error('MCP Error:', response.error.code, response.error.message);

    switch (response.error.code) {
      case -32002:
        // Session not initialized
        sendInitialize();
        break;
      case -32601:
        // Method not found
        console.error('Unsupported method');
        break;
      case -32602:
        // Invalid params
        console.error('Check parameters');
        break;
      default:
        console.error('Unknown error');
    }
  }
});
```

### 3. Context Usage

**Recommended Context Keys**:
```javascript
// User preferences
"user:preferences"
"user:timezone"
"user:notification_settings"

// Workflow state
"workflow:current_step"
"workflow:started_at"
"workflow:data"

// Cache
"cache:projects"
"cache:last_refresh"

// Temporary
"temp:selection"
"temp:draft"
```

### 4. Performance

**Tips**:
- Batch related requests in single session
- Use context to cache frequently accessed data
- Close sessions promptly to free resources
- Monitor session count via `/api/v1/mcp/info`

### 5. Security

**Recommendations**:
- Validate all tool parameters
- Sanitize context values
- Implement rate limiting
- Use HTTPS/WSS in production
- Implement authentication middleware

---

## Troubleshooting

### Issue: "Session not initialized"

**Error**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32002,
    "message": "Session not initialized"
  }
}
```

**Solution**: Always call `initialize` after connecting:
```javascript
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    client_info: {name: "MyClient", version: "1.0.0"}
  }
}));
```

### Issue: Context not persisting

**Problem**: Context disappears between requests

**Causes**:
1. Using HTTP (ephemeral sessions)
2. Session timeout
3. Server restart

**Solution**:
- Use WebSocket for stateful sessions
- Check session timeout settings
- Implement context persistence if needed

### Issue: "Method not found"

**Error**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found: xyz"
  }
}
```

**Solution**: Check method name spelling and server capabilities:
```bash
curl http://localhost:8000/api/v1/mcp/info
```

### Issue: Resource not found

**Error**: Resource URI doesn't exist

**Solution**: List available resources first:
```javascript
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: 1,
  method: "resources/list",
  params: {}
}));
```

### Issue: Database connection errors

**Problem**: Provider can't access database

**Solution**: Check database service and migrations:
```bash
docker-compose ps postgres
docker-compose exec backend alembic current
```

### Debugging

**Enable debug logging**:
```python
import logging
logging.getLogger("app.mcp").setLevel(logging.DEBUG)
```

**Monitor sessions**:
```bash
curl http://localhost:8000/api/v1/mcp/info | jq '.stats'
```

**Check server health**:
```bash
curl http://localhost:8000/api/v1/mcp/health
```

---

## Additional Resources

### Documentation
- [MCP Protocol Specification](https://modelcontextprotocol.io/docs)
- [CommandCenter API Docs](http://localhost:8000/docs)
- [SCHEDULING.md](./SCHEDULING.md) - Scheduling system details
- [WEBHOOKS.md](./WEBHOOKS.md) - Webhook integration

### Code References
- **MCP Server**: `backend/app/mcp/server.py`
- **Resource Provider**: `backend/app/mcp/providers/commandcenter_resources.py`
- **Tool Provider**: `backend/app/mcp/providers/commandcenter_tools.py`
- **Prompt Provider**: `backend/app/mcp/providers/commandcenter_prompts.py`
- **Connection Manager**: `backend/app/mcp/connection.py`

### Testing
```bash
# Run MCP tests
docker-compose exec backend pytest backend/tests/test_mcp/

# Test WebSocket connection
wscat -c ws://localhost:8000/api/v1/mcp/ws

# Test HTTP endpoint
curl -X POST http://localhost:8000/api/v1/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

---

**Last Updated**: 2025-10-12
**Version**: 1.0.0
**Author**: CommandCenter Development Team
