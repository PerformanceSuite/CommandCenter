# Hub Testing Guide

## Test Organization

```
hub/
├── backend/tests/
│   ├── unit/              # Fast, isolated tests
│   │   ├── test_router_tasks.py
│   │   └── test_tasks_orchestration.py
│   └── integration/       # Tests with real Redis/Celery
│       ├── conftest.py
│       └── test_background_tasks.py
├── frontend/src/__tests__/
│   ├── components/        # React component tests
│   ├── hooks/            # Custom hook tests
│   └── services/         # API service tests
└── scripts/
    └── e2e-test.sh       # Full stack E2E test
```

## Running Tests

### Backend Unit Tests

**Prerequisites:** None (all mocked)

```bash
cd hub/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_router_tasks.py -v

# Run specific test
pytest tests/unit/test_router_tasks.py::TestStartProjectEndpoint::test_start_project_returns_task_id -v

# With coverage
pytest tests/unit/ --cov=app --cov-report=html
open htmlcov/index.html
```

**Expected:** All 10 tests pass

### Backend Integration Tests

**Prerequisites:** Redis running on localhost:6379

```bash
# Start Redis
docker run -d --name test-redis -p 6379:6379 redis:7-alpine

# Run integration tests (fast subset)
pytest tests/integration/ -v -m "not slow"

# Run all integration tests (includes 30-min Dagger tests)
pytest tests/integration/ -v

# Stop Redis
docker stop test-redis && docker rm test-redis
```

**Expected:** 4-5 tests pass (slow tests skipped)

### Frontend Tests

**Prerequisites:** None (vitest handles mocking)

```bash
cd hub/frontend
npm install

# Run all tests
npm test

# Watch mode (re-run on changes)
npm run test:watch

# UI mode (interactive)
npm run test:ui

# Coverage
npm run test:coverage
open coverage/index.html
```

**Expected:** All 56 tests pass

### End-to-End Test

**Prerequisites:** Docker + Docker Compose

```bash
cd hub
./scripts/e2e-test.sh
```

**Expected:** All 6 checks pass (Redis, Worker, Backend, Task submission, Polling, Flower)

## Test Categories

### Unit Tests (Backend)

**Purpose:** Test individual functions/classes in isolation

**Characteristics:**
- Fast (< 1 second each)
- No external dependencies
- All I/O mocked
- High coverage target (> 80%)

**Example:**
```python
@patch('app.tasks.orchestration.OrchestrationService')
def test_start_project_success(mock_service):
    result = start_project_task.apply(args=[1]).result
    assert result["success"] is True
```

### Integration Tests (Backend)

**Purpose:** Test interaction between components with real infrastructure

**Characteristics:**
- Slower (2-5 seconds each)
- Requires Redis
- Real Celery task execution
- Medium coverage target (> 60%)

**Example:**
```python
def test_task_submission_returns_id():
    result = start_project_task.delay(project_id=999)
    assert result.id is not None
    result.revoke(terminate=True)
```

### Component Tests (Frontend)

**Purpose:** Test React components render correctly

**Characteristics:**
- Fast (10-50ms each)
- Uses @testing-library/react
- Mocked API calls
- Focus on user interactions

**Example:**
```typescript
it('start button triggers start action', () => {
  render(<ProjectCard project={mockProject} />);
  fireEvent.click(screen.getByRole('button', { name: /start/i }));
  expect(mockStartProject).toHaveBeenCalledWith(mockProject.id);
});
```

### Hook Tests (Frontend)

**Purpose:** Test custom React hooks

**Characteristics:**
- Fast (with fake timers)
- Uses @testing-library/react-hooks
- Tests state changes over time

**Example:**
```typescript
it('should poll every 2 seconds', async () => {
  vi.useFakeTimers();
  renderHook(() => useTaskStatus(taskId));

  vi.advanceTimersByTime(2000);
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));

  vi.useRealTimers();
});
```

## Writing Tests

### Test-Driven Development (TDD)

**Process:**
1. Write failing test
2. Run test (verify it fails)
3. Write minimal code to pass
4. Run test (verify it passes)
5. Refactor
6. Commit

**Example:**
```bash
# 1. Write test
cat > tests/unit/test_new_feature.py << EOF
def test_new_feature():
    result = new_function(42)
    assert result == 84
EOF

# 2. Run (should fail)
pytest tests/unit/test_new_feature.py -v
# Expected: FAILED - function not found

# 3. Implement
cat > app/new_feature.py << EOF
def new_function(x):
    return x * 2
EOF

# 4. Run (should pass)
pytest tests/unit/test_new_feature.py -v
# Expected: PASSED

# 5. Commit
git add tests/unit/test_new_feature.py app/new_feature.py
git commit -m "feat: add new_function with doubling logic"
```

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Set up test data and mocks
    mock_service = MagicMock()
    mock_service.get_data.return_value = {"value": 42}

    # Act - Execute the code under test
    result = function_to_test(mock_service)

    # Assert - Verify results
    assert result == 42
    mock_service.get_data.assert_called_once()
```

### Mocking Best Practices

**DO:**
- Mock external dependencies (API, DB, filesystem)
- Use `@patch` decorator for clean syntax
- Verify mock calls with assertions
- Use `MagicMock` for complex objects

**DON'T:**
- Mock the code under test
- Over-mock (keep tests realistic)
- Forget to clean up mocks
- Share mocks between tests

## Debugging Tests

### Backend

```bash
# Run with debugger
pytest tests/unit/test_file.py::test_name --pdb

# Verbose output
pytest tests/unit/test_file.py -vv

# Print statements (use -s)
pytest tests/unit/test_file.py -s

# Show locals on failure
pytest tests/unit/test_file.py -l
```

### Frontend

```bash
# Debug mode
npm run test:ui

# Single test file
npm test -- src/__tests__/components/ProjectCard.test.tsx

# Watch specific file
npm run test:watch -- ProjectCard
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Hub Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd hub/backend && pip install -r requirements.txt -r requirements-dev.txt
      - run: cd hub/backend && pytest tests/unit/ -v
      - run: cd hub/backend && pytest tests/integration/ -v -m "not slow"

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd hub/frontend && npm install
      - run: cd hub/frontend && npm test
```

## Test Maintenance

### Regular Tasks

**After adding feature:**
- Write unit tests (> 80% coverage)
- Write integration test (happy path)
- Update E2E test if needed

**Before merging:**
- All tests pass locally
- Coverage meets targets
- No skipped/disabled tests (unless documented)

**Monthly:**
- Review slow tests (> 1s unit, > 10s integration)
- Remove obsolete tests
- Update mocks for API changes

### Coverage Targets

| Test Type | Target Coverage |
|-----------|----------------|
| Backend Unit | > 80% |
| Backend Integration | > 60% |
| Frontend Components | > 75% |
| Frontend Hooks | > 85% |

**Check coverage:**
```bash
# Backend
cd hub/backend && pytest --cov=app --cov-report=term-missing

# Frontend
cd hub/frontend && npm run test:coverage
```

## Known Issues

### Slow Tests

**Symptom:** Tests timeout or take > 5 seconds

**Causes:**
- Real network calls (should be mocked)
- Real delays (use fake timers)
- Large data sets (use smaller fixtures)

**Fix:**
- Use `vi.useFakeTimers()` for time-dependent tests
- Mock all network calls
- Reduce test data size

### Flaky Tests

**Symptom:** Tests pass sometimes, fail others

**Causes:**
- Race conditions
- Shared state between tests
- Timing dependencies

**Fix:**
- Use `waitFor()` instead of fixed delays
- Clean up state in `afterEach()`
- Mock time-dependent code

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Celery Testing](https://docs.celeryq.dev/en/stable/userguide/testing.html)
