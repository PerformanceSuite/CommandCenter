"""
Unit tests for GitHub service
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime
from github import GithubException

from app.services.github_service import GitHubService
from tests.utils import MockGitHubRepo, MockGitHubCommit


@pytest.mark.unit
class TestGitHubService:
    """Test GitHubService class"""

    def test_init_with_token(self):
        """Test GitHubService initialization with token"""
        service = GitHubService(access_token="test_token")
        assert service.token == "test_token"

    def test_init_without_token(self):
        """Test GitHubService initialization without token"""
        service = GitHubService()
        assert service.token is not None  # Uses config default

    @pytest.mark.asyncio
    async def test_authenticate_repo_success(self, mocker):
        """Test successful repository authentication"""
        mock_repo = MockGitHubRepo()
        mock_github = mocker.MagicMock()
        mock_github.get_repo.return_value = mock_repo

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        result = await service.authenticate_repo("testowner", "testrepo")

        assert result is True
        mock_github.get_repo.assert_called_once_with("testowner/testrepo")

    @pytest.mark.asyncio
    async def test_authenticate_repo_failure(self, mocker):
        """Test failed repository authentication"""
        mock_github = mocker.MagicMock()
        mock_github.get_repo.side_effect = GithubException(
            status=401,
            data={"message": "Bad credentials"}
        )

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        result = await service.authenticate_repo("testowner", "testrepo")

        assert result is False

    @pytest.mark.asyncio
    async def test_authenticate_repo_other_error(self, mocker):
        """Test repository authentication with non-auth error"""
        mock_github = mocker.MagicMock()
        mock_github.get_repo.side_effect = GithubException(
            status=404,
            data={"message": "Not found"}
        )

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        with pytest.raises(GithubException):
            await service.authenticate_repo("testowner", "testrepo")

    @pytest.mark.asyncio
    async def test_list_user_repos(self, mocker):
        """Test listing user repositories"""
        mock_repos = [
            MockGitHubRepo(name="repo1", owner="user1"),
            MockGitHubRepo(name="repo2", owner="user1"),
        ]

        mock_user = mocker.MagicMock()
        mock_user.get_repos.return_value = mock_repos

        mock_github = mocker.MagicMock()
        mock_github.get_user.return_value = mock_user

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        result = await service.list_user_repos(username="user1")

        assert len(result) == 2
        assert result[0]["name"] == "repo1"
        assert result[1]["name"] == "repo2"
        assert result[0]["owner"] == "user1"

    @pytest.mark.asyncio
    async def test_list_authenticated_user_repos(self, mocker):
        """Test listing authenticated user's repositories"""
        mock_repos = [MockGitHubRepo(name="myrepo")]

        mock_user = mocker.MagicMock()
        mock_user.get_repos.return_value = mock_repos

        mock_github = mocker.MagicMock()
        mock_github.get_user.return_value = mock_user

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        result = await service.list_user_repos()

        assert len(result) == 1
        assert result[0]["name"] == "myrepo"

    @pytest.mark.asyncio
    async def test_sync_repository_success(self, mocker):
        """Test successful repository sync"""
        mock_commit = MockGitHubCommit(
            sha="abc123",
            message="Test commit",
            author="Test Author"
        )

        mock_commits = mocker.MagicMock()
        mock_commits.totalCount = 1
        mock_commits.__getitem__ = lambda self, idx: mock_commit

        mock_repo = MockGitHubRepo()
        mock_repo.get_commits = mocker.MagicMock(return_value=mock_commits)

        mock_github = mocker.MagicMock()
        mock_github.get_repo.return_value = mock_repo

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        result = await service.sync_repository("testowner", "testrepo")

        assert result["synced"] is True
        assert result["full_name"] == "testowner/testrepo"
        assert result["last_commit_sha"] == "abc123"
        assert result["changes_detected"] is False

    @pytest.mark.asyncio
    async def test_sync_repository_with_changes(self, mocker):
        """Test repository sync detecting changes"""
        mock_commit = MockGitHubCommit(sha="def456")

        mock_commits = mocker.MagicMock()
        mock_commits.totalCount = 1
        mock_commits.__getitem__ = lambda self, idx: mock_commit

        mock_repo = MockGitHubRepo()
        mock_repo.get_commits = mocker.MagicMock(return_value=mock_commits)

        mock_github = mocker.MagicMock()
        mock_github.get_repo.return_value = mock_repo

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        # Pass old SHA to detect changes
        result = await service.sync_repository(
            "testowner",
            "testrepo",
            last_known_sha="abc123"
        )

        assert result["changes_detected"] is True
        assert result["last_commit_sha"] == "def456"

    @pytest.mark.asyncio
    async def test_get_repository_info(self, mocker):
        """Test getting repository information"""
        mock_repo = MockGitHubRepo(
            owner="testowner",
            name="testrepo",
            description="Test repository",
            stars=100,
            language="Python"
        )

        mock_github = mocker.MagicMock()
        mock_github.get_repo.return_value = mock_repo

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        result = await service.get_repository_info("testowner", "testrepo")

        assert result["owner"] == "testowner"
        assert result["name"] == "testrepo"
        assert result["description"] == "Test repository"
        assert result["stars"] == 100
        assert result["language"] == "Python"
        assert "topics" in result

    @pytest.mark.asyncio
    async def test_search_repositories(self, mocker):
        """Test searching repositories"""
        mock_repos = [
            MockGitHubRepo(name="result1", description="First result"),
            MockGitHubRepo(name="result2", description="Second result"),
        ]

        mock_github = mocker.MagicMock()
        mock_github.search_repositories.return_value = mock_repos

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        result = await service.search_repositories("python", max_results=10)

        assert len(result) == 2
        assert result[0]["name"] == "result1"
        assert result[1]["name"] == "result2"

    @pytest.mark.asyncio
    async def test_search_repositories_max_results(self, mocker):
        """Test searching repositories with max_results limit"""
        mock_repos = [MockGitHubRepo(name=f"repo{i}") for i in range(20)]

        mock_github = mocker.MagicMock()
        mock_github.search_repositories.return_value = mock_repos

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        result = await service.search_repositories("test", max_results=5)

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_list_user_repos_error(self, mocker):
        """Test error handling in list_user_repos"""
        mock_github = mocker.MagicMock()
        mock_github.get_user.side_effect = GithubException(
            status=404,
            data={"message": "User not found"}
        )

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        with pytest.raises(Exception) as exc_info:
            await service.list_user_repos(username="nonexistent")

        assert "Failed to list repositories" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_github_api_error_handling(self, mocker):
        """GitHubService handles API errors gracefully."""
        mock_github = mocker.MagicMock()
        mock_github.get_repo.side_effect = GithubException(
            status=403,
            data={"message": "Rate limit exceeded"}
        )

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        with pytest.raises(Exception) as exc_info:
            await service.get_repository_info("owner", "repo")

        assert "Failed to get repository info" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_github_search_error_handling(self, mocker):
        """GitHubService handles search errors gracefully."""
        mock_github = mocker.MagicMock()
        mock_github.search_repositories.side_effect = GithubException(
            status=422,
            data={"message": "Validation failed"}
        )

        service = GitHubService(access_token="test_token")
        service.github = mock_github

        with pytest.raises(Exception) as exc_info:
            await service.search_repositories("invalid query")

        assert "Failed to search repositories" in str(exc_info.value)
