"""
AI Arena Debate Protocol

Multi-round debate orchestration with consensus detection.

Example:
    from libs.ai_arena import AgentRegistry
    from libs.ai_arena.debate import DebateOrchestrator, DebateConfig

    # Create agents
    registry = AgentRegistry(gateway)
    agents = registry.create_default_team()

    # Configure debate
    config = DebateConfig(max_rounds=3, consensus_threshold=0.7)

    # Run debate
    orchestrator = DebateOrchestrator(agents, config)
    result = await orchestrator.debate(
        question="Should we expand into Europe?",
        context="Current revenue is $10M from US.",
    )

    print(f"Answer: {result.final_answer}")
    print(f"Consensus: {result.consensus_level.value}")
"""

from .consensus import ConsensusDetector, ConsensusResult
from .orchestrator import DebateError, DebateOrchestrator, DebateTimeoutError, run_quick_debate
from .prompts import DiscussionPromptGenerator
from .state import ConsensusLevel, DebateConfig, DebateResult, DebateRound, DebateStatus

__all__ = [
    # Orchestrator
    "DebateOrchestrator",
    "run_quick_debate",
    # State
    "DebateConfig",
    "DebateResult",
    "DebateRound",
    "DebateStatus",
    "ConsensusLevel",
    # Consensus
    "ConsensusDetector",
    "ConsensusResult",
    # Prompts
    "DiscussionPromptGenerator",
    # Exceptions
    "DebateError",
    "DebateTimeoutError",
]
