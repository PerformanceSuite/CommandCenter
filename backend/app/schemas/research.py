"""
Pydantic schemas for Research Task and Knowledge Entry endpoints
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.research_task import TaskStatus


class ResearchTaskBase(BaseModel):
    """Base schema for research task"""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    technology_id: Optional[int] = None
    repository_id: Optional[int] = None
    user_notes: Optional[str] = None
    findings: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0)


class ResearchTaskCreate(ResearchTaskBase):
    """Schema for creating a research task"""

    pass


class ResearchTaskUpdate(BaseModel):
    """Schema for updating a research task"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    user_notes: Optional[str] = None
    findings: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    actual_hours: Optional[int] = Field(None, ge=0)


class ResearchTaskInDB(ResearchTaskBase):
    """Schema for research task in database"""

    id: int
    uploaded_documents: Optional[list] = None
    completed_at: Optional[datetime] = None
    progress_percentage: int
    actual_hours: Optional[int] = None
    metadata_: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchTaskResponse(ResearchTaskInDB):
    """Schema for research task API response"""

    pass


class KnowledgeEntryBase(BaseModel):
    """Base schema for knowledge entry"""

    title: str = Field(..., min_length=1, max_length=512)
    content: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    technology_id: Optional[int] = None
    source_file: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None


class KnowledgeEntryCreate(KnowledgeEntryBase):
    """Schema for creating a knowledge entry"""

    vector_db_id: Optional[str] = None
    embedding_model: Optional[str] = None


class KnowledgeEntryUpdate(BaseModel):
    """Schema for updating a knowledge entry"""

    title: Optional[str] = Field(None, min_length=1, max_length=512)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    technology_id: Optional[int] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class KnowledgeEntryInDB(KnowledgeEntryBase):
    """Schema for knowledge entry in database"""

    id: int
    vector_db_id: Optional[str] = None
    embedding_model: Optional[str] = None
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    confidence_score: Optional[float] = None
    relevance_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeEntryResponse(KnowledgeEntryInDB):
    """Schema for knowledge entry API response"""

    pass


class KnowledgeSearchRequest(BaseModel):
    """Schema for knowledge base search request"""

    query: str = Field(..., min_length=1)
    category: Optional[str] = None
    technology_id: Optional[int] = None
    limit: int = Field(default=5, ge=1, le=50)


class KnowledgeSearchResult(BaseModel):
    """Schema for knowledge search result"""

    content: str
    title: str
    category: str
    technology_id: Optional[int] = None
    source_file: Optional[str] = None
    score: float
    metadata: dict


class ResearchTaskListResponse(BaseModel):
    """Schema for research task list response"""

    total: int
    items: list[ResearchTaskResponse]
    page: int = 1
    page_size: int = 50


# ============================================================================
# Research Agent Orchestration Schemas (Phase 2)
# ============================================================================


class AgentTaskRequest(BaseModel):
    """Request schema for individual agent task"""

    role: str = Field(
        ...,
        description="Agent role: technology_scout, deep_researcher, comparator, integrator, monitor",
    )
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=32000)


class MultiAgentLaunchRequest(BaseModel):
    """Request schema for launching multiple agents"""

    tasks: list[AgentTaskRequest]
    max_concurrent: int = Field(default=3, ge=1, le=10)
    project_id: int


class TechnologyDeepDiveRequest(BaseModel):
    """Request schema for technology deep dive"""

    technology_name: str = Field(..., min_length=1)
    research_questions: Optional[list[str]] = None
    project_id: int
    model: Optional[str] = None
    provider: Optional[str] = None


class AgentResultMetadata(BaseModel):
    """Metadata about agent execution"""

    agent_role: str
    model: str
    provider: str
    usage: dict
    execution_time_seconds: float


class AgentResult(BaseModel):
    """Result from individual agent"""

    data: dict
    metadata: Optional[AgentResultMetadata] = None
    error: Optional[str] = None


class ResearchOrchestrationResponse(BaseModel):
    """Response schema for research orchestration task"""

    task_id: str
    status: str  # pending|running|completed|failed
    technology: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[list[AgentResult]] = None
    summary: Optional[str] = None
    error: Optional[str] = None


class TechnologyMonitorRequest(BaseModel):
    """Request schema for technology monitoring"""

    technology_id: int
    sources: list[str] = Field(
        default=["hackernews", "github"]
    )  # hackernews, github, arxiv
    days_back: int = Field(default=7, ge=1, le=30)


class MonitoringAlert(BaseModel):
    """Alert from monitoring system"""

    type: str  # security|breaking_change|deprecation|opportunity
    severity: str  # low|medium|high|critical
    description: str
    action_required: Optional[str] = None
    source_url: Optional[str] = None


class TechnologyMonitorResponse(BaseModel):
    """Response schema for technology monitoring"""

    technology_id: int
    technology_name: str
    period: str
    hackernews: Optional[dict] = None
    github: Optional[dict] = None
    arxiv: Optional[dict] = None
    alerts: list[MonitoringAlert] = []
    last_updated: datetime


class ModelInfo(BaseModel):
    """Information about an AI model"""

    model_id: str
    provider: str
    tier: str  # premium|standard|economy|local
    cost_per_1m_tokens: Optional[float] = None
    max_tokens: int
    description: Optional[str] = None


class AvailableModelsResponse(BaseModel):
    """Response schema for available models"""

    providers: dict  # provider -> list of models
    default_provider: str
    default_model: str


class ResearchSummaryResponse(BaseModel):
    """Summary statistics for research activities"""

    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    agents_deployed: int
    total_cost_usd: float
    avg_execution_time_seconds: float
