# Hub Monitoring with Celery Flower

## Overview

Flower provides real-time monitoring of Celery workers and tasks.

## Quick Start

### Start Monitoring Stack

```bash
cd hub
docker-compose -f docker-compose.monitoring.yml up -d
```

### Access Flower Dashboard

Open http://localhost:5555

## Dashboard Features

### Workers Tab
- Shows active Celery workers
- Worker status (online/offline)
- Current tasks being processed
- Worker resource usage

### Tasks Tab
- Task history (success/failure)
- Task duration statistics
- Active tasks
- Task arguments and results

### Monitor Tab
- Real-time task events
- Success/failure rate graphs
- Task execution timeline

## Key Metrics

**Task Performance:**
- Average duration per task type
- Success rate: target > 95%
- Retry rate: target < 5%

**Worker Health:**
- Active workers: expect 2 (concurrency=2)
- Queue depth: target < 10 tasks
- Failed tasks: investigate any failures

## Alerts

**Critical (action required immediately):**
- All workers offline
- Redis unavailable
- Task failure rate > 10%

**Warning (investigate soon):**
- Queue depth > 10 tasks
- Average task duration > 30 minutes
- Worker CPU/memory > 80%

## Troubleshooting

### Worker Not Showing
```bash
# Check worker logs
docker logs hub-celery-worker

# Restart worker
docker-compose -f docker-compose.monitoring.yml restart celery-worker
```

### Tasks Stuck in Queue
```bash
# Check Redis connection
docker exec hub-redis redis-cli ping

# Check worker capacity
# View in Flower: Workers tab → Pool size
```

### Flower Not Accessible
```bash
# Check Flower logs
docker logs hub-flower

# Verify port not in use
lsof -i :5555
```

## Production Deployment

**Security:**
- Add authentication: `--basic_auth=user:password`
- Use HTTPS with reverse proxy
- Restrict access by IP

**Example with auth:**
```yaml
# In docker-compose.monitoring.yml
flower:
  command: celery -A app.celery_app flower --port=5555 --basic_auth=admin:secure_password_here
```

## Cleanup

```bash
# Stop monitoring stack
docker-compose -f docker-compose.monitoring.yml down

# Remove volumes (clears Redis data)
docker-compose -f docker-compose.monitoring.yml down -v
```
