# MCP (Model Context Protocol) Architecture

## Overview

The Model Context Protocol (MCP) enables CommandCenter to expose its capabilities (resources, tools, and prompts) to AI assistants and other intelligent systems. This document describes the MCP implementation architecture in CommandCenter.

## What is MCP?

MCP is a standardized protocol that allows AI applications to access external data sources and tools. It follows a JSON-RPC 2.0 message format and provides three main types of capabilities:

- **Resources**: Read-only data that can be accessed by AI assistants (projects, technologies, research tasks)
- **Tools**: Callable functions that can perform actions (create tasks, analyze projects)
- **Prompts**: Template messages that guide AI assistant behavior

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        MCP Client                            │
│                    (AI Assistant/IDE)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ JSON-RPC 2.0
                            │ (stdio/HTTP/WebSocket)
┌───────────────────────────▼─────────────────────────────────┐
│                      Transport Layer                         │
│                   (StdioTransport, etc.)                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      MCPServer (Base)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           MCPProtocolHandler                        │   │
│  │      (JSON-RPC parsing & validation)                │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         MCPConnectionManager                        │   │
│  │      (Session & request routing)                    │   │
│  └─────────────────────────────────────────────────────┘   │
└──────┬───────────────────┬──────────────────┬───────────────┘
       │                   │                  │
┌──────▼──────┐    ┌──────▼──────┐   ┌──────▼──────┐
│  Resource   │    │    Tool     │   │   Prompt    │
│  Providers  │    │  Providers  │   │  Providers  │
└──────┬──────┘    └──────┬──────┘   └──────┬──────┘
       │                   │                  │
┌──────▼──────────────────▼──────────────────▼───────────────┐
│              CommandCenter Services                         │
│    (GitHubService, ResearchService, RAGService, etc.)      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Protocol Handler (`app/mcp/protocol.py`)

Handles JSON-RPC 2.0 message parsing and validation.

**Key Classes**:
- `JSONRPCRequest`: Request model with validation
- `JSONRPCResponse`: Response model
- `JSONRPCError`: Error object
- `MCPProtocolHandler`: Parse/serialize messages, handle exceptions

**Example**:
```python
from app.mcp.protocol import MCPProtocolHandler

handler = MCPProtocolHandler()

# Parse incoming request
request = await handler.parse_request(raw_json)

# Create success response
response = handler.create_response(request.id, {"data": "value"})

# Create error response
error_response = handler.create_error_response(
    request.id, -32600, "Invalid Request"
)
```

### 2. Server (`app/mcp/server.py`)

Base server class that coordinates all MCP functionality.

**Key Methods**:
- `initialize()`: Initialize server and providers
- `start()`: Start accepting connections
- `shutdown()`: Cleanup resources
- `register_resource_provider()`: Add resource provider
- `register_tool_provider()`: Add tool provider
- `register_prompt_provider()`: Add prompt provider

**Example**:
```python
from app.mcp import MCPServer
from app.mcp.config import MCPServerConfig, MCPServerInfo

config = MCPServerConfig(
    server_info=MCPServerInfo(
        name="commandcenter-mcp",
        version="1.0.0"
    )
)

server = MCPServer(config)

# Register providers
server.register_resource_provider(ProjectResourceProvider())
server.register_tool_provider(ResearchToolProvider())

# Start server
await server.initialize()
await server.start()
```

### 3. Connection Manager (`app/mcp/connection.py`)

Manages client sessions and routes requests to handlers.

**Key Classes**:
- `MCPSession`: Represents a client session
- `MCPConnectionManager`: Manages multiple sessions

**Features**:
- Session lifecycle management
- Request routing
- Session timeout handling
- Concurrent connection support

### 4. Providers (`app/mcp/providers/`)

Provider interfaces define how to expose CommandCenter capabilities.

#### Resource Provider

Exposes read-only data from CommandCenter.

```python
from app.mcp.providers.base import Resource, ResourceContent, ResourceProvider

class ProjectResourceProvider(ResourceProvider):
    def __init__(self, db: AsyncSession):
        super().__init__("projects")
        self.db = db

    async def list_resources(self):
        # Return list of available resources
        return [
            Resource(
                uri="commandcenter://projects",
                name="Projects",
                description="List of all projects"
            )
        ]

    async def read_resource(self, uri: str):
        # Return resource content
        if uri == "commandcenter://projects":
            projects = await self.get_projects()
            return ResourceContent(
                uri=uri,
                mime_type="application/json",
                text=json.dumps(projects)
            )
        raise ResourceNotFoundError(uri)
```

#### Tool Provider

Exposes callable functions that perform actions.

```python
from app.mcp.providers.base import Tool, ToolParameter, ToolProvider, ToolResult

class ResearchToolProvider(ToolProvider):
    def __init__(self, research_service: ResearchService):
        super().__init__("research")
        self.research_service = research_service

    async def list_tools(self):
        return [
            Tool(
                name="create_task",
                description="Create a new research task",
                parameters=[
                    ToolParameter(
                        name="title",
                        type="string",
                        required=True
                    )
                ]
            )
        ]

    async def call_tool(self, name: str, arguments: dict):
        if name == "create_task":
            task = await self.research_service.create_task(
                arguments["title"]
            )
            return ToolResult(
                success=True,
                result={"task_id": task.id}
            )
        raise ToolNotFoundError(name)
```

#### Prompt Provider

Exposes prompt templates for AI assistants.

```python
from app.mcp.providers.base import (
    Prompt,
    PromptProvider,
    PromptResult,
    PromptMessage
)

class AnalysisPromptProvider(PromptProvider):
    def __init__(self):
        super().__init__("analysis")

    async def list_prompts(self):
        return [
            Prompt(
                name="research_analysis",
                description="Analyze research findings"
            )
        ]

    async def get_prompt(self, name: str, arguments: dict = None):
        if name == "research_analysis":
            return PromptResult(
                messages=[
                    PromptMessage(
                        role="system",
                        content="You are a research analyst."
                    ),
                    PromptMessage(
                        role="user",
                        content="Analyze the research data."
                    )
                ]
            )
        raise PromptNotFoundError(name)
```

### 5. Configuration (`app/mcp/config.py`)

Server configuration and capability management.

**Key Classes**:
- `MCPServerConfig`: Server configuration
- `MCPCapabilities`: What the server supports
- `MCPServerInfo`: Server metadata
- `MCPServerRegistry`: Discover available servers

**Example**:
```python
from app.mcp.config import (
    MCPServerConfig,
    MCPServerInfo,
    MCPCapabilities
)

config = MCPServerConfig(
    server_info=MCPServerInfo(
        name="commandcenter-mcp",
        version="1.0.0",
        description="CommandCenter MCP Server",
        vendor="CommandCenter"
    ),
    capabilities=MCPCapabilities(
        resources=True,
        tools=True,
        prompts=True,
        logging=False
    ),
    transport="stdio",
    max_connections=10,
    timeout=30
)
```

### 6. Transports (`app/mcp/transports/`)

Transport layers for different communication methods.

#### Stdio Transport

Primary transport for MCP - reads from stdin, writes to stdout.

```python
from app.mcp.transports import StdioTransport, run_stdio_server

server = MCPServer(config)
# ... register providers ...

# Run with stdio transport
await run_stdio_server(server)
```

## MCP Protocol Flow

### 1. Initialization Handshake

```json
// Client -> Server
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocol_version": "2024-11-05",
    "capabilities": {"roots": false, "sampling": false},
    "client_info": {"name": "my-client", "version": "1.0.0"}
  }
}

// Server -> Client
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocol_version": "2024-11-05",
    "capabilities": {
      "resources": true,
      "tools": true,
      "prompts": true
    },
    "server_info": {
      "name": "commandcenter-mcp",
      "version": "1.0.0"
    }
  }
}
```

### 2. List Resources

```json
// Client -> Server
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/list",
  "params": {}
}

// Server -> Client
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "resources": [
      {
        "uri": "commandcenter://projects",
        "name": "Projects",
        "description": "List of all projects"
      }
    ]
  }
}
```

### 3. Read Resource

```json
// Client -> Server
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/read",
  "params": {"uri": "commandcenter://projects"}
}

// Server -> Client
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "uri": "commandcenter://projects",
    "mime_type": "application/json",
    "text": "[{\"id\": 1, \"name\": \"Project A\"}]"
  }
}
```

### 4. Call Tool

```json
// Client -> Server
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "create_task",
    "arguments": {"title": "New Task"}
  }
}

// Server -> Client
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "success": true,
    "result": {"task_id": 123}
  }
}
```

## Error Handling

MCP uses standard JSON-RPC 2.0 error codes:

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Invalid request structure |
| -32601 | Method not found | Method doesn't exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Server error |
| -32001 | Resource not found | Resource URI not found |
| -32002 | Tool not found | Tool name not found |
| -32003 | Prompt not found | Prompt name not found |

**Example Error Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": "Method 'unknown/method' not found"
  }
}
```

## Creating Custom MCP Servers

### Step 1: Define Configuration

```python
from app.mcp import MCPServer
from app.mcp.config import MCPServerConfig, MCPServerInfo

config = MCPServerConfig(
    server_info=MCPServerInfo(
        name="my-mcp-server",
        version="1.0.0"
    )
)

server = MCPServer(config)
```

### Step 2: Create Providers

```python
from app.mcp.providers.base import ResourceProvider

class MyResourceProvider(ResourceProvider):
    async def list_resources(self):
        # Implementation
        pass

    async def read_resource(self, uri: str):
        # Implementation
        pass
```

### Step 3: Register Providers

```python
server.register_resource_provider(MyResourceProvider())
server.register_tool_provider(MyToolProvider())
server.register_prompt_provider(MyPromptProvider())
```

### Step 4: Run Server

```python
from app.mcp.transports import run_stdio_server

await run_stdio_server(server)
```

## Testing

### Unit Tests

Test individual components:

```python
import pytest
from app.mcp.protocol import MCPProtocolHandler

@pytest.mark.asyncio
async def test_parse_request():
    handler = MCPProtocolHandler()
    request = await handler.parse_request('{"jsonrpc": "2.0", ...}')
    assert request.method == "test/method"
```

### Integration Tests

Test full request/response cycles:

```python
@pytest.mark.asyncio
async def test_complete_workflow():
    server = MCPServer(config)
    server.register_resource_provider(TestProvider())

    await server.initialize()
    session = await server.create_session()

    response = await server.handle_message(
        session.session_id,
        '{"jsonrpc": "2.0", "method": "resources/list", ...}'
    )

    assert "resources" in json.loads(response)["result"]
```

## Best Practices

### 1. Provider Design

- **Single Responsibility**: Each provider should handle one domain
- **Async Operations**: All provider methods are async
- **Error Handling**: Raise specific MCP exceptions (ResourceNotFoundError, etc.)
- **Resource URIs**: Use consistent URI schemes (e.g., `commandcenter://domain/resource`)

### 2. Session Management

- **Initialization Required**: Clients must call `initialize` before other methods
- **Session Cleanup**: Clean up resources when sessions close
- **Timeout Handling**: Configure appropriate session timeouts

### 3. Security

- **Input Validation**: Validate all parameters using Pydantic
- **Access Control**: Implement authorization in providers if needed
- **Error Messages**: Don't leak sensitive information in errors

### 4. Performance

- **Lazy Loading**: Load data only when requested
- **Caching**: Cache frequently accessed resources
- **Pagination**: Support pagination for large resource lists
- **Async All The Way**: Never block the event loop

## Future Enhancements

- **HTTP Transport**: REST API endpoint for MCP
- **WebSocket Transport**: Real-time bidirectional communication
- **Resource Subscriptions**: Notify clients of resource changes
- **Sampling Support**: Allow AI to request samples/completions
- **Logging**: Structured logging for debugging

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- CommandCenter API Documentation: `http://localhost:8000/docs`

## Support

For questions or issues with MCP implementation:
- Review test examples in `backend/tests/test_mcp/`
- Check logs for debugging information
- Consult MCP specification for protocol details
