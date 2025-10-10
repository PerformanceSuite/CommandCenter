"""
Pydantic schemas for Technology endpoints
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.technology import (
    TechnologyDomain,
    TechnologyStatus,
    IntegrationDifficulty,
    MaturityLevel,
    CostTier,
)


class TechnologyBase(BaseModel):
    """Base schema for technology"""

    title: str = Field(..., min_length=1, max_length=255)
    vendor: Optional[str] = Field(None, max_length=255)
    domain: TechnologyDomain = TechnologyDomain.OTHER
    status: TechnologyStatus = TechnologyStatus.DISCOVERY
    relevance_score: int = Field(default=50, ge=0, le=100)
    priority: int = Field(default=3, ge=1, le=5)
    description: Optional[str] = None
    notes: Optional[str] = None
    use_cases: Optional[str] = None
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    website_url: Optional[str] = None
    tags: Optional[str] = None

    # Technology Radar v2 fields
    latency_ms: Optional[float] = Field(None, ge=0)
    throughput_qps: Optional[int] = Field(None, ge=0)
    integration_difficulty: Optional[IntegrationDifficulty] = None
    integration_time_estimate_days: Optional[int] = Field(None, ge=0)
    maturity_level: Optional[MaturityLevel] = None
    stability_score: Optional[int] = Field(None, ge=0, le=100)
    cost_tier: Optional[CostTier] = None
    cost_monthly_usd: Optional[float] = Field(None, ge=0)
    dependencies: Optional[Dict[str, Any]] = None
    alternatives: Optional[str] = None
    last_hn_mention: Optional[datetime] = None
    hn_score_avg: Optional[int] = Field(None, ge=0)
    github_stars: Optional[int] = Field(None, ge=0)
    github_last_commit: Optional[datetime] = None


class TechnologyCreate(TechnologyBase):
    """Schema for creating a technology"""

    pass


class TechnologyUpdate(BaseModel):
    """Schema for updating a technology"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    vendor: Optional[str] = Field(None, max_length=255)
    domain: Optional[TechnologyDomain] = None
    status: Optional[TechnologyStatus] = None
    relevance_score: Optional[int] = Field(None, ge=0, le=100)
    priority: Optional[int] = Field(None, ge=1, le=5)
    description: Optional[str] = None
    notes: Optional[str] = None
    use_cases: Optional[str] = None
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    website_url: Optional[str] = None
    tags: Optional[str] = None

    # Technology Radar v2 fields
    latency_ms: Optional[float] = Field(None, ge=0)
    throughput_qps: Optional[int] = Field(None, ge=0)
    integration_difficulty: Optional[IntegrationDifficulty] = None
    integration_time_estimate_days: Optional[int] = Field(None, ge=0)
    maturity_level: Optional[MaturityLevel] = None
    stability_score: Optional[int] = Field(None, ge=0, le=100)
    cost_tier: Optional[CostTier] = None
    cost_monthly_usd: Optional[float] = Field(None, ge=0)
    dependencies: Optional[Dict[str, Any]] = None
    alternatives: Optional[str] = None
    last_hn_mention: Optional[datetime] = None
    hn_score_avg: Optional[int] = Field(None, ge=0)
    github_stars: Optional[int] = Field(None, ge=0)
    github_last_commit: Optional[datetime] = None


class TechnologyInDB(TechnologyBase):
    """Schema for technology in database"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TechnologyResponse(TechnologyInDB):
    """Schema for technology API response"""

    pass


class TechnologyListResponse(BaseModel):
    """Schema for technology list response"""

    total: int
    items: list[TechnologyResponse]
    page: int = 1
    page_size: int = 50
