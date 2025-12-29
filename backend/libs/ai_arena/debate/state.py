"""
Debate State Management

Data structures for tracking debate progress, rounds, and results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..agents import AgentResponse


class ConsensusLevel(str, Enum):
    """Level of consensus reached in a debate."""

    STRONG = "strong"  # All agents agree with high confidence
    MODERATE = "moderate"  # Majority agrees with reasonable confidence
    WEAK = "weak"  # Slight majority or low confidence agreement
    DEADLOCK = "deadlock"  # No clear consensus


class DebateStatus(str, Enum):
    """Current status of a debate."""

    PENDING = "pending"  # Not yet started
    IN_PROGRESS = "in_progress"  # Currently running
    COMPLETED = "completed"  # Finished with result
    FAILED = "failed"  # Error during execution
    TIMEOUT = "timeout"  # Exceeded time limit


@dataclass
class DebateRound:
    """A single round of debate responses."""

    round_number: int
    responses: list[AgentResponse]
    consensus_level: ConsensusLevel | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert round to dictionary."""
        return {
            "round_number": self.round_number,
            "responses": [r.to_dict() for r in self.responses],
            "consensus_level": self.consensus_level.value if self.consensus_level else None,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DebateRound:
        """Create round from dictionary."""
        return cls(
            round_number=data["round_number"],
            responses=[AgentResponse.from_dict(r) for r in data["responses"]],
            consensus_level=(
                ConsensusLevel(data["consensus_level"]) if data.get("consensus_level") else None
            ),
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
            metadata=data.get("metadata", {}),
        )

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence across all responses."""
        if not self.responses:
            return 0.0
        return sum(r.confidence for r in self.responses) / len(self.responses)

    @property
    def confidence_spread(self) -> float:
        """Calculate the spread (max - min) of confidence scores."""
        if not self.responses:
            return 0.0
        confidences = [r.confidence for r in self.responses]
        return max(confidences) - min(confidences)


@dataclass
class ChairmanSynthesis:
    """Final synthesis from the chairman model."""

    model: str
    summary: str
    final_verdict: str
    key_insights: list[str]
    dissent_acknowledged: str
    confidence: float
    cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "summary": self.summary,
            "final_verdict": self.final_verdict,
            "key_insights": self.key_insights,
            "dissent_acknowledged": self.dissent_acknowledged,
            "confidence": self.confidence,
            "cost": self.cost,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChairmanSynthesis:
        """Create from dictionary."""
        return cls(
            model=data["model"],
            summary=data["summary"],
            final_verdict=data["final_verdict"],
            key_insights=data.get("key_insights", []),
            dissent_acknowledged=data.get("dissent_acknowledged", ""),
            confidence=data.get("confidence", 0.0),
            cost=data.get("cost", 0.0),
        )


@dataclass
class DebateResult:
    """Final result of a completed debate."""

    debate_id: str
    question: str
    rounds: list[DebateRound]
    final_answer: str
    final_confidence: float
    consensus_level: ConsensusLevel
    dissenting_views: list[AgentResponse]
    status: DebateStatus
    started_at: datetime
    completed_at: datetime | None = None
    total_cost: float = 0.0
    error_message: str | None = None
    chairman_synthesis: ChairmanSynthesis | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "debate_id": self.debate_id,
            "question": self.question,
            "rounds": [r.to_dict() for r in self.rounds],
            "final_answer": self.final_answer,
            "final_confidence": self.final_confidence,
            "consensus_level": self.consensus_level.value,
            "dissenting_views": [r.to_dict() for r in self.dissenting_views],
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_cost": self.total_cost,
            "error_message": self.error_message,
            "chairman_synthesis": self.chairman_synthesis.to_dict()
            if self.chairman_synthesis
            else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DebateResult:
        """Create result from dictionary."""
        chairman_data = data.get("chairman_synthesis")
        return cls(
            debate_id=data["debate_id"],
            question=data["question"],
            rounds=[DebateRound.from_dict(r) for r in data["rounds"]],
            final_answer=data["final_answer"],
            final_confidence=data["final_confidence"],
            consensus_level=ConsensusLevel(data["consensus_level"]),
            dissenting_views=[AgentResponse.from_dict(r) for r in data["dissenting_views"]],
            status=DebateStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
            total_cost=data.get("total_cost", 0.0),
            error_message=data.get("error_message"),
            chairman_synthesis=ChairmanSynthesis.from_dict(chairman_data)
            if chairman_data
            else None,
            metadata=data.get("metadata", {}),
        )

    @property
    def total_rounds(self) -> int:
        """Get total number of rounds."""
        return len(self.rounds)

    @property
    def duration_seconds(self) -> float | None:
        """Calculate debate duration in seconds."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def get_all_responses(self) -> list[AgentResponse]:
        """Get all responses across all rounds."""
        responses = []
        for round_data in self.rounds:
            responses.extend(round_data.responses)
        return responses

    def get_agent_responses(self, agent_name: str) -> list[AgentResponse]:
        """Get all responses from a specific agent."""
        return [r for r in self.get_all_responses() if r.agent_name == agent_name]


@dataclass
class DebateConfig:
    """Configuration for a debate session."""

    max_rounds: int = 3
    consensus_threshold: float = 0.7  # Agreement level needed for consensus
    confidence_threshold: int = 70  # Minimum confidence for strong consensus
    timeout_seconds: float = 300.0  # 5 minute timeout
    parallel_responses: bool = True  # Whether to collect responses in parallel
    include_critic: bool = True  # Whether to include devil's advocate
    # Chairman synthesis configuration (LLM Council Stage 4)
    enable_chairman: bool = True  # Whether to use chairman synthesis
    chairman_provider: str = "claude"  # Provider for chairman model (uses best available)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "max_rounds": self.max_rounds,
            "consensus_threshold": self.consensus_threshold,
            "confidence_threshold": self.confidence_threshold,
            "timeout_seconds": self.timeout_seconds,
            "parallel_responses": self.parallel_responses,
            "include_critic": self.include_critic,
            "enable_chairman": self.enable_chairman,
            "chairman_provider": self.chairman_provider,
            "metadata": self.metadata,
        }
