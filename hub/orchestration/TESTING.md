# Orchestration Service Testing

## End-to-End Workflow Test

**Status**: Ready for execution (requires infrastructure setup)

### Prerequisites

The orchestration service requires the following infrastructure:

1. **PostgreSQL Database**
   - Connection string: `postgresql://commandcenter:password@postgres:5432/commandcenter`
   - Run migrations: `npx prisma migrate deploy`

2. **NATS Server**
   - Connection string: `nats://commandcenter-hub-nats:4222`
   - Required for event-driven workflow triggers

3. **Dagger Engine**
   - Docker daemon running
   - Required for sandboxed agent execution

### Setup Steps

```bash
# 1. Start infrastructure (add to hub/docker-compose.yml):
# - postgres service
# - nats service
# - orchestration service

# 2. Run database migrations
cd hub/orchestration
npx prisma migrate deploy

# 3. Start orchestration service
npm run dev
# Server should start on port 9002

# 4. In another terminal, register agents
npx ts-node scripts/register-agents.ts

# 5. Create workflow
npx ts-node scripts/create-workflow.ts examples/scan-and-notify-workflow.json

# 6. Get workflow ID
curl http://localhost:9002/api/workflows?projectId=1 | jq '.[0].id'

# 7. Trigger workflow
WORKFLOW_ID="<from-step-6>"
npx ts-node scripts/trigger-workflow.ts $WORKFLOW_ID '{"repositoryPath": "./src"}'

# 8. Check workflow run status
curl http://localhost:9002/api/workflows/$WORKFLOW_ID/runs

# 9. Verify agent runs
curl http://localhost:9002/api/agents/runs?workflowRunId=<run-id>
```

### Expected Results

**Workflow Execution:**
- WorkflowRun status: SUCCESS
- Agent runs: 2 (security-scanner + notifier)
- Execution time: ~5-10 seconds

**Security Scanner Output:**
```json
{
  "findings": [],
  "summary": {
    "total": 0,
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "scannedFiles": 28,
  "scanDurationMs": 3
}
```

**Notifier Output:**
```json
{
  "success": true,
  "channel": "console",
  "timestamp": "2025-11-19T..."
}
```

### Test Status

- ✅ Agents built and tested locally
- ✅ Registration scripts created
- ✅ Workflow definition created
- ✅ Trigger script created
- ⏳ Infrastructure setup pending
- ⏳ E2E execution pending

### Next Steps

To complete E2E testing:
1. Add orchestration service to `hub/docker-compose.yml`
2. Add postgres and NATS services if not present
3. Run the setup steps above
4. Verify workflow executes end-to-end
5. Update this document with actual test results
