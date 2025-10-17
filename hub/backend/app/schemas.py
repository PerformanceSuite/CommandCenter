"""
Pydantic schemas for Hub API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectBase(BaseModel):
    """Base schema for project"""

    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(..., description="Full path to project folder")


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""

    use_existing_cc: bool = Field(
        False, description="Use existing CommandCenter installation instead of cloning"
    )
    existing_cc_path: Optional[str] = Field(
        None, description="Path to existing CommandCenter (required if use_existing_cc=True)"
    )


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""

    name: Optional[str] = None
    status: Optional[str] = None
    health: Optional[str] = None
    repo_count: Optional[int] = None
    tech_count: Optional[int] = None
    task_count: Optional[int] = None


class ProjectResponse(ProjectBase):
    """Schema for project response"""

    id: int
    slug: str
    backend_port: int
    frontend_port: int
    postgres_port: int
    redis_port: int
    status: str
    health: str
    is_configured: bool
    repo_count: int
    tech_count: int
    task_count: int
    last_started: Optional[datetime]
    last_stopped: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProjectStats(BaseModel):
    """Hub project statistics"""

    total_projects: int = 0
    running: int = 0
    stopped: int = 0
    errors: int = 0


class PortSet(BaseModel):
    """Set of ports for a CommandCenter instance"""

    backend: int
    frontend: int
    postgres: int
    redis: int


class FilesystemBrowseRequest(BaseModel):
    """Request to browse filesystem"""

    path: Optional[str] = None


class FilesystemBrowseResponse(BaseModel):
    """Response from filesystem browse"""

    currentPath: str
    parent: Optional[str]
    directories: list[dict]  # [{name: str, path: str}]


class OrchestrationResponse(BaseModel):
    """Response from orchestration operation"""

    success: bool
    message: str
    project_id: int
    status: Optional[str] = None
