"""MCP Registry System

Tool and Resource registry for MCP servers.
Provides registration, discovery, and invocation of tools and resources.
"""

from typing import Dict, List, Any, Callable, Optional, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
import inspect
from .utils import get_logger

logger = get_logger(__name__)


class ToolInputType(str, Enum):
    """Tool input schema types"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None

    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format"""
        schema = {
            'type': self.type,
            'description': self.description
        }
        if self.default is not None:
            schema['default'] = self.default
        return schema


@dataclass
class ToolDefinition:
    """Tool definition for MCP"""
    name: str
    description: str
    parameters: List[ToolParameter]
    handler: Callable[..., Awaitable[Any]]

    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP tool format"""
        # Build JSON schema for parameters
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_schema()
            if param.required:
                required.append(param.name)

        input_schema = {
            'type': 'object',
            'properties': properties
        }
        if required:
            input_schema['required'] = required

        return {
            'name': self.name,
            'description': self.description,
            'inputSchema': input_schema
        }


@dataclass
class ResourceDefinition:
    """Resource definition for MCP"""
    uri: str
    name: str
    description: str
    mime_type: str
    handler: Callable[..., Awaitable[Any]]

    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP resource format"""
        return {
            'uri': self.uri,
            'name': self.name,
            'description': self.description,
            'mimeType': self.mime_type
        }


class ToolRegistry:
    """Registry for MCP tools

    Manages tool registration, discovery, and invocation.
    """

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        logger.debug("ToolRegistry initialized")

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter],
        handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Register a new tool

        Args:
            name: Tool name (must be unique)
            description: Tool description
            parameters: List of tool parameters
            handler: Async function to handle tool calls

        Raises:
            ValueError: If tool name already registered
        """
        if name in self.tools:
            raise ValueError(f"Tool '{name}' already registered")

        # Validate handler is async
        if not inspect.iscoroutinefunction(handler):
            raise ValueError(f"Tool handler for '{name}' must be an async function")

        tool = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        )
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool

        Args:
            name: Tool name to remove
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Unregistered tool: {name}")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name

        Args:
            name: Tool name

        Returns:
            ToolDefinition or None if not found
        """
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools in MCP format

        Returns:
            List of tool definitions in MCP format
        """
        return [tool.to_mcp_format() for tool in self.tools.values()]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool by name

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
            Exception: Any exception raised by the tool handler
        """
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")

        logger.debug(f"Calling tool: {name} with arguments: {arguments}")

        try:
            # Validate required parameters
            required_params = [p.name for p in tool.parameters if p.required]
            missing = [p for p in required_params if p not in arguments]
            if missing:
                raise ValueError(f"Missing required parameters: {missing}")

            # Call handler with arguments
            result = await tool.handler(**arguments)
            logger.debug(f"Tool {name} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}", exc_info=True)
            raise

    def has_tool(self, name: str) -> bool:
        """Check if tool is registered

        Args:
            name: Tool name

        Returns:
            True if tool is registered
        """
        return name in self.tools


class ResourceRegistry:
    """Registry for MCP resources

    Manages resource registration, discovery, and access.
    """

    def __init__(self):
        self.resources: Dict[str, ResourceDefinition] = {}
        logger.debug("ResourceRegistry initialized")

    def register_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str,
        handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Register a new resource

        Args:
            uri: Resource URI (must be unique)
            name: Resource name
            description: Resource description
            mime_type: MIME type (e.g., 'application/json', 'text/plain')
            handler: Async function to handle resource reads

        Raises:
            ValueError: If URI already registered
        """
        if uri in self.resources:
            raise ValueError(f"Resource URI '{uri}' already registered")

        # Validate handler is async
        if not inspect.iscoroutinefunction(handler):
            raise ValueError(f"Resource handler for '{uri}' must be an async function")

        resource = ResourceDefinition(
            uri=uri,
            name=name,
            description=description,
            mime_type=mime_type,
            handler=handler
        )
        self.resources[uri] = resource
        logger.info(f"Registered resource: {uri}")

    def unregister_resource(self, uri: str) -> None:
        """Unregister a resource

        Args:
            uri: Resource URI to remove
        """
        if uri in self.resources:
            del self.resources[uri]
            logger.info(f"Unregistered resource: {uri}")

    def get_resource(self, uri: str) -> Optional[ResourceDefinition]:
        """Get resource definition by URI

        Args:
            uri: Resource URI

        Returns:
            ResourceDefinition or None if not found
        """
        return self.resources.get(uri)

    def list_resources(self) -> List[Dict[str, Any]]:
        """List all registered resources in MCP format

        Returns:
            List of resource definitions in MCP format
        """
        return [resource.to_mcp_format() for resource in self.resources.values()]

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource by URI

        Args:
            uri: Resource URI

        Returns:
            Resource content with metadata

        Raises:
            ValueError: If resource not found
            Exception: Any exception raised by the resource handler
        """
        resource = self.get_resource(uri)
        if resource is None:
            raise ValueError(f"Resource '{uri}' not found")

        logger.debug(f"Reading resource: {uri}")

        try:
            # Call handler
            content = await resource.handler()

            # Return in MCP format
            return {
                'contents': [{
                    'uri': uri,
                    'mimeType': resource.mime_type,
                    'text': content if isinstance(content, str) else str(content)
                }]
            }

        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
            raise

    def has_resource(self, uri: str) -> bool:
        """Check if resource is registered

        Args:
            uri: Resource URI

        Returns:
            True if resource is registered
        """
        return uri in self.resources
