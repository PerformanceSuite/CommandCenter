"""
MCP provider interfaces for resources, tools, and prompts.

Providers expose CommandCenter capabilities to MCP clients.
"""

from app.mcp.providers.base import BaseProvider, PromptProvider, ResourceProvider, ToolProvider
from app.mcp.providers.commandcenter_prompts import CommandCenterPromptProvider
from app.mcp.providers.commandcenter_resources import CommandCenterResourceProvider
from app.mcp.providers.commandcenter_tools import CommandCenterToolProvider

__all__ = [
    "BaseProvider",
    "ResourceProvider",
    "ToolProvider",
    "PromptProvider",
    "CommandCenterResourceProvider",
    "CommandCenterToolProvider",
    "CommandCenterPromptProvider",
]
