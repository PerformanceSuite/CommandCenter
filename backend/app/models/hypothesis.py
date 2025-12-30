"""
Hypothesis model for research intelligence validation
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
    from app.models.debate import Debate
    from app.models.evidence import Evidence
    from app.models.project import Project
    from app.models.research_task import ResearchTask


class HypothesisCategory(str, enum.Enum):
    """Categories for hypothesis classification"""

    CUSTOMER = "customer"
    PROBLEM = "problem"
    SOLUTION = "solution"
    TECHNICAL = "technical"
    MARKET = "market"
    REGULATORY = "regulatory"
    COMPETITIVE = "competitive"
    GTM = "gtm"  # Go-to-market


class HypothesisStatus(str, enum.Enum):
    """Hypothesis validation status"""

    UNTESTED = "untested"
    VALIDATING = "validating"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    NEEDS_MORE_DATA = "needs_more_data"


class ImpactLevel(str, enum.Enum):
    """Impact level for hypothesis prioritization"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLevel(str, enum.Enum):
    """Risk level for hypothesis prioritization"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Hypothesis(Base):
    """Hypothesis for research intelligence validation

    Hypotheses are always attached to a research task (parent).
    They go through validation via multi-agent debates and
    accumulate evidence over time.
    """

    __tablename__ = "hypotheses"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys - always has a project and research task parent
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    research_task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("research_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core hypothesis data
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[HypothesisCategory] = mapped_column(
        SQLEnum(HypothesisCategory), nullable=False
    )
    status: Mapped[HypothesisStatus] = mapped_column(
        SQLEnum(HypothesisStatus), nullable=False, default=HypothesisStatus.UNTESTED
    )

    # Prioritization
    impact: Mapped[ImpactLevel] = mapped_column(
        SQLEnum(ImpactLevel), nullable=False, default=ImpactLevel.MEDIUM
    )
    risk: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel), nullable=False, default=RiskLevel.MEDIUM
    )
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Validation results
    validation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # KnowledgeBeast reference - indexed when validated
    knowledge_entry_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="hypotheses")
    research_task: Mapped["ResearchTask"] = relationship(
        "ResearchTask", back_populates="hypotheses"
    )
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="hypothesis", cascade="all, delete-orphan"
    )
    debates: Mapped[list["Debate"]] = relationship(
        "Debate", back_populates="hypothesis", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Hypothesis(id={self.id}, status='{self.status.value}', category='{self.category.value}')>"
