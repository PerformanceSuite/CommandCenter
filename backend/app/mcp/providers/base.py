"""
Base provider classes for MCP resources, tools, and prompts.

These abstract classes define the interface that all MCP providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Resource models
class Resource(BaseModel):
    """
    MCP Resource representation.

    Attributes:
        uri: Unique resource identifier
        name: Human-readable name
        description: Optional description
        mime_type: Optional MIME type of the resource
        metadata: Optional additional metadata
    """

    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ResourceContent(BaseModel):
    """
    Resource content data.

    Attributes:
        uri: Resource URI
        mime_type: Content MIME type
        text: Text content (if applicable)
        blob: Binary content (if applicable)
        metadata: Optional metadata
    """

    uri: str
    mime_type: str
    text: Optional[str] = None
    blob: Optional[bytes] = None
    metadata: Optional[Dict[str, Any]] = None


# Tool models
class ToolParameter(BaseModel):
    """
    Tool parameter definition.

    Attributes:
        name: Parameter name
        type: Parameter type (string, number, boolean, object, array)
        description: Optional description
        required: Whether parameter is required
        default: Optional default value
    """

    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None


class Tool(BaseModel):
    """
    MCP Tool representation.

    Attributes:
        name: Unique tool identifier
        description: Tool description
        parameters: List of tool parameters
        returns: Description of what the tool returns
    """

    name: str
    description: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    returns: Optional[str] = None


class ToolResult(BaseModel):
    """
    Tool execution result.

    Attributes:
        success: Whether execution was successful
        result: Result data (if successful)
        error: Error message (if failed)
        metadata: Optional metadata
    """

    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Prompt models
class PromptParameter(BaseModel):
    """
    Prompt parameter definition.

    Attributes:
        name: Parameter name
        description: Optional description
        required: Whether parameter is required
        default: Optional default value
    """

    name: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[str] = None


class Prompt(BaseModel):
    """
    MCP Prompt representation.

    Attributes:
        name: Unique prompt identifier
        description: Prompt description
        parameters: List of prompt parameters
    """

    name: str
    description: str
    parameters: List[PromptParameter] = Field(default_factory=list)


class PromptMessage(BaseModel):
    """
    Individual prompt message.

    Attributes:
        role: Message role (system, user, assistant)
        content: Message content
    """

    role: str
    content: str


class PromptResult(BaseModel):
    """
    Rendered prompt result.

    Attributes:
        messages: List of prompt messages
        metadata: Optional metadata
    """

    messages: List[PromptMessage]
    metadata: Optional[Dict[str, Any]] = None


# Base provider classes
class BaseProvider(ABC):
    """
    Base class for all MCP providers.

    All providers share common lifecycle methods.
    """

    def __init__(self, name: str):
        """
        Initialize base provider.

        Args:
            name: Provider name
        """
        self.name = name
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize provider resources.

        Called when the provider is registered with an MCP server.
        Override to perform setup tasks.
        """
        self._initialized = True

    async def shutdown(self) -> None:
        """
        Cleanup provider resources.

        Called when the server is shutting down.
        Override to perform cleanup tasks.
        """
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized


class ResourceProvider(BaseProvider):
    """
    Base class for resource providers.

    Resource providers expose data from CommandCenter (projects, technologies,
    research tasks, etc.) as MCP resources.
    """

    @abstractmethod
    async def list_resources(self) -> List[Resource]:
        """
        List all resources this provider exposes.

        Returns:
            List of Resource objects

        Raises:
            MCPException: If listing fails
        """

    @abstractmethod
    async def read_resource(self, uri: str) -> ResourceContent:
        """
        Read specific resource by URI.

        Args:
            uri: Resource URI

        Returns:
            ResourceContent with resource data

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            MCPException: If reading fails
        """


class ToolProvider(BaseProvider):
    """
    Base class for tool providers.

    Tool providers expose CommandCenter functionality (analyze_project,
    create_task, etc.) as callable MCP tools.
    """

    @abstractmethod
    async def list_tools(self) -> List[Tool]:
        """
        List all tools this provider exposes.

        Returns:
            List of Tool objects

        Raises:
            MCPException: If listing fails
        """

    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute tool with given arguments.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            ToolResult with execution result

        Raises:
            ToolNotFoundError: If tool doesn't exist
            InvalidParamsError: If arguments are invalid
            MCPException: If execution fails
        """


class PromptProvider(BaseProvider):
    """
    Base class for prompt providers.

    Prompt providers expose prompt templates that can be used with AI assistants.
    """

    @abstractmethod
    async def list_prompts(self) -> List[Prompt]:
        """
        List all prompts this provider exposes.

        Returns:
            List of Prompt objects

        Raises:
            MCPException: If listing fails
        """

    @abstractmethod
    async def get_prompt(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> PromptResult:
        """
        Get rendered prompt template with arguments filled.

        Args:
            name: Prompt name
            arguments: Optional template arguments

        Returns:
            PromptResult with rendered messages

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            InvalidParamsError: If arguments are invalid
            MCPException: If rendering fails
        """
