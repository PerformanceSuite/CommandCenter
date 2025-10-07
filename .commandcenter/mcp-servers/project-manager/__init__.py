"""Project Manager MCP Server

Main orchestration server for CommandCenter projects.
Provides tools for workflow coordination, agent spawning, and project analysis.
"""

from .server import ProjectManagerServer

__all__ = ['ProjectManagerServer']

__version__ = '1.0.0'
