"""
Model Context Protocol (MCP) implementation for CommandCenter.

This package provides the core infrastructure for exposing CommandCenter's
capabilities (resources, tools, prompts) to AI assistants via the MCP protocol.
"""

from app.mcp.config import MCPCapabilities, MCPServerConfig
from app.mcp.protocol import JSONRPCError, JSONRPCRequest, JSONRPCResponse, MCPProtocolHandler
from app.mcp.server import MCPServer

__all__ = [
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "MCPProtocolHandler",
    "MCPServer",
    "MCPServerConfig",
    "MCPCapabilities",
]
