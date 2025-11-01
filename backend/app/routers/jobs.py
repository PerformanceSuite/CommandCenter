"""
Jobs API router for managing async task execution.
"""

from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from app.database import get_db
from app.services.job_service import JobService
from app.services.optimized_job_service import OptimizedJobService
from app.schemas import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobListResponse,
    JobProgressResponse,
    JobStatisticsResponse,
)
from app.models import JobStatus

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


# WebSocket connection manager for real-time updates
class ConnectionManager:
    """Manage WebSocket connections for job progress updates."""

    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, job_id: int, websocket: WebSocket):
        """Connect a WebSocket client to a job."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, job_id: int, websocket: WebSocket):
        """Disconnect a WebSocket client from a job."""
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def broadcast(self, job_id: int, message: dict):
        """Broadcast a message to all clients watching a job."""
        if job_id not in self.active_connections:
            return

        disconnected = []
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(job_id, websocket)


manager = ConnectionManager()


@router.get("", response_model=JobListResponse)
async def list_jobs(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: AsyncSession = Depends(get_db),
):
    """
    List jobs with optional filters.

    Returns paginated list of jobs with filters for project, status, and type.
    Uses optimized single-query pagination to avoid N+1 pattern.
    """
    # Use optimized service to get jobs and count in single query
    service = OptimizedJobService(db)
    jobs, total = await service.list_jobs_with_count(
        project_id=project_id,
        status_filter=status_filter,
        job_type=job_type,
        skip=skip,
        limit=limit,
    )

    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new job.

    Creates a new job with pending status. The job will be picked up
    by Celery workers for execution.
    """
    service = JobService(db)
    job = await service.create_job(
        project_id=job_data.project_id,
        job_type=job_data.job_type,
        parameters=job_data.parameters,
        created_by=job_data.created_by,
        tags=job_data.tags,
    )

    return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get job by ID.

    Returns detailed information about a specific job.
    """
    service = JobService(db)
    job = await service.get_job(job_id)
    return JobResponse.model_validate(job)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update job status and progress.

    Updates job fields such as status, progress, current_step, result, or error.
    Automatically broadcasts updates to connected WebSocket clients.
    """
    service = JobService(db)
    job = await service.update_job(
        job_id=job_id,
        status=job_update.status,
        progress=job_update.progress,
        current_step=job_update.current_step,
        result=job_update.result,
        error=job_update.error,
        traceback=job_update.traceback,
    )

    # Broadcast update to WebSocket clients
    await manager.broadcast(
        job_id,
        {
            "type": "job_update",
            "job_id": job_id,
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step,
        },
    )

    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a job.

    Deletes a job record. Cannot delete running jobs - cancel them first.
    """
    service = JobService(db)
    await service.delete_job(job_id)
    return None


@router.post("/{job_id}/dispatch", response_model=JobResponse)
async def dispatch_job(
    job_id: int,
    delay_seconds: int = Query(
        0, ge=0, le=3600, description="Delay before execution (0-3600 seconds)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Dispatch a pending job to Celery for async execution.

    Submits the job to the Celery task queue for processing. The job must
    be in pending status. Returns the updated job with the Celery task ID.

    Args:
        job_id: Job ID to dispatch
        delay_seconds: Optional delay before execution (0-3600 seconds)

    Returns:
        Updated job with celery_task_id populated
    """
    service = JobService(db)
    task_id = await service.dispatch_job(job_id, delay_seconds=delay_seconds)

    # Get updated job
    job = await service.get_job(job_id)

    # Broadcast dispatch event to WebSocket clients
    await manager.broadcast(
        job_id,
        {
            "type": "job_dispatched",
            "job_id": job_id,
            "celery_task_id": task_id,
            "delay_seconds": delay_seconds,
        },
    )

    return JobResponse.model_validate(job)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a running or pending job.

    Attempts to cancel a job and revoke the associated Celery task.
    Only works for jobs in pending or running state.
    """
    service = JobService(db)
    job = await service.cancel_job(job_id)

    # Broadcast cancellation to WebSocket clients
    await manager.broadcast(
        job_id,
        {
            "type": "job_cancelled",
            "job_id": job_id,
            "status": job.status,
        },
    )

    return JobResponse.model_validate(job)


@router.get("/{job_id}/progress", response_model=JobProgressResponse)
async def get_job_progress(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get job progress information.

    Returns detailed progress information including Celery task status if available.
    """
    service = JobService(db)
    progress = await service.get_job_progress(job_id)
    return JobProgressResponse(**progress)


@router.get("/active/list", response_model=JobListResponse)
async def list_active_jobs(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all active jobs (pending or running).

    Returns jobs that are currently being processed or waiting to be processed.
    """
    service = JobService(db)
    jobs = await service.get_active_jobs(project_id=project_id)

    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=len(jobs),
        skip=0,
        limit=len(jobs),
    )


@router.get("/statistics/summary", response_model=JobStatisticsResponse)
async def get_job_statistics(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get job statistics.

    Returns aggregated statistics including total jobs, jobs by status,
    success rate, and average duration.
    Uses optimized aggregation queries instead of loading all records.
    """
    # Use optimized service for statistics calculation
    service = OptimizedJobService(db)
    stats = await service.get_statistics_optimized(project_id=project_id)
    return JobStatisticsResponse(**stats)


@router.websocket("/ws/{job_id}")
async def websocket_job_progress(
    websocket: WebSocket,
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time job progress updates.

    Connect to this endpoint to receive real-time updates about a job's progress.
    The connection will automatically close when the job reaches a terminal state.

    Example client code:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/jobs/ws/123');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Job update:', data);
    };
    ```
    """
    # Verify job exists
    service = JobService(db)
    try:
        job = await service.get_job(job_id)
    except HTTPException:
        await websocket.close(code=1008, reason="Job not found")
        return

    # Connect to job updates
    await manager.connect(job_id, websocket)

    try:
        # Send initial status
        await websocket.send_json(
            {
                "type": "connected",
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "current_step": job.current_step,
            }
        )

        # Poll for updates and send to client
        while True:
            # Refresh job status from database
            job = await service.get_job(job_id)

            # Send periodic updates
            await websocket.send_json(
                {
                    "type": "progress",
                    "job_id": job_id,
                    "status": job.status,
                    "progress": job.progress,
                    "current_step": job.current_step,
                    "is_terminal": job.is_terminal,
                }
            )

            # Close connection if job is finished
            if job.is_terminal:
                await websocket.send_json(
                    {
                        "type": "completed",
                        "job_id": job_id,
                        "status": job.status,
                        "result": job.result,
                        "error": job.error,
                    }
                )
                break

            # Wait before next update (1 second polling interval)
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)
    except Exception as e:
        # Log error and close connection
        print(f"WebSocket error for job {job_id}: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        manager.disconnect(job_id, websocket)
