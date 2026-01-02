"""Pydantic schemas for skills."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    """Base schema for skills."""
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: str
    category: str = "workflow"
    tags: List[str] = []
    version: str = "1.0.0"
    author: Optional[str] = None
    is_public: bool = True


class SkillCreate(SkillBase):
    """Schema for creating a skill."""
    project_id: Optional[int] = None


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    is_public: Optional[bool] = None


class SkillResponse(SkillBase):
    """Schema for skill responses."""
    id: int
    project_id: Optional[int]
    usage_count: int
    success_count: int
    failure_count: int
    effectiveness_score: float
    last_validated_at: Optional[datetime]
    validation_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SkillUsageCreate(BaseModel):
    """Schema for recording skill usage."""
    skill_id: int
    session_id: Optional[str] = None
    outcome: Optional[str] = None  # success, failure, neutral
    outcome_notes: Optional[str] = None


class SkillUsageResponse(BaseModel):
    """Schema for skill usage responses."""
    id: int
    skill_id: int
    project_id: Optional[int]
    user_id: Optional[int]
    session_id: Optional[str]
    used_at: datetime
    outcome: Optional[str]
    outcome_notes: Optional[str]

    class Config:
        from_attributes = True


class SkillImportRequest(BaseModel):
    """Schema for importing skills from filesystem."""
    path: str = Field(..., description="Path to skills directory (e.g., ~/.claude/skills)")
    overwrite: bool = Field(default=False, description="Overwrite existing skills with same slug")


class SkillSearchRequest(BaseModel):
    """Schema for searching skills."""
    query: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    min_effectiveness: Optional[float] = None
    include_private: bool = False
