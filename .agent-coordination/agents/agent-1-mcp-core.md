# Agent 1: MCP Core Infrastructure

**Agent Name**: mcp-core-infrastructure
**Phase**: 1 (Foundation)
**Branch**: agent/mcp-core-infrastructure
**Duration**: 8-12 hours
**Dependencies**: None (foundation layer)

---

## Mission

Build the core Model Context Protocol (MCP) infrastructure for CommandCenter. This is the foundation that all MCP servers will build upon.

You are implementing the MCP protocol specification (JSON-RPC 2.0) to enable CommandCenter to expose its capabilities (resources, tools, prompts) to AI assistants and other MCP clients.

---

## Deliverables

### 1. MCP Protocol Handler (`backend/app/mcp/protocol.py`)
- JSON-RPC 2.0 request/response handling
- Protocol version negotiation
- Error handling and validation
- Message serialization/deserialization

### 2. Base Server Implementation (`backend/app/mcp/server.py`)
- `MCPServer` base class
- Server lifecycle (initialize → running → shutdown)
- Capability registration system
- Transport layer abstraction (stdio, HTTP, WebSocket)

### 3. Provider Interfaces (`backend/app/mcp/providers/`)
- `ResourceProvider` - Expose data (projects, technologies, research tasks)
- `ToolProvider` - Expose callable functions (analyze_project, create_task)
- `PromptProvider` - Expose prompt templates

### 4. Connection Manager (`backend/app/mcp/connection.py`)
- Client connection handling
- Session management
- Request routing to appropriate handlers

### 5. Configuration System (`backend/app/mcp/config.py`)
- MCP server configuration schema
- Discovery mechanism for available servers
- Server registration and metadata

### 6. Utilities (`backend/app/mcp/utils.py`)
- Logging helpers
- Validation functions
- Common exceptions

### 7. Tests (`backend/tests/test_mcp/`)
- Protocol handler tests
- Server lifecycle tests
- Provider interface tests
- Connection manager tests
- Integration test: Basic MCP server startup

---

## Technical Specifications

### MCP Protocol Basics

**Request Format** (JSON-RPC 2.0):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {}
}
```

**Response Format**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resources": [...]
  }
}
```

### Core Methods to Implement

1. **initialize**: Handshake and capability exchange
2. **resources/list**: List available resources
3. **resources/read**: Read specific resource
4. **tools/list**: List available tools
5. **tools/call**: Execute a tool
6. **prompts/list**: List available prompts
7. **prompts/get**: Get specific prompt template

### Architecture

```
backend/app/mcp/
├── __init__.py
├── protocol.py          # JSON-RPC handler
├── server.py            # Base MCPServer class
├── connection.py        # Connection management
├── config.py            # Configuration
├── utils.py             # Utilities
├── providers/
│   ├── __init__.py
│   ├── base.py          # Base provider classes
│   ├── resource.py      # ResourceProvider
│   ├── tool.py          # ToolProvider
│   └── prompt.py        # PromptProvider
└── transports/
    ├── __init__.py
    ├── stdio.py         # Stdio transport
    └── http.py          # HTTP transport (future)
```

---

## Implementation Guidelines

### 1. Protocol Handler (`protocol.py`)

```python
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class JSONRPCRequest(BaseModel):
    jsonrpc: str = Field(default="2.0")
    id: Optional[int | str] = None
    method: str
    params: Optional[Dict[str, Any]] = None

class JSONRPCResponse(BaseModel):
    jsonrpc: str = Field(default="2.0")
    id: Optional[int | str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class MCPProtocolHandler:
    """Handles MCP protocol message parsing and validation"""

    async def handle_request(self, raw_message: str) -> JSONRPCResponse:
        """Parse and handle incoming JSON-RPC request"""
        pass

    def create_response(self, request_id: int | str, result: Any) -> JSONRPCResponse:
        """Create successful response"""
        pass

    def create_error(self, request_id: int | str, code: int, message: str) -> JSONRPCResponse:
        """Create error response"""
        pass
```

### 2. Base Server (`server.py`)

```python
from abc import ABC, abstractmethod
from typing import List
from app.mcp.providers.base import ResourceProvider, ToolProvider, PromptProvider

class MCPServer(ABC):
    """Base class for MCP servers"""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.resource_providers: List[ResourceProvider] = []
        self.tool_providers: List[ToolProvider] = []
        self.prompt_providers: List[PromptProvider] = []

    async def initialize(self) -> Dict[str, Any]:
        """Initialize server and return capabilities"""
        pass

    async def shutdown(self):
        """Cleanup and shutdown"""
        pass

    def register_resource_provider(self, provider: ResourceProvider):
        """Register a resource provider"""
        pass

    @abstractmethod
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources"""
        pass

    @abstractmethod
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read specific resource by URI"""
        pass

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        pass

    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific tool"""
        pass
```

### 3. Provider Interfaces (`providers/base.py`)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ResourceProvider(ABC):
    """Base class for resource providers"""

    @abstractmethod
    async def list_resources(self) -> List[Dict[str, Any]]:
        """Return list of resources this provider exposes"""
        pass

    @abstractmethod
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read specific resource by URI"""
        pass

class ToolProvider(ABC):
    """Base class for tool providers"""

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of tools this provider exposes"""
        pass

    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool with given arguments"""
        pass

class PromptProvider(ABC):
    """Base class for prompt providers"""

    @abstractmethod
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """Return list of prompts this provider exposes"""
        pass

    @abstractmethod
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Get prompt template with arguments filled"""
        pass
```

---

## Testing Strategy

### Unit Tests
- Test JSON-RPC parsing (valid/invalid messages)
- Test server lifecycle (init → running → shutdown)
- Test provider registration
- Test error handling

### Integration Tests
- Create minimal MCP server
- Register dummy providers
- Send MCP requests, verify responses
- Test capability negotiation

### Example Test (`tests/test_mcp/test_protocol.py`)

```python
import pytest
from app.mcp.protocol import MCPProtocolHandler, JSONRPCRequest

@pytest.mark.asyncio
async def test_handle_valid_request():
    handler = MCPProtocolHandler()

    request_json = '{"jsonrpc": "2.0", "id": 1, "method": "resources/list", "params": {}}'
    response = await handler.handle_request(request_json)

    assert response.jsonrpc == "2.0"
    assert response.id == 1
    assert response.error is None

@pytest.mark.asyncio
async def test_handle_invalid_json():
    handler = MCPProtocolHandler()

    response = await handler.handle_request("invalid json")

    assert response.error is not None
    assert response.error["code"] == -32700  # Parse error
```

---

## Dependencies

```txt
# Add to backend/requirements.txt
jsonrpc-python>=0.12.0  # JSON-RPC implementation
pydantic>=2.0.0         # Already present, for validation
```

---

## Documentation

Create `docs/MCP_ARCHITECTURE.md` with:
- MCP protocol overview
- Server implementation guide
- Provider development guide
- Examples of creating custom MCP servers

---

## Success Criteria

- ✅ All MCP protocol methods implemented
- ✅ Base server class functional
- ✅ Provider interfaces defined and documented
- ✅ Connection manager handles multiple clients
- ✅ Configuration system discovers servers
- ✅ 80%+ test coverage
- ✅ Integration test: Full request/response cycle works
- ✅ No external dependencies on other agents

---

## Notes

- This is foundational work - prioritize correctness over features
- Follow async/await patterns throughout
- Use Pydantic for all validation
- Comprehensive error handling (protocol errors, validation errors, server errors)
- Extensive logging for debugging

---

## Self-Review Checklist

Before marking PR as ready:
- [ ] All 7 deliverables complete
- [ ] Tests pass (pytest tests/test_mcp/ -v)
- [ ] Linting passes (black, flake8)
- [ ] Type hints on all functions
- [ ] Docstrings (Google style) on all classes/methods
- [ ] MCP_ARCHITECTURE.md documentation complete
- [ ] Example usage in docs
- [ ] No TODOs or FIXMEs left
- [ ] Self-review score: 10/10
