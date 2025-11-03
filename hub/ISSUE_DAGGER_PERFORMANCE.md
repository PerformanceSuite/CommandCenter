# Hub Dagger Orchestration Performance Issue

## Summary
The Hub's Dagger-based orchestration for starting CommandCenter instances is extremely slow and blocks the API, making it impractical for production use.

## Current Behavior
- **First-time project start**: 20-30+ minutes (blocking)
- **Subsequent starts**: 3-5 minutes (estimated, blocking)
- API endpoint `/api/orchestration/{project_id}/start` blocks until Dagger completes
- No progress updates or feedback to user
- Browser shows "Internal Server Error" during long operations

## Expected Behavior
- **First-time project start**: 2-3 minutes (background)
- **Subsequent starts**: 30-60 seconds (background)
- API endpoint returns immediately with status "starting"
- Background job/task handles actual Dagger operations
- WebSocket or polling provides progress updates
- UI shows real-time status (building, pulling, starting, etc.)

## Root Causes

### 1. Synchronous API Design
**File**: `hub/backend/app/routers/orchestration.py`

The `/start` endpoint waits for the entire Dagger build/start process:

```python
@router.post("/{project_id}/start", response_model=OrchestrationResponse)
async def start_project(
    project_id: int,
    service: OrchestrationService = Depends(get_orchestration_service),
):
    try:
        result = await service.start_project(project_id)  # This blocks for 20-30 min!
        return OrchestrationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

### 2. No Background Task Queue
The Hub doesn't use Celery or any background task system. All Dagger operations run in the request/response cycle.

### 3. Dagger Build Overhead
Dagger's first-time builds are inherently slower than docker-compose because:
- Separate build cache (doesn't reuse host Docker images)
- BuildKit is thorough but slow
- No layer sharing between projects
- Rebuilds even if images exist locally

## Impact
- **User Experience**: Terrible - appears frozen/broken
- **Scalability**: Cannot start multiple projects concurrently
- **Reliability**: Timeouts, connection drops during long operations
- **Development**: Debugging is painful

## Reproduction Steps
1. Create a new project in Hub (any size)
2. Click "Start" button
3. Observe:
   - API call hangs for 20-30 minutes
   - No feedback or progress
   - Browser may show "Internal Server Error"
   - Docker shows Dagger engine container but no project containers

## Environment
- **Hub Backend**: FastAPI with Dagger SDK 0.19.4
- **Docker**: Docker Desktop 28.5.1
- **OS**: macOS (darwin)
- **Project tested**: Performia (6.3GB, but issue affects all projects)

## Proposed Solutions

### Short-term (Quick Wins)

#### 1. Add Timeout + Better Error Handling
```python
import asyncio

@router.post("/{project_id}/start")
async def start_project(project_id: int, service: OrchestrationService = ...):
    try:
        # Timeout after 60 seconds, let background process continue
        result = await asyncio.wait_for(
            service.start_project(project_id),
            timeout=60.0
        )
        return OrchestrationResponse(**result)
    except asyncio.TimeoutError:
        # Return "starting" status, actual work continues in background
        return OrchestrationResponse(
            success=True,
            message="Project is starting in the background. Check status for progress.",
            status="starting"
        )
```

#### 2. Document docker-compose Alternative
Add to README:
```markdown
## Starting Projects Manually (Faster)

For now, docker-compose is much faster than Hub's Dagger orchestration:

\`\`\`bash
cd /path/to/your/project
docker-compose up -d
\`\`\`

Then register the running project in Hub UI.
```

### Medium-term (Proper Fix)

#### 3. Background Task System with Celery
```python
# hub/backend/app/tasks/orchestration.py
from celery import shared_task

@shared_task(bind=True)
def start_project_task(self, project_id: int):
    """Background task to start project via Dagger"""
    service = OrchestrationService(...)

    # Update progress
    self.update_state(state='BUILDING', meta={'step': 'Pulling base images'})

    # Run Dagger operations
    result = service.start_project_sync(project_id)

    return result

# In router
@router.post("/{project_id}/start")
async def start_project(project_id: int):
    task = start_project_task.delay(project_id)
    return {"task_id": task.id, "status": "starting"}
```

#### 4. Status Polling Endpoint
```python
@router.get("/{project_id}/start-status/{task_id}")
async def get_start_status(project_id: int, task_id: str):
    task = AsyncResult(task_id)
    return {
        "state": task.state,
        "progress": task.info.get('step', 'Starting...'),
        "ready": task.state == 'SUCCESS'
    }
```

### Long-term (Performance Optimization)

#### 5. Dagger Build Cache Optimization
- Pre-build common base images
- Share build cache between projects
- Use Dagger's layer caching effectively

#### 6. Consider Hybrid Approach
- Use docker-compose for actual container orchestration (fast, reliable)
- Use Dagger only for custom build steps (when needed)
- Hub manages docker-compose.yml files per project

#### 7. WebSocket Progress Updates
Real-time build/start progress to frontend via WebSockets

## Workaround (Current)
Use docker-compose directly:
```bash
cd /Users/danielconnolly/Projects/Performia
docker-compose up -d
```

## Related Files
- `hub/backend/app/routers/orchestration.py` - API endpoints
- `hub/backend/app/services/orchestration_service.py` - Dagger orchestration logic
- `hub/backend/app/dagger_modules/commandcenter.py` - Dagger stack definition

## Testing Done
- Tested with Performia project (6.3GB)
- Tested with test project (smaller)
- Both exhibit same blocking behavior
- Operation times: 20-30+ minutes consistently

## Priority
**High** - This makes the Hub nearly unusable for its primary purpose (managing CommandCenter instances)

## Labels
- `bug`
- `performance`
- `hub`
- `dagger`
- `priority: high`
