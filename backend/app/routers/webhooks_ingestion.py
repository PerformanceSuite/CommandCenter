"""
Webhook endpoints for knowledge ingestion
"""

import logging
import hmac
import hashlib
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Query, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.ingestion_source import IngestionSource, SourceType
from app.tasks.ingestion_tasks import process_webhook_payload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def verify_github_signature(
    payload_body: bytes, signature_header: str, secret: str
) -> bool:
    """
    Verify GitHub webhook signature.

    Args:
        payload_body: Raw request body
        signature_header: X-Hub-Signature-256 header value
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header.split("=")[1]

    # Calculate HMAC
    mac = hmac.new(secret.encode(), payload_body, hashlib.sha256)
    calculated_signature = mac.hexdigest()

    return hmac.compare_digest(calculated_signature, expected_signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    source_id: int = Query(..., description="ID of webhook ingestion source"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive GitHub webhooks for repository updates.

    Supported events:
    - release: New releases
    - push: Code commits
    """
    # Load source
    result = await db.execute(
        select(IngestionSource).where(
            IngestionSource.id == source_id, IngestionSource.type == SourceType.WEBHOOK
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Webhook source not found")

    if not source.enabled:
        raise HTTPException(status_code=403, detail="Webhook source is disabled")

    # Get payload
    payload_body = await request.body()
    payload = await request.json()

    # Verify signature
    secret = source.config.get("secret", "")
    if not verify_github_signature(payload_body, x_hub_signature_256, secret):
        logger.warning(f"Invalid GitHub webhook signature for source {source_id}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Check if event is configured
    allowed_events = source.config.get("events", [])
    if allowed_events and x_github_event not in allowed_events:
        logger.info(f"Ignoring GitHub event '{x_github_event}' for source {source_id}")
        return {"status": "ignored", "event": x_github_event}

    # Queue task asynchronously
    task = process_webhook_payload.delay(
        source_id=source.id, payload=payload, event_type=x_github_event
    )

    logger.info(
        f"Queued GitHub webhook processing: task_id={task.id}, event={x_github_event}"
    )

    return {"status": "accepted", "task_id": task.id, "event": x_github_event}


@router.post("/generic")
async def generic_webhook(
    request: Request,
    project_id: int = Query(..., description="Project ID for ingestion"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive generic webhooks from custom integrations.

    Expected payload format:
    {
        "title": "Document title",
        "content": "Full content",
        "url": "Source URL (optional)",
        "metadata": {
            "category": "documentation",
            "priority": 8,
            ...
        }
    }
    """
    # Validate API key
    expected_api_key = os.getenv("GENERIC_WEBHOOK_API_KEY")

    if not expected_api_key:
        logger.error("GENERIC_WEBHOOK_API_KEY environment variable not configured")
        raise HTTPException(
            status_code=500, detail="Webhook API key not configured on server"
        )

    if not x_api_key:
        logger.warning("Generic webhook request missing X-API-Key header")
        raise HTTPException(status_code=401, detail="Missing API key")

    if x_api_key != expected_api_key:
        logger.warning(
            f"Invalid API key provided for generic webhook: {x_api_key[:8]}..."
        )
        raise HTTPException(status_code=401, detail="Invalid API key")

    payload = await request.json()

    # Validate required fields
    if "title" not in payload or "content" not in payload:
        raise HTTPException(
            status_code=400, detail="Payload must include 'title' and 'content' fields"
        )

    # Queue task
    task = process_webhook_payload.delay(
        source_id=None,  # Generic webhook doesn't require source
        payload=payload,
        event_type="generic",
        project_id=project_id,
    )

    logger.info(f"Queued generic webhook processing: task_id={task.id}")

    return {"status": "accepted", "task_id": task.id}
