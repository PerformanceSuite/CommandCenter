# CommandCenter Hub

Multi-project management interface for CommandCenter instances.

## Features

- **Project Management**: Create, start, stop, delete CommandCenter instances
- **Port Isolation**: Automatic port allocation to avoid conflicts
- **Background Tasks**: Non-blocking project operations with Celery
- **Real-time Progress**: Live progress updates for long-running operations
- **Monitoring Dashboard**: Celery Flower for task/worker monitoring
- **Folder Browser**: Select project directories visually
- **Status Tracking**: Real-time project status (stopped/starting/running/error)

## Architecture

### Technology Stack

**Backend:**
- FastAPI (API server)
- Celery (background tasks)
- Redis (message broker)
- SQLite (project registry)
- Dagger (container orchestration)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- Vitest (testing)

### Background Task System

Hub uses Celery for asynchronous project operations:

```
User → Hub API → Celery Queue → Worker → Dagger → Docker
         ↓           ↓              ↓
      Task ID    Redis Store    Progress Updates
```

**Benefits:**
- API responds in < 100ms (just queues task)
- No 20-30 min blocking during first start
- Real-time progress updates every 2 seconds
- Concurrent operations on multiple projects

**Monitoring:**
- Flower dashboard at http://localhost:5555
- View active tasks, worker status, performance metrics

## Event System

Hub uses an event-driven architecture with NATS message bus. All state changes are captured as events for observability, integration, and replay.

**Quick Start:**
```bash
# Stream events in real-time
websocat ws://localhost:9001/api/events/stream?subject=hub.>

# Query historical events
curl http://localhost:9001/api/events?limit=10

# Check NATS health
curl http://localhost:9001/health/nats
```

**Documentation:** See `docs/EVENT_SYSTEM.md` for full details.

**Endpoints:**
- `POST /api/events` - Publish event
- `GET /api/events` - Query events
- `WS /api/events/stream` - Real-time stream

## Quick Start

### Docker (Production)

```bash
# Start all services
docker-compose -f docker-compose.monitoring.yml up -d

# Access Hub
open http://localhost:9000

# Monitor tasks
open http://localhost:5555
```

### Development

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup instructions.

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[MONITORING.md](MONITORING.md)** - Celery Flower monitoring
- **[TESTING.md](TESTING.md)** - Running tests
- **[Design Doc](../docs/plans/2025-11-02-hub-background-tasks-design.md)** - Background tasks architecture

## Testing

```bash
# Backend unit tests
cd backend
pytest tests/unit/ -v

# Backend integration tests (requires Redis)
docker run -d -p 6379:6379 redis:7-alpine
pytest tests/integration/ -v -m "not slow"

# Frontend tests
cd frontend
npm test

# End-to-end test
./scripts/e2e-test.sh
```

## Monitoring

**Flower Dashboard** (http://localhost:5555):
- Real-time task monitoring
- Worker status and performance
- Task history and statistics

**Key Metrics:**
- Task success rate: target > 95%
- Average task duration: 10-30 min (first start), < 5 min (subsequent)
- Queue depth: target < 10 tasks

## Troubleshooting

**Tasks not running:**
```bash
# Check worker logs
docker logs hub-celery-worker

# Check Redis
docker exec hub-redis redis-cli ping
```

**Slow tasks:**
- First Dagger build: 20-30 min (normal)
- Subsequent builds: 2-5 min (cached)
- Check Flower for task duration

**Worker crashes:**
```bash
# Restart worker
docker-compose -f docker-compose.monitoring.yml restart celery-worker
```

See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) for more details.

## Contributing

See [../CONTRIBUTING.md](../CONTRIBUTING.md)

## License

See [../LICENSE](../LICENSE)
