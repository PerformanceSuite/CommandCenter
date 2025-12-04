# VERIA Integration - Quick Reference Guide

**Last Updated**: 2025-12-03
**Status**: Ready for Implementation
**Audience**: Developers & DevOps

---

## Quick Facts

| Item | Details |
|------|---------|
| **VERIA Endpoint** | http://127.0.0.1:8082 |
| **CommandCenter Orchestration** | http://localhost:9002 |
| **Federation Service** | http://localhost:8001 |
| **NATS Broker** | nats://localhost:4222 |
| **Project ID** | "veria" (string identifier) |
| **Auth Model** | JWT (after Phase 1) |
| **Key Agents** | veria-compliance, veria-intelligence |

---

## Architecture Diagram

```
VERIA Platform                      CommandCenter Hub
┌────────────────┐                 ┌──────────────────────────┐
│ Intelligence   │                 │ Workflow Orchestration   │
│ Service        │                 │ (Port 9002)              │
│ :8082          │◄────HTTP────►   │ - Agent Registry         │
│                │   ← JWT →       │ - Workflow Engine        │
│                │                 │ - Dagger Executor        │
└────────────────┘                 └──────────────────────────┘
       ▲                                     ▲
       │                                     │
       │  NATS Events                        │
       │  (Pub/Sub)                          │
       │                                     │
       └─────────────────────┬───────────────┘
                             │
                    ┌────────▼────────┐
                    │  NATS Broker    │
                    │  JetStream      │
                    │  :4222          │
                    └─────────────────┘
                             ▲
                             │
                    ┌────────┴────────┐
                    │                 │
            ┌───────▼──────┐  ┌──────▼───────┐
            │ Federation   │  │ Prometheus   │
            │ Service      │  │ Monitoring   │
            │ :8001        │  │ :9091        │
            └──────────────┘  └──────────────┘
```

---

## Authentication Quick Start

### 1. Get JWT Token (VERIA)

```bash
curl -X POST http://localhost:8001/federation/token \
  -H "X-API-Key: veria-secret-key-here" \
  -H "Content-Type: application/json"

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "project:veria workflows:read workflows:write"
}
```

### 2. Use JWT for API Calls (VERIA)

```bash
JWT_TOKEN="eyJhbGciOiJIUzI1NiI..."

# List workflows
curl -X GET http://localhost:9002/api/workflows?projectId=veria \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-CommandCenter-ProjectId: veria"

# Trigger workflow
curl -X POST http://localhost:9002/api/workflows/{id}/trigger \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-CommandCenter-ProjectId: veria" \
  -H "Content-Type: application/json" \
  -d '{"contextJson": {}}'
```

---

## Workflow Integration Examples

### Example 1: Simple VERIA Agent

```json
{
  "name": "scan-and-attest",
  "trigger": "manual",
  "nodes": [
    {
      "id": "scan",
      "agentId": "security-scanner",
      "action": "scan",
      "inputs": {
        "path": "/workspace"
      },
      "dependsOn": [],
      "approvalRequired": false
    },
    {
      "id": "attest",
      "agentId": "veria-compliance",
      "action": "attest",
      "inputs": {
        "findings": "{{scan.output.findings}}",
        "compliance_level": "medium"
      },
      "dependsOn": ["scan"],
      "approvalRequired": false
    }
  ]
}
```

**Template Resolution**: `{{scan.output.findings}}` → actual findings from scan agent output

### Example 2: With Human Approval

```json
{
  "id": "approve",
  "agentId": "approval",
  "action": "wait-for-approval",
  "inputs": {
    "message": "Review VERIA attestation before deployment"
  },
  "dependsOn": ["attest"],
  "approvalRequired": true
}
```

---

## VERIA API Endpoints

### Attestation

```
POST /api/attest
Authorization: X-API-Key: veria-secret-key
X-CommandCenter-ProjectId: 1
X-CommandCenter-WorkflowRunId: workflow-run-uuid

Request:
{
  "findings": [
    {
      "category": "secret",
      "severity": "critical",
      "file": "src/config.ts",
      "description": "Database password in code"
    }
  ],
  "compliance_level": "medium"
}

Response 200 OK:
{
  "success": true,
  "attestation_id": "veria-attest-001",
  "compliance_score": 87,
  "details": {
    "validated_count": 23,
    "failed_count": 2,
    "recommendations": ["Move secrets to .env"]
  }
}

Response 500 Internal Error:
{
  "error": "service_error",
  "message": "VERIA service unavailable"
}
```

### Analysis

```
POST /api/analyze
Authorization: X-API-Key: veria-secret-key

Request:
{
  "type": "dependency_risk",
  "target": {
    "repository_url": "https://github.com/example/repo",
    "commit_sha": "abc123..."
  }
}

Response 200 OK:
{
  "analysis_id": "veria-analysis-001",
  "status": "completed",
  "findings": {
    "high_risk_dependencies": 3,
    "known_vulnerabilities": 2
  }
}
```

---

## Event Subscription (NATS)

### VERIA Subscribes to Workflow Events

```javascript
// In VERIA Intelligence Service
const nc = new NATSConnection("nats://localhost:4222");

// Subscribe to all workflow completions
const subscription = nc.subscribe("hub.workflow.*.success");

for await (const msg of subscription) {
  const event = JSON.parse(new TextDecoder().decode(msg.data));
  console.log(`Workflow ${event.workflow_id} completed with findings:`, event.findings);

  // VERIA processes findings
  await analyzeAndPublishIntelligence(event);

  // Acknowledge message (JetStream)
  msg.ack();
}
```

### VERIA Publishes Intelligence Events

```
Subject: veria.intelligence.analysis.completed
Payload:
{
  "event_id": "uuid",
  "analysis_id": "veria-analysis-001",
  "workflow_run_id": "commandcenter-workflow-uuid",
  "status": "completed",
  "findings": {...},
  "timestamp": "2025-12-03T10:00:00Z"
}
```

---

## Debugging & Troubleshooting

### Check VERIA Health

```bash
curl http://127.0.0.1:8082/health
# {status: "ok", timestamp: "..."}
```

### Verify JWT Token

```bash
# Decode (base64 the middle part)
JWT="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ2ZXJpYSIsImlhdCI6MTcwMjY0MjgwMH0.signature"

# Split and decode payload:
echo "eyJzdWIiOiJ2ZXJpYSIsImlhdCI6MTcwMjY0MjgwMH0" | base64 -d | jq .

# Expected output:
{
  "sub": "veria-project",
  "projectId": "veria",
  "scope": "project:veria workflows:read workflows:write",
  "aud": "commandcenter-orchestration",
  "iss": "commandcenter-federation",
  "exp": 1702646400,
  "iat": 1702642800
}
```

### Monitor NATS Events

```bash
# Subscribe to VERIA-related events
nats sub "hub.workflow.*.success" --server=nats://localhost:4222

# Subscribe to VERIA intelligence events
nats sub "veria.intelligence.>" --server=nats://localhost:4222

# Publish test event
nats pub "hub.workflow.1.success" '{"workflow_id": "test"}'
```

### Check Grafana Dashboards

1. Open http://localhost:3003
2. Navigate to "Agent Performance" dashboard
3. Filter by agent: "veria-compliance"
4. View execution duration, success rate, error trends

### View Logs

```bash
# Orchestration service logs
docker-compose logs -f orchestration

# Federation service logs
docker-compose logs -f federation

# Filter for VERIA-related errors
docker-compose logs orchestration | grep -i veria
```

---

## Common Issues & Solutions

### Issue: "401 Unauthorized"

**Cause**: Invalid JWT or API key

**Solution**:
```bash
# 1. Verify API key is correct
echo $VERIA_API_KEY

# 2. Get fresh JWT token
curl -H "X-API-Key: $VERIA_API_KEY" http://localhost:8001/federation/token

# 3. Use new token in Authorization header
curl -H "Authorization: Bearer <new-token>" http://localhost:9002/api/workflows
```

### Issue: "30-second timeout exceeded"

**Cause**: VERIA API slow or unavailable

**Solution**:
```bash
# 1. Check VERIA health
curl http://127.0.0.1:8082/health

# 2. Test VERIA API directly
curl -X POST http://127.0.0.1:8082/api/attest \
  -H "X-API-Key: $VERIA_API_KEY" \
  -d '{"findings": [], "compliance_level": "medium"}'

# 3. Check network connectivity
ping 127.0.0.1
nc -zv 127.0.0.1 8082
```

### Issue: "Project ID mismatch"

**Cause**: JWT projectId doesn't match request header

**Solution**:
```bash
# Ensure header matches JWT claim:
curl -H "Authorization: Bearer $JWT" \
  -H "X-CommandCenter-ProjectId: veria" \  # Must be "veria"
  http://localhost:9002/api/workflows

# Decode JWT to verify:
# {"projectId": "veria", ...}
```

### Issue: "Workflow run failed (no error message)"

**Cause**: Agent timeout or crash

**Solution**:
```bash
# 1. Check agent run status
curl http://localhost:9002/api/workflows/{id}/runs/{runId} | jq '.agentRuns'

# 2. View agent logs in Grafana
# Dashboard: Agent Performance
# Filter: agent_name = "veria-compliance"

# 3. Increase timeout in agent definition (future release)
# Currently: 30 seconds (hardcoded)
```

---

## Configuration Files

### `.env` (Required)

```bash
# Federation Service
FEDERATION_API_KEYS=["veria-secret-key-here", "other-keys"]

# NATS
NATS_URL=nats://localhost:4222

# Orchestration Database
DATABASE_URL=postgresql://user:pass@localhost:5432/orchestration_db

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
PROMETHEUS_PUSHGATEWAY=http://localhost:9091
```

### `veria-dev/project.json` (Hub Registry)

```json
{
  "projectId": "veria",
  "instanceId": "veria-dev",
  "name": "VERIA Platform",
  "owner": "commandcenter",
  "env": "dev",
  "endpoints": {
    "api": "http://127.0.0.1:8082"
  },
  "health": {
    "url": "http://127.0.0.1:8082/health"
  }
}
```

---

## Performance Benchmarks

| Metric | Target | Notes |
|--------|--------|-------|
| JWT token generation | < 50ms | Cached in Redis (future) |
| Workflow execution | < 5s (p95) | Local agents only |
| VERIA attestation | < 500ms | Direct API call |
| End-to-end workflow | < 2s (p95) | Scan + Attest + Response |
| Concurrent workflows | 10 without degradation | Limited by Dagger parallelism |

---

## Monitoring Queries (Prometheus)

```promql
# VERIA agent success rate (last 5 minutes)
rate(agent_runs_total{agent_name="veria-compliance", status="SUCCESS"}[5m]) /
rate(agent_runs_total{agent_name="veria-compliance"}[5m])

# VERIA agent p95 duration
histogram_quantile(0.95, rate(agent_duration_seconds_bucket{agent_name="veria-compliance"}[5m]))

# Workflow success rate (includes VERIA nodes)
rate(workflow_runs_total{status="SUCCESS"}[5m]) /
rate(workflow_runs_total[5m])

# NATS message rate to VERIA
rate(nats_publish_total{subject=~"hub.workflow.*"}[5m])
```

---

## Testing Checklist

- [ ] VERIA health endpoint responding
- [ ] JWT token generation working
- [ ] JWT validation in orchestration service
- [ ] VERIA agent executes in workflow
- [ ] Timeout protection (30s) enforced
- [ ] Load test: 10 concurrent workflows
- [ ] Secret injection (no secrets in logs)
- [ ] Monitoring dashboards show VERIA metrics
- [ ] Error scenarios handled gracefully

---

## Deployment Checklist

- [ ] VERIA API key configured in Federation Service
- [ ] JWT secret key generated and secured
- [ ] VERIA agents registered in CommandCenter
- [ ] Network routing verified (port 8082 reachable)
- [ ] Timeout protection enabled
- [ ] Secrets manager configured (future)
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented
- [ ] Team trained on VERIA integration

---

## Resources

- **Full Documentation**: `docs/VERIA_INTEGRATION.md`
- **Architecture**: `hub-prototype/projects/veria-dev/project.json`
- **Orchestration API**: `hub/orchestration/src/api/`
- **Federation Service**: `federation/`
- **Monitoring**: Grafana dashboards at http://localhost:3003

---

## Support & Escalation

**Level 1**: Check this guide and VERIA_INTEGRATION.md

**Level 2**: Review logs and dashboards
- Grafana: http://localhost:3003
- Prometheus: http://localhost:9091
- NATS: http://localhost:8223

**Level 3**: Debug with network tools
```bash
curl, nc, nats-cli, docker-compose logs
```

**Level 4**: Review design documents
- `docs/VERIA_INTEGRATION.md` (Part 6-7: Concerns & Recommendations)
- `docs/plans/2025-11-18-phase-10-agent-orchestration-design.md`

---

**Quick Reference Version**: 1.0
**Last Updated**: 2025-12-03
**Next Update**: After Phase 1 JWT implementation
