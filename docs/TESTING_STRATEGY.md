# Testing Strategy

CommandCenter testing philosophy, coverage goals, and best practices.

## Test Pyramid

We follow the test pyramid principle: many unit tests, some integration tests, few E2E tests.

```
           /\
          /15\ E2E (10% of tests)
         /----\
        / 58  \ Integration (15% of tests)
       /--------\
      /   290   \ Unit (75% of tests)
     /------------\
```

**Current Status:**
- Unit tests: ~290 tests (75%)
- Integration tests: ~58 tests (15%)
- E2E tests: ~40 tests (10%)
- **Total**: ~390 tests

---

## When to Write Each Type

### Unit Tests (75% of suite)

**What:** Test individual functions, methods, classes in isolation

**When to write:**
- Pure functions
- Business logic
- Data transformations
- Validation logic
- Utility functions

**Characteristics:**
- Fast (<1ms each)
- No external dependencies
- Mock everything external
- High volume

**Example scenarios:**
- Model validation
- Service logic
- Schema transformations
- Helper functions

**Code Example:**

```python
# Unit Test - Tests business logic in isolation
import pytest
from app.services.technology_service import TechnologyService
from app.models.technology import Technology

@pytest.mark.unit
def test_calculate_relevance_score():
    """Unit test: Pure function, no database, no external calls"""
    service = TechnologyService()

    # Test with high adoption
    score = service.calculate_relevance(
        adoption_rate=90,
        community_activity=85,
        maturity=8
    )

    assert score >= 80  # High relevance
    assert isinstance(score, int)

    # Test with low adoption
    score = service.calculate_relevance(
        adoption_rate=10,
        community_activity=15,
        maturity=3
    )

    assert score <= 30  # Low relevance
```

### Integration Tests (15% of suite)

**What:** Test interactions between components

**When to write:**
- API endpoints
- Database operations
- External service calls
- Multi-component workflows

**Characteristics:**
- Moderate speed (~100ms each)
- Real database/services
- End-to-end flows
- Moderate volume

**Example scenarios:**
- CRUD API endpoints
- Repository sync flows
- Knowledge base queries
- Authentication flows

**Code Example:**

```python
# Integration Test - Tests API endpoint with real database
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_technology_endpoint(db_session):
    """Integration test: Real database, full HTTP request/response"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make real HTTP POST request
        response = await client.post("/api/v1/technologies", json={
            "title": "FastAPI",
            "domain": "web-frameworks",
            "vendor": "Tiangolo",
            "status": "production",
            "relevance": 95
        })

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "FastAPI"
        assert data["id"] is not None

        # Verify data persisted in database
        from sqlalchemy import select
        from app.models.technology import Technology

        result = await db_session.execute(
            select(Technology).where(Technology.title == "FastAPI")
        )
        tech = result.scalar_one()
        assert tech.title == "FastAPI"
        assert tech.relevance == 95
```

### E2E Tests (10% of suite)

**What:** Test complete user journeys through UI

**When to write:**
- Critical user paths only
- Happy path scenarios
- Major feature workflows

**Characteristics:**
- Slow (~5-10s each)
- Full stack
- Browser automation
- Low volume

**Example scenarios:**
- User login + dashboard
- Create technology workflow
- Research task management
- Knowledge base search

**Code Example:**

```typescript
// E2E Test - Tests complete user journey through browser
import { test, expect } from '@playwright/test';

test('user can create and view technology in radar', async ({ page }) => {
  // E2E test: Full user journey from login to viewing result

  // Navigate to app
  await page.goto('http://localhost:3000');

  // Navigate to Technology Radar
  await page.click('text=Technology Radar');
  await expect(page).toHaveURL(/.*radar/);

  // Click Add Technology button
  await page.click('button:has-text("Add Technology")');

  // Fill out form (real UI interaction)
  await page.fill('[name="title"]', 'React 19');
  await page.selectOption('[name="domain"]', 'frontend');
  await page.fill('[name="vendor"]', 'Meta');
  await page.selectOption('[name="status"]', 'production');
  await page.fill('[name="relevance"]', '95');

  // Submit form
  await page.click('button:has-text("Create")');

  // Verify success (waits for UI update)
  await expect(page.locator('text=React 19')).toBeVisible();

  // Verify it appears in the radar chart
  const radarChart = page.locator('[data-testid="radar-chart"]');
  await expect(radarChart).toContainText('React 19');
});
```

---

## Coverage Goals

### Backend

**Target:** 80%+ coverage (enforced in CI)

**Priority areas:**
- Services: 90%+
- Models: 85%+
- Routers: 80%+
- Utils: 95%+

**Excluded:**
- Test files
- Migration scripts
- Configuration files

### Frontend

**Target:** 60%+ coverage (enforced in CI)

**Priority areas:**
- Components: 70%+
- Hooks: 80%+
- Services: 85%+
- Utils: 90%+

**Excluded:**
- Test files
- Storybook stories
- Type definitions

### Critical Paths

**Target:** 100% coverage

Critical paths must have both integration AND E2E coverage:
- User authentication
- Data CRUD operations
- Security boundaries
- Error handling

---

## Security Testing Approach

### Required Security Tests

1. **Project Isolation** (MANDATORY)
   - User A cannot access User B's data
   - Cross-project queries blocked
   - Database filters by project_id

2. **JWT Validation** (MANDATORY)
   - Tampered tokens rejected
   - Expired tokens rejected
   - Invalid format rejected

3. **Input Validation**
   - SQL injection prevention
   - XSS protection
   - CSRF tokens

4. **RBAC (Role-Based Access Control)**
   - Permission checks
   - Owner vs member access
   - Admin capabilities

### Security Test Locations

```
backend/tests/security/
├── test_project_isolation.py   # Data isolation
├── test_jwt_security.py         # Token validation
├── test_sql_injection.py        # SQL injection
├── test_xss.py                  # XSS protection
└── test_rbac_basic.py           # Permissions
```

---

## Performance Testing Approach

### N+1 Query Detection

**Goal:** Prevent inefficient database queries

**Approach:**
- Use query counter fixture
- Assert query count ≤ threshold
- Flag tests with >3 queries

**Example:**
```python
def test_no_n_plus_one(query_counter):
    response = client.get("/api/v1/technologies")
    assert len(query_counter) <= 3  # 1 main + 2 joins
```

### API Response Time Benchmarks

**Targets:**
- GET endpoints: <500ms
- POST endpoints: <300ms
- Complex queries: <1500ms

**Approach:**
- Time each request
- Assert duration < threshold
- Track trends over time

### Load Testing

**Not in unit tests** - use K6 or Locust separately

---

## CI/CD Integration

### CI Pipeline

```yaml
1. Smoke tests (<5 min)        # Fast feedback
2. Unit tests (parallel)        # Bulk of tests
3. Integration tests (sharded)  # Database tests
4. E2E tests (sharded 4-way)   # Browser tests
5. Performance check            # Regression detection
```

### Test Sharding

- **E2E**: 4-way parallel (30min → 8min)
- **Integration**: By category (api, services, db)
- **Unit**: Single job (fast enough)

### Coverage Enforcement

```yaml
coverage:
  backend:
    target: 80%
    fail-below: true
  frontend:
    target: 60%
    fail-below: true
```

#### Codecov Configuration

Coverage tracking is managed via `.codecov.yml` in the repository root:

```yaml
# .codecov.yml - Codecov configuration
coverage:
  status:
    project:
      default:
        target: 80%           # Overall project coverage target
        threshold: 1%         # Allow 1% drop without failing
    patch:
      default:
        target: 70%           # New code must be 70%+ covered
        threshold: 0%         # No drop allowed for new code

comment:
  require_changes: true       # Only comment when coverage changes
  behavior: default           # Show coverage summary
  layout: "diff, flags, files"

ignore:
  - "**/__pycache__"
  - "**/node_modules"
  - "**/dist"
  - "**/build"
  - "backend/alembic/versions/*"    # Migration files
  - "backend/app/models/__init__.py" # Model imports
  - "**/conftest.py"                # Test fixtures
  - "**/*_test.py"                  # Test files themselves
  - "**/*.test.ts"
  - "**/*.spec.ts"
```

**Key Settings:**
- **project.target**: Overall repository coverage target (80%)
- **patch.target**: Coverage required for new code in PRs (70%)
- **threshold**: Acceptable coverage drop (1% for project, 0% for patches)
- **ignore**: Files excluded from coverage calculation

**Badge:** Add to README.md:
```markdown
[![codecov](https://codecov.io/gh/YOUR_ORG/CommandCenter/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_ORG/CommandCenter)
```

### PR Requirements

- All tests must pass
- Coverage must meet targets
- No performance regressions
- Security tests must pass (cannot skip)

---

## Test Quality Standards

### Good Test Characteristics

✅ **Independent** - Can run in any order
✅ **Repeatable** - Same result every time
✅ **Fast** - Runs in milliseconds (unit)
✅ **Isolated** - No shared state
✅ **Clear** - Obvious what's being tested

### Bad Test Smells

❌ **Flaky** - Passes/fails randomly
❌ **Slow** - Takes seconds (unit test)
❌ **Dependent** - Requires specific order
❌ **Opaque** - Unclear what's tested
❌ **Brittle** - Breaks on unrelated changes

### Test Naming

**Good:**
```python
def test_user_cannot_access_other_project_technologies():
    # Clear what's being tested
```

**Bad:**
```python
def test_tech():
    # Unclear, vague
```

---

## Common Patterns

### Using Fixtures

```python
@pytest.fixture
def sample_technology(db_session):
    """Create sample technology for testing."""
    tech = Technology(title="Python", domain="backend")
    db_session.add(tech)
    db_session.commit()
    return tech

def test_with_fixture(sample_technology):
    assert sample_technology.title == "Python"
```

### Using Factories

```python
def test_with_factory(db_session):
    tech = TechnologyFactory.create(title="Python")
    assert tech.id is not None
```

### Mocking External Services

```python
def test_github_api(mocker):
    mock_github = mocker.patch('app.services.github_service.Github')
    mock_github.return_value.get_repo.return_value = MockRepo()

    service = GitHubService()
    result = service.get_repository("owner/repo")

    assert result is not None
```

---

## Performance Best Practices

Fast tests = fast development cycles. Follow these practices to keep test suite performant.

### Unit Test Performance

**Target:** <1ms per test

```python
# ❌ Bad - Slow unit test (100ms+)
@pytest.mark.unit
def test_calculate_score(db_session):  # Don't use database in unit tests!
    tech = Technology(title="Python")
    db_session.add(tech)
    db_session.commit()
    assert tech.calculate_score() > 0

# ✅ Good - Fast unit test (<1ms)
@pytest.mark.unit
def test_calculate_score():
    tech = Technology(title="Python")
    assert tech.calculate_score() > 0  # Pure function, no I/O
```

**Tips:**
- No database, no file I/O, no network
- Mock all external dependencies
- Use in-memory objects
- Avoid `time.sleep()` - use fake timers

### Integration Test Performance

**Target:** ~100ms per test

```python
# ❌ Bad - Slow integration test (2000ms+)
@pytest.mark.integration
async def test_bulk_create_technologies(db_session):
    # Creating 100 records one at a time
    for i in range(100):
        tech = Technology(title=f"Tech {i}")
        db_session.add(tech)
        await db_session.commit()  # 100 round trips!

    count = await db_session.execute(select(func.count(Technology.id)))
    assert count.scalar() == 100

# ✅ Good - Fast integration test (~100ms)
@pytest.mark.integration
async def test_bulk_create_technologies(db_session):
    # Bulk insert in single transaction
    technologies = [Technology(title=f"Tech {i}") for i in range(100)]
    db_session.add_all(technologies)
    await db_session.commit()  # Single round trip

    count = await db_session.execute(select(func.count(Technology.id)))
    assert count.scalar() == 100
```

**Tips:**
- Use database transactions (rollback after test)
- Bulk operations instead of loops
- Share expensive fixtures (database, API clients)
- Minimize data created - test with 2-3 records, not 100

### E2E Test Performance

**Target:** <10s per test

```typescript
// ❌ Bad - Slow E2E test (30s+)
test('user flow', async ({ page }) => {
  await page.goto('/');
  await page.waitForTimeout(5000);  // Arbitrary wait
  await page.click('button');
  await page.waitForTimeout(3000);  // More arbitrary waits
  await page.fill('input', 'value');
  await page.waitForTimeout(2000);
  // ...slow and flaky
});

// ✅ Good - Fast E2E test (~5s)
test('user flow', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');  // Wait for real condition
  await page.click('button');
  await expect(page.locator('.modal')).toBeVisible();  // Explicit wait
  await page.fill('input', 'value');
  await expect(page.locator('.success')).toBeVisible();
  // ...fast and reliable
});
```

**Tips:**
- Wait for conditions, not arbitrary timeouts
- Use `waitForLoadState()`, `waitForSelector()`
- Minimize navigation - test multiple things in one journey
- Use Playwright's auto-waiting features
- Parallelize with test sharding

### Fixture Performance

```python
# ❌ Bad - Expensive fixture created every test
@pytest.fixture
def db_with_data(db_session):
    # Recreates 1000 records for EVERY test!
    for i in range(1000):
        db_session.add(Technology(title=f"Tech {i}"))
    db_session.commit()
    return db_session

# ✅ Good - Shared expensive fixture
@pytest.fixture(scope="session")
def db_with_data(db_session_factory):
    # Created once, shared across all tests
    session = db_session_factory()
    for i in range(1000):
        session.add(Technology(title=f"Tech {i}"))
    session.commit()
    return session
```

**Tips:**
- Use `scope="session"` for expensive setup
- Use `scope="module"` for moderately expensive setup
- Default `scope="function"` only when needed
- Clean up between tests if sharing fixtures

### Monitoring Test Performance

```bash
# Find slowest tests
pytest --durations=10

# Show tests slower than 1s
pytest --durations-min=1.0

# Profile specific test
pytest tests/test_slow.py --profile

# Track over time
pytest --durations=0 --durations-min=0.1 > test-timings.txt
```

**Performance Budget:**
- Unit test suite: <30s total
- Integration test suite: <5min total
- E2E test suite: <10min total (with sharding)
- Full CI pipeline: <25min total

**Red Flags:**
- Unit test >100ms → Move to integration
- Integration test >5s → Optimize or split
- E2E test >30s → Too much in one test, split up
- Test suite doubling time → Time for optimization sprint

---

## Continuous Improvement

### Weekly
- Review flaky tests
- Update slow test report
- Check coverage trends

### Monthly
- Review test pyramid ratio
- Update performance baselines
- Refactor common patterns

### Quarterly
- Major test refactoring
- Tool/framework updates
- Strategy refinement

---

## Resources

- [Testing Quickstart](./TESTING_QUICKSTART.md) - How to run tests
- [Contributing Guide](./CONTRIBUTING.md#testing-requirements) - PR requirements
- [CI Workflows](./CI_WORKFLOWS.md) - CI/CD pipeline details
- [pytest docs](https://docs.pytest.org/)
- [Playwright docs](https://playwright.dev/)
- [React Testing Library](https://testing-library.com/react)
