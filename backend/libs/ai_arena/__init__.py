"""
AI Arena - Multi-Model Debate System

A system for strategic research and hypothesis validation using
multiple AI models (Claude, Gemini, GPT) in structured debates.

Example (Quick Debate):
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

Example (Hypothesis Validation - Phase 4):
    from libs.llm_gateway import LLMGateway
    from libs.ai_arena import AgentRegistry
    from libs.ai_arena.hypothesis import (
        Hypothesis,
        HypothesisCategory,
        HypothesisCreate,
        HypothesisRegistry,
        HypothesisValidator,
        ImpactLevel,
        RiskLevel,
        TestabilityLevel,
    )

    gateway = LLMGateway()
    registry = AgentRegistry(gateway)
    agents = registry.create_default_team()

    # Create hypothesis
    hypothesis_registry = HypothesisRegistry()
    hypothesis = hypothesis_registry.create(HypothesisCreate(
        statement="Enterprise customers will pay $2K/month for compliance",
        category=HypothesisCategory.PRICING,
        impact=ImpactLevel.HIGH,
        risk=RiskLevel.HIGH,
        testability=TestabilityLevel.MEDIUM,
        success_criteria="5 of 10 prospects confirm willingness to pay"
    ))

    # Validate through AI Arena debate
    validator = HypothesisValidator(agents)
    result = await validator.validate(hypothesis)

    print(f"Status: {result.status.value}")
    print(f"Score: {result.validation_score}%")
    print(f"Recommendation: {result.recommendation}")
"""

# Phase 4: Hypothesis Validation (import submodule for access)
from . import hypothesis
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
    # Hypothesis validation (Phase 4)
    "hypothesis",
]
