"""
MCP Server base implementation.

Provides the base MCPServer class that all MCP servers inherit from.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.mcp.config import (
    MCPCapabilities,
    MCPClientCapabilities,
    MCPInitializeParams,
    MCPInitializeResult,
    MCPServerConfig,
    MCPServerInfo,
)
from app.mcp.connection import MCPConnectionManager, MCPSession
from app.mcp.protocol import JSONRPCRequest
from app.mcp.providers.base import (
    PromptProvider,
    ResourceProvider,
    ToolProvider,
)
from app.mcp.utils import (
    InvalidParamsError,
    PromptNotFoundError,
    ResourceNotFoundError,
    ToolNotFoundError,
    get_mcp_logger,
)

logger = get_mcp_logger(__name__)


class MCPServer:
    """
    Base class for MCP servers.

    Provides core functionality for handling MCP protocol requests,
    managing providers, and coordinating client sessions.
    """

    def __init__(self, config: MCPServerConfig):
        """
        Initialize MCP server.

        Args:
            config: Server configuration
        """
        self.config = config
        self.server_info = config.server_info
        self.capabilities = config.capabilities

        # Provider storage
        self._resource_providers: List[ResourceProvider] = []
        self._tool_providers: List[ToolProvider] = []
        self._prompt_providers: List[PromptProvider] = []

        # Connection management
        self._connection_manager = MCPConnectionManager(
            max_connections=config.max_connections,
            session_timeout=config.timeout,
        )

        # Server state
        self._running = False
        self._initialized = False
        self._logger = logger

        # Register core handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register core MCP method handlers."""
        self._connection_manager.register_handler("initialize", self._handle_initialize)
        self._connection_manager.register_handler(
            "resources/list", self._handle_list_resources
        )
        self._connection_manager.register_handler(
            "resources/read", self._handle_read_resource
        )
        self._connection_manager.register_handler("tools/list", self._handle_list_tools)
        self._connection_manager.register_handler("tools/call", self._handle_call_tool)
        self._connection_manager.register_handler(
            "prompts/list", self._handle_list_prompts
        )
        self._connection_manager.register_handler(
            "prompts/get", self._handle_get_prompt
        )
        # Context management handlers
        self._connection_manager.register_handler("context/set", self._handle_context_set)
        self._connection_manager.register_handler("context/get", self._handle_context_get)
        self._connection_manager.register_handler("context/has", self._handle_context_has)
        self._connection_manager.register_handler(
            "context/delete", self._handle_context_delete
        )
        self._connection_manager.register_handler(
            "context/clear", self._handle_context_clear
        )
        self._connection_manager.register_handler("context/list", self._handle_context_list)

    # Provider management
    def register_resource_provider(self, provider: ResourceProvider) -> None:
        """
        Register a resource provider.

        Args:
            provider: ResourceProvider instance
        """
        self._resource_providers.append(provider)
        self._logger.info(f"Registered resource provider: {provider.name}")

    def register_tool_provider(self, provider: ToolProvider) -> None:
        """
        Register a tool provider.

        Args:
            provider: ToolProvider instance
        """
        self._tool_providers.append(provider)
        self._logger.info(f"Registered tool provider: {provider.name}")

    def register_prompt_provider(self, provider: PromptProvider) -> None:
        """
        Register a prompt provider.

        Args:
            provider: PromptProvider instance
        """
        self._prompt_providers.append(provider)
        self._logger.info(f"Registered prompt provider: {provider.name}")

    # Lifecycle methods
    async def initialize(self) -> None:
        """
        Initialize server and all providers.

        Called before server starts accepting connections.
        """
        if self._initialized:
            self._logger.warning("Server already initialized")
            return

        self._logger.info(f"Initializing server: {self.server_info.name}")

        # Initialize all providers
        for provider in self._resource_providers:
            await provider.initialize()

        for provider in self._tool_providers:
            await provider.initialize()

        for provider in self._prompt_providers:
            await provider.initialize()

        self._initialized = True
        self._logger.info("Server initialization complete")

    async def start(self) -> None:
        """
        Start the MCP server.

        Override this method to implement transport-specific startup logic.
        """
        if not self._initialized:
            await self.initialize()

        self._running = True
        self._logger.info(f"Server started: {self.server_info.name}")

    async def shutdown(self) -> None:
        """
        Shutdown server and cleanup resources.

        Called when server is stopping.
        """
        self._logger.info("Shutting down server")
        self._running = False

        # Shutdown all providers
        for provider in self._resource_providers:
            await provider.shutdown()

        for provider in self._tool_providers:
            await provider.shutdown()

        for provider in self._prompt_providers:
            await provider.shutdown()

        self._initialized = False
        self._logger.info("Server shutdown complete")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    def is_initialized(self) -> bool:
        """Check if server is initialized."""
        return self._initialized

    # Request handlers
    async def _handle_initialize(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle initialize request.

        Args:
            request: JSON-RPC request
            session: Client session

        Returns:
            Initialize result
        """
        try:
            params = MCPInitializeParams.model_validate(request.params or {})

            # Update session with client info
            session.update_client_info(params.client_info.model_dump())

            # Return server capabilities
            result = MCPInitializeResult(
                capabilities=self.capabilities,
                server_info=self.server_info,
            )

            self._logger.info(
                f"Session {session.session_id} initialized with client: "
                f"{params.client_info.name}"
            )

            return result.model_dump()

        except Exception as e:
            self._logger.error(f"Initialize error: {e}")
            raise InvalidParamsError(f"Invalid initialize params: {str(e)}")

    async def _handle_list_resources(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle resources/list request.

        Args:
            request: JSON-RPC request
            session: Client session

        Returns:
            List of resources
        """
        resources = []

        for provider in self._resource_providers:
            provider_resources = await provider.list_resources()
            resources.extend([r.model_dump() for r in provider_resources])

        return {"resources": resources}

    async def _handle_read_resource(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle resources/read request.

        Args:
            request: JSON-RPC request
            session: Client session

        Returns:
            Resource content

        Raises:
            InvalidParamsError: If URI not provided
            ResourceNotFoundError: If resource not found
        """
        params = request.params or {}
        uri = params.get("uri")

        if not uri:
            raise InvalidParamsError("URI parameter required")

        # Try each provider until one succeeds
        for provider in self._resource_providers:
            try:
                content = await provider.read_resource(uri)
                return content.model_dump()
            except ResourceNotFoundError:
                continue

        # No provider found the resource
        raise ResourceNotFoundError(uri)

    async def _handle_list_tools(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle tools/list request.

        Args:
            request: JSON-RPC request
            session: Client session

        Returns:
            List of tools
        """
        tools = []

        for provider in self._tool_providers:
            provider_tools = await provider.list_tools()
            tools.extend([t.model_dump() for t in provider_tools])

        return {"tools": tools}

    async def _handle_call_tool(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle tools/call request.

        Args:
            request: JSON-RPC request
            session: Client session

        Returns:
            Tool execution result

        Raises:
            InvalidParamsError: If name not provided
            ToolNotFoundError: If tool not found
        """
        params = request.params or {}
        name = params.get("name")
        arguments = params.get("arguments", {})

        if not name:
            raise InvalidParamsError("Tool name parameter required")

        # Try each provider until one succeeds
        for provider in self._tool_providers:
            try:
                result = await provider.call_tool(name, arguments)
                return result.model_dump()
            except ToolNotFoundError:
                continue

        # No provider found the tool
        raise ToolNotFoundError(name)

    async def _handle_list_prompts(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle prompts/list request.

        Args:
            request: JSON-RPC request
            session: Client session

        Returns:
            List of prompts
        """
        prompts = []

        for provider in self._prompt_providers:
            provider_prompts = await provider.list_prompts()
            prompts.extend([p.model_dump() for p in provider_prompts])

        return {"prompts": prompts}

    async def _handle_get_prompt(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle prompts/get request.

        Args:
            request: JSON-RPC request
            session: Client session

        Returns:
            Rendered prompt

        Raises:
            InvalidParamsError: If name not provided
            PromptNotFoundError: If prompt not found
        """
        params = request.params or {}
        name = params.get("name")
        arguments = params.get("arguments")

        if not name:
            raise InvalidParamsError("Prompt name parameter required")

        # Try each provider until one succeeds
        for provider in self._prompt_providers:
            try:
                result = await provider.get_prompt(name, arguments)
                return result.model_dump()
            except PromptNotFoundError:
                continue

        # No provider found the prompt
        raise PromptNotFoundError(name)

    # Context management handlers
    async def _handle_context_set(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle context/set request.

        Sets a context key-value pair for the current session.

        Args:
            request: JSON-RPC request with params: {key: str, value: Any}
            session: Client session

        Returns:
            Success confirmation

        Raises:
            InvalidParamsError: If key or value not provided
        """
        params = request.params or {}
        key = params.get("key")
        value = params.get("value")

        if not key:
            raise InvalidParamsError("Context key parameter required")

        if value is None:
            raise InvalidParamsError("Context value parameter required")

        session.set_context(key, value)
        self._logger.debug(f"Session {session.session_id} set context: {key}")

        return {"success": True, "key": key}

    async def _handle_context_get(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle context/get request.

        Gets a context value for the current session.

        Args:
            request: JSON-RPC request with params: {key: str, default: Any (optional)}
            session: Client session

        Returns:
            Context value

        Raises:
            InvalidParamsError: If key not provided
        """
        params = request.params or {}
        key = params.get("key")
        default = params.get("default")

        if not key:
            raise InvalidParamsError("Context key parameter required")

        value = session.get_context(key, default)
        self._logger.debug(f"Session {session.session_id} get context: {key}")

        return {"key": key, "value": value, "exists": session.has_context(key)}

    async def _handle_context_has(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle context/has request.

        Checks if a context key exists for the current session.

        Args:
            request: JSON-RPC request with params: {key: str}
            session: Client session

        Returns:
            Boolean indicating if key exists

        Raises:
            InvalidParamsError: If key not provided
        """
        params = request.params or {}
        key = params.get("key")

        if not key:
            raise InvalidParamsError("Context key parameter required")

        exists = session.has_context(key)
        self._logger.debug(f"Session {session.session_id} check context: {key} = {exists}")

        return {"key": key, "exists": exists}

    async def _handle_context_delete(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle context/delete request.

        Deletes a context key from the current session.

        Args:
            request: JSON-RPC request with params: {key: str}
            session: Client session

        Returns:
            Success confirmation

        Raises:
            InvalidParamsError: If key not provided
        """
        params = request.params or {}
        key = params.get("key")

        if not key:
            raise InvalidParamsError("Context key parameter required")

        deleted = session.delete_context(key)
        self._logger.debug(f"Session {session.session_id} delete context: {key} = {deleted}")

        return {"success": deleted, "key": key}

    async def _handle_context_clear(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle context/clear request.

        Clears all context from the current session.

        Args:
            request: JSON-RPC request (no params needed)
            session: Client session

        Returns:
            Success confirmation
        """
        session.clear_context()
        self._logger.info(f"Session {session.session_id} cleared all context")

        return {"success": True, "message": "All context cleared"}

    async def _handle_context_list(
        self, request: JSONRPCRequest, session: MCPSession
    ) -> Dict[str, Any]:
        """
        Handle context/list request.

        Lists all context keys and values for the current session.

        Args:
            request: JSON-RPC request (no params needed)
            session: Client session

        Returns:
            Dictionary of all context
        """
        context = session.get_all_context()
        self._logger.debug(f"Session {session.session_id} list context: {len(context)} items")

        return {"context": context, "count": len(context)}

    # Session management
    async def create_session(
        self, client_info: Optional[Dict[str, Any]] = None
    ) -> MCPSession:
        """
        Create new client session.

        Args:
            client_info: Optional client information

        Returns:
            New session
        """
        return await self._connection_manager.create_session(client_info)

    async def close_session(self, session_id: str) -> None:
        """
        Close client session.

        Args:
            session_id: Session identifier
        """
        await self._connection_manager.close_session(session_id)

    async def handle_message(self, session_id: str, message: str) -> Optional[str]:
        """
        Handle incoming message for a session.

        Args:
            session_id: Session identifier
            message: Raw JSON-RPC message

        Returns:
            Response message (or None for notifications)
        """
        return await self._connection_manager.handle_request(session_id, message)

    # Utility methods
    def get_capabilities(self) -> MCPCapabilities:
        """
        Get server capabilities.

        Returns:
            Server capabilities
        """
        return self.capabilities

    def get_server_info(self) -> MCPServerInfo:
        """
        Get server information.

        Returns:
            Server information
        """
        return self.server_info

    def get_stats(self) -> Dict[str, Any]:
        """
        Get server statistics.

        Returns:
            Dictionary with server stats
        """
        return {
            "server_name": self.server_info.name,
            "version": self.server_info.version,
            "running": self._running,
            "initialized": self._initialized,
            "active_sessions": self._connection_manager.get_active_sessions(),
            "resource_providers": len(self._resource_providers),
            "tool_providers": len(self._tool_providers),
            "prompt_providers": len(self._prompt_providers),
        }
