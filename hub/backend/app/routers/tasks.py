"""Background task endpoints for async operations"""
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from app.tasks.orchestration import (
    start_project_task,
    stop_project_task,
    restart_project_task,
    get_project_logs_task,
)
from app.schemas import TaskResponse, TaskStatusResponse

router = APIRouter(prefix="/api", tags=["background-tasks"])


@router.post("/orchestration/{project_id}/start", response_model=TaskResponse)
async def start_project(project_id: int) -> TaskResponse:
    """
    Start CommandCenter project in background.

    Returns task_id for polling status.
    """
    task = start_project_task.delay(project_id)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Project start initiated. Poll /api/task-status/{task.id} for progress."
    )


@router.post("/orchestration/{project_id}/stop", response_model=TaskResponse)
async def stop_project(project_id: int) -> TaskResponse:
    """
    Stop CommandCenter project in background.

    Returns task_id for polling status.
    """
    task = stop_project_task.delay(project_id)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Project stop initiated. Poll /api/task-status/{task.id} for progress."
    )


@router.post("/orchestration/{project_id}/restart/{service_name}", response_model=TaskResponse)
async def restart_service(project_id: int, service_name: str) -> TaskResponse:
    """
    Restart specific service in CommandCenter project (background).

    Returns task_id for polling status.
    """
    task = restart_project_task.delay(project_id, service_name)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Service {service_name} restart initiated. Poll /api/task-status/{task.id} for progress."
    )


@router.get("/orchestration/{project_id}/logs/{service_name}", response_model=TaskResponse)
async def get_service_logs(
    project_id: int,
    service_name: str,
    lines: int = 100
) -> TaskResponse:
    """
    Retrieve service logs in background.

    Args:
        project_id: Project ID
        service_name: Service name
        lines: Number of log lines to retrieve (default: 100)

    Returns task_id for polling status.
    """
    task = get_project_logs_task.delay(project_id, service_name, lines)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Log retrieval initiated. Poll /api/task-status/{task.id} for results."
    )


@router.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Poll background task status and progress.

    Returns current state, progress percentage, and result/error if complete.
    """
    task = AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "state": task.state,
        "ready": task.ready(),
    }

    if task.state == 'PENDING':
        response['status'] = 'Task is queued, waiting to start...'
        response['progress'] = 0

    elif task.state == 'BUILDING':
        # Get custom progress from task.update_state()
        info = task.info or {}
        response['status'] = info.get('step', 'Building...')
        response['progress'] = info.get('progress', 50)

    elif task.state == 'RUNNING':
        info = task.info or {}
        response['status'] = info.get('step', 'Running...')
        response['progress'] = info.get('progress', 90)

    elif task.state == 'STOPPING':
        info = task.info or {}
        response['status'] = info.get('step', 'Stopping...')
        response['progress'] = info.get('progress', 50)

    elif task.state == 'RESTARTING':
        info = task.info or {}
        response['status'] = info.get('step', 'Restarting...')
        response['progress'] = info.get('progress', 50)

    elif task.state == 'FETCHING':
        info = task.info or {}
        response['status'] = info.get('step', 'Fetching...')
        response['progress'] = info.get('progress', 50)

    elif task.state == 'SUCCESS':
        response['status'] = 'Completed successfully'
        response['progress'] = 100
        response['result'] = task.result

    elif task.state == 'FAILURE':
        response['status'] = 'Task failed'
        response['progress'] = 0
        response['error'] = str(task.info)

    else:
        # Unknown state
        response['status'] = f'Unknown state: {task.state}'
        response['progress'] = 0

    return TaskStatusResponse(**response)
