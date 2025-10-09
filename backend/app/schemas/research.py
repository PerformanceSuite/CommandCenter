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
