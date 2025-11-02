"""
MCP provider interfaces for resources, tools, and prompts.

Providers expose CommandCenter capabilities to MCP clients.
"""

from app.mcp.providers.base import (
    BaseProvider,
    ResourceProvider,
    ToolProvider,
    PromptProvider,
)
from app.mcp.providers.commandcenter_resources import (
    CommandCenterResourceProvider,
)
from app.mcp.providers.commandcenter_tools import CommandCenterToolProvider
from app.mcp.providers.commandcenter_prompts import CommandCenterPromptProvider

__all__ = [
    "BaseProvider",
    "ResourceProvider",
    "ToolProvider",
    "PromptProvider",
    "CommandCenterResourceProvider",
    "CommandCenterToolProvider",
    "CommandCenterPromptProvider",
]
