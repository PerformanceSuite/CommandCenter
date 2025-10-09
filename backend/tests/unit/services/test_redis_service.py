"""
Unit tests for RedisService with project-level namespacing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.redis_service import RedisService


@pytest.fixture
def redis_service():
    """Create a RedisService instance for testing"""
    service = RedisService()
    service.enabled = True
    service.redis_client = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_make_key_format():
    """Test that keys follow correct namespace pattern"""
    redis = RedisService()

    key = redis._make_key(123, "repo", "owner/name")
    assert key == "project:123:repo:owner/name"

    key = redis._make_key(456, "rate_limit", "github_api")
    assert key == "project:456:rate_limit:github_api"

    key = redis._make_key(789, "pr", "18")
    assert key == "project:789:pr:18"


@pytest.mark.asyncio
async def test_cache_isolation_between_projects(redis_service):
    """Test that Project A cannot read Project B's cache"""
    # Mock redis get to return different values for different keys
    async def mock_get(key):
        if key == "project:1:repo:owner/name":
            return '{"data": "project1_data"}'
        elif key == "project:2:repo:owner/name":
            return '{"data": "project2_data"}'
        return None

    redis_service.redis_client.get = AsyncMock(side_effect=mock_get)

    # Each project reads only their own data
    result1 = await redis_service.get(1, "repo", "owner/name")
    assert result1 == {"data": "project1_data"}

    result2 = await redis_service.get(2, "repo", "owner/name")
    assert result2 == {"data": "project2_data"}

    # Verify the correct keys were requested
    calls = redis_service.redis_client.get.call_args_list
    assert len(calls) == 2
    assert calls[0][0][0] == "project:1:repo:owner/name"
    assert calls[1][0][0] == "project:2:repo:owner/name"


@pytest.mark.asyncio
async def test_set_with_project_namespacing(redis_service):
    """Test that set operations use project namespacing"""
    await redis_service.set(123, "repo", "owner/name", {"test": "data"}, ttl=600)

    # Verify setex was called with correct key and TTL
    redis_service.redis_client.setex.assert_called_once()
    call_args = redis_service.redis_client.setex.call_args[0]
    assert call_args[0] == "project:123:repo:owner/name"
    assert call_args[1] == 600  # TTL
    assert '{"test": "data"}' in call_args[2]  # JSON serialized value


@pytest.mark.asyncio
async def test_set_with_default_ttl(redis_service):
    """Test that set uses default TTL when not specified"""
    await redis_service.set(123, "repo", "owner/name", {"test": "data"})

    # Verify default TTL of 3600 seconds (1 hour)
    redis_service.redis_client.setex.assert_called_once()
    call_args = redis_service.redis_client.setex.call_args[0]
    assert call_args[1] == 3600  # Default TTL


@pytest.mark.asyncio
async def test_delete_with_project_namespacing(redis_service):
    """Test that delete operations use project namespacing"""
    await redis_service.delete(123, "repo", "owner/name")

    # Verify delete was called with correct key
    redis_service.redis_client.delete.assert_called_once_with("project:123:repo:owner/name")


@pytest.mark.asyncio
async def test_pattern_delete_only_affects_project(redis_service):
    """Test that pattern deletion is isolated by project"""
    # Mock scan_iter to return keys for the pattern
    async def mock_scan_iter(match):
        if match == "project:1:repo:*":
            return iter(["project:1:repo:repo1", "project:1:repo:repo2"])
        elif match == "project:2:repo:*":
            return iter(["project:2:repo:repo1"])
        return iter([])

    redis_service.redis_client.scan_iter = AsyncMock(side_effect=mock_scan_iter)
    redis_service.redis_client.delete = AsyncMock(return_value=2)

    # Delete all repo keys for project 1
    deleted = await redis_service.delete_pattern(1, "repo:*")
    assert deleted == 2

    # Verify correct pattern was used
    redis_service.redis_client.scan_iter.assert_called_with(match="project:1:repo:*")
    redis_service.redis_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_exists_with_project_namespacing(redis_service):
    """Test that exists check uses project namespacing"""
    redis_service.redis_client.exists = AsyncMock(return_value=1)

    result = await redis_service.exists(123, "repo", "owner/name")
    assert result is True

    # Verify exists was called with correct key
    redis_service.redis_client.exists.assert_called_once_with("project:123:repo:owner/name")


@pytest.mark.asyncio
async def test_exists_returns_false_when_not_found(redis_service):
    """Test that exists returns False when key doesn't exist"""
    redis_service.redis_client.exists = AsyncMock(return_value=0)

    result = await redis_service.exists(123, "repo", "owner/name")
    assert result is False


@pytest.mark.asyncio
async def test_get_returns_none_when_disabled():
    """Test that get returns None when Redis is disabled"""
    redis = RedisService()
    redis.enabled = False

    result = await redis.get(123, "repo", "owner/name")
    assert result is None


@pytest.mark.asyncio
async def test_set_returns_false_when_disabled():
    """Test that set returns False when Redis is disabled"""
    redis = RedisService()
    redis.enabled = False

    result = await redis.set(123, "repo", "owner/name", {"test": "data"})
    assert result is False


@pytest.mark.asyncio
async def test_get_handles_json_decode_error(redis_service):
    """Test that get handles JSON decode errors gracefully"""
    redis_service.redis_client.get = AsyncMock(return_value='invalid json{')

    result = await redis_service.get(123, "repo", "owner/name")
    # Should return None and log error (not raise exception)
    assert result is None


@pytest.mark.asyncio
async def test_multiple_projects_same_key_type():
    """Test that multiple projects can cache same key type without collision"""
    redis = RedisService()

    # Different projects, same key type and identifier
    key1 = redis._make_key(100, "repo", "test")
    key2 = redis._make_key(200, "repo", "test")
    key3 = redis._make_key(300, "repo", "test")

    # All keys should be unique
    assert key1 == "project:100:repo:test"
    assert key2 == "project:200:repo:test"
    assert key3 == "project:300:repo:test"
    assert len({key1, key2, key3}) == 3  # All unique


@pytest.mark.asyncio
async def test_delete_pattern_with_no_matches(redis_service):
    """Test that delete_pattern handles no matches gracefully"""
    # Mock scan_iter to return empty iterator
    async def mock_scan_iter(match):
        return iter([])

    redis_service.redis_client.scan_iter = AsyncMock(side_effect=mock_scan_iter)

    deleted = await redis_service.delete_pattern(123, "nonexistent:*")
    assert deleted == 0

    # delete should not be called if no keys found
    redis_service.redis_client.delete.assert_not_called()


@pytest.mark.asyncio
async def test_deprecated_make_cache_key_warning():
    """Test that deprecated make_cache_key logs warning"""
    redis = RedisService()

    with patch('app.services.redis_service.logger') as mock_logger:
        result = redis.make_cache_key("part1", "part2", "part3")

        # Should still work but log warning
        assert result == "part1:part2:part3"
        mock_logger.warning.assert_called_once()
        assert "deprecated" in mock_logger.warning.call_args[0][0].lower()
