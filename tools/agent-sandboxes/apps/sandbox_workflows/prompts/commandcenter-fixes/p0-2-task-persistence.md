# P0-2: Replace In-Memory Task Storage with Redis Persistence

## Objective
Replace the in-memory task dict in research_orchestration.py with Redis-backed persistence to prevent data loss on restart.

## File to Modify
`backend/app/routers/research_orchestration.py`

## Task

1. **Find the in-memory storage** at approximately line 40:
   ```python
   # In-memory task storage (will be lost on restart)
   tasks: Dict[str, Any] = {}
   ```

2. **Replace with Redis-backed storage**:
   - Use the existing Redis connection from the app
   - Create a TaskStorage class that wraps Redis operations
   - Use JSON serialization for task data
   - Add TTL (time-to-live) for automatic cleanup of old tasks

3. **Implementation approach**:
   ```python
   import json
   from typing import Optional
   from app.core.redis import get_redis_client

   class TaskStorage:
       PREFIX = "research_task:"
       TTL = 86400 * 7  # 7 days

       @classmethod
       async def get(cls, task_id: str) -> Optional[dict]:
           redis = await get_redis_client()
           data = await redis.get(f"{cls.PREFIX}{task_id}")
           return json.loads(data) if data else None

       @classmethod
       async def set(cls, task_id: str, task_data: dict) -> None:
           redis = await get_redis_client()
           await redis.setex(
               f"{cls.PREFIX}{task_id}",
               cls.TTL,
               json.dumps(task_data)
           )

       @classmethod
       async def delete(cls, task_id: str) -> None:
           redis = await get_redis_client()
           await redis.delete(f"{cls.PREFIX}{task_id}")
   ```

4. **Update all usages** of the `tasks` dict to use `TaskStorage`

5. **Add error handling** for Redis connection failures

6. **Add tests**:
   - Test task creation persists to Redis
   - Test task retrieval from Redis
   - Test task deletion
   - Test TTL expiration

## Acceptance Criteria
- [ ] In-memory dict replaced with Redis storage
- [ ] TaskStorage class implemented
- [ ] All router endpoints updated
- [ ] Error handling for Redis failures
- [ ] Tests added and passing

## Branch Name
`fix/p0-task-persistence`

## After Completion
1. Commit changes with message: `fix(backend): Replace in-memory task storage with Redis persistence`
2. Push branch to origin
3. Do NOT create PR (will be done by orchestrator)
