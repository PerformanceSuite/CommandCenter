"""
Schedule management REST API endpoints.

This module provides:
- CRUD operations for schedules
- Manual schedule execution
- Schedule statistics and health monitoring
- Pagination and filtering support
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models import Schedule
from app.services.schedule_service import ScheduleService
from app.schemas import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleListResponse,
    ScheduleExecutionRequest,
    ScheduleExecutionResponse,
    ScheduleStatistics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/schedules", tags=["schedules"])


@router.post(
    "", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED
)
async def create_schedule(
    schedule: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new schedule.

    Args:
        schedule: Schedule creation data
        db: Database session

    Returns:
        Created schedule

    Raises:
        HTTPException: If validation fails or conflict detected
    """
    try:
        service = ScheduleService(db)
        created = await service.create_schedule(
            project_id=schedule.project_id,
            name=schedule.name,
            task_type=schedule.task_type,
            frequency=schedule.frequency,
            task_parameters=schedule.task_parameters,
            cron_expression=schedule.cron_expression,
            interval_seconds=schedule.interval_seconds,
            timezone=schedule.timezone,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            description=schedule.description,
            enabled=schedule.enabled,
            created_by=schedule.created_by,
            tags=schedule.tags,
        )

        logger.info(
            f"Created schedule {created.id} for project {schedule.project_id}"
        )
        return ScheduleResponse.model_validate(created)

    except ValueError as e:
        logger.warning(f"Invalid schedule creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule",
        )


@router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    project_id: Optional[int] = Query(
        None, description="Filter by project ID"
    ),
    enabled: Optional[bool] = Query(
        None, description="Filter by enabled status"
    ),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    frequency: Optional[str] = Query(None, description="Filter by frequency"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    List schedules with optional filtering and pagination.

    Args:
        project_id: Filter by project ID
        enabled: Filter by enabled status
        task_type: Filter by task type
        frequency: Filter by frequency
        page: Page number (starts at 1)
        page_size: Number of items per page
        db: Database session

    Returns:
        Paginated list of schedules
    """
    try:
        # Build query with filters
        query = select(Schedule)
        filters = []

        if project_id is not None:
            filters.append(Schedule.project_id == project_id)
        if enabled is not None:
            filters.append(Schedule.enabled == enabled)
        if task_type:
            filters.append(Schedule.task_type == task_type)
        if frequency:
            filters.append(Schedule.frequency == frequency)

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = (
            query.offset(offset)
            .limit(page_size)
            .order_by(Schedule.created_at.desc())
        )

        # Execute query
        result = await db.execute(query)
        schedules = result.scalars().all()

        # Calculate pages
        pages = (total + page_size - 1) // page_size

        return ScheduleListResponse(
            schedules=[ScheduleResponse.model_validate(s) for s in schedules],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Failed to list schedules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list schedules",
        )


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get schedule by ID.

    Args:
        schedule_id: Schedule ID
        db: Database session

    Returns:
        Schedule details

    Raises:
        HTTPException: If schedule not found
    """
    try:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule {schedule_id} not found",
            )

        return ScheduleResponse.model_validate(schedule)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get schedule {schedule_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schedule",
        )


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    updates: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update schedule.

    Args:
        schedule_id: Schedule ID
        updates: Fields to update
        db: Database session

    Returns:
        Updated schedule

    Raises:
        HTTPException: If schedule not found or validation fails
    """
    try:
        service = ScheduleService(db)

        # Convert to dict and remove None values
        update_dict = updates.model_dump(exclude_unset=True)

        updated = await service.update_schedule(
            schedule_id=schedule_id, **update_dict
        )

        logger.info(f"Updated schedule {schedule_id}")
        return ScheduleResponse.model_validate(updated)

    except ValueError as e:
        logger.warning(f"Invalid schedule update: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Failed to update schedule {schedule_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update schedule",
        )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete schedule.

    Args:
        schedule_id: Schedule ID
        db: Database session

    Raises:
        HTTPException: If schedule not found
    """
    try:
        service = ScheduleService(db)
        await service.delete_schedule(schedule_id)

        logger.info(f"Deleted schedule {schedule_id}")

    except ValueError as e:
        logger.warning(f"Schedule deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Failed to delete schedule {schedule_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule",
        )


@router.post(
    "/{schedule_id}/execute",
    response_model=ScheduleExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_schedule(
    schedule_id: int,
    request: Optional[ScheduleExecutionRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a schedule manually.

    Args:
        schedule_id: Schedule ID
        request: Execution options (force execution)
        db: Database session

    Returns:
        Execution response with job ID

    Raises:
        HTTPException: If schedule not found or execution fails
    """
    try:
        service = ScheduleService(db)

        # If force is True, execute regardless of schedule state
        if request and request.force:
            # Get schedule
            result = await db.execute(
                select(Schedule).where(Schedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()

            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schedule {schedule_id} not found",
                )

            # Temporarily enable if disabled
            was_disabled = not schedule.enabled
            if was_disabled:
                schedule.enabled = True

            job = await service.execute_schedule(schedule_id)

            # Restore disabled state
            if was_disabled:
                schedule.enabled = False
            await db.commit()

        else:
            # Normal execution (checks if schedule is active)
            job = await service.execute_schedule(schedule_id)

        # Get updated schedule
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        logger.info(
            f"Manually executed schedule {schedule_id}, created job {job.id}"
        )

        return ScheduleExecutionResponse(
            schedule_id=schedule_id,
            schedule_name=schedule.name if schedule else "",
            job_id=job.id,
            executed_at=job.created_at,
            next_run_at=schedule.next_run_at if schedule else None,
            message=f"Schedule executed successfully, job {job.id} created",
        )

    except ValueError as e:
        logger.warning(f"Schedule execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to execute schedule {schedule_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute schedule",
        )


@router.get("/statistics/summary", response_model=ScheduleStatistics)
async def get_schedule_statistics(
    project_id: Optional[int] = Query(
        None, description="Filter by project ID"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get schedule statistics.

    Args:
        project_id: Optional project ID filter
        db: Database session

    Returns:
        Schedule statistics
    """
    try:
        service = ScheduleService(db)
        stats = await service.get_schedule_statistics(project_id=project_id)

        return ScheduleStatistics(**stats)

    except Exception as e:
        logger.error(f"Failed to get schedule statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schedule statistics",
        )


@router.get("/due/list", response_model=List[ScheduleResponse])
async def list_due_schedules(
    limit: int = Query(
        100, ge=1, le=500, description="Maximum schedules to return"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    List schedules that are due for execution.

    Args:
        limit: Maximum number of schedules to return
        db: Database session

    Returns:
        List of due schedules
    """
    try:
        service = ScheduleService(db)
        due_schedules = await service.get_due_schedules(limit=limit)

        return [ScheduleResponse.model_validate(s) for s in due_schedules]

    except Exception as e:
        logger.error(f"Failed to list due schedules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list due schedules",
        )


@router.post("/{schedule_id}/enable", response_model=ScheduleResponse)
async def enable_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Enable a schedule.

    Args:
        schedule_id: Schedule ID
        db: Database session

    Returns:
        Updated schedule

    Raises:
        HTTPException: If schedule not found
    """
    try:
        service = ScheduleService(db)
        updated = await service.update_schedule(
            schedule_id=schedule_id, enabled=True
        )

        logger.info(f"Enabled schedule {schedule_id}")
        return ScheduleResponse.model_validate(updated)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Failed to enable schedule {schedule_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable schedule",
        )


@router.post("/{schedule_id}/disable", response_model=ScheduleResponse)
async def disable_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Disable a schedule.

    Args:
        schedule_id: Schedule ID
        db: Database session

    Returns:
        Updated schedule

    Raises:
        HTTPException: If schedule not found
    """
    try:
        service = ScheduleService(db)
        updated = await service.update_schedule(
            schedule_id=schedule_id, enabled=False
        )

        logger.info(f"Disabled schedule {schedule_id}")
        return ScheduleResponse.model_validate(updated)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Failed to disable schedule {schedule_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable schedule",
        )
