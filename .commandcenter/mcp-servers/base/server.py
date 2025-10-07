"""Base MCP Server

Core MCP server implementation that handles protocol, transport, and request routing.
Extensible base class for building custom MCP servers.
"""

import asyncio
from typing import Dict, Any, Optional
from .protocol import (
    MCPProtocol, MCPRequest, MCPResponse, MCPMethod, MCPErrorCode
)
from .transport import StdioTransport
from .registry import ToolRegistry, ResourceRegistry
from .utils import get_logger, load_config

logger = get_logger(__name__)


class BaseMCPServer:
    """Base MCP Server

    Provides core MCP server functionality including:
    - Protocol handling (JSON-RPC 2.0)
    - Transport layer (stdio)
    - Tool and resource registries
    - Request routing and handling
    - Lifecycle management
    """

    def __init__(self, name: str, version: str, config_path: Optional[str] = None):
        """Initialize MCP server

        Args:
            name: Server name
            version: Server version
            config_path: Path to configuration file (optional)
        """
        self.name = name
        self.version = version
        self.config_path = config_path

        # Core components
        self.protocol = MCPProtocol()
        self.transport = StdioTransport()
        self.tool_registry = ToolRegistry()
        self.resource_registry = ResourceRegistry()

        # Configuration
        self.config: Optional[Dict[str, Any]] = None
        if config_path:
            try:
                self.config = load_config(config_path)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Could not load configuration: {e}")

        # Set protocol info
        self.protocol.set_server_info(name, version)

        # Set transport message handler
        self.transport.set_message_handler(self._handle_message)

        logger.info(f"Initialized {name} v{version}")

    def _update_capabilities(self) -> None:
        """Update server capabilities based on registered tools and resources"""
        capabilities = {}

        # Tools capability
        if self.tool_registry.tools:
            capabilities['tools'] = {}

        # Resources capability
        if self.resource_registry.resources:
            capabilities['resources'] = {}

        self.protocol.set_capabilities(capabilities)

    async def _handle_message(self, message: str) -> str:
        """Handle incoming MCP message

        Args:
            message: Raw message string

        Returns:
            Response message string
        """
        try:
            # Parse message
            request = self.protocol.parse_message(message)
            logger.debug(f"Handling request: {request.method}")

            # Route to handler
            response = await self._route_request(request)

            # Format response
            return self.protocol.format_response(response)

        except ValueError as e:
            # Protocol/parsing error
            logger.error(f"Protocol error: {e}")
            error_response = MCPResponse.error_response(
                id=None,
                code=MCPErrorCode.PARSE_ERROR,
                message=str(e)
            )
            return self.protocol.format_response(error_response)

        except Exception as e:
            # Internal error
            logger.error(f"Internal error: {e}", exc_info=True)
            error_response = MCPResponse.error_response(
                id=None,
                code=MCPErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                data=str(e)
            )
            return self.protocol.format_response(error_response)

    async def _route_request(self, request: MCPRequest) -> MCPResponse:
        """Route request to appropriate handler

        Args:
            request: Parsed MCP request

        Returns:
            MCP response
        """
        method = request.method

        try:
            # Handle lifecycle methods
            if method == MCPMethod.INITIALIZE:
                result = self.protocol.handle_initialize(request.params or {})
                return MCPResponse.success(request.id, result)

            elif method == MCPMethod.INITIALIZED:
                # Notification, no response needed
                logger.info("Client initialized")
                return None

            elif method == MCPMethod.PING:
                return MCPResponse.success(request.id, {})

            elif method == MCPMethod.SHUTDOWN:
                logger.info("Shutdown requested")
                self.transport.stop()
                return MCPResponse.success(request.id, {})

            # Require initialization for all other methods
            self.protocol.require_initialized()

            # Handle tool methods
            if method == MCPMethod.TOOLS_LIST:
                tools = self.tool_registry.list_tools()
                return MCPResponse.success(request.id, {'tools': tools})

            elif method == MCPMethod.TOOLS_CALL:
                params = request.params or {}
                tool_name = params.get('name')
                arguments = params.get('arguments', {})

                if not tool_name:
                    return MCPResponse.error_response(
                        request.id,
                        MCPErrorCode.INVALID_PARAMS,
                        "Missing required parameter: name"
                    )

                try:
                    result = await self.tool_registry.call_tool(tool_name, arguments)
                    return MCPResponse.success(request.id, {'result': result})
                except ValueError as e:
                    return MCPResponse.error_response(
                        request.id,
                        MCPErrorCode.TOOL_NOT_FOUND,
                        str(e)
                    )
                except Exception as e:
                    return MCPResponse.error_response(
                        request.id,
                        MCPErrorCode.TOOL_EXECUTION_ERROR,
                        str(e)
                    )

            # Handle resource methods
            elif method == MCPMethod.RESOURCES_LIST:
                resources = self.resource_registry.list_resources()
                return MCPResponse.success(request.id, {'resources': resources})

            elif method == MCPMethod.RESOURCES_READ:
                params = request.params or {}
                uri = params.get('uri')

                if not uri:
                    return MCPResponse.error_response(
                        request.id,
                        MCPErrorCode.INVALID_PARAMS,
                        "Missing required parameter: uri"
                    )

                try:
                    result = await self.resource_registry.read_resource(uri)
                    return MCPResponse.success(request.id, result)
                except ValueError as e:
                    return MCPResponse.error_response(
                        request.id,
                        MCPErrorCode.RESOURCE_NOT_FOUND,
                        str(e)
                    )
                except Exception as e:
                    return MCPResponse.error_response(
                        request.id,
                        MCPErrorCode.RESOURCE_READ_ERROR,
                        str(e)
                    )

            # Unknown method
            else:
                return MCPResponse.error_response(
                    request.id,
                    MCPErrorCode.METHOD_NOT_FOUND,
                    f"Method not found: {method}"
                )

        except ValueError as e:
            # Validation error (e.g., not initialized)
            return MCPResponse.error_response(
                request.id,
                MCPErrorCode.SERVER_NOT_INITIALIZED,
                str(e)
            )

    async def run(self) -> None:
        """Run the MCP server

        Starts the transport and begins processing messages.
        Blocks until server is shut down.
        """
        logger.info(f"Starting {self.name} v{self.version}")

        # Update capabilities before starting
        self._update_capabilities()

        # Start transport
        await self.transport.start()

        logger.info("Server stopped")

    def send_progress(self, progress: float, total: float, message: str = "") -> None:
        """Send progress notification

        Args:
            progress: Current progress value
            total: Total progress value
            message: Optional progress message
        """
        params = {
            'progress': progress,
            'total': total
        }
        if message:
            params['message'] = message

        self.transport.send_notification(MCPMethod.PROGRESS, params)

    def send_message(self, level: str, message: str) -> None:
        """Send message notification

        Args:
            level: Message level (debug, info, warning, error)
            message: Message text
        """
        self.transport.send_notification(
            MCPMethod.MESSAGE,
            {'level': level, 'message': message}
        )
