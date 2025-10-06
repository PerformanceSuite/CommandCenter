# Backend Test Suite

## Overview

Comprehensive test suite for the CommandCenter backend API, covering unit tests, integration tests, and achieving 80%+ code coverage.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── utils.py                 # Test utilities and helpers
├── unit/                    # Unit tests
│   ├── models/             # Database model tests
│   ├── schemas/            # Pydantic schema tests
│   └── services/           # Service layer tests
└── integration/            # Integration tests
    └── test_*_api.py       # API endpoint tests
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Run Specific Test Types
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Database tests only
pytest -m db
```

### Run Specific Test File
```bash
pytest tests/unit/models/test_repository.py -v
```

## Test Fixtures

### Database Fixtures
- `async_engine`: SQLAlchemy async engine with in-memory SQLite
- `async_session`: Async database session
- `db_session`: Database session with automatic rollback

### API Client Fixtures
- `async_client`: FastAPI test client with dependency injection

### Mock Data Fixtures
- `test_repository_data`: Sample repository data
- `test_technology_data`: Sample technology data
- `test_research_task_data`: Sample research task data
- `mock_github_service`: Mocked GitHub service
- `mock_rag_service`: Mocked RAG service

## Test Utilities

### Model Creation Helpers
```python
from tests.utils import (
    create_test_repository,
    create_test_technology,
    create_test_research_task,
    create_test_knowledge_entry
)

# Create test repository
repo = await create_test_repository(db_session, owner="test", name="repo")
```

### Mock Objects
```python
from tests.utils import MockGitHubRepo, MockGitHubCommit

# Create mock GitHub repository
mock_repo = MockGitHubRepo(name="testrepo", owner="testowner")
```

## Coverage Goals

- **Overall Coverage**: 80%+
- **Models**: 90%+
- **Services**: 85%+
- **Schemas**: 95%+
- **API Endpoints**: 80%+

## Test Categories

### Unit Tests (tests/unit/)
- **Models**: Test database models, relationships, validation
- **Schemas**: Test Pydantic models, validation, serialization
- **Services**: Test business logic, external API interactions

### Integration Tests (tests/integration/)
- **API Endpoints**: Test full request/response cycle
- **Database Transactions**: Test data persistence
- **Authentication**: Test auth flows
- **Error Handling**: Test error responses

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures for automatic cleanup
3. **Mocking**: Mock external services (GitHub, RAG)
4. **Async**: Use `pytest-asyncio` for async tests
5. **Markers**: Use pytest markers for test categorization

## CI/CD Integration

Tests run automatically on:
- Push to main branch
- Pull request creation
- Pre-commit hooks

Minimum coverage threshold: 80%

## Troubleshooting

### Database Errors
- Ensure async engine is properly initialized
- Check that Base.metadata is imported correctly

### Async Test Issues
- Verify `@pytest.mark.asyncio` decorator
- Check event loop configuration in conftest.py

### Import Errors
- Ensure PYTHONPATH includes project root
- Check that all __init__.py files exist
