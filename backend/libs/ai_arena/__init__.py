"""
AI Arena - Multi-Model Debate System

A system for strategic research and hypothesis validation using
multiple AI models (Claude, Gemini, GPT) in structured debates.

Example:
    from libs.llm_gateway import LLMGateway
    from libs.ai_arena import AgentRegistry, AnalystAgent

    gateway = LLMGateway()
    registry = AgentRegistry(gateway)

    # Create default debate team
    registry.create_default_team()

    # Or create individual agents
    analyst = AnalystAgent(gateway)
    response = await analyst.respond("What is the market size for X?")
    print(response.answer)
    print(f"Confidence: {response.confidence}%")
"""

from .agents import (
    AgentConfig,
    AgentResponse,
    AnalystAgent,
    BaseAgent,
    CriticAgent,
    ResearcherAgent,
    StrategistAgent,
)
from .registry import AGENT_TYPES, AgentRegistry

__all__ = [
    # Registry
    "AgentRegistry",
    "AGENT_TYPES",
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
