# CommandCenter Hub Testing Guide

This document describes the testing infrastructure and practices for the CommandCenter Hub, the meta-application that manages multiple CommandCenter instances using Dagger SDK.

## Overview

The Hub testing strategy focuses on:
- **Backend**: Unit and integration tests for project management and Dagger orchestration
- **Frontend**: Component and service tests for the React UI
- **Mocking Strategy**: All Dagger SDK calls are mocked - tests never actually start containers

## Backend Testing

### Test Structure

```
hub/backend/tests/
├── conftest.py                 # Fixtures and test utilities
├── utils/
│   ├── factories.py            # Data factories for test objects
│   └── helpers.py              # Helper functions
├── unit/
│   ├── models/
│   │   └── test_project.py     # Project model tests (8 tests)
│   └── services/
│       └── test_orchestration_service.py  # Orchestration tests (14 tests)
└── integration/
    └── test_projects_api.py    # API integration tests
```

### Running Backend Tests

```bash
cd hub/backend

# Run all tests
DATABASE_URL="sqlite+aiosqlite:///:memory:" python3 -m pytest tests/ -v

# Run unit tests only
DATABASE_URL="sqlite+aiosqlite:///:memory:" python3 -m pytest tests/unit/ -v

# Run with coverage
DATABASE_URL="sqlite+aiosqlite:///:memory:" python3 -m pytest tests/ --cov=app --cov-report=html

# Run specific test file
DATABASE_URL="sqlite+aiosqlite:///:memory:" python3 -m pytest tests/unit/models/test_project.py -v
```

### Key Testing Concepts

#### 1. Database Fixtures

Tests use in-memory SQLite for isolation and speed:

```python
@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create async database session for testing"""
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
```

#### 2. Mocking Dagger SDK

**Critical**: Tests NEVER actually call Dagger or start containers. All Dagger operations are mocked:

```python
@pytest.fixture
def mock_dagger_stack():
    """Mock CommandCenterStack for testing orchestration service"""
    stack = AsyncMock()
    stack.__aenter__ = AsyncMock(return_value=stack)
    stack.__aexit__ = AsyncMock(return_value=None)
    stack.start = AsyncMock(return_value={
        "success": True,
        "message": "Stack started successfully",
        "services": {...}
    })
    return stack
```

Usage in tests:

```python
with patch(
    "app.services.orchestration_service.CommandCenterStack",
    return_value=mock_stack,
):
    result = await service.start_project(project_id)
```

#### 3. Port Conflict Simulation

Tests can simulate port conflicts without actually binding ports:

```python
def create_port_conflict_mock(conflicting_ports: list[int]):
    """Mock socket to simulate port conflicts"""
    def connect_ex_side_effect(address):
        host, port = address
        return 0 if port in conflicting_ports else 1  # 0 = in use

    mock_sock = MagicMock()
    mock_sock.connect_ex.side_effect = connect_ex_side_effect
    return mock_sock
```

### Test Categories

#### Unit Tests - Models (8 tests)

Tests for `app.models.Project`:
- Project creation and validation
- Unique constraints (name, slug, ports)
- Status transitions
- Default values and timestamps
- Query filtering

#### Unit Tests - Services (14 tests)

Tests for `app.services.orchestration_service.OrchestrationService`:
- Project start/stop/restart lifecycle
- Port conflict detection
- Active stack registry management
- Error handling (Dagger failures, invalid projects)
- Status queries
- Timestamp updates

**Key principle**: These tests verify orchestration LOGIC, not Dagger itself.

### Test Utilities

#### Factories (`tests/utils/factories.py`)

Reusable factory functions for creating test data:

```python
ProjectFactory.create_project(
    name="TestProject",
    status="running",
    backend_port=8010
)

PortSetFactory.create_port_set(
    backend=8010,
    frontend=3010
)
```

#### Helpers (`tests/utils/helpers.py`)

Utility functions:
- `create_mock_dagger_response()` - Mock Dagger operation results
- `create_mock_dagger_stack()` - Full mock stack with lifecycle
- `create_port_conflict_mock()` - Simulate port conflicts
- `create_test_project()` - Quick DB project creation

## Frontend Testing

### Test Structure

```
hub/frontend/src/
├── test-utils/
│   ├── setup.ts               # Vitest configuration
│   └── mocks.ts               # Mock data and helpers
└── __tests__/
    ├── components/
    │   ├── ProjectCard.test.tsx     # ProjectCard tests (13 tests)
    │   └── Dashboard.test.tsx       # Dashboard tests (4 tests)
    └── services/
        └── api.test.ts              # API client tests (14 tests)
```

### Running Frontend Tests

```bash
cd hub/frontend

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

### Key Testing Concepts

#### 1. Test Setup (`test-utils/setup.ts`)

Configures React Testing Library and Vitest:

```typescript
import '@testing-library/jest-dom';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    // ... event handlers
  }),
});
```

#### 2. Mock Data (`test-utils/mocks.ts`)

Centralized mock data for consistent testing:

```typescript
export const mockProjects: Project[] = [
  {
    id: 1,
    name: 'TestProject1',
    status: 'stopped',
    // ...
  },
  // ...
];

export const mockStats: ProjectStats = {
  total_projects: 3,
  running: 1,
  stopped: 1,
  errors: 1,
};
```

#### 3. Component Testing

Tests use `@testing-library/react` for user-centric testing:

```typescript
it('start button triggers start action', async () => {
  const { api } = await import('../../services/api');
  const project = createMockProject({ status: 'stopped', id: 1 });

  render(<ProjectCard project={project} onDelete={mockOnDelete} />);

  const startButton = screen.getByRole('button', { name: /start/i });
  await userEvent.click(startButton);

  await waitFor(() => {
    expect(api.orchestration.start).toHaveBeenCalledWith(1);
  });
});
```

#### 4. API Mocking

Mock `fetch` for API tests:

```typescript
beforeEach(() => {
  global.fetch = vi.fn();
});

it('list() fetches all projects', async () => {
  (global.fetch as any).mockResolvedValueOnce(
    createMockResponse(mockProjects)
  );

  const result = await projectsApi.list();

  expect(global.fetch).toHaveBeenCalledWith(
    '/api/projects/',
    expect.objectContaining({
      headers: expect.objectContaining({
        'Content-Type': 'application/json',
      }),
    })
  );
});
```

### Test Categories

#### Component Tests - ProjectCard (13 tests)

- Renders project information correctly
- Displays status indicators (stopped, running, error)
- Start/stop/open button interactions
- Delete confirmation workflow
- Error state handling

#### Component Tests - Dashboard (4 tests)

- Loading state display
- Project list rendering
- Empty state display
- API call verification

#### Service Tests - API Client (14 tests)

- Projects API (list, get, create, delete, stats)
- Orchestration API (start, stop, restart, status, health)
- Filesystem API (getHome, browse)
- Error handling

## Test Coverage

### Current Coverage

**Backend**: 27 tests passing
- Models: 8 tests
- Services: 14 tests
- Existing tests: 5 tests

**Frontend**: 31 tests passing
- Components: 17 tests
- Services: 14 tests

**Total**: 58 tests

### What's Tested

✅ Project model validation and constraints
✅ Orchestration service logic (start/stop/restart)
✅ Port conflict detection
✅ Active stack registry management
✅ Project status transitions
✅ React component rendering
✅ User interactions (clicks, form submissions)
✅ API client methods
✅ Error handling

### What's NOT Tested (By Design)

❌ Actual Dagger container operations (mocked)
❌ Real Docker container lifecycle
❌ Network I/O to running containers
❌ Database migrations (tested separately)

## Common Patterns

### Testing Async Operations

```python
@pytest.mark.asyncio
async def test_async_operation(db_session):
    """Test async database operation"""
    service = ProjectService(db_session)
    result = await service.list_projects()
    assert len(result) >= 0
```

### Testing Error Conditions

```python
async def test_start_project_port_conflict(db_session, sample_project):
    """Test that port conflicts are detected"""
    service = OrchestrationService(db_session)

    conflicting_ports = [sample_project.frontend_port]
    mock_sock = create_port_conflict_mock(conflicting_ports)

    with patch("socket.socket", return_value=mock_sock):
        with pytest.raises(RuntimeError, match="ports are already in use"):
            await service.start_project(sample_project.id)
```

### Testing React User Events

```typescript
it('delete button shows confirmation dialog', async () => {
  const project = createMockProject({ status: 'stopped' });
  render(<ProjectCard project={project} onDelete={mockOnDelete} />);

  const deleteButton = screen.getByRole('button', { name: /delete/i });
  await userEvent.click(deleteButton);

  expect(screen.getByText(/delete files too/i)).toBeInTheDocument();
});
```

## Debugging Tests

### Backend

```bash
# Run single test with verbose output
DATABASE_URL="sqlite+aiosqlite:///:memory:" python3 -m pytest tests/unit/models/test_project.py::test_project_creation -vv

# Show print statements
DATABASE_URL="sqlite+aiosqlite:///:memory:" python3 -m pytest tests/unit/ -s

# Drop into debugger on failure
DATABASE_URL="sqlite+aiosqlite:///:memory:" python3 -m pytest tests/unit/ --pdb
```

### Frontend

```bash
# Run single test
npm test -- ProjectCard

# Debug mode
npm test -- --inspect --inspect-brk

# Update snapshots (if using)
npm test -- -u
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Hub Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd hub/backend
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          cd hub/backend
          DATABASE_URL="sqlite+aiosqlite:///:memory:" pytest tests/ -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd hub/frontend
          npm install
      - name: Run tests
        run: |
          cd hub/frontend
          npm test
```

## Best Practices

### DO

✅ Mock all Dagger SDK calls
✅ Use in-memory database for speed
✅ Test business logic, not external libraries
✅ Write descriptive test names
✅ Use factories for test data
✅ Test error conditions
✅ Keep tests isolated and independent

### DON'T

❌ Start actual Docker containers in tests
❌ Rely on external services
❌ Test implementation details
❌ Share mutable state between tests
❌ Write tests that depend on execution order
❌ Skip error path testing

## Troubleshooting

### "Module not found" errors

Ensure you're in the correct directory and dependencies are installed:

```bash
# Backend
cd hub/backend
pip install -r requirements-dev.txt

# Frontend
cd hub/frontend
npm install
```

### "Database locked" errors

Using in-memory SQLite avoids this, but if using file-based SQLite:

```python
# In conftest.py, use :memory:
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
```

### Async test warnings

Ensure `@pytest.mark.asyncio` decorator is present:

```python
@pytest.mark.asyncio
async def test_my_async_function():
    result = await my_async_function()
    assert result is not None
```

### Frontend mock hoisting issues

Keep mock definitions inline in `vi.mock()` calls:

```typescript
// ❌ DON'T: External reference
const mockApi = { list: vi.fn() };
vi.mock('../../services/api', () => ({ api: mockApi }));

// ✅ DO: Inline definition
vi.mock('../../services/api', () => ({
  api: {
    list: vi.fn(),
  },
}));
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

## Summary

The Hub testing infrastructure provides comprehensive coverage of project management and orchestration logic while avoiding expensive container operations. By mocking Dagger SDK calls, tests run fast and reliably without requiring Docker or external services.

**Key Stats**:
- 58 total tests
- Backend: 27 tests (models, services, existing)
- Frontend: 31 tests (components, services)
- All Dagger operations mocked
- No actual containers started
- Fast execution (< 1 second total)
