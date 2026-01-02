# Stream C: AlertManager Deployment

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
# The GITHUB_TOKEN is available in your environment
# Configure git to use it for push operations
git remote set-url origin https://${GITHUB_TOKEN}@github.com/PerformanceSuite/CommandCenter.git

# Verify it's set (should show https://ghp_...@github.com/...)
git remote -v
```

**You MUST do this before attempting to push.** The sandbox doesn't have SSH keys.

---

## Context

CommandCenter has **23 alert rules defined** in `monitoring/alerts.yml`, but AlertManager is **not deployed**. These alerts never fire because there's no alert receiver configured.

This is part of the **Autonomy pillar** - enabling the system to detect and respond to conditions proactively.

## Your Mission

Deploy AlertManager and wire it to Prometheus so alerts actually fire.

## Branch

Create and work on: `feature/alertmanager-deploy`

## Step-by-Step Implementation

### Step 1: Create AlertManager Configuration

Create `monitoring/alertmanager.yml`:

```yaml
# AlertManager Configuration for CommandCenter
# https://prometheus.io/docs/alerting/latest/configuration/

global:
  resolve_timeout: 5m
  # SMTP config (update with actual values)
  # smtp_smarthost: 'smtp.gmail.com:587'
  # smtp_from: 'alertmanager@commandcenter.local'
  # smtp_auth_username: 'your-email@gmail.com'
  # smtp_auth_password: 'your-app-password'

# Route tree
route:
  # Default receiver
  receiver: 'default-receiver'

  # Group alerts by these labels
  group_by: ['alertname', 'severity', 'service']

  # Wait before sending first notification
  group_wait: 30s

  # Wait before sending updated notification
  group_interval: 5m

  # Wait before resending notification
  repeat_interval: 4h

  # Child routes for specific alert types
  routes:
    # Critical alerts - shorter intervals
    - match:
        severity: critical
      receiver: 'critical-receiver'
      group_wait: 10s
      repeat_interval: 1h

    # Warning alerts
    - match:
        severity: warning
      receiver: 'warning-receiver'
      repeat_interval: 4h

    # Info alerts - less frequent
    - match:
        severity: info
      receiver: 'info-receiver'
      repeat_interval: 12h

# Inhibition rules - prevent notification floods
inhibit_rules:
  # If critical is firing, suppress warning for same alertname
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']

# Receivers
receivers:
  - name: 'default-receiver'
    webhook_configs:
      - url: 'http://backend:8000/api/v1/alerts/webhook'
        send_resolved: true

  - name: 'critical-receiver'
    webhook_configs:
      - url: 'http://backend:8000/api/v1/alerts/webhook'
        send_resolved: true
    # Uncomment for Slack integration
    # slack_configs:
    #   - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    #     channel: '#alerts-critical'
    #     title: '🚨 Critical Alert'
    #     text: '{{ .CommonAnnotations.summary }}'

  - name: 'warning-receiver'
    webhook_configs:
      - url: 'http://backend:8000/api/v1/alerts/webhook'
        send_resolved: true

  - name: 'info-receiver'
    webhook_configs:
      - url: 'http://backend:8000/api/v1/alerts/webhook'
        send_resolved: true

# Templates for notifications (optional)
# templates:
#   - '/etc/alertmanager/templates/*.tmpl'
```

### Step 2: Update Docker Compose

Edit `docker-compose.yml` (or `docker-compose.prod.yml`):

```yaml
services:
  # ... existing services ...

  alertmanager:
    image: prom/alertmanager:v0.27.0
    container_name: cc-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager-data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
      - '--cluster.listen-address='  # Disable clustering for single instance
    restart: unless-stopped
    networks:
      - cc-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9093/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  # ... existing volumes ...
  alertmanager-data:
```

### Step 3: Update Prometheus Configuration

Edit `monitoring/prometheus.yml` to point to AlertManager:

```yaml
# Global configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Rule files
rule_files:
  - /etc/prometheus/alerts.yml

# Scrape configurations
scrape_configs:
  # ... existing scrape configs ...

  # Add AlertManager scrape
  - job_name: 'alertmanager'
    static_configs:
      - targets: ['alertmanager:9093']
```

### Step 4: Create Alert Webhook Endpoint

Create `backend/app/routers/alerts.py`:

```python
"""Webhook endpoint for AlertManager alerts."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertLabel(BaseModel):
    alertname: str
    severity: Optional[str] = None
    service: Optional[str] = None
    instance: Optional[str] = None


class AlertAnnotation(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None


class Alert(BaseModel):
    status: str  # "firing" or "resolved"
    labels: AlertLabel
    annotations: AlertAnnotation
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: Optional[str] = None
    fingerprint: Optional[str] = None


class AlertManagerPayload(BaseModel):
    version: str
    groupKey: str
    status: str  # "firing" or "resolved"
    receiver: str
    groupLabels: dict
    commonLabels: dict
    commonAnnotations: dict
    externalURL: str
    alerts: List[Alert]


async def process_alerts(payload: AlertManagerPayload):
    """Process alerts in background."""
    for alert in payload.alerts:
        status_emoji = "🔥" if alert.status == "firing" else "✅"
        severity = alert.labels.severity or "unknown"

        logger.info(
            f"{status_emoji} Alert {alert.status.upper()}: "
            f"[{severity}] {alert.labels.alertname} - "
            f"{alert.annotations.summary or 'No summary'}"
        )

        # TODO: Future integrations
        # - Store in database for history
        # - Emit NATS event for real-time UI
        # - Trigger auto-remediation workflows
        # - Send to external integrations (Slack, PagerDuty, etc.)


@router.post("/webhook")
async def receive_alert(
    payload: AlertManagerPayload,
    background_tasks: BackgroundTasks
):
    """
    Receive alerts from AlertManager.

    This endpoint receives POST requests from AlertManager when alerts
    fire or resolve. It processes them asynchronously to avoid blocking.
    """
    logger.info(
        f"Received {len(payload.alerts)} alerts, status: {payload.status}, "
        f"receiver: {payload.receiver}"
    )

    # Process in background to respond quickly
    background_tasks.add_task(process_alerts, payload)

    return {"status": "accepted", "alerts_received": len(payload.alerts)}


@router.get("/status")
async def alertmanager_status():
    """Check AlertManager connection status."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://alertmanager:9093/api/v2/status",
                timeout=5.0
            )
            if response.status_code == 200:
                return {"status": "connected", "alertmanager": response.json()}
            return {"status": "error", "code": response.status_code}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}


@router.get("/active")
async def get_active_alerts():
    """Get currently active alerts from AlertManager."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://alertmanager:9093/api/v2/alerts",
                timeout=5.0
            )
            if response.status_code == 200:
                return {"alerts": response.json()}
            return {"error": f"AlertManager returned {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
```

### Step 5: Register Router

Edit `backend/app/main.py`:

```python
from app.routers import alerts

# Add with other router includes
app.include_router(alerts.router, prefix="/api/v1")
```

### Step 6: Add Grafana Dashboard Panel

Edit `monitoring/grafana/dashboards/commandcenter-overview.json` to add an alerts panel:

```json
{
  "title": "Active Alerts",
  "type": "table",
  "gridPos": {"h": 6, "w": 12, "x": 0, "y": 0},
  "targets": [
    {
      "expr": "ALERTS{alertstate=\"firing\"}",
      "format": "table",
      "instant": true
    }
  ],
  "transformations": [
    {
      "id": "organize",
      "options": {
        "excludeByName": {"Time": true, "Value": true},
        "indexByName": {},
        "renameByName": {}
      }
    }
  ],
  "fieldConfig": {
    "defaults": {
      "custom": {"displayMode": "color-text"}
    },
    "overrides": [
      {
        "matcher": {"id": "byName", "options": "severity"},
        "properties": [
          {
            "id": "mappings",
            "value": [
              {"type": "value", "options": {"critical": {"color": "red", "text": "🔴 CRITICAL"}}},
              {"type": "value", "options": {"warning": {"color": "orange", "text": "🟠 WARNING"}}},
              {"type": "value", "options": {"info": {"color": "blue", "text": "🔵 INFO"}}}
            ]
          }
        ]
      }
    ]
  }
}
```

### Step 7: Verify Existing Alert Rules

Check `monitoring/alerts.yml` exists and has valid rules:

```bash
# List current alert rules
cat monitoring/alerts.yml

# Validate with promtool (if available)
docker run --rm -v $(pwd)/monitoring:/etc/prometheus prom/prometheus promtool check rules /etc/prometheus/alerts.yml
```

### Step 8: Test Alert Pipeline

Create a test alert rule in `monitoring/alerts.yml`:

```yaml
groups:
  - name: test
    rules:
      - alert: TestAlert
        expr: vector(1)  # Always fires
        for: 1m
        labels:
          severity: info
        annotations:
          summary: "Test alert - AlertManager is working"
          description: "This is a test alert to verify the pipeline. You can delete this rule after verification."
```

### Verification

```bash
# Start services
docker-compose up -d alertmanager prometheus

# Check AlertManager is running
curl http://localhost:9093/-/healthy

# Check Prometheus can reach AlertManager
curl http://localhost:9090/api/v1/alertmanagers

# Check backend webhook endpoint
curl http://localhost:8000/api/v1/alerts/status

# Wait 1-2 minutes, then check for test alert
curl http://localhost:9093/api/v2/alerts

# Check backend logs for webhook receipt
docker-compose logs backend | grep -i alert
```

## Commit Strategy

1. `feat(monitoring): add AlertManager configuration`
2. `feat(docker): add AlertManager service to compose`
3. `feat(monitoring): update Prometheus to use AlertManager`
4. `feat(api): add alert webhook endpoint`
5. `docs(monitoring): update README with AlertManager setup`

## Create PR

Title: `feat(monitoring): deploy AlertManager for alert notifications`

Body:
```markdown
## Summary
Deploys AlertManager to enable the 23 existing alert rules to actually fire and notify.

## Changes
- Added `monitoring/alertmanager.yml` with routing and receiver config
- Added AlertManager service to docker-compose
- Updated Prometheus config to point to AlertManager
- Added `/api/v1/alerts/webhook` endpoint for receiving alerts
- Added `/api/v1/alerts/status` and `/api/v1/alerts/active` endpoints

## Alert Flow
```
Prometheus → evaluates rules → fires alert → AlertManager → webhook → backend → log/store/emit
```

## Testing
1. Start services: `docker-compose up -d alertmanager prometheus`
2. Check health: `curl http://localhost:9093/-/healthy`
3. Check active alerts: `curl http://localhost:9093/api/v2/alerts`

## Future Enhancements
- Store alerts in database for history
- Emit NATS events for real-time UI updates
- Slack/PagerDuty integration
- Auto-remediation triggers
```

## Completion Criteria

- [ ] AlertManager config created
- [ ] Docker Compose updated
- [ ] Prometheus config updated
- [ ] Backend webhook endpoint created
- [ ] Services start without errors
- [ ] Test alert fires and reaches webhook
- [ ] PR created with clear description
