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

**Next Steps**: Proceed to Phase 5 (Worktree Setup) and Phase 6 (Implementation Plan).
