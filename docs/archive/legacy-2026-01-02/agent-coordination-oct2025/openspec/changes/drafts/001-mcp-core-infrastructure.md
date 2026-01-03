# Change Proposal 001: MCP Core Infrastructure

**Agent**: Agent 1 (mcp-core-infrastructure)
**Phase**: 1 - Foundation
**Status**: DRAFT
**Created**: 2025-10-11
**Target Checkpoint**: 1-3 (3 checkpoints x 2 hours each)

---

## Summary

Implement the foundational Model Context Protocol (MCP) infrastructure for CommandCenter. This includes the JSON-RPC 2.0 protocol handler, base server implementation, provider interfaces (Resource, Tool, Prompt), connection management, and configuration system.

**Goal**: Create a robust, extensible MCP framework that Agents 4 and 5 will build MCP servers upon.

---

## Motivation

CommandCenter needs MCP infrastructure to expose its capabilities (project analysis, research orchestration) to AI assistants and IDE integrations. This is the foundational layer that all MCP servers will build upon.

**Problem**: No existing MCP implementation in CommandCenter
**Solution**: Build clean, async-first MCP protocol implementation following JSON-RPC 2.0 spec
**Value**: Enables CommandCenter integration with Claude Code, Cursor, and other MCP clients

---

## Proposed Changes

### Files to Create

```
backend/app/mcp/
├── __init__.py                         # Module initialization
├── protocol.py                         # JSON-RPC 2.0 handler (200 LOC)
├── server.py                           # Base MCPServer class (250 LOC)
├── connection.py                       # Connection management (150 LOC)
├── config.py                           # Configuration schema (100 LOC)
├── utils.py                            # Logging, validation, exceptions (100 LOC)
├── providers/
│   ├── __init__.py
│   ├── base.py                         # Provider base classes (200 LOC)
│   ├── resource.py                     # ResourceProvider interface (80 LOC)
│   ├── tool.py                         # ToolProvider interface (80 LOC)
│   └── prompt.py                       # PromptProvider interface (80 LOC)
└── transports/
    ├── __init__.py
    ├── stdio.py                        # Stdio transport (150 LOC)
    └── http.py                         # HTTP transport stub (50 LOC)

backend/tests/test_mcp/
├── __init__.py
├── test_protocol.py                    # Protocol tests (300 LOC, 18 tests)
├── test_server.py                      # Server tests (250 LOC, 15 tests)
├── test_connection.py                  # Connection tests (150 LOC, 10 tests)
├── test_providers.py                   # Provider tests (200 LOC, 11 tests)
└── fixtures/
    ├── __init__.py
    └── mcp_fixtures.py                 # Test fixtures (100 LOC)

docs/MCP_ARCHITECTURE.md                # Architecture documentation (500 lines)
```

**Total Estimated**: ~2,500 LOC implementation + ~1,000 LOC tests + 500 lines docs

---

## Implementation Details

### Phase 1: Checkpoint 1 (40% - 2 hours)

**Deliverables**:
1. JSON-RPC 2.0 protocol handler (`protocol.py`)
   - Request/response parsing
   - Error handling (parse error, invalid request, method not found)
   - Pydantic models: `JSONRPCRequest`, `JSONRPCResponse`
2. Base server skeleton (`server.py`)
   - `MCPServer` abstract class
   - Lifecycle methods: `initialize()`, `shutdown()`
   - Provider registration: `register_resource_provider()`, etc.
3. Provider base classes (`providers/base.py`)
   - `ResourceProvider` ABC
   - `ToolProvider` ABC
   - `PromptProvider` ABC
4. Basic tests (18 tests)
   - Protocol parsing tests
   - Server initialization tests
   - Provider registration tests

**Contracts Exported**:
- `MCPServer` class with `register_provider()` method
- `ResourceProvider`, `ToolProvider`, `PromptProvider` interfaces
- `JSONRPCRequest`, `JSONRPCResponse` models

**Tests**: 18/54 passing (33%)

---

### Phase 2: Checkpoint 2 (40% - 2 hours)

**Deliverables**:
1. Complete server implementation (`server.py`)
   - `list_resources()`, `read_resource()` routing to providers
   - `list_tools()`, `call_tool()` routing to providers
   - `list_prompts()`, `get_prompt()` routing to providers
   - Capability negotiation
2. Connection manager (`connection.py`)
   - Client connection handling
   - Session management
   - Request routing
3. Stdio transport (`transports/stdio.py`)
   - Read from stdin, write to stdout
   - Message framing
4. Configuration system (`config.py`)
   - `MCPServerConfig` Pydantic model
   - Server discovery mechanism
5. Additional tests (21 tests)
   - End-to-end request/response cycle
   - Connection handling tests
   - Transport tests

**Tests**: 39/54 passing (72%)

---

### Phase 3: Checkpoint 3 (20% - 2 hours)

**Deliverables**:
1. Utilities (`utils.py`)
   - Logging helpers
   - Validation functions
   - Custom exceptions: `MCPError`, `ProtocolError`, `ValidationError`
2. HTTP transport stub (`transports/http.py`)
   - Placeholder for future HTTP transport
3. Documentation (`docs/MCP_ARCHITECTURE.md`)
   - Protocol overview
   - Server implementation guide
   - Provider development guide
   - Usage examples
4. Polish and final tests (15 tests)
   - Error handling edge cases
   - Async provider support tests
   - Integration test: Full MCP server lifecycle

**Tests**: 54/54 passing (100%)

---

## Interface Contracts

### MCPServer Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.mcp.providers.base import ResourceProvider, ToolProvider, PromptProvider

class MCPServer(ABC):
    """Base class for all MCP servers"""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.resource_providers: List[ResourceProvider] = []
        self.tool_providers: List[ToolProvider] = []
        self.prompt_providers: List[PromptProvider] = []

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize server and return capabilities.

        Returns:
            Dict with server info and capabilities:
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "resources": {"listChanged": True},
                    "tools": {"listChanged": True},
                    "prompts": {"listChanged": True}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
            }
        """
        pass

    async def shutdown(self) -> None:
        """Cleanup and shutdown server"""
        pass

    def register_resource_provider(self, provider: ResourceProvider) -> None:
        """Register a resource provider"""
        self.resource_providers.append(provider)

    def register_tool_provider(self, provider: ToolProvider) -> None:
        """Register a tool provider"""
        self.tool_providers.append(provider)

    def register_prompt_provider(self, provider: PromptProvider) -> None:
        """Register a prompt provider"""
        self.prompt_providers.append(provider)

    @abstractmethod
    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        List all available resources.

        Returns:
            List of resource objects:
            [{
                "uri": "resource://projects/123",
                "name": "Project 123",
                "description": "...",
                "mimeType": "application/json"
            }]
        """
        pass

    @abstractmethod
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read specific resource by URI.

        Args:
            uri: Resource URI (e.g., "resource://projects/123")

        Returns:
            Resource content:
            {
                "uri": uri,
                "mimeType": "application/json",
                "text": "..." or "blob": "..."
            }
        """
        pass

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.

        Returns:
            List of tool objects:
            [{
                "name": "analyze_project",
                "description": "Analyze a project directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {...}
                }
            }]
        """
        pass

    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a specific tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result (any JSON-serializable value)
        """
        pass
```

### Provider Interfaces

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

## Dependencies

### New Dependencies to Add

```txt
# Add to backend/requirements.txt
pydantic>=2.0.0       # Already present, for validation
```

No external MCP libraries - implementing protocol from scratch for full control.

---

## Testing Strategy

### Unit Tests (44 tests)
- Protocol parsing (valid/invalid JSON-RPC)
- Server lifecycle (init, register, shutdown)
- Provider registration and routing
- Error handling (protocol errors, validation errors)

### Integration Tests (10 tests)
- Full request/response cycle
- Multiple providers registered
- Async provider support
- Connection lifecycle

### Test Coverage Target
- 90%+ coverage on all modules
- 100% coverage on protocol.py (critical)

---

## Documentation

### MCP_ARCHITECTURE.md Contents

1. **Overview**
   - What is MCP?
   - Why CommandCenter needs it
   - Architecture diagram

2. **Protocol Basics**
   - JSON-RPC 2.0 format
   - MCP-specific methods
   - Capability negotiation

3. **Server Implementation**
   - Subclassing `MCPServer`
   - Registering providers
   - Lifecycle management

4. **Provider Development**
   - Implementing ResourceProvider
   - Implementing ToolProvider
   - Implementing PromptProvider
   - Best practices

5. **Usage Examples**
   - Creating a basic MCP server
   - Adding custom resources
   - Testing your server

6. **Troubleshooting**
   - Common errors
   - Debugging tips

---

## Success Criteria

- ✅ All 54 tests passing
- ✅ Protocol correctly implements JSON-RPC 2.0
- ✅ Base server functional with provider routing
- ✅ Connection manager handles multiple clients
- ✅ Configuration system works
- ✅ 90%+ test coverage
- ✅ Integration test: Full MCP server lifecycle works
- ✅ Documentation complete with examples
- ✅ No external dependencies on Agents 2 or 3
- ✅ Agent 4 and 5 can build servers using these interfaces

---

## Risks & Mitigation

### Risk 1: Protocol Complexity
**Risk**: JSON-RPC 2.0 has edge cases (batch requests, notifications)
**Mitigation**: Start with simple request/response, add features incrementally
**Checkpoint**: If too complex by checkpoint 2, defer batch requests to Phase 2

### Risk 2: Async Provider Support
**Risk**: Some providers may be sync, some async
**Mitigation**: Detect async using `inspect.iscoroutinefunction()`, handle both
**Checkpoint**: Test with both sync and async dummy providers in checkpoint 2

### Risk 3: Transport Abstraction
**Risk**: Transport layer may not be flexible enough
**Mitigation**: Start with stdio (simplest), design abstract interface
**Checkpoint**: HTTP transport is stub only, full implementation in Phase 2 if needed

---

## Coordination Notes

### Exports for Other Agents

**Agent 2 (Project Analyzer)** needs:
- None directly (Agent 2 doesn't integrate with MCP in Phase 1)

**Agent 3 (CLI Interface)** needs:
- None directly (CLI doesn't use MCP in Phase 1)

**Agents 4 & 5 (Phase 2)** will need:
- `MCPServer` base class
- All provider interfaces
- Configuration system
- Documentation on how to create servers

### Imports from Other Agents

- None (Agent 1 is foundational, has no dependencies)

---

## Checkpoint Deliverables Summary

| Checkpoint | Progress | Tests | Key Deliverables |
|------------|----------|-------|------------------|
| 1 | 40% | 18/54 | Protocol handler, server skeleton, provider interfaces |
| 2 | 80% | 39/54 | Full server routing, connection manager, transport |
| 3 | 100% | 54/54 | Utils, docs, polish, integration test |

---

## Review Criteria

### Code Quality
- [ ] Black + Flake8 pass
- [ ] Type hints on all functions
- [ ] Google-style docstrings on all classes/methods
- [ ] No TODOs or FIXMEs

### Functionality
- [ ] Protocol implements JSON-RPC 2.0 spec
- [ ] Server handles all MCP methods
- [ ] Providers can be registered and called
- [ ] Async and sync providers both work

### Testing
- [ ] 54/54 tests passing
- [ ] 90%+ coverage
- [ ] Integration test works end-to-end

### Documentation
- [ ] MCP_ARCHITECTURE.md complete
- [ ] Examples provided
- [ ] Troubleshooting section

### Coordination
- [ ] STATUS.json updated after each commit
- [ ] Contracts match implementation
- [ ] No blockers for Phase 2 agents

---

## Next Steps After Completion

1. **Phase 2 agents can begin**
   - Agent 4 (Project Manager MCP) builds on this
   - Agent 5 (Research Orchestrator MCP) builds on this

2. **Integration validation**
   - Create example MCP server using these interfaces
   - Test with real MCP client (Claude Code, Cursor)

3. **Documentation handoff**
   - MCP_ARCHITECTURE.md becomes guide for Phase 2
   - Example server becomes template

---

## Notes

- This is **pure infrastructure** - no business logic
- Focus on **correctness over features** - get protocol right
- **Extensive logging** for debugging
- **Async-first** throughout - all I/O operations async
- **Pydantic validation** for all messages
- Follow **CommandCenter conventions**: Black formatting, type hints, docstrings
