# Docker Functionality Integration Tests

## Overview

Integration tests validate Hub's Dagger SDK integration using **REAL Docker containers** (not mocked). Tests verify complete lifecycle management, orchestration, and multi-stack coordination.

## ⚠️ IMPORTANT: Real Containers

These tests create **actual Docker containers** via Dagger SDK:
- Slower than unit tests (10-60s per test)
- Require Docker daemon running
- Use high ports (18000+) to avoid conflicts
- Automatic cleanup after tests

## Test Structure

### Dagger SDK Integration (`test_dagger_integration.py`)

**Tests (12 total):**
1. Start complete stack (postgres, redis, backend, frontend)
2. Stop preserves volumes (data persistence)
3. Restart reuses existing volumes
4. Build backend image with Dagger
5. Build frontend image with Dagger
6. Mount project directory into containers
7. Pass environment variables to containers
8. Expose ports correctly
9. Health check waits for container ready
10. Error handling for failed container start
11. Cleanup on partial failure
12. Multiple stacks run simultaneously

### Container Lifecycle (`test_container_lifecycle.py`)

**Tests (8 total):**
1. Full lifecycle (create, start, stop, restart, remove)
2. Start already-running is idempotent
3. Stop already-stopped is idempotent
4. Container logs accessible
5. Container status updates correctly
6. Restart preserves configuration
7. Force stop when graceful fails
8. Restart after container crash

### Stack Orchestration (`test_stack_orchestration.py`)

**Tests (6 total):**
1. Services start in correct order (dependency-aware)
2. Dependencies verified before starting dependents
3. Partial failure rolls back entire stack
4. Health checks prevent premature ready status
5. OrchestrationService tracks multiple active stacks
6. Registry cleanup on stack removal

## Running Integration Tests

**Prerequisites:**
```bash
# Docker must be running
docker ps

# Ports 18000+ available
lsof -i :18000
```

**Run all integration tests:**
```bash
cd hub/backend
pytest tests/integration/ -v -s
```

**Run specific category:**
```bash
pytest tests/integration/test_dagger_integration.py -v
```

**Run single test:**
```bash
pytest tests/integration/test_dagger_integration.py::test_start_complete_stack -v -s
```

**With markers:**
```bash
# Integration tests only
pytest -m integration -v

# Exclude integration tests
pytest -m "not integration"
```

## Test Count

**Total: 26 tests**
- Dagger SDK integration: 12 tests
- Container lifecycle: 8 tests
- Stack orchestration: 6 tests

## Expected Runtime

- Individual test: 10-60 seconds
- Full suite: 5-10 minutes (sequential)
- Parallel execution: 3-5 minutes

## Test Ports

High port numbers avoid conflicts:

| Service | Port | Purpose |
|---------|------|---------|
| Backend | 18000 | API server |
| Frontend | 13000 | Web UI |
| PostgreSQL | 15432 | Database |
| Redis | 16379 | Cache |

Additional projects increment by 10 (18010, 18020, etc.)

## Troubleshooting

### Docker not running

```bash
# macOS/Windows
Start Docker Desktop

# Verify
docker ps
```

### Port conflicts

```bash
# Find process using port
lsof -i :18000
kill -9 <PID>

# Or change ports in project_config fixture
```

### Tests hang/timeout

```bash
# Check Docker resources
docker info | grep -i memory

# Increase timeout in pytest.ini
timeout = 600
```

### Orphaned containers

```bash
# List all containers
docker ps -a

# Remove test containers
docker ps -a --filter name=integration-test -q | xargs docker rm -f

# Remove test volumes
docker volume ls --filter name=integration-test -q | xargs docker volume rm
```

## Architecture

### Real vs Mocked

**These tests use REAL Dagger SDK:**
- Actual Docker API calls
- Real containers created
- Real volume persistence
- Real network isolation

**NOT mocked**:
- No MagicMock for Dagger client
- No fake containers
- Actual integration validation

### Cleanup

Tests use `async with` context managers:
```python
async with dagger.Connection() as client:
    # Containers created
    yield client
    # Automatic cleanup
```

## Best Practices

1. **Run separately from unit tests:**
   ```bash
   pytest -m "not integration"  # Fast unit tests
   pytest -m integration        # Slow integration tests
   ```

2. **Use cleanup fixtures**
3. **Use high ports (18000+)**
4. **Check Docker before running:**
   ```bash
   docker ps  # Verify Docker running
   ```

5. **Monitor resources:**
   ```bash
   docker stats  # Watch resource usage
   ```

## CI/CD Integration

Integration tests run in CI (`.github/workflows/test-docker.yml`):
- Docker-in-Docker environment
- Parallel execution
- Automatic cleanup
- Failure artifact collection

## Next Steps

1. **Add more scenarios:**
   - Rolling updates
   - Blue-green deployments
   - Network failures

2. **Performance benchmarks:**
   - Startup time tracking
   - Resource monitoring

3. **Chaos testing:**
   - Container crashes
   - Network interruptions
   - Resource exhaustion
