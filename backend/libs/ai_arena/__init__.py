"""
AI Arena - Multi-Model Debate System

A system for strategic research and hypothesis validation using
multiple AI models (Claude, Gemini, GPT) in structured debates.

Example:
    from libs.llm_gateway import LLMGateway
    from libs.ai_arena import AgentRegistry, DebateOrchestrator

    gateway = LLMGateway()
    registry = AgentRegistry(gateway)

    # Create default debate team
    agents = registry.create_default_team()

    # Run a debate
    orchestrator = DebateOrchestrator(agents)
    result = await orchestrator.debate(
        question="Should we expand into Europe?",
        context="Current revenue is $10M from US customers.",
    )

    print(f"Answer: {result.final_answer}")
    print(f"Consensus: {result.consensus_level.value}")
    print(f"Confidence: {result.final_confidence}%")
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
from .debate import (
    ConsensusDetector,
    ConsensusLevel,
    ConsensusResult,
    DebateConfig,
    DebateError,
    DebateOrchestrator,
    DebateResult,
    DebateRound,
    DebateStatus,
    DebateTimeoutError,
    run_quick_debate,
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
    # Debate orchestration
    "DebateOrchestrator",
    "DebateConfig",
    "DebateResult",
    "DebateRound",
    "DebateStatus",
    "ConsensusLevel",
    "ConsensusDetector",
    "ConsensusResult",
    "DebateError",
    "DebateTimeoutError",
    "run_quick_debate",
]
