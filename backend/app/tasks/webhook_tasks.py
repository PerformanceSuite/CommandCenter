"""
Webhook delivery tasks for async event notification.
"""

import asyncio
import logging
from typing import Any, Dict

from app.database import AsyncSessionLocal
from app.services.webhook_service import WebhookService
from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.webhook_tasks.deliver_webhook",
    max_retries=0,  # Retries handled by WebhookService
    acks_late=True,
)
def deliver_webhook(self, delivery_id: int, attempt_number: int = 1) -> Dict[str, Any]:
    """
    Deliver a webhook to external system with retry logic.

    This task is responsible for attempting webhook delivery.
    Retry logic with exponential backoff is handled by WebhookService.

    Args:
        delivery_id: Webhook delivery ID
        attempt_number: Current attempt number (1-based)

    Returns:
        dict: Delivery result with status and details
    """
    try:
        # Use sync wrapper for async function
        result = asyncio.run(_deliver_webhook_async(delivery_id, attempt_number))
        return result
    except Exception as e:
        logger.exception(f"Error in deliver_webhook task: {e}")
        return {
            "status": "error",
            "delivery_id": delivery_id,
            "attempt_number": attempt_number,
            "error": str(e),
        }


async def _deliver_webhook_async(delivery_id: int, attempt_number: int) -> Dict[str, Any]:
    """
    Async implementation of webhook delivery.

    Args:
        delivery_id: Webhook delivery ID
        attempt_number: Current attempt number

    Returns:
        Delivery result dictionary
    """
    async with AsyncSessionLocal() as db:
        service = WebhookService(db)

        try:
            success = await service.deliver_webhook(delivery_id, attempt_number)

            if success:
                logger.info(
                    f"Webhook delivery {delivery_id} completed successfully "
                    f"(attempt {attempt_number})"
                )
                return {
                    "status": "success",
                    "delivery_id": delivery_id,
                    "attempt_number": attempt_number,
                }
            else:
                logger.warning(f"Webhook delivery {delivery_id} failed (attempt {attempt_number})")
                return {
                    "status": "failed",
                    "delivery_id": delivery_id,
                    "attempt_number": attempt_number,
                }
        finally:
            await service.close()


@celery_app.task(
    bind=True,
    name="app.tasks.webhook_tasks.create_and_deliver_webhook",
    max_retries=0,
)
def create_and_deliver_webhook(
    self,
    config_id: int,
    project_id: int,
    event_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a webhook delivery and immediately attempt delivery.

    This is a convenience task for triggering webhooks from other tasks.

    Args:
        config_id: Webhook configuration ID
        project_id: Project ID
        event_type: Event type
        payload: Event payload

    Returns:
        dict: Delivery result
    """
    try:
        result = asyncio.run(
            _create_and_deliver_webhook_async(config_id, project_id, event_type, payload)
        )
        return result
    except Exception as e:
        logger.exception(f"Error in create_and_deliver_webhook task: {e}")
        return {
            "status": "error",
            "config_id": config_id,
            "event_type": event_type,
            "error": str(e),
        }


async def _create_and_deliver_webhook_async(
    config_id: int,
    project_id: int,
    event_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Async implementation of create and deliver webhook.

    Args:
        config_id: Webhook configuration ID
        project_id: Project ID
        event_type: Event type
        payload: Event payload

    Returns:
        Delivery result dictionary
    """
    async with AsyncSessionLocal() as db:
        service = WebhookService(db)

        try:
            # Create delivery
            delivery = await service.create_delivery(
                config_id=config_id,
                project_id=project_id,
                event_type=event_type,
                payload=payload,
            )

            if not delivery:
                # Event filtered out or skipped
                return {
                    "status": "skipped",
                    "config_id": config_id,
                    "event_type": event_type,
                    "reason": "Event filtered or not subscribed",
                }

            # Immediately attempt delivery
            success = await service.deliver_webhook(delivery.id, attempt_number=1)

            return {
                "status": "success" if success else "failed",
                "delivery_id": delivery.id,
                "config_id": config_id,
                "event_type": event_type,
            }
        finally:
            await service.close()


@celery_app.task(
    bind=True,
    name="app.tasks.webhook_tasks.process_pending_deliveries",
    max_retries=0,
)
def process_pending_deliveries(self, max_deliveries: int = 100) -> Dict[str, Any]:
    """
    Process pending webhook deliveries (scheduled retries).

    This task should be run periodically (e.g., every 5 minutes) to handle
    delivery retries with exponential backoff.

    Args:
        max_deliveries: Maximum number of deliveries to process

    Returns:
        dict: Processing result with counts
    """
    try:
        result = asyncio.run(_process_pending_deliveries_async(max_deliveries))
        return result
    except Exception as e:
        logger.exception(f"Error in process_pending_deliveries task: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


async def _process_pending_deliveries_async(max_deliveries: int) -> Dict[str, Any]:
    """
    Async implementation of process pending deliveries.

    Args:
        max_deliveries: Maximum number of deliveries to process

    Returns:
        Processing result dictionary
    """
    async with AsyncSessionLocal() as db:
        service = WebhookService(db)

        try:
            # Get pending deliveries
            pending = await service.get_pending_deliveries(max_deliveries)

            if not pending:
                logger.debug("No pending webhook deliveries to process")
                return {
                    "status": "success",
                    "processed": 0,
                    "successful": 0,
                    "failed": 0,
                }

            logger.info(f"Processing {len(pending)} pending webhook deliveries")

            # Process each delivery
            successful = 0
            failed = 0

            for delivery in pending:
                try:
                    success = await service.deliver_webhook(
                        delivery.id, delivery.attempt_number + 1
                    )
                    if success:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.exception(f"Error processing webhook delivery {delivery.id}: {e}")
                    failed += 1

            logger.info(
                f"Processed {len(pending)} webhook deliveries: "
                f"{successful} successful, {failed} failed"
            )

            return {
                "status": "success",
                "processed": len(pending),
                "successful": successful,
                "failed": failed,
            }
        finally:
            await service.close()
