"""
Job schemas for API validation and serialization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobBase(BaseModel):
    """Base job schema with common fields."""

    job_type: str = Field(..., description="Type of job (analysis, export, etc.)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Job input parameters")
    tags: Optional[Dict[str, Any]] = Field(default=None, description="Custom tags for filtering")


class JobCreate(JobBase):
    """Schema for creating a new job."""

    project_id: int = Field(..., description="Project ID this job belongs to")
    created_by: Optional[int] = Field(default=None, description="User ID who created the job")


class JobUpdate(BaseModel):
    """Schema for updating job status and progress."""

    status: Optional[str] = Field(default=None, description="Job status")
    progress: Optional[int] = Field(
        default=None, ge=0, le=100, description="Progress percentage (0-100)"
    )
    current_step: Optional[str] = Field(default=None, description="Current operation description")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Job result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    traceback: Optional[str] = Field(default=None, description="Full traceback for debugging")


class JobResponse(JobBase):
    """Schema for job API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Job ID")
    project_id: int = Field(..., description="Project ID")
    celery_task_id: Optional[str] = Field(default=None, description="Celery task UUID")
    status: str = Field(..., description="Job status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    current_step: Optional[str] = Field(default=None, description="Current operation description")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Job result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    created_by: Optional[int] = Field(default=None, description="User ID who created the job")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion timestamp")
    duration_seconds: Optional[float] = Field(default=None, description="Job duration in seconds")


class JobListResponse(BaseModel):
    """Schema for paginated job list responses."""

    jobs: List[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")


class JobProgressResponse(BaseModel):
    """Schema for job progress information."""

    job_id: int = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    current_step: Optional[str] = Field(default=None, description="Current operation description")
    is_terminal: bool = Field(..., description="Whether job is finished")
    is_active: bool = Field(..., description="Whether job is actively running")
    created_at: Optional[str] = Field(
        default=None, description="Job creation timestamp (ISO format)"
    )
    started_at: Optional[str] = Field(default=None, description="Job start timestamp (ISO format)")
    completed_at: Optional[str] = Field(
        default=None, description="Job completion timestamp (ISO format)"
    )
    duration_seconds: Optional[float] = Field(default=None, description="Job duration in seconds")
    celery_status: Optional[str] = Field(
        default=None, description="Celery task status (if available)"
    )
    celery_info: Optional[Any] = Field(default=None, description="Additional Celery task info")


class JobStatisticsResponse(BaseModel):
    """Schema for job statistics."""

    total: int = Field(..., description="Total number of jobs")
    by_status: Dict[str, int] = Field(
        ..., description="Job counts by status (pending, running, completed, etc.)"
    )
    success_rate: Optional[float] = Field(
        default=None,
        description="Success rate percentage (completed / (completed + failed) * 100)",
    )
    average_duration_seconds: Optional[float] = Field(
        default=None, description="Average duration of completed jobs in seconds"
    )
    active_jobs: int = Field(..., description="Number of active jobs (pending + running)")
