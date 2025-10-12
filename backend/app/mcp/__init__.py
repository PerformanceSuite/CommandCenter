"""
Model Context Protocol (MCP) implementation for CommandCenter.

This package provides the core infrastructure for exposing CommandCenter's
capabilities (resources, tools, prompts) to AI assistants via the MCP protocol.
"""

from app.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    MCPProtocolHandler,
)
from app.mcp.server import MCPServer
from app.mcp.config import MCPServerConfig, MCPCapabilities

__all__ = [
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "MCPProtocolHandler",
    "MCPServer",
    "MCPServerConfig",
    "MCPCapabilities",
]
