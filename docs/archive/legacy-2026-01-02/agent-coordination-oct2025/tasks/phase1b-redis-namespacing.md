# Phase 1b: Redis Namespacing Agent

## Mission
Namespace all Redis cache keys by project_id to prevent cache collisions.

## Priority
CRITICAL - Prevents cache data leaks

## Estimated Time
3 hours

## Tasks

### 1. Update RedisService (1.5 hours)
```python
# backend/app/services/redis_service.py

class RedisService:
    def _make_key(self, project_id: int, key_type: str, identifier: str) -> str:
        """Generate namespaced key: project:{id}:{type}:{identifier}"""
        return f"project:{project_id}:{key_type}:{identifier}"

    async def get(self, project_id: int, key_type: str, identifier: str):
        key = self._make_key(project_id, key_type, identifier)
        return await self.redis.get(key)

    async def set(self, project_id: int, key_type: str, identifier: str, value, ttl=3600):
        key = self._make_key(project_id, key_type, identifier)
        return await self.redis.setex(key, ttl, value)

    async def delete_pattern(self, project_id: int, pattern: str):
        """Delete all keys matching project:id:pattern"""
        full_pattern = f"project:{project_id}:{pattern}"
        keys = await self.redis.keys(full_pattern)
        if keys:
            await self.redis.delete(*keys)
```

### 2. Update All Cache Calls (1 hour)
Update all places using RedisService to pass project_id:
- GitHub API caching
- Rate limit tracking
- Repository info caching

### 3. Add Tests (30 min)
Test cache isolation:
- Project A sets key, Project B can't read it
- Project A invalidates cache, Project B unaffected
- Pattern matching only affects project's keys

## Success Criteria
- ✅ All Redis keys include project_id
- ✅ Cache isolation verified
- ✅ No cross-project cache access
- ✅ Tests pass
