"""
AI Arena Agents

Specialized AI agents for multi-model debate and hypothesis validation.
"""

from .analyst import AnalystAgent
from .base import AgentConfig, AgentResponse, BaseAgent
from .critic import CriticAgent
from .researcher import ResearcherAgent
from .strategist import StrategistAgent

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentConfig",
    "AgentResponse",
    # Specialized agents
    "AnalystAgent",
    "ResearcherAgent",
    "StrategistAgent",
    "CriticAgent",
]
