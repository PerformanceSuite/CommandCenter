"""
Pydantic schemas for schedule management.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ScheduleBase(BaseModel):
    """Base schedule schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Schedule name")
    description: Optional[str] = Field(
        None, max_length=512, description="Schedule description"
    )
    task_type: str = Field(
        ..., min_length=1, max_length=50, description="Task type to execute"
    )
    task_parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Task-specific parameters"
    )
    frequency: str = Field(
        ...,
        description="Schedule frequency (once, hourly, daily, weekly, monthly, cron)",
    )
    cron_expression: Optional[str] = Field(
        None,
        max_length=100,
        description="Cron expression (required if frequency='cron')",
    )
    interval_seconds: Optional[int] = Field(
        None, gt=0, description="Interval in seconds (for custom intervals)"
    )
    timezone: str = Field(
        default="UTC", max_length=50, description="IANA timezone for schedule execution"
    )
    start_time: Optional[datetime] = Field(None, description="When to start executing")
    end_time: Optional[datetime] = Field(None, description="When to stop executing")
    enabled: bool = Field(default=True, description="Whether schedule is enabled")
    tags: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Custom tags for filtering"
    )

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        """Validate frequency value."""
        valid_frequencies = ["once", "hourly", "daily", "weekly", "monthly", "cron"]
        if v not in valid_frequencies:
            raise ValueError(
                f"Invalid frequency '{v}'. Must be one of: {', '.join(valid_frequencies)}"
            )
        return v

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate end_time is after start_time."""
        if v and info.data.get("start_time") and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class ScheduleCreate(ScheduleBase):
    """Schema for creating a new schedule."""

    project_id: int = Field(..., gt=0, description="Project ID")
    created_by: Optional[int] = Field(
        None, gt=0, description="User ID who created schedule"
    )


class ScheduleUpdate(BaseModel):
    """Schema for updating an existing schedule."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=512)
    task_type: Optional[str] = Field(None, min_length=1, max_length=50)
    task_parameters: Optional[Dict[str, Any]] = None
    frequency: Optional[str] = None
    cron_expression: Optional[str] = Field(None, max_length=100)
    interval_seconds: Optional[int] = Field(None, gt=0)
    timezone: Optional[str] = Field(None, max_length=50)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    enabled: Optional[bool] = None
    tags: Optional[Dict[str, Any]] = None

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: Optional[str]) -> Optional[str]:
        """Validate frequency value."""
        if v is not None:
            valid_frequencies = ["once", "hourly", "daily", "weekly", "monthly", "cron"]
            if v not in valid_frequencies:
                raise ValueError(
                    f"Invalid frequency '{v}'. Must be one of: {', '.join(valid_frequencies)}"
                )
        return v


class ScheduleResponse(BaseModel):
    """Schema for schedule response."""

    id: int
    project_id: int
    name: str
    description: Optional[str]
    task_type: str
    task_parameters: Dict[str, Any]
    frequency: str
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    timezone: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    enabled: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    run_count: int
    success_count: int
    failure_count: int
    success_rate: Optional[float]
    is_active: bool
    last_error: Optional[str]
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    created_by: Optional[int]
    tags: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    """Schema for paginated schedule list response."""

    schedules: list[ScheduleResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ScheduleExecutionRequest(BaseModel):
    """Schema for manual schedule execution request."""

    force: bool = Field(
        default=False,
        description="Force execution even if schedule is not due or disabled",
    )


class ScheduleExecutionResponse(BaseModel):
    """Schema for schedule execution response."""

    schedule_id: int
    schedule_name: str
    job_id: int
    executed_at: datetime
    next_run_at: Optional[datetime]
    message: str


class ScheduleStatistics(BaseModel):
    """Schema for schedule statistics."""

    total_schedules: int
    enabled_schedules: int
    disabled_schedules: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    by_frequency: Dict[str, int]


class ScheduleHealthIssue(BaseModel):
    """Schema for schedule health issue."""

    schedule_id: int
    schedule_name: str
    issue_type: str
    details: str
    severity: str  # critical, warning, info


class ScheduleHealthReport(BaseModel):
    """Schema for schedule health report."""

    timestamp: datetime
    total_schedules: int
    total_issues: int
    critical_issues: int
    warnings: int
    info: int
    issues: Dict[str, list[ScheduleHealthIssue]]
