"""Tests for MCP provider interfaces."""

import pytest

from app.mcp.providers.base import (
    BaseProvider,
    Prompt,
    PromptMessage,
    PromptParameter,
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


class TestResourceModels:
    """Tests for resource models."""

    def test_resource_creation(self):
        """Test creating resource."""
        resource = Resource(
            uri="test://resource/1",
            name="Test Resource",
            description="A test resource",
            mime_type="application/json",
        )

        assert resource.uri == "test://resource/1"
        assert resource.name == "Test Resource"
        assert resource.description == "A test resource"
        assert resource.mime_type == "application/json"

    def test_resource_content(self):
        """Test resource content model."""
        content = ResourceContent(
            uri="test://resource/1",
            mime_type="text/plain",
            text="Test content",
        )

        assert content.uri == "test://resource/1"
        assert content.mime_type == "text/plain"
        assert content.text == "Test content"
        assert content.blob is None


class TestToolModels:
    """Tests for tool models."""

    def test_tool_parameter(self):
        """Test tool parameter model."""
        param = ToolParameter(
            name="input",
            type="string",
            description="Input parameter",
            required=True,
            default="default value",
        )

        assert param.name == "input"
        assert param.type == "string"
        assert param.required is True
        assert param.default == "default value"

    def test_tool_creation(self):
        """Test creating tool."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(name="param1", type="string", required=True),
                ToolParameter(name="param2", type="number", required=False),
            ],
            returns="Result description",
        )

        assert tool.name == "test_tool"
        assert len(tool.parameters) == 2
        assert tool.returns == "Result description"

    def test_tool_result_success(self):
        """Test successful tool result."""
        result = ToolResult(success=True, result={"output": "value"})

        assert result.success is True
        assert result.result == {"output": "value"}
        assert result.error is None

    def test_tool_result_error(self):
        """Test error tool result."""
        result = ToolResult(success=False, error="Something went wrong")

        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.result is None


class TestPromptModels:
    """Tests for prompt models."""

    def test_prompt_parameter(self):
        """Test prompt parameter model."""
        param = PromptParameter(
            name="topic",
            description="Topic to generate prompt about",
            required=True,
            default="general",
        )

        assert param.name == "topic"
        assert param.description == "Topic to generate prompt about"
        assert param.required is True

    def test_prompt_creation(self):
        """Test creating prompt."""
        prompt = Prompt(
            name="test_prompt",
            description="A test prompt template",
            parameters=[
                PromptParameter(name="param1", required=True),
            ],
        )

        assert prompt.name == "test_prompt"
        assert len(prompt.parameters) == 1

    def test_prompt_message(self):
        """Test prompt message model."""
        message = PromptMessage(role="user", content="Test message")

        assert message.role == "user"
        assert message.content == "Test message"

    def test_prompt_result(self):
        """Test prompt result model."""
        result = PromptResult(
            messages=[
                PromptMessage(role="system", content="System prompt"),
                PromptMessage(role="user", content="User prompt"),
            ]
        )

        assert len(result.messages) == 2
        assert result.messages[0].role == "system"


class MockResourceProvider(ResourceProvider):
    """Mock resource provider for testing."""

    def __init__(self):
        super().__init__("mock_resource_provider")
        self.resources = [
            Resource(uri="test://resource/1", name="Resource 1"),
            Resource(uri="test://resource/2", name="Resource 2"),
        ]

    async def list_resources(self):
        return self.resources

    async def read_resource(self, uri: str):
        for resource in self.resources:
            if resource.uri == uri:
                return ResourceContent(uri=uri, mime_type="text/plain", text=f"Content for {uri}")
        raise ResourceNotFoundError(uri)


class MockToolProvider(ToolProvider):
    """Mock tool provider for testing."""

    def __init__(self):
        super().__init__("mock_tool_provider")
        self.tools = [
            Tool(name="tool1", description="Tool 1"),
            Tool(name="tool2", description="Tool 2"),
        ]

    async def list_tools(self):
        return self.tools

    async def call_tool(self, name: str, arguments: dict):
        for tool in self.tools:
            if tool.name == name:
                return ToolResult(success=True, result={"output": f"Result from {name}"})
        raise ToolNotFoundError(name)


class MockPromptProvider(PromptProvider):
    """Mock prompt provider for testing."""

    def __init__(self):
        super().__init__("mock_prompt_provider")
        self.prompts = [
            Prompt(name="prompt1", description="Prompt 1"),
            Prompt(name="prompt2", description="Prompt 2"),
        ]

    async def list_prompts(self):
        return self.prompts

    async def get_prompt(self, name: str, arguments: dict = None):
        for prompt in self.prompts:
            if prompt.name == name:
                return PromptResult(
                    messages=[PromptMessage(role="user", content=f"Prompt content for {name}")]
                )
        raise PromptNotFoundError(name)


class TestBaseProvider:
    """Tests for base provider."""

    @pytest.mark.asyncio
    async def test_provider_initialization(self):
        """Test provider initialization."""
        provider = MockResourceProvider()

        assert provider.name == "mock_resource_provider"
        assert not provider.is_initialized

        await provider.initialize()

        assert provider.is_initialized

    @pytest.mark.asyncio
    async def test_provider_shutdown(self):
        """Test provider shutdown."""
        provider = MockResourceProvider()

        await provider.initialize()
        assert provider.is_initialized

        await provider.shutdown()
        assert not provider.is_initialized


class TestResourceProvider:
    """Tests for resource provider."""

    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Test listing resources."""
        provider = MockResourceProvider()
        resources = await provider.list_resources()

        assert len(resources) == 2
        assert resources[0].name == "Resource 1"

    @pytest.mark.asyncio
    async def test_read_resource_success(self):
        """Test reading existing resource."""
        provider = MockResourceProvider()
        content = await provider.read_resource("test://resource/1")

        assert content.uri == "test://resource/1"
        assert "Content for" in content.text

    @pytest.mark.asyncio
    async def test_read_resource_not_found(self):
        """Test reading non-existent resource."""
        provider = MockResourceProvider()

        with pytest.raises(ResourceNotFoundError):
            await provider.read_resource("test://nonexistent")


class TestToolProvider:
    """Tests for tool provider."""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing tools."""
        provider = MockToolProvider()
        tools = await provider.list_tools()

        assert len(tools) == 2
        assert tools[0].name == "tool1"

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test calling existing tool."""
        provider = MockToolProvider()
        result = await provider.call_tool("tool1", {})

        assert result.success is True
        assert "Result from" in result.result["output"]

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self):
        """Test calling non-existent tool."""
        provider = MockToolProvider()

        with pytest.raises(ToolNotFoundError):
            await provider.call_tool("nonexistent_tool", {})


class TestPromptProvider:
    """Tests for prompt provider."""

    @pytest.mark.asyncio
    async def test_list_prompts(self):
        """Test listing prompts."""
        provider = MockPromptProvider()
        prompts = await provider.list_prompts()

        assert len(prompts) == 2
        assert prompts[0].name == "prompt1"

    @pytest.mark.asyncio
    async def test_get_prompt_success(self):
        """Test getting existing prompt."""
        provider = MockPromptProvider()
        result = await provider.get_prompt("prompt1")

        assert len(result.messages) == 1
        assert "Prompt content" in result.messages[0].content

    @pytest.mark.asyncio
    async def test_get_prompt_not_found(self):
        """Test getting non-existent prompt."""
        provider = MockPromptProvider()

        with pytest.raises(PromptNotFoundError):
            await provider.get_prompt("nonexistent_prompt")
