"""
Batch operation schemas for API validation and serialization.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class BatchAnalyzeRequest(BaseModel):
    """Schema for batch repository analysis request."""

    repository_ids: List[int] = Field(
        ..., description="List of repository IDs to analyze", min_length=1
    )
    priority: Optional[int] = Field(
        default=5, ge=1, le=10, description="Job priority (1-10, higher = more urgent)"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional analysis parameters"
    )
    notify_on_complete: Optional[bool] = Field(
        default=True, description="Send notification when batch completes"
    )
    tags: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom tags for filtering"
    )


class BatchExportRequest(BaseModel):
    """Schema for batch export request."""

    analysis_ids: List[int] = Field(
        ..., description="List of analysis IDs to export", min_length=1
    )
    format: str = Field(
        ..., description="Export format (sarif, markdown, html, csv, json)"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Format-specific export parameters"
    )
    tags: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom tags for filtering"
    )


class BatchImportRequest(BaseModel):
    """Schema for batch technology import request."""

    technologies: List[Dict[str, Any]] = Field(
        ..., description="List of technologies to import", min_length=1
    )
    project_id: int = Field(..., description="Target project ID")
    merge_strategy: Optional[str] = Field(
        default="skip", description="Conflict resolution (skip, overwrite, merge)"
    )
    tags: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom tags for filtering"
    )


class BatchJobResponse(BaseModel):
    """Schema for batch job response."""

    model_config = ConfigDict(from_attributes=True)

    job_id: int = Field(..., description="Batch job ID")
    job_type: str = Field(..., description="Type of batch operation")
    total_items: int = Field(..., description="Total number of items in batch")
    completed_items: int = Field(
        default=0, description="Number of completed items"
    )
    failed_items: int = Field(default=0, description="Number of failed items")
    status: str = Field(..., description="Overall batch status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    started_at: Optional[datetime] = Field(
        default=None, description="Batch start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Batch completion timestamp"
    )
    results: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Individual item results"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BatchAnalyzeResponse(BatchJobResponse):
    """Schema for batch analyze response with analysis-specific fields."""

    repository_ids: List[int] = Field(..., description="Repository IDs being analyzed")
    celery_task_id: Optional[str] = Field(
        default=None, description="Celery task UUID"
    )


class BatchExportResponse(BatchJobResponse):
    """Schema for batch export response with export-specific fields."""

    format: str = Field(..., description="Export format")
    download_urls: Optional[List[str]] = Field(
        default=None, description="Download URLs for completed exports"
    )


class BatchImportResponse(BatchJobResponse):
    """Schema for batch import response with import-specific fields."""

    imported_count: int = Field(default=0, description="Number of successfully imported items")
    skipped_count: int = Field(default=0, description="Number of skipped items (duplicates)")
    failed_count: int = Field(default=0, description="Number of failed imports")
    conflicts: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="List of conflicts encountered"
    )


class BatchStatisticsResponse(BaseModel):
    """Schema for batch operation statistics."""

    total_batches: int = Field(..., description="Total number of batch operations")
    active_batches: int = Field(..., description="Number of currently active batches")
    by_type: Dict[str, int] = Field(
        ..., description="Batch counts by type (analyze, export, import)"
    )
    by_status: Dict[str, int] = Field(
        ..., description="Batch counts by status (pending, running, completed, failed)"
    )
    average_duration_seconds: Optional[float] = Field(
        default=None, description="Average batch duration in seconds"
    )
    success_rate: Optional[float] = Field(
        default=None, description="Overall batch success rate percentage"
    )
