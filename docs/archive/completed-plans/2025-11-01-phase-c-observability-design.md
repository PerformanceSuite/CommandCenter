# Phase C: Observability Layer - Design Document

**Date**: 2025-11-01
**Status**: Approved
**Approach**: Pragmatic Quick Wins (Incremental)

## Executive Summary

Phase C enhances CommandCenter's observability by building on the existing Prometheus/Grafana/Loki stack. We add critical capabilities—error tracking, database observability, request correlation, and operational dashboards—without introducing new external dependencies or SaaS costs. This incremental approach delivers fast ROI while establishing patterns for future distributed tracing (Phase D).

**Key Decisions**:
- ✅ Self-hosted error tracking (Loki + Prometheus) instead of Sentry Cloud
- ✅ Correlation IDs extracted from hub-prototype pattern
- ✅ PostgreSQL exporter for database metrics
- ✅ 4-week phased rollout with feature flags

## Background

### Current State

CommandCenter has **60% observability maturity**:

**Strengths** (Production-ready):
- Prometheus metrics with custom application metrics
- Grafana visualization with basic dashboard
- Loki log aggregation with Promtail shipping
- Structured JSON logging with request IDs
- Comprehensive health checks (database, Redis, Celery)
- AlertManager with 15+ production alerts

**Critical Gaps**:
- No distributed tracing (10% maturity)
- Basic error tracking (30% maturity - logs only)
- Minimal database observability (25% maturity)
- No correlation between API → Celery → Database
- Existing metrics under-utilized (no advanced dashboards)

### hub-prototype Analysis

The hub-prototype revealed valuable patterns:
- **Correlation IDs**: Every event has UUID for distributed tracing foundation
- **Event Origin Tracking**: Identify which component emitted event
- **JSONL Event Streaming**: Append-only audit trail with temporal replay

**Extracted for Phase C**:
- Correlation ID middleware pattern
- Event origin concept → adapted for request context
- Temporal correlation → request_id as join key across logs/metrics

## Goals & Success Criteria

### Capabilities to Deliver

1. **Enhanced Error Tracking** - Self-hosted using Loki + Prometheus
2. **Database Observability** - postgres_exporter + dashboards
3. **Request Correlation** - IDs propagated: API → Celery → Database
4. **Operational Dashboards** - Error tracking, DB performance, Celery, Golden Signals
5. **Proactive Alerting** - AlertManager rules for critical conditions

### Success Metrics

- **Mean-Time-to-Detection (MTTD)**: < 5 minutes for critical errors
- **Mean-Time-to-Resolution (MTTR)**: 50% reduction via correlation IDs
- **False Positive Alerts**: < 5% of total alerts
- **Dashboard Adoption**: Team uses dashboards daily for debugging
- **Performance Overhead**: Middleware latency < 1ms

## Architecture

### High-Level Stack

```
┌─────────────────────────────────────────┐
│         Observability Layer             │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────┐  ┌──────────┐            │
│  │ Grafana  │  │AlertMgr  │            │
│  │ Enhanced │  │New Rules │            │
│  │Dashboards│  │          │            │
│  └────┬─────┘  └────┬─────┘            │
│       │             │                   │
│  ┌────▼─────┬──────▼──────┬─────────┐  │
│  │Prometheus│    Loki     │Postgres │  │
│  │ Existing │  Enhanced   │Exporter │  │
│  │          │ Parsing     │  NEW    │  │
│  └────▲─────┴──────▲──────┴────▲────┘  │
│       │            │           │        │
└───────┼────────────┼───────────┼────────┘
        │            │           │
┌───────▼────────────▼───────────▼────────┐
│    Instrumented Application             │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   FastAPI Backend                │  │
│  │  - NEW: Correlation ID middleware│  │
│  │  - NEW: Error metrics counter    │  │
│  │  - Enhanced: Structured errors   │  │
│  │  - Existing: Prometheus metrics  │  │
│  └──────────┬───────────────────────┘  │
│             │                           │
│  ┌──────────▼───────────┐              │
│  │   Celery Workers     │              │
│  │  - NEW: Inherit      │              │
│  │    correlation IDs   │              │
│  │  - Enhanced: Task    │              │
│  │    error metrics     │              │
│  └──────────┬───────────┘              │
│             │                           │
│  ┌──────────▼───────────┐              │
│  │   PostgreSQL         │              │
│  │  - NEW: Exporter     │              │
│  │  - NEW: Query        │              │
│  │    comments (IDs)    │              │
│  └──────────────────────┘              │
│                                         │
└─────────────────────────────────────────┘
```

### New Components

#### 1. postgres_exporter (Docker Container)

**Purpose**: Expose PostgreSQL internal metrics to Prometheus

**Implementation**:
- Image: `prometheuscommunity/postgres-exporter:latest`
- Port: 9187
- Connection: Read-only `exporter_user` with monitoring privileges
- Metrics: Connection pools, query stats, table sizes, index usage, bloat

**Docker Compose** (`docker-compose.prod.yml`):
```yaml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter:latest
  environment:
    DATA_SOURCE_NAME: "postgresql://exporter_user:${EXPORTER_PASSWORD}@postgres:5432/commandcenter?sslmode=disable"
  ports:
    - "9187:9187"
  depends_on:
    - postgres
  restart: unless-stopped
```

**Database Setup** (migration):
```sql
CREATE USER exporter_user WITH PASSWORD '${EXPORTER_PASSWORD}';
GRANT CONNECT ON DATABASE commandcenter TO exporter_user;
GRANT pg_monitor TO exporter_user;
```

#### 2. Correlation ID Middleware (FastAPI)

**Purpose**: Generate/extract request IDs and propagate through system

**File**: `backend/app/middleware/correlation.py`

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logging import get_logger_with_context

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store in request state
        request.state.request_id = correlation_id

        # Add to logging context
        logger = get_logger_with_context(__name__, request_id=correlation_id)
        request.state.logger = logger

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = correlation_id

        return response
```

**Registration** (`backend/app/main.py`):
```python
from app.middleware.correlation import CorrelationIDMiddleware

app.add_middleware(CorrelationIDMiddleware)
```

#### 3. Error Metrics Counter (Prometheus)

**Purpose**: Track errors by endpoint, status code, and type

**File**: `backend/app/utils/metrics.py` (addition)

```python
from prometheus_client import Counter

error_counter = Counter(
    'commandcenter_errors_total',
    'Total errors by endpoint and type',
    ['endpoint', 'status_code', 'error_type']
)
```

**Enhanced Exception Handler** (`backend/app/main.py`):
```python
@app.exception_handler(Exception)
async def enhanced_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")

    # Increment error metric
    error_counter.labels(
        endpoint=request.url.path,
        status_code=500,
        error_type=type(exc).__name__
    ).inc()

    # Structured error logging
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "user_id": getattr(request.state, "user_id", None),
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id}
    )
```

#### 4. Celery Task Correlation

**Purpose**: Inherit correlation IDs in async tasks

**File**: `backend/app/tasks/__init__.py` (enhancement)

```python
@celery_app.task(bind=True)
def tracked_task(self, *args, **kwargs):
    # Extract correlation ID from headers
    request_id = self.request.get("headers", {}).get("request_id", "unknown")

    # Set up logger with correlation
    logger = get_logger_with_context(__name__, request_id=request_id)

    # Task execution with correlation context
    logger.info(f"Starting task {self.name}", extra={"request_id": request_id})

    try:
        result = execute_task_logic(*args, **kwargs)
        logger.info(f"Task completed", extra={"request_id": request_id})
        return result
    except Exception as e:
        logger.error(f"Task failed", extra={"request_id": request_id}, exc_info=True)
        raise
```

**Task Invocation** (pass request_id):
```python
from celery import current_task

def trigger_background_job(request_id: str):
    tracked_task.apply_async(
        args=[...],
        headers={"request_id": request_id}
    )
```

#### 5. Database Query Comments

**Purpose**: Tag SQL queries with correlation IDs for pg_stat_statements

**File**: `backend/app/db/session.py` (SQLAlchemy event)

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def add_query_comment(conn, cursor, statement, parameters, context, executemany):
    # Extract request_id from connection context
    request_id = getattr(context, "request_id", None)
    if request_id:
        statement = f"/* request_id: {request_id} */ {statement}"
    return statement, parameters
```

#### 6. Grafana Dashboards

**Purpose**: Visualize observability data

**Files** (JSON dashboard definitions):
- `monitoring/grafana/dashboards/error-tracking.json` - Error rates, top errors, search
- `monitoring/grafana/dashboards/database-performance.json` - Connection pools, slow queries, index usage
- `monitoring/grafana/dashboards/celery-deep-dive.json` - Task duration, failure rates, queue depth
- `monitoring/grafana/dashboards/golden-signals.json` - Latency, traffic, errors, saturation (API overview)

**Key Panels**:

**Error Tracking Dashboard**:
- Error rate over time (line chart)
- Errors by endpoint (bar chart)
- Error type distribution (pie chart)
- Recent errors with stack traces (table from Loki)
- Request ID lookup (input field → filter logs)

**Database Performance Dashboard**:
- Active connections vs pool limit (gauge + graph)
- Query duration percentiles P50/P95/P99 (heatmap)
- Top 10 slowest queries (table)
- Connection pool saturation (%) over time
- Table sizes and growth trends

**Celery Deep-Dive Dashboard**:
- Tasks executed per minute (line chart)
- Task duration by type (histogram)
- Task failure rate (%) by type
- Queue depth over time
- Worker status (up/down indicators)

**Golden Signals Dashboard**:
- Latency: Request duration P50/P95/P99
- Traffic: Requests per second by endpoint
- Errors: Error rate (%) over time
- Saturation: CPU, memory, connection pools

#### 7. AlertManager Rules

**Purpose**: Proactive notifications for critical conditions

**File**: `monitoring/alerts.yml` (additions)

```yaml
groups:
  - name: phase_c_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (rate(commandcenter_errors_total[5m]) / rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # Database connection pool exhausted
      - alert: DatabasePoolExhausted
        expr: |
          (pg_stat_database_numbackends / pg_settings_max_connections) > 0.9
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Pool utilization is {{ $value | humanizePercentage }} (threshold: 90%)"

      # Slow API responses
      - alert: SlowAPIResponses
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API P95 latency above threshold"
          description: "P95 latency is {{ $value }}s (threshold: 1s)"

      # Celery worker down
      - alert: CeleryWorkerDown
        expr: |
          celery_workers_active < 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "No Celery workers active"
          description: "Background job processing is stopped"

      # Disk space low
      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space below 10%"
          description: "Available: {{ $value | humanizePercentage }}"
```

## Data Flow & Correlation

### Request Correlation Flow

```
1. HTTP Request arrives
   ↓
2. Correlation Middleware
   - Extract X-Request-ID header OR generate UUID
   - Store in request.state.request_id
   - Inject into logging context
   ↓
3. API Handler executes
   - All logs include request_id
   - Metrics labeled with request_id
   - Errors tagged with request_id
   ↓
4. Celery Task triggered
   - Pass request_id in task headers
   - Task logger inherits request_id
   - Task metrics labeled with request_id
   ↓
5. Database Query executed
   - Add SQL comment: /* request_id: xyz */
   - postgres_exporter captures slow queries with IDs
   ↓
6. Response returned
   - X-Request-ID header in response
   - Client can reference for support
```

### Error Tracking Flow

```
1. Exception occurs in FastAPI
   ↓
2. Global exception handler catches
   - Log with full stack trace (Loki)
   - Increment error counter (Prometheus)
   - Include: request_id, endpoint, user_id, error_type
   ↓
3. Grafana Error Dashboard shows
   - Error rate over time (from Prometheus)
   - Top errors by endpoint
   - Error details (query Loki by request_id)
   ↓
4. AlertManager fires if threshold exceeded
   - Slack notification: "Error rate >5% on /api/v1/repositories"
   - Includes dashboard link + recent errors
```

### Database Observability Flow

```
1. postgres_exporter polls PostgreSQL every 15s
   - Connection pool stats
   - Query duration from pg_stat_statements
   - Table sizes, index usage, bloat
   ↓
2. Prometheus scrapes exporter metrics
   ↓
3. Grafana Database Dashboard displays
   - Active connections vs pool limit
   - Slowest queries (P95/P99)
   - Connection pool saturation
   - Table growth trends
   ↓
4. Alert fires if pool > 90%
   - "Database connection pool nearly exhausted"
```

### Correlation as Join Key

The correlation ID (`request_id`) serves as a **join key** across observability data:

- **Logs** (Loki): Filter by `{request_id="abc123"}`
- **Metrics** (Prometheus): `commandcenter_errors_total{request_id="abc123"}`
- **Traces** (Future - Phase D): Span context will use request_id
- **Database**: SQL comments in `pg_stat_statements` with request_id

**Debugging Workflow**:
1. Alert fires: "High error rate on /api/v1/repositories"
2. Open Grafana error dashboard → see spike
3. Click spike → drill into Loki logs filtered by timerange + endpoint
4. Find request_id in error log
5. Search Loki for all logs with that request_id (full trace)
6. Check postgres_exporter slow queries for same request_id
7. Identify root cause (e.g., slow query → timeout → error)

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Goals**: Add correlation middleware, enhance error tracking

**Tasks**:
1. Create `backend/app/middleware/correlation.py`
2. Register middleware in `backend/app/main.py`
3. Add `error_counter` metric to `backend/app/utils/metrics.py`
4. Enhance global exception handler with structured logging + metrics
5. Write unit tests for correlation middleware
6. Write integration tests for error flow
7. Deploy to dev environment
8. Verify no performance regressions (< 1ms overhead)

**Acceptance Criteria**:
- All API requests have X-Request-ID in response
- All log entries include request_id field
- Error metric increments on exceptions
- Tests pass (unit + integration)

### Phase 2: Database Observability (Week 2)

**Goals**: Add postgres_exporter, enable query correlation

**Tasks**:
1. Create database migration for `exporter_user` role
2. Add postgres-exporter service to `docker-compose.prod.yml`
3. Configure Prometheus to scrape exporter (port 9187)
4. Add SQLAlchemy event listener for query comments
5. Test query comment injection in development
6. Create database performance dashboard JSON
7. Deploy to staging environment
8. Verify exporter metrics appear in Prometheus

**Acceptance Criteria**:
- postgres_exporter running and scraped by Prometheus
- pg_stat_statements contains query comments with request_id
- Database dashboard displays connection pool metrics
- No database performance impact (< 1% overhead)

### Phase 3: Dashboards & Alerts (Week 3)

**Goals**: Build operational dashboards, configure alerts

**Tasks**:
1. Create error tracking dashboard JSON
2. Create Celery deep-dive dashboard JSON
3. Create Golden Signals overview dashboard JSON
4. Add alert rules to `monitoring/alerts.yml`
5. Configure AlertManager notification channels (Slack/email)
6. Test alert firing manually (trigger conditions)
7. Verify alert notifications received
8. Document runbooks for each alert

**Acceptance Criteria**:
- 4 new Grafana dashboards imported
- 5 new AlertManager rules defined
- Alerts fire correctly when thresholds exceeded
- Runbooks documented in `docs/runbooks/`

### Phase 4: Production Rollout (Week 4)

**Goals**: Deploy to production, monitor, iterate

**Tasks**:
1. Deploy Phase C changes to production
2. Monitor error rates and dashboard usage for 48 hours
3. Enable alerts gradually (warning alerts first, then critical)
4. Collect team feedback on dashboards
5. Iterate on alert thresholds based on false positives
6. Document correlation ID debugging workflow
7. Train team on new dashboards
8. Retrospective: What worked? What needs improvement?

**Acceptance Criteria**:
- Production deployment successful, no regressions
- MTTD < 5 minutes verified via synthetic incident
- MTTR reduced by 50% compared to pre-Phase-C baseline
- False positive rate < 5%
- Team using dashboards daily

## Testing Strategy

### Unit Tests

**Correlation Middleware** (`tests/middleware/test_correlation.py`):
- Test UUID generation when X-Request-ID header missing
- Test header extraction when X-Request-ID present
- Test propagation to response headers
- Test injection into logging context
- Test error handling (middleware shouldn't fail requests)

**Error Handler** (`tests/test_error_handler.py`):
- Test error metric incremented on exception
- Test structured log entry created
- Test request_id included in error response
- Test different exception types

### Integration Tests

**End-to-End Correlation** (`tests/integration/test_correlation_flow.py`):
```python
async def test_api_to_celery_correlation():
    # 1. Make API request
    response = await client.post("/api/v1/repositories/1/sync")
    request_id = response.headers["X-Request-ID"]

    # 2. Verify log entry has request_id
    log_entry = await get_log_by_request_id(request_id)
    assert log_entry["request_id"] == request_id

    # 3. Verify Celery task inherited request_id
    task = await get_celery_task_by_request_id(request_id)
    assert task.request.headers["request_id"] == request_id

    # 4. Verify database query has comment
    slow_query = await get_slow_query_by_request_id(request_id)
    assert f"/* request_id: {request_id} */" in slow_query
```

**Error Flow** (`tests/integration/test_error_tracking.py`):
```python
async def test_error_tracked_end_to_end():
    # 1. Trigger error
    response = await client.get("/api/v1/trigger-error")
    request_id = response.json()["request_id"]

    # 2. Verify metric incremented
    metrics = await get_prometheus_metrics()
    assert metrics["commandcenter_errors_total"] > 0

    # 3. Verify log entry with stack trace
    log_entry = await get_log_by_request_id(request_id)
    assert "Traceback" in log_entry["message"]
```

### Load Tests

**Middleware Performance** (`tests/performance/test_middleware_overhead.py`):
```python
async def test_correlation_middleware_overhead():
    # Measure baseline latency without middleware
    baseline = await measure_latency(endpoint="/health", iterations=1000)

    # Measure latency with middleware
    with_middleware = await measure_latency(endpoint="/health", iterations=1000)

    # Assert overhead < 1ms
    overhead = with_middleware - baseline
    assert overhead < 0.001  # 1ms
```

**postgres_exporter Impact** (`tests/performance/test_exporter_impact.py`):
```python
async def test_exporter_db_overhead():
    # Measure database CPU/memory before exporter
    baseline_cpu = await get_db_cpu_usage()
    baseline_mem = await get_db_memory_usage()

    # Enable exporter, run for 5 minutes
    await enable_postgres_exporter()
    await asyncio.sleep(300)

    # Measure database CPU/memory with exporter
    with_exporter_cpu = await get_db_cpu_usage()
    with_exporter_mem = await get_db_memory_usage()

    # Assert overhead < 1%
    assert (with_exporter_cpu - baseline_cpu) / baseline_cpu < 0.01
    assert (with_exporter_mem - baseline_mem) / baseline_mem < 0.01
```

### Manual Testing

**Dashboard Validation**:
1. Error Dashboard:
   - Trigger 500 error → verify appears in dashboard within 30s
   - Click error → verify Loki logs displayed with stack trace
   - Search by request_id → verify filters correctly

2. Database Dashboard:
   - Run slow query → verify appears in "Top 10 Slowest Queries"
   - Open many connections → verify "Active Connections" gauge increases
   - Check connection pool saturation → verify < 90% under normal load

3. Celery Dashboard:
   - Trigger background job → verify task count increases
   - Simulate task failure → verify failure rate panel updates
   - Check queue depth → verify increases when workers stopped

4. Golden Signals:
   - Load test API → verify traffic panel shows increased RPS
   - Trigger errors → verify error rate % increases
   - Check latency heatmap → verify P95 < 1s under normal load

## Trade-offs & Alternatives

### Error Tracking: Self-Hosted vs Sentry Cloud

**Decision**: Self-hosted using Loki + Prometheus

**Rationale**:
- No external dependencies or recurring costs
- Full data control (compliance/privacy)
- Builds on existing infrastructure (no new services)
- Team already familiar with Grafana

**Trade-offs**:
- Manual error grouping (vs automatic in Sentry)
- Basic deduplication (vs intelligent in Sentry)
- Requires Grafana/Loki skills (vs Sentry's polished UI)
- Missing features: release tracking, source maps, user feedback

**Considered Alternatives**:
1. **Sentry Cloud** (~$26/mo): Rejected due to cost + external dependency
2. **Self-hosted Sentry** (~6 containers, 4GB RAM): Rejected due to operational overhead
3. **GlitchTip** (Sentry-compatible): Rejected due to missing features vs enhanced logging approach

**Future Consideration**: If error volume exceeds 10k/day or team needs advanced features (source maps, user feedback), revisit Sentry Cloud.

### Distributed Tracing: Now vs Later

**Decision**: Defer OpenTelemetry to Phase D

**Rationale**:
- Correlation IDs provide 80% of tracing value with 20% effort
- OTEL requires instrumenting entire stack (FastAPI, Celery, SQLAlchemy, Redis)
- Backend infrastructure (Jaeger/Tempo) adds operational overhead
- Incremental approach: Prove value with correlation IDs first

**Phase C Foundation**:
- Correlation ID middleware establishes pattern
- request_id propagation matches OTEL trace context concept
- Easy migration: request_id → trace_id + span_id in Phase D

### Dashboard Strategy: Pre-built vs Custom

**Decision**: Pre-built JSON dashboards in git

**Rationale**:
- Version controlled (track changes, roll back)
- Reproducible across environments (dev, staging, prod)
- Team can iterate via PR reviews
- Grafana provisioning auto-imports on startup

**Trade-offs**:
- Less flexible than editing in Grafana UI
- Requires JSON editing skills
- Dashboard changes need container restart

**Mitigation**: Document dashboard editing workflow in `docs/dashboards.md`

## Deferred to Future Phases

### Phase D: Distributed Tracing

**Scope**:
- OpenTelemetry SDK integration (Python + JavaScript)
- Jaeger or Tempo backend (self-hosted)
- Automatic instrumentation for FastAPI, Celery, SQLAlchemy, Redis
- Trace visualization UI
- Span-level metrics (latency, error rates per span)

**Why Defer**:
- Correlation IDs provide sufficient debugging capability for Phase C
- OTEL adds complexity (instrumentation, backend infrastructure)
- Want to validate Phase C patterns before committing to OTEL

### Phase E: Advanced Analytics

**Scope**:
- Business metrics (user actions, feature usage, conversion funnels)
- SLO/SLI tracking (99.9% uptime, < 500ms P95 latency)
- Cost attribution (API costs per endpoint/user)
- Performance regression detection
- Anomaly detection (ML-based alerting)

**Why Defer**:
- Requires stable observability foundation (Phase C provides this)
- Business metrics need product clarity
- Advanced analytics tools (PromQL, LogQL) require team upskilling

### hub-prototype Integration

**Scope**:
- Extract event streaming pattern from hub-prototype
- Unified NATS event bus for cross-service events
- Federation: hub-prototype observing multiple CommandCenter instances
- Correlation across hub → CommandCenter instance boundary

**Why Defer**:
- hub-prototype still in development (Phases 4-6 not integrated)
- Main CommandCenter needs solid observability foundation first
- Federation is advanced use case (multi-instance deployments)

## Risks & Mitigations

### Risk: Middleware Performance Overhead

**Probability**: Low
**Impact**: High (would affect all requests)

**Mitigation**:
- Lightweight UUID generation (< 1ms)
- Load testing before production deployment
- Feature flag to disable middleware if issues arise
- Monitoring: Track P95 latency before/after Phase C

### Risk: postgres_exporter Database Impact

**Probability**: Medium
**Impact**: Medium (could slow queries)

**Mitigation**:
- Read-only user with minimal privileges
- Exporter polls every 15s (not real-time)
- Performance testing: Measure DB CPU/memory before/after
- Can disable exporter if performance degrades

### Risk: Alert Fatigue (False Positives)

**Probability**: High (common with new alerts)
**Impact**: Medium (team ignores real alerts)

**Mitigation**:
- Start with warning alerts, tune thresholds before enabling critical
- Monitor false positive rate (target < 5%)
- Iterate on thresholds based on 48-hour production observation
- Document alert tuning process in runbooks

### Risk: Dashboard Complexity (Low Adoption)

**Probability**: Medium
**Impact**: Medium (team doesn't use dashboards)

**Mitigation**:
- Design dashboards with team input (not in isolation)
- Focus on actionable insights (not vanity metrics)
- Training session on dashboard usage
- Feedback loop: Iterate based on team usage patterns

### Risk: Log Volume Explosion

**Probability**: Medium
**Impact**: Medium (Loki storage costs)

**Mitigation**:
- Structured logging with log levels (avoid DEBUG in production)
- Loki retention policy: 30 days (configurable)
- Log sampling for high-volume endpoints (future optimization)
- Monitor Loki disk usage, alert if > 80%

## Success Validation

### Week 1 (Post-Deployment)

**Metrics to Track**:
- Middleware latency overhead (should be < 1ms)
- Error metric accuracy (compare to log count)
- Dashboard load times (should be < 3s)
- Alert false positive rate

**Validation**:
- Trigger synthetic error → appears in dashboard within 30s
- Check correlation: API log → Celery task log (request_id matches)
- Load test: Verify no latency regression

### Week 4 (Full Rollout)

**Metrics to Track**:
- MTTD: Mean-time-to-detection for critical errors
- MTTR: Mean-time-to-resolution for incidents
- Dashboard usage: Unique users per day
- Alert actionability: % of alerts leading to bug fixes

**Validation**:
- MTTD < 5 minutes (vs pre-Phase-C baseline)
- MTTR reduced by 50% (correlation IDs speed debugging)
- Team using dashboards daily (> 80% of engineers)
- False positive rate < 5%

### Month 3 (Long-term)

**Metrics to Track**:
- Production incident reduction (fewer user-reported issues)
- Performance optimization wins (slow queries fixed via dashboards)
- Developer satisfaction (survey: observability tools usefulness)

**Validation**:
- 30% reduction in production incidents
- 5+ performance optimizations driven by observability data
- Developer satisfaction score > 8/10

## References

### Related Documents

- `docs/CURRENT_SESSION.md` - Session notes
- `docs/PROJECT.md` - Overall project status
- `monitoring/prometheus.yml` - Prometheus configuration
- `monitoring/alerts.yml` - AlertManager rules
- `monitoring/grafana/dashboards/` - Dashboard JSON files
- `backend/app/utils/logging.py` - Logging utilities
- `backend/app/utils/metrics.py` - Metrics definitions

### External Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboard Design](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
- [postgres_exporter Documentation](https://github.com/prometheus-community/postgres_exporter)
- [FastAPI Middleware Guide](https://fastapi.tiangolo.com/advanced/middleware/)
- [OpenTelemetry Correlation Context](https://opentelemetry.io/docs/concepts/context-propagation/) (for Phase D)

### Key Files for Implementation

**Main CommandCenter**:
- `/backend/app/middleware/correlation.py` (NEW)
- `/backend/app/main.py` (ENHANCE: exception handler, middleware registration)
- `/backend/app/utils/metrics.py` (ENHANCE: add error_counter)
- `/backend/app/tasks/__init__.py` (ENHANCE: correlation inheritance)
- `/backend/app/db/session.py` (ENHANCE: query comments)
- `/docker-compose.prod.yml` (ENHANCE: add postgres-exporter)
- `/monitoring/grafana/dashboards/*.json` (NEW: 4 dashboards)
- `/monitoring/alerts.yml` (ENHANCE: add Phase C rules)

**hub-prototype** (reference patterns):
- `/hub-prototype/src/hub/mockBus.ts` (correlation ID pattern)
- `/hub-prototype/schemas/event.schema.json` (event structure)

---

## Phase 5: Worktree Setup

### Overview

Phase C implementation will be done in an isolated git worktree to avoid disrupting the main development branch during the 4-week rollout. This approach allows parallel development of other features while Phase C progresses through testing and iteration.

### Worktree Structure

```
CommandCenter/
├── .git/                           # Main git directory
├── backend/                        # Main worktree (current work)
├── frontend/
├── ...
└── worktree/
    └── phase-c-observability/      # Phase C isolated worktree
        ├── backend/
        ├── frontend/
        ├── monitoring/
        └── docs/
```

### Setup Commands

```bash
# Create isolated worktree from main
git worktree add worktree/phase-c-observability -b phase-c-observability

# Switch to worktree
cd worktree/phase-c-observability

# Verify isolation
git branch
# * phase-c-observability

# Copy environment configuration
cp ../../.env .env
# Update COMPOSE_PROJECT_NAME to avoid conflicts
sed -i 's/commandcenter/commandcenter-phase-c/g' .env

# Start services with unique project name
docker-compose -p commandcenter-phase-c up -d

# Verify services running on different ports
docker ps | grep phase-c
```

### Port Allocation

To avoid conflicts with main development environment:

| Service | Main | Phase C Worktree |
|---------|------|------------------|
| Backend | 8000 | 8100 |
| Frontend | 3000 | 3100 |
| PostgreSQL | 5432 | 5532 |
| Redis | 6379 | 6479 |
| Prometheus | 9090 | 9190 |
| Grafana | 3001 | 3101 |
| postgres-exporter | 9187 | 9287 |

**Phase C .env additions**:
```bash
# Update these in worktree/.env
BACKEND_PORT=8100
FRONTEND_PORT=3100
POSTGRES_PORT=5532
REDIS_PORT=6479
PROMETHEUS_PORT=9190
GRAFANA_PORT=3101
POSTGRES_EXPORTER_PORT=9287
EXPORTER_PASSWORD=<generate-unique-password>
```

### Benefits of Worktree Approach

1. **Isolation**: Main branch remains stable during Phase C development
2. **Parallel Work**: Other features can be developed on main simultaneously
3. **Safe Testing**: Load tests and performance validation don't impact main
4. **Easy Comparison**: Compare Phase C metrics against main baseline
5. **Clean Merge**: Review all changes in single PR when ready

### Development Workflow

```bash
# Day-to-day development in worktree
cd worktree/phase-c-observability

# Make changes
# Run tests
make test

# Commit to phase-c-observability branch
git add .
git commit -m "feat: add correlation ID middleware"

# Push to remote
git push -u origin phase-c-observability

# When complete, create PR
gh pr create --title "Phase C: Observability Layer" \
  --body-file docs/plans/2025-11-01-phase-c-observability-design.md \
  --base main --head phase-c-observability
```

### Cleanup After Merge

```bash
# After PR merged to main
cd ../..  # Return to main repo root

# Remove worktree
git worktree remove worktree/phase-c-observability

# Delete branch (if desired)
git branch -d phase-c-observability

# Stop Phase C containers
docker-compose -p commandcenter-phase-c down -v
```

---

## Phase 6: Detailed Implementation Plan

### Overview

This section provides bite-sized, actionable tasks for implementing Phase C. Each task is designed to be completable in 1-4 hours and includes acceptance criteria.

### Week 1: Foundation (Correlation & Error Tracking)

#### Task 1.1: Create Correlation ID Middleware

**File**: `backend/app/middleware/correlation.py`

**Steps**:
1. Create `backend/app/middleware/` directory if not exists
2. Implement `CorrelationIDMiddleware` class (see Architecture section for code)
3. Add docstrings and type hints
4. Handle edge cases (missing headers, malformed UUIDs)

**Acceptance Criteria**:
- File exists at correct path
- Class inherits from `BaseHTTPMiddleware`
- Generates UUID if `X-Request-ID` header missing
- Extracts existing `X-Request-ID` if present
- Stores in `request.state.request_id`
- Adds to response headers
- Performance: < 0.5ms overhead per request

**Verification**:
```bash
# Start server
make dev

# Test header extraction
curl -H "X-Request-ID: test123" http://localhost:8100/health
# Response should include: X-Request-ID: test123

# Test UUID generation
curl http://localhost:8100/health
# Response should include: X-Request-ID: <valid-uuid>
```

#### Task 1.2: Register Middleware in FastAPI

**File**: `backend/app/main.py`

**Steps**:
1. Import `CorrelationIDMiddleware`
2. Add middleware registration after app initialization
3. Ensure order: Correlation middleware → CORS → other middleware
4. Verify middleware active in startup logs

**Code Addition**:
```python
from app.middleware.correlation import CorrelationIDMiddleware

# After app = FastAPI()
app.add_middleware(CorrelationIDMiddleware)
```

**Acceptance Criteria**:
- Import statement added
- Middleware registered before route definitions
- No import errors on server start
- All requests receive `X-Request-ID` header

**Verification**:
```bash
# Check logs show middleware registered
docker-compose -p commandcenter-phase-c logs backend | grep -i correlation

# Test multiple endpoints
for endpoint in /health /api/v1/repositories /api/v1/technologies; do
  curl -I http://localhost:8100$endpoint | grep X-Request-ID
done
```

#### Task 1.3: Add Error Counter Metric

**File**: `backend/app/utils/metrics.py`

**Steps**:
1. Open existing `metrics.py`
2. Add `error_counter` Prometheus Counter with labels
3. Export in module `__all__`
4. Add docstring explaining metric purpose

**Code Addition**:
```python
from prometheus_client import Counter

error_counter = Counter(
    'commandcenter_errors_total',
    'Total errors by endpoint and type',
    ['endpoint', 'status_code', 'error_type']
)

__all__ = [..., 'error_counter']
```

**Acceptance Criteria**:
- Metric defined with correct name and labels
- Counter (not Gauge or Histogram)
- Exported in `__all__`
- No syntax errors

**Verification**:
```bash
# Check metric registered
curl http://localhost:8100/metrics | grep commandcenter_errors_total
# Should show metric with help text
```

#### Task 1.4: Enhance Global Exception Handler

**File**: `backend/app/main.py`

**Steps**:
1. Locate existing `@app.exception_handler(Exception)`
2. Import `error_counter` from `app.utils.metrics`
3. Extract `request_id` from `request.state`
4. Increment `error_counter` with labels
5. Enhance log entry with structured fields
6. Include `request_id` in error response JSON

**Code Changes** (see Architecture section for complete code)

**Acceptance Criteria**:
- Exception handler increments `error_counter`
- Log entry includes: request_id, endpoint, method, error_type, user_id
- Error response includes `request_id` field
- Stack trace logged (exc_info=True)

**Verification**:
```bash
# Trigger error endpoint (create test endpoint if needed)
curl http://localhost:8100/api/v1/trigger-test-error

# Check metric incremented
curl http://localhost:8100/metrics | grep commandcenter_errors_total
# Should show count > 0

# Check logs
docker-compose -p commandcenter-phase-c logs backend | tail -20
# Should show structured log with request_id
```

#### Task 1.5: Write Unit Tests for Middleware

**File**: `backend/tests/middleware/test_correlation.py`

**Steps**:
1. Create `tests/middleware/` directory
2. Write test cases:
   - `test_generates_uuid_when_header_missing()`
   - `test_extracts_existing_request_id()`
   - `test_adds_request_id_to_response_headers()`
   - `test_stores_request_id_in_request_state()`
   - `test_middleware_doesnt_fail_on_error()`

**Example Test**:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_generates_uuid_when_header_missing():
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # UUID length

def test_extracts_existing_request_id():
    response = client.get("/health", headers={"X-Request-ID": "test123"})
    assert response.headers["X-Request-ID"] == "test123"
```

**Acceptance Criteria**:
- All 5 test cases pass
- Tests use TestClient (not manual HTTP calls)
- Tests are independent (no shared state)
- Coverage > 90% for middleware module

**Verification**:
```bash
pytest backend/tests/middleware/test_correlation.py -v
# All tests should pass
```

#### Task 1.6: Write Integration Tests for Error Flow

**File**: `backend/tests/integration/test_error_tracking.py`

**Steps**:
1. Create test endpoint that raises exception
2. Write test that triggers error and verifies:
   - Metric incremented
   - Log entry created with request_id
   - Error response includes request_id

**Example Test**:
```python
async def test_error_tracked_end_to_end():
    # Trigger error
    response = await async_client.get("/api/v1/trigger-test-error")

    # Verify response includes request_id
    assert "request_id" in response.json()
    request_id = response.json()["request_id"]

    # Verify metric incremented (query Prometheus)
    metrics = await get_prometheus_metrics()
    assert metrics["commandcenter_errors_total"] > 0
```

**Acceptance Criteria**:
- Test creates real error (not mocked)
- Verifies metric increment
- Verifies structured logging
- Test is idempotent (can run multiple times)

**Verification**:
```bash
pytest backend/tests/integration/test_error_tracking.py -v
```

#### Task 1.7: Load Test Middleware Performance

**File**: `backend/tests/performance/test_middleware_overhead.py`

**Steps**:
1. Create performance test suite
2. Measure baseline latency (health endpoint, 1000 iterations)
3. Enable middleware
4. Measure with-middleware latency (same endpoint, 1000 iterations)
5. Assert overhead < 1ms

**Example Test** (see Architecture section for complete code)

**Acceptance Criteria**:
- Test runs 1000+ iterations for statistical significance
- Measures both baseline and with-middleware latency
- Asserts overhead < 1ms (P95 or average)
- Test passes consistently

**Verification**:
```bash
pytest backend/tests/performance/test_middleware_overhead.py -v
# Should report: "Middleware overhead: 0.3ms (acceptable)"
```

#### Task 1.8: Deploy to Dev Environment & Verify

**Steps**:
1. Ensure all tests pass: `make test`
2. Build containers: `docker-compose -p commandcenter-phase-c build`
3. Start services: `docker-compose -p commandcenter-phase-c up -d`
4. Check health: `make health`
5. Verify middleware active: `curl -I http://localhost:8100/health | grep X-Request-ID`
6. Verify metrics endpoint: `curl http://localhost:8100/metrics | grep commandcenter_errors_total`

**Acceptance Criteria**:
- All containers running
- Health checks pass
- All API responses include `X-Request-ID`
- Error metric visible in `/metrics`
- No performance regression (baseline latency check)

**Verification**:
```bash
# Run smoke tests
./scripts/smoke-test.sh

# Check logs for errors
docker-compose -p commandcenter-phase-c logs | grep -i error
```

---

### Week 2: Database Observability

#### Task 2.1: Create Database Migration for Exporter User

**File**: `backend/alembic/versions/XXXX_add_exporter_user.py`

**Steps**:
1. Generate migration: `alembic revision -m "add exporter user for postgres_exporter"`
2. Implement `upgrade()`:
   - Create `exporter_user` role
   - Grant `CONNECT` on database
   - Grant `pg_monitor` role
3. Implement `downgrade()`:
   - Revoke grants
   - Drop `exporter_user` role

**Migration Code**:
```python
from alembic import op

def upgrade():
    op.execute("""
        CREATE USER exporter_user WITH PASSWORD 'EXPORTER_PASSWORD_PLACEHOLDER';
        GRANT CONNECT ON DATABASE commandcenter TO exporter_user;
        GRANT pg_monitor TO exporter_user;
    """)

def downgrade():
    op.execute("""
        REVOKE pg_monitor FROM exporter_user;
        REVOKE CONNECT ON DATABASE commandcenter FROM exporter_user;
        DROP USER exporter_user;
    """)
```

**Acceptance Criteria**:
- Migration file created
- Both upgrade and downgrade implemented
- Password uses environment variable (not hardcoded)
- Migration applies cleanly: `alembic upgrade head`

**Verification**:
```bash
# Apply migration
docker-compose -p commandcenter-phase-c exec backend alembic upgrade head

# Check user created
docker-compose -p commandcenter-phase-c exec postgres psql -U commandcenter -d commandcenter \
  -c "\du exporter_user"
# Should show exporter_user role

# Test downgrade
docker-compose -p commandcenter-phase-c exec backend alembic downgrade -1
# User should be removed
```

#### Task 2.2: Add postgres-exporter Service to Docker Compose

**File**: `docker-compose.prod.yml`

**Steps**:
1. Add `postgres-exporter` service (see Architecture section for config)
2. Use `prometheuscommunity/postgres-exporter:latest` image
3. Set `DATA_SOURCE_NAME` environment variable with connection string
4. Expose port 9287 (Phase C worktree allocation)
5. Add `depends_on: postgres`

**Service Definition** (see Architecture section)

**Acceptance Criteria**:
- Service defined in docker-compose.prod.yml
- Port mapped correctly
- Connection string uses exporter_user
- Service starts successfully

**Verification**:
```bash
# Start exporter
docker-compose -p commandcenter-phase-c -f docker-compose.prod.yml up -d postgres-exporter

# Check health
curl http://localhost:9287/metrics | head -20
# Should show PostgreSQL metrics

# Check logs
docker-compose -p commandcenter-phase-c logs postgres-exporter
# Should show "Listening on :9187"
```

#### Task 2.3: Configure Prometheus to Scrape Exporter

**File**: `monitoring/prometheus.yml`

**Steps**:
1. Add postgres-exporter scrape job
2. Configure scrape interval: 15s
3. Set target: `postgres-exporter:9187`
4. Add labels: `job=postgres, instance=commandcenter-phase-c`

**Config Addition**:
```yaml
scrape_configs:
  # Existing jobs...

  - job_name: 'postgres'
    scrape_interval: 15s
    static_configs:
      - targets: ['postgres-exporter:9187']
        labels:
          instance: 'commandcenter-phase-c'
```

**Acceptance Criteria**:
- Scrape job added to prometheus.yml
- Valid YAML syntax
- Prometheus reloads config without errors
- Exporter metrics appear in Prometheus

**Verification**:
```bash
# Restart Prometheus
docker-compose -p commandcenter-phase-c restart prometheus

# Check Prometheus targets
curl http://localhost:9190/api/v1/targets | jq '.data.activeTargets[] | select(.job=="postgres")'
# Should show postgres-exporter target as "up"

# Query metric
curl 'http://localhost:9190/api/v1/query?query=pg_stat_database_numbackends' | jq
# Should return PostgreSQL connection metrics
```

#### Task 2.4: Add SQLAlchemy Event Listener for Query Comments

**File**: `backend/app/db/session.py`

**Steps**:
1. Import SQLAlchemy event
2. Implement `before_cursor_execute` listener
3. Extract `request_id` from connection context
4. Prepend SQL comment: `/* request_id: xyz */`
5. Register listener on Engine

**Code Addition** (see Architecture section for complete code)

**Acceptance Criteria**:
- Event listener registered
- Comments added to all queries
- request_id extracted from context
- No performance impact (< 0.1ms per query)

**Verification**:
```bash
# Enable pg_stat_statements in PostgreSQL
docker-compose -p commandcenter-phase-c exec postgres psql -U commandcenter -d commandcenter \
  -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

# Make API request
curl -H "X-Request-ID: test123" http://localhost:8100/api/v1/repositories

# Check pg_stat_statements for comment
docker-compose -p commandcenter-phase-c exec postgres psql -U commandcenter -d commandcenter \
  -c "SELECT query FROM pg_stat_statements WHERE query LIKE '%request_id: test123%' LIMIT 5;"
# Should show queries with /* request_id: test123 */ comments
```

#### Task 2.5: Create Database Performance Dashboard

**File**: `monitoring/grafana/dashboards/database-performance.json`

**Steps**:
1. Create dashboard JSON with 6 panels:
   - Active Connections (gauge + graph)
   - Query Duration Percentiles (heatmap)
   - Top 10 Slowest Queries (table)
   - Connection Pool Saturation (%)
   - Table Sizes (bar chart)
   - Index Usage (table)
2. Use postgres_exporter metrics
3. Add variables: time range, database name
4. Set refresh interval: 30s

**Key Panels**:

**Active Connections**:
```json
{
  "targets": [{
    "expr": "pg_stat_database_numbackends{datname='commandcenter'}"
  }],
  "title": "Active Connections"
}
```

**Query Duration P95**:
```json
{
  "targets": [{
    "expr": "histogram_quantile(0.95, rate(pg_stat_statements_mean_time_bucket[5m]))"
  }],
  "title": "Query Duration P95"
}
```

**Acceptance Criteria**:
- Dashboard JSON valid (import into Grafana without errors)
- All 6 panels display data
- Variables work (time range selection)
- Dashboard loads in < 3s

**Verification**:
```bash
# Import dashboard
curl -X POST http://admin:admin@localhost:3101/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/dashboards/database-performance.json

# Open in browser
open http://localhost:3101/d/database-performance
# Verify all panels show data
```

#### Task 2.6: Test Query Comment Injection

**File**: `backend/tests/integration/test_query_comments.py`

**Steps**:
1. Create test that makes API request with known request_id
2. Query pg_stat_statements for comment
3. Assert comment contains request_id

**Example Test**:
```python
async def test_query_comments_include_request_id():
    request_id = "test-query-comment-123"

    # Make API request
    await async_client.get("/api/v1/repositories", headers={"X-Request-ID": request_id})

    # Query pg_stat_statements
    result = await db.execute(
        text("SELECT query FROM pg_stat_statements WHERE query LIKE :pattern"),
        {"pattern": f"%request_id: {request_id}%"}
    )
    queries = result.fetchall()

    # Assert at least one query has comment
    assert len(queries) > 0
    assert request_id in queries[0]['query']
```

**Acceptance Criteria**:
- Test creates real database queries
- Verifies comment appears in pg_stat_statements
- Test is deterministic (no race conditions)

**Verification**:
```bash
pytest backend/tests/integration/test_query_comments.py -v
```

#### Task 2.7: Deploy to Staging & Verify

**Steps**:
1. Ensure all Week 2 tests pass
2. Apply database migration: `alembic upgrade head`
3. Start postgres-exporter: `docker-compose up -d postgres-exporter`
4. Verify exporter metrics in Prometheus
5. Import database dashboard into Grafana
6. Load test: Run 1000 queries, verify comment overhead < 1%

**Acceptance Criteria**:
- postgres-exporter running and scraped by Prometheus
- Database dashboard shows real data
- Query comments visible in pg_stat_statements
- No performance regression

**Verification**:
```bash
# Load test
./scripts/load-test.sh --duration 60s --rps 100

# Check performance overhead
# Compare query latency before/after comment injection
```

---

### Week 3: Dashboards & Alerts

#### Task 3.1: Create Error Tracking Dashboard

**File**: `monitoring/grafana/dashboards/error-tracking.json`

**Panels**:
1. Error Rate Over Time (line chart)
2. Errors by Endpoint (bar chart)
3. Error Type Distribution (pie chart)
4. Recent Errors (table from Loki)
5. Request ID Lookup (input → filter logs)

**Example Panel - Error Rate**:
```json
{
  "targets": [{
    "expr": "rate(commandcenter_errors_total[5m])"
  }],
  "title": "Error Rate (per second)"
}
```

**Acceptance Criteria**:
- All 5 panels defined
- Error data displayed correctly
- Request ID lookup filters Loki logs
- Dashboard loads quickly (< 3s)

**Verification**: Import and verify visually

#### Task 3.2: Create Celery Deep-Dive Dashboard

**File**: `monitoring/grafana/dashboards/celery-deep-dive.json`

**Panels**:
1. Tasks Executed per Minute (line chart)
2. Task Duration by Type (histogram)
3. Task Failure Rate (%)
4. Queue Depth Over Time
5. Worker Status (up/down indicators)

**Key Metric - Task Duration**:
```json
{
  "targets": [{
    "expr": "histogram_quantile(0.95, rate(celery_task_duration_seconds_bucket[5m]))"
  }],
  "title": "Task Duration P95"
}
```

**Acceptance Criteria**:
- All 5 panels defined
- Celery metrics displayed
- Worker status accurate

**Verification**: Trigger background jobs, verify dashboard updates

#### Task 3.3: Create Golden Signals Dashboard

**File**: `monitoring/grafana/dashboards/golden-signals.json`

**Panels** (Google SRE's Four Golden Signals):
1. Latency: Request duration P50/P95/P99
2. Traffic: Requests per second by endpoint
3. Errors: Error rate (%)
4. Saturation: CPU, memory, connection pools

**Example - Latency**:
```json
{
  "targets": [
    {"expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))", "legendFormat": "P50"},
    {"expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))", "legendFormat": "P95"},
    {"expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))", "legendFormat": "P99"}
  ],
  "title": "API Latency"
}
```

**Acceptance Criteria**:
- All 4 golden signals represented
- Actionable insights (not vanity metrics)
- Dashboard useful for on-call engineers

**Verification**: Use during simulated incident

#### Task 3.4: Add Alert Rules to alerts.yml

**File**: `monitoring/alerts.yml`

**Steps**:
1. Add Phase C alert group
2. Implement 5 rules (see Architecture section):
   - HighErrorRate (> 5% for 5 minutes)
   - DatabasePoolExhausted (> 90% for 2 minutes)
   - SlowAPIResponses (P95 > 1s for 5 minutes)
   - CeleryWorkerDown (< 1 worker for 1 minute)
   - DiskSpaceLow (< 10% for 5 minutes)
3. Set appropriate severities (critical/warning)
4. Add descriptive annotations

**Example Rule** (see Architecture section for complete rules)

**Acceptance Criteria**:
- All 5 rules defined
- Valid PromQL expressions
- Appropriate thresholds and durations
- Descriptive annotations

**Verification**:
```bash
# Validate alerts.yml syntax
promtool check rules monitoring/alerts.yml

# Reload AlertManager
docker-compose -p commandcenter-phase-c restart alertmanager

# Check rules loaded
curl http://localhost:9093/api/v1/rules | jq '.data.groups[] | select(.name=="phase_c_alerts")'
```

#### Task 3.5: Configure AlertManager Notification Channels

**File**: `monitoring/alertmanager.yml`

**Steps**:
1. Add Slack receiver (if Slack webhook available)
2. Add email receiver (if SMTP configured)
3. Configure routing: critical → Slack, warning → email
4. Set grouping: by alert name
5. Configure repeat interval: 4 hours

**Config Example**:
```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'SLACK_WEBHOOK_URL'
        channel: '#commandcenter-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

route:
  receiver: 'slack'
  group_by: ['alertname']
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'slack'
    - match:
        severity: warning
      receiver: 'email'
```

**Acceptance Criteria**:
- Notification channels configured
- Routing rules defined
- Test alert sent successfully

**Verification**:
```bash
# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts -d '[{
  "labels": {"alertname": "TestAlert", "severity": "critical"},
  "annotations": {"description": "Test alert from Phase C setup"}
}]'

# Check Slack/email received
```

#### Task 3.6: Test Alert Firing Manually

**Steps**:
1. Trigger HighErrorRate: Send 100 error requests
2. Trigger DatabasePoolExhausted: Open 90% of connections
3. Trigger SlowAPIResponses: Inject artificial delay
4. Trigger CeleryWorkerDown: Stop Celery container
5. Verify alerts fire within expected timeframes

**Test Script**:
```bash
#!/bin/bash
# test-alerts.sh

# Test HighErrorRate
for i in {1..100}; do
  curl http://localhost:8100/api/v1/trigger-test-error
done

# Wait 5 minutes
sleep 300

# Check if alert fired
curl http://localhost:9093/api/v1/alerts | jq '.data[] | select(.labels.alertname=="HighErrorRate")'
```

**Acceptance Criteria**:
- All 5 alerts can be triggered manually
- Alerts fire within expected duration (for=X)
- Alerts resolve when condition clears
- Notifications sent to configured channels

**Verification**: Run test script, verify alerts in AlertManager UI

#### Task 3.7: Document Runbooks for Each Alert

**File**: `docs/runbooks/phase-c-alerts.md`

**Structure**:
For each alert, document:
1. **Alert Name**
2. **Description**: What condition triggered it
3. **Impact**: What's broken for users
4. **Investigation Steps**: How to diagnose root cause
5. **Resolution Steps**: How to fix
6. **Escalation**: When to escalate

**Example Runbook**:
```markdown
## HighErrorRate

**Description**: Error rate > 5% for 5 minutes

**Impact**: Users experiencing high failure rate for API requests

**Investigation**:
1. Open Error Tracking dashboard
2. Identify which endpoint(s) have errors
3. Click spike → view Loki logs
4. Extract request_id from error log
5. Search all logs for that request_id
6. Check Database dashboard for slow queries

**Resolution**:
1. If slow query: Optimize query or add index
2. If external service down: Enable circuit breaker
3. If bug: Hotfix and deploy
4. If spike: Scale up backend containers

**Escalation**: If unresolved after 30 minutes, escalate to on-call engineer
```

**Acceptance Criteria**:
- Runbook for all 5 alerts
- Clear investigation steps
- Actionable resolution steps
- Escalation criteria defined

**Verification**: Review with team for clarity

---

### Week 4: Production Rollout

#### Task 4.1: Deploy Phase C to Production

**Steps**:
1. Merge `phase-c-observability` branch to `main`
2. Update production `.env` with Phase C variables
3. Apply database migrations: `alembic upgrade head`
4. Build containers: `docker-compose -f docker-compose.prod.yml build`
5. Start services: `docker-compose -f docker-compose.prod.yml up -d`
6. Verify health: `make health`
7. Import Grafana dashboards
8. Reload AlertManager rules

**Deployment Checklist**:
- [ ] All tests pass in CI/CD
- [ ] Staging validation complete
- [ ] Database migration tested
- [ ] Rollback plan documented
- [ ] Team notified of deployment
- [ ] Monitoring dashboard open during deployment

**Acceptance Criteria**:
- Production deployment successful
- No errors in logs
- All health checks pass
- Dashboards displaying data

**Verification**:
```bash
# Check all services healthy
curl https://commandcenter.yourcompany.com/health

# Verify correlation IDs in production
curl -I https://commandcenter.yourcompany.com/api/v1/repositories | grep X-Request-ID

# Check Prometheus targets
curl https://prometheus.yourcompany.com/api/v1/targets
```

#### Task 4.2: Monitor for 48 Hours

**Steps**:
1. Open all 4 dashboards in Grafana
2. Monitor error rates (should be stable)
3. Monitor database performance (no degradation)
4. Monitor middleware overhead (< 1ms confirmed)
5. Check for alerts (expect 0 false positives)
6. Collect team feedback on dashboards

**Monitoring Checklist**:
- [ ] Error rate stable (compare to pre-Phase-C)
- [ ] P95 latency stable (< 1ms increase)
- [ ] Database connection pool healthy (< 50% utilization)
- [ ] Celery tasks processing normally
- [ ] No unexpected alerts fired
- [ ] Dashboards loading quickly (< 3s)

**Acceptance Criteria**:
- No production incidents caused by Phase C
- Error tracking working (verify with synthetic error)
- Correlation IDs present in all logs

**Verification**: Daily check-ins with team

#### Task 4.3: Enable Alerts Gradually

**Steps**:
1. **Day 1**: Enable warning alerts only
   - DatabasePoolExhausted (warning)
   - SlowAPIResponses (warning)
   - DiskSpaceLow (warning)
2. **Day 2**: Tune thresholds based on false positives
3. **Day 3**: Enable critical alerts
   - HighErrorRate (critical)
   - CeleryWorkerDown (critical)
4. **Day 4**: Monitor alert actionability

**Tuning Process**:
- Track all alerts fired in spreadsheet
- For each alert: Was it actionable? (yes/no)
- If false positive: Adjust threshold or duration
- Target: < 5% false positive rate

**Acceptance Criteria**:
- All alerts enabled by Day 3
- False positive rate < 5%
- At least 1 real issue caught by alerts

**Verification**: Alert log analysis

#### Task 4.4: Collect Team Feedback on Dashboards

**Steps**:
1. Send survey to engineering team:
   - Which dashboards are most useful?
   - Which panels are confusing?
   - What's missing?
   - How often do you use them?
2. Hold 30-minute dashboard review session
3. Document requested changes
4. Prioritize improvements for iteration

**Survey Questions**:
1. How often do you use the dashboards? (daily/weekly/never)
2. Which dashboard is most useful for debugging? (multiple choice)
3. Which panels are confusing or unclear? (free text)
4. What metrics are missing that would help you? (free text)
5. Overall satisfaction: 1-10 scale

**Acceptance Criteria**:
- Survey responses from 80%+ of team
- At least 3 actionable improvement suggestions
- Overall satisfaction score > 7/10

**Verification**: Survey results doc

#### Task 4.5: Iterate on Alert Thresholds

**Steps**:
1. Review all alerts fired in first week
2. Calculate false positive rate per alert
3. For alerts with > 10% false positive:
   - Increase threshold OR
   - Increase duration OR
   - Add additional conditions
4. Update `monitoring/alerts.yml`
5. Deploy updated rules

**Example Iteration**:
```yaml
# Before
- alert: HighErrorRate
  expr: (rate(commandcenter_errors_total[5m]) / rate(http_requests_total[5m])) > 0.05
  for: 5m

# After (reduced false positives)
- alert: HighErrorRate
  expr: (rate(commandcenter_errors_total[5m]) / rate(http_requests_total[5m])) > 0.08
  for: 10m  # Increased duration
```

**Acceptance Criteria**:
- False positive rate < 5% for all alerts
- At least 2 alert thresholds tuned based on data
- Team agrees alerts are actionable

**Verification**: Week 2 alert log analysis

#### Task 4.6: Document Correlation ID Debugging Workflow

**File**: `docs/debugging-with-correlation-ids.md`

**Content**:
1. **Overview**: What are correlation IDs and why useful
2. **Finding a Request ID**: From error logs, dashboards, user reports
3. **Tracing a Request**: How to search Loki for all logs with ID
4. **Cross-System Correlation**: API → Celery → Database
5. **Dashboard Drill-Down**: Using Grafana to investigate
6. **Example Scenarios**: Real debugging examples

**Example Scenario**:
```markdown
### Scenario: User Reports Slow API Response

1. User provides timestamp: 2025-11-05 14:32:15
2. Open Golden Signals dashboard, zoom to that time
3. Identify spike in P95 latency on `/api/v1/repositories/{id}/sync`
4. Click spike → drill into Loki logs for that endpoint + timerange
5. Find log entry: "Slow query detected" with request_id: abc123
6. Search Loki: `{request_id="abc123"}` → see full request trace
7. Check Database dashboard: "Top 10 Slowest Queries" for request_id
8. Identify: Full table scan on `repositories` table
9. Resolution: Add index on frequently queried column
```

**Acceptance Criteria**:
- Document covers all use cases
- Includes screenshots of dashboards
- Step-by-step instructions clear
- Reviewed by at least 2 team members

**Verification**: Team walkthrough

#### Task 4.7: Train Team on New Dashboards

**Steps**:
1. Schedule 60-minute training session
2. **Demo 1**: Error Tracking Dashboard (15 min)
   - Trigger error, show in dashboard
   - Demonstrate request_id lookup
3. **Demo 2**: Database Performance Dashboard (15 min)
   - Show connection pool metrics
   - Explain slow query analysis
4. **Demo 3**: Debugging Workflow (20 min)
   - Walk through real incident
   - Show correlation across systems
5. **Q&A** (10 min)
6. Share recording and docs

**Training Materials**:
- Slide deck with dashboard screenshots
- Hands-on exercise: "Debug this synthetic error"
- Cheat sheet: Common PromQL/LogQL queries

**Acceptance Criteria**:
- Training session held with 80%+ attendance
- Recording shared in team channel
- At least 3 team members complete hands-on exercise
- Follow-up survey: > 8/10 usefulness rating

**Verification**: Attendance log + survey

#### Task 4.8: Retrospective & Documentation

**Steps**:
1. Hold Phase C retrospective meeting (60 min)
2. **Discuss**:
   - What went well?
   - What didn't go well?
   - What would we do differently?
   - What did we learn?
3. Document lessons learned
4. Update `docs/PROJECT.md` with Phase C completion
5. Plan Phase D (OpenTelemetry) kickoff

**Retrospective Format**:
- **Start**: What should we start doing?
- **Stop**: What should we stop doing?
- **Continue**: What should we continue doing?

**Documentation Updates**:
- Update PROJECT.md: Phase C status = Complete
- Create Phase C completion report
- Archive Phase C planning docs
- Update observability maturity score (60% → 85%)

**Acceptance Criteria**:
- Retrospective held with full team
- Lessons learned documented
- PROJECT.md updated
- Phase D planning scheduled

**Verification**: Meeting notes published

---

**Phase C Implementation Complete!** 🎉

**Next Phase**: Phase D - OpenTelemetry Distributed Tracing
