"""
Hypothesis Schema Definitions

Pydantic models for hypothesis management and validation tracking.
Based on Lean Startup validation board methodology.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HypothesisStatus(str, Enum):
    """Current status of hypothesis validation."""

    UNTESTED = "untested"  # No validation attempted yet
    VALIDATING = "validating"  # Currently running validation
    VALIDATED = "validated"  # Evidence supports hypothesis
    INVALIDATED = "invalidated"  # Evidence contradicts hypothesis
    NEEDS_MORE_DATA = "needs_more_data"  # Inconclusive, need more research
    PIVOTED = "pivoted"  # Hypothesis was modified based on findings


class HypothesisCategory(str, Enum):
    """Category of hypothesis (Lean Startup classification)."""

    CUSTOMER = "customer"  # Who is the customer?
    PROBLEM = "problem"  # Is this a real problem?
    SOLUTION = "solution"  # Does our solution solve it?
    CHANNEL = "channel"  # How will we reach customers?
    REVENUE = "revenue"  # What will they pay?
    MARKET = "market"  # Market size and dynamics
    TECHNICAL = "technical"  # Technical feasibility
    REGULATORY = "regulatory"  # Legal/compliance requirements
    COMPETITIVE = "competitive"  # Competitive landscape
    GTM = "gtm"  # Go-to-market strategy


class ImpactLevel(str, Enum):
    """Business impact if hypothesis is wrong."""

    HIGH = "high"  # Critical to business viability
    MEDIUM = "medium"  # Significant but not fatal
    LOW = "low"  # Minor impact


class RiskLevel(str, Enum):
    """Risk that hypothesis is wrong."""

    HIGH = "high"  # High uncertainty
    MEDIUM = "medium"  # Some supporting evidence
    LOW = "low"  # Well-supported assumption


class TestabilityLevel(str, Enum):
    """How easily the hypothesis can be tested."""

    EASY = "easy"  # Can test quickly with existing data
    MEDIUM = "medium"  # Requires some research/interviews
    HARD = "hard"  # Requires significant effort or time


def _generate_evidence_id() -> str:
    """Generate a unique evidence ID."""
    import uuid

    return f"ev_{uuid.uuid4().hex[:12]}"


class HypothesisEvidence(BaseModel):
    """A piece of evidence supporting or contradicting a hypothesis."""

    id: str = Field(default_factory=_generate_evidence_id, description="Unique evidence ID")
    source: str = Field(..., description="Source of evidence (URL, interview, etc.)")
    content: str = Field(..., description="Summary of the evidence")
    supports: bool = Field(..., description="True if supports hypothesis, False if contradicts")
    confidence: int = Field(
        default=70,
        ge=0,
        le=100,
        description="Confidence in this evidence (0-100)",
    )
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    collected_by: str = Field(default="ai_arena", description="Who/what collected this evidence")
    metadata: dict[str, Any] = Field(default_factory=dict)


class HypothesisPriority(BaseModel):
    """Calculated priority based on Impact × Risk × Testability."""

    score: float = Field(..., ge=0, le=100, description="Priority score 0-100")
    impact_weight: float = Field(default=0.4, description="Weight for impact")
    risk_weight: float = Field(default=0.4, description="Weight for risk")
    testability_weight: float = Field(default=0.2, description="Weight for testability")

    @classmethod
    def calculate(
        cls,
        impact: ImpactLevel,
        risk: RiskLevel,
        testability: TestabilityLevel,
    ) -> HypothesisPriority:
        """Calculate priority score from levels."""
        # Convert to numeric values
        impact_map = {ImpactLevel.HIGH: 100, ImpactLevel.MEDIUM: 60, ImpactLevel.LOW: 30}
        risk_map = {RiskLevel.HIGH: 100, RiskLevel.MEDIUM: 60, RiskLevel.LOW: 30}
        # Easier to test = higher priority (inverse)
        testability_map = {
            TestabilityLevel.EASY: 100,
            TestabilityLevel.MEDIUM: 60,
            TestabilityLevel.HARD: 30,
        }

        weights = cls(score=0)  # Temporary to get weights
        score = (
            impact_map[impact] * weights.impact_weight
            + risk_map[risk] * weights.risk_weight
            + testability_map[testability] * weights.testability_weight
        )

        return cls(score=score)


class HypothesisCreate(BaseModel):
    """Schema for creating a new hypothesis."""

    statement: str = Field(
        ...,
        min_length=10,
        description="The hypothesis statement (e.g., 'Enterprise customers will pay $2K/month for X')",
    )
    category: HypothesisCategory
    impact: ImpactLevel
    risk: RiskLevel
    testability: TestabilityLevel
    success_criteria: str = Field(
        ...,
        min_length=5,
        description="What would validate this? (e.g., '5 of 10 prospects say they would pay')",
    )
    context: str | None = Field(default=None, description="Additional context for validation")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: dict[str, Any] = Field(default_factory=dict)


class HypothesisUpdate(BaseModel):
    """Schema for updating an existing hypothesis."""

    statement: str | None = None
    category: HypothesisCategory | None = None
    impact: ImpactLevel | None = None
    risk: RiskLevel | None = None
    testability: TestabilityLevel | None = None
    status: HypothesisStatus | None = None
    success_criteria: str | None = None
    context: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class Hypothesis(BaseModel):
    """Full hypothesis model with all fields."""

    id: str = Field(..., description="Unique hypothesis ID")
    statement: str = Field(..., description="The hypothesis statement")
    category: HypothesisCategory
    impact: ImpactLevel
    risk: RiskLevel
    testability: TestabilityLevel
    status: HypothesisStatus = Field(default=HypothesisStatus.UNTESTED)
    success_criteria: str = Field(..., description="What would validate this?")
    context: str | None = Field(default=None, description="Additional context")

    # Evidence tracking
    evidence: list[HypothesisEvidence] = Field(default_factory=list)
    supporting_count: int = Field(default=0, description="Count of supporting evidence")
    contradicting_count: int = Field(default=0, description="Count of contradicting evidence")

    # Priority
    priority: HypothesisPriority | None = None

    # Validation results
    debate_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Results from AI Arena debates",
    )
    validation_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Overall validation confidence 0-100",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    validated_at: datetime | None = None

    # Metadata
    tags: list[str] = Field(default_factory=list)
    linked_task_id: str | None = Field(default=None, description="Linked CommandCenter task")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Calculate priority after model creation."""
        if self.priority is None:
            self.priority = HypothesisPriority.calculate(self.impact, self.risk, self.testability)
        # Update evidence counts
        self.supporting_count = sum(1 for e in self.evidence if e.supports)
        self.contradicting_count = sum(1 for e in self.evidence if not e.supports)

    def add_evidence(self, evidence: HypothesisEvidence) -> None:
        """Add evidence to the hypothesis."""
        self.evidence.append(evidence)
        if evidence.supports:
            self.supporting_count += 1
        else:
            self.contradicting_count += 1
        self.updated_at = datetime.utcnow()

    def to_debate_question(self) -> str:
        """Convert hypothesis to a debate question."""
        return f"""Evaluate the following business hypothesis:

**Hypothesis:** {self.statement}

**Category:** {self.category.value}
**Success Criteria:** {self.success_criteria}

{f'**Context:** {self.context}' if self.context else ''}

Please analyze:
1. Is this hypothesis likely true or false based on available evidence and reasoning?
2. What are the key assumptions underlying this hypothesis?
3. What evidence would be most valuable to collect?
4. What are the main risks if this hypothesis is wrong?
"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Hypothesis:
        """Create from dictionary."""
        return cls.model_validate(data)


class HypothesisValidationResult(BaseModel):
    """Result of validating a hypothesis through AI Arena debate."""

    hypothesis_id: str
    status: HypothesisStatus
    validation_score: float = Field(ge=0, le=100, description="Confidence in validation 0-100")

    # Debate summary
    debate_id: str
    consensus_reached: bool
    rounds_taken: int
    final_answer: str
    reasoning_summary: str

    # Evidence collected
    new_evidence: list[HypothesisEvidence] = Field(default_factory=list)

    # Recommendations
    recommendation: str = Field(..., description="Action recommendation based on result")
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Questions for further research",
    )

    # Costs
    total_cost: float = Field(default=0.0, description="Total API cost for validation")
    duration_seconds: float = Field(default=0.0, description="Time taken for validation")

    # Timestamps
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Full debate result as dict (optional, for storage/retrieval)
    debate_result: dict[str, Any] | None = Field(
        default=None, description="Full debate result dict for detailed analysis"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump(mode="json")
