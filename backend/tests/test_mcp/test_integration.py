"""Integration tests for MCP server."""

import json
import pytest

from app.mcp import MCPServer
from app.mcp.config import MCPCapabilities, MCPServerConfig, MCPServerInfo
from app.mcp.providers.base import (
    Prompt,
    PromptMessage,
    PromptProvider,
    PromptResult,
    Resource,
    ResourceContent,
    ResourceProvider,
    Tool,
    ToolParameter,
    ToolProvider,
    ToolResult,
)
from app.mcp.utils import PromptNotFoundError, ResourceNotFoundError, ToolNotFoundError


class CompleteResourceProvider(ResourceProvider):
    """Complete resource provider implementation."""

    def __init__(self):
        super().__init__("complete_resources")
        self.resources = [
            Resource(
                uri="commandcenter://technologies",
                name="Technologies",
                description="List of technologies",
                mime_type="application/json",
            ),
            Resource(
                uri="commandcenter://research-tasks",
                name="Research Tasks",
                description="List of research tasks",
                mime_type="application/json",
            ),
        ]

    async def list_resources(self):
        return self.resources

    async def read_resource(self, uri: str):
        if uri == "commandcenter://technologies":
            return ResourceContent(
                uri=uri,
                mime_type="application/json",
                text='[{"id": 1, "name": "Python"}, {"id": 2, "name": "FastAPI"}]',
            )
        elif uri == "commandcenter://research-tasks":
            return ResourceContent(
                uri=uri,
                mime_type="application/json",
                text='[{"id": 1, "title": "Evaluate MCP protocol"}]',
            )
        raise ResourceNotFoundError(uri)


class CompleteToolProvider(ToolProvider):
    """Complete tool provider implementation."""

    def __init__(self):
        super().__init__("complete_tools")
        self.tools = [
            Tool(
                name="create_task",
                description="Create a new research task",
                parameters=[
                    ToolParameter(
                        name="title", type="string", description="Task title", required=True
                    ),
                    ToolParameter(
                        name="description",
                        type="string",
                        description="Task description",
                        required=False,
                    ),
                ],
                returns="Created task ID",
            ),
            Tool(
                name="analyze_repository",
                description="Analyze a GitHub repository",
                parameters=[
                    ToolParameter(
                        name="repo_url",
                        type="string",
                        description="Repository URL",
                        required=True,
                    ),
                ],
                returns="Analysis results",
            ),
        ]

    async def list_tools(self):
        return self.tools

    async def call_tool(self, name: str, arguments: dict):
        if name == "create_task":
            title = arguments.get("title")
            return ToolResult(
                success=True,
                result={"task_id": 123, "title": title, "status": "created"},
            )
        elif name == "analyze_repository":
            repo_url = arguments.get("repo_url")
            return ToolResult(
                success=True,
                result={
                    "repo": repo_url,
                    "languages": ["Python", "JavaScript"],
                    "stars": 42,
                },
            )
        raise ToolNotFoundError(name)


class CompletePromptProvider(PromptProvider):
    """Complete prompt provider implementation."""

    def __init__(self):
        super().__init__("complete_prompts")
        self.prompts = [
            Prompt(
                name="research_analysis",
                description="Analyze research findings",
                parameters=[],
            ),
            Prompt(
                name="technology_evaluation",
                description="Evaluate a technology",
                parameters=[],
            ),
        ]

    async def list_prompts(self):
        return self.prompts

    async def get_prompt(self, name: str, arguments: dict = None):
        if name == "research_analysis":
            return PromptResult(
                messages=[
                    PromptMessage(
                        role="system",
                        content="You are a research analyst. Analyze the given research findings and provide insights.",
                    ),
                    PromptMessage(
                        role="user",
                        content="Please analyze the research findings and summarize key points.",
                    ),
                ]
            )
        elif name == "technology_evaluation":
            return PromptResult(
                messages=[
                    PromptMessage(
                        role="system",
                        content="You are a technology evaluator. Assess technologies objectively.",
                    ),
                    PromptMessage(
                        role="user",
                        content="Evaluate the technology and provide pros and cons.",
                    ),
                ]
            )
        raise PromptNotFoundError(name)


@pytest.fixture
async def complete_server():
    """Create complete MCP server with all providers."""
    config = MCPServerConfig(
        server_info=MCPServerInfo(
            name="commandcenter-mcp",
            version="1.0.0",
            description="CommandCenter MCP Server",
            vendor="CommandCenter",
        ),
        capabilities=MCPCapabilities(
            resources=True,
            tools=True,
            prompts=True,
            logging=False,
        ),
    )

    server = MCPServer(config)

    # Register all providers
    server.register_resource_provider(CompleteResourceProvider())
    server.register_tool_provider(CompleteToolProvider())
    server.register_prompt_provider(CompletePromptProvider())

    await server.initialize()
    await server.start()

    yield server

    await server.shutdown()


class TestMCPIntegration:
    """Integration tests for complete MCP workflow."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, complete_server):
        """Test complete MCP workflow from initialization to method calls."""
        # Create session
        session = await complete_server.create_session()

        # Step 1: Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocol_version": "2024-11-05",
                "capabilities": {"roots": False, "sampling": False},
                "client_info": {
                    "name": "integration-test-client",
                    "version": "1.0.0",
                },
            },
        }

        response = await complete_server.handle_message(
            session.session_id, json.dumps(init_request)
        )
        init_data = json.loads(response)

        assert init_data["result"]["server_info"]["name"] == "commandcenter-mcp"
        assert "capabilities" in init_data["result"]

        # Step 2: List resources
        list_resources_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list",
            "params": {},
        }

        response = await complete_server.handle_message(
            session.session_id, json.dumps(list_resources_request)
        )
        resources_data = json.loads(response)

        assert len(resources_data["result"]["resources"]) == 2
        assert any(r["name"] == "Technologies" for r in resources_data["result"]["resources"])

        # Step 3: Read a resource
        read_resource_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/read",
            "params": {"uri": "commandcenter://technologies"},
        }

        response = await complete_server.handle_message(
            session.session_id, json.dumps(read_resource_request)
        )
        resource_data = json.loads(response)

        assert resource_data["result"]["uri"] == "commandcenter://technologies"
        assert "Python" in resource_data["result"]["text"]

        # Step 4: List tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/list",
            "params": {},
        }

        response = await complete_server.handle_message(
            session.session_id, json.dumps(list_tools_request)
        )
        tools_data = json.loads(response)

        assert len(tools_data["result"]["tools"]) == 2
        assert any(t["name"] == "create_task" for t in tools_data["result"]["tools"])

        # Step 5: Call a tool
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "create_task",
                "arguments": {"title": "Test MCP Integration"},
            },
        }

        response = await complete_server.handle_message(
            session.session_id, json.dumps(call_tool_request)
        )
        tool_data = json.loads(response)

        assert tool_data["result"]["success"] is True
        assert tool_data["result"]["result"]["task_id"] == 123

        # Step 6: List prompts
        list_prompts_request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "prompts/list",
            "params": {},
        }

        response = await complete_server.handle_message(
            session.session_id, json.dumps(list_prompts_request)
        )
        prompts_data = json.loads(response)

        assert len(prompts_data["result"]["prompts"]) == 2
        assert any(
            p["name"] == "research_analysis"
            for p in prompts_data["result"]["prompts"]
        )

        # Step 7: Get a prompt
        get_prompt_request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "prompts/get",
            "params": {"name": "research_analysis"},
        }

        response = await complete_server.handle_message(
            session.session_id, json.dumps(get_prompt_request)
        )
        prompt_data = json.loads(response)

        assert len(prompt_data["result"]["messages"]) == 2
        assert prompt_data["result"]["messages"][0]["role"] == "system"

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, complete_server):
        """Test handling multiple concurrent sessions."""
        # Create two sessions
        session1 = await complete_server.create_session({"client": "client1"})
        session2 = await complete_server.create_session({"client": "client2"})

        # Initialize both sessions
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocol_version": "2024-11-05",
                "capabilities": {"roots": False, "sampling": False},
                "client_info": {"name": "test-client", "version": "1.0.0"},
            },
        }

        response1 = await complete_server.handle_message(
            session1.session_id, json.dumps(init_request)
        )
        response2 = await complete_server.handle_message(
            session2.session_id, json.dumps(init_request)
        )

        assert json.loads(response1)["id"] == 1
        assert json.loads(response2)["id"] == 1

        # Both sessions should work independently
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list",
            "params": {},
        }

        response1 = await complete_server.handle_message(
            session1.session_id, json.dumps(list_request)
        )
        response2 = await complete_server.handle_message(
            session2.session_id, json.dumps(list_request)
        )

        assert "resources" in json.loads(response1)["result"]
        assert "resources" in json.loads(response2)["result"]

    @pytest.mark.asyncio
    async def test_error_handling(self, complete_server):
        """Test comprehensive error handling."""
        session = await complete_server.create_session()
        session.set_initialized(True)

        # Test invalid JSON
        response = await complete_server.handle_message(
            session.session_id, "invalid json"
        )
        error_data = json.loads(response)
        assert "error" in error_data
        assert error_data["error"]["code"] == -32700

        # Test method not found
        unknown_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "unknown/method",
            "params": {},
        }
        response = await complete_server.handle_message(
            session.session_id, json.dumps(unknown_request)
        )
        error_data = json.loads(response)
        assert error_data["error"]["code"] == -32601

        # Test resource not found
        not_found_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/read",
            "params": {"uri": "nonexistent://resource"},
        }
        response = await complete_server.handle_message(
            session.session_id, json.dumps(not_found_request)
        )
        error_data = json.loads(response)
        assert "error" in error_data

    @pytest.mark.asyncio
    async def test_server_statistics(self, complete_server):
        """Test server statistics reporting."""
        stats = complete_server.get_stats()

        assert stats["server_name"] == "commandcenter-mcp"
        assert stats["running"] is True
        assert stats["initialized"] is True
        assert stats["resource_providers"] == 1
        assert stats["tool_providers"] == 1
        assert stats["prompt_providers"] == 1
