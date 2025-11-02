"""
MCP server configuration and capability management.

Defines configuration schemas and server capability negotiation.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MCPCapabilities(BaseModel):
    """
    MCP server capabilities.

    Defines what capabilities this server supports during initialization.

    Attributes:
        resources: Whether server supports resources
        tools: Whether server supports tools
        prompts: Whether server supports prompts
        logging: Whether server supports logging
        experimental: Optional experimental capabilities
    """

    resources: bool = True
    tools: bool = True
    prompts: bool = True
    logging: bool = False
    experimental: Optional[Dict[str, bool]] = None


class MCPServerInfo(BaseModel):
    """
    MCP server information.

    Attributes:
        name: Server name
        version: Server version
        description: Optional server description
        vendor: Optional vendor information
    """

    name: str
    version: str
    description: Optional[str] = None
    vendor: Optional[str] = None


class MCPServerConfig(BaseModel):
    """
    MCP server configuration.

    Attributes:
        server_info: Server information
        capabilities: Server capabilities
        transport: Transport type (stdio, http, websocket)
        host: Host address (for HTTP/WebSocket)
        port: Port number (for HTTP/WebSocket)
        max_connections: Maximum concurrent connections
        timeout: Request timeout in seconds
        metadata: Optional additional metadata
    """

    server_info: MCPServerInfo
    capabilities: MCPCapabilities = Field(default_factory=MCPCapabilities)
    transport: str = "stdio"
    host: Optional[str] = None
    port: Optional[int] = None
    max_connections: int = 10
    timeout: int = 30
    metadata: Optional[Dict[str, str]] = None

    def model_post_init(self, __context) -> None:
        """Validate configuration after initialization."""
        if self.transport in ["http", "websocket"]:
            if not self.host or not self.port:
                raise ValueError(f"Host and port required for {self.transport} transport")


class MCPClientCapabilities(BaseModel):
    """
    MCP client capabilities (received during initialization).

    Attributes:
        roots: Whether client supports workspace roots
        sampling: Whether client supports sampling
        experimental: Optional experimental capabilities
    """

    roots: bool = False
    sampling: bool = False
    experimental: Optional[Dict[str, bool]] = None


class MCPInitializeParams(BaseModel):
    """
    Parameters for initialize request.

    Attributes:
        protocol_version: MCP protocol version
        capabilities: Client capabilities
        client_info: Client information
    """

    protocol_version: str
    capabilities: MCPClientCapabilities
    client_info: MCPServerInfo


class MCPInitializeResult(BaseModel):
    """
    Result of initialize request.

    Attributes:
        protocol_version: MCP protocol version
        capabilities: Server capabilities
        server_info: Server information
    """

    protocol_version: str = "2024-11-05"  # MCP protocol version
    capabilities: MCPCapabilities
    server_info: MCPServerInfo


class MCPServerRegistry:
    """
    Registry for MCP servers.

    Allows discovery and management of available MCP servers.
    """

    def __init__(self):
        """Initialize server registry."""
        self._servers: Dict[str, MCPServerConfig] = {}

    def register(self, server_id: str, config: MCPServerConfig) -> None:
        """
        Register MCP server.

        Args:
            server_id: Unique server identifier
            config: Server configuration

        Raises:
            ValueError: If server_id already registered
        """
        if server_id in self._servers:
            raise ValueError(f"Server {server_id} already registered")
        self._servers[server_id] = config

    def unregister(self, server_id: str) -> None:
        """
        Unregister MCP server.

        Args:
            server_id: Server identifier

        Raises:
            KeyError: If server_id not found
        """
        if server_id not in self._servers:
            raise KeyError(f"Server {server_id} not registered")
        del self._servers[server_id]

    def get(self, server_id: str) -> Optional[MCPServerConfig]:
        """
        Get server configuration.

        Args:
            server_id: Server identifier

        Returns:
            Server configuration or None if not found
        """
        return self._servers.get(server_id)

    def list(self) -> List[tuple[str, MCPServerConfig]]:
        """
        List all registered servers.

        Returns:
            List of (server_id, config) tuples
        """
        return list(self._servers.items())

    def list_by_capability(self, capability: str) -> List[tuple[str, MCPServerConfig]]:
        """
        List servers supporting specific capability.

        Args:
            capability: Capability name (resources, tools, prompts)

        Returns:
            List of (server_id, config) tuples
        """
        result = []
        for server_id, config in self._servers.items():
            if getattr(config.capabilities, capability, False):
                result.append((server_id, config))
        return result


# Global server registry instance
_registry = MCPServerRegistry()


def get_server_registry() -> MCPServerRegistry:
    """
    Get global server registry.

    Returns:
        Server registry instance
    """
    return _registry
