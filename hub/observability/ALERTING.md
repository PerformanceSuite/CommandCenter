# Alerting System Documentation

**CommandCenter Orchestration Service - Phase 10 Phase 5**

This document describes the alerting infrastructure, alert rules, notification routing, and operational procedures.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Alert Rules](#alert-rules)
3. [Notification Routing](#notification-routing)
4. [Testing Alerts](#testing-alerts)
5. [Runbooks](#runbooks)
6. [Maintenance](#maintenance)

---

## Architecture Overview

### Components

```
┌─────────────────┐
│  Prometheus     │  Evaluates alert rules every 15s
│  Alert Rules    │  Triggers alerts when conditions met
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AlertManager   │  Routes alerts based on severity
│  (Port 9093)    │  Groups & deduplicates notifications
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Webhook        │  POST /api/webhooks/alertmanager
│  Endpoint       │  Orchestration service (Port 8020)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Workflow       │  alert-notification workflow
│  System         │  Triggers notifier agent
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Notifier       │  Sends to Slack/Discord/Console
│  Agent          │  Severity-based routing
└─────────────────┘
```

### Data Flow

1. **Prometheus** evaluates alert rules every 15 seconds
2. **AlertManager** receives firing alerts from Prometheus
3. **Grouping**: Alerts grouped by `alertname`, `severity`, `component`
4. **Routing**: Alerts routed to webhook based on severity
5. **Webhook**: Orchestration service receives AlertManager payload
6. **Workflow**: Creates workflow run with alert context
7. **Notifier**: Sends formatted message to appropriate channel

---

## Alert Rules

### Critical Alerts

**Target**: Immediate action required, pages on-call engineer

| Alert Name | Condition | Duration | Description |
|------------|-----------|----------|-------------|
| `WorkflowFailureRate` | > 10% workflows failing | 5 minutes | High workflow failure rate |
| `ServiceDown` | Service not responding | 1 minute | Orchestration service unavailable |
| `DatabaseConnectionLoss` | No DB queries | 1 minute | Database connection lost |
| `HighErrorRate` | > 50 HTTP 5xx/min | 2 minutes | Excessive server errors |

**Notification**: Slack `#alerts-critical` channel + PagerDuty (production)

**Response Time**: < 5 minutes acknowledgment, < 15 minutes mitigation

---

### Warning Alerts

**Target**: Non-urgent issues, investigate within business hours

| Alert Name | Condition | Duration | Description |
|------------|-----------|----------|-------------|
| `HighWorkflowDuration` | p95 > 5 minutes | 10 minutes | Workflows running slow |
| `AgentFailureSpike` | > 5 failures/10min per agent | 10 minutes | Specific agent failing |
| `ApprovalBacklog` | > 20 pending approvals | 30 minutes | Large approval queue |
| `HighMemoryUsage` | > 80% heap memory | 5 minutes | Memory pressure |
| `HighEventLoopLag` | > 100ms lag | 5 minutes | Event loop blocked |
| `SlowAPIResponse` | p95 > 2 seconds | 10 minutes | API latency issues |

**Notification**: Slack `#alerts-warning` channel

**Response Time**: < 4 hours acknowledgment, < 1 day investigation

---

### SLO Alerts

**Target**: Track service level objective violations

| Alert Name | SLO Target | Window | Description |
|------------|------------|--------|-------------|
| `WorkflowSuccessRateSLO` | ≥ 99% | 30 days | Workflow success rate below target |
| `AgentSuccessRateSLO` | ≥ 98% | 7 days | Agent success rate below target |
| `APIAvailabilitySLO` | ≥ 99.9% | 30 days | API uptime below target |

**Notification**: Slack `#slo-violations` channel + weekly summary email

**Response Time**: < 1 day analysis, remediation plan within 3 days

---

## Notification Routing

### AlertManager Configuration

**Location**: `hub/observability/alertmanager.yml`

**Routing Logic**:

```yaml
# Critical alerts: 10s wait, 1h repeat
severity=critical → orchestration-webhook (immediate)

# Warning alerts: 30s wait, 4h repeat
severity=warning → orchestration-webhook (grouped)

# SLO alerts: 1h wait, 24h repeat
component=slo → orchestration-webhook (daily summary)
```

### Webhook Integration

**Endpoint**: `POST http://host.docker.internal:8020/api/webhooks/alertmanager`

**Payload**: Standard AlertManager webhook format
```json
{
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighErrorRate",
        "severity": "critical",
        "component": "api"
      },
      "annotations": {
        "summary": "High 5xx error rate: 75 errors/min",
        "description": "More than 50 server errors per minute",
        "runbook_url": "https://docs.commandcenter.io/runbooks/high-error-rate"
      }
    }
  ]
}
```

**Workflow**: `alert-notification` (auto-created on first alert)

**Steps**:
1. Notifier agent receives alert context
2. Formats message with severity emoji
3. Routes to channel based on severity
   - `critical` → Slack `#alerts-critical`
   - `warning` → Console (development) or Slack `#alerts-warning` (production)
   - `slo` → Slack `#slo-violations`

---

## Testing Alerts

### 1. Manual Alert Trigger

**Trigger specific alert using PromQL**:

```bash
# Simulate high memory usage
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Check alert is firing
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'
```

### 2. AlertManager Webhook Test

**Send test webhook directly**:

```bash
curl -X POST http://localhost:8020/api/webhooks/alertmanager \
  -H 'Content-Type: application/json' \
  -d '{
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "TestAlert",
        "severity": "warning",
        "component": "test"
      },
      "annotations": {
        "summary": "This is a test alert",
        "description": "Testing the alerting pipeline",
        "runbook_url": "https://example.com/runbook"
      }
    }
  ]
}'
```

**Expected**:
1. Webhook returns 200 OK with `workflowRuns` array
2. Workflow run created in database
3. Notifier agent executes
4. Message appears in console (dev) or Slack (prod)

### 3. End-to-End Alert Test

**Trigger real alert condition**:

```bash
# Start observability stack
cd hub
docker-compose -f docker-compose.observability.yml up -d

# Start orchestration service
cd orchestration
npm run dev

# Trigger high error rate (hit non-existent endpoint repeatedly)
for i in {1..100}; do
  curl http://localhost:8020/api/nonexistent 2>/dev/null &
done

# Wait 2 minutes for alert to fire
# Check Prometheus alerts
open http://localhost:9090/alerts

# Check AlertManager
open http://localhost:9093/#/alerts

# Verify workflow runs
curl http://localhost:8020/api/workflows/runs | jq '.runs[] | select(.trigger=="alertmanager_webhook")'
```

---

## Runbooks

### WorkflowFailureRate

**Alert**: High workflow failure rate (> 10%)

**Investigation**:
1. Open Grafana Workflow Overview dashboard
2. Check "Runs by Workflow" panel - identify failing workflows
3. Filter Agent Performance dashboard by failing workflows
4. Review agent execution logs in Grafana Explore

**Remediation**:
- If agent dependency issue → Fix external API/credential
- If code bug → Rollback recent deployment
- If infrastructure → Scale resources or restart service

**Escalation**: Page platform lead if failures > 50% for 10 minutes

---

### ServiceDown

**Alert**: Orchestration service unavailable

**Investigation**:
```bash
# Check service status
docker ps | grep orchestration

# View recent logs
docker logs hub-orchestration --tail 100

# Check database connectivity
docker exec hub-orchestration npm run db:ping
```

**Remediation**:
1. Restart service: `docker restart hub-orchestration`
2. If restart fails, check database: `docker logs hub-postgres`
3. If database down, restart: `docker restart hub-postgres`
4. Verify service health: `curl http://localhost:8020/api/health`

**Escalation**: If service won't start after 2 restart attempts

---

### DatabaseConnectionLoss

**Alert**: No database queries detected

**Investigation**:
```bash
# Check PostgreSQL status
docker ps | grep postgres

# Check connection from service
docker exec hub-orchestration psql -h postgres -U orchestration -c "SELECT 1"

# Review PostgreSQL logs
docker logs hub-postgres --tail 50
```

**Remediation**:
1. Restart database: `docker restart hub-postgres`
2. Restart orchestration service: `docker restart hub-orchestration`
3. Check connection pool settings in `config.ts`
4. Verify DATABASE_URL environment variable

**Escalation**: If connection loss persists > 5 minutes

---

### HighMemoryUsage

**Alert**: Heap memory > 80%

**Investigation**:
```bash
# Check current memory usage
curl http://localhost:9464/metrics | grep process_runtime_nodejs_memory

# Take heap snapshot (requires --inspect flag)
kill -USR2 $(pgrep -f "orchestration")

# Analyze heap dump
# Use Chrome DevTools Memory Profiler
```

**Remediation**:
1. Restart service to clear memory: `docker restart hub-orchestration`
2. Review recent deployments for memory leaks
3. Analyze heap snapshot for unbounded growth
4. Increase heap size if legitimate growth: `NODE_OPTIONS=--max-old-space-size=4096`

**Escalation**: If memory leak confirmed and fix unavailable

---

### AgentFailureSpike

**Alert**: Specific agent failing frequently (> 5 failures/10min)

**Investigation**:
1. Open Agent Performance dashboard
2. Check "Failure Rate by Agent" panel
3. Review agent execution logs
4. Test agent in isolation

**Remediation**:
- If external API issue → Contact API provider, implement retry logic
- If credential issue → Rotate credentials, update agent config
- If agent bug → Disable agent temporarily, deploy fix

**Escalation**: If agent critical to operations and no fix available

---

## Maintenance

### Silence Alerts During Maintenance

**Using AlertManager UI** (`http://localhost:9093`):
1. Click "Silences"
2. Click "New Silence"
3. Add matcher: `alertname=~ ".*"` (all alerts) or specific alert
4. Set duration (e.g., 1 hour)
5. Add comment: "Maintenance window - deploying v1.2.3"
6. Click "Create"

**Using API**:
```bash
curl -X POST http://localhost:9093/api/v1/silences \
  -H 'Content-Type: application/json' \
  -d '{
  "matchers": [
    {"name": "alertname", "value": ".*", "isRegex": true}
  ],
  "startsAt": "2025-11-19T10:00:00Z",
  "endsAt": "2025-11-19T11:00:00Z",
  "createdBy": "platform-team",
  "comment": "Scheduled maintenance"
}'
```

### Update Alert Rules

**Process**:
1. Edit `hub/observability/prometheus-alerts.yml`
2. Validate syntax: `promtool check rules prometheus-alerts.yml`
3. Reload Prometheus: `docker exec hub-prometheus-obs kill -HUP 1`
4. Verify rules loaded: `curl http://localhost:9090/api/v1/rules`

**Testing**:
- Test new rule in Grafana Explore before deploying
- Use `for: 0s` temporarily to test trigger immediately
- Restore proper `for` duration after testing

### Update AlertManager Configuration

**Process**:
1. Edit `hub/observability/alertmanager.yml`
2. Validate syntax: `amtool check-config alertmanager.yml`
3. Reload AlertManager: `docker exec hub-alertmanager kill -HUP 1`
4. Verify config: `curl http://localhost:9093/api/v1/status`

---

## Production Checklist

**Before deploying alerting to production**:

- [ ] Configure production Slack webhooks in `alertmanager.yml`
- [ ] Set up PagerDuty integration for critical alerts
- [ ] Create Slack channels: `#alerts-critical`, `#alerts-warning`, `#slo-violations`
- [ ] Test end-to-end alert flow in staging environment
- [ ] Document on-call rotation and escalation procedures
- [ ] Train team on alert acknowledgment and resolution
- [ ] Set up alert dashboard in NOC/operations center
- [ ] Configure alert retention (AlertManager data volume backup)
- [ ] Schedule monthly SLO review meetings
- [ ] Create incident response playbooks for each critical alert

---

## Troubleshooting

### Alerts Not Firing

**Check Prometheus**:
```bash
# Verify rules loaded
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.name=="WorkflowFailureRate")'

# Check alert state
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname=="WorkflowFailureRate")'
```

**Common issues**:
- Rule file not mounted in Prometheus container
- Syntax error in PromQL expression
- Metrics not available (check scrape targets)

### Alerts Not Routing to Webhook

**Check AlertManager**:
```bash
# View active alerts
curl http://localhost:9093/api/v1/alerts

# Check routing configuration
curl http://localhost:9093/api/v1/status
```

**Common issues**:
- AlertManager not reachable by Prometheus
- Webhook URL incorrect (`host.docker.internal` vs `localhost`)
- Webhook endpoint returning errors (check orchestration logs)

### Notifications Not Sent

**Check Workflow Runs**:
```bash
# List recent alert workflows
curl http://localhost:8020/api/workflows/runs?trigger=alertmanager_webhook

# Check specific run details
curl http://localhost:8020/api/workflows/runs/{runId}
```

**Common issues**:
- `alert-notification` workflow not created
- Notifier agent not registered
- Notifier agent failing (check agent run logs)
- Slack webhook URL missing or invalid (production)

---

## Metrics

**Track alerting system health**:

- **Alert Firing Rate**: `rate(alertmanager_alerts_received_total[5m])`
- **Alert Routing Success**: `rate(alertmanager_alerts_invalid_total[5m])`
- **Notification Success**: `rate(alertmanager_notifications_total[5m])`
- **Notification Failures**: `rate(alertmanager_notifications_failed_total[5m])`

**Dashboard**: Grafana "Alerting Health" (create manually)

---

*Last Updated*: 2025-11-19
*Owner*: Platform Engineering Team
*On-Call*: See PagerDuty rotation (production)
