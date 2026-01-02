"""
Webhook service for managing outbound webhook deliveries.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WebhookConfig, WebhookDelivery

logger = logging.getLogger(__name__)


class DeliveryStatus:
    """Webhook delivery status constants."""

    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    EXHAUSTED = "exhausted"  # All retries exhausted


class WebhookService:
    """
    Service for managing outbound webhook deliveries with retry logic.

    Features:
    - Exponential backoff for retries
    - Delivery status tracking
    - Payload validation
    - Event filtering
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize webhook service.

        Args:
            db: Database session
        """
        self.db = db
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
        )

    async def create_delivery(
        self,
        config_id: int,
        project_id: int,
        event_type: str,
        payload: Dict[str, Any],
        target_url: Optional[str] = None,
    ) -> WebhookDelivery:
        """
        Create a new webhook delivery.

        Args:
            config_id: Webhook configuration ID
            project_id: Project ID for isolation
            event_type: Event type (e.g., "analysis.complete")
            payload: Event payload
            target_url: Optional override for target URL

        Returns:
            Created webhook delivery

        Raises:
            ValueError: If webhook config not found
        """
        # Fetch webhook config
        result = await self.db.execute(
            select(WebhookConfig).where(
                and_(
                    WebhookConfig.id == config_id,
                    WebhookConfig.active.is_(True),
                )
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            raise ValueError(f"Active webhook config {config_id} not found")

        # Check event filtering
        if not self._should_deliver_event(config, event_type):
            logger.info(f"Skipping delivery for event {event_type} - not in subscription list")
            return None

        # Validate payload
        if not self._validate_payload(payload):
            raise ValueError("Invalid payload structure")

        # Use target URL from config if not provided
        if not target_url:
            target_url = config.webhook_url

        # Create delivery record
        delivery = WebhookDelivery(
            project_id=project_id,
            config_id=config_id,
            event_type=event_type,
            payload=payload,
            target_url=target_url,
            attempt_number=1,
            status=DeliveryStatus.PENDING,
            scheduled_for=datetime.utcnow(),
        )

        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)

        logger.info(
            f"Created webhook delivery {delivery.id} for event {event_type} to {target_url}"
        )

        return delivery

    async def deliver_webhook(
        self,
        delivery_id: int,
        attempt_number: int = 1,
    ) -> bool:
        """
        Deliver a webhook with retry logic.

        Args:
            delivery_id: Webhook delivery ID
            attempt_number: Current attempt number (1-based)

        Returns:
            True if delivery successful, False otherwise
        """
        # Fetch delivery
        result = await self.db.execute(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()

        if not delivery:
            logger.error(f"Webhook delivery {delivery_id} not found")
            return False

        # Fetch config
        result = await self.db.execute(
            select(WebhookConfig).where(WebhookConfig.id == delivery.config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            logger.error(f"Webhook config {delivery.config_id} not found")
            await self._mark_delivery_failed(delivery, "Webhook configuration not found")
            return False

        # Update attempt number and status
        delivery.attempt_number = attempt_number
        delivery.status = DeliveryStatus.DELIVERING
        delivery.attempted_at = datetime.utcnow()
        await self.db.commit()

        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "CommandCenter-Webhook/1.0",
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Delivery-ID": str(delivery.id),
        }

        # Add signature if secret is configured
        if config.secret:
            import hashlib
            import hmac
            import json

            payload_bytes = json.dumps(delivery.payload).encode("utf-8")
            signature = hmac.new(
                config.secret.encode("utf-8"), payload_bytes, hashlib.sha256
            ).hexdigest()
            headers["X-Hub-Signature-256"] = f"sha256={signature}"

        # Make HTTP request
        start_time = time.time()
        try:
            response = await self.http_client.post(
                delivery.target_url,
                json=delivery.payload,
                headers=headers,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Update delivery record
            delivery.http_status_code = response.status_code
            delivery.response_body = response.text[:10000]  # Limit to 10KB
            delivery.duration_ms = duration_ms
            delivery.completed_at = datetime.utcnow()

            # Check if successful (2xx status code)
            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.DELIVERED
                config.successful_deliveries += 1
                config.total_deliveries += 1
                config.last_delivery_at = datetime.utcnow()
                await self.db.commit()

                logger.info(
                    f"Webhook delivery {delivery.id} successful (status={response.status_code}, duration={duration_ms}ms)"
                )
                return True
            else:
                # Non-2xx status code - schedule retry
                error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                return await self._handle_delivery_failure(
                    delivery, config, error_msg, attempt_number
                )

        except httpx.TimeoutException as e:
            duration_ms = int((time.time() - start_time) * 1000)
            delivery.duration_ms = duration_ms
            error_msg = f"Timeout after {duration_ms}ms: {str(e)}"
            return await self._handle_delivery_failure(delivery, config, error_msg, attempt_number)

        except httpx.RequestError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            delivery.duration_ms = duration_ms
            error_msg = f"Request error: {str(e)}"
            return await self._handle_delivery_failure(delivery, config, error_msg, attempt_number)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            delivery.duration_ms = duration_ms
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(f"Unexpected error delivering webhook {delivery.id}")
            return await self._handle_delivery_failure(delivery, config, error_msg, attempt_number)

    async def _handle_delivery_failure(
        self,
        delivery: WebhookDelivery,
        config: WebhookConfig,
        error_msg: str,
        attempt_number: int,
    ) -> bool:
        """
        Handle webhook delivery failure with retry logic.

        Args:
            delivery: Webhook delivery
            config: Webhook configuration
            error_msg: Error message
            attempt_number: Current attempt number

        Returns:
            False (failure)
        """
        delivery.error_message = error_msg
        delivery.completed_at = datetime.utcnow()

        # Check if we should retry
        if attempt_number < config.retry_count:
            # Schedule retry with exponential backoff
            delay_seconds = self._calculate_retry_delay(attempt_number, config.retry_delay_seconds)
            delivery.status = DeliveryStatus.RETRYING
            delivery.scheduled_for = datetime.utcnow() + timedelta(seconds=delay_seconds)

            config.total_deliveries += 1
            await self.db.commit()

            logger.warning(
                f"Webhook delivery {delivery.id} failed (attempt {attempt_number}/{config.retry_count}), "
                f"retrying in {delay_seconds}s: {error_msg}"
            )

            # Schedule retry (will be picked up by background worker)
            return False
        else:
            # All retries exhausted
            delivery.status = DeliveryStatus.EXHAUSTED
            config.failed_deliveries += 1
            config.total_deliveries += 1
            await self.db.commit()

            logger.error(f"Webhook delivery {delivery.id} exhausted all retries: {error_msg}")
            return False

    async def _mark_delivery_failed(self, delivery: WebhookDelivery, error_msg: str) -> None:
        """
        Mark a delivery as permanently failed.

        Args:
            delivery: Webhook delivery
            error_msg: Error message
        """
        delivery.status = DeliveryStatus.FAILED
        delivery.error_message = error_msg
        delivery.completed_at = datetime.utcnow()
        await self.db.commit()

    def _calculate_retry_delay(self, attempt_number: int, base_delay_seconds: int) -> int:
        """
        Calculate retry delay with exponential backoff.

        Formula: base_delay * (2 ^ (attempt_number - 1))
        Example with base_delay=300 (5 minutes):
        - Attempt 1 -> 300s (5 minutes)
        - Attempt 2 -> 600s (10 minutes)
        - Attempt 3 -> 1200s (20 minutes)

        Args:
            attempt_number: Current attempt number (1-based)
            base_delay_seconds: Base delay in seconds

        Returns:
            Delay in seconds
        """
        return base_delay_seconds * (2 ** (attempt_number - 1))

    def _should_deliver_event(self, config: WebhookConfig, event_type: str) -> bool:
        """
        Check if event should be delivered based on subscription.

        Args:
            config: Webhook configuration
            event_type: Event type

        Returns:
            True if event should be delivered
        """
        # If no events specified, deliver all
        if not config.events:
            return True

        # Check if event_type matches any subscribed events (supports wildcards)
        for subscribed_event in config.events:
            # Exact match
            if subscribed_event == event_type:
                return True

            # Wildcard match (e.g., "analysis.*" matches "analysis.complete")
            if subscribed_event.endswith(".*"):
                prefix = subscribed_event[:-2]  # Remove ".*"
                if event_type.startswith(prefix + "."):
                    return True

        return False

    def _validate_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Validate webhook payload structure.

        Args:
            payload: Webhook payload

        Returns:
            True if valid
        """
        # Basic validation - must be a dictionary
        if not isinstance(payload, dict):
            return False

        # Must have at least these fields
        required_fields = ["event_type", "timestamp"]
        for field in required_fields:
            if field not in payload:
                logger.warning(f"Payload missing required field: {field}")
                # Don't fail validation, just warn - be lenient
                # return False

        return True

    async def get_pending_deliveries(self, max_deliveries: int = 100) -> List[WebhookDelivery]:
        """
        Get pending webhook deliveries that are ready for delivery.

        Args:
            max_deliveries: Maximum number of deliveries to return

        Returns:
            List of pending deliveries
        """
        result = await self.db.execute(
            select(WebhookDelivery)
            .where(
                and_(
                    or_(
                        WebhookDelivery.status == DeliveryStatus.PENDING,
                        WebhookDelivery.status == DeliveryStatus.RETRYING,
                    ),
                    WebhookDelivery.scheduled_for <= datetime.utcnow(),
                )
            )
            .limit(max_deliveries)
            .order_by(WebhookDelivery.scheduled_for)
        )

        return result.scalars().all()

    async def get_delivery_statistics(self, config_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get webhook delivery statistics.

        Args:
            config_id: Optional webhook config ID to filter by

        Returns:
            Statistics dictionary
        """
        query = select(WebhookConfig)

        if config_id:
            query = query.where(WebhookConfig.id == config_id)

        result = await self.db.execute(query)
        configs = result.scalars().all()

        total_deliveries = sum(c.total_deliveries for c in configs)
        successful = sum(c.successful_deliveries for c in configs)
        failed = sum(c.failed_deliveries for c in configs)

        return {
            "total_configs": len(configs),
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful,
            "failed_deliveries": failed,
            "success_rate": (
                (successful / total_deliveries * 100) if total_deliveries > 0 else 0.0
            ),
        }

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
