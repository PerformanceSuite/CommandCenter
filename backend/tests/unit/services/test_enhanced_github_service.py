"""
Unit tests for EnhancedGitHubService project ID generation and cache namespacing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.enhanced_github_service import EnhancedGitHubService
from app.services.redis_service import RedisService


@pytest.fixture
def mock_redis():
    """Create a mock Redis service"""
    redis = AsyncMock(spec=RedisService)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    redis.delete_pattern = AsyncMock(return_value=0)
    return redis


@pytest.fixture
def github_service(mock_redis):
    """Create an EnhancedGitHubService instance with mock Redis"""
    with patch('app.services.enhanced_github_service.Github'):
        service = EnhancedGitHubService(
            access_token="test_token",
            redis_service=mock_redis
        )
        return service


def test_get_project_id_with_explicit_repository_id(mock_redis):
    """Test that explicit repository_id is used when provided"""
    service = EnhancedGitHubService(
        redis_service=mock_redis,
        repository_id=12345
    )

    project_id = service._get_project_id("owner", "repo")
    assert project_id == 12345


def test_get_project_id_generates_stable_hash():
    """Test that project ID is stable for same owner/repo"""
    service = EnhancedGitHubService()

    # Same owner/repo should always generate same project_id
    id1 = service._get_project_id("testowner", "testrepo")
    id2 = service._get_project_id("testowner", "testrepo")
    assert id1 == id2

    # Different repos should generate different IDs
    id3 = service._get_project_id("testowner", "otherrepo")
    assert id1 != id3

    # Different owners should generate different IDs
    id4 = service._get_project_id("otherowner", "testrepo")
    assert id1 != id4


def test_get_project_id_case_insensitive():
    """Test that project ID generation is case-insensitive"""
    service = EnhancedGitHubService()

    id1 = service._get_project_id("TestOwner", "TestRepo")
    id2 = service._get_project_id("testowner", "testrepo")
    id3 = service._get_project_id("TESTOWNER", "TESTREPO")

    # All should generate same ID
    assert id1 == id2 == id3


def test_get_project_id_returns_positive_integer():
    """Test that generated project IDs are positive integers"""
    service = EnhancedGitHubService()

    project_id = service._get_project_id("owner", "repo")
    assert isinstance(project_id, int)
    assert project_id > 0
    assert project_id < 2**63  # Within 64-bit signed integer range


@pytest.mark.asyncio
async def test_get_repository_info_uses_project_namespacing(github_service, mock_redis):
    """Test that get_repository_info uses project-namespaced cache"""
    # Mock GitHub API response
    mock_repo = MagicMock()
    mock_repo.owner.login = "testowner"
    mock_repo.name = "testrepo"
    mock_repo.full_name = "testowner/testrepo"
    mock_repo.description = "Test repo"
    mock_repo.html_url = "https://github.com/testowner/testrepo"
    mock_repo.clone_url = "https://github.com/testowner/testrepo.git"
    mock_repo.default_branch = "main"
    mock_repo.private = False
    mock_repo.stargazers_count = 10
    mock_repo.forks_count = 5
    mock_repo.language = "Python"
    mock_repo.id = 12345
    mock_repo.created_at = None
    mock_repo.updated_at = None
    mock_repo.get_topics.return_value = []
    mock_repo.has_issues = True
    mock_repo.has_wiki = True
    mock_repo.has_pages = False
    mock_repo.open_issues_count = 3

    github_service.github.get_repo = MagicMock(return_value=mock_repo)

    # Call get_repository_info
    result = await github_service.get_repository_info("testowner", "testrepo")

    # Verify Redis get was called with project namespacing
    mock_redis.get.assert_called_once()
    call_args = mock_redis.get.call_args[0]
    project_id = call_args[0]
    key_type = call_args[1]
    identifier = call_args[2]

    assert isinstance(project_id, int)
    assert project_id > 0
    assert key_type == "repo"
    assert identifier == "testowner/testrepo"

    # Verify Redis set was called with project namespacing
    mock_redis.set.assert_called_once()
    set_call_args = mock_redis.set.call_args[0]
    assert set_call_args[0] == project_id  # Same project_id
    assert set_call_args[1] == "repo"
    assert set_call_args[2] == "testowner/testrepo"


@pytest.mark.asyncio
async def test_list_pull_requests_uses_project_namespacing(github_service, mock_redis):
    """Test that list_pull_requests uses project-namespaced cache"""
    # Mock GitHub API response
    mock_pr = MagicMock()
    mock_pr.number = 1
    mock_pr.title = "Test PR"
    mock_pr.state = "open"
    mock_pr.user.login = "testuser"
    mock_pr.created_at = None
    mock_pr.updated_at = None
    mock_pr.merged = False
    mock_pr.mergeable = True
    mock_pr.head.ref = "feature-branch"
    mock_pr.base.ref = "main"
    mock_pr.html_url = "https://github.com/testowner/testrepo/pull/1"

    mock_repo = MagicMock()
    mock_repo.get_pulls.return_value = [mock_pr]
    github_service.github.get_repo = MagicMock(return_value=mock_repo)

    # Call list_pull_requests
    result = await github_service.list_pull_requests("testowner", "testrepo", state="open")

    # Verify Redis get was called with project namespacing
    mock_redis.get.assert_called_once()
    call_args = mock_redis.get.call_args[0]
    project_id = call_args[0]
    key_type = call_args[1]
    identifier = call_args[2]

    assert isinstance(project_id, int)
    assert project_id > 0
    assert key_type == "prs"
    assert identifier == "testowner/testrepo:open"

    # Verify Redis set was called with project namespacing and short TTL
    mock_redis.set.assert_called_once()
    set_call_args = mock_redis.set.call_args[0]
    set_call_kwargs = mock_redis.set.call_args[1]
    assert set_call_args[0] == project_id
    assert set_call_args[1] == "prs"
    assert set_call_args[2] == "testowner/testrepo:open"
    assert set_call_kwargs['ttl'] == 60  # Short TTL for PRs


@pytest.mark.asyncio
async def test_invalidate_cache_uses_project_namespacing(github_service, mock_redis):
    """Test that invalidate_cache uses project-namespaced pattern"""
    await github_service.invalidate_cache("testowner", "testrepo")

    # Verify delete_pattern was called with project namespacing
    mock_redis.delete_pattern.assert_called_once()
    call_args = mock_redis.delete_pattern.call_args[0]
    project_id = call_args[0]
    pattern = call_args[1]

    assert isinstance(project_id, int)
    assert project_id > 0
    assert pattern == "*"  # Delete all entries for this project


@pytest.mark.asyncio
async def test_different_repos_get_different_project_ids(github_service, mock_redis):
    """Test that different repositories get different project IDs in cache"""
    # Mock GitHub API
    mock_repo = MagicMock()
    mock_repo.owner.login = "owner"
    mock_repo.name = "repo"
    mock_repo.full_name = "owner/repo"
    mock_repo.description = "Test"
    mock_repo.html_url = "https://github.com/owner/repo"
    mock_repo.clone_url = "https://github.com/owner/repo.git"
    mock_repo.default_branch = "main"
    mock_repo.private = False
    mock_repo.stargazers_count = 0
    mock_repo.forks_count = 0
    mock_repo.language = "Python"
    mock_repo.id = 123
    mock_repo.created_at = None
    mock_repo.updated_at = None
    mock_repo.get_topics.return_value = []
    mock_repo.has_issues = True
    mock_repo.has_wiki = True
    mock_repo.has_pages = False
    mock_repo.open_issues_count = 0

    github_service.github.get_repo = MagicMock(return_value=mock_repo)

    # Fetch info for two different repos
    await github_service.get_repository_info("owner1", "repo1")
    project_id_1 = mock_redis.set.call_args[0][0]

    mock_redis.reset_mock()

    await github_service.get_repository_info("owner2", "repo2")
    project_id_2 = mock_redis.set.call_args[0][0]

    # Project IDs should be different
    assert project_id_1 != project_id_2


@pytest.mark.asyncio
async def test_cache_hit_doesnt_call_github_api(github_service, mock_redis):
    """Test that cache hit prevents GitHub API call"""
    # Mock Redis to return cached data
    cached_data = {
        "owner": "testowner",
        "name": "testrepo",
        "full_name": "testowner/testrepo",
        "description": "Cached repo"
    }
    mock_redis.get = AsyncMock(return_value=cached_data)

    # Call get_repository_info
    result = await github_service.get_repository_info("testowner", "testrepo")

    # Should return cached data
    assert result == cached_data

    # GitHub API should NOT be called
    github_service.github.get_repo.assert_not_called()
