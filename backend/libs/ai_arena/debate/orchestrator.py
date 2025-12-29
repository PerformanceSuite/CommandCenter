"""
Debate Orchestrator for AI Arena

Manages multi-round debates between AI agents, coordinating
responses, detecting consensus, and compiling final results.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import structlog

from ..agents import AgentResponse, BaseAgent
from .consensus import ConsensusDetector
from .prompts import DiscussionPromptGenerator
from .state import ConsensusLevel, DebateConfig, DebateResult, DebateRound, DebateStatus

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


class DebateError(Exception):
    """Base exception for debate errors."""

    pass


class DebateTimeoutError(DebateError):
    """Debate exceeded time limit."""

    pass


class DebateOrchestrator:
    """
    Orchestrates multi-round debates between AI agents.

    The orchestrator:
    1. Collects responses from all agents in parallel
    2. Analyzes consensus after each round
    3. Generates follow-up prompts incorporating previous responses
    4. Continues until consensus is reached or max rounds exceeded
    5. Compiles final result with synthesized answer

    Example:
        from libs.ai_arena import AgentRegistry
        from libs.ai_arena.debate import DebateOrchestrator

        registry = AgentRegistry(gateway)
        registry.create_default_team()

        orchestrator = DebateOrchestrator(registry.list_agents())
        result = await orchestrator.debate(
            question="Should we expand into the European market?",
            context="Current revenue is $10M, primarily from US customers.",
        )

        print(f"Answer: {result.final_answer}")
        print(f"Consensus: {result.consensus_level.value}")
        print(f"Confidence: {result.final_confidence}%")
    """

    def __init__(
        self,
        agents: list[BaseAgent],
        config: DebateConfig | None = None,
    ):
        """
        Initialize the debate orchestrator.

        Args:
            agents: List of agents participating in the debate
            config: Optional debate configuration
        """
        if not agents:
            raise ValueError("At least one agent is required for a debate")

        self.agents = agents
        self.config = config or DebateConfig()
        self.consensus_detector = ConsensusDetector(
            agreement_threshold=self.config.consensus_threshold,
            strong_confidence_threshold=self.config.confidence_threshold,
        )
        self.prompt_generator = DiscussionPromptGenerator()

    async def debate(
        self,
        question: str,
        context: str | None = None,
        debate_id: str | None = None,
    ) -> DebateResult:
        """
        Run a full debate on a question.

        Args:
            question: The question or hypothesis to debate
            context: Optional additional context
            debate_id: Optional custom debate ID

        Returns:
            DebateResult with final answer and all round data

        Raises:
            DebateTimeoutError: If debate exceeds timeout
            DebateError: For other debate failures
        """
        debate_id = debate_id or str(uuid.uuid4())
        started_at = datetime.utcnow()
        rounds: list[DebateRound] = []
        total_cost = 0.0

        logger.info(
            "debate_started",
            debate_id=debate_id,
            question_preview=question[:100],
            agent_count=len(self.agents),
            max_rounds=self.config.max_rounds,
        )

        try:
            # Run debate rounds
            for round_num in range(self.config.max_rounds):
                round_started = datetime.utcnow()

                # Generate prompts for this round
                if round_num == 0:
                    # Initial round - no previous context
                    previous_responses = None
                else:
                    # Follow-up rounds - include previous responses
                    previous_responses = rounds[-1].responses if rounds else None

                # Collect responses from all agents
                responses, round_cost = await self._collect_responses(
                    question=question,
                    context=context,
                    previous_responses=previous_responses,
                    round_num=round_num,
                )
                total_cost += round_cost

                # Analyze consensus
                consensus_result = self.consensus_detector.detect(responses)

                # Create round record
                round_data = DebateRound(
                    round_number=round_num,
                    responses=responses,
                    consensus_level=consensus_result.level,
                    started_at=round_started,
                    completed_at=datetime.utcnow(),
                    metadata={
                        "agreement_score": consensus_result.agreement_score,
                        "weighted_confidence": consensus_result.weighted_confidence,
                    },
                )
                rounds.append(round_data)

                logger.info(
                    "debate_round_completed",
                    debate_id=debate_id,
                    round_number=round_num + 1,
                    consensus_level=consensus_result.level.value,
                    agreement_score=round(consensus_result.agreement_score, 2),
                )

                # Check if we should stop
                if not self.consensus_detector.should_continue_debate(
                    consensus_result, round_num, self.config.max_rounds
                ):
                    break

            # Compile final result
            result = self._compile_result(
                debate_id=debate_id,
                question=question,
                rounds=rounds,
                started_at=started_at,
                total_cost=total_cost,
            )

            logger.info(
                "debate_completed",
                debate_id=debate_id,
                total_rounds=len(rounds),
                final_consensus=result.consensus_level.value,
                final_confidence=round(result.final_confidence, 1),
                duration_seconds=result.duration_seconds,
                total_cost=round(total_cost, 4),
            )

            return result

        except asyncio.TimeoutError as e:
            logger.error("debate_timeout", debate_id=debate_id)
            return self._create_failed_result(
                debate_id=debate_id,
                question=question,
                rounds=rounds,
                started_at=started_at,
                status=DebateStatus.TIMEOUT,
                error_message=str(e),
                total_cost=total_cost,
            )
        except Exception as e:
            logger.error("debate_failed", debate_id=debate_id, error=str(e))
            return self._create_failed_result(
                debate_id=debate_id,
                question=question,
                rounds=rounds,
                started_at=started_at,
                status=DebateStatus.FAILED,
                error_message=str(e),
                total_cost=total_cost,
            )

    async def _collect_responses(
        self,
        question: str,
        context: str | None,
        previous_responses: list[AgentResponse] | None,
        round_num: int,
    ) -> tuple[list[AgentResponse], float]:
        """
        Collect responses from all agents.

        Returns:
            Tuple of (responses, total_cost)
        """
        if self.config.parallel_responses:
            # Collect in parallel for speed
            tasks = [
                self._get_agent_response(agent, question, context, previous_responses)
                for agent in self.agents
            ]

            # Apply timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.timeout_seconds,
            )

            responses = []
            total_cost = 0.0

            for result in results:
                if isinstance(result, Exception):
                    logger.warning("agent_response_failed", error=str(result))
                else:
                    response, cost = result
                    responses.append(response)
                    total_cost += cost

            return responses, total_cost
        else:
            # Collect sequentially
            responses = []
            total_cost = 0.0

            for agent in self.agents:
                try:
                    response, cost = await self._get_agent_response(
                        agent, question, context, previous_responses
                    )
                    responses.append(response)
                    total_cost += cost
                except Exception as e:
                    logger.warning(
                        "agent_response_failed",
                        agent=agent.name,
                        error=str(e),
                    )

            return responses, total_cost

    async def _get_agent_response(
        self,
        agent: BaseAgent,
        question: str,
        context: str | None,
        previous_responses: list[AgentResponse] | None,
    ) -> tuple[AgentResponse, float]:
        """
        Get response from a single agent.

        Returns:
            Tuple of (response, cost)
        """
        response = await agent.respond(
            question=question,
            context=context,
            previous_responses=previous_responses,
        )

        # Extract cost from the gateway response metadata if available
        # For now, we estimate based on token counts
        # In production, this would come from the LLMGateway
        cost = 0.0  # Cost is tracked by the LLMGateway metrics

        return response, cost

    def _compile_result(
        self,
        debate_id: str,
        question: str,
        rounds: list[DebateRound],
        started_at: datetime,
        total_cost: float,
    ) -> DebateResult:
        """Compile the final debate result."""
        if not rounds:
            return self._create_failed_result(
                debate_id=debate_id,
                question=question,
                rounds=rounds,
                started_at=started_at,
                status=DebateStatus.FAILED,
                error_message="No rounds completed",
                total_cost=total_cost,
            )

        # Get final round consensus
        final_round = rounds[-1]
        final_consensus = self.consensus_detector.detect(final_round.responses)

        # Determine final answer from majority
        final_answer = final_consensus.majority_answer
        if not final_answer and final_round.responses:
            # Fallback to highest confidence response
            best_response = max(final_round.responses, key=lambda r: r.confidence)
            final_answer = best_response.answer

        return DebateResult(
            debate_id=debate_id,
            question=question,
            rounds=rounds,
            final_answer=final_answer,
            final_confidence=final_consensus.weighted_confidence,
            consensus_level=final_consensus.level,
            dissenting_views=final_consensus.dissenting_responses,
            status=DebateStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            total_cost=total_cost,
        )

    def _create_failed_result(
        self,
        debate_id: str,
        question: str,
        rounds: list[DebateRound],
        started_at: datetime,
        status: DebateStatus,
        error_message: str,
        total_cost: float,
    ) -> DebateResult:
        """Create a failed debate result."""
        return DebateResult(
            debate_id=debate_id,
            question=question,
            rounds=rounds,
            final_answer="",
            final_confidence=0.0,
            consensus_level=ConsensusLevel.DEADLOCK,
            dissenting_views=[],
            status=status,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            total_cost=total_cost,
            error_message=error_message,
        )


async def run_quick_debate(
    agents: list[BaseAgent],
    question: str,
    context: str | None = None,
    max_rounds: int = 2,
) -> DebateResult:
    """
    Convenience function to run a quick debate.

    Args:
        agents: List of agents to participate
        question: Question to debate
        context: Optional context
        max_rounds: Maximum rounds (default 2 for speed)

    Returns:
        DebateResult
    """
    config = DebateConfig(max_rounds=max_rounds)
    orchestrator = DebateOrchestrator(agents, config)
    return await orchestrator.debate(question, context)
