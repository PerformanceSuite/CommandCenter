# Testing Setup Guide

## Test Categories

### Unit Tests
- **Location**: `tests/unit/`, `tests/events/`
- **Dependencies**: None (uses mocks and in-memory database)
- **Run with**: `pytest tests/unit tests/events`
- **Speed**: Fast (< 1 second)

### Router Tests
- **Location**: `tests/routers/`
- **Dependencies**: None (uses in-memory SQLite + ASGITransport)
- **Run with**: `pytest tests/routers`
- **Speed**: Fast (< 1 second)

### Integration Tests
- **Location**: `tests/integration/`
- **Dependencies**: Redis (for Celery background tasks)
- **Run with**: `pytest tests/integration -m integration`
- **Speed**: Slow (5-30 seconds per test)
- **Requirements**: See setup instructions below

## Prerequisites for Integration Tests

### 1. Redis (Required for Celery tasks)

**macOS (Homebrew)**:
```bash
brew install redis
brew services start redis

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

**Linux (apt)**:
```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Verify
redis-cli ping
```

**Docker (Cross-platform)**:
```bash
docker run -d --name redis-test -p 6379:6379 redis:7-alpine
```

### 2. Environment Configuration

Set environment variables for tests:

```bash
# For integration tests
export REDIS_URL="redis://localhost:6379/1"  # Use DB 1 for tests
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

Or create a `.env.test` file:
```bash
REDIS_URL=redis://localhost:6379/1
DATABASE_URL=sqlite+aiosqlite:///:memory:
```

## Running Tests

### Run All Tests (Requires Redis)
```bash
pytest
```

### Run Only Unit Tests (No Dependencies)
```bash
pytest tests/unit tests/events tests/routers -v
```

### Run Integration Tests (Requires Redis)
```bash
# Start Redis first
brew services start redis  # macOS
# OR
docker run -d -p 6379:6379 redis:7-alpine

# Run tests
pytest tests/integration -m integration -v
```

### Skip Integration Tests
```bash
pytest -m "not integration"
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.unit` - Fast unit tests with mocks
- `@pytest.mark.integration` - Integration tests requiring services
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.timeout(N)` - Tests with custom timeout

## CI/CD Configuration

For CI environments (GitHub Actions, GitLab CI), use service containers:

### GitHub Actions Example
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
    options: --health-cmd "redis-cli ping" --health-interval 10s
```

### GitLab CI Example
```yaml
services:
  - redis:7-alpine

variables:
  REDIS_URL: "redis://redis:6379/1"
```

## Celery Worker for Tests

Integration tests that use Celery tasks (`task_always_eager=False`) need either:

1. **Option A: Eager Mode** (Recommended for most tests)
   - Set `task_always_eager=True` in conftest.py
   - Tasks run synchronously in the same process
   - No worker needed

2. **Option B: Real Worker** (For testing async behavior)
   - Start a Celery worker: `celery -A app.celery_app worker --loglevel=info`
   - Tests will queue tasks to Redis and worker will execute them
   - Required for testing concurrency, retries, etc.

Current configuration uses **Option B** (`task_always_eager=False`) to test real async behavior.

## Troubleshooting

### Redis Connection Errors
```
kombu.exceptions.OperationalError: Error connecting to redis:6379
```

**Solution**:
1. Check Redis is running: `redis-cli ping`
2. Verify REDIS_URL: `echo $REDIS_URL`
3. Update to localhost: `export REDIS_URL="redis://localhost:6379/1"`

### Database Errors
```
sqlalchemy.exc.OperationalError: no such table: events
```

**Solution**:
- Tests should use in-memory database with fixtures
- Check test imports database fixtures from conftest.py
- Ensure `@pytest_asyncio.fixture` is used for async fixtures

### Import Errors
```
ModuleNotFoundError: No module named 'pytest_asyncio'
```

**Solution**:
```bash
pip install -r requirements.txt
# Or specifically:
pip install pytest-asyncio pytest-timeout
```

## Performance Tips

1. **Parallel Execution**: Use `pytest-xdist` for parallel tests
   ```bash
   pip install pytest-xdist
   pytest -n auto  # Use all CPU cores
   ```

2. **Test Selection**: Run specific test files/functions
   ```bash
   pytest tests/unit/test_project_model.py::test_project_creation -v
   ```

3. **Verbose Output**: Use `-v` for detailed output, `-vv` for more detail
   ```bash
   pytest -vv --tb=short
   ```

## Test Coverage

Generate coverage reports:

```bash
pip install pytest-cov
pytest --cov=app --cov-report=html --cov-report=term
open htmlcov/index.html  # View in browser
```

## Summary

| Test Type | Dependencies | Speed | Command |
|-----------|-------------|-------|---------|
| Unit | None | Fast | `pytest tests/unit tests/events tests/routers` |
| Integration | Redis | Slow | `pytest tests/integration -m integration` |
| All | Redis | Mixed | `pytest` |
| No Integration | None | Fast | `pytest -m "not integration"` |
