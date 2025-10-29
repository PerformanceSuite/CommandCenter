# Docker Testing Infrastructure

## Overview

Docker-based test execution ensures CI/production parity by running tests in isolated containers with identical environments.

## Components

### Test Dockerfiles

Each component has a dedicated test Dockerfile:

- `backend/Dockerfile.test` - Backend tests with pytest
- `frontend/Dockerfile.test` - Frontend tests with Vitest
- `hub/backend/Dockerfile.test` - Hub backend with Docker CLI
- `hub/frontend/Dockerfile.test` - Hub frontend tests

### Docker Compose Orchestration

`docker-compose.test.yml` orchestrates:
- **postgres-test**: Test database (port 5433)
- **redis-test**: Test cache (port 6380)
- **test-backend**: Backend tests with dependencies
- **test-frontend**: Frontend tests
- **test-hub-backend**: Hub backend with Docker socket
- **test-hub-frontend**: Hub frontend tests

### Makefile Targets

```bash
make test-docker              # Run all tests
make test-docker-backend      # Backend only
make test-docker-frontend     # Frontend only
make test-docker-hub          # Hub tests
make test-security            # Security tests
make test-performance         # Performance tests
make test-docker-clean        # Cleanup resources
```

## Usage

### Local Development

**Run all tests:**
```bash
make test-docker-all
```

**Run specific component:**
```bash
make test-docker-backend
```

**Debug in container:**
```bash
make test-docker-shell-backend
pytest tests/security/ -v
```

**Extract coverage reports:**
```bash
make test-docker-coverage
# Reports in ./coverage-reports/
```

### CI/CD Integration

GitHub Actions workflow (`.github/workflows/test-docker.yml`) runs automatically on:
- Pull requests to main
- Pushes to main
- Manual workflow dispatch

**Jobs:**
- `test-backend-docker`: Backend tests with coverage
- `test-frontend-docker`: Frontend tests with coverage

## Architecture

### Volume Mounts

```yaml
# Source code (live updates)
- ./backend:/app

# Node modules (cached)
- /app/node_modules

# Test results (extracted)
- backend-test-results:/app/test-results
- backend-coverage:/app/coverage
```

### Environment Variables

**Backend:**
```yaml
DATABASE_URL: postgresql://test:test@postgres-test:5432/commandcenter_test
REDIS_URL: redis://redis-test:6379
SECRET_KEY: test-secret-key
TESTING: "true"
```

**Frontend:**
```yaml
CI: "true"
VITE_API_URL: http://localhost:8000
```

## Benefits

1. **CI/Production Parity**: Tests run in same environment as production containers
2. **Isolation**: Each test run uses fresh database and cache instances
3. **Consistency**: No "works on my machine" issues
4. **Parallel Execution**: Docker Compose can run multiple test suites simultaneously
5. **Easy Cleanup**: `make test-docker-clean` removes all test resources

## Troubleshooting

### Port conflicts

Test services use alternate ports:
- PostgreSQL: 5433 (instead of 5432)
- Redis: 6380 (instead of 6379)

### Slow builds

Enable BuildKit for faster builds:
```bash
export DOCKER_BUILDKIT=1
```

### Tests fail in Docker but pass locally

Check environment variables:
```bash
docker-compose -f docker-compose.test.yml run --rm test-backend env
```
