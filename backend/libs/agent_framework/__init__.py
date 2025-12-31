"""
Agent Framework - Unified agent execution and management.

This module provides:
- PromptImprover: Analyze and improve agent prompts
- PersonaStore: Manage agent persona definitions
- Persona: Data class for agent personas
- AgentExecutor: Execute agents in various environments (coming soon)
"""

from .persona_store import Persona, PersonaStore
from .prompt_improver import PromptAnalysis, PromptImprover

__all__ = [
    "PromptImprover",
    "PromptAnalysis",
    "PersonaStore",
    "Persona",
]
