from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    """Schema for creating/registering projects."""
    slug: str = Field(..., max_length=50, pattern="^[a-z0-9-]+$")
    name: str = Field(..., max_length=200)
    hub_url: str = Field(..., max_length=500)
    mesh_namespace: str = Field(..., max_length=100)
    tags: List[str] = Field(default_factory=list)


class ProjectResponse(BaseModel):
    """Schema for project responses."""
    id: int
    slug: str
    name: str
    hub_url: str
    mesh_namespace: str
    status: ProjectStatus
    tags: List[str]
    last_heartbeat_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
