"""
Pydantic schemas for Intelligence Integration (Research Hub)

Schemas for:
- Hypothesis management and validation
- Evidence collection and linking
- Debate orchestration and results
- Research findings indexing
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.debate import ConsensusLevel, DebateStatus, DebateVerdict
from app.models.evidence import EvidenceSourceType, EvidenceStance
from app.models.hypothesis import HypothesisCategory, HypothesisStatus, ImpactLevel, RiskLevel
from app.models.research_finding import FindingType

# ============================================================================
# Hypothesis Schemas
# ============================================================================


class HypothesisBase(BaseModel):
    """Base schema for hypothesis"""

    statement: str = Field(..., min_length=10, description="The hypothesis statement")
    category: HypothesisCategory = Field(..., description="Hypothesis category")
    impact: ImpactLevel = Field(default=ImpactLevel.MEDIUM, description="Impact level")
    risk: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Risk level")


class HypothesisCreate(HypothesisBase):
    """Schema for creating a hypothesis under a research task"""

    pass


class QuickHypothesisCreate(HypothesisBase):
    """Schema for quick hypothesis creation (auto-creates parent task)"""

    context: Optional[str] = Field(
        None, description="Optional context for auto-generated research task"
    )


class HypothesisUpdate(BaseModel):
    """Schema for updating a hypothesis"""

    statement: Optional[str] = Field(None, min_length=10)
    category: Optional[HypothesisCategory] = None
    status: Optional[HypothesisStatus] = None
    impact: Optional[ImpactLevel] = None
    risk: Optional[RiskLevel] = None
    priority_score: Optional[float] = Field(None, ge=0.0, le=100.0)


class HypothesisInDB(HypothesisBase):
    """Schema for hypothesis in database"""

    id: int
    project_id: int
    research_task_id: int
    status: HypothesisStatus
    priority_score: float
    validation_score: Optional[float] = None
    knowledge_entry_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HypothesisResponse(HypothesisInDB):
    """Schema for hypothesis API response"""

    evidence_count: int = 0
    debate_count: int = 0


class HypothesisListResponse(BaseModel):
    """Schema for hypothesis list response"""

    total: int
    items: list[HypothesisResponse]


class QuickHypothesisResponse(BaseModel):
    """Response for quick hypothesis creation"""

    hypothesis_id: int
    research_task_id: int
    hypothesis: HypothesisResponse


# ============================================================================
# Evidence Schemas
# ============================================================================


class EvidenceBase(BaseModel):
    """Base schema for evidence"""

    content: str = Field(..., min_length=1, description="Evidence content")
    stance: EvidenceStance = Field(..., description="Evidence stance")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class EvidenceCreate(EvidenceBase):
    """Schema for creating evidence manually"""

    source_type: EvidenceSourceType = EvidenceSourceType.MANUAL
    source_id: Optional[str] = None


class EvidenceFromSuggestion(BaseModel):
    """Schema for accepting suggested evidence"""

    suggestion_indices: list[int] = Field(..., description="Indices of suggestions to accept")


class EvidenceInDB(EvidenceBase):
    """Schema for evidence in database"""

    id: int
    hypothesis_id: int
    source_type: EvidenceSourceType
    source_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceResponse(EvidenceInDB):
    """Schema for evidence API response"""

    pass


class EvidenceListResponse(BaseModel):
    """Schema for evidence list response"""

    total: int
    items: list[EvidenceResponse]


class EvidenceSuggestion(BaseModel):
    """Schema for AI-suggested evidence"""

    content: str
    source_type: EvidenceSourceType
    source_id: Optional[str] = None
    suggested_stance: EvidenceStance
    confidence: float
    relevance_score: float
    source_collection: str  # findings, hypotheses, or evidence


class SuggestedEvidenceResponse(BaseModel):
    """Response with suggested evidence from KB"""

    suggestions: list[EvidenceSuggestion]
    query_used: str


# ============================================================================
# Debate Schemas
# ============================================================================


class DebateCreate(BaseModel):
    """Schema for starting a validation debate"""

    agents: list[str] = Field(
        default=["analyst", "researcher", "strategist", "critic"],
        description="Agent roles to participate in debate",
    )
    rounds: int = Field(default=3, ge=1, le=10, description="Number of debate rounds")


class DebateInDB(BaseModel):
    """Schema for debate in database"""

    id: int
    hypothesis_id: int
    status: DebateStatus
    rounds_requested: int
    rounds_completed: int
    agents_used: Optional[list[str]] = None
    consensus_level: Optional[ConsensusLevel] = None
    final_verdict: Optional[DebateVerdict] = None
    verdict_reasoning: Optional[str] = None
    gap_analysis: Optional[dict[str, Any]] = None
    suggested_research: Optional[dict[str, Any]] = None
    knowledge_entry_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DebateResponse(DebateInDB):
    """Schema for debate API response"""

    pass


class DebateStartResponse(BaseModel):
    """Response when starting a debate"""

    debate_id: int
    status: DebateStatus


class GapSuggestion(BaseModel):
    """A suggested research task from gap analysis"""

    title: str
    description: str
    priority: str  # high, medium, low
    estimated_effort: str  # low, medium, high


class SuggestedTasksResponse(BaseModel):
    """Response with suggested research tasks from gap analysis"""

    debate_id: int
    suggestions: list[GapSuggestion]


class CreateTaskFromGapRequest(BaseModel):
    """Request to create a research task from a gap suggestion"""

    suggestion_index: int = Field(..., ge=0)


class CreateTaskFromGapResponse(BaseModel):
    """Response after creating a task from gap analysis"""

    research_task_id: int
    title: str


# ============================================================================
# Research Finding Schemas
# ============================================================================


class ResearchFindingBase(BaseModel):
    """Base schema for research finding"""

    content: str = Field(..., min_length=1)
    finding_type: FindingType
    agent_role: str = Field(..., min_length=1, max_length=100)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    sources: Optional[list[str]] = None


class ResearchFindingCreate(ResearchFindingBase):
    """Schema for creating a research finding"""

    pass


class ResearchFindingInDB(ResearchFindingBase):
    """Schema for research finding in database"""

    id: int
    research_task_id: int
    knowledge_entry_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchFindingResponse(ResearchFindingInDB):
    """Schema for research finding API response"""

    pass


class ResearchFindingListResponse(BaseModel):
    """Schema for research finding list response"""

    total: int
    items: list[ResearchFindingResponse]


class IndexFindingsResponse(BaseModel):
    """Response after indexing findings to KB"""

    indexed_count: int
    task_id: int


# ============================================================================
# Intelligence Dashboard Schemas
# ============================================================================


class IntelligenceSummary(BaseModel):
    """Combined intelligence stats for a project"""

    research_tasks: dict[str, Any] = Field(default_factory=lambda: {"total": 0, "by_status": {}})
    hypotheses: dict[str, Any] = Field(
        default_factory=lambda: {
            "total": 0,
            "validated": 0,
            "invalidated": 0,
            "needs_data": 0,
            "untested": 0,
        }
    )
    knowledge_base: dict[str, Any] = Field(
        default_factory=lambda: {
            "documents": 0,
            "findings_indexed": 0,
            "hypotheses_indexed": 0,
        }
    )
    gaps: dict[str, Any] = Field(default_factory=lambda: {"open_count": 0, "oldest_gap": None})


class NeedsAttentionItem(BaseModel):
    """Hypothesis or task needing attention"""

    id: int
    type: str  # hypothesis or task
    title: str
    reason: str  # why it needs attention
    priority: str
    created_at: datetime


class NeedsAttentionResponse(BaseModel):
    """Response with items needing attention"""

    items: list[NeedsAttentionItem]
    total: int


class RecentValidation(BaseModel):
    """Recent validation activity"""

    hypothesis_id: int
    statement: str
    verdict: Optional[DebateVerdict]
    validation_score: Optional[float]
    completed_at: datetime


class RecentValidationsResponse(BaseModel):
    """Response with recent validations"""

    validations: list[RecentValidation]


# ============================================================================
# Validation Context Schema
# ============================================================================


class ValidationContext(BaseModel):
    """Context package for debate agents"""

    hypothesis_id: int
    statement: str
    category: HypothesisCategory
    impact: ImpactLevel
    risk: RiskLevel

    # Parent task context
    task_id: int
    task_title: str
    task_description: Optional[str] = None

    # Existing evidence
    evidence: list[EvidenceResponse] = []

    # RAG results from KB
    related_findings: list[dict[str, Any]] = []
    related_hypotheses: list[dict[str, Any]] = []
    contradicting_evidence: list[dict[str, Any]] = []
