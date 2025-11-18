# Federation Service Tests

## Overview

Tests are organized into:
- **Unit tests**: `test_catalog_service.py` - Database service layer tests
- **Integration tests**: `test_heartbeat_worker.py` - End-to-end NATS heartbeat flow tests

## Prerequisites

### Database
Integration tests require a PostgreSQL test database. Configure via environment:

```bash
export TEST_DATABASE_URL=postgresql+asyncpg://commandcenter:changeme@localhost:5432/commandcenter_fed_test
```

Or use Docker:

```bash
docker run -d \
  --name postgres-test \
  -e POSTGRES_USER=commandcenter \
  -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=commandcenter_fed_test \
  -p 5432:5432 \
  postgres:16
```

### NATS Server (for integration tests)

Install NATS server:

**macOS:**
```bash
brew install nats-server
```

**Linux:**
```bash
# Download from https://github.com/nats-io/nats-server/releases
wget https://github.com/nats-io/nats-server/releases/download/v2.10.7/nats-server-v2.10.7-linux-amd64.tar.gz
tar -xzf nats-server-v2.10.7-linux-amd64.tar.gz
sudo mv nats-server-v2.10.7-linux-amd64/nats-server /usr/local/bin/
```

**Alternative:** The test suite will use an existing NATS server at `$NATS_URL` if `nats-server` is not installed.

## Running Tests

### All tests
```bash
cd federation
source venv/bin/activate
pytest
```

### Unit tests only
```bash
pytest tests/test_catalog_service.py
```

### Integration tests only
```bash
pytest tests/test_heartbeat_worker.py
```

### Verbose output
```bash
pytest -v
```

### With coverage
```bash
pytest --cov=app --cov-report=html
```

## Test Scenarios Covered

### Unit Tests (`test_catalog_service.py`)
- ✅ Register new project
- ✅ Update heartbeat (mark project ONLINE)
- ✅ Filter projects by status (ONLINE/OFFLINE)
- ✅ Mark stale projects OFFLINE after threshold (90s)
- ✅ Handle missing project during heartbeat update

### Integration Tests (`test_heartbeat_worker.py`)
- ✅ **Valid heartbeat**: Worker receives and processes valid NATS message
- ✅ **Invalid JSON**: Worker rejects malformed JSON gracefully
- ✅ **Schema validation**: Pydantic rejects messages with missing required fields
- ✅ **Unknown project**: Worker handles heartbeat for unregistered project
- ✅ **Namespace validation**: Pydantic validates mesh_namespace matches project_slug
- ✅ **Stale detection**: Stale checker marks projects OFFLINE after 90s
- ✅ **Multiple projects**: Worker handles concurrent heartbeats from multiple hubs
- ✅ **Slug normalization**: Worker normalizes project_slug to lowercase

## Metrics Validation

Integration tests verify:
- Heartbeat message metrics tracked (success/error/unknown)
- NATS connection status gauge updated
- Stale checker metrics tracked
- Project catalog count gauges updated

## Debugging Tests

### View test logs
```bash
pytest -v -s
```

### Run single test
```bash
pytest tests/test_heartbeat_worker.py::test_heartbeat_worker_receives_valid_message -v
```

### Check NATS server
```bash
# Verify NATS is running
nats-server --version

# Check NATS connection
nats account info
```

## CI/CD Integration

For CI environments without nats-server binary:

```yaml
# Example GitHub Actions
services:
  nats:
    image: nats:2.10
    ports:
      - 4222:4222
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: commandcenter
      POSTGRES_PASSWORD: changeme
      POSTGRES_DB: commandcenter_fed_test
    ports:
      - 5432:5432

env:
  NATS_URL: nats://localhost:4222
  TEST_DATABASE_URL: postgresql+asyncpg://commandcenter:changeme@localhost:5432/commandcenter_fed_test
```

## Troubleshooting

### "NATS server not found"
Install `nats-server` or ensure `$NATS_URL` points to running server.

### "Database does not exist"
Create test database:
```bash
createdb commandcenter_fed_test
```

### "Connection refused"
Ensure PostgreSQL and NATS are running:
```bash
pg_isready
nats-server --version
```

### "Port already in use"
Check for conflicting services on ports 4222 (NATS) and 5432 (PostgreSQL).
