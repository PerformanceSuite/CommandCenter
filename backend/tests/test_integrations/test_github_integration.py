"""Tests for GitHub integration service."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.github_integration import GitHubIntegration
from app.models.integration import Integration, IntegrationStatus, IntegrationType
from app.models.research_task import ResearchTask


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_integration():
    """Create mock Integration model."""
    integration = MagicMock(spec=Integration)
    integration.id = 1
    integration.project_id = 1
    integration.integration_type = IntegrationType.GITHUB
    integration.status = IntegrationStatus.ACTIVE
    integration.enabled = True
    integration.access_token_encrypted = "encrypted_token"
    integration.config = {"webhook_secret": "test_secret"}
    integration.is_healthy = True
    integration.is_token_expired = False
    integration.needs_refresh = False
    return integration


class TestGitHubIntegrationInit:
    """Tests for GitHub integration initialization."""

    @pytest.mark.asyncio
    async def test_create_github_integration(self, mock_db_session):
        """Test creating GitHub integration."""
        integration = GitHubIntegration(integration_id=1, db=mock_db_session)

        assert integration.integration_id == 1
        assert integration.integration_type == IntegrationType.GITHUB

    @pytest.mark.asyncio
    async def test_load_integration(self, mock_db_session, mock_integration):
        """Test loading integration from database."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_integration
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)
        loaded = await integration.load()

        assert loaded == mock_integration


class TestIssuesSync:
    """Tests for GitHub Issues ↔ Research Tasks sync."""

    @pytest.mark.asyncio
    async def test_sync_new_issue_to_task(self, mock_db_session, mock_integration):
        """Test syncing new GitHub issue to research task."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            mock_integration,  # load()
            None,  # _find_task_by_issue() - no existing task
        ]
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)

        issue_data = {
            "number": 123,
            "title": "Test Issue",
            "body": "Issue description",
            "state": "open",
            "labels": [{"name": "priority: high"}],
            "html_url": "https://github.com/owner/repo/issues/123",
        }

        repository = {
            "id": 456,
            "full_name": "owner/repo",
        }

        # Execute
        task = await integration.sync_issue_to_task(
            issue_number=123,
            issue_data=issue_data,
            repository=repository,
        )

        # Verify
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called()
        assert task is not None

    @pytest.mark.asyncio
    async def test_sync_existing_issue_updates_task(self, mock_db_session, mock_integration):
        """Test syncing existing issue updates the task."""
        # Setup existing task
        existing_task = MagicMock(spec=ResearchTask)
        existing_task.id = 1
        existing_task.title = "Old Title"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            mock_integration,  # load()
            existing_task,  # _find_task_by_issue() - found
        ]
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)

        issue_data = {
            "number": 123,
            "title": "Updated Title",
            "body": "Updated description",
            "state": "open",
            "labels": [],
            "html_url": "https://github.com/owner/repo/issues/123",
        }

        repository = {"id": 456, "full_name": "owner/repo"}

        # Execute
        task = await integration.sync_issue_to_task(
            issue_number=123,
            issue_data=issue_data,
            repository=repository,
        )

        # Verify
        assert task == existing_task
        assert existing_task.title == "Updated Title"
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_issue_state_mapping(self, mock_db_session):
        """Test GitHub issue state maps correctly to task status."""
        integration = GitHubIntegration(integration_id=1, db=mock_db_session)

        assert integration._map_issue_state_to_task_status("open") == "todo"
        assert integration._map_issue_state_to_task_status("closed") == "done"

    @pytest.mark.asyncio
    async def test_priority_extraction_from_labels(self, mock_db_session):
        """Test extracting priority from GitHub labels."""
        integration = GitHubIntegration(integration_id=1, db=mock_db_session)

        # High priority
        labels_high = [{"name": "priority: high"}, {"name": "bug"}]
        assert integration._extract_priority_from_labels(labels_high) == "high"

        # Low priority
        labels_low = [{"name": "priority: low"}]
        assert integration._extract_priority_from_labels(labels_low) == "low"

        # Default (medium)
        labels_default = [{"name": "bug"}]
        assert integration._extract_priority_from_labels(labels_default) == "medium"


class TestWebhooks:
    """Tests for webhook handling."""

    @pytest.mark.asyncio
    async def test_webhook_signature_verification(self, mock_db_session, mock_integration):
        """Test webhook signature verification."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_integration
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)
        await integration.load()

        payload = b'{"action": "opened"}'
        secret = "test_secret"

        # Generate valid signature
        import hashlib
        import hmac

        valid_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        # Test valid signature
        assert integration.verify_webhook_signature(payload, valid_signature, secret) is True

        # Test invalid signature
        assert integration.verify_webhook_signature(payload, "invalid_signature", secret) is False

    @pytest.mark.asyncio
    async def test_handle_issues_webhook_opened(self, mock_db_session, mock_integration):
        """Test handling issues webhook when issue is opened."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            mock_integration,  # load()
            None,  # _find_task_by_issue()
        ]
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)

        payload = {
            "action": "opened",
            "issue": {
                "number": 123,
                "title": "New Issue",
                "body": "Description",
                "state": "open",
                "labels": [],
                "html_url": "https://github.com/owner/repo/issues/123",
            },
            "repository": {
                "id": 456,
                "full_name": "owner/repo",
            },
        }

        result = await integration.handle_webhook("issues", payload)

        assert result["status"] == "synced"
        assert result["action"] == "opened"
        mock_db_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_handle_pull_request_webhook(self, mock_db_session, mock_integration):
        """Test handling pull_request webhook."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_integration
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)

        payload = {
            "action": "opened",
            "pull_request": {
                "number": 42,
                "title": "Fix bug",
                "html_url": "https://github.com/owner/repo/pull/42",
            },
            "repository": {
                "full_name": "owner/repo",
            },
        }

        result = await integration.handle_webhook("pull_request", payload)

        assert result["status"] == "analysis_triggered"
        assert result["pr_number"] == 42


class TestConnectionAndHealth:
    """Tests for connection testing and health checks."""

    @pytest.mark.asyncio
    @patch("app.integrations.github_integration.Github")
    async def test_test_connection_success(
        self, mock_github_class, mock_db_session, mock_integration
    ):
        """Test successful connection test."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_integration
        mock_db_session.execute.return_value = mock_result

        mock_user = MagicMock()
        mock_user.login = "testuser"
        mock_github = MagicMock()
        mock_github.get_user.return_value = mock_user
        mock_github_class.return_value = mock_github

        with patch("app.integrations.github_integration.decrypt_value", return_value="test_token"):
            integration = GitHubIntegration(integration_id=1, db=mock_db_session)
            result = await integration.test_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_get_display_name(self, mock_db_session, mock_integration):
        """Test getting display name."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_integration
        mock_db_session.execute.return_value = mock_result

        with patch("app.integrations.github_integration.Github") as mock_github_class:
            mock_user = MagicMock()
            mock_user.login = "octocat"
            mock_github = MagicMock()
            mock_github.get_user.return_value = mock_user
            mock_github_class.return_value = mock_github

            with patch(
                "app.integrations.github_integration.decrypt_value", return_value="test_token"
            ):
                integration = GitHubIntegration(integration_id=1, db=mock_db_session)
                name = await integration.get_display_name()

        assert name == "GitHub: octocat"

    @pytest.mark.asyncio
    async def test_health_check(self, mock_db_session, mock_integration):
        """Test health check."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_integration
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)
        health = await integration.check_health()

        assert health["integration_id"] == 1
        assert health["integration_type"] == IntegrationType.GITHUB
        assert health["is_healthy"] is True


class TestErrorHandling:
    """Tests for error handling and recording."""

    @pytest.mark.asyncio
    async def test_record_success(self, mock_db_session, mock_integration):
        """Test recording successful operation."""
        mock_integration.success_count = 5
        mock_integration.error_count = 2

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_integration
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)
        await integration.record_success()

        assert mock_integration.success_count == 6
        assert mock_integration.error_count == 0  # Reset on success
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_record_error(self, mock_db_session, mock_integration):
        """Test recording error."""
        mock_integration.error_count = 2

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_integration
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)
        await integration.record_error("Test error message")

        assert mock_integration.error_count == 3
        assert mock_integration.last_error == "Test error message"
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_disable_after_multiple_errors(self, mock_db_session, mock_integration):
        """Test integration disabled after 5 consecutive errors."""
        mock_integration.error_count = 4  # One away from threshold

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_integration
        mock_db_session.execute.return_value = mock_result

        integration = GitHubIntegration(integration_id=1, db=mock_db_session)
        await integration.record_error("Fatal error")

        assert mock_integration.error_count == 5
        assert mock_integration.enabled is False
        assert mock_integration.status == IntegrationStatus.ERROR
