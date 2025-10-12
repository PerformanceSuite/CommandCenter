# Agent 7: Documentation & Examples

**Agent Name**: docs-and-examples
**Phase**: 3 (UI/UX & Integration)
**Branch**: agent/docs-and-examples
**Duration**: 6-8 hours
**Dependencies**: All agents 1-6

---

## Mission

Create comprehensive documentation and examples for the MCP architecture, enabling users and developers to understand, configure, and extend CommandCenter's MCP capabilities. This includes architecture docs, CLI guides, API references, example workflows, troubleshooting guides, and a video demo script.

You are the educator and evangelist for the MCP architecture, making it accessible to all users.

---

## Deliverables

### 1. MCP Architecture Documentation (`docs/MCP_ARCHITECTURE.md`)
- **Overview**: What is MCP and why CommandCenter uses it
- **Architecture Diagram**: Visual representation of MCP components
- **Core Concepts**: Resources, Tools, Prompts, Servers, Providers
- **Server Registry**: How servers are discovered and registered
- **Protocol Specification**: JSON-RPC 2.0 implementation details
- **Extension Guide**: How to create custom MCP servers
- **Security Considerations**: Authentication, authorization, data isolation

### 2. CLI Usage Guide (`docs/CLI_GUIDE.md`)
- **Installation**: How to install and setup CLI
- **Configuration**: Config file format and options (`~/.commandcenter/config.yaml`)
- **Commands Reference**:
  - `commandcenter analyze <path>` - Analyze project
  - `commandcenter launch-agents <project-id>` - Launch research agents
  - `commandcenter workflow list` - List workflows
  - `commandcenter workflow status <id>` - Check workflow status
  - `commandcenter mcp list-servers` - List MCP servers
  - `commandcenter mcp query-resource <uri>` - Query MCP resource
- **Examples**: Common usage patterns with expected output
- **Troubleshooting**: Common errors and solutions

### 3. API Documentation (`docs/API_REFERENCE.md`)
- **MCP Endpoints**:
  - `GET /api/v1/mcp/servers` - List MCP servers
  - `POST /api/v1/mcp/servers/{name}/resources` - Query resources
  - `POST /api/v1/mcp/servers/{name}/tools/{tool}` - Execute tool
  - `GET /api/v1/mcp/servers/{name}/prompts` - List prompts
- **Workflow Endpoints**:
  - `POST /api/v1/workflows` - Create workflow
  - `POST /api/v1/workflows/{id}/execute` - Execute workflow
  - `GET /api/v1/workflows/{id}` - Get workflow status
  - `GET /api/v1/workflows/{id}/results` - Get results
  - `WS /api/v1/workflows/{id}/stream` - Stream updates
- **Request/Response Examples**: Complete examples with curl
- **Error Codes**: All possible error responses
- **Rate Limiting**: API limits and best practices

### 4. Example Workflows (`docs/examples/`)
- **Example 1: React Project Analysis** (`react-project-analysis.md`)
  - Full walkthrough: analyze React project → generate workflow → execute agents
  - Expected technologies detected
  - Sample research gaps
  - Complete agent outputs
- **Example 2: Python FastAPI Analysis** (`python-fastapi-analysis.md`)
  - Security-focused analysis workflow
  - Dependency audit example
  - Performance optimization recommendations
- **Example 3: Multi-language Monorepo** (`monorepo-analysis.md`)
  - Handling multiple tech stacks in one project
  - Technology comparison across services
  - Architecture recommendations
- **Example 4: Custom Research Workflow** (`custom-workflow.md`)
  - How to create custom workflows via API
  - Manually specify tasks and dependencies
  - Custom prompt templates

### 5. Integration Guide (`docs/INTEGRATION_GUIDE.md`)
- **Integrating with External Tools**:
  - Claude Desktop integration
  - VS Code extension configuration
  - CI/CD integration (GitHub Actions, GitLab CI)
- **Webhook Configuration**: Trigger analysis on git push
- **Custom MCP Clients**: Building your own MCP client
- **Provider Extensions**: Adding new AI model providers

### 6. Troubleshooting Guide (`docs/TROUBLESHOOTING.md`)
- **Common Issues**:
  - MCP server not starting
  - Workflow stuck in "running" status
  - API authentication errors
  - WebSocket connection failures
  - Agent execution timeouts
- **Debugging Tips**:
  - Enabling debug logs
  - Inspecting MCP protocol messages
  - Testing individual tools via CLI
  - Monitoring database for workflow state
- **Performance Tuning**:
  - Optimal concurrency settings
  - Database query optimization
  - Caching strategies
- **Error Reference**: Complete error code documentation

### 7. Configuration Reference (`docs/CONFIGURATION_REFERENCE.md`)
- **Environment Variables**: All MCP-related env vars
- **MCP Server Configuration**: Server-specific settings
- **Model Provider Config**: API keys, endpoints, model selection
- **Workflow Defaults**: Default concurrency, timeouts, retry logic
- **Frontend Config**: WebSocket URLs, polling intervals
- **Security Settings**: CORS, authentication, encryption

### 8. Video Demo Script (`docs/VIDEO_DEMO_SCRIPT.md`)
- **Scene 1: Introduction** (30 seconds)
  - What is CommandCenter MCP
  - Use case: Automated project analysis
- **Scene 2: CLI Demo** (2 minutes)
  - Analyze a project: `commandcenter analyze ~/Projects/my-app`
  - Show detected technologies and research gaps
  - Generate and execute workflow
- **Scene 3: UI Demo** (3 minutes)
  - Navigate to Project Analysis Dashboard
  - Trigger analysis via UI
  - View real-time workflow execution
  - Explore dependency graph
  - View agent results
- **Scene 4: MCP Configuration** (1 minute)
  - Show MCP Server List
  - Browse available resources
  - Execute a tool via UI
- **Scene 5: Results & Export** (1 minute)
  - View aggregated results
  - Export as PDF
  - Share link generation
- **Scene 6: Conclusion** (30 seconds)
  - Summary of capabilities
  - Call to action (GitHub repo, docs link)

---

## Technical Specifications

### Documentation Structure

```
docs/
├── MCP_ARCHITECTURE.md          # Core architecture
├── CLI_GUIDE.md                 # CLI usage
├── API_REFERENCE.md             # API documentation
├── INTEGRATION_GUIDE.md         # Integration patterns
├── TROUBLESHOOTING.md           # Debugging help
├── CONFIGURATION_REFERENCE.md   # Config options
├── VIDEO_DEMO_SCRIPT.md         # Demo script
├── examples/
│   ├── react-project-analysis.md
│   ├── python-fastapi-analysis.md
│   ├── monorepo-analysis.md
│   └── custom-workflow.md
└── diagrams/
    ├── mcp-architecture.png
    ├── workflow-execution.png
    └── dependency-graph-example.png
```

### Documentation Standards

- **Format**: Markdown with GitHub-flavored syntax
- **Code Blocks**: Always specify language for syntax highlighting
- **Links**: Use relative links for internal docs
- **Images**: Store in `docs/diagrams/`, reference with relative paths
- **Version**: Include "Last Updated" timestamp at top
- **Audience**: Write for both users and developers

---

## Implementation Guidelines

### 1. MCP Architecture Documentation Template

```markdown
# MCP Architecture

**Last Updated**: 2025-10-11

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Core Concepts](#core-concepts)
- [Protocol Specification](#protocol-specification)
- [Security](#security)

## Overview

CommandCenter implements the Model Context Protocol (MCP) to expose project analysis and research orchestration capabilities to AI assistants and external tools. MCP is a standardized protocol (similar to Language Server Protocol) that allows AI applications to safely interact with local and remote data sources.

### Why MCP?

- **Standardization**: Industry-standard protocol for AI tool integration
- **Security**: Controlled access to sensitive project data
- **Extensibility**: Easy to add new capabilities without breaking changes
- **Interoperability**: Works with Claude Desktop, VS Code, and custom clients

## Architecture

![MCP Architecture Diagram](diagrams/mcp-architecture.png)

CommandCenter exposes two MCP servers:

1. **Project Manager Server**: Project analysis and task management
2. **Research Orchestrator Server**: Automated research workflow orchestration

Each server implements the MCP protocol (JSON-RPC 2.0) and exposes:
- **Resources**: Read-only data (projects, analysis results)
- **Tools**: Executable functions (analyze project, execute workflow)
- **Prompts**: Template prompts for AI assistants

## Core Concepts

### Resources

Resources are read-only data exposed via URI schemes:

```
project://1                    # Project details
project://1/technologies       # Technologies in project
analysis://1                   # Latest analysis results
workflow://abc-123             # Workflow details
```

### Tools

Tools are executable functions with typed inputs/outputs:

```json
{
  "name": "analyze_project",
  "description": "Analyze a project directory",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_path": { "type": "string" },
      "force_rescan": { "type": "boolean" }
    },
    "required": ["project_path"]
  }
}
```

### Prompts

Prompts are reusable templates for AI interactions:

```json
{
  "name": "project_analysis_template",
  "description": "Template for project analysis",
  "arguments": [
    { "name": "project_name", "required": true },
    { "name": "technologies", "required": true }
  ]
}
```

## Protocol Specification

CommandCenter implements MCP over stdio and HTTP transports.

### Request Format (JSON-RPC 2.0)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {}
}
```

### Response Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resources": [
      {
        "uri": "project://1",
        "name": "my-project",
        "description": "Project details",
        "mimeType": "application/json"
      }
    ]
  }
}
```

### Error Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request"
  }
}
```

## Security

### Authentication

MCP servers require authentication via:
1. **API Key**: Passed in `Authorization` header
2. **Session Token**: For web UI access

### Authorization

Fine-grained permissions per resource/tool:
- **Read**: Access to resources (projects, analysis results)
- **Execute**: Ability to run tools (analyze, execute workflows)
- **Admin**: Server configuration and management

### Data Isolation

Each project is isolated:
- Separate database records
- Unique workflow execution contexts
- No cross-project data leakage

See `DATA_ISOLATION.md` for complete isolation architecture.
```

### 2. CLI Guide Template

```markdown
# CLI Usage Guide

**Last Updated**: 2025-10-11

## Installation

```bash
cd backend
pip install -e .  # Install CLI in development mode

# Verify installation
commandcenter --version
```

## Configuration

Create config file at `~/.commandcenter/config.yaml`:

```yaml
# CommandCenter CLI Configuration

# API connection
api:
  url: http://localhost:8000
  api_key: your-api-key-here

# Default settings
defaults:
  max_concurrent_agents: 3
  workflow_timeout: 3600  # seconds
  analysis_cache_ttl: 86400  # 24 hours

# Model providers
providers:
  anthropic:
    api_key: sk-ant-...
    default_model: claude-3-5-sonnet-20241022
  openai:
    api_key: sk-...
    default_model: gpt-4-turbo
```

## Commands

### `commandcenter analyze`

Analyze a project directory and detect technologies.

**Usage**:
```bash
commandcenter analyze <project-path> [options]

Options:
  --force-rescan      Force re-analysis even if cached
  --output=FORMAT     Output format: json|table|summary (default: table)
  --launch-agents     Auto-launch research agents after analysis
  --priority=LEVEL    Filter by priority: high|medium|low
```

**Example**:
```bash
$ commandcenter analyze ~/Projects/my-react-app --launch-agents

🔍 Analyzing project: my-react-app
✓ Scanning directory structure... (1.2s)
✓ Detecting technologies... (0.8s)
✓ Analyzing dependencies... (2.1s)
✓ Identifying research gaps... (1.5s)

📊 Analysis Results:
┌─────────────────┬───────┐
│ Technology      │ Count │
├─────────────────┼───────┤
│ React           │ 18.x  │
│ TypeScript      │ 5.x   │
│ Vite            │ 4.x   │
│ TailwindCSS     │ 3.x   │
└─────────────────┴───────┘

🔬 Research Gaps Identified: 5
  1. [HIGH] Security audit for React dependencies
  2. [HIGH] Performance optimization for large lists
  3. [MEDIUM] Accessibility compliance review
  4. [MEDIUM] Compare TailwindCSS vs alternatives
  5. [LOW] Documentation generation

🚀 Launching research agents...
  ✓ Workflow created: wf-abc-123
  ✓ 5 agents queued (3 concurrent)
  ⏳ Agent 1/5 running: Security audit...

View progress: http://localhost:3000/workflows/wf-abc-123
```

### `commandcenter workflow`

Manage research workflows.

**Subcommands**:
```bash
commandcenter workflow list                    # List all workflows
commandcenter workflow status <workflow-id>    # Check workflow status
commandcenter workflow cancel <workflow-id>    # Cancel running workflow
commandcenter workflow results <workflow-id>   # View results
```

**Example**:
```bash
$ commandcenter workflow status wf-abc-123

📋 Workflow: wf-abc-123
   Project: my-react-app
   Status: RUNNING
   Progress: 3/5 tasks completed (60%)

Tasks:
  ✓ Security audit (completed, 45s)
  ✓ Performance optimization (completed, 62s)
  ✓ Accessibility review (completed, 38s)
  ⏳ Technology comparison (running, 15s elapsed)
  ⏸  Documentation generation (pending)

Estimated completion: 2 minutes
```

### `commandcenter mcp`

Interact with MCP servers.

**Subcommands**:
```bash
commandcenter mcp list-servers               # List available MCP servers
commandcenter mcp list-resources <server>    # List resources from server
commandcenter mcp query-resource <uri>       # Query specific resource
commandcenter mcp call-tool <server> <tool>  # Execute a tool
```

**Example**:
```bash
$ commandcenter mcp list-servers

MCP Servers:
  ✓ project-manager (v1.0.0) - Project analysis and management
  ✓ research-orchestrator (v1.0.0) - Research workflow orchestration

$ commandcenter mcp list-resources project-manager

Resources:
  • projects://list - All projects
  • project://{id} - Project details
  • project://{id}/technologies - Technologies in project
  • analysis://{id} - Analysis results

$ commandcenter mcp query-resource project://1

{
  "id": 1,
  "name": "my-react-app",
  "owner": "user",
  "technologies": ["React", "TypeScript"],
  "last_analyzed": "2025-10-11T14:30:00Z"
}
```

## Troubleshooting

### Error: "API connection failed"

**Solution**: Check that backend is running:
```bash
cd backend
docker-compose up
```

Verify API URL in config: `~/.commandcenter/config.yaml`

### Error: "Project analysis failed"

**Solution**: Ensure project path is correct and accessible:
```bash
ls -la ~/Projects/my-app  # Verify path exists
```

Check logs:
```bash
commandcenter --debug analyze ~/Projects/my-app
```
```

### 3. Example Workflow Template (`examples/react-project-analysis.md`)

```markdown
# Example: React Project Analysis

This example demonstrates a complete project analysis workflow for a React application.

## Project Structure

```
my-react-app/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   └── App.tsx
└── tests/
```

## Step 1: Analyze Project

```bash
commandcenter analyze ~/Projects/my-react-app --output=json > analysis.json
```

**Output** (`analysis.json`):
```json
{
  "project_id": 42,
  "name": "my-react-app",
  "technologies": [
    {
      "title": "React",
      "version": "18.2.0",
      "domain": "Frontend",
      "status": "adopt"
    },
    {
      "title": "TypeScript",
      "version": "5.2.0",
      "domain": "Language",
      "status": "adopt"
    },
    {
      "title": "Vite",
      "version": "4.5.0",
      "domain": "Build Tools",
      "status": "trial"
    }
  ],
  "research_gaps": [
    {
      "id": 1,
      "title": "React 18 Concurrent Features Review",
      "description": "Analyze usage of React 18 concurrent features",
      "priority": "high"
    },
    {
      "id": 2,
      "title": "TypeScript Strict Mode Compliance",
      "description": "Check TypeScript strict mode compliance",
      "priority": "medium"
    }
  ]
}
```

## Step 2: Generate Workflow

```bash
commandcenter workflow create --project=42 --output=json > workflow.json
```

**Output** (`workflow.json`):
```json
{
  "workflow_id": "wf-react-001",
  "project_id": 42,
  "tasks": [
    {
      "id": "task-1",
      "type": "security_analysis",
      "title": "React Dependency Security Audit",
      "model": "claude-3-5-sonnet-20241022",
      "provider": "anthropic",
      "priority": 100,
      "dependencies": []
    },
    {
      "id": "task-2",
      "type": "performance_review",
      "title": "React Performance Optimization",
      "model": "claude-3-5-sonnet-20241022",
      "provider": "anthropic",
      "priority": 50,
      "dependencies": ["task-1"]
    }
  ],
  "max_concurrent": 3
}
```

## Step 3: Execute Workflow

```bash
commandcenter workflow execute wf-react-001 --follow
```

**Output** (streaming):
```
⏳ Executing workflow: wf-react-001
✓ Task 1/2 started: React Dependency Security Audit
  Model: Claude 3.5 Sonnet
  Analyzing package.json dependencies...
  ✓ Completed in 45s

  Findings:
  • 2 HIGH severity vulnerabilities found
  • 5 MEDIUM severity vulnerabilities found
  • Recommendations: Update react-router-dom to v6.20+

✓ Task 2/2 started: React Performance Optimization
  Model: Claude 3.5 Sonnet
  Analyzing component render patterns...
  ✓ Completed in 62s

  Findings:
  • Identified 3 unnecessary re-renders in ProductList
  • Bundle size can be reduced by 30% with code splitting
  • Recommendations: Implement React.memo for expensive components

✅ Workflow complete!
   Total time: 2m 15s
   Tasks completed: 2/2
   Total cost: $0.42

View results: http://localhost:3000/workflows/wf-react-001
```

## Step 4: View Results

Navigate to `http://localhost:3000/workflows/wf-react-001` to view:
- Aggregated results from all agents
- Dependency graph visualization
- Detailed recommendations
- Export options (PDF, Markdown)

## Expected Outcomes

After completing this workflow, you will have:
1. ✅ Complete security audit of React dependencies
2. ✅ Performance optimization recommendations
3. ✅ Actionable tasks to improve code quality
4. ✅ Detailed report exportable as PDF

## Next Steps

- Implement recommended security updates
- Apply performance optimizations
- Re-run analysis to verify improvements
```

---

## Testing Strategy

### Documentation Quality Tests

```bash
# Test all markdown files for broken links
npm install -g markdown-link-check
find docs -name "*.md" -exec markdown-link-check {} \;

# Test code examples execute correctly
cd docs/examples
./test-examples.sh  # Custom script to verify examples work
```

### Example Validation

```python
# tests/test_examples.py
import subprocess
import json

def test_react_example_analysis():
    """Verify React example produces expected output"""
    result = subprocess.run(
        ["commandcenter", "analyze", "tests/fixtures/react-app", "--output=json"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)

    # Verify expected technologies detected
    tech_names = [t["title"] for t in data["technologies"]]
    assert "React" in tech_names
    assert "TypeScript" in tech_names

def test_workflow_example():
    """Verify workflow example completes successfully"""
    # Test workflow generation and execution
    # ...
```

---

## Success Criteria

- ✅ All 8 deliverables complete
- ✅ Documentation covers all MCP features
- ✅ CLI guide with complete command reference
- ✅ API reference with curl examples
- ✅ 4+ example workflows (React, Python, monorepo, custom)
- ✅ Troubleshooting guide with common issues
- ✅ Configuration reference complete
- ✅ Video demo script ready for recording
- ✅ All links verified (no broken links)
- ✅ All code examples tested and working
- ✅ Diagrams created and referenced correctly
- ✅ Self-review score: 10/10

---

## Self-Review Checklist

Before marking PR as ready:
- [ ] All 8 deliverables complete
- [ ] Markdown linting passed
- [ ] All internal links verified
- [ ] All code examples tested
- [ ] Diagrams created (use draw.io or similar)
- [ ] Video demo script reviewed
- [ ] No spelling/grammar errors
- [ ] Consistent formatting throughout
- [ ] Table of contents in all major docs
- [ ] "Last Updated" timestamps added
- [ ] Self-review score: 10/10
