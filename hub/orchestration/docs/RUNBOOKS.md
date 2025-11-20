# Operations Runbooks

Troubleshooting guides and operational procedures for the CommandCenter orchestration system.

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Service Health](#service-health)
3. [Database Issues](#database-issues)
4. [Agent Failures](#agent-failures)
5. [Workflow Debugging](#workflow-debugging)
6. [Performance Issues](#performance-issues)
7. [Recovery Procedures](#recovery-procedures)

---

## Common Issues

### Issue: Workflow Stuck in RUNNING

**Symptoms**:
- Workflow status stays RUNNING forever
- No agent runs completing
- Frontend shows infinite spinner

**Diagnosis**:
```bash
# Check workflow status
curl http://localhost:9002/api/workflows/:workflowId/runs/:runId

# Check agent runs
curl http://localhost:9002/api/workflows/:workflowId/runs/:runId/agent-runs

# Check Dagger executor logs
docker logs hub-orchestration 2>&1 | grep "DaggerExecutor"
```

**Root Causes**:
1. **Dagger container failure** - Agent crashed without returning output
2. **JSON parsing error** - Agent printed invalid JSON
3. **Database connection lost** - Status updates failed

**Resolution**:
```bash
# Option 1: Restart orchestration service
docker compose -f docker-compose.observability.yml restart orchestration

# Option 2: Manual workflow status update (last resort)
docker compose exec postgres psql -U user -d orchestration
UPDATE "WorkflowRun" SET status = 'FAILED', "updatedAt" = NOW() WHERE id = 'run-id';
\q
```

---

### Issue: Agent Fails with "ERR_UNKNOWN_FILE_EXTENSION"

**Symptoms**:
- Agent run fails immediately
- Error: "Unknown file extension .ts"

**Root Cause**: TypeScript runtime not installed in Dagger container

**Resolution**:
```typescript
// In src/dagger/executor.ts:49-62
const agentContainer = client
  .container()
  .from('node:20-alpine')
  .withDirectory('/app', agentDir)
  .withWorkdir('/app')
  .withExec(['npm', 'install'])
  .withExec(['npm', 'install', '-g', 'tsx'])  // Add tsx runtime
  .withExec([
    'tsx',  // Use tsx instead of ts-node
    'index.ts',
    JSON.stringify(input),
  ]);
```

**Verify Fix**:
```bash
# Rebuild and test
cd hub/orchestration
npm run build
npm start

# Trigger test workflow
curl -X POST http://localhost:9002/api/workflows/:id/trigger
```

---

### Issue: "Cannot resolve dependency X"

**Symptoms**:
- Workflow creation fails
- Error: "Circular dependency detected"

**Root Cause**: Invalid edge definitions creating cycles

**Diagnosis**:
```bash
# Check workflow edges
curl http://localhost:9002/api/workflows/:workflowId | jq '.edges'
```

**Resolution**:
```typescript
// Fix circular dependency
// BEFORE (circular):
edges: [
  { from: "A", to: "B" },
  { from: "B", to: "C" },
  { from: "C", to: "A" }  // Circular!
]

// AFTER (acyclic):
edges: [
  { from: "A", to: "B" },
  { from: "B", to: "C" }
]
```

---

### Issue: AlertManager Webhook Fails

**Symptoms**:
- Alerts not triggering workflows
- 500 errors from AlertManager webhook endpoint

**Diagnosis**:
```bash
# Check AlertManager logs
docker logs hub-alertmanager 2>&1 | grep "error"

# Test webhook manually
curl -X POST http://localhost:9002/api/webhooks/alertmanager \
  -H "Content-Type: application/json" \
  -d '{"alerts": [{"labels": {"alertname": "test"}}]}'
```

**Root Causes**:
1. **Missing NATSClient** - WorkflowRunner instantiated incorrectly
2. **Invalid workflow schema** - Using obsolete `steps` field
3. **Status not updating** - Failed workflows not marked FAILED

**Resolution**: See commit `4383a78` for fixes

---

## Service Health

### Check All Services

```bash
# Docker Compose status
docker compose -f docker-compose.observability.yml ps

# Expected: All services "Up" status
# - postgres (port 5432)
# - nats (ports 4222, 8222)
# - orchestration (port 9002)
# - prometheus (port 9090)
# - grafana (port 3003)
# - tempo (port 3200)
# - loki (port 3100)
# - otel-collector (ports 4317, 4318)
# - alertmanager (port 9093)
```

### Orchestration Service Health

```bash
# Health check
curl http://localhost:9002/health
# Expected: {"status": "ok", "timestamp": "..."}

# Database health
curl http://localhost:9002/health/db
# Expected: {"status": "connected"}

# NATS health
curl http://localhost:9002/health/nats
# Expected: {"status": "connected"}
```

### Service Logs

```bash
# Orchestration service
docker logs hub-orchestration --tail 100 --follow

# PostgreSQL
docker logs hub-postgres --tail 100

# NATS
docker logs hub-nats --tail 100

# All errors across services
docker compose -f docker-compose.observability.yml logs | grep -i error
```

---

## Database Issues

### Issue: "relation does not exist"

**Symptoms**:
- API returns 500 errors
- Logs show "relation \"WorkflowRun\" does not exist"

**Root Cause**: Prisma migrations not applied

**Resolution**:
```bash
cd hub/orchestration
npx prisma migrate deploy
npx prisma generate
npm run build
docker compose restart orchestration
```

### Issue: Connection Pool Exhausted

**Symptoms**:
- Slow API responses
- "Too many clients" errors

**Diagnosis**:
```sql
-- Check active connections
docker compose exec postgres psql -U user -d orchestration
SELECT count(*) FROM pg_stat_activity WHERE datname = 'orchestration';
\q
```

**Resolution**:
```typescript
// Increase connection pool (src/config.ts)
DATABASE_URL: process.env.DATABASE_URL + '?pool_timeout=30&connection_limit=20'
```

### Backup & Restore

**Backup**:
```bash
docker compose exec postgres pg_dump -U user orchestration > backup.sql
```

**Restore**:
```bash
docker compose exec -T postgres psql -U user orchestration < backup.sql
```

---

## Agent Failures

### Debug Agent Locally

```bash
# Run agent outside Docker
cd hub/orchestration/agents/security-scanner
npm install
npm start '{"repositoryPath": "/workspace", "scanType": "all"}'

# Check exit code
echo $?
# 0 = success, 1 = failure
```

### Common Agent Errors

**Error**: "No input provided"
```bash
# Missing CLI argument
npm start  # Wrong
npm start '{"input": "value"}'  # Correct
```

**Error**: "Zod validation failed"
```bash
# Invalid input schema
npm start '{"invalid": "field"}'  # Wrong
npm start '{"repositoryPath": "/workspace"}'  # Correct
```

**Error**: "ENOENT: no such file or directory"
```bash
# File not found - check path exists
ls /workspace  # Verify path
```

### Agent Output Validation

```bash
# Test agent output is valid JSON
npm start '{"input": "value"}' | jq .
# Should parse successfully

# If parsing fails, check for:
# - console.log() in agent code (should use console.error)
# - Emoji/unicode in output (use stderr for logs)
# - Multi-line output (should be single JSON line)
```

---

## Workflow Debugging

### Enable Debug Logging

```typescript
// In src/dagger/executor.ts
console.error('[DEBUG] Agent input:', JSON.stringify(input));
console.error('[DEBUG] Agent output:', stdout);
console.error('[DEBUG] Agent stderr:', stderr);
```

### Trace Workflow Execution

```bash
# View workflow run history
curl http://localhost:9002/api/workflows/:workflowId/runs | jq '.[]'

# View specific run
curl http://localhost:9002/api/workflows/:workflowId/runs/:runId | jq .

# View agent runs
curl http://localhost:9002/api/workflows/:workflowId/runs/:runId/agent-runs | jq '.[]'
```

### Check Grafana Dashboards

```bash
# Open Grafana
open http://localhost:3003

# View dashboards:
# - Workflow Overview (workflow success rate, duration)
# - Agent Performance (agent failures, retries)
# - System Health (API latency, errors)
```

### Check Prometheus Metrics

```bash
# Query workflow success rate
curl -g 'http://localhost:9090/api/v1/query?query=workflow_success_rate'

# Query agent failures
curl -g 'http://localhost:9090/api/v1/query?query=agent_runs_total{status="FAILED"}'
```

---

## Performance Issues

### Slow Workflow Execution

**Diagnosis**:
```bash
# Check p95 duration
curl -g 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(workflow_duration_seconds_bucket[5m]))'

# Check agent duration breakdown
curl http://localhost:9002/api/workflows/:workflowId/runs/:runId | jq '.agentRuns[] | {name: .agent.name, duration: .durationMs}'
```

**Common Causes**:
1. **Slow agent**: Optimize agent code
2. **Large input**: Reduce data passed to agents
3. **Dagger container startup**: Cache Docker images

**Resolution**:
```bash
# Pre-build agent Docker images
cd hub/orchestration/agents/security-scanner
docker build -t commandcenter-agent-security-scanner .

# Warm up Dagger cache
npm start '{"repositoryPath": "/workspace", "scanType": "all"}'
```

### High Memory Usage

**Diagnosis**:
```bash
# Check container memory
docker stats hub-orchestration

# Check Node.js heap
curl http://localhost:9002/metrics | grep heap_size_bytes
```

**Resolution**:
```bash
# Increase Node.js heap (if needed)
NODE_OPTIONS="--max-old-space-size=4096" npm start
```

---

## Recovery Procedures

### Restart Services

```bash
# Restart single service
docker compose -f docker-compose.observability.yml restart orchestration

# Restart all services
docker compose -f docker-compose.observability.yml restart

# Full restart (clears state)
docker compose -f docker-compose.observability.yml down
docker compose -f docker-compose.observability.yml up -d
```

### Reset Database

**⚠️ WARNING: Destroys all workflow data**

```bash
cd hub/orchestration
npx prisma migrate reset
npx prisma generate
npm run build
docker compose restart orchestration
```

### Rollback Deployment

```bash
# Rollback to previous commit
git log --oneline  # Find commit hash
git checkout <commit-hash>

# Rebuild and restart
cd hub/orchestration
npm install
npm run build
docker compose restart orchestration
```

---

## Escalation

### Level 1: Self-Service
- Check this runbook
- Review Grafana dashboards
- Check service logs

### Level 2: Team Lead
- Persistent failures (> 1 hour)
- Data integrity issues
- Security incidents

### Level 3: Engineering
- Database corruption
- Infrastructure outages
- Critical bugs

---

## Useful Commands

```bash
# Quick health check
docker compose ps && curl -s http://localhost:9002/health | jq .

# View all errors
docker compose logs | grep -i error | tail -20

# Restart everything
docker compose down && docker compose up -d

# Database shell
docker compose exec postgres psql -U user -d orchestration

# Check disk space
df -h

# Check Docker images
docker images | grep commandcenter
```

---

*Last updated: 2025-11-20*
*Next review: Before production deployment*
