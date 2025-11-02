"""
Integration tests for webhook ingestion
"""
import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_source import IngestionSource, SourceType
from app.models.project import Project


@pytest.fixture(autouse=True)
def mock_celery_task():
    """Mock Celery task execution for all tests"""
    with patch("app.routers.webhooks_ingestion.process_webhook_payload") as mock_task:
        mock_result = MagicMock()
        mock_result.id = "test-task-id-123"
        mock_task.delay.return_value = mock_result
        yield mock_task


@pytest.fixture
async def github_webhook_source(
    db_session: AsyncSession, sample_project: Project
) -> IngestionSource:
    """Create a GitHub webhook source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.WEBHOOK,
        name="GitHub Releases",
        url="/api/webhooks/github",
        priority=10,
        enabled=True,
        config={"secret": "test-secret-key", "events": ["release", "push"]},
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


@pytest.mark.asyncio
async def test_github_webhook_release_event(
    async_client: AsyncClient, github_webhook_source: IngestionSource
):
    """Test processing GitHub release webhook"""
    payload = {
        "action": "published",
        "release": {
            "tag_name": "v1.0.0",
            "name": "Version 1.0.0",
            "body": "# Release Notes\n\n- Feature 1\n- Feature 2",
            "html_url": "https://github.com/user/repo/releases/tag/v1.0.0",
            "published_at": "2024-01-15T10:30:00Z",
        },
        "repository": {"full_name": "user/repo"},
    }

    # Generate signature (GitHub uses raw JSON bytes)
    secret = github_webhook_source.config["secret"].encode()
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()

    response = await async_client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}", "X-GitHub-Event": "release"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_generic_webhook_with_custom_payload(
    async_client: AsyncClient, sample_project: Project
):
    """Test processing generic webhook with custom payload"""
    payload = {
        "title": "New Documentation",
        "content": "Updated API documentation is available...",
        "url": "https://example.com/docs/api",
        "metadata": {"category": "documentation", "priority": 8},
    }

    response = await async_client.post(
        f"/api/webhooks/generic?project_id={sample_project.id}",
        json=payload,
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_signature_verification_failure(
    async_client: AsyncClient, github_webhook_source: IngestionSource
):
    """Test webhook rejected with invalid signature"""
    payload = {"test": "data"}

    response = await async_client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={"X-Hub-Signature-256": "sha256=invalidsignature", "X-GitHub-Event": "release"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_disabled_source(
    db_session: AsyncSession, async_client: AsyncClient, github_webhook_source: IngestionSource
):
    """Test webhook rejected when source is disabled"""
    github_webhook_source.enabled = False
    await db_session.commit()

    payload = {"test": "data"}
    secret = github_webhook_source.config["secret"].encode()
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()

    response = await async_client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}", "X-GitHub-Event": "push"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_github_webhook_push_event(
    async_client: AsyncClient, github_webhook_source: IngestionSource
):
    """Test processing GitHub push webhook with commits"""
    payload = {
        "ref": "refs/heads/main",
        "commits": [
            {
                "id": "abc123",
                "message": "Add new feature",
                "author": {"name": "Developer", "email": "dev@example.com"},
                "timestamp": "2024-01-15T10:30:00Z",
                "url": "https://github.com/user/repo/commit/abc123",
            },
            {
                "id": "def456",
                "message": "Fix bug",
                "author": {"name": "Developer", "email": "dev@example.com"},
                "timestamp": "2024-01-15T11:00:00Z",
                "url": "https://github.com/user/repo/commit/def456",
            },
        ],
        "repository": {"full_name": "user/repo"},
    }

    # Generate signature
    secret = github_webhook_source.config["secret"].encode()
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()

    response = await async_client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}", "X-GitHub-Event": "push"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert "task_id" in response.json()


@pytest.mark.asyncio
async def test_github_webhook_event_filtering(
    async_client: AsyncClient, github_webhook_source: IngestionSource
):
    """Test that ignored events return status='ignored'"""
    payload = {"action": "opened", "issue": {"number": 42, "title": "Test issue"}}

    # Generate signature
    secret = github_webhook_source.config["secret"].encode()
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()

    response = await async_client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={
            "X-Hub-Signature-256": f"sha256={signature}",
            "X-GitHub-Event": "issues",  # Not in allowed events list
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert response.json()["event"] == "issues"


@pytest.mark.asyncio
async def test_generic_webhook_missing_required_fields(
    async_client: AsyncClient, sample_project: Project, monkeypatch
):
    """Test generic webhook with missing required fields returns 400"""
    monkeypatch.setenv("GENERIC_WEBHOOK_API_KEY", "test-api-key")

    # Missing 'title' field
    payload = {"content": "Some content", "url": "https://example.com/docs"}

    response = await async_client.post(
        f"/api/webhooks/generic?project_id={sample_project.id}",
        json=payload,
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == 400
    assert "title" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_github_webhook_non_existent_source(async_client: AsyncClient):
    """Test webhook with non-existent source_id returns 404"""
    payload = {"test": "data"}

    # Use a source_id that doesn't exist
    response = await async_client.post(
        "/api/webhooks/github?source_id=99999",
        json=payload,
        headers={"X-Hub-Signature-256": "sha256=fakesignature", "X-GitHub-Event": "release"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_webhook_task_queuing_verification(
    async_client: AsyncClient, github_webhook_source: IngestionSource
):
    """Test that webhook returns task_id for queued task"""
    payload = {
        "action": "published",
        "release": {"tag_name": "v2.0.0", "name": "Version 2.0.0", "body": "Release notes"},
    }

    # Generate signature
    secret = github_webhook_source.config["secret"].encode()
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()

    response = await async_client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}", "X-GitHub-Event": "release"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert "task_id" in response_data
    assert response_data["task_id"] is not None
    assert response_data["status"] == "accepted"
