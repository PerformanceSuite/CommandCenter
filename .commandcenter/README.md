# CommandCenter MCP Infrastructure

This directory contains the Model Context Protocol (MCP) infrastructure for CommandCenter.

## Overview

CommandCenter uses MCP servers to provide AI-powered project management, knowledge base access, and multi-agent coordination through a standardized protocol. This enables cross-IDE support and multi-provider AI routing.

## Directory Structure

```
.commandcenter/
├── config.json                    # Main configuration
├── config.schema.json             # Configuration schema
├── mcp-servers/                   # MCP server implementations
│   ├── base/                      # Base MCP server template
│   │   ├── server.py             # BaseMCPServer class
│   │   ├── protocol.py           # MCP protocol handler
│   │   ├── transport.py          # Stdio transport
│   │   ├── registry.py           # Tool/resource registry
│   │   ├── utils.py              # Utilities
│   │   └── config_validator.py   # Config validation
│   └── project-manager/          # Project Manager MCP server
│       ├── server.py             # Main server
│       ├── config.py             # Server config
│       ├── tools/                # Tool implementations
│       │   ├── workflow.py       # Workflow coordination
│       │   ├── agent.py          # Agent spawning
│       │   ├── git.py            # Git operations
│       │   ├── analysis.py       # Project analysis
│       │   └── progress.py       # Progress tracking
│       └── resources/            # Resource providers
│           ├── project_state.py  # Project state
│           └── workflows.py      # Workflow templates
├── .agent-coordination/          # Agent coordination system
│   ├── status.json              # Agent status tracking
│   ├── dependencies.json        # Agent dependencies
│   ├── merge-queue.json         # PR merge queue
│   ├── tasks/                   # Agent task definitions
│   └── workflows/               # Workflow templates
└── prompts/                      # Prompt templates
    └── commands/                 # Command templates
```

## MCP Servers

### 1. Project Manager (project-manager)

Main orchestration server for CommandCenter.

**Tools:**
- `analyze_project` - Analyze project structure and technologies
- `create_workflow` - Create agent workflows
- `spawn_agent` - Launch agents in worktrees
- `track_progress` - Monitor agent progress
- `merge_results` - Merge agent branches
- `generate_command` - Generate CLI commands

**Resources:**
- `project://state` - Current project state
- `project://workflows` - Available workflows
- `project://agents` - Active agents status

**Transport:** stdio (default)

### 2. KnowledgeBeast (knowledgebeast)

RAG-powered knowledge base with per-project isolation.

**Tools:** (to be implemented by knowledgebeast-mcp-agent)
- `ingest_documents` - Ingest documents
- `search_knowledge` - Semantic search
- `get_statistics` - Knowledge base stats

**Transport:** stdio

### 3. AgentFlow Coordinator (agentflow)

Multi-agent workflow coordination.

**Tools:** (to be implemented by agentflow-coordinator-agent)
- `coordinate_agents` - Coordinate agent execution
- `resolve_conflicts` - Resolve merge conflicts
- `review_agent` - Review agent work

**Transport:** stdio

### 4. VIZTRTR (viztrtr)

UI/UX analysis server (headless mode).

**Tools:** (to be implemented by viztrtr-mcp-agent)
- `analyze_ui` - Analyze UI components
- `score_ux` - Score user experience

**Transport:** stdio

### 5. API Keys Manager (api_keys)

Multi-provider AI routing and key management.

**Tools:** (to be implemented by api-manager-agent)
- `route_request` - Route AI requests
- `manage_keys` - Manage API keys
- `track_usage` - Track API usage

**Transport:** stdio

## Configuration

Configuration is stored in `config.json`. Edit using:

```bash
# Show configuration
/mcp-config

# Edit configuration
/mcp-config edit <key> <value>

# Validate configuration
/mcp-config validate
```

### Key Configuration Sections

- **project**: Project metadata and isolation settings
- **mcp_servers**: Server enable/disable and transport settings
- **ai_providers**: AI provider routing and model selection
- **workflows**: Workflow templates and execution settings
- **git**: Git configuration for worktrees
- **security**: Security settings
- **logging**: Logging configuration

## Slash Commands

CommandCenter provides slash commands for IDE integration:

- `/init-commandcenter` - Initialize MCP infrastructure
- `/start-workflow <type>` - Start agent workflow
- `/agent-status` - Show agent status
- `/mcp-config` - Manage configuration

## Getting Started

### Initialize CommandCenter

```bash
/init-commandcenter
```

This will:
1. Analyze your project
2. Create `.commandcenter/` structure
3. Generate project-specific config
4. Set up agent coordination

### Start a Workflow

```bash
# Start parallel improvement workflow
/start-workflow parallel-improvement

# Start MCP development workflow
/start-workflow phased mcp-infrastructure knowledgebeast api-manager
```

### Monitor Progress

```bash
/agent-status
```

## Development

### Running MCP Servers

Each MCP server can be run independently:

```bash
# Run Project Manager server
cd .commandcenter/mcp-servers/project-manager
python server.py
```

### Adding Custom Tools

1. Create tool implementation in `tools/`
2. Register tool in server's `_register_tools()` method
3. Add tool parameters using `ToolParameter`
4. Implement async handler function

Example:

```python
self.tool_registry.register_tool(
    name='my_tool',
    description='My custom tool',
    parameters=[
        ToolParameter(
            name='input',
            type='string',
            description='Input parameter',
            required=True
        )
    ],
    handler=self.my_tool_handler
)

async def my_tool_handler(self, input: str) -> dict:
    # Tool implementation
    return {'result': input.upper()}
```

### Adding Custom Resources

1. Create resource provider in `resources/`
2. Register resource in server's `_register_resources()` method
3. Implement async handler function

Example:

```python
self.resource_registry.register_resource(
    uri='myproject://resource',
    name='My Resource',
    description='Custom resource',
    mime_type='application/json',
    handler=self.get_my_resource
)

async def get_my_resource(self) -> str:
    import json
    data = {'key': 'value'}
    return json.dumps(data)
```

## Architecture

### MCP Protocol

CommandCenter MCP servers implement JSON-RPC 2.0 over stdio transport:

- **Request:** `{"jsonrpc": "2.0", "method": "tools/call", "params": {...}, "id": 1}`
- **Response:** `{"jsonrpc": "2.0", "result": {...}, "id": 1}`

### Tool Invocation Flow

1. Client sends `tools/call` request with tool name and arguments
2. Server routes to tool handler via registry
3. Tool executes and returns result
4. Server sends response back to client

### Resource Access Flow

1. Client sends `resources/read` request with URI
2. Server routes to resource handler via registry
3. Resource handler fetches data
4. Server sends resource content back to client

## Testing

Tests are located in `tests/mcp/`:

```bash
# Run all MCP tests
pytest tests/mcp/

# Run specific test file
pytest tests/mcp/test_base_server.py

# Run with coverage
pytest tests/mcp/ --cov=.commandcenter
```

## Security

- All MCP servers run in isolated processes
- Stdio transport prevents network exposure
- Tool execution is sandboxed
- Configuration validation prevents injection
- API keys are encrypted at rest

## Troubleshooting

### Server won't start

1. Check configuration: `/mcp-config validate`
2. Check logs: stderr output
3. Verify Python dependencies installed
4. Check file permissions

### Tool not found

1. Verify tool is registered in server
2. Check tool name spelling
3. Verify server is initialized
4. Check server capabilities

### Resource not found

1. Verify resource URI is correct
2. Check resource is registered
3. Verify resource handler implemented
4. Check resource handler doesn't throw errors

## Contributing

When adding new MCP servers or tools:

1. Follow existing code patterns
2. Add comprehensive docstrings
3. Write unit and integration tests
4. Update this README
5. Validate configuration schema
6. Test with multiple clients

## License

Same as CommandCenter project.
