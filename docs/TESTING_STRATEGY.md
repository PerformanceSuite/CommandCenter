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
