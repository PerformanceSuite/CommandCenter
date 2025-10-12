# Schedule Management System

Complete guide to CommandCenter's schedule management and automated task execution system.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Schedule Types](#schedule-types)
- [API Reference](#api-reference)
- [Celery Beat Integration](#celery-beat-integration)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)

## Overview

The CommandCenter schedule management system enables automated execution of recurring tasks including:

- **Repository Analysis**: Automated code analysis on a schedule
- **Data Export**: Scheduled exports in various formats (SARIF, Markdown, CSV, etc.)
- **Webhook Delivery**: Periodic webhook notifications
- **Batch Operations**: Scheduled bulk operations

### Key Features

- **6 Frequency Types**: Once, hourly, daily, weekly, monthly, and custom cron expressions
- **Timezone Support**: Full IANA timezone support for accurate scheduling
- **Execution Windows**: Optional start/end times to constrain execution periods
- **Health Monitoring**: Automatic detection of failing or stale schedules
- **Conflict Detection**: Warns about overlapping schedules
- **Audit Logging**: Complete execution history with success/failure tracking
- **Manual Execution**: Force execute schedules on demand

## Architecture

### Components

```
┌─────────────────────┐
│   Celery Beat       │  Periodic task dispatcher
│   (Redis-backed)    │  - Runs every minute
└──────────┬──────────┘  - Checks due schedules
           │
           ▼
┌─────────────────────┐
│  Schedule Service   │  Business logic layer
│                     │  - CRUD operations
└──────────┬──────────┘  - Next run calculation
           │             - Conflict detection
           ▼
┌─────────────────────┐
│    Job Service      │  Async execution
│                     │  - Creates jobs
└──────────┬──────────┘  - Dispatches to Celery
           │
           ▼
┌─────────────────────┐
│   Celery Worker     │  Task execution
│                     │  - Runs analysis
└─────────────────────┘  - Sends webhooks
```

### Data Flow

1. **Schedule Creation**: User creates schedule via API
2. **Next Run Calculation**: Service calculates next execution time
3. **Beat Dispatcher**: Celery Beat checks for due schedules every minute
4. **Job Creation**: ScheduleService creates Job for due schedule
5. **Task Execution**: Celery worker executes job asynchronously
6. **Result Recording**: Success/failure recorded in schedule audit log
7. **Next Run Update**: Schedule next_run_at updated for future execution

## Schedule Types

### 1. Once (One-time Execution)

Execute a task exactly once at a specified time.

```python
{
    "frequency": "once",
    "start_time": "2025-10-15T14:00:00Z"
}
```

**Use Cases**:
- One-time migrations
- Single event notifications
- Deferred task execution

### 2. Hourly

Execute at the top of every hour.

```python
{
    "frequency": "hourly"
}
```

**Alignment**: Tasks align to `:00` of each hour (e.g., 14:00, 15:00, 16:00)

**Use Cases**:
- Frequent status checks
- Real-time data synchronization
- Hourly metrics collection

### 3. Daily

Execute once per day at midnight (UTC or specified timezone).

```python
{
    "frequency": "daily",
    "timezone": "America/New_York"
}
```

**Alignment**: Tasks align to `00:00:00` in the specified timezone

**Use Cases**:
- Daily reports
- Nightly backups
- End-of-day processing

### 4. Weekly

Execute once per week on Monday at midnight.

```python
{
    "frequency": "weekly",
    "timezone": "UTC"
}
```

**Alignment**: Tasks align to Monday `00:00:00`

**Use Cases**:
- Weekly summaries
- Weekly data aggregation
- Periodic cleanup tasks

### 5. Monthly

Execute on the first day of each month at midnight.

```python
{
    "frequency": "monthly"
}
```

**Alignment**: Tasks align to first day of month `00:00:00`

**Use Cases**:
- Monthly reports
- Monthly billing
- Subscription renewals

### 6. Cron (Custom Expressions)

Execute based on cron expression for maximum flexibility.

```python
{
    "frequency": "cron",
    "cron_expression": "0 2 * * *"  # Daily at 2 AM
}
```

**Supported Cron Format**:
```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

**Common Cron Examples**:

| Expression | Description |
|------------|-------------|
| `0 * * * *` | Every hour at :00 |
| `*/15 * * * *` | Every 15 minutes |
| `0 2 * * *` | Daily at 2:00 AM |
| `0 9-17 * * *` | Every hour between 9 AM - 5 PM |
| `0 0 * * 0` | Weekly on Sunday at midnight |
| `0 0 1 * *` | Monthly on 1st at midnight |
| `0 0 1 1 *` | Annually on Jan 1 at midnight |

**Use Cases**:
- Complex scheduling requirements
- Business-hour-only execution
- Custom maintenance windows

## API Reference

### Create Schedule

**Endpoint**: `POST /api/v1/schedules`

**Request**:
```json
{
    "project_id": 1,
    "name": "Daily Repository Analysis",
    "description": "Analyze repository changes daily",
    "task_type": "analysis",
    "frequency": "daily",
    "timezone": "America/New_York",
    "task_parameters": {
        "repository_id": 42,
        "analysis_type": "full"
    },
    "enabled": true,
    "tags": {
        "team": "backend",
        "priority": "high"
    }
}
```

**Response**: `201 Created`
```json
{
    "id": 123,
    "project_id": 1,
    "name": "Daily Repository Analysis",
    "description": "Analyze repository changes daily",
    "task_type": "analysis",
    "frequency": "daily",
    "timezone": "America/New_York",
    "next_run_at": "2025-10-13T04:00:00Z",
    "enabled": true,
    "run_count": 0,
    "success_count": 0,
    "failure_count": 0,
    "success_rate": null,
    "is_active": true,
    "created_at": "2025-10-12T15:30:00Z",
    "updated_at": "2025-10-12T15:30:00Z"
}
```

### List Schedules

**Endpoint**: `GET /api/v1/schedules`

**Query Parameters**:
- `project_id` (optional): Filter by project
- `enabled` (optional): Filter by enabled status
- `task_type` (optional): Filter by task type
- `frequency` (optional): Filter by frequency
- `page` (default: 1): Page number
- `page_size` (default: 50, max: 100): Items per page

**Response**: `200 OK`
```json
{
    "schedules": [...],
    "total": 25,
    "page": 1,
    "page_size": 50,
    "pages": 1
}
```

### Get Schedule

**Endpoint**: `GET /api/v1/schedules/{schedule_id}`

**Response**: `200 OK`
```json
{
    "id": 123,
    "project_id": 1,
    "name": "Daily Repository Analysis",
    ...
}
```

### Update Schedule

**Endpoint**: `PATCH /api/v1/schedules/{schedule_id}`

**Request**:
```json
{
    "name": "Updated Schedule Name",
    "frequency": "weekly",
    "enabled": false
}
```

**Response**: `200 OK`

**Note**: Updating `frequency`, `cron_expression`, `interval_seconds`, or `timezone` automatically recalculates `next_run_at`.

### Delete Schedule

**Endpoint**: `DELETE /api/v1/schedules/{schedule_id}`

**Response**: `204 No Content`

### Execute Schedule

**Endpoint**: `POST /api/v1/schedules/{schedule_id}/execute`

**Request** (optional):
```json
{
    "force": true  // Execute even if disabled or not due
}
```

**Response**: `202 Accepted`
```json
{
    "schedule_id": 123,
    "schedule_name": "Daily Repository Analysis",
    "job_id": 456,
    "executed_at": "2025-10-12T15:45:00Z",
    "next_run_at": "2025-10-13T04:00:00Z",
    "message": "Schedule executed successfully, job 456 created"
}
```

### Enable/Disable Schedule

**Endpoints**:
- `POST /api/v1/schedules/{schedule_id}/enable`
- `POST /api/v1/schedules/{schedule_id}/disable`

**Response**: `200 OK`
```json
{
    "id": 123,
    "enabled": false,
    ...
}
```

### Get Schedule Statistics

**Endpoint**: `GET /api/v1/schedules/statistics/summary`

**Query Parameters**:
- `project_id` (optional): Filter by project

**Response**: `200 OK`
```json
{
    "total_schedules": 15,
    "enabled_schedules": 12,
    "disabled_schedules": 3,
    "total_runs": 1250,
    "successful_runs": 1180,
    "failed_runs": 70,
    "success_rate": 94.4,
    "by_frequency": {
        "daily": 8,
        "hourly": 4,
        "weekly": 2,
        "cron": 1
    }
}
```

### List Due Schedules

**Endpoint**: `GET /api/v1/schedules/due/list`

**Query Parameters**:
- `limit` (default: 100, max: 500): Maximum schedules to return

**Response**: `200 OK`
```json
[
    {
        "id": 123,
        "name": "Daily Analysis",
        "next_run_at": "2025-10-12T14:00:00Z",
        ...
    }
]
```

## Celery Beat Integration

### Configuration

Celery Beat is configured in `backend/app/tasks/__init__.py` with RedBeat (Redis-backed scheduler):

```python
celery_app.conf.update(
    beat_scheduler="redbeat.RedBeatScheduler",
    redbeat_redis_url=CELERY_BROKER_URL,
)
```

### Automatic Tasks

The system runs three automatic periodic tasks:

#### 1. Schedule Dispatcher

**Task**: `dispatch_due_schedules`
**Schedule**: Every 60 seconds
**Purpose**: Find and execute schedules that are due

```python
# Defined in backend/app/beat_schedule.py
"dispatch-due-schedules": {
    "task": "app.tasks.scheduled_tasks.dispatch_due_schedules",
    "schedule": 60.0,
}
```

#### 2. Schedule Cleanup

**Task**: `cleanup_expired_schedules`
**Schedule**: Daily at 2:00 AM UTC
**Purpose**: Disable schedules past their `end_time`

```python
"cleanup-expired-schedules": {
    "task": "app.tasks.scheduled_tasks.cleanup_expired_schedules",
    "schedule": crontab(hour=2, minute=0),
}
```

#### 3. Schedule Health Monitor

**Task**: `monitor_schedule_health`
**Schedule**: Every 5 minutes
**Purpose**: Detect and alert on problematic schedules

```python
"monitor-schedule-health": {
    "task": "app.tasks.scheduled_tasks.monitor_schedule_health",
    "schedule": crontab(minute="*/5"),
}
```

### Starting Celery Beat

#### Docker Compose (Recommended)

```bash
# Start all services including Celery Beat
make start

# View Beat logs
docker-compose logs -f celery-beat
```

#### Manual Start

```bash
# In backend directory
celery -A app.tasks beat --loglevel=info
```

## Examples

### Example 1: Daily Repository Analysis

```bash
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "name": "Daily Code Analysis",
    "task_type": "analysis",
    "frequency": "daily",
    "timezone": "America/New_York",
    "task_parameters": {
        "repository_id": 42,
        "analysis_type": "security"
    },
    "description": "Daily security scan at midnight ET"
}'
```

### Example 2: Hourly Status Check

```bash
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "name": "Hourly Health Check",
    "task_type": "health_check",
    "frequency": "hourly",
    "task_parameters": {},
    "description": "Check system health every hour"
}'
```

### Example 3: Weekly Report (Cron)

```bash
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "name": "Weekly Report",
    "task_type": "export",
    "frequency": "cron",
    "cron_expression": "0 9 * * 1",
    "timezone": "America/Los_Angeles",
    "task_parameters": {
        "format": "pdf",
        "report_type": "summary"
    },
    "description": "Weekly report every Monday at 9 AM PT"
}'
```

### Example 4: Limited Time Campaign

```bash
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "name": "Campaign Notifications",
    "task_type": "webhook_delivery",
    "frequency": "daily",
    "start_time": "2025-11-01T00:00:00Z",
    "end_time": "2025-11-30T23:59:59Z",
    "task_parameters": {
        "webhook_id": 15
    },
    "description": "Daily notifications during November campaign"
}'
```

### Example 5: Business Hours Only

```bash
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "name": "Business Hours Sync",
    "task_type": "sync",
    "frequency": "cron",
    "cron_expression": "0 9-17 * * 1-5",
    "timezone": "America/New_York",
    "description": "Sync every hour, 9 AM - 5 PM, Monday-Friday ET"
}'
```

## Best Practices

### 1. Schedule Naming

Use clear, descriptive names that include:
- **Purpose**: What does it do?
- **Frequency**: How often?
- **Scope**: What does it affect?

**Good Examples**:
- `Daily Security Scan - Main Repository`
- `Hourly Status Check - Production`
- `Weekly Report Export - All Projects`

**Bad Examples**:
- `Schedule 1`
- `Test`
- `ASAP`

### 2. Timezone Management

**Always specify timezones explicitly** for predictable behavior:

```python
# ✅ Good - Explicit timezone
{
    "frequency": "daily",
    "timezone": "America/New_York"
}

# ❌ Risky - Depends on server timezone
{
    "frequency": "daily"
    # Defaults to UTC, may confuse users
}
```

**Common Timezones**:
- `UTC` - Universal coordinated time
- `America/New_York` - Eastern Time (US)
- `America/Los_Angeles` - Pacific Time (US)
- `Europe/London` - UK time
- `Asia/Tokyo` - Japan time

### 3. Task Parameters

Store all task-specific configuration in `task_parameters`:

```json
{
    "task_type": "analysis",
    "task_parameters": {
        "repository_id": 42,
        "analysis_type": "security",
        "include_dependencies": true,
        "notify_on_completion": true,
        "notification_emails": ["team@example.com"]
    }
}
```

### 4. Execution Windows

Use `start_time` and `end_time` for temporary schedules:

```json
{
    "frequency": "daily",
    "start_time": "2025-11-01T00:00:00Z",
    "end_time": "2025-11-30T23:59:59Z"
}
```

**Automatic Cleanup**: The `cleanup_expired_schedules` task disables schedules past their `end_time` daily.

### 5. Tags for Organization

Use tags to organize and filter schedules:

```json
{
    "tags": {
        "environment": "production",
        "team": "backend",
        "priority": "high",
        "cost_center": "engineering"
    }
}
```

### 6. Monitor Success Rates

Check `success_rate` regularly:
- **> 95%**: Healthy
- **80-95%**: Investigate failures
- **< 80%**: Critical - requires immediate attention

### 7. Test Before Production

1. Create schedule as **disabled** initially
2. Execute manually with `force: true`
3. Verify job completes successfully
4. Enable schedule for automatic execution

```bash
# Step 1: Create disabled
curl -X POST .../schedules -d '{"enabled": false, ...}'

# Step 2: Test execution
curl -X POST .../schedules/123/execute -d '{"force": true}'

# Step 3: Check job results
curl -X GET .../jobs/456

# Step 4: Enable if successful
curl -X POST .../schedules/123/enable
```

## Troubleshooting

### Schedule Not Executing

**Symptoms**: Schedule shows `next_run_at` in the past but hasn't executed

**Checks**:

1. **Is schedule enabled?**
   ```bash
   curl http://localhost:8000/api/v1/schedules/123
   # Check: "enabled": true
   ```

2. **Is Celery Beat running?**
   ```bash
   docker-compose ps celery-beat
   # Should show: Up
   ```

3. **Check Beat logs**:
   ```bash
   docker-compose logs celery-beat | grep -i "due schedules"
   ```

4. **Is schedule within execution window?**
   ```bash
   # Check start_time and end_time fields
   curl http://localhost:8000/api/v1/schedules/123
   ```

5. **Check due schedules endpoint**:
   ```bash
   curl http://localhost:8000/api/v1/schedules/due/list
   ```

### Schedule Repeatedly Failing

**Symptoms**: High `failure_count`, low `success_rate`

**Debug Steps**:

1. **Check last error**:
   ```bash
   curl http://localhost:8000/api/v1/schedules/123
   # Check: "last_error" field
   ```

2. **Review job execution logs**:
   ```bash
   # Find recent jobs for this schedule
   curl "http://localhost:8000/api/v1/jobs?tags.schedule_id=123"
   ```

3. **Check Celery worker logs**:
   ```bash
   docker-compose logs celery-worker | grep "schedule_id=123"
   ```

4. **Validate task_parameters**:
   - Ensure repository_id exists
   - Check file paths
   - Verify API credentials

### Timezone Issues

**Symptoms**: Schedule executes at wrong time

**Solutions**:

1. **Verify timezone string**:
   ```python
   import pytz
   tz = pytz.timezone('America/New_York')  # Should not raise
   ```

2. **Check current time in timezone**:
   ```python
   from datetime import datetime
   import pytz

   tz = pytz.timezone('America/New_York')
   now_tz = datetime.utcnow().astimezone(tz)
   print(now_tz)
   ```

3. **Use UTC for debugging**:
   ```bash
   # Temporarily set to UTC to isolate timezone issues
   curl -X PATCH .../schedules/123 -d '{"timezone": "UTC"}'
   ```

### Cron Expression Not Working

**Symptoms**: Schedule never executes or executes at wrong time

**Debug**:

1. **Validate cron expression**:
   ```python
   from croniter import croniter
   from datetime import datetime

   expr = "0 2 * * *"
   now = datetime.utcnow()

   # Should not raise
   iter = croniter(expr, now)
   next_run = iter.get_next(datetime)
   print(f"Next run: {next_run}")
   ```

2. **Test with online tool**:
   - Visit: https://crontab.guru/
   - Enter expression
   - Verify interpretation

3. **Common mistakes**:
   ```bash
   # ❌ Wrong - Missing field
   "0 2 * *"

   # ✅ Correct - 5 fields
   "0 2 * * *"

   # ❌ Wrong - Invalid range
   "0 25 * * *"  # Hour 25 doesn't exist

   # ✅ Correct
   "0 23 * * *"  # Hour 23 (11 PM)
   ```

### High Memory/CPU Usage

**Symptoms**: Celery Beat consuming excessive resources

**Causes**:
- Too many schedules checked per minute
- Complex cron expressions
- Large `next_run_at` calculations

**Solutions**:

1. **Limit active schedules**:
   ```bash
   # Disable unused schedules
   curl -X POST .../schedules/123/disable
   ```

2. **Increase Beat interval** (not recommended):
   ```python
   # In beat_schedule.py - change from 60s to 120s
   "dispatch-due-schedules": {
       "schedule": 120.0,  # Every 2 minutes
   }
   ```

3. **Archive old schedules**:
   ```bash
   # Delete schedules past end_time
   curl -X DELETE .../schedules/123
   ```

## Monitoring

### Health Check Endpoint

The `monitor_schedule_health` task runs every 5 minutes and checks for:

1. **High Failure Rate**: `success_rate < 50%` after 10+ runs
2. **Stale Schedules**: No execution in 7+ days (non-once schedules)
3. **Consecutive Failures**: Last 3 runs all failed

**Access Health Report**:
```bash
# View latest health monitoring results in logs
docker-compose logs celery-worker | grep "schedule_health"
```

### Prometheus Metrics

The system exposes metrics for monitoring:

```
# Schedule execution metrics
commandcenter_schedule_runs_total{schedule_id, status}
commandcenter_schedule_execution_duration_seconds{schedule_id}

# Schedule states
commandcenter_schedules_total{status}  # enabled/disabled
commandcenter_schedules_due{} # Current due count
```

**Grafana Dashboard** (recommended):
- Schedule success rate over time
- Due schedules count
- Failed schedules by type
- Average execution duration

### Alerting Rules

**Recommended Alerts**:

1. **High Failure Rate**:
   ```yaml
   alert: ScheduleHighFailureRate
   expr: schedule_success_rate < 0.8
   for: 1h
   ```

2. **Stale Schedules**:
   ```yaml
   alert: ScheduleNotExecuting
   expr: time() - schedule_last_run_timestamp > 604800  # 7 days
   ```

3. **Beat Not Running**:
   ```yaml
   alert: CeleryBeatDown
   expr: up{job="celery-beat"} == 0
   for: 5m
   ```

### Logs

**Key log messages**:

```bash
# Schedule created
INFO  Created schedule 123 (Daily Analysis) with next run at 2025-10-13T00:00:00Z

# Schedule executed
INFO  Executed schedule 123, created job 456, next run at 2025-10-14T00:00:00Z

# Dispatcher summary
INFO  Schedule dispatcher completed: 5 dispatched, 0 failed

# Health issues detected
WARNING  Found 2 critical schedule issues

# Cleanup summary
INFO  Schedule cleanup completed: 3 schedules disabled
```

**Access logs**:
```bash
# All schedule-related logs
docker-compose logs backend celery-worker celery-beat | grep -i schedule

# Specific schedule
docker-compose logs backend celery-worker | grep "schedule_id=123"

# Health monitoring
docker-compose logs celery-worker | grep "monitor_schedule_health"
```

---

## Summary

The CommandCenter schedule management system provides:

✅ **6 frequency types** for flexible scheduling
✅ **Timezone-aware** execution with IANA support
✅ **Automatic execution** via Celery Beat
✅ **Health monitoring** for early issue detection
✅ **Comprehensive API** for full CRUD control
✅ **Audit logging** for compliance and debugging
✅ **Manual execution** for testing and emergency runs

**Next Steps**:
1. Review [API Reference](#api-reference) for integration
2. Check [Examples](#examples) for common patterns
3. Follow [Best Practices](#best-practices) for production use
4. Set up [Monitoring](#monitoring) for reliability

For support, see [Troubleshooting](#troubleshooting) or check logs with `docker-compose logs`.
