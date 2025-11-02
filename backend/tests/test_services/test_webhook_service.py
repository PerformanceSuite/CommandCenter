"""
Tests for WebhookService
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.models import Project, Repository, WebhookConfig, WebhookDelivery
from app.services.webhook_service import DeliveryStatus, WebhookService


@pytest.fixture
async def webhook_config(db_session):
    """Create a test webhook configuration."""
    # Create project
    project = Project(
        name="Test Project",
        owner="test-owner",
        description="Test project for webhooks",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create repository
    repo = Repository(
        project_id=project.id,
        name="test-repo",
        owner="test-owner",
        full_name="test-owner/test-repo",
        description="Test repository",
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)

    # Create webhook config
    config = WebhookConfig(
        project_id=project.id,
        repository_id=repo.id,
        webhook_url="https://example.com/webhook",
        secret="test-secret-key",
        events=["analysis.complete", "export.complete"],
        active=True,
        retry_count=3,
        retry_delay_seconds=300,
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    return config


@pytest.fixture
def webhook_service(db_session):
    """Create webhook service instance."""
    return WebhookService(db_session)


class TestWebhookServiceCreation:
    """Test webhook delivery creation."""

    @pytest.mark.asyncio
    async def test_create_delivery_success(self, webhook_service, webhook_config, db_session):
        """Test successful webhook delivery creation."""
        payload = {
            "event_type": "analysis.complete",
            "timestamp": datetime.utcnow().isoformat(),
            "repository": "test-owner/test-repo",
            "analysis_id": 123,
        }

        delivery = await webhook_service.create_delivery(
            config_id=webhook_config.id,
            project_id=webhook_config.project_id,
            event_type="analysis.complete",
            payload=payload,
        )

        assert delivery is not None
        assert delivery.config_id == webhook_config.id
        assert delivery.project_id == webhook_config.project_id
        assert delivery.event_type == "analysis.complete"
        assert delivery.payload == payload
        assert delivery.target_url == webhook_config.webhook_url
        assert delivery.status == DeliveryStatus.PENDING
        assert delivery.attempt_number == 1

    @pytest.mark.asyncio
    async def test_create_delivery_with_custom_target_url(
        self, webhook_service, webhook_config, db_session
    ):
        """Test delivery creation with custom target URL."""
        custom_url = "https://custom.example.com/webhook"
        payload = {"event_type": "export.complete", "timestamp": datetime.utcnow().isoformat()}

        delivery = await webhook_service.create_delivery(
            config_id=webhook_config.id,
            project_id=webhook_config.project_id,
            event_type="export.complete",
            payload=payload,
            target_url=custom_url,
        )

        assert delivery.target_url == custom_url

    @pytest.mark.asyncio
    async def test_create_delivery_filtered_event(
        self, webhook_service, webhook_config, db_session
    ):
        """Test that unsubscribed events are filtered."""
        payload = {"event_type": "unsubscribed.event"}

        delivery = await webhook_service.create_delivery(
            config_id=webhook_config.id,
            project_id=webhook_config.project_id,
            event_type="unsubscribed.event",
            payload=payload,
        )

        assert delivery is None

    @pytest.mark.asyncio
    async def test_create_delivery_wildcard_event(
        self, webhook_service, webhook_config, db_session
    ):
        """Test wildcard event matching."""
        # Update config to use wildcard
        webhook_config.events = ["analysis.*"]
        db_session.add(webhook_config)
        await db_session.commit()

        payload = {"event_type": "analysis.started"}

        delivery = await webhook_service.create_delivery(
            config_id=webhook_config.id,
            project_id=webhook_config.project_id,
            event_type="analysis.started",
            payload=payload,
        )

        assert delivery is not None
        assert delivery.event_type == "analysis.started"


class TestWebhookDelivery:
    """Test webhook delivery logic."""

    @pytest.mark.asyncio
    async def test_successful_delivery(self, webhook_service, webhook_config, db_session):
        """Test successful webhook delivery."""
        # Create delivery
        payload = {"event_type": "test.event", "data": "test"}
        delivery = await webhook_service.create_delivery(
            config_id=webhook_config.id,
            project_id=webhook_config.project_id,
            event_type="test.event",
            payload=payload,
        )

        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "received"}'

        with patch.object(webhook_service.http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            success = await webhook_service.deliver_webhook(delivery.id, attempt_number=1)

            assert success is True
            assert mock_post.called
            assert mock_post.call_args[0][0] == webhook_config.webhook_url

            # Verify delivery was updated
            await db_session.refresh(delivery)
            assert delivery.status == DeliveryStatus.DELIVERED
            assert delivery.http_status_code == 200
            assert delivery.attempted_at is not None
            assert delivery.completed_at is not None
            assert delivery.duration_ms is not None

    @pytest.mark.asyncio
    async def test_delivery_with_signature(self, webhook_service, webhook_config, db_session):
        """Test that delivery includes HMAC signature."""
        payload = {"event_type": "test.event"}
        delivery = await webhook_service.create_delivery(
            config_id=webhook_config.id,
            project_id=webhook_config.project_id,
            event_type="test.event",
            payload=payload,
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch.object(webhook_service.http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await webhook_service.deliver_webhook(delivery.id, attempt_number=1)

            # Verify signature header was included
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert "X-Hub-Signature-256" in headers
            assert headers["X-Hub-Signature-256"].startswith("sha256=")

    @pytest.mark.asyncio
    async def test_delivery_failure_with_retry(self, webhook_service, webhook_config, db_session):
        """Test delivery failure triggers retry."""
        payload = {"event_type": "test.event"}
        delivery = await webhook_service.create_delivery(
            config_id=webhook_config.id,
            project_id=webhook_config.project_id,
            event_type="test.event",
            payload=payload,
        )

        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(webhook_service.http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            success = await webhook_service.deliver_webhook(delivery.id, attempt_number=1)

            assert success is False

            # Verify delivery marked for retry
            await db_session.refresh(delivery)
            assert delivery.status == DeliveryStatus.RETRYING
            assert delivery.error_message is not None
            assert delivery.scheduled_for > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_delivery_exhausts_retries(self, webhook_service, webhook_config, db_session):
        """Test delivery exhausts all retries."""
        payload = {"event_type": "test.event"}
        delivery = await webhook_service.create_delivery(
            config_id=webhook_config.id,
            project_id=webhook_config.project_id,
            event_type="test.event",
            payload=payload,
        )

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Error"

        with patch.object(webhook_service.http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Attempt delivery with max retries
            success = await webhook_service.deliver_webhook(
                delivery.id, attempt_number=webhook_config.retry_count
            )

            assert success is False

            # Verify delivery exhausted
            await db_session.refresh(delivery)
            assert delivery.status == DeliveryStatus.EXHAUSTED

    @pytest.mark.asyncio
    async def test_delivery_timeout(self, webhook_service, webhook_config, db_session):
        """Test delivery timeout handling."""
        payload = {"event_type": "test.event"}
        delivery = await webhook_service.create_delivery(
            config_id=webhook_config.id,
            project_id=webhook_config.project_id,
            event_type="test.event",
            payload=payload,
        )

        with patch.object(webhook_service.http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            success = await webhook_service.deliver_webhook(delivery.id, attempt_number=1)

            assert success is False

            # Verify error recorded
            await db_session.refresh(delivery)
            assert "Timeout" in delivery.error_message


class TestRetryLogic:
    """Test retry logic and exponential backoff."""

    def test_calculate_retry_delay(self, webhook_service):
        """Test exponential backoff calculation."""
        base_delay = 300  # 5 minutes

        # Attempt 1: 300s (5 min)
        delay_1 = webhook_service._calculate_retry_delay(1, base_delay)
        assert delay_1 == 300

        # Attempt 2: 600s (10 min)
        delay_2 = webhook_service._calculate_retry_delay(2, base_delay)
        assert delay_2 == 600

        # Attempt 3: 1200s (20 min)
        delay_3 = webhook_service._calculate_retry_delay(3, base_delay)
        assert delay_3 == 1200


class TestEventFiltering:
    """Test event filtering logic."""

    def test_should_deliver_exact_match(self, webhook_service, webhook_config):
        """Test exact event type matching."""
        assert webhook_service._should_deliver_event(webhook_config, "analysis.complete")
        assert webhook_service._should_deliver_event(webhook_config, "export.complete")
        assert not webhook_service._should_deliver_event(webhook_config, "other.event")

    def test_should_deliver_wildcard(self, webhook_service, webhook_config):
        """Test wildcard event matching."""
        webhook_config.events = ["analysis.*", "export.complete"]

        assert webhook_service._should_deliver_event(webhook_config, "analysis.started")
        assert webhook_service._should_deliver_event(webhook_config, "analysis.complete")
        assert webhook_service._should_deliver_event(webhook_config, "analysis.failed")
        assert webhook_service._should_deliver_event(webhook_config, "export.complete")
        assert not webhook_service._should_deliver_event(webhook_config, "export.started")

    def test_should_deliver_no_events(self, webhook_service, webhook_config):
        """Test that empty events list allows all."""
        webhook_config.events = []

        assert webhook_service._should_deliver_event(webhook_config, "any.event")
        assert webhook_service._should_deliver_event(webhook_config, "another.event")


class TestPayloadValidation:
    """Test payload validation."""

    def test_validate_valid_payload(self, webhook_service):
        """Test valid payload validation."""
        payload = {
            "event_type": "test.event",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"key": "value"},
        }

        assert webhook_service._validate_payload(payload) is True

    def test_validate_minimal_payload(self, webhook_service):
        """Test minimal valid payload."""
        payload = {"event_type": "test.event", "timestamp": datetime.utcnow().isoformat()}

        assert webhook_service._validate_payload(payload) is True

    def test_validate_invalid_payload(self, webhook_service):
        """Test invalid payload (not a dict)."""
        assert webhook_service._validate_payload("invalid") is False
        assert webhook_service._validate_payload(None) is False
        assert webhook_service._validate_payload([]) is False


class TestStatistics:
    """Test delivery statistics."""

    @pytest.mark.asyncio
    async def test_get_delivery_statistics(self, webhook_service, webhook_config, db_session):
        """Test delivery statistics calculation."""
        # Update config with some deliveries
        webhook_config.total_deliveries = 10
        webhook_config.successful_deliveries = 7
        webhook_config.failed_deliveries = 3
        db_session.add(webhook_config)
        await db_session.commit()

        stats = await webhook_service.get_delivery_statistics(webhook_config.id)

        assert stats["total_configs"] == 1
        assert stats["total_deliveries"] == 10
        assert stats["successful_deliveries"] == 7
        assert stats["failed_deliveries"] == 3
        assert stats["success_rate"] == 70.0

    @pytest.mark.asyncio
    async def test_get_delivery_statistics_no_deliveries(
        self, webhook_service, webhook_config, db_session
    ):
        """Test statistics with no deliveries."""
        stats = await webhook_service.get_delivery_statistics(webhook_config.id)

        assert stats["total_deliveries"] == 0
        assert stats["success_rate"] == 0.0


class TestPendingDeliveries:
    """Test pending delivery retrieval."""

    @pytest.mark.asyncio
    async def test_get_pending_deliveries(self, webhook_service, webhook_config, db_session):
        """Test retrieving pending deliveries."""
        # Create some deliveries
        for i in range(3):
            delivery = WebhookDelivery(
                project_id=webhook_config.project_id,
                config_id=webhook_config.id,
                event_type="test.event",
                payload={"index": i},
                target_url=webhook_config.webhook_url,
                status=DeliveryStatus.PENDING if i < 2 else DeliveryStatus.RETRYING,
                attempt_number=1,
                scheduled_for=datetime.utcnow() - timedelta(minutes=i),
            )
            db_session.add(delivery)

        await db_session.commit()

        # Get pending deliveries
        pending = await webhook_service.get_pending_deliveries(max_deliveries=10)

        assert len(pending) == 3
        # Should be ordered by scheduled_for
        assert pending[0].payload["index"] == 2  # Oldest scheduled

    @pytest.mark.asyncio
    async def test_get_pending_deliveries_respects_scheduled_time(
        self, webhook_service, webhook_config, db_session
    ):
        """Test that future scheduled deliveries are not returned."""
        # Create delivery scheduled for future
        future_delivery = WebhookDelivery(
            project_id=webhook_config.project_id,
            config_id=webhook_config.id,
            event_type="test.event",
            payload={},
            target_url=webhook_config.webhook_url,
            status=DeliveryStatus.PENDING,
            attempt_number=1,
            scheduled_for=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(future_delivery)
        await db_session.commit()

        pending = await webhook_service.get_pending_deliveries()

        assert len(pending) == 0
