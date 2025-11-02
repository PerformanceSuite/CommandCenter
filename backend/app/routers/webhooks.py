"""
GitHub webhook management endpoints
"""

import logging
import time
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.models import WebhookConfig, WebhookEvent, WebhookDelivery, Repository
from app.schemas import (
    WebhookConfigCreate,
    WebhookConfigUpdate,
    WebhookConfigResponse,
    WebhookEventResponse,
    WebhookDeliveryCreate,
    WebhookDeliveryResponse,
    WebhookDeliveryListResponse,
    WebhookStatisticsResponse,
)
from app.services.webhook_service import WebhookService
from app.utils.webhook_verification import verify_github_signature
from app.services.metrics_service import metrics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github", status_code=status.HTTP_200_OK)
async def receive_github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Receive and process GitHub webhook events

    Args:
        request: FastAPI request object
        x_github_event: GitHub event type
        x_github_delivery: GitHub delivery ID
        x_hub_signature_256: GitHub signature
        db: Database session

    Returns:
        Success message
    """
    start_time = time.time()

    try:
        # Get raw body for signature verification
        body = await request.body()
        payload = await request.json()

        # Extract repository info from payload
        repository_full_name = None
        if "repository" in payload:
            repository_full_name = payload["repository"]["full_name"]

        # Find webhook configuration for this repository
        webhook_config = None
        if repository_full_name:
            # Try to find repository and its webhook config
            result = await db.execute(
                select(Repository).where(Repository.full_name == repository_full_name)
            )
            repo = result.scalar_one_or_none()

            if repo:
                result = await db.execute(
                    select(WebhookConfig)
                    .where(WebhookConfig.repository_id == repo.id)
                    .where(WebhookConfig.active is True)
                )
                webhook_config = result.scalar_one_or_none()

        # Verify signature if we have a webhook config
        if webhook_config:
            verify_github_signature(body, webhook_config.secret, x_hub_signature_256)

        # Record webhook event receipt
        metrics_service.record_webhook_event(x_github_event, repository_full_name or "unknown")

        # Check if event already processed (idempotency)
        result = await db.execute(
            select(WebhookEvent).where(WebhookEvent.delivery_id == x_github_delivery)
        )
        existing_event = result.scalar_one_or_none()

        if existing_event:
            logger.info(f"Webhook event {x_github_delivery} already processed")
            return {
                "status": "already_processed",
                "delivery_id": x_github_delivery,
            }

        # Store webhook event
        webhook_event = WebhookEvent(
            config_id=webhook_config.id if webhook_config else None,
            event_type=x_github_event,
            delivery_id=x_github_delivery,
            payload=payload,
            repository_full_name=repository_full_name,
            processed=False,
            received_at=datetime.utcnow(),
        )
        db.add(webhook_event)

        # Update webhook config last delivery time
        if webhook_config:
            webhook_config.last_delivery_at = datetime.utcnow()

        await db.commit()

        # Process the webhook event asynchronously
        await process_webhook_event(webhook_event, db)

        duration = time.time() - start_time
        metrics_service.record_webhook_processed(x_github_event, duration)

        logger.info(f"Successfully processed webhook event {x_github_delivery} ({x_github_event})")

        return {
            "status": "success",
            "event_type": x_github_event,
            "delivery_id": x_github_delivery,
        }

    except Exception as e:
        duration = time.time() - start_time
        metrics_service.record_webhook_failed(x_github_event, type(e).__name__)
        logger.error(f"Failed to process webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        )


async def process_webhook_event(event: WebhookEvent, db: AsyncSession):
    """
    Process a webhook event

    Args:
        event: Webhook event to process
        db: Database session
    """
    try:
        # Process different event types
        if event.event_type == "push":
            await process_push_event(event, db)
        elif event.event_type == "pull_request":
            await process_pr_event(event, db)
        elif event.event_type == "issues":
            await process_issue_event(event, db)

        # Mark as processed
        event.processed = True
        event.processed_at = datetime.utcnow()
        await db.commit()

    except Exception as e:
        event.error = str(e)
        await db.commit()
        logger.error(f"Failed to process webhook event {event.delivery_id}: {e}")


async def process_push_event(event: WebhookEvent, db: AsyncSession):
    """Process push webhook event"""
    payload = event.payload
    logger.info(f"Processing push event for {event.repository_full_name}")

    # Find repository and trigger sync
    if event.repository_full_name:
        result = await db.execute(
            select(Repository).where(Repository.full_name == event.repository_full_name)
        )
        repo = result.scalar_one_or_none()

        if repo:
            # Update last commit info
            if "head_commit" in payload and payload["head_commit"]:
                commit = payload["head_commit"]
                repo.last_commit_sha = commit.get("id")
                repo.last_commit_message = commit.get("message")
                repo.last_commit_author = commit.get("author", {}).get("name")
                repo.last_commit_date = (
                    datetime.fromisoformat(commit.get("timestamp").replace("Z", "+00:00"))
                    if commit.get("timestamp")
                    else None
                )

            await db.commit()
            logger.info(f"Updated repository {repo.full_name} from push event")


async def process_pr_event(event: WebhookEvent, db: AsyncSession):
    """Process pull request webhook event"""
    payload = event.payload
    action = payload.get("action")
    logger.info(f"Processing PR event ({action}) for {event.repository_full_name}")

    # You can add custom logic here, e.g., auto-label PRs, trigger reviews, etc.


async def process_issue_event(event: WebhookEvent, db: AsyncSession):
    """Process issue webhook event"""
    payload = event.payload
    action = payload.get("action")
    logger.info(f"Processing issue event ({action}) for {event.repository_full_name}")

    # You can add custom logic here, e.g., auto-label issues, notifications, etc.


@router.post(
    "/configs",
    response_model=WebhookConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook_config(
    config_data: WebhookConfigCreate, db: AsyncSession = Depends(get_db)
) -> WebhookConfig:
    """
    Create a new webhook configuration

    Args:
        config_data: Webhook configuration data
        db: Database session

    Returns:
        Created webhook configuration
    """
    # Verify repository exists
    result = await db.execute(select(Repository).where(Repository.id == config_data.repository_id))
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {config_data.repository_id} not found",
        )

    # Check if webhook config already exists
    result = await db.execute(
        select(WebhookConfig).where(WebhookConfig.repository_id == config_data.repository_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Webhook configuration already exists for repository {config_data.repository_id}",
        )

    # Create webhook config
    webhook_config = WebhookConfig(
        repository_id=config_data.repository_id,
        webhook_url=config_data.webhook_url,
        secret=config_data.secret,
        events=config_data.events,
        active=True,
    )

    db.add(webhook_config)
    await db.commit()
    await db.refresh(webhook_config)

    return webhook_config


@router.get("/configs", response_model=List[WebhookConfigResponse])
async def list_webhook_configs(
    repository_id: int = None, db: AsyncSession = Depends(get_db)
) -> List[WebhookConfig]:
    """
    List webhook configurations

    Args:
        repository_id: Optional filter by repository ID
        db: Database session

    Returns:
        List of webhook configurations
    """
    query = select(WebhookConfig)

    if repository_id:
        query = query.where(WebhookConfig.repository_id == repository_id)

    result = await db.execute(query.order_by(desc(WebhookConfig.created_at)))
    return result.scalars().all()


@router.get("/configs/{config_id}", response_model=WebhookConfigResponse)
async def get_webhook_config(config_id: int, db: AsyncSession = Depends(get_db)) -> WebhookConfig:
    """
    Get webhook configuration by ID

    Args:
        config_id: Webhook configuration ID
        db: Database session

    Returns:
        Webhook configuration
    """
    result = await db.execute(select(WebhookConfig).where(WebhookConfig.id == config_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook configuration {config_id} not found",
        )

    return config


@router.patch("/configs/{config_id}", response_model=WebhookConfigResponse)
async def update_webhook_config(
    config_id: int,
    config_data: WebhookConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> WebhookConfig:
    """
    Update webhook configuration

    Args:
        config_id: Webhook configuration ID
        config_data: Update data
        db: Database session

    Returns:
        Updated webhook configuration
    """
    result = await db.execute(select(WebhookConfig).where(WebhookConfig.id == config_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook configuration {config_id} not found",
        )

    # Update fields
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_config(config_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """
    Delete webhook configuration

    Args:
        config_id: Webhook configuration ID
        db: Database session
    """
    result = await db.execute(select(WebhookConfig).where(WebhookConfig.id == config_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook configuration {config_id} not found",
        )

    await db.delete(config)
    await db.commit()


@router.get("/events", response_model=List[WebhookEventResponse])
async def list_webhook_events(
    event_type: str = None,
    repository_full_name: str = None,
    processed: bool = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> List[WebhookEvent]:
    """
    List webhook events

    Args:
        event_type: Optional filter by event type
        repository_full_name: Optional filter by repository
        processed: Optional filter by processed status
        limit: Maximum number of events to return
        db: Database session

    Returns:
        List of webhook events
    """
    query = select(WebhookEvent)

    if event_type:
        query = query.where(WebhookEvent.event_type == event_type)

    if repository_full_name:
        query = query.where(WebhookEvent.repository_full_name == repository_full_name)

    if processed is not None:
        query = query.where(WebhookEvent.processed == processed)

    result = await db.execute(query.order_by(desc(WebhookEvent.received_at)).limit(limit))
    return result.scalars().all()


# ===== Webhook Delivery Endpoints =====


@router.post(
    "/deliveries",
    response_model=WebhookDeliveryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook_delivery(
    delivery_data: WebhookDeliveryCreate,
    db: AsyncSession = Depends(get_db),
) -> WebhookDelivery:
    """
    Create a new webhook delivery

    Args:
        delivery_data: Webhook delivery data
        db: Database session

    Returns:
        Created webhook delivery
    """
    # TODO: Get project_id from auth context (currently hardcoded)
    project_id = 1

    service = WebhookService(db)
    try:
        delivery = await service.create_delivery(
            config_id=delivery_data.config_id,
            project_id=project_id,
            event_type=delivery_data.event_type,
            payload=delivery_data.payload,
            target_url=delivery_data.target_url,
        )

        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event type not subscribed or filtered",
            )

        return delivery
    finally:
        await service.close()


@router.get("/deliveries", response_model=WebhookDeliveryListResponse)
async def list_webhook_deliveries(
    config_id: int = None,
    event_type: str = None,
    status_filter: str = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    List webhook deliveries with pagination

    Args:
        config_id: Optional filter by webhook config ID
        event_type: Optional filter by event type
        status_filter: Optional filter by delivery status
        page: Page number (1-based)
        page_size: Items per page
        db: Database session

    Returns:
        Paginated list of webhook deliveries
    """
    query = select(WebhookDelivery)

    # Apply filters
    if config_id:
        query = query.where(WebhookDelivery.config_id == config_id)

    if event_type:
        query = query.where(WebhookDelivery.event_type == event_type)

    if status_filter:
        query = query.where(WebhookDelivery.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(WebhookDelivery.created_at)).limit(page_size).offset(offset)
    )
    deliveries = result.scalars().all()

    return {
        "deliveries": deliveries,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/deliveries/{delivery_id}", response_model=WebhookDeliveryResponse)
async def get_webhook_delivery(
    delivery_id: int, db: AsyncSession = Depends(get_db)
) -> WebhookDelivery:
    """
    Get webhook delivery by ID

    Args:
        delivery_id: Webhook delivery ID
        db: Database session

    Returns:
        Webhook delivery
    """
    result = await db.execute(select(WebhookDelivery).where(WebhookDelivery.id == delivery_id))
    delivery = result.scalar_one_or_none()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook delivery {delivery_id} not found",
        )

    return delivery


@router.post("/deliveries/{delivery_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_webhook_delivery(
    delivery_id: int, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retry a failed webhook delivery

    Args:
        delivery_id: Webhook delivery ID
        db: Database session

    Returns:
        Retry status
    """
    # Fetch delivery
    result = await db.execute(select(WebhookDelivery).where(WebhookDelivery.id == delivery_id))
    delivery = result.scalar_one_or_none()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook delivery {delivery_id} not found",
        )

    # Check if delivery can be retried
    if delivery.status not in ["failed", "exhausted", "retrying"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry delivery with status '{delivery.status}'",
        )

    # Schedule for immediate retry
    delivery.status = "pending"
    delivery.scheduled_for = datetime.utcnow()
    delivery.error_message = None
    await db.commit()

    logger.info(f"Manually scheduled retry for webhook delivery {delivery_id}")

    return {
        "status": "scheduled",
        "delivery_id": delivery_id,
        "message": "Delivery scheduled for retry",
    }


@router.get("/statistics", response_model=WebhookStatisticsResponse)
async def get_webhook_statistics(
    config_id: int = None, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get webhook delivery statistics

    Args:
        config_id: Optional filter by webhook config ID
        db: Database session

    Returns:
        Webhook statistics
    """
    service = WebhookService(db)
    try:
        stats = await service.get_delivery_statistics(config_id)
        return stats
    finally:
        await service.close()
