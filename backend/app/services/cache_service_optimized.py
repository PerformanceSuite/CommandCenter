"""
Enhanced Redis Cache Service with performance optimizations.
Adds cache stampede prevention, batch operations, and monitoring.
"""

import json
import hashlib
import pickle
from typing import Optional, Any, Callable, Awaitable, List, TypeVar, Union, Dict
from datetime import timedelta
from functools import wraps
import asyncio

# Lazy imports
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

T = TypeVar("T")


class OptimizedCacheService:
    """
    High-performance caching service with Redis backend.
    Includes cache stampede prevention, pattern invalidation,
    and performance monitoring.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: timedelta = timedelta(minutes=5),
        prefix: str = "cc",
    ):
        """
        Initialize optimized cache service.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live for cached items
            prefix: Global prefix for all cache keys
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not installed. Install with: pip install redis")

        import os

        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.default_ttl = default_ttl
        self.prefix = prefix
        self.redis_client: Optional[redis.Redis] = None
        self._locks = {}  # Local lock registry

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client with connection pooling."""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # Allow binary data
                max_connections=20,  # Connection pool size
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 1,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                },
                health_check_interval=30,
            )
        return self.redis_client

    def _generate_key(self, namespace: str, params: Union[dict, str]) -> str:
        """Generate a cache key from namespace and parameters."""
        if isinstance(params, str):
            return f"{self.prefix}:{namespace}:{params}"

        param_str = json.dumps(params, sort_keys=True, default=str)
        hash_digest = hashlib.md5(param_str.encode()).hexdigest()[:16]
        return f"{self.prefix}:{namespace}:{hash_digest}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with automatic deserialization."""
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value is None:
                return None

            # Try JSON first, fallback to pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value)
                except Exception:
                    return value.decode() if isinstance(value, bytes) else value
        except Exception as e:
            print(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """Set value in cache with automatic serialization."""
        try:
            client = await self._get_client()
            ttl = ttl or self.default_ttl

            # Serialize value
            try:
                data = json.dumps(value, default=str)
            except (TypeError, ValueError):
                data = pickle.dumps(value)

            return await client.setex(key, int(ttl.total_seconds()), data)
        except Exception as e:
            print(f"Cache set error for {key}: {e}")
            return False

    async def get_or_set(
        self,
        namespace: str,
        params: Union[dict, str],
        fetch_func: Callable[[], Awaitable[T]],
        ttl: Optional[timedelta] = None,
        force_refresh: bool = False,
    ) -> T:
        """
        Get from cache or fetch and cache with stampede prevention.

        Args:
            namespace: Cache namespace
            params: Parameters for cache key
            fetch_func: Async function to fetch data if not cached
            ttl: Time-to-live
            force_refresh: Force cache refresh

        Returns:
            Cached or freshly fetched data
        """
        cache_key = self._generate_key(namespace, params)

        # Check cache first
        if not force_refresh:
            cached = await self.get(cache_key)
            if cached is not None:
                return cached

        # Prevent cache stampede with distributed lock
        client = await self._get_client()
        lock_key = f"{cache_key}:lock"
        lock_acquired = False

        try:
            # Try to acquire lock (expires after 30 seconds)
            lock_acquired = await client.set(lock_key, "1", nx=True, ex=30)

            if not lock_acquired:
                # Another process is fetching, wait briefly
                for _ in range(50):  # Max 5 seconds wait
                    await asyncio.sleep(0.1)
                    cached = await self.get(cache_key)
                    if cached is not None:
                        return cached

            # Fetch fresh data
            data = await fetch_func()
            await self.set(cache_key, data, ttl)
            return data

        finally:
            # Release lock if we acquired it
            if lock_acquired:
                await client.delete(lock_key)

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values in a single operation."""
        try:
            client = await self._get_client()
            values = await client.mget(keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            result[key] = pickle.loads(value)
                        except Exception:
                            result[key] = value
            return result
        except Exception as e:
            print(f"Cache mget error: {e}")
            return {}

    async def mset(self, items: Dict[str, Any], ttl: Optional[timedelta] = None) -> bool:
        """Set multiple values in a single operation."""
        try:
            client = await self._get_client()
            ttl = ttl or self.default_ttl
            ttl_seconds = int(ttl.total_seconds())

            # Prepare pipeline for atomic operation
            pipe = client.pipeline()

            for key, value in items.items():
                try:
                    data = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    data = pickle.dumps(value)
                pipe.setex(key, ttl_seconds, data)

            await pipe.execute()
            return True
        except Exception as e:
            print(f"Cache mset error: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern using SCAN."""
        try:
            client = await self._get_client()

            # Add prefix if not present
            if not pattern.startswith(self.prefix):
                pattern = f"{self.prefix}:{pattern}"

            deleted = 0
            cursor = 0

            # Use SCAN for better performance
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += await client.delete(*keys)
                if cursor == 0:
                    break

            return deleted
        except Exception as e:
            print(f"Cache invalidate pattern error: {e}")
            return 0

    async def get_stats(self) -> dict:
        """Get comprehensive cache statistics."""
        try:
            client = await self._get_client()
            info = await client.info("stats")
            memory = await client.info("memory")

            # Calculate hit rate
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total_ops = hits + misses
            hit_rate = (hits / total_ops * 100) if total_ops > 0 else 0

            return {
                "total_keys": await client.dbsize(),
                "memory_used": memory.get("used_memory_human"),
                "memory_peak": memory.get("used_memory_peak_human"),
                "hits": hits,
                "misses": misses,
                "hit_rate": round(hit_rate, 2),
                "evicted_keys": info.get("evicted_keys", 0),
                "connected_clients": info.get("connected_clients", 0),
                "ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {}

    def cached(
        self,
        namespace: str,
        ttl: Optional[timedelta] = None,
        key_func: Optional[Callable] = None,
    ):
        """
        Decorator for caching function results.

        Example:
            @cache.cached("tech:list", ttl=timedelta(minutes=10))
            async def list_technologies(**filters):
                return await db.query(Technology).filter(**filters)
        """

        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                # Generate cache key
                if key_func:
                    cache_params = key_func(*args, **kwargs)
                else:
                    # Default: use function name and all arguments
                    cache_params = {
                        "func": func.__name__,
                        "args": str(args),
                        "kwargs": str(sorted(kwargs.items())),
                    }

                return await self.get_or_set(
                    namespace=namespace,
                    params=cache_params,
                    fetch_func=lambda: func(*args, **kwargs),
                    ttl=ttl,
                )

            return wrapper

        return decorator

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None


class CacheMetrics:
    """Performance metrics for cache operations."""

    def __init__(self, cache_service: OptimizedCacheService):
        self.cache = cache_service
        self.operations = {"gets": 0, "sets": 0, "hits": 0, "misses": 0, "errors": 0}

    async def record_get(self, hit: bool):
        """Record a cache get operation."""
        self.operations["gets"] += 1
        if hit:
            self.operations["hits"] += 1
        else:
            self.operations["misses"] += 1

    async def record_set(self):
        """Record a cache set operation."""
        self.operations["sets"] += 1

    async def record_error(self):
        """Record a cache error."""
        self.operations["errors"] += 1

    def get_metrics(self) -> dict:
        """Get current metrics."""
        total_gets = self.operations["gets"]
        hit_rate = self.operations["hits"] / total_gets * 100 if total_gets > 0 else 0

        return {**self.operations, "hit_rate": round(hit_rate, 2)}

    def reset(self):
        """Reset metrics."""
        for key in self.operations:
            self.operations[key] = 0


# Global cache instance management
_cache_instance: Optional[OptimizedCacheService] = None


async def get_cache_service() -> OptimizedCacheService:
    """Get or create global cache service instance."""
    global _cache_instance

    if _cache_instance is None:
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _cache_instance = OptimizedCacheService(redis_url=redis_url)

    return _cache_instance


# Example usage patterns
async def cache_technology_list(
    filters: dict, fetch_func: Callable, ttl: timedelta = timedelta(minutes=5)
):
    """Cache technology list queries."""
    cache = await get_cache_service()
    return await cache.get_or_set(
        namespace="tech:list", params=filters, fetch_func=fetch_func, ttl=ttl
    )


async def cache_job_stats(
    project_id: Optional[int],
    fetch_func: Callable,
    ttl: timedelta = timedelta(minutes=2),
):
    """Cache job statistics."""
    cache = await get_cache_service()
    params = {"project_id": project_id} if project_id else {}
    return await cache.get_or_set(
        namespace="job:stats", params=params, fetch_func=fetch_func, ttl=ttl
    )


async def invalidate_technology_cache():
    """Invalidate all technology-related caches."""
    cache = await get_cache_service()
    return await cache.invalidate_pattern("tech:*")
