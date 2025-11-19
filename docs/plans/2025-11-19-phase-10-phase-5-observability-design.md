# Phase 10 Phase 5: Observability Stack - Design Document

**Date**: 2025-11-19
**Status**: Design Complete - Ready for Implementation
**Design Philosophy**: OpenTelemetry-Native + Production-Grade + Hybrid Deployment

---

## Executive Summary

Phase 5 implements a **production-grade observability stack** for the CommandCenter agent orchestration system using OpenTelemetry as the unified instrumentation layer. The design provides comprehensive visibility into workflow execution, agent performance, system health, and cost tracking through distributed tracing, metrics, and logging.

**Key Goals**:
- Debug workflow failures with distributed tracing
- Monitor performance and identify bottlenecks
- Track costs and optimize resource usage
- Production-ready observability for scale

**Architecture**: OpenTelemetry SDK → OTEL Collector → Tempo (traces) + Prometheus (metrics) + Loki (logs) → Grafana (visualization & alerts)

---

## 1. Architecture Overview

### 1.1 Component Stack

```
┌─────────────────────────────────────────────────────────────┐
│           Orchestration Service (TypeScript)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  @opentelemetry/sdk-node                             │  │
│  │  - Auto-instrumentation (Express, Prisma, Axios)     │  │
│  │  - Custom spans for workflow/agent execution         │  │
│  │  - Metrics (workflow duration, agent runs, errors)   │  │
│  │  - Context propagation across async operations       │  │
│  └────────────────────┬─────────────────────────────────┘  │
└─────────────────────────┼─────────────────────────────────────┘
                          │ OTLP (gRPC)
                          ▼
         ┌──────────────────────────────────┐
         │  OpenTelemetry Collector         │
         │  - Receive OTLP data             │
         │  - Process & enrich spans        │
         │  - Export to multiple backends   │
         └────┬─────────┬────────────┬──────┘
              │         │            │
      Traces  │    Metrics│      Logs│
              ▼         ▼            ▼
        ┌─────────┐ ┌──────────┐ ┌──────┐
        │ Tempo   │ │Prometheus│ │ Loki │
        │ (traces)│ │ (metrics)│ │(logs)│
        └────┬────┘ └─────┬────┘ └──┬───┘
             │            │          │
             └────────────┴──────────┘
                        │
                 ┌──────▼──────┐
                 │   Grafana   │
                 │  Dashboards │
                 │   & Alerts  │
                 └─────────────┘
```

### 1.2 Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Instrumentation** | OpenTelemetry SDK | Vendor-neutral, auto-instrumentation, industry standard |
| **Trace Backend** | Grafana Tempo | Open source, efficient storage, Grafana-native |
| **Metrics Backend** | Prometheus | De facto standard for metrics, powerful PromQL |
| **Log Backend** | Grafana Loki | Log aggregation optimized for Grafana |
| **Visualization** | Grafana | Unified UI for traces/metrics/logs |
| **Collector** | OTEL Collector | Buffer, process, route telemetry data |

### 1.3 Key Benefits

- ✅ **Single instrumentation library** - OpenTelemetry for all signals
- ✅ **Automatic tracing** - HTTP, database, external calls traced automatically
- ✅ **Vendor-neutral** - Can switch backends without code changes
- ✅ **Production-proven** - Used by Netflix, Uber, Airbnb
- ✅ **Cost-effective** - All open-source components

---

## 2. Instrumentation Strategy

### 2.1 Three Layers of Observability

#### Layer 1: Auto-Instrumentation (Zero-code changes)

```typescript
// src/instrumentation.ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { PrometheusExporter } from '@opentelemetry/exporter-prometheus';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'orchestration-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.npm_package_version,
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317',
  }),
  metricReader: new PrometheusExporter({
    port: 9464,
    endpoint: '/metrics',
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-express': { enabled: true },
      '@opentelemetry/instrumentation-prisma': { enabled: true },
      '@opentelemetry/instrumentation-http': { enabled: true },
      '@opentelemetry/instrumentation-axios': { enabled: true },
    }),
  ],
});

sdk.start();

// Graceful shutdown
process.on('SIGTERM', () => {
  sdk.shutdown().finally(() => process.exit(0));
});
```

**Automatically traces**:
- All HTTP requests (Express routes)
- Database queries (Prisma)
- External HTTP calls (Axios)
- Async operations with context propagation

#### Layer 2: Custom Workflow/Agent Spans

```typescript
// src/services/workflow-runner.ts
import { trace, SpanStatusCode, context } from '@opentelemetry/api';

const tracer = trace.getTracer('workflow-runner');

export class WorkflowRunner {
  async executeWorkflow(runId: string): Promise<WorkflowRun> {
    return tracer.startActiveSpan('workflow.execute', async (span) => {
      const workflowRun = await prisma.workflowRun.findUnique({
        where: { id: runId },
        include: { workflow: true },
      });

      // Add span attributes
      span.setAttribute('workflow.run.id', runId);
      span.setAttribute('workflow.id', workflowRun.workflow.id);
      span.setAttribute('workflow.name', workflowRun.workflow.name);
      span.setAttribute('workflow.trigger', workflowRun.trigger);

      try {
        // Update status
        await prisma.workflowRun.update({
          where: { id: runId },
          data: { status: 'RUNNING', startedAt: new Date() },
        });

        // Execute agents with sub-spans
        const results = [];
        for (const node of workflowRun.workflow.nodes) {
          const result = await this.executeAgent(workflowRun.id, node);
          results.push(result);
        }

        // Success
        span.setStatus({ code: SpanStatusCode.OK });
        span.setAttribute('workflow.status', 'SUCCESS');

        return await prisma.workflowRun.update({
          where: { id: runId },
          data: {
            status: 'SUCCESS',
            finishedAt: new Date(),
          },
        });
      } catch (error) {
        // Record error in span
        span.recordException(error);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });
        span.setAttribute('workflow.status', 'FAILED');
        span.setAttribute('error.type', error.constructor.name);

        throw error;
      } finally {
        span.end();
      }
    });
  }

  async executeAgent(workflowRunId: string, node: WorkflowNode): Promise<AgentRun> {
    return tracer.startActiveSpan('agent.execute', async (span) => {
      span.setAttribute('agent.id', node.agentId);
      span.setAttribute('agent.action', node.action);
      span.setAttribute('workflow.run.id', workflowRunId);

      const startTime = Date.now();

      try {
        const agentRun = await prisma.agentRun.create({
          data: {
            workflowRunId,
            agentId: node.agentId,
            inputJson: node.inputsJson,
            status: 'RUNNING',
            startedAt: new Date(),
          },
        });

        // Execute agent via Dagger
        const result = await this.daggerExecutor.runAgent(
          node.agentId,
          node.action,
          node.inputsJson
        );

        const duration = Date.now() - startTime;

        span.setAttribute('agent.status', 'SUCCESS');
        span.setAttribute('agent.duration.ms', duration);
        span.setStatus({ code: SpanStatusCode.OK });

        return await prisma.agentRun.update({
          where: { id: agentRun.id },
          data: {
            status: 'SUCCESS',
            outputJson: result,
            finishedAt: new Date(),
            durationMs: duration,
          },
        });
      } catch (error) {
        span.recordException(error);
        span.setStatus({ code: SpanStatusCode.ERROR });
        span.setAttribute('agent.status', 'FAILED');
        span.setAttribute('error.message', error.message);

        throw error;
      } finally {
        span.end();
      }
    });
  }
}
```

#### Layer 3: Custom Metrics

```typescript
// src/metrics/workflow-metrics.ts
import { metrics } from '@opentelemetry/api';

const meter = metrics.getMeter('orchestration-service');

// Workflow metrics
export const workflowRunCounter = meter.createCounter('workflow.runs.total', {
  description: 'Total number of workflow runs',
  unit: '1',
});

export const workflowDuration = meter.createHistogram('workflow.duration', {
  description: 'Workflow execution time',
  unit: 'ms',
});

export const activeWorkflows = meter.createUpDownCounter('workflows.active', {
  description: 'Number of currently running workflows',
  unit: '1',
});

export const workflowApprovalWaitTime = meter.createHistogram('workflow.approval.wait_time', {
  description: 'Time spent waiting for approval',
  unit: 'ms',
});

// Agent metrics
export const agentRunCounter = meter.createCounter('agent.runs.total', {
  description: 'Total number of agent executions',
  unit: '1',
});

export const agentDuration = meter.createHistogram('agent.duration', {
  description: 'Agent execution time',
  unit: 'ms',
});

export const agentErrorCounter = meter.createCounter('agent.errors.total', {
  description: 'Total agent execution failures',
  unit: '1',
});

export const agentRetryCounter = meter.createCounter('agent.retry.count', {
  description: 'Number of agent retry attempts',
  unit: '1',
});

// Usage in code
workflowRunCounter.add(1, {
  status: 'SUCCESS',
  workflow_id: workflow.id,
  trigger_type: workflowRun.trigger,
});

workflowDuration.record(duration, {
  workflow_id: workflow.id,
  status: workflowRun.status,
});

activeWorkflows.add(1); // Start
// ... execute workflow ...
activeWorkflows.add(-1); // End
```

---

## 3. Metrics & Dashboards

### 3.1 Key Metrics

#### Workflow Metrics
- `workflow.runs.total` (counter)
  - Labels: `status` (SUCCESS/FAILED/PENDING), `workflow_id`, `trigger_type`
- `workflow.duration` (histogram)
  - Labels: `workflow_id`, `status`
- `workflows.active` (gauge)
  - Current count of running workflows
- `workflow.approval.wait_time` (histogram)
  - Labels: `workflow_id`, `node_id`

#### Agent Metrics
- `agent.runs.total` (counter)
  - Labels: `agent_type`, `status`, `workflow_id`
- `agent.duration` (histogram)
  - Labels: `agent_type`, `action`, `status`
- `agent.errors.total` (counter)
  - Labels: `agent_type`, `error_type`
- `agent.retry.count` (counter)
  - Labels: `agent_type`, `reason`

#### System Metrics (auto-collected)
- `http.server.duration` - API endpoint latency
- `http.server.request.size` / `response.size` - Request/response sizes
- `db.client.operation.duration` - Database query performance
- `process.runtime.nodejs.memory.heap` - Memory usage
- `process.runtime.nodejs.cpu.utilization` - CPU usage
- `process.runtime.nodejs.event_loop.lag` - Event loop lag

### 3.2 Grafana Dashboards

#### Dashboard 1: Workflow Overview
**Purpose**: High-level workflow execution monitoring

**Panels**:
1. **Workflows per Minute** (Time series)
   - Query: `sum(rate(workflow_runs_total[1m])) by (status)`
   - Shows: success (green), failed (red), pending (yellow)

2. **Average Workflow Duration** (Gauge)
   - Query: `histogram_quantile(0.95, workflow_duration_bucket)`
   - Alert: > 5 minutes

3. **Active Workflows** (Gauge)
   - Query: `workflows_active`
   - Real-time count

4. **Top 10 Slowest Workflows** (Bar chart)
   - Query: `topk(10, avg(workflow_duration) by (workflow_id))`

5. **Workflow Success Rate** (Stat)
   - Query: `sum(rate(workflow_runs_total{status="SUCCESS"}[5m])) / sum(rate(workflow_runs_total[5m]))`
   - Target: 99%

6. **Approval Queue Depth** (Time series)
   - Query: `count(workflow_runs{status="WAITING_APPROVAL"})`

#### Dashboard 2: Agent Performance
**Purpose**: Agent-level execution analysis

**Panels**:
1. **Agent Execution Heatmap** (Heatmap)
   - Query: `sum(rate(agent_runs_total[5m])) by (agent_type, time)`
   - Shows: when agents run most frequently

2. **Agent Duration Percentiles** (Time series)
   - Query: `histogram_quantile(0.50, agent_duration_bucket)` (p50)
   - Query: `histogram_quantile(0.95, agent_duration_bucket)` (p95)
   - Query: `histogram_quantile(0.99, agent_duration_bucket)` (p99)

3. **Agent Failure Rate** (Bar gauge)
   - Query: `sum(rate(agent_errors_total[5m])) by (agent_type)`

4. **Most Expensive Agents** (Table)
   - Query: `sum(agent_duration * agent_runs_total) by (agent_type)`
   - Columns: Agent Type, Total Duration, Avg Duration, Execution Count

5. **Agent Retry Trends** (Time series)
   - Query: `sum(rate(agent_retry_count[1m])) by (agent_type, reason)`

#### Dashboard 3: System Health
**Purpose**: Infrastructure and API health

**Panels**:
1. **API Response Times** (Time series)
   - Query: `histogram_quantile(0.95, http_server_duration_bucket) by (http_route)`

2. **Database Query Latency** (Time series)
   - Query: `histogram_quantile(0.95, db_client_operation_duration_bucket)`

3. **Error Rate** (Stat + time series)
   - Query: `sum(rate(http_server_requests_total{status=~"5.."}[1m]))`
   - Alert: > 10 errors/min

4. **Node.js Memory** (Time series)
   - Query: `process_runtime_nodejs_memory_heap_bytes`
   - Alert: > 80% of max heap

5. **Event Loop Lag** (Time series)
   - Query: `process_runtime_nodejs_event_loop_lag_milliseconds`
   - Alert: > 100ms

6. **Active HTTP Connections** (Gauge)
   - Query: `http_server_active_connections`

#### Dashboard 4: Cost Tracking
**Purpose**: Resource usage and cost allocation

**Panels**:
1. **Agent Execution Minutes** (Bar chart)
   - Query: `sum(agent_duration / 60000) by (agent_type)`
   - For cost allocation by agent type

2. **Workflow Cost Breakdown** (Pie chart)
   - Query: `sum(workflow_duration) by (workflow_id)`
   - Shows: which workflows consume most resources

3. **Monthly Execution Trends** (Time series)
   - Query: `sum(increase(agent_runs_total[30d]))`

4. **Cost per Workflow Type** (Table)
   - Columns: Workflow, Runs, Total Duration, Avg Cost

---

## 4. Infrastructure & Deployment

### 4.1 Docker Compose (Local Development)

```yaml
# hub/docker-compose.observability.yml
version: '3.8'

services:
  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.91.0
    container_name: hub-otel-collector
    command: ["--config=/etc/otel-collector-config.yml"]
    volumes:
      - ./observability/otel-collector-config.yml:/etc/otel-collector-config.yml
    ports:
      - "4317:4317"   # OTLP gRPC receiver
      - "4318:4318"   # OTLP HTTP receiver
      - "8888:8888"   # Metrics endpoint
    networks:
      - observability

  # Tempo (Distributed Tracing)
  tempo:
    image: grafana/tempo:2.3.1
    container_name: hub-tempo
    command: ["-config.file=/etc/tempo.yml"]
    volumes:
      - ./observability/tempo.yml:/etc/tempo.yml
      - tempo_data:/tmp/tempo
    ports:
      - "3200:3200"   # Tempo HTTP
      - "4317"        # OTLP gRPC (internal)
    networks:
      - observability

  # Prometheus (Metrics)
  prometheus:
    image: prom/prometheus:v2.48.1
    container_name: hub-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - observability

  # Loki (Logs)
  loki:
    image: grafana/loki:2.9.3
    container_name: hub-loki
    command: -config.file=/etc/loki/local-config.yml
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
    networks:
      - observability

  # Grafana (Visualization)
  grafana:
    image: grafana/grafana:10.2.3
    container_name: hub-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=http://localhost:3001
      - GF_AUTH_ANONYMOUS_ENABLED=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./observability/grafana/provisioning:/etc/grafana/provisioning
      - ./observability/grafana/dashboards:/var/lib/grafana/dashboards
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
      - tempo
      - loki
    networks:
      - observability

volumes:
  tempo_data:
    driver: local
  prometheus_data:
    driver: local
  loki_data:
    driver: local
  grafana_data:
    driver: local

networks:
  observability:
    driver: bridge
```

**Usage**:
```bash
# Start observability stack
docker-compose -f docker-compose.observability.yml up -d

# Access dashboards
open http://localhost:3001  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
open http://localhost:3200  # Tempo

# View logs
docker-compose -f docker-compose.observability.yml logs -f

# Stop stack
docker-compose -f docker-compose.observability.yml down
```

### 4.2 Production Kubernetes Deployment

**Helm Chart Structure**:
```
observability/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── otel-collector/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── tempo/
    │   ├── statefulset.yaml
    │   ├── service.yaml
    │   └── pvc.yaml
    ├── prometheus/
    │   ├── statefulset.yaml
    │   ├── service.yaml
    │   └── pvc.yaml
    ├── loki/
    │   ├── statefulset.yaml
    │   ├── service.yaml
    │   └── pvc.yaml
    └── grafana/
        ├── deployment.yaml
        ├── service.yaml
        ├── ingress.yaml
        └── pvc.yaml
```

**Production Considerations**:
- Persistent volumes for data retention (30 days Prometheus, 7 days Tempo)
- Ingress with TLS for external access
- Resource limits (CPU/memory)
- Horizontal pod autoscaling for OTEL Collector
- High availability (3 replicas for Prometheus/Tempo)
- Backup strategy for Grafana dashboards

---

## 5. Alerting & SLOs

### 5.1 Grafana Alert Rules

#### Critical Alerts (PagerDuty/On-Call)

**WorkflowFailureRate**:
```yaml
alert: WorkflowFailureRate
expr: |
  sum(rate(workflow_runs_total{status="FAILED"}[5m]))
  / sum(rate(workflow_runs_total[5m])) > 0.10
for: 5m
labels:
  severity: critical
annotations:
  summary: "High workflow failure rate ({{ $value | humanizePercentage }})"
  description: "More than 10% of workflows are failing in the last 5 minutes"
  runbook_url: "https://docs.commandcenter.io/runbooks/workflow-failure-rate"
```

**ServiceDown**:
```yaml
alert: ServiceDown
expr: up{job="orchestration-service"} == 0
for: 1m
labels:
  severity: critical
annotations:
  summary: "Orchestration service is down"
  description: "The orchestration service has been unavailable for 1 minute"
```

**DatabaseConnectionLoss**:
```yaml
alert: DatabaseConnectionLoss
expr: |
  rate(db_client_operation_duration_count[1m]) == 0
for: 1m
labels:
  severity: critical
annotations:
  summary: "No database queries in the last minute"
  description: "Database connection may be lost"
```

**HighErrorRate**:
```yaml
alert: HighErrorRate
expr: |
  sum(rate(http_server_requests_total{status=~"5.."}[1m])) > 50
for: 2m
labels:
  severity: critical
annotations:
  summary: "High 5xx error rate: {{ $value }} errors/min"
  description: "More than 50 server errors per minute"
```

#### Warning Alerts (Slack Notifications)

**HighWorkflowDuration**:
```yaml
alert: HighWorkflowDuration
expr: |
  histogram_quantile(0.95,
    rate(workflow_duration_bucket[5m])) > 300000
for: 10m
labels:
  severity: warning
annotations:
  summary: "High workflow duration (p95: {{ $value | humanizeDuration }})"
  description: "95th percentile workflow duration > 5 minutes"
```

**AgentFailureSpike**:
```yaml
alert: AgentFailureSpike
expr: |
  sum(rate(agent_errors_total[10m])) by (agent_type) > 0.5
for: 10m
labels:
  severity: warning
annotations:
  summary: "Agent {{ $labels.agent_type }} failing frequently"
  description: "More than 5 failures in 10 minutes"
```

**ApprovalBacklog**:
```yaml
alert: ApprovalBacklog
expr: |
  count(workflow_runs{status="WAITING_APPROVAL"}) > 20
for: 30m
labels:
  severity: warning
annotations:
  summary: "Large approval backlog ({{ $value }} workflows)"
  description: "More than 20 workflows waiting for approval"
```

**HighMemoryUsage**:
```yaml
alert: HighMemoryUsage
expr: |
  process_runtime_nodejs_memory_heap_bytes
  / process_runtime_nodejs_memory_heap_max_bytes > 0.8
for: 5m
labels:
  severity: warning
annotations:
  summary: "High memory usage ({{ $value | humanizePercentage }})"
  description: "Process memory usage > 80% for 5 minutes"
```

### 5.2 Service Level Objectives (SLOs)

```yaml
slos:
  - name: Workflow Success Rate
    description: Percentage of workflows that complete successfully
    target: 99.0%
    window: 30d
    query: |
      sum(rate(workflow_runs_total{status="SUCCESS"}[30d]))
      / sum(rate(workflow_runs_total[30d]))

  - name: API Availability
    description: Percentage of time the API is responding to requests
    target: 99.9%
    window: 30d
    query: up{job="orchestration-service"}

  - name: Workflow Latency (p95)
    description: 95th percentile workflow completion time
    target: 95%
    percentile: p95
    threshold: 120s
    window: 7d
    query: |
      histogram_quantile(0.95,
        rate(workflow_duration_bucket[7d]))

  - name: Agent Success Rate
    description: Percentage of agent executions that succeed
    target: 98.0%
    window: 7d
    query: |
      sum(rate(agent_runs_total{status="SUCCESS"}[7d]))
      / sum(rate(agent_runs_total[7d]))
```

### 5.3 Alert Integration with Notifier Agent

**Grafana Webhook → Workflow Trigger**:

```typescript
// src/api/routes/webhooks.ts
router.post('/webhooks/grafana', async (req, res) => {
  const alert: GrafanaAlert = req.body;

  // Map Grafana alert to workflow context
  const context = {
    severity: alert.state === 'alerting' ? 'critical' : 'warning',
    alert_name: alert.ruleName,
    message: alert.message,
    dashboard_url: alert.dashboardURL,
    runbook_url: getRunbookURL(alert.ruleName),
    timestamp: new Date().toISOString(),
    labels: alert.labels,
  };

  // Trigger alert-notification workflow
  const workflowRun = await prisma.workflowRun.create({
    data: {
      workflowId: 'alert-notification-workflow-id',
      trigger: 'grafana_webhook',
      contextJson: context,
      status: 'PENDING',
    },
  });

  // Execute workflow (notifier agent will send Slack/Discord message)
  await workflowRunner.executeWorkflow(workflowRun.id);

  res.status(200).json({ workflowRunId: workflowRun.id });
});
```

This routes Grafana alerts through the workflow system, leveraging the existing `notifier` agent for delivery to Slack/Discord/etc.

---

## 6. Implementation Roadmap

### Phase 1: Foundation (2-3 hours)

**Tasks**:
1. Install OpenTelemetry dependencies
   ```bash
   npm install @opentelemetry/sdk-node \
     @opentelemetry/auto-instrumentations-node \
     @opentelemetry/exporter-trace-otlp-grpc \
     @opentelemetry/exporter-prometheus
   ```

2. Create instrumentation setup (`src/instrumentation.ts`)
   - Initialize NodeSDK
   - Configure auto-instrumentations
   - Set up OTLP exporter

3. Update `src/index.ts` to import instrumentation first
   ```typescript
   import './instrumentation'; // MUST be first import
   import { startServer } from './api/server';
   ```

4. Create Docker Compose observability stack
   - `docker-compose.observability.yml`
   - Configuration files for OTEL Collector, Prometheus, Tempo, Loki

5. Start stack and verify basic traces
   ```bash
   docker-compose -f docker-compose.observability.yml up -d
   npm run dev
   # Make API request
   # Check Tempo UI for traces
   ```

**Success Criteria**:
- ✅ Auto-instrumentation capturing HTTP/DB calls
- ✅ Traces visible in Tempo
- ✅ Prometheus scraping metrics

### Phase 2: Custom Spans (2-3 hours)

**Tasks**:
1. Add workflow execution spans
   - Start span at workflow trigger
   - Add attributes (workflow ID, name, trigger)
   - Record duration and status

2. Add agent execution spans
   - Nested spans for each agent
   - Attributes (agent type, action, inputs)
   - Error recording

3. Add approval wait time tracking
   - Span for approval requests
   - Duration from request to decision

4. Verify context propagation
   - Ensure parent-child span relationships
   - Check trace continuity across async operations

**Success Criteria**:
- ✅ Complete workflow execution trace with agent spans
- ✅ Error details in failed spans
- ✅ Parent-child relationships correct

### Phase 3: Metrics & Dashboards (3-4 hours)

**Tasks**:
1. Implement custom metrics
   - Create meter and instruments
   - Add metric recording in workflow/agent code
   - Labels for filtering (status, workflow_id, agent_type)

2. Configure Grafana data sources
   - Tempo (traces)
   - Prometheus (metrics)
   - Loki (logs)

3. Build 4 core dashboards
   - Workflow Overview
   - Agent Performance
   - System Health
   - Cost Tracking

4. Set up dashboard provisioning
   - JSON dashboard definitions
   - Auto-load on Grafana startup

**Success Criteria**:
- ✅ Custom metrics appearing in Prometheus
- ✅ Dashboards showing real-time data
- ✅ Dashboards persist after Grafana restart

### Phase 4: Alerting (2-3 hours)

**Tasks**:
1. Configure Grafana alert rules
   - Critical alerts (4 rules)
   - Warning alerts (4 rules)

2. Set up notification channels
   - Slack via notifier agent webhook
   - Email for critical alerts

3. Define SLO targets
   - Configure recording rules
   - Create SLO dashboard

4. Test alert delivery end-to-end
   - Trigger failing workflow
   - Verify alert fires
   - Check Slack notification

5. Create runbooks
   - Document common alerts
   - Troubleshooting steps

**Success Criteria**:
- ✅ Alerts fire within 1 minute of threshold breach
- ✅ Slack notifications delivered
- ✅ Runbooks accessible from alert messages

---

## 7. Testing Strategy

### 7.1 Local Verification

1. **Start Observability Stack**:
   ```bash
   docker-compose -f docker-compose.observability.yml up -d
   ```

2. **Start Orchestration Service**:
   ```bash
   npm run dev
   ```

3. **Trigger Test Workflow**:
   ```bash
   curl -X POST http://localhost:9002/api/workflows/scan-and-notify/trigger \
     -H "Content-Type: application/json" \
     -d '{"contextJson": {"repository": "test-repo"}}'
   ```

4. **Verify Observability**:
   - **Traces**: Open Tempo UI (http://localhost:3200), search for trace
   - **Metrics**: Open Prometheus (http://localhost:9090), query `workflow_runs_total`
   - **Dashboards**: Open Grafana (http://localhost:3001), view Workflow Overview dashboard

**Expected Results**:
- Trace shows HTTP request → workflow execution → agent runs
- Metrics show workflow count incremented
- Dashboard shows workflow in "success" category

### 7.2 Load Testing

1. **Trigger Concurrent Workflows**:
   ```bash
   for i in {1..50}; do
     curl -X POST http://localhost:9002/api/workflows/scan-and-notify/trigger \
       -H "Content-Type: application/json" \
       -d "{\"contextJson\": {\"repo\": \"repo-$i\"}}" &
   done
   wait
   ```

2. **Verify Metrics Scale**:
   - Check `workflows.active` gauge shows 50
   - Check `workflow_runs_total` increments by 50
   - Verify no metric cardinality explosion

3. **Check Dashboard Performance**:
   - Dashboards remain responsive
   - Queries complete in < 1s

### 7.3 Failure Scenarios

1. **Trigger Failing Agent**:
   ```bash
   # Workflow with agent that will fail
   curl -X POST http://localhost:9002/api/workflows/test-failure/trigger
   ```

2. **Verify Error Observability**:
   - Trace shows failed span with exception details
   - `agent.errors.total` metric incremented
   - Dashboard shows failure in red

3. **Check Alert Fires**:
   - If failure rate > 10%, alert should fire within 5 minutes
   - Slack notification should be delivered
   - Alert state visible in Grafana

### 7.4 Success Criteria

- ✅ All HTTP/DB operations auto-traced without code changes
- ✅ Custom workflow/agent spans with detailed attributes
- ✅ Dashboards show real-time workflow metrics
- ✅ Alerts fire within 1 minute of threshold breach
- ✅ End-to-end trace from API request → workflow → agents → response
- ✅ Metrics have low cardinality (< 100 unique label combinations)
- ✅ Dashboard queries complete in < 2 seconds under load
- ✅ Observability stack uses < 500MB memory combined

---

## 8. Configuration Files

### 8.1 OpenTelemetry Collector Config

```yaml
# observability/otel-collector-config.yml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

  resource:
    attributes:
      - key: deployment.environment
        value: ${ENVIRONMENT}
        action: upsert

  # Add useful attributes
  attributes:
    actions:
      - key: service.namespace
        value: commandcenter-hub
        action: upsert

exporters:
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: orchestration

  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource, attributes]
      exporters: [otlp/tempo]

    metrics:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [prometheus]

    logs:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [loki]
```

### 8.2 Prometheus Config

```yaml
# observability/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'commandcenter-hub'
    environment: 'development'

scrape_configs:
  # Orchestration service metrics
  - job_name: 'orchestration-service'
    static_configs:
      - targets: ['host.docker.internal:9464']

  # OTEL Collector metrics
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8888']

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### 8.3 Tempo Config

```yaml
# observability/tempo.yml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317

ingester:
  trace_idle_period: 10s
  max_block_bytes: 1_000_000
  max_block_duration: 5m

compactor:
  compaction:
    block_retention: 168h  # 7 days

storage:
  trace:
    backend: local
    wal:
      path: /tmp/tempo/wal
    local:
      path: /tmp/tempo/blocks

query_frontend:
  search:
    duration_slo: 5s
    throughput_bytes_slo: 1.073741824e+09
```

### 8.4 Grafana Provisioning

```yaml
# observability/grafana/provisioning/datasources/datasources.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    editable: false
    jsonData:
      tracesToLogs:
        datasourceUid: 'loki'
      serviceMap:
        datasourceUid: 'prometheus'

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "traceID=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"
```

---

## 9. Operational Considerations

### 9.1 Data Retention

| Component | Retention | Storage | Rationale |
|-----------|-----------|---------|-----------|
| **Prometheus** | 30 days | ~5GB | Metrics for trend analysis |
| **Tempo** | 7 days | ~10GB | Recent traces for debugging |
| **Loki** | 7 days | ~3GB | Log correlation with traces |
| **Grafana** | Indefinite | ~100MB | Dashboard configs |

### 9.2 Resource Requirements

**Development (Docker Compose)**:
- CPU: 2 cores
- Memory: 4GB total
  - OTEL Collector: 512MB
  - Tempo: 1GB
  - Prometheus: 1GB
  - Loki: 512MB
  - Grafana: 512MB

**Production (Kubernetes)**:
- CPU: 8 cores
- Memory: 16GB total
- Storage: 50GB (persistent volumes)

### 9.3 Backup Strategy

- **Grafana Dashboards**: Export JSON to git repository
- **Alert Rules**: Store YAML configs in git
- **Prometheus Data**: Not backed up (can be regenerated)
- **Tempo Traces**: Not backed up (short retention)

### 9.4 Security Considerations

- **Authentication**: Grafana admin password (change default!)
- **Network**: Observability stack on private network
- **Ingress**: TLS for external access
- **Secrets**: Store Grafana password in secrets manager
- **RBAC**: Grafana roles for view-only vs admin users

---

## 10. Future Enhancements

### Phase 6+ Potential Additions

1. **Continuous Profiling**
   - Pyroscope integration
   - CPU/memory flame graphs
   - Profile workflow bottlenecks

2. **Anomaly Detection**
   - ML-based alerting
   - Detect unusual workflow patterns
   - Adaptive thresholds

3. **Distributed Tracing Across Projects**
   - Trace workflows that span multiple CommandCenter instances
   - Federation-aware tracing

4. **Cost Optimization Dashboard**
   - Cloud cost integration (AWS/GCP cost APIs)
   - Agent cost-per-execution
   - Recommendations for optimization

5. **Custom Grafana Plugin**
   - Workflow execution visualizer
   - Interactive DAG view with trace data
   - Agent run timeline

---

## Appendix A: Dependencies

```json
{
  "dependencies": {
    "@opentelemetry/sdk-node": "^0.45.0",
    "@opentelemetry/auto-instrumentations-node": "^0.39.0",
    "@opentelemetry/exporter-trace-otlp-grpc": "^0.45.0",
    "@opentelemetry/exporter-prometheus": "^0.45.0",
    "@opentelemetry/api": "^1.7.0",
    "@opentelemetry/resources": "^1.18.0",
    "@opentelemetry/semantic-conventions": "^1.18.0"
  }
}
```

## Appendix B: Useful PromQL Queries

```promql
# Workflow success rate (last 5 minutes)
sum(rate(workflow_runs_total{status="SUCCESS"}[5m]))
/ sum(rate(workflow_runs_total[5m]))

# Top 5 slowest workflows
topk(5, avg(workflow_duration) by (workflow_id))

# Agent error rate by type
sum(rate(agent_errors_total[5m])) by (agent_type)

# API latency p95 by endpoint
histogram_quantile(0.95,
  sum(rate(http_server_duration_bucket[5m])) by (le, http_route))

# Memory usage trend
process_runtime_nodejs_memory_heap_bytes / 1024 / 1024

# Active workflows vs capacity
workflows_active / 100  # assuming capacity of 100
```

## Appendix C: Runbook Template

```markdown
# Runbook: [Alert Name]

## Severity
[Critical / Warning]

## Description
[What this alert means]

## Impact
[What happens if not addressed]

## Diagnosis Steps
1. Check Grafana dashboard: [link]
2. Query Prometheus: [example query]
3. View traces in Tempo: [search query]
4. Check logs: [Loki query]

## Resolution Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Prevention
[How to prevent this in the future]

## Escalation
[Who to contact if resolution fails]
```

---

**End of Design Document**
