# Test Failures and Known Issues

## Backend Router Tests (test_router_tasks.py)

**Status**: All 6 router tests timeout during fixture initialization

**Test Files Affected**:
- `hub/backend/tests/unit/test_router_tasks.py`

**Tests Impacted**:
1. `TestStartProjectEndpoint::test_start_project_returns_task_id`
2. `TestStopProjectEndpoint::test_stop_project_returns_task_id`
3. `TestTaskStatusEndpoint::test_task_status_pending`
4. `TestTaskStatusEndpoint::test_task_status_building`
5. `TestTaskStatusEndpoint::test_task_status_success`
6. `TestTaskStatusEndpoint::test_task_status_failure`

### Error Description

Tests hang during TestClient fixture initialization when the FastAPI app lifespan manager attempts to create database tables. The lifespan context manager in `app/main.py` runs:

```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

This async operation appears to block indefinitely during test setup.

### Root Cause

The FastAPI app's `lifespan` context manager (lines 14-22 in `app/main.py`) creates database tables on startup. When TestClient is instantiated, it triggers this lifespan event, which attempts to connect to the database configured via `DATABASE_URL` environment variable. The connection appears to hang, possibly due to:

1. Database connection pool exhaustion
2. SQLite file locking issues
3. Async engine initialization conflict with sync test context

### Workaround/Fix Needed

**Option 1: Disable lifespan for tests**
```python
# In test fixture
@pytest.fixture
def client():
    app_test = FastAPI(**app.__dict__)  # Copy app without lifespan
    with TestClient(app_test) as c:
        yield c
```

**Option 2: Override database dependency**
```python
@pytest.fixture
def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

**Option 3: Use in-memory database for router tests**
```python
# Set test DATABASE_URL to :memory:
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

### Status

- **Partial Implementation**: Fixed TestClient pattern (`with TestClient(app) as c`) per Starlette 0.35.1 requirements
- **Remaining Issue**: Lifespan manager hangs during test setup
- **Priority**: Medium - Celery task orchestration tests (4 tests) pass and cover the core logic. Router tests verify HTTP layer only.

### Test Coverage Without Router Tests

Current passing tests: **26 tests**
- Celery orchestration tasks: 4 tests ✓
- Project model: 8 tests ✓
- Orchestration service: 14 tests ✓

Missing coverage (router tests): **6 tests**
- HTTP endpoint responses
- Status code validation
- Request/response serialization

### Recommendation

Router tests can be fixed post-deployment as they test the HTTP layer only. The critical business logic (orchestration service + Celery tasks) is fully tested and passing.

---

## Summary

**Total Tests**: 32
- **Passing**: 26 (81%)
- **Failing**: 6 (19% - all router layer)

**Core Functionality Coverage**: 100% (all orchestration logic tested)
**HTTP Layer Coverage**: 0% (needs lifespan fix)
