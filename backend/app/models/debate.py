"""
Debate model for multi-agent hypothesis validation
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.hypothesis import Hypothesis


class DebateStatus(str, enum.Enum):
    """Status of a debate"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ConsensusLevel(str, enum.Enum):
    """Level of consensus reached in debate"""

    STRONG = "strong"  # All agents agree
    MODERATE = "moderate"  # Majority agrees
    WEAK = "weak"  # Slight majority
    DEADLOCK = "deadlock"  # No consensus


class DebateVerdict(str, enum.Enum):
    """Final verdict from debate"""

    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    NEEDS_MORE_DATA = "needs_more_data"


class Debate(Base):
    """Multi-agent debate for hypothesis validation

    Debates orchestrate multiple AI agents to evaluate
    a hypothesis from different perspectives. Results
    include consensus level, verdict, and gap analysis.
    """

    __tablename__ = "debates"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to hypothesis
    hypothesis_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hypotheses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Debate configuration
    status: Mapped[DebateStatus] = mapped_column(
        SQLEnum(DebateStatus), nullable=False, default=DebateStatus.PENDING
    )
    rounds_requested: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    rounds_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agents_used: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # ["analyst", "researcher", "strategist", "critic"]

    # Results
    consensus_level: Mapped[Optional[ConsensusLevel]] = mapped_column(
        SQLEnum(ConsensusLevel), nullable=True
    )
    final_verdict: Mapped[Optional[DebateVerdict]] = mapped_column(
        SQLEnum(DebateVerdict), nullable=True
    )
    verdict_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Gap analysis and follow-up suggestions
    gap_analysis: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Structured missing info
    suggested_research: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Suggested follow-up tasks

    # Full transcript stored in KnowledgeBeast for RAG
    knowledge_entry_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    hypothesis: Mapped["Hypothesis"] = relationship("Hypothesis", back_populates="debates")

    def __repr__(self) -> str:
        return (
            f"<Debate(id={self.id}, status='{self.status.value}', verdict='{self.final_verdict}')>"
        )
