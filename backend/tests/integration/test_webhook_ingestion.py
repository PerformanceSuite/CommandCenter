"""
Integration tests for webhook ingestion
"""
import pytest
import hmac
import hashlib
import json
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_source import IngestionSource, SourceType
from app.models.project import Project


@pytest.fixture
async def github_webhook_source(db_session: AsyncSession, sample_project: Project) -> IngestionSource:
    """Create a GitHub webhook source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.WEBHOOK,
        name="GitHub Releases",
        url="/api/webhooks/github",
        priority=10,
        enabled=True,
        config={
            "secret": "test-secret-key",
            "events": ["release", "push"]
        }
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


@pytest.mark.asyncio
async def test_github_webhook_release_event(async_client: AsyncClient, github_webhook_source: IngestionSource):
    """Test processing GitHub release webhook"""
    payload = {
        "action": "published",
        "release": {
            "tag_name": "v1.0.0",
            "name": "Version 1.0.0",
            "body": "# Release Notes\n\n- Feature 1\n- Feature 2",
            "html_url": "https://github.com/user/repo/releases/tag/v1.0.0",
            "published_at": "2024-01-15T10:30:00Z"
        },
        "repository": {
            "full_name": "user/repo"
        }
    }

    # Generate signature (GitHub uses raw JSON bytes)
    secret = github_webhook_source.config['secret'].encode()
    payload_bytes = json.dumps(payload).encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()

    response = await async_client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={
            "X-Hub-Signature-256": f"sha256={signature}",
            "X-GitHub-Event": "release"
        }
    )

    assert response.status_code == 200
    assert response.json()['status'] == 'accepted'


@pytest.mark.asyncio
async def test_generic_webhook_with_custom_payload(async_client: AsyncClient, sample_project: Project):
    """Test processing generic webhook with custom payload"""
    payload = {
        "title": "New Documentation",
        "content": "Updated API documentation is available...",
        "url": "https://example.com/docs/api",
        "metadata": {
            "category": "documentation",
            "priority": 8
        }
    }

    response = await async_client.post(
        f"/api/webhooks/generic?project_id={sample_project.id}",
        json=payload,
        headers={"X-API-Key": "test-api-key"}
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_signature_verification_failure(async_client: AsyncClient, github_webhook_source: IngestionSource):
    """Test webhook rejected with invalid signature"""
    payload = {"test": "data"}

    response = await async_client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={
            "X-Hub-Signature-256": "sha256=invalidsignature",
            "X-GitHub-Event": "release"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_disabled_source(db_session: AsyncSession, async_client: AsyncClient, github_webhook_source: IngestionSource):
    """Test webhook rejected when source is disabled"""
    github_webhook_source.enabled = False
    await db_session.commit()

    payload = {"test": "data"}
    secret = github_webhook_source.config['secret'].encode()
    payload_bytes = json.dumps(payload).encode()
    signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()

    response = await async_client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={
            "X-Hub-Signature-256": f"sha256={signature}",
            "X-GitHub-Event": "push"
        }
    )

    assert response.status_code == 403
