"""Base MCP Server Template

This module provides a reusable foundation for building Model Context Protocol (MCP) servers.
It implements the MCP protocol specification with stdio transport, tool registry, and resource
provider interfaces.
"""

from .server import BaseMCPServer
from .protocol import MCPProtocol, MCPRequest, MCPResponse
from .transport import StdioTransport
from .registry import ToolRegistry, ResourceRegistry
from .utils import get_logger, load_config

__all__ = [
    'BaseMCPServer',
    'MCPProtocol',
    'MCPRequest',
    'MCPResponse',
    'StdioTransport',
    'ToolRegistry',
    'ResourceRegistry',
    'get_logger',
    'load_config',
]

__version__ = '1.0.0'
