"""
Hypothesis Validator

Validates business hypotheses using AI Arena multi-model debates.
Integrates with the debate orchestrator to run structured validation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

import structlog

from ..agents import BaseAgent
from ..debate import ConsensusLevel, DebateConfig, DebateOrchestrator, DebateResult
from .schema import Hypothesis, HypothesisEvidence, HypothesisStatus, HypothesisValidationResult

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for hypothesis validation."""

    max_debate_rounds: int = 3
    consensus_threshold: float = 0.7
    confidence_threshold: int = 70
    timeout_seconds: float = 300.0
    parallel_responses: bool = True

    # Validation thresholds
    validation_threshold: float = 70.0  # Score above this = validated
    invalidation_threshold: float = 40.0  # Score below this = invalidated

    # Event callbacks
    on_round_complete: Callable[[int, list], None] | None = None
    on_validation_complete: Callable[[HypothesisValidationResult], None] | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


class HypothesisValidator:
    """
    Validates hypotheses using AI Arena debates.

    The validator:
    1. Converts hypotheses into debate questions
    2. Runs multi-model debates to evaluate the hypothesis
    3. Synthesizes debate results into validation outcomes
    4. Extracts evidence from agent responses
    5. Determines final validation status
    6. (NEW) Runs Chairman synthesis for authoritative final judgment

    Example:
        from libs.ai_arena import AgentRegistry, HypothesisValidator
        from libs.ai_arena.hypothesis import Hypothesis, HypothesisCreate
        from libs.llm_gateway import LLMGateway

        # Create gateway and agents
        gateway = LLMGateway()
        registry = AgentRegistry(gateway)
        agents = registry.create_default_team()

        # Create validator with gateway for chairman synthesis
        validator = HypothesisValidator(agents, llm_gateway=gateway)

        # Create and validate hypothesis
        hypothesis = Hypothesis(
            id="h1",
            statement="Enterprise customers will pay $2K/month for compliance",
            category="pricing",
            impact="high",
            risk="high",
            testability="medium",
            success_criteria="5 of 10 prospects confirm willingness to pay"
        )

        result = await validator.validate(hypothesis)
        print(f"Status: {result.status}")
        print(f"Score: {result.validation_score}%")
        print(f"Chairman: {result.chairman_summary}")  # NEW
    """

    def __init__(
        self,
        agents: list[BaseAgent],
        config: ValidationConfig | None = None,
        llm_gateway=None,
    ):
        """
        Initialize the hypothesis validator.

        Args:
            agents: List of agents to participate in validation debates
            config: Optional validation configuration
            llm_gateway: Optional LLM gateway for chairman synthesis
        """
        if not agents:
            raise ValueError("At least one agent is required for validation")

        self.agents = agents
        self.config = config or ValidationConfig()
        self.llm_gateway = llm_gateway

        # Create debate configuration with chairman enabled
        self._debate_config = DebateConfig(
            max_rounds=self.config.max_debate_rounds,
            consensus_threshold=self.config.consensus_threshold,
            confidence_threshold=self.config.confidence_threshold,
            timeout_seconds=self.config.timeout_seconds,
            parallel_responses=self.config.parallel_responses,
            enable_chairman=llm_gateway is not None,  # Enable if gateway provided
        )

    async def validate(
        self,
        hypothesis: Hypothesis,
        additional_context: str | None = None,
    ) -> HypothesisValidationResult:
        """
        Validate a hypothesis through AI Arena debate.

        Args:
            hypothesis: The hypothesis to validate
            additional_context: Optional extra context for the debate

        Returns:
            HypothesisValidationResult with validation outcome
        """
        validation_id = f"val_{uuid.uuid4().hex[:12]}"
        started_at = datetime.utcnow()

        logger.info(
            "hypothesis_validation_started",
            validation_id=validation_id,
            hypothesis_id=hypothesis.id,
            category=hypothesis.category.value,
        )

        # Update hypothesis status
        hypothesis.status = HypothesisStatus.VALIDATING
        hypothesis.updated_at = datetime.utcnow()

        # Build debate question
        question = hypothesis.to_debate_question()
        if additional_context:
            question += f"\n\n**Additional Context:** {additional_context}"

        # Add existing evidence to context
        if hypothesis.evidence:
            evidence_context = self._format_existing_evidence(hypothesis.evidence)
            question += f"\n\n**Existing Evidence:**\n{evidence_context}"

        # Run debate with chairman synthesis if gateway available
        orchestrator = DebateOrchestrator(
            self.agents,
            self._debate_config,
            llm_gateway=self.llm_gateway,
        )
        debate_result = await orchestrator.debate(question, hypothesis.context)

        # Process debate result
        result = self._process_debate_result(
            hypothesis=hypothesis,
            debate_result=debate_result,
            validation_id=validation_id,
            started_at=started_at,
        )

        # Update hypothesis with results
        self._update_hypothesis(hypothesis, result, debate_result)

        # Callback if configured
        if self.config.on_validation_complete:
            self.config.on_validation_complete(result)

        logger.info(
            "hypothesis_validation_completed",
            validation_id=validation_id,
            hypothesis_id=hypothesis.id,
            status=result.status.value,
            validation_score=round(result.validation_score, 1),
            consensus_reached=result.consensus_reached,
        )

        return result

    def _format_existing_evidence(self, evidence: list[HypothesisEvidence]) -> str:
        """Format existing evidence for debate context."""
        lines = []
        for ev in evidence:
            support_str = "Supporting" if ev.supports else "Contradicting"
            lines.append(f"- [{support_str}] {ev.content} (Source: {ev.source})")
        return "\n".join(lines)

    def _process_debate_result(
        self,
        hypothesis: Hypothesis,
        debate_result: DebateResult,
        validation_id: str,
        started_at: datetime,
    ) -> HypothesisValidationResult:
        """Process debate result into validation result."""
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()

        # Calculate validation score
        validation_score = self._calculate_validation_score(debate_result)

        # Determine status
        status = self._determine_status(validation_score, debate_result)

        # Extract evidence from responses
        new_evidence = self._extract_evidence(debate_result, hypothesis.id)

        # Generate recommendation
        recommendation = self._generate_recommendation(status, validation_score, debate_result)

        # Extract follow-up questions
        follow_up_questions = self._extract_follow_up_questions(debate_result)

        # Summarize reasoning
        reasoning_summary = self._summarize_reasoning(debate_result)

        return HypothesisValidationResult(
            hypothesis_id=hypothesis.id,
            status=status,
            validation_score=validation_score,
            debate_id=debate_result.debate_id,
            consensus_reached=debate_result.consensus_level
            in (ConsensusLevel.STRONG, ConsensusLevel.MODERATE),
            rounds_taken=debate_result.total_rounds,
            final_answer=debate_result.final_answer,
            reasoning_summary=reasoning_summary,
            new_evidence=new_evidence,
            recommendation=recommendation,
            follow_up_questions=follow_up_questions,
            total_cost=debate_result.total_cost,
            duration_seconds=duration,
            validated_at=completed_at,
            metadata={
                "validation_id": validation_id,
                "consensus_level": debate_result.consensus_level.value,
                "final_confidence": debate_result.final_confidence,
            },
        )

    def _calculate_validation_score(self, debate_result: DebateResult) -> float:
        """
        Calculate validation score from debate result.

        The score is based on:
        - Agent confidence in the hypothesis
        - Consensus level achieved
        - Whether agents support or reject the hypothesis
        """
        if not debate_result.rounds:
            return 50.0  # Neutral if no rounds completed

        final_round = debate_result.rounds[-1]
        if not final_round.responses:
            return 50.0

        # Base score from final confidence
        base_score = debate_result.final_confidence

        # Adjust based on consensus
        consensus_multiplier = {
            ConsensusLevel.STRONG: 1.0,
            ConsensusLevel.MODERATE: 0.9,
            ConsensusLevel.WEAK: 0.75,
            ConsensusLevel.DEADLOCK: 0.5,
        }
        multiplier = consensus_multiplier.get(debate_result.consensus_level, 0.5)

        # If rejecting, the score represents confidence in rejection
        # We still return a high score but change the status interpretation
        adjusted_score = base_score * multiplier

        # Store whether this is a rejection in the score context
        # Higher score = more confident in the assessment (either way)
        return min(100.0, max(0.0, adjusted_score))

    def _determine_status(
        self, validation_score: float, debate_result: DebateResult
    ) -> HypothesisStatus:
        """Determine hypothesis status from validation score and debate."""
        # Check the final answer for direction
        answer_lower = debate_result.final_answer.lower()
        reject_indicators = [
            "invalid",
            "likely false",
            "rejected",
            "no",
            "unlikely",
            "not supported",
        ]

        is_rejection = any(ind in answer_lower for ind in reject_indicators)

        if validation_score >= self.config.validation_threshold:
            if is_rejection:
                return HypothesisStatus.INVALIDATED
            return HypothesisStatus.VALIDATED
        elif validation_score <= self.config.invalidation_threshold:
            if is_rejection:
                return HypothesisStatus.INVALIDATED
            # Low score on support = needs more data
            return HypothesisStatus.NEEDS_MORE_DATA
        else:
            return HypothesisStatus.NEEDS_MORE_DATA

    def _extract_evidence(
        self, debate_result: DebateResult, hypothesis_id: str
    ) -> list[HypothesisEvidence]:
        """Extract evidence from debate responses."""
        evidence_list = []

        for round_data in debate_result.rounds:
            for response in round_data.responses:
                for ev in response.evidence:
                    evidence = HypothesisEvidence(
                        source=f"AI Arena - {response.agent_name}",
                        content=ev,
                        supports=response.confidence >= 60,  # High confidence = support
                        confidence=response.confidence,
                        collected_by=response.agent_name,
                        metadata={
                            "debate_id": debate_result.debate_id,
                            "round": round_data.round_number,
                            "model": response.model,
                        },
                    )
                    evidence_list.append(evidence)

        return evidence_list

    def _generate_recommendation(
        self,
        status: HypothesisStatus,
        validation_score: float,
        debate_result: DebateResult,
    ) -> str:
        """Generate actionable recommendation based on validation result."""
        recommendations = {
            HypothesisStatus.VALIDATED: (
                f"The hypothesis appears well-supported with {validation_score:.0f}% confidence. "
                "Consider proceeding with implementation while monitoring for changes. "
                "Continue to collect real-world evidence to confirm."
            ),
            HypothesisStatus.INVALIDATED: (
                f"The hypothesis appears to be contradicted with {validation_score:.0f}% confidence. "
                "Consider pivoting the approach or investigating the underlying assumptions. "
                "Review the dissenting views for alternative directions."
            ),
            HypothesisStatus.NEEDS_MORE_DATA: (
                f"The validation is inconclusive ({validation_score:.0f}% confidence). "
                "Consider conducting customer interviews, market research, or testing experiments "
                "to gather more definitive evidence before making decisions."
            ),
        }

        return recommendations.get(
            status,
            "Unable to determine a clear recommendation. Review the debate details for insights.",
        )

    def _extract_follow_up_questions(self, debate_result: DebateResult) -> list[str]:
        """Extract follow-up questions from debate responses."""
        questions = []

        # Look for questions in reasoning
        import re

        for round_data in debate_result.rounds:
            for response in round_data.responses:
                # Find questions in reasoning text
                found = re.findall(r"(?:^|\n)\s*[-•]\s*(.+\?)", response.reasoning)
                questions.extend(found)

                # Also look for "we need to know" patterns
                need_patterns = re.findall(
                    r"(?:need to|should|important to)\s+(?:know|understand|determine|find out)\s+(.+?)(?:\.|$)",
                    response.reasoning,
                    re.IGNORECASE,
                )
                questions.extend([f"What is {p.strip()}?" for p in need_patterns])

        # Deduplicate and limit
        unique_questions = list(dict.fromkeys(questions))
        return unique_questions[:5]

    def _summarize_reasoning(self, debate_result: DebateResult) -> str:
        """Create a summary of the debate reasoning."""
        # Use chairman synthesis if available (LLM Council Stage 4)
        if debate_result.chairman_synthesis:
            chairman = debate_result.chairman_synthesis
            summary = f"**Chairman Synthesis** (Confidence: {chairman.confidence}%)\n\n"
            summary += f"{chairman.summary}\n\n"
            if chairman.key_insights:
                summary += "**Key Insights:**\n"
                for insight in chairman.key_insights:
                    summary += f"- {insight}\n"
            if chairman.dissent_acknowledged:
                summary += f"\n**Dissenting Views Considered:** {chairman.dissent_acknowledged}"
            return summary

        # Fallback to agent-by-agent summary
        if not debate_result.rounds:
            return "No debate rounds completed."

        final_round = debate_result.rounds[-1]
        if not final_round.responses:
            return "No responses in final round."

        # Get key points from each agent
        points = []
        for response in final_round.responses:
            # Take first 200 chars of reasoning
            summary = response.reasoning[:200]
            if len(response.reasoning) > 200:
                summary += "..."
            points.append(f"**{response.agent_name}**: {summary}")

        return "\n\n".join(points)

    def _update_hypothesis(
        self,
        hypothesis: Hypothesis,
        result: HypothesisValidationResult,
        debate_result: DebateResult,
    ) -> None:
        """Update hypothesis with validation results."""
        hypothesis.status = result.status
        hypothesis.validation_score = result.validation_score
        hypothesis.validated_at = result.validated_at
        hypothesis.updated_at = datetime.utcnow()

        # Add new evidence
        for evidence in result.new_evidence:
            hypothesis.add_evidence(evidence)

        # Store debate result
        hypothesis.debate_results.append(debate_result.to_dict())


async def validate_hypothesis_quick(
    agents: list[BaseAgent],
    hypothesis: Hypothesis,
    max_rounds: int = 2,
) -> HypothesisValidationResult:
    """
    Convenience function for quick hypothesis validation.

    Args:
        agents: List of agents to participate
        hypothesis: Hypothesis to validate
        max_rounds: Maximum debate rounds (default 2 for speed)

    Returns:
        HypothesisValidationResult
    """
    config = ValidationConfig(max_debate_rounds=max_rounds)
    validator = HypothesisValidator(agents, config)
    return await validator.validate(hypothesis)
