"""
Consensus Detection for AI Arena Debates

Implements confidence-weighted voting and agreement detection
based on the ReConcile framework (ACL 2024).
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from ..agents import AgentResponse
from .state import ConsensusLevel

logger = structlog.get_logger(__name__)


@dataclass
class ConsensusResult:
    """Result of consensus analysis."""

    level: ConsensusLevel
    agreement_score: float  # 0.0 to 1.0
    weighted_confidence: float  # Confidence-weighted average
    majority_answer: str
    majority_count: int
    total_agents: int
    dissenting_responses: list[AgentResponse]

    @property
    def agreement_percentage(self) -> float:
        """Agreement as a percentage."""
        return self.agreement_score * 100


class ConsensusDetector:
    """
    Detects consensus among agent responses using confidence-weighted voting.

    Based on the ReConcile framework which demonstrates that confidence-weighted
    voting across diverse models achieves better consensus than simple majority.

    The algorithm:
    1. Normalize answers (lowercase, strip whitespace)
    2. Group responses by normalized answer
    3. Calculate confidence-weighted votes for each answer group
    4. Determine consensus level based on agreement and confidence thresholds
    """

    def __init__(
        self,
        agreement_threshold: float = 0.7,
        strong_confidence_threshold: int = 80,
        moderate_confidence_threshold: int = 60,
    ):
        """
        Initialize consensus detector.

        Args:
            agreement_threshold: Proportion of agents needed for consensus (0-1)
            strong_confidence_threshold: Minimum avg confidence for strong consensus
            moderate_confidence_threshold: Minimum avg confidence for moderate consensus
        """
        self.agreement_threshold = agreement_threshold
        self.strong_confidence_threshold = strong_confidence_threshold
        self.moderate_confidence_threshold = moderate_confidence_threshold

    def detect(self, responses: list[AgentResponse]) -> ConsensusResult:
        """
        Analyze responses and detect consensus level.

        Args:
            responses: List of agent responses to analyze

        Returns:
            ConsensusResult with consensus level and details
        """
        if not responses:
            return ConsensusResult(
                level=ConsensusLevel.DEADLOCK,
                agreement_score=0.0,
                weighted_confidence=0.0,
                majority_answer="",
                majority_count=0,
                total_agents=0,
                dissenting_responses=[],
            )

        # Group responses by normalized answer
        answer_groups = self._group_by_answer(responses)

        # Find the majority group
        majority_answer, majority_responses = max(
            answer_groups.items(),
            key=lambda x: self._calculate_group_weight(x[1]),
        )

        # Calculate metrics
        majority_count = len(majority_responses)
        total_agents = len(responses)
        agreement_score = majority_count / total_agents

        # Calculate confidence-weighted average for majority
        weighted_confidence = self._calculate_weighted_confidence(majority_responses)

        # Identify dissenting responses
        dissenting = [r for r in responses if r not in majority_responses]

        # Determine consensus level
        level = self._determine_level(
            agreement_score=agreement_score,
            weighted_confidence=weighted_confidence,
            total_agents=total_agents,
        )

        logger.info(
            "consensus_detected",
            level=level.value,
            agreement_score=round(agreement_score, 2),
            weighted_confidence=round(weighted_confidence, 1),
            majority_count=majority_count,
            total_agents=total_agents,
        )

        return ConsensusResult(
            level=level,
            agreement_score=agreement_score,
            weighted_confidence=weighted_confidence,
            majority_answer=majority_answer,
            majority_count=majority_count,
            total_agents=total_agents,
            dissenting_responses=dissenting,
        )

    def _group_by_answer(self, responses: list[AgentResponse]) -> dict[str, list[AgentResponse]]:
        """Group responses by normalized answer."""
        groups: dict[str, list[AgentResponse]] = {}

        for response in responses:
            # Normalize the answer for comparison
            normalized = self._normalize_answer(response.answer)

            if normalized not in groups:
                groups[normalized] = []
            groups[normalized].append(response)

        return groups

    def _normalize_answer(self, answer: str) -> str:
        """
        Normalize answer for comparison.

        This is a simple normalization - in practice, you might want
        semantic similarity comparison for more robust matching.
        """
        # Basic normalization: lowercase, strip, remove common prefixes
        normalized = answer.lower().strip()

        # Remove common answer prefixes
        prefixes_to_remove = [
            "i believe ",
            "i think ",
            "in my opinion, ",
            "my answer is ",
            "the answer is ",
            "yes, ",
            "no, ",
        ]
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :]

        return normalized.strip()

    def _calculate_group_weight(self, responses: list[AgentResponse]) -> float:
        """
        Calculate the weight of an answer group.

        Uses confidence-weighted voting where higher confidence
        responses contribute more to the group weight.
        """
        if not responses:
            return 0.0

        # Sum of confidence-weighted votes
        total_weight = sum(r.confidence / 100.0 for r in responses)
        return total_weight

    def _calculate_weighted_confidence(self, responses: list[AgentResponse]) -> float:
        """
        Calculate confidence-weighted average confidence.

        Responses with higher confidence contribute more to the average.
        """
        if not responses:
            return 0.0

        total_weight = sum(r.confidence for r in responses)
        weighted_sum = sum(r.confidence * r.confidence for r in responses)

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _determine_level(
        self,
        agreement_score: float,
        weighted_confidence: float,
        total_agents: int,
    ) -> ConsensusLevel:
        """Determine consensus level based on metrics."""
        # Need at least 2 agents for meaningful consensus
        if total_agents < 2:
            return ConsensusLevel.WEAK

        # Strong consensus: high agreement AND high confidence
        if (
            agreement_score >= self.agreement_threshold
            and weighted_confidence >= self.strong_confidence_threshold
        ):
            return ConsensusLevel.STRONG

        # Moderate consensus: good agreement with reasonable confidence
        if (
            agreement_score >= self.agreement_threshold
            and weighted_confidence >= self.moderate_confidence_threshold
        ):
            return ConsensusLevel.MODERATE

        # Weak consensus: majority agrees but confidence is low
        if agreement_score > 0.5:
            return ConsensusLevel.WEAK

        # Deadlock: no clear majority
        return ConsensusLevel.DEADLOCK

    def should_continue_debate(
        self,
        consensus_result: ConsensusResult,
        current_round: int,
        max_rounds: int,
    ) -> bool:
        """
        Determine if debate should continue.

        Args:
            consensus_result: Current consensus analysis
            current_round: Current round number (0-indexed)
            max_rounds: Maximum allowed rounds

        Returns:
            True if debate should continue, False if it should stop
        """
        # Stop if we've reached max rounds
        if current_round >= max_rounds - 1:
            return False

        # Stop if strong consensus reached
        if consensus_result.level == ConsensusLevel.STRONG:
            return False

        # Continue if deadlock or weak consensus - agents might converge
        return True
