"""
Evidence model for hypothesis validation
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.hypothesis import Hypothesis


class EvidenceSourceType(str, enum.Enum):
    """Source types for evidence"""

    RESEARCH_FINDING = "research_finding"  # From research agent runs
    KNOWLEDGE_BASE = "knowledge_base"  # From KnowledgeBeast RAG
    MANUAL = "manual"  # User-provided
    EXTERNAL = "external"  # External sources (URLs, papers, etc.)


class EvidenceStance(str, enum.Enum):
    """Evidence stance relative to hypothesis"""

    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    NEUTRAL = "neutral"


class Evidence(Base):
    """Evidence supporting or contradicting a hypothesis

    Evidence is collected from various sources:
    - Research findings from agent runs
    - KnowledgeBeast knowledge base queries
    - Manual user input
    - External sources
    """

    __tablename__ = "evidence"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to hypothesis
    hypothesis_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hypotheses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Evidence content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Source tracking
    source_type: Mapped[EvidenceSourceType] = mapped_column(
        SQLEnum(EvidenceSourceType), nullable=False
    )
    source_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # finding_id, KB doc ID, or URL

    # Stance and confidence
    stance: Mapped[EvidenceStance] = mapped_column(SQLEnum(EvidenceStance), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    hypothesis: Mapped["Hypothesis"] = relationship("Hypothesis", back_populates="evidence")

    def __repr__(self) -> str:
        return f"<Evidence(id={self.id}, stance='{self.stance.value}', source='{self.source_type.value}')>"
