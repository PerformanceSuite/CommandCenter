"""
Pydantic schemas for ingestion sources
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from app.models.ingestion_source import SourceType, SourceStatus


class IngestionSourceBase(BaseModel):
    """Base schema for ingestion source"""
    name: str = Field(..., min_length=1, max_length=255)
    type: SourceType
    url: Optional[str] = None
    path: Optional[str] = None
    schedule: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None


class IngestionSourceCreate(IngestionSourceBase):
    """Schema for creating ingestion source"""
    project_id: int


class IngestionSourceUpdate(BaseModel):
    """Schema for updating ingestion source"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    path: Optional[str] = None
    schedule: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class IngestionSourceResponse(IngestionSourceBase):
    """Schema for ingestion source response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    status: SourceStatus
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    documents_ingested: int
    error_count: int
    created_at: datetime
    updated_at: datetime


class IngestionSourceList(BaseModel):
    """Schema for list of ingestion sources"""
    sources: list[IngestionSourceResponse]
    total: int
