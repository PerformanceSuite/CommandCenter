"""Alert webhook endpoint for AlertManager integration."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


class AlertLabel(BaseModel):
    alertname: str
    severity: Optional[str] = None
    service: Optional[str] = None
    instance: Optional[str] = None


class Alert(BaseModel):
    status: str  # "firing" or "resolved"
    labels: AlertLabel
    annotations: dict = {}
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: Optional[str] = None
    fingerprint: str


class AlertManagerWebhook(BaseModel):
    receiver: str
    status: str
    alerts: List[Alert]
    groupLabels: dict = {}
    commonLabels: dict = {}
    commonAnnotations: dict = {}
    externalURL: str
    version: str = "4"
    groupKey: str


@router.post("/webhook")
async def receive_alert(payload: AlertManagerWebhook, background_tasks: BackgroundTasks):
    """
    Receive alerts from AlertManager webhook.
    
    This endpoint logs alerts and could be extended to:
    - Store in database
    - Send to Slack/Discord
    - Trigger automated remediation
    - Update dashboard status
    """
    for alert in payload.alerts:
        if alert.status == "firing":
            logger.warning(
                f"🚨 ALERT FIRING: {alert.labels.alertname} "
                f"(severity: {alert.labels.severity}, service: {alert.labels.service})"
            )
        else:
            logger.info(
                f"✅ ALERT RESOLVED: {alert.labels.alertname} "
                f"(service: {alert.labels.service})"
            )
    
    # Could add background task for async processing
    # background_tasks.add_task(store_alerts, payload)
    
    return {"status": "received", "alert_count": len(payload.alerts)}


@router.get("/health")
async def alerts_health():
    """Health check for alerts subsystem."""
    return {
        "status": "healthy",
        "alertmanager_url": "http://alertmanager:9093",
        "timestamp": datetime.utcnow().isoformat()
    }
