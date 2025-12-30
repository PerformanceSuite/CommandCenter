"""
ResearchFinding model for individual findings from research agent runs
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.research_task import ResearchTask


class FindingType(str, enum.Enum):
    """Types of research findings"""

    FACT = "fact"  # Verified factual information
    CLAIM = "claim"  # Unverified assertion
    INSIGHT = "insight"  # Analysis or interpretation
    QUESTION = "question"  # Open question raised
    RECOMMENDATION = "recommendation"  # Suggested action


class ResearchFinding(Base):
    """Individual findings from research agent runs

    Findings are discrete pieces of information extracted
    from research task execution. They are indexed in
    KnowledgeBeast for RAG-based retrieval.
    """

    __tablename__ = "research_findings"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to research task
    research_task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("research_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Finding content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    finding_type: Mapped[FindingType] = mapped_column(SQLEnum(FindingType), nullable=False)

    # Agent attribution
    agent_role: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Which agent produced this

    # Confidence and sources
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    sources: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # Array of source URLs/references

    # KnowledgeBeast reference
    knowledge_entry_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    research_task: Mapped["ResearchTask"] = relationship(
        "ResearchTask", back_populates="research_findings"
    )

    def __repr__(self) -> str:
        return f"<ResearchFinding(id={self.id}, type='{self.finding_type.value}', agent='{self.agent_role}')>"
