# Hub Background Tasks with Celery - Design Document

**Date**: 2025-11-02
**Status**: Design Approved
**Goal**: Add background task processing to Hub to prevent 20-30 minute API blocking during Dagger orchestration

---

## Overview

Transform Hub's Dagger orchestration from blocking synchronous API calls to non-blocking background tasks with real-time progress updates. This solves the critical UX issue where starting a CommandCenter instance appears to hang for 20-30 minutes.

### Success Criteria

**Performance**:
- API response time: < 100ms (just queues task)
- Frontend shows progress updates within 2 seconds
- All orchestration operations (start/stop/restart/logs) return immediately

**User Experience**:
- Clear progress feedback during long operations
- Ability to navigate away and return (task continues)
- Meaningful error messages with recovery suggestions

**Architecture**:
- Zero monthly fees (self-hosted Redis + Celery)
- Independent from main CommandCenter instance
- Supports concurrent operations on multiple projects

---

## Architecture

### System Components

```
┌─────────────┐
│   Browser   │
│  (React UI) │
└──────┬──────┘
       │ HTTP Polling (every 2s)
       │
┌──────▼──────────────────────────┐
│   Hub Backend (FastAPI)         │
│  - POST /start → task_id        │
│  - GET /task-status/{id}        │
└──────┬──────────────────────────┘
       │ Celery Tasks
       │
┌──────▼──────────────────────────┐
│   Redis                         │
│  - Message Broker               │
│  - Result Backend               │
└──────┬──────────────────────────┘
       │ Task Queue
       │
┌──────▼──────────────────────────┐
│   Celery Workers                │
│  - Execute Dagger operations    │
│  - Update task progress         │
│  - Store results                │
└─────────────────────────────────┘
```

### Task Flow

1. **User Action**: Clicks "Start Project" in Hub UI
2. **API Call**: `POST /api/orchestration/{project_id}/start`
3. **Task Creation**: Hub creates Celery task, returns `task_id` immediately (< 100ms)
4. **Worker Pickup**: Celery worker picks up task from Redis queue
5. **Execution**: Worker runs Dagger orchestration (20-30 min for first start)
6. **Progress Updates**: Worker updates state in Redis: `PENDING → BUILDING → RUNNING → SUCCESS`
7. **Frontend Polling**: UI polls `/task-status/{task_id}` every 2 seconds
8. **Completion**: Task finishes, result stored in Redis, polling stops

---

## Backend Implementation

### File Structure

```
hub/backend/
├── app/
│   ├── celery_app.py              # NEW: Celery configuration
│   ├── config.py                  # UPDATED: Add Celery settings
│   ├── tasks/
│   │   ├── __init__.py           # NEW
│   │   └── orchestration.py      # NEW: Background task definitions
│   ├── routers/
│   │   ├── orchestration.py      # UPDATED: Return task_id, non-blocking
│   │   └── tasks.py              # NEW: Task status polling endpoint
│   ├── schemas/
│   │   └── task.py               # NEW: TaskStatus, TaskResult schemas
│   └── services/
│       └── orchestration_service.py  # EXISTING: Reused by tasks
├── docker-compose.yml             # UPDATED: Add Redis + Celery worker
└── requirements.txt               # UPDATED: Add celery, redis
```

### Key Components

#### 1. Celery Configuration (`celery_app.py`)

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "hub",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    task_send_sent_event=True,
    worker_send_task_events=True,
    result_expires=3600,  # 1 hour
    task_soft_time_limit=3600,  # 1 hour warning
    task_time_limit=7200,  # 2 hour hard limit
)

celery_app.autodiscover_tasks(['app.tasks'])
```

#### 2. Background Tasks (`tasks/orchestration.py`)

```python
from celery import shared_task
from app.services.orchestration_service import OrchestrationService
from app.database import AsyncSessionLocal

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def start_project_task(self, project_id: int):
    """Start CommandCenter project via Dagger (background)"""
    try:
        # Update: Initializing
        self.update_state(
            state='BUILDING',
            meta={'step': 'Initializing Dagger client...', 'progress': 10}
        )

        # Get project and create service
        async with AsyncSessionLocal() as db:
            service = OrchestrationService(db)

            # Update: Building containers
            self.update_state(
                state='BUILDING',
                meta={'step': 'Building containers (this may take 20-30 min)...', 'progress': 30}
            )

            # Run Dagger orchestration
            result = await service.start_project(project_id)

            # Update: Starting services
            self.update_state(
                state='RUNNING',
                meta={'step': 'Starting services...', 'progress': 80}
            )

            return {
                "success": True,
                "project_id": project_id,
                "result": result
            }

    except DaggerBuildError as e:
        # Retry on transient failures
        raise self.retry(exc=e, countdown=60)

    except Exception as e:
        # Log and fail permanently
        logger.error(f"Failed to start project {project_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_id": project_id
        }

@shared_task(bind=True)
def stop_project_task(self, project_id: int):
    """Stop CommandCenter project (background)"""
    # Similar implementation
    pass

@shared_task(bind=True)
def restart_service_task(self, project_id: int, service_name: str):
    """Restart specific service (background)"""
    # Similar implementation
    pass

@shared_task(bind=True)
def get_logs_task(self, project_id: int, service_name: str, lines: int = 100):
    """Retrieve service logs (background)"""
    # Similar implementation
    pass
```

#### 3. Updated Router (`routers/orchestration.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from celery.result import AsyncResult
from app.tasks.orchestration import start_project_task, stop_project_task
from app.schemas.task import TaskResponse, TaskStatusResponse

router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])

@router.post("/{project_id}/start", response_model=TaskResponse)
async def start_project(project_id: int):
    """Start project in background, return task ID"""
    task = start_project_task.delay(project_id)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Project start initiated. Poll /task-status/{task_id} for progress."
    )

@router.post("/{project_id}/stop", response_model=TaskResponse)
async def stop_project(project_id: int):
    """Stop project in background, return task ID"""
    task = stop_project_task.delay(project_id)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message="Project stop initiated."
    )

@router.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Poll task status and progress"""
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
        # Get custom progress
        info = task.info or {}
        response['status'] = info.get('step', 'Building...')
        response['progress'] = info.get('progress', 50)

    elif task.state == 'RUNNING':
        info = task.info or {}
        response['status'] = info.get('step', 'Running...')
        response['progress'] = info.get('progress', 90)

    elif task.state == 'SUCCESS':
        response['status'] = 'Completed successfully'
        response['progress'] = 100
        response['result'] = task.result

    elif task.state == 'FAILURE':
        response['status'] = 'Task failed'
        response['progress'] = 0
        response['error'] = str(task.info)

    return TaskStatusResponse(**response)
```

#### 4. Schemas (`schemas/task.py`)

```python
from pydantic import BaseModel
from typing import Optional, Any

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    ready: bool
    status: str
    progress: int
    result: Optional[Any] = None
    error: Optional[str] = None
```

---

## Frontend Implementation

### Task Status Hook (`hooks/useTaskStatus.ts`)

```typescript
import { useState, useEffect } from 'react';

interface TaskStatus {
  task_id: string;
  state: string;
  ready: boolean;
  status: string;
  progress: number;
  result?: any;
  error?: string;
}

export const useTaskStatus = (taskId: string | null) => {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!taskId) return;

    setIsPolling(true);

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/orchestration/task-status/${taskId}`);
        const data = await response.json();
        setStatus(data);

        // Stop polling when task finishes
        if (['SUCCESS', 'FAILURE', 'REVOKED'].includes(data.state)) {
          setIsPolling(false);
          return true; // Signal to stop interval
        }

        return false; // Continue polling
      } catch (error) {
        console.error('Error polling task status:', error);
        return false;
      }
    };

    // Poll immediately
    pollStatus();

    // Then poll every 2 seconds
    const interval = setInterval(async () => {
      const shouldStop = await pollStatus();
      if (shouldStop) {
        clearInterval(interval);
      }
    }, 2000);

    return () => {
      clearInterval(interval);
      setIsPolling(false);
    };
  }, [taskId]);

  return { status, isPolling };
};
```

### Updated ProjectCard Component

```typescript
const ProjectCard = ({ project }) => {
  const [taskId, setTaskId] = useState<string | null>(null);
  const { status, isPolling } = useTaskStatus(taskId);

  const handleStart = async () => {
    const response = await fetch(`/api/orchestration/${project.id}/start`, {
      method: 'POST'
    });
    const data = await response.json();
    setTaskId(data.task_id);
  };

  return (
    <div className="project-card">
      <h3>{project.name}</h3>

      {isPolling && (
        <div className="progress-section">
          <ProgressBar value={status?.progress || 0} />
          <p className="status-text">{status?.status}</p>
        </div>
      )}

      {!isPolling && (
        <button onClick={handleStart}>Start Project</button>
      )}

      {status?.error && (
        <div className="error-message">{status.error}</div>
      )}
    </div>
  );
};
```

---

## Infrastructure Setup

### docker-compose.yml

```yaml
version: '3.8'

services:
  hub-backend:
    build: ./hub/backend
    ports:
      - "9001:9001"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/hub.db
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - ./hub/backend:/app
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - hub_redis_data:/data
    command: redis-server --appendonly yes

  celery-worker:
    build: ./hub/backend
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - DATABASE_URL=sqlite+aiosqlite:///./data/hub.db
    volumes:
      - ./hub/backend:/app
      - /var/run/docker.sock:/var/run/docker.sock  # For Dagger access
    depends_on:
      - redis

  hub-frontend:
    build: ./hub/frontend
    ports:
      - "9000:9000"
    environment:
      - VITE_API_BASE_URL=http://localhost:9001
    volumes:
      - ./hub/frontend:/app

volumes:
  hub_redis_data:
```

### Development Workflow

```bash
# Start all services
docker-compose up

# OR run individually for development:

# Terminal 1: Redis
docker-compose up redis

# Terminal 2: Hub Backend
cd hub/backend
uvicorn app.main:app --reload --port 9001

# Terminal 3: Celery Worker
cd hub/backend
celery -A app.celery_app worker --loglevel=info

# Terminal 4: Hub Frontend
cd hub/frontend
npm run dev
```

---

## Error Handling & Resilience

### Task Retry Logic

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def start_project_task(self, project_id: int):
    try:
        # ... task logic ...
    except DaggerBuildError as e:
        # Retry on transient failures (network issues, resource constraints)
        raise self.retry(exc=e, countdown=60)
    except Exception as e:
        # Don't retry on permanent errors
        logger.error(f"Permanent failure: {e}")
        raise
```

### Timeout Handling

**Celery Worker**:
- `task_soft_time_limit`: 3600s (1 hour) - warning
- `task_time_limit`: 7200s (2 hours) - hard kill
- Long Dagger builds allowed (no timeout on worker)

**Frontend**:
- Show "Still building..." message after 10 minutes
- Continue polling (no timeout)
- Allow user to navigate away (task continues)

### Stuck Task Detection

```python
# In worker, send heartbeat every 30 seconds
@shared_task(bind=True)
def start_project_task(self, project_id: int):
    last_heartbeat = time.time()

    # During long operations
    for step in build_steps:
        # Update heartbeat
        if time.time() - last_heartbeat > 30:
            self.update_state(state='BUILDING', meta={'heartbeat': time.time()})
            last_heartbeat = time.time()
```

**Admin endpoint** to detect stuck tasks:
- If no heartbeat update for 5 minutes → mark as "possibly stuck"
- Allow manual intervention (cancel/restart)

---

## Migration Strategy

### Phase 1: Infrastructure Setup (Week 1)

**Tasks**:
- Add Redis to docker-compose
- Configure Celery app
- Deploy Celery worker
- Verify worker connects to Redis

**Deliverables**:
- Redis running and accessible
- Celery worker running (no tasks yet)
- Health check endpoint for Celery

### Phase 2: Backend Tasks (Week 1-2)

**Tasks**:
- Implement background tasks (start/stop/restart/logs)
- Add task status polling endpoint
- Add schemas for task responses
- Update routers to return task_id

**Deliverables**:
- All 4 operations available as background tasks
- Status polling endpoint functional
- Unit tests for task logic
- Integration tests with real Redis

**Backwards Compatibility**:
- Keep existing synchronous endpoints (mark deprecated)
- New endpoints use `/v2/` prefix or feature flag

### Phase 3: Frontend Updates (Week 2)

**Tasks**:
- Implement `useTaskStatus` hook
- Update ProjectCard with progress UI
- Add progress bar component
- Handle error states

**Deliverables**:
- UI shows real-time progress
- Users can navigate away and return
- Error messages displayed clearly

**Feature Flag**:
- Toggle between sync/async modes
- Gradual rollout to test in production

### Phase 4: Cleanup & Monitoring (Week 3)

**Tasks**:
- Remove old synchronous endpoints
- Remove feature flags
- Add Celery Flower dashboard (optional)
- Set up monitoring/alerts

**Deliverables**:
- Clean codebase (no deprecated code)
- Monitoring dashboard
- Documentation updated

---

## Testing Strategy

### Unit Tests

**Backend** (`tests/unit/test_tasks.py`):
```python
@patch('app.tasks.orchestration.OrchestrationService')
def test_start_project_task_success(mock_service):
    # Mock Dagger operations
    mock_service.return_value.start_project.return_value = {"status": "running"}

    # Execute task
    result = start_project_task(project_id=1)

    assert result['success'] is True
    assert result['project_id'] == 1
```

**Frontend** (`src/hooks/__tests__/useTaskStatus.test.ts`):
```typescript
it('polls task status until completion', async () => {
  // Mock API responses
  fetchMock.mockResponses(
    [JSON.stringify({ state: 'PENDING', progress: 0 })],
    [JSON.stringify({ state: 'BUILDING', progress: 50 })],
    [JSON.stringify({ state: 'SUCCESS', progress: 100 })]
  );

  const { result } = renderHook(() => useTaskStatus('task-123'));

  await waitFor(() => expect(result.current.status?.state).toBe('SUCCESS'));
  expect(fetchMock).toHaveBeenCalledTimes(3);
});
```

### Integration Tests

**With Real Redis + Celery** (`tests/integration/test_task_lifecycle.py`):
```python
@pytest.mark.integration
def test_full_task_lifecycle():
    # Start Redis + Celery worker
    # Submit task
    response = client.post('/api/orchestration/1/start')
    task_id = response.json()['task_id']

    # Poll until complete
    for _ in range(60):  # 2 min timeout
        status = client.get(f'/api/orchestration/task-status/{task_id}').json()
        if status['ready']:
            break
        time.sleep(2)

    assert status['state'] == 'SUCCESS'
```

### E2E Tests

**Full Stack Test**:
1. Start Hub with Redis + Celery
2. Create test project via API
3. Start project via background task
4. Poll status every 2 seconds
5. Verify containers actually running (`docker ps`)
6. Stop project via background task
7. Verify containers stopped

---

## Monitoring & Operations

### Metrics to Track

**Task Performance**:
- Average task duration by operation (start/stop/restart)
- Task failure rate
- Retry attempts per task
- Queue depth (tasks waiting)

**System Health**:
- Redis memory usage
- Celery worker CPU/memory
- Active tasks count
- Failed tasks in last hour

### Optional: Celery Flower Dashboard

```bash
# Install Flower
pip install flower

# Run dashboard
celery -A app.celery_app flower --port=5555

# Access at http://localhost:5555
```

**Features**:
- Real-time task monitoring
- Worker status
- Task history
- Rate graphs

### Alerts

**Critical**:
- Redis down
- All Celery workers down
- Task failure rate > 10%

**Warning**:
- Queue depth > 10 tasks
- Average task duration > 40 min
- Redis memory > 80%

---

## Configuration

### Settings (`app/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_track_started: bool = True

    # Task Limits
    task_soft_time_limit: int = 3600   # 1 hour
    task_time_limit: int = 7200        # 2 hours
    task_result_expires: int = 3600    # Results expire after 1 hour

    # Polling
    task_status_poll_interval: int = 2  # Frontend polls every 2 seconds

    # Worker
    celery_worker_concurrency: int = 2  # Max concurrent tasks

    class Config:
        env_file = ".env"
```

### Environment Variables

```bash
# .env
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_WORKER_CONCURRENCY=2
TASK_STATUS_POLL_INTERVAL=2
```

---

## Dependencies

### Backend Requirements

```txt
# requirements.txt additions
celery==5.3.4
redis==5.0.1
flower==2.0.1  # Optional, for monitoring
```

### Frontend Dependencies

```json
// package.json - no new dependencies needed
// Uses native fetch API and React hooks
```

---

## Success Metrics

### Performance Targets

- **API Response Time**: < 100ms (task queuing only)
- **First Progress Update**: < 2 seconds after task starts
- **UI Responsiveness**: No blocking, smooth interactions
- **Task Throughput**: Support 5+ concurrent project starts

### User Experience Goals

- **Clear Feedback**: User knows what's happening at all times
- **Interruptible**: Can navigate away, task continues
- **Recoverable**: Clear error messages with retry/fix suggestions
- **Predictable**: Progress bar reflects actual completion (10% → 30% → 80% → 100%)

---

## Future Enhancements

**Not in Initial Scope** (defer to future iterations):

1. **WebSocket Progress Updates**
   - Replace polling with real-time push
   - Lower latency, less bandwidth

2. **Task Prioritization**
   - Priority queue for critical operations
   - Deprioritize non-urgent tasks

3. **Task Cancellation**
   - Allow users to cancel long-running tasks
   - Graceful cleanup of partial Dagger builds

4. **Task History & Analytics**
   - Dashboard showing all past tasks
   - Performance trends over time

5. **Multi-Worker Scaling**
   - Auto-scale workers based on queue depth
   - Kubernetes deployment

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Redis goes down | All tasks fail | Add Redis persistence, monitoring, auto-restart |
| Celery worker crashes | Tasks stuck in queue | Supervisor/systemd auto-restart, multiple workers |
| Task takes > 2 hours | Hard timeout kills it | Optimize Dagger builds, increase limit if needed |
| Frontend polling overwhelms API | Server overload | Rate limiting, exponential backoff on errors |
| Task result expires before user checks | Lost status | Increase `result_expires`, store in database |

---

## References

- Celery Documentation: https://docs.celeryq.dev/
- Redis Documentation: https://redis.io/docs/
- FastAPI Background Tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- Dagger SDK: https://docs.dagger.io/api/python

---

**Approved By**: User
**Next Steps**: Create implementation plan with detailed tasks
