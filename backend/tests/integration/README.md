# Integration Tests Documentation

## Overview

This directory contains integration tests for the CommandCenter application. Integration tests verify that multiple components work together correctly, including:

- **Export System**: SARIF, HTML, CSV, Excel, and JSON export formats
- **WebSocket**: Real-time job progress updates and broadcasts
- **Celery Tasks**: Async job execution, status updates, and error handling

## Test Structure

```
tests/integration/
├── __init__.py              # Package marker
├── conftest.py              # Integration test fixtures
├── test_export_integration.py       # Export system tests (20+ tests)
├── test_websocket_integration.py    # WebSocket tests (20+ tests)
├── test_celery_integration.py       # Celery task tests (30+ tests)
└── README.md                # This file
```

## Running Tests

### Run All Integration Tests

```bash
# From project root
cd backend
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_export_integration.py -v

# Run specific test class
pytest tests/integration/test_export_integration.py::TestExportIntegration -v

# Run specific test
pytest tests/integration/test_export_integration.py::TestExportIntegration::test_sarif_export_complete_workflow -v
```

### Run with Markers

Integration tests are marked with `@pytest.mark.integration`:

```bash
# Run only integration tests
pytest -m integration -v

# Run integration tests excluding slow tests
pytest -m "integration and not slow" -v

# Run only slow integration tests
pytest -m "integration and slow" -v
```

### Parallel Execution

Run tests in parallel for faster execution:

```bash
# Run with 4 workers
pytest tests/integration/ -n 4

# Auto-detect CPU count
pytest tests/integration/ -n auto
```

## Test Fixtures

### Core Fixtures (from conftest.py)

- `test_project`: Creates a test project
- `test_repository`: Creates a test repository
- `test_technology`: Creates a test technology
- `test_job`: Creates a test job
- `test_analysis_data`: Complete analysis data for export testing
- `job_service`: JobService instance
- `websocket_test_client`: Async client for WebSocket testing
- `export_test_data`: Sample data for export format testing
- `celery_config`: Celery configuration for testing
- `mock_celery_task`: Mocked Celery task

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_my_integration(
    async_client: AsyncClient,
    test_project: Project,
    test_analysis_data: Dict[str, Any],
):
    """Example integration test using fixtures."""
    project_id = test_analysis_data["project_id"]

    response = await async_client.get(
        f"/api/v1/export/json?project_id={project_id}"
    )

    assert response.status_code == 200
```

## Test Coverage

### Export Integration Tests (test_export_integration.py)

**Test Classes:**
- `TestExportIntegration`: 20+ tests for export workflows
- `TestExportErrorHandling`: 3 tests for error handling

**Coverage:**
- SARIF export with GitHub Code Scanning compatibility
- HTML export with embedded visualizations
- CSV export (5 types: technologies, dependencies, metrics, gaps, combined)
- Excel export with multi-sheet workbooks
- JSON export for programmatic access
- Batch export endpoints
- Rate limiting validation
- Content-Length headers
- Concurrent requests
- Empty analysis handling
- Error scenarios

### WebSocket Integration Tests (test_websocket_integration.py)

**Test Classes:**
- `TestWebSocketIntegration`: 15+ tests for WebSocket connections
- `TestConnectionManager`: 3 tests for connection management
- `TestWebSocketPerformance`: 2 tests for performance

**Coverage:**
- Connection establishment and authentication
- Real-time job progress updates
- Multiple concurrent clients
- Broadcasting to multiple clients
- Error handling and recovery
- Connection cleanup
- Job completion notifications
- Concurrent updates
- JSON serialization
- Performance under load
- Memory leak prevention

### Celery Integration Tests (test_celery_integration.py)

**Test Classes:**
- `TestCeleryJobIntegration`: 15+ tests for job workflows
- `TestCeleryTaskHandlers`: 3 tests for task handlers
- `TestJobErrorHandling`: 4 tests for error handling
- `TestJobServiceMethods`: 3 tests for service methods

**Coverage:**
- Job creation workflow
- Job dispatch to Celery
- Delayed execution
- Status updates during execution
- Job completion with results
- Job failure with error tracking
- Job cancellation
- Progress tracking
- Active jobs listing
- Job statistics
- Filtering and pagination
- Task handlers (analyze, export, batch)
- Error handling (invalid types, non-existent jobs, timeouts)
- Service method validation

## Test Data

### Sample Analysis Data

```python
{
    "technologies": [
        {"name": "Python", "category": "languages", "version": "3.11"},
        {"name": "FastAPI", "category": "frameworks", "version": "0.109.0"},
    ],
    "dependencies": [
        {"name": "requests", "version": "2.31.0", "is_outdated": False},
    ],
    "gaps": [
        {"technology": "Python", "current_version": "3.9", "latest_version": "3.11"},
    ],
    "metrics": {
        "total_technologies": 3,
        "outdated_dependencies": 1,
    }
}
```

## CI/CD Integration

### GitHub Actions

Integration tests are automatically run on:
- Pull requests to `main` branch
- Pushes to `main` branch
- Manual workflow dispatch

See `.github/workflows/integration-tests.yml` for configuration.

### Local Pre-commit

Run integration tests before committing:

```bash
# Add to .git/hooks/pre-push
pytest tests/integration/ -v --tb=short
```

## Best Practices

### 1. Test Independence

Each test should be independent and not rely on other tests:

```python
@pytest.mark.asyncio
async def test_feature(db_session, test_project):
    # Create test data
    job = await create_test_job(db_session, test_project)

    # Test logic
    result = await test_feature(job)

    # Assert
    assert result.success

    # No need to cleanup - fixtures handle it
```

### 2. Use Descriptive Test Names

```python
# Good
async def test_export_sarif_includes_github_code_scanning_rules():
    pass

# Bad
async def test_export():
    pass
```

### 3. Test Both Success and Failure Cases

```python
async def test_job_completion_success():
    # Test successful completion
    pass

async def test_job_completion_with_errors():
    # Test failure handling
    pass
```

### 4. Mock External Services

```python
@patch('app.services.github_service.PyGithub')
async def test_repository_sync(mock_github):
    mock_github.return_value.get_repo.return_value = mock_repo
    # Test logic
```

### 5. Validate Both API and Database

```python
async def test_job_creation(async_client, db_session):
    # Test API response
    response = await async_client.post("/api/v1/jobs", json=data)
    assert response.status_code == 201

    # Verify database state
    job = await JobService(db_session).get_job(job_id)
    assert job.status == JobStatus.PENDING
```

## Debugging Failed Tests

### Verbose Output

```bash
pytest tests/integration/test_export_integration.py::test_name -vv
```

### Show Print Statements

```bash
pytest tests/integration/ -s
```

### Show Full Traceback

```bash
pytest tests/integration/ --tb=long
```

### Run with Debugger

```bash
pytest tests/integration/test_export_integration.py::test_name --pdb
```

### Log Output

```bash
pytest tests/integration/ --log-cli-level=DEBUG
```

## Performance Considerations

### Slow Tests

Tests marked with `@pytest.mark.slow` may take longer to execute:

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_websocket_handles_rapid_updates():
    # Long-running test
    pass
```

Skip slow tests during development:

```bash
pytest tests/integration/ -m "not slow"
```

### Database Isolation

Each test uses an isolated in-memory SQLite database for fast execution:

```python
@pytest.fixture(scope="function")
async def async_engine():
    """Create async engine for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    # ...
```

## Troubleshooting

### Import Errors

Ensure you're in the backend directory and have installed dependencies:

```bash
cd backend
pip install -r requirements-dev.txt
```

### Database Errors

Clear test database if corrupted:

```bash
rm test.db test.db-*
```

### Celery Task Errors

Ensure Celery is configured for testing in `conftest.py`:

```python
celery_config = {
    "broker_url": "memory://",
    "result_backend": "cache+memory://",
    "task_always_eager": True,
}
```

### WebSocket Connection Errors

Ensure FastAPI app is properly configured for testing in fixtures.

## Contributing

When adding new integration tests:

1. Create tests in appropriate file:
   - Export tests → `test_export_integration.py`
   - WebSocket tests → `test_websocket_integration.py`
   - Celery tests → `test_celery_integration.py`

2. Use existing fixtures from `conftest.py`

3. Add new fixtures to `conftest.py` if needed

4. Mark tests appropriately:
   - `@pytest.mark.integration` (required)
   - `@pytest.mark.slow` (if >1 second)
   - `@pytest.mark.asyncio` (for async tests)

5. Document complex test scenarios

6. Ensure tests are independent and idempotent

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Celery Testing](https://docs.celeryq.dev/en/stable/userguide/testing.html)
- [SARIF Specification](https://sarifweb.azurewebsites.net/)
