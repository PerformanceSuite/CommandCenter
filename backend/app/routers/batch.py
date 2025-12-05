"""
Batch operations API router for bulk operations on repositories and analyses.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.project_context import get_current_project_id
from app.database import get_db
from app.schemas.batch import (
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    BatchExportRequest,
    BatchExportResponse,
    BatchImportRequest,
    BatchImportResponse,
    BatchStatisticsResponse,
)
from app.schemas.job import JobResponse
from app.services.batch_service import BatchService

router = APIRouter(prefix="/api/v1/batch", tags=["batch"])


@router.post(
    "/analyze",
    response_model=BatchAnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def batch_analyze(
    request: BatchAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    project_id: int = Depends(get_current_project_id),
) -> BatchAnalyzeResponse:
    """
    Create a batch analysis job for multiple repositories.

    This endpoint creates an async job that will analyze all specified repositories
    in parallel. Progress can be tracked via the jobs API.

    **Requirements:**
    - At least one repository ID
    - All repositories must exist and be accessible

    **Returns:**
    - 202 Accepted with job details and Celery task ID

    **Example:**
    ```json
    {
        "repository_ids": [1, 2, 3, 4, 5],
        "priority": 8,
        "parameters": {
            "analyze_dependencies": true,
            "check_security": true
        },
        "notify_on_complete": true
    }
    ```
    """
    service = BatchService(db)

    try:
        job = await service.analyze_repositories(
            project_id=project_id,
            repository_ids=request.repository_ids,
            priority=request.priority or 5,
            parameters=request.parameters,
            notify_on_complete=request.notify_on_complete,
            tags=request.tags,
        )

        return BatchAnalyzeResponse(
            job_id=job.id,
            job_type=job.job_type,
            total_items=len(request.repository_ids),
            completed_items=0,
            failed_items=0,
            status=job.status,
            progress=job.progress,
            started_at=job.started_at,
            completed_at=job.completed_at,
            repository_ids=request.repository_ids,
            celery_task_id=job.celery_task_id,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch analysis: {str(e)}",
        )


@router.post("/export", response_model=BatchExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def batch_export(
    request: BatchExportRequest,
    db: AsyncSession = Depends(get_db),
    project_id: int = Depends(get_current_project_id),
) -> BatchExportResponse:
    """
    Create a batch export job for multiple analyses.

    This endpoint creates an async job that will export all specified analyses
    in the requested format. Download URLs will be provided in the job result.

    **Supported Formats:**
    - `sarif`: Static Analysis Results Interchange Format (GitHub/VS Code compatible)
    - `markdown`: GitHub-ready markdown reports
    - `html`: Self-contained HTML dashboard
    - `csv`: Spreadsheet-compatible CSV
    - `json`: Raw JSON data

    **Returns:**
    - 202 Accepted with job details

    **Example:**
    ```json
    {
        "analysis_ids": [10, 11, 12],
        "format": "sarif",
        "parameters": {
            "include_metrics": true,
            "compress": true
        }
    }
    ```
    """
    service = BatchService(db)

    try:
        job = await service.export_analyses(
            project_id=project_id,
            analysis_ids=request.analysis_ids,
            format=request.format,
            parameters=request.parameters,
            tags=request.tags,
        )

        return BatchExportResponse(
            job_id=job.id,
            job_type=job.job_type,
            total_items=len(request.analysis_ids),
            completed_items=0,
            failed_items=0,
            status=job.status,
            progress=job.progress,
            started_at=job.started_at,
            completed_at=job.completed_at,
            format=request.format,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch export: {str(e)}",
        )


@router.post("/import", response_model=BatchImportResponse, status_code=status.HTTP_202_ACCEPTED)
async def batch_import(
    request: BatchImportRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchImportResponse:
    """
    Create a batch import job for technologies.

    This endpoint creates an async job that will import all specified technologies
    into the project. Conflict resolution is handled according to the merge strategy.

    **Merge Strategies:**
    - `skip`: Skip existing technologies (default, safest)
    - `overwrite`: Overwrite existing technologies with new data
    - `merge`: Merge new data with existing (preserve non-conflicting fields)

    **Required Fields per Technology:**
    - `title`: Technology name
    - `domain`: Technology domain (frontend, backend, data, infra, etc.)

    **Returns:**
    - 202 Accepted with job details

    **Example:**
    ```json
    {
        "technologies": [
            {"title": "React", "domain": "frontend", "vendor": "Meta"},
            {"title": "FastAPI", "domain": "backend", "vendor": "Sebastián Ramírez"}
        ],
        "project_id": 1,
        "merge_strategy": "skip"
    }
    ```
    """
    service = BatchService(db)

    try:
        job = await service.import_technologies(
            project_id=request.project_id,
            technologies=request.technologies,
            merge_strategy=request.merge_strategy,
            tags=request.tags,
        )

        return BatchImportResponse(
            job_id=job.id,
            job_type=job.job_type,
            total_items=len(request.technologies),
            completed_items=0,
            failed_items=0,
            imported_count=0,
            skipped_count=0,
            failed_count=0,
            status=job.status,
            progress=job.progress,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch import: {str(e)}",
        )


@router.get("/statistics", response_model=BatchStatisticsResponse)
async def get_batch_statistics(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
) -> BatchStatisticsResponse:
    """
    Get statistics for batch operations.

    Returns aggregated statistics about all batch operations, optionally filtered
    by project. Includes counts by type, status, and performance metrics.

    **Query Parameters:**
    - `project_id` (optional): Filter statistics by project

    **Returns:**
    - Batch operation statistics

    **Example Response:**
    ```json
    {
        "total_batches": 42,
        "active_batches": 3,
        "by_type": {
            "batch_analysis": 25,
            "batch_export": 12,
            "batch_import": 5
        },
        "by_status": {
            "completed": 35,
            "running": 3,
            "failed": 4
        },
        "average_duration_seconds": 127.5,
        "success_rate": 89.7
    }
    ```
    """
    service = BatchService(db)

    try:
        stats = await service.get_batch_statistics(project_id=project_id)
        return BatchStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve batch statistics: {str(e)}",
        )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_batch_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """
    Get details for a specific batch job.

    This is a convenience endpoint that wraps the jobs API for batch operations.
    Use this to check the status and progress of a batch operation.

    **Returns:**
    - Job details including progress, status, and results

    **See Also:**
    - `GET /api/v1/jobs/{job_id}` - Full job API with more options
    - `WS /api/v1/jobs/ws/{job_id}` - WebSocket for real-time progress updates
    """
    from app.services.job_service import JobService

    service = JobService(db)

    try:
        job = await service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch job {job_id} not found",
            )

        return JobResponse.model_validate(job)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve batch job: {str(e)}",
        )
