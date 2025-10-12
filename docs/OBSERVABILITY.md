# CommandCenter Observability Guide

## Overview

This document describes the observability features in CommandCenter, including health checks, logging, metrics, tracing, and alerting thresholds.

## Health Checks

### Endpoints

#### Basic Health Check
```
GET /health
```

Returns basic application status. Use for load balancer health checks.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "app": "Command Center",
  "version": "0.1.0"
}
```

#### Detailed Health Check
```
GET /health/detailed
```

Returns comprehensive health status for all system components.

**Response (200 OK - All healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-12T10:30:00Z",
  "response_time_ms": 125.5,
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.2,
      "pool_status": "Pool size: 5  Connections in pool: 3",
      "timestamp": "2025-10-12T10:30:00Z"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 8.3,
      "total_commands": 12450,
      "databases": 1,
      "timestamp": "2025-10-12T10:30:00Z"
    },
    "celery": {
      "status": "healthy",
      "response_time_ms": 45.1,
      "workers": 2,
      "active_tasks": 3,
      "registered_tasks": 15,
      "timestamp": "2025-10-12T10:30:00Z"
    }
  }
}
```

**Response (503 Service Unavailable - Component unhealthy):**
```json
{
  "status": "unhealthy",
  "timestamp": "2025-10-12T10:30:00Z",
  "response_time_ms": 2150.0,
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12.1,
      "pool_status": "Pool size: 5  Connections in pool: 4",
      "timestamp": "2025-10-12T10:30:00Z"
    },
    "redis": {
      "status": "unhealthy",
      "error": "Connection refused",
      "timestamp": "2025-10-12T10:30:00Z"
    },
    "celery": {
      "status": "unhealthy",
      "error": "No Celery workers available",
      "timestamp": "2025-10-12T10:30:00Z"
    }
  }
}
```

### Health Status Definitions

- **healthy**: Component is functioning normally
- **degraded**: Component has issues but system can still operate (e.g., Redis disabled)
- **unhealthy**: Component is down or not responding

## Structured Logging

### Configuration

Logging is configured via environment variables:

```bash
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=/app/logs/commandcenter.log  # Optional file output
JSON_LOGS=true              # Enable JSON format (recommended for production)
ENVIRONMENT=production      # Enables file logging if LOG_FILE is set
```

### JSON Log Format

```json
{
  "time": "2025-10-12T10:30:00.123456Z",
  "level": "INFO",
  "logger": "app.routers.batch",
  "module": "batch",
  "function": "analyze_repositories",
  "line": 145,
  "msg": "Batch analysis started",
  "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": 1,
  "duration": 0.523,
  "status_code": 200,
  "method": "POST",
  "path": "/api/v1/batch/analyze"
}
```

### Request Tracing

Every HTTP request is assigned a unique `request_id` (UUID) that appears in:
- All log entries for that request
- Response header: `X-Request-ID`

Use the request ID to trace a request through the entire system, including:
- API endpoint handling
- Database queries
- Celery task execution
- External API calls

**Example: Trace a failing request**
```bash
# Find the request ID from the error response header
curl -v http://localhost:8000/api/v1/batch/analyze

# Search logs for that request ID
docker-compose logs backend | grep "f47ac10b-58cc-4372-a567-0e02b2c3d479"
```

## Prometheus Metrics

### Metrics Endpoint

```
GET /metrics
```

Returns Prometheus-formatted metrics for scraping.

### Available Metrics

#### Application Metrics

- `commandcenter_app_info` - Application version and environment info
- `http_requests_total` - Total HTTP requests by method, path, status
- `http_request_duration_seconds` - HTTP request duration histogram
- `http_requests_inprogress` - Current in-progress HTTP requests

#### Database Metrics

- `commandcenter_db_connection_pool_size{state="idle|active|total"}` - Connection pool metrics

#### Repository Operations

- `commandcenter_repository_operations_total{operation, status}` - Repository operations counter
  - Operations: `create`, `sync`, `update`, `delete`
  - Status: `success`, `error`

#### Technology Operations

- `commandcenter_technology_operations_total{operation, status}` - Technology operations counter

#### Research Tasks

- `commandcenter_research_task_duration_seconds{task_type}` - Task duration histogram
- `commandcenter_active_research_tasks` - Current active tasks gauge

#### RAG Operations

- `commandcenter_rag_operations_total{operation, status}` - RAG operations counter
- `commandcenter_rag_query_duration_seconds` - Query duration histogram

#### Cache Operations

- `commandcenter_cache_operations_total{operation, result}` - Cache hits/misses
  - Operations: `get`, `set`, `delete`
  - Result: `hit`, `miss`

#### Batch Operations (New in Sprint 1.3)

- `commandcenter_batch_operations_total{operation_type, status}` - Batch operation counter
  - Operation types: `analyze`, `export`, `import`
  - Status: `success`, `error`

- `commandcenter_batch_operation_duration_seconds{operation_type}` - Operation duration histogram
  - Buckets: 1s, 5s, 10s, 30s, 60s, 120s, 300s, 600s, 1800s, 3600s

- `commandcenter_batch_items_processed_total{operation_type, status}` - Items processed counter

- `commandcenter_batch_active_jobs` - Currently active batch jobs gauge

#### Job Operations (New in Sprint 1.3)

- `commandcenter_job_operations_total{job_type, status}` - Job operation counter
  - Job types: `analysis`, `export`, `import`, `sync`, `webhook`, `scheduled`
  - Status: `success`, `error`

- `commandcenter_job_duration_seconds{job_type}` - Job execution duration histogram
  - Buckets: 1s, 5s, 10s, 30s, 60s, 120s, 300s, 600s, 1800s, 3600s, 7200s

- `commandcenter_job_queue_size{status}` - Jobs in queue by status
  - Status: `pending`, `running`, `completed`, `failed`

#### API Key Usage

- `commandcenter_api_key_usage_total{service, endpoint}` - External API usage counter

## Alerting Thresholds

### Critical Alerts (Immediate Action Required)

#### Health Check Failures
```yaml
# Component completely down
- alert: ComponentDown
  expr: up{job="commandcenter"} == 0
  for: 1m
  severity: critical
  description: "CommandCenter service is not responding"

# Database unavailable
- alert: DatabaseDown
  expr: commandcenter_db_health_status == 0
  for: 30s
  severity: critical
  description: "PostgreSQL database is unavailable"

# All Celery workers down
- alert: CeleryWorkersDown
  expr: commandcenter_celery_workers == 0
  for: 1m
  severity: critical
  description: "No Celery workers available for job processing"
```

#### Performance Degradation
```yaml
# HTTP response time > 5 seconds
- alert: SlowAPIResponses
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
  for: 3m
  severity: critical
  description: "95th percentile API response time > 5 seconds"

# Database query time > 2 seconds
- alert: SlowDatabaseQueries
  expr: histogram_quantile(0.95, rate(commandcenter_db_query_duration_seconds_bucket[5m])) > 2
  for: 3m
  severity: critical
  description: "95th percentile database query time > 2 seconds"
```

#### Resource Exhaustion
```yaml
# Database connection pool > 90% utilization
- alert: DatabasePoolExhaustion
  expr: commandcenter_db_connection_pool_size{state="active"} / commandcenter_db_connection_pool_size{state="total"} > 0.9
  for: 5m
  severity: critical
  description: "Database connection pool > 90% utilized"

# Job queue > 100 pending jobs
- alert: JobQueueBacklog
  expr: commandcenter_job_queue_size{status="pending"} > 100
  for: 10m
  severity: critical
  description: "Job queue has > 100 pending jobs"
```

### Warning Alerts (Investigation Recommended)

#### Performance
```yaml
# HTTP error rate > 5%
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 5m
  severity: warning
  description: "HTTP 5xx error rate > 5%"

# Batch operation failure rate > 10%
- alert: HighBatchFailureRate
  expr: rate(commandcenter_batch_operations_total{status="error"}[15m]) / rate(commandcenter_batch_operations_total[15m]) > 0.1
  for: 10m
  severity: warning
  description: "Batch operation failure rate > 10%"

# Cache miss rate > 50%
- alert: HighCacheMissRate
  expr: rate(commandcenter_cache_operations_total{result="miss"}[10m]) / rate(commandcenter_cache_operations_total[10m]) > 0.5
  for: 15m
  severity: warning
  description: "Cache miss rate > 50% - consider cache warming"
```

#### Resource Usage
```yaml
# Celery workers < 2
- alert: LowCeleryWorkers
  expr: commandcenter_celery_workers < 2
  for: 5m
  severity: warning
  description: "Only {value} Celery worker(s) available (recommend >= 2)"

# Active tasks per worker > 10
- alert: HighCeleryLoad
  expr: commandcenter_celery_active_tasks / commandcenter_celery_workers > 10
  for: 10m
  severity: warning
  description: "Celery workers are overloaded ({value} tasks/worker)"

# Job queue > 50 pending
- alert: JobQueueGrowing
  expr: commandcenter_job_queue_size{status="pending"} > 50
  for: 15m
  severity: warning
  description: "Job queue has {value} pending jobs - consider scaling"
```

#### Business Logic
```yaml
# No batch operations in 1 hour (if expected)
- alert: NoBatchOperations
  expr: rate(commandcenter_batch_operations_total[1h]) == 0
  for: 1h
  severity: warning
  description: "No batch operations executed in the last hour"

# High job failure rate
- alert: HighJobFailureRate
  expr: rate(commandcenter_job_operations_total{status="error"}[15m]) / rate(commandcenter_job_operations_total[15m]) > 0.2
  for: 10m
  severity: warning
  description: "Job failure rate > 20%"
```

## Monitoring Setup

### Prometheus Configuration

Add CommandCenter to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'commandcenter'
    scrape_interval: 15s
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Key panels to create:

1. **System Health**
   - Component status (Database, Redis, Celery)
   - Overall uptime percentage
   - Response times (p50, p95, p99)

2. **HTTP Traffic**
   - Requests per second by endpoint
   - Error rate (4xx, 5xx)
   - Request duration histogram

3. **Batch Operations**
   - Operations per hour by type
   - Success/failure rate
   - Duration percentiles
   - Items processed per operation

4. **Job Queue**
   - Queue size by status (stacked area chart)
   - Job processing rate
   - Job duration by type
   - Worker count

5. **Database**
   - Connection pool utilization
   - Query duration percentiles
   - Operations per second

6. **Cache**
   - Hit rate percentage
   - Operations per second
   - Redis memory usage (if available)

### Alertmanager Integration

Example Alertmanager configuration:

```yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:5001/'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<your-pagerduty-key>'

  - name: 'slack'
    slack_configs:
      - api_url: '<your-slack-webhook-url>'
        channel: '#commandcenter-alerts'
```

## Testing Observability

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed | jq

# Check from docker-compose
make health
```

### Metrics

```bash
# View all metrics
curl http://localhost:8000/metrics

# Filter specific metrics
curl http://localhost:8000/metrics | grep batch_operations

# Check via Prometheus
curl http://localhost:9090/api/v1/query?query=commandcenter_batch_operations_total
```

### Logs

```bash
# View JSON logs
docker-compose logs backend | tail -50

# Filter by request ID
docker-compose logs backend | grep "f47ac10b-58cc-4372-a567-0e02b2c3d479"

# Filter by log level
docker-compose logs backend | grep '"level":"ERROR"'

# Follow logs in real-time
docker-compose logs -f backend
```

### Tracing

```bash
# Make a request and capture request ID
REQUEST_ID=$(curl -v http://localhost:8000/api/v1/batch/analyze \
  -H "Content-Type: application/json" \
  -d '{"repository_ids": [1, 2, 3]}' \
  2>&1 | grep -i "x-request-id" | cut -d' ' -f3)

# Trace request through logs
docker-compose logs backend | grep "$REQUEST_ID"
```

## Best Practices

### Production Deployment

1. **Enable structured JSON logging**
   ```bash
   JSON_LOGS=true
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

2. **Configure log aggregation**
   - Use ELK Stack, Loki, or CloudWatch Logs
   - Index by request_id for distributed tracing
   - Set retention policies (30-90 days)

3. **Setup Prometheus scraping**
   - 15-second scrape interval
   - Store metrics for 30-90 days
   - Configure alerting rules

4. **Create Grafana dashboards**
   - System health overview
   - Per-component details
   - Business metrics (operations/hour)

5. **Configure alerting**
   - Critical: PagerDuty/phone for immediate action
   - Warning: Slack/email for investigation
   - Test alerts regularly

### Troubleshooting

#### High Error Rate

1. Check `/health/detailed` for component issues
2. Search logs for ERROR level entries
3. Check Prometheus for error metrics by endpoint
4. Review request traces using X-Request-ID

#### Slow Performance

1. Check response time percentiles (p95, p99)
2. Identify slow endpoints in metrics
3. Review database query times
4. Check Celery worker load
5. Review cache hit rate

#### Job Queue Backlog

1. Check Celery worker count: `commandcenter_celery_workers`
2. Review active tasks: `commandcenter_celery_active_tasks`
3. Check for failing jobs: `commandcenter_job_operations_total{status="error"}`
4. Review job duration: `commandcenter_job_duration_seconds`
5. Consider scaling workers or investigating long-running jobs

## Additional Resources

- [FastAPI Production Deployment](https://fastapi.tiangolo.com/deployment/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboard Design](https://grafana.com/docs/grafana/latest/best-practices/)
- [Structured Logging](https://www.structlog.org/en/stable/)
