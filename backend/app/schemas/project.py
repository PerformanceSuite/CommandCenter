"""
Pydantic schemas for Project model
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    """Base Project schema with common fields"""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    owner: str = Field(..., min_length=1, max_length=255, description="Project owner")
    description: Optional[str] = Field(None, description="Project description")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    owner: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project responses"""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectWithCounts(ProjectResponse):
    """Schema for project with entity counts"""

    repository_count: int = 0
    technology_count: int = 0
    research_task_count: int = 0
    knowledge_entry_count: int = 0

    model_config = ConfigDict(from_attributes=True)
