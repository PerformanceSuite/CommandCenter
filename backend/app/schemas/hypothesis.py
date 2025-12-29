"""
Pydantic schemas for Hypothesis API endpoints.

These schemas adapt the ai_arena hypothesis models for REST API use.
"""

from datetime import datetime
from typing import Any

from libs.ai_arena.hypothesis.schema import (
    HypothesisCategory,
    HypothesisStatus,
    ImpactLevel,
    RiskLevel,
    TestabilityLevel,
)
from pydantic import BaseModel, ConfigDict, Field

# Request Schemas


class HypothesisValidateRequest(BaseModel):
    """Request to validate a hypothesis via AI debate."""

    max_rounds: int = Field(default=3, ge=1, le=5, description="Maximum debate rounds")
    agents: list[str] = Field(
        default=["analyst", "researcher", "critic"],
        description="Agent types to include in debate",
    )


class HypothesisListParams(BaseModel):
    """Query parameters for listing hypotheses."""

    status: HypothesisStatus | None = None
    category: HypothesisCategory | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# Response Schemas


class HypothesisEvidenceResponse(BaseModel):
    """Evidence item in API response."""

    id: str
    source: str
    content: str
    supports: bool
    confidence: int
    collected_at: datetime
    collected_by: str

    model_config = ConfigDict(from_attributes=True)


class HypothesisSummaryResponse(BaseModel):
    """Hypothesis summary for list views."""

    id: str
    statement: str
    category: HypothesisCategory
    status: HypothesisStatus
    priority_score: float = Field(description="Calculated priority 0-100")
    evidence_count: int
    validation_score: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HypothesisDetailResponse(HypothesisSummaryResponse):
    """Full hypothesis details including evidence."""

    impact: ImpactLevel
    risk: RiskLevel
    testability: TestabilityLevel
    success_criteria: str
    context: str | None = None
    tags: list[str] = []
    evidence: list[HypothesisEvidenceResponse] = []
    validated_at: datetime | None = None
    metadata: dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class HypothesisListResponse(BaseModel):
    """Paginated list of hypotheses."""

    items: list[HypothesisSummaryResponse]
    total: int
    limit: int
    offset: int


class HypothesisStatsResponse(BaseModel):
    """Dashboard statistics."""

    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    average_validation_score: float
    validated_count: int
    invalidated_count: int
    needs_data_count: int
    untested_count: int


# Validation Task Schemas


class ValidationTaskResponse(BaseModel):
    """Response when starting a validation task."""

    task_id: str
    hypothesis_id: str
    status: str = "started"
    message: str = "Validation started"


class ValidationStatusResponse(BaseModel):
    """Current status of a validation task."""

    task_id: str
    hypothesis_id: str
    status: str  # running, completed, failed
    current_round: int = 0
    max_rounds: int = 3
    responses_count: int = 0
    consensus_level: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None


class ValidationResultResponse(BaseModel):
    """Final validation result."""

    hypothesis_id: str
    status: HypothesisStatus
    validation_score: float
    consensus_reached: bool
    rounds_taken: int
    final_answer: str
    reasoning_summary: str
    recommendation: str
    follow_up_questions: list[str] = []
    duration_seconds: float
    total_cost: float
    validated_at: datetime


# Debate Response Schemas


class AgentResponseSchema(BaseModel):
    """Response from an AI agent in a debate round."""

    answer: str
    reasoning: str
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    evidence: list[str] = []
    agent_name: str
    model: str


class DebateRoundSchema(BaseModel):
    """A single round of debate responses."""

    round_number: int
    responses: list[AgentResponseSchema]
    consensus_level: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    metadata: dict[str, Any] = {}


class DebateResultResponse(BaseModel):
    """Full debate result with all rounds."""

    debate_id: str
    question: str
    rounds: list[DebateRoundSchema]
    final_answer: str
    final_confidence: float
    consensus_level: str
    dissenting_views: list[AgentResponseSchema] = []
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    total_cost: float = 0.0
    error_message: str | None = None


# Evidence Explorer Schemas


class EvidenceItemResponse(BaseModel):
    """Evidence item with associated hypothesis info."""

    id: str
    hypothesis_id: str
    hypothesis_statement: str
    source: str
    content: str
    supports: bool
    confidence: int
    collected_at: datetime
    collected_by: str
    metadata: dict[str, Any] = {}


class EvidenceListResponse(BaseModel):
    """Paginated list of evidence items."""

    items: list[EvidenceItemResponse]
    total: int
    limit: int
    offset: int


class EvidenceStatsResponse(BaseModel):
    """Statistics about all evidence."""

    total: int
    supporting: int
    contradicting: int
    average_confidence: float
    by_source_type: dict[str, int]
    by_collector: dict[str, int]
