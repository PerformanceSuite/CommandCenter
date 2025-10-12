"""Tests for MCP server."""

import json
import pytest

from app.mcp.config import (
    MCPCapabilities,
    MCPServerConfig,
    MCPServerInfo,
)
from app.mcp.server import MCPServer
from app.mcp.providers.base import (
    Resource,
    ResourceContent,
    ResourceProvider,
    Tool,
    ToolProvider,
    ToolResult,
    Prompt,
    PromptProvider,
    PromptResult,
    PromptMessage,
)
from app.mcp.utils import (
    ResourceNotFoundError,
    ToolNotFoundError,
    PromptNotFoundError,
)


class MockResourceProvider(ResourceProvider):
    """Mock resource provider for testing."""

    def __init__(self):
        super().__init__("test_resources")
        self.resources = [
            Resource(
                uri="commandcenter://project/1",
                name="Test Project",
                description="A test project",
            )
        ]

    async def list_resources(self):
        return self.resources

    async def read_resource(self, uri: str):
        for resource in self.resources:
            if resource.uri == uri:
                return ResourceContent(
                    uri=uri,
                    mime_type="application/json",
                    text='{"id": 1, "name": "Test Project"}',
                )
        raise ResourceNotFoundError(uri)


class MockToolProvider(ToolProvider):
    """Mock tool provider for testing."""

    def __init__(self):
        super().__init__("test_tools")
        self.tools = [
            Tool(
                name="analyze_project",
                description="Analyze a project",
                parameters=[],
            )
        ]

    async def list_tools(self):
        return self.tools

    async def call_tool(self, name: str, arguments: dict):
        if name == "analyze_project":
            return ToolResult(
                success=True, result={"analysis": "Project looks good"}
            )
        raise ToolNotFoundError(name)


class MockPromptProvider(PromptProvider):
    """Mock prompt provider for testing."""

    def __init__(self):
        super().__init__("test_prompts")
        self.prompts = [
            Prompt(
                name="code_review",
                description="Code review prompt",
                parameters=[],
            )
        ]

    async def list_prompts(self):
        return self.prompts

    async def get_prompt(self, name: str, arguments: dict = None):
        if name == "code_review":
            return PromptResult(
                messages=[
                    PromptMessage(
                        role="system", content="You are a code reviewer"
                    ),
                    PromptMessage(role="user", content="Review this code"),
                ]
            )
        raise PromptNotFoundError(name)


@pytest.fixture
def server_config():
    """Create test server configuration."""
    return MCPServerConfig(
        server_info=MCPServerInfo(
            name="test-mcp-server",
            version="1.0.0",
            description="Test MCP Server",
        ),
        capabilities=MCPCapabilities(
            resources=True,
            tools=True,
            prompts=True,
        ),
    )


@pytest.fixture
async def server(server_config):
    """Create and initialize test server."""
    srv = MCPServer(server_config)

    # Register mock providers
    srv.register_resource_provider(MockResourceProvider())
    srv.register_tool_provider(MockToolProvider())
    srv.register_prompt_provider(MockPromptProvider())

    await srv.initialize()
    await srv.start()

    yield srv

    await srv.shutdown()


class TestMCPServer:
    """Tests for MCP server."""

    def test_server_creation(self, server_config):
        """Test creating server instance."""
        server = MCPServer(server_config)

        assert server.server_info.name == "test-mcp-server"
        assert server.capabilities.resources is True
        assert not server.is_running()
        assert not server.is_initialized()

    @pytest.mark.asyncio
    async def test_server_initialization(self, server_config):
        """Test server initialization."""
        server = MCPServer(server_config)
        server.register_resource_provider(MockResourceProvider())

        await server.initialize()

        assert server.is_initialized()

    @pytest.mark.asyncio
    async def test_server_start(self, server_config):
        """Test server start."""
        server = MCPServer(server_config)

        await server.start()

        assert server.is_running()
        assert server.is_initialized()

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_server_shutdown(self, server):
        """Test server shutdown."""
        assert server.is_running()

        await server.shutdown()

        assert not server.is_running()
        assert not server.is_initialized()

    @pytest.mark.asyncio
    async def test_register_providers(self, server_config):
        """Test registering providers."""
        server = MCPServer(server_config)

        resource_provider = MockResourceProvider()
        tool_provider = MockToolProvider()
        prompt_provider = MockPromptProvider()

        server.register_resource_provider(resource_provider)
        server.register_tool_provider(tool_provider)
        server.register_prompt_provider(prompt_provider)

        assert len(server._resource_providers) == 1
        assert len(server._tool_providers) == 1
        assert len(server._prompt_providers) == 1

    @pytest.mark.asyncio
    async def test_session_management(self, server):
        """Test creating and closing sessions."""
        session = await server.create_session({"name": "test-client"})

        assert session.session_id is not None
        assert session.client_info["name"] == "test-client"

        await server.close_session(session.session_id)

    @pytest.mark.asyncio
    async def test_initialize_request(self, server):
        """Test handling initialize request."""
        session = await server.create_session()

        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocol_version": "2024-11-05",
                "capabilities": {"roots": False, "sampling": False},
                "client_info": {"name": "test-client", "version": "1.0.0"},
            },
        }

        response = await server.handle_message(
            session.session_id, json.dumps(request_data)
        )

        response_data = json.loads(response)

        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == 1
        assert "result" in response_data
        assert response_data["result"]["server_info"]["name"] == "test-mcp-server"
        assert session.is_initialized()

    @pytest.mark.asyncio
    async def test_list_resources_request(self, server):
        """Test handling resources/list request."""
        session = await server.create_session()
        session.set_initialized(True)

        request_data = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list",
            "params": {},
        }

        response = await server.handle_message(
            session.session_id, json.dumps(request_data)
        )

        response_data = json.loads(response)

        assert response_data["id"] == 2
        assert "result" in response_data
        assert "resources" in response_data["result"]
        assert len(response_data["result"]["resources"]) > 0

    @pytest.mark.asyncio
    async def test_read_resource_request(self, server):
        """Test handling resources/read request."""
        session = await server.create_session()
        session.set_initialized(True)

        request_data = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/read",
            "params": {"uri": "commandcenter://project/1"},
        }

        response = await server.handle_message(
            session.session_id, json.dumps(request_data)
        )

        response_data = json.loads(response)

        assert response_data["id"] == 3
        assert "result" in response_data
        assert response_data["result"]["uri"] == "commandcenter://project/1"
        assert "text" in response_data["result"]

    @pytest.mark.asyncio
    async def test_list_tools_request(self, server):
        """Test handling tools/list request."""
        session = await server.create_session()
        session.set_initialized(True)

        request_data = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/list",
            "params": {},
        }

        response = await server.handle_message(
            session.session_id, json.dumps(request_data)
        )

        response_data = json.loads(response)

        assert response_data["id"] == 4
        assert "tools" in response_data["result"]
        assert len(response_data["result"]["tools"]) > 0

    @pytest.mark.asyncio
    async def test_call_tool_request(self, server):
        """Test handling tools/call request."""
        session = await server.create_session()
        session.set_initialized(True)

        request_data = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "analyze_project", "arguments": {}},
        }

        response = await server.handle_message(
            session.session_id, json.dumps(request_data)
        )

        response_data = json.loads(response)

        assert response_data["id"] == 5
        assert "result" in response_data
        assert response_data["result"]["success"] is True

    @pytest.mark.asyncio
    async def test_list_prompts_request(self, server):
        """Test handling prompts/list request."""
        session = await server.create_session()
        session.set_initialized(True)

        request_data = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "prompts/list",
            "params": {},
        }

        response = await server.handle_message(
            session.session_id, json.dumps(request_data)
        )

        response_data = json.loads(response)

        assert response_data["id"] == 6
        assert "prompts" in response_data["result"]
        assert len(response_data["result"]["prompts"]) > 0

    @pytest.mark.asyncio
    async def test_get_prompt_request(self, server):
        """Test handling prompts/get request."""
        session = await server.create_session()
        session.set_initialized(True)

        request_data = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "prompts/get",
            "params": {"name": "code_review"},
        }

        response = await server.handle_message(
            session.session_id, json.dumps(request_data)
        )

        response_data = json.loads(response)

        assert response_data["id"] == 7
        assert "messages" in response_data["result"]
        assert len(response_data["result"]["messages"]) > 0

    @pytest.mark.asyncio
    async def test_method_not_found(self, server):
        """Test handling unknown method."""
        session = await server.create_session()
        session.set_initialized(True)

        request_data = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "unknown/method",
            "params": {},
        }

        response = await server.handle_message(
            session.session_id, json.dumps(request_data)
        )

        response_data = json.loads(response)

        assert response_data["id"] == 8
        assert "error" in response_data
        assert response_data["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_uninitialized_session(self, server):
        """Test that uninitialized sessions can't call methods."""
        session = await server.create_session()

        request_data = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "resources/list",
            "params": {},
        }

        response = await server.handle_message(
            session.session_id, json.dumps(request_data)
        )

        response_data = json.loads(response)

        assert response_data["id"] == 9
        assert "error" in response_data

    @pytest.mark.asyncio
    async def test_get_stats(self, server):
        """Test getting server statistics."""
        stats = server.get_stats()

        assert stats["server_name"] == "test-mcp-server"
        assert stats["version"] == "1.0.0"
        assert stats["running"] is True
        assert stats["resource_providers"] == 1
        assert stats["tool_providers"] == 1
        assert stats["prompt_providers"] == 1
