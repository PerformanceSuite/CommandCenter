# Testing Quickstart Guide

Quick guide to running and writing tests in CommandCenter.

## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [Running Tests](#running-tests)
3. [Writing Your First Test](#writing-your-first-test)
4. [Test Organization](#test-organization)
5. [Debugging Tests](#debugging-tests)
6. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 16** (for integration tests)
- **Redis 7** (for caching tests)
- **Playwright** (for E2E tests)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### E2E Setup

```bash
npx playwright install
```

### Database Setup

```bash
# Create test database
createdb commandcenter_test

# Run migrations
cd backend
alembic upgrade head
```

---

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/unit/models/test_technology.py

# Run specific test
pytest tests/unit/models/test_technology.py::test_technology_validation

# Run with coverage
pytest --cov=app --cov-report=html

# Run in verbose mode
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only security tests
pytest tests/security/

# Run only performance tests
pytest tests/performance/
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run specific test file
npm test -- Dashboard.test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Run specific component tests
npm test -- components/
```

### E2E Tests

```bash
# Run all E2E tests
npx playwright test

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test file
npx playwright test e2e/tests/smoke.spec.ts

# Run in debug mode
npx playwright test --debug

# Run specific browser
npx playwright test --project=chromium

# Generate HTML report
npx playwright show-report
```

### Docker Tests

```bash
# Run all tests in Docker
make test-docker

# Run backend tests in Docker
make test-docker-backend

# Run frontend tests in Docker
make test-docker-frontend
```

---

## Writing Your First Test

### Backend Unit Test Example

```python
# backend/tests/unit/services/test_my_service.py
import pytest
from app.services.my_service import MyService

def test_my_function_returns_expected_value():
    """Test that my_function returns the correct value."""
    service = MyService()
    result = service.my_function(input=42)

    assert result == 84
    assert isinstance(result, int)

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    service = MyService()
    result = await service.async_function()

    assert result is not None
```

### Frontend Component Test Example

```typescript
// frontend/src/__tests__/components/MyComponent.test.tsx
import { render, screen } from '@testing-library/react';
import { MyComponent } from '../../components/MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />);

    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<MyComponent onClick={handleClick} />);

    screen.getByRole('button').click();

    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### E2E Test Example

```typescript
// e2e/tests/my-flow.spec.ts
import { test, expect } from '@playwright/test';

test('user can complete workflow', async ({ page }) => {
  await page.goto('/');

  // Interact with page
  await page.click('button:has-text("Start")');

  // Assert outcome
  await expect(page.locator('.success-message')).toBeVisible();
});
```

---

## Test Organization

### File Structure

```
backend/tests/
├── unit/              # Fast, isolated tests
│   ├── models/
│   ├── services/
│   └── schemas/
├── integration/       # API and database tests
├── security/          # Security-focused tests
├── performance/       # Performance benchmarks
└── conftest.py        # Shared fixtures

frontend/src/__tests__/
├── components/        # Component tests
├── hooks/             # Hook tests
├── services/          # Service tests
└── utils/             # Utility tests

e2e/tests/            # End-to-end tests
```

### Naming Conventions

- **Test files**: `test_*.py` or `*.test.tsx`
- **Test functions**: `test_descriptive_name()`
- **Fixtures**: Clear, descriptive names
- **Test classes**: `TestClassName` (if using classes)

### When to Put Tests Where

- **Unit tests**: Pure functions, models, utilities
- **Integration tests**: API endpoints, database operations
- **E2E tests**: Critical user journeys only

---

## Debugging Tests

### Backend Debugging

**Using print statements:**
```python
def test_something():
    result = function()
    print(f"Result: {result}")  # Will show in test output
    assert result == expected
```

**Using breakpoints:**
```python
def test_something():
    import pdb; pdb.set_trace()  # Debugger stops here
    result = function()
    assert result == expected
```

**Running single test with output:**
```bash
pytest tests/unit/test_file.py::test_name -v -s
```

### Frontend Debugging

**Using console.log:**
```typescript
it('debugs component', () => {
  const { debug } = render(<MyComponent />);
  debug();  // Prints DOM
  console.log(screen.getByRole('button'));
});
```

**Using VS Code debugger:**
Add breakpoint in test, run with debugger attached.

### E2E Debugging

**Headed mode:**
```bash
npx playwright test --headed
```

**Debug mode (step through):**
```bash
npx playwright test --debug
```

**Playwright Inspector:**
```bash
PWDEBUG=1 npx playwright test
```

**Screenshots on failure:**
```typescript
test('my test', async ({ page }) => {
  await page.screenshot({ path: 'screenshot.png' });
});
```

---

## Troubleshooting

### Common Backend Issues

**Issue: Database connection errors**
```
Solution: Ensure PostgreSQL is running and test database exists
  createdb commandcenter_test
```

**Issue: Import errors**
```
Solution: Ensure virtual environment is activated and dependencies installed
  source venv/bin/activate
  pip install -r requirements.txt
```

**Issue: Tests hanging**
```
Solution: Use --timeout flag
  pytest --timeout=10
```

### Common Frontend Issues

**Issue: "Cannot find module"**
```
Solution: Clear cache and reinstall
  rm -rf node_modules package-lock.json
  npm install
```

**Issue: Tests timeout**
```
Solution: Increase timeout in test
  it('slow test', async () => {
    // ...
  }, 10000);  // 10 second timeout
```

### Common E2E Issues

**Issue: "Browser not found"**
```
Solution: Install Playwright browsers
  npx playwright install
```

**Issue: "Element not found"**
```
Solution: Use proper waits
  await page.waitForSelector('.my-element');
  await expect(page.locator('.my-element')).toBeVisible();
```

**Issue: Flaky tests**
```
Solution: Use waitFor and proper assertions
  await page.waitForLoadState('networkidle');
  await expect(element).toBeVisible();
```

---

## Best Practices

### General
- ✅ Write tests before fixing bugs (regression tests)
- ✅ One assertion per test (when possible)
- ✅ Clear, descriptive test names
- ✅ Use fixtures for common setup
- ✅ Clean up after tests (fixtures handle this)

### Backend
- ✅ Use async fixtures for async tests
- ✅ Mock external APIs
- ✅ Use factories for test data
- ✅ Isolate database tests (transactions)

### Frontend
- ✅ Test user behavior, not implementation
- ✅ Use userEvent over fireEvent
- ✅ Query by accessibility roles
- ✅ Avoid testing library internals

### E2E
- ✅ Test critical paths only
- ✅ Use page object pattern
- ✅ Avoid hard waits (use waitFor)
- ✅ Keep tests independent

---

## Quick Reference

```bash
# Backend
pytest                          # All tests
pytest tests/unit              # Unit only
pytest -k "technology"         # Tests matching keyword
pytest --lf                    # Last failed
pytest --ff                    # Failed first
pytest -x                      # Stop on first failure

# Frontend
npm test                       # All tests
npm test -- --watch           # Watch mode
npm test -- Dashboard         # Specific test
npm test -- --coverage        # With coverage

# E2E
npx playwright test           # All E2E
npx playwright test --headed  # See browser
npx playwright test --debug   # Debug mode
npx playwright show-report    # View report
```

---

**Need more help?** See [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) for testing philosophy and [CONTRIBUTING.md](./CONTRIBUTING.md) for PR requirements.
