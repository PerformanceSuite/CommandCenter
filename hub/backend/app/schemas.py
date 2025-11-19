"""
Pydantic schemas for Hub API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Response(BaseModel):
    """Generic API response"""

    success: bool
    message: str


class ProjectBase(BaseModel):
    """Base schema for project"""

    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(..., description="Full path to project folder")


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""

    pass


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


# Task Schemas for Background Operations

class TaskResponse(BaseModel):
    """Response when submitting a background task"""

    task_id: str = Field(..., description="Celery task ID for polling status")
    status: str = Field(..., description="Initial status (pending)")
    message: str = Field(..., description="Human-readable message")


class TaskStatusResponse(BaseModel):
    """Response when polling task status"""

    task_id: str = Field(..., description="Celery task ID")
    state: str = Field(..., description="Celery task state (PENDING, BUILDING, SUCCESS, etc)")
    ready: bool = Field(..., description="True if task is complete")
    status: str = Field(..., description="Human-readable status message")
    progress: int = Field(..., description="Progress percentage (0-100)")
    result: Optional[dict] = Field(None, description="Task result if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
