# Week 2 Testing Implementation - Design Document

**Created:** 2025-10-28
**Approach:** 5 Parallel Tracks (Track-based Organization)
**Timeline:** Week 2 (2025-10-28 to 2025-11-04)
**Goal:** Security, Performance, and Docker Testing with Hub Security

---

## Executive Summary

Week 2 builds on Week 1's testing foundation by implementing critical security and performance tests, adding Docker-based test execution infrastructure, and expanding testing to Hub's orchestration layer.

**Key Objectives:**
- Implement security tests for project isolation, JWT validation, and RBAC
- Add performance tests with N+1 query detection and API benchmarks
- Create Docker test infrastructure for CI/production parity
- Implement Hub-specific security and Docker functionality tests
- Run tests both locally and in containerized environments

**Execution Strategy:** 5 parallel agents working in isolated git worktrees, following Week 1's proven approach.

**Total Deliverable:** ~70 new tests + complete Docker test infrastructure

---

## Design Decisions

### Decision 1: Parallel Worktrees + Track-based Organization

**Chosen Approach:** 5 independent tracks in isolated git worktrees

**Rationale:**
- Week 1 success: 250+ tests delivered using this approach (833% over plan)
- Clear separation of concerns prevents conflicts
- Parallel execution maximizes development velocity
- Independent commit histories for easier rollback
- Clean merge strategy at consolidation

**Alternative Considered:** Sequential single-branch approach
- **Rejected:** Much slower, no parallelization benefits

**Alternative Considered:** Application-based (3 tracks: CC, Hub, CI)
- **Rejected:** Mixed concerns per track, less clear separation

### Decision 2: Expanded Scope with Hub Security

**Chosen Approach:** Include Hub-specific security and Docker functionality tests in Week 2

**Rationale:**
- Hub uses Dagger SDK for orchestration (unique security concerns)
- Multi-instance isolation is critical for data security
- Docker functionality tests validate Hub's core value proposition
- Better to address security early than defer to Week 3

**Original Plan:** 18 security + 13 performance = 31 tests
**Expanded Scope:** 34 security + 13 performance + 26 Docker functionality = 73 tests

### Decision 3: Docker Test Infrastructure

**Chosen Approach:** Both containerized test execution AND Docker functionality tests

**Rationale:**
- Containerized execution ensures CI/production parity
- Eliminates "works on my machine" issues
- Docker functionality tests validate Hub's Dagger orchestration
- Comprehensive coverage of Docker ecosystem

**Components:**
- `Dockerfile.test` for each application component
- `docker-compose.test.yml` for test orchestration
- CI workflows for automated Docker testing
- Local development scripts (`make test-docker`)

---

## Architecture Overview

### 5 Parallel Tracks

```
.worktrees/
├── testing-security/           → testing/week2-security
│   └── CommandCenter security tests (18 tests)
├── testing-performance/        → testing/week2-performance
│   └── N+1 detection + benchmarks (13 tests)
├── testing-docker-infra/       → testing/week2-docker-infra
│   └── Docker test infrastructure
├── testing-hub-security/       → testing/week2-hub-security
│   └── Hub security tests (16 tests)
└── testing-docker-func/        → testing/week2-docker-functionality
    └── Dagger SDK tests (26 tests)
```

**Benefits:**
- Complete isolation (no merge conflicts)
- Parallel agent execution (5 agents simultaneously)
- Independent testing and validation
- Atomic merges per track

---

## Track 1: Security Tests (testing/week2-security)

**Goal:** Implement CommandCenter security tests for project isolation, JWT security, and basic RBAC

**Deliverables:** 18 tests

### 1.1 Project Isolation Tests (10 tests)

**File:** `backend/tests/security/test_project_isolation.py`

**Tests:**
1. User A cannot read User B's technologies
2. User A cannot modify User B's technologies
3. User A cannot delete User B's technologies
4. User A cannot read User B's repositories
5. User A cannot read User B's research tasks
6. User A cannot read User B's knowledge entries
7. Technology list filtered by user's project_id
8. Repository list filtered by user's project_id
9. Research task list filtered by user's project_id
10. Cross-project foreign key references rejected

**Infrastructure:**

```python
# backend/tests/security/conftest.py

@pytest.fixture
async def user_a(db_session):
    """Create isolated user A with project"""
    return await create_user_with_project(
        db_session,
        email="user_a@test.com",
        project_id="project-a"
    )

@pytest.fixture
async def user_b(db_session):
    """Create isolated user B with project"""
    return await create_user_with_project(
        db_session,
        email="user_b@test.com",
        project_id="project-b"
    )

@pytest.fixture
def auth_headers_factory(jwt_token_factory):
    """Create authorization headers for user"""
    def _create_headers(user):
        token = jwt_token_factory(user_id=user.id)
        return {"Authorization": f"Bearer {token}"}
    return _create_headers
```

**Test Pattern:**

```python
async def test_user_cannot_read_other_user_technologies(
    user_a, user_b, client, auth_headers_factory
):
    """User A cannot see User B's technologies"""
    # Create technology for User B
    tech_b = await create_technology(user_b, title="Secret Tech")

    # User A queries technologies
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/technologies", headers=headers)

    # Assert User B's technology not in results
    assert response.status_code == 200
    tech_ids = [t["id"] for t in response.json()]
    assert tech_b.id not in tech_ids
```

### 1.2 JWT Security Tests (5 tests)

**File:** `backend/tests/security/test_jwt_security.py`

**Tests:**
1. Token with tampered signature rejected (returns 401)
2. Token with tampered payload rejected (returns 401)
3. Expired token rejected (returns 401)
4. Token with invalid format rejected (returns 401)
5. Malformed token rejected (returns 401, not 500)

**Infrastructure:**

```python
# backend/tests/security/conftest.py

@pytest.fixture
def jwt_token_factory():
    """Factory for creating test JWT tokens"""
    def _create_token(
        user_id: str,
        expires_delta: timedelta = None,
        tampered: bool = False,
        tamper_type: str = "signature"  # or "payload"
    ):
        from app.utils.auth import create_access_token

        if expires_delta is None:
            expires_delta = timedelta(minutes=30)

        token = create_access_token(
            data={"sub": user_id},
            expires_delta=expires_delta
        )

        if tampered:
            if tamper_type == "signature":
                # Modify last part of token (signature)
                parts = token.split(".")
                parts[2] = parts[2][:-5] + "XXXXX"
                token = ".".join(parts)
            elif tamper_type == "payload":
                # Modify middle part (payload)
                parts = token.split(".")
                parts[1] = parts[1][:-5] + "XXXXX"
                token = ".".join(parts)

        return token

    return _create_token
```

**Test Pattern:**

```python
async def test_tampered_signature_rejected(jwt_token_factory, client):
    """Token with modified signature is rejected"""
    token = jwt_token_factory(
        user_id="user1",
        tampered=True,
        tamper_type="signature"
    )

    response = await client.get(
        "/api/v1/technologies",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()
```

### 1.3 RBAC Basic Tests (3 tests)

**File:** `backend/tests/security/test_rbac_basic.py`

**Tests:**
1. Regular user cannot delete other users
2. Project owner has full access to their project
3. Non-owner has read-only access (if roles implemented)

**Infrastructure:**

```python
@pytest.fixture
async def user_with_role(db_session):
    """Create user with specific role"""
    async def _create(email: str, role: str, project_id: str):
        user = User(
            email=email,
            project_id=project_id,
            role=role  # 'owner', 'member', 'viewer'
        )
        db_session.add(user)
        await db_session.commit()
        return user
    return _create
```

**Test Pattern:**

```python
async def test_regular_user_cannot_delete_other_users(
    user_a, user_b, client, auth_headers_factory
):
    """Non-admin cannot delete users"""
    headers = auth_headers_factory(user_a)
    response = await client.delete(
        f"/api/v1/users/{user_b.id}",
        headers=headers
    )

    assert response.status_code == 403
    assert "forbidden" in response.json()["detail"].lower()
```

### Success Criteria

- ✅ All 18 tests passing
- ✅ Project isolation enforced at API and database level
- ✅ JWT validation catches all tampering attempts
- ✅ RBAC basic patterns established
- ✅ Tests run in <5 seconds
- ✅ No false positives/negatives

---

## Track 2: Performance Tests (testing/week2-performance)

**Goal:** Detect N+1 queries and establish API performance baselines

**Deliverables:** 13 tests

### 2.1 N+1 Query Detection (5 tests)

**File:** `backend/tests/performance/test_n_plus_one_queries.py`

**Tests:**
1. Technologies list endpoint (with relationships)
2. Research tasks list endpoint (with relationships)
3. Repositories list with technologies
4. Single technology detail (with repos and research)
5. Knowledge base query with metadata

**Infrastructure:**

```python
# backend/tests/performance/conftest.py

from sqlalchemy import event

@pytest.fixture
def query_counter(db_session):
    """Count queries executed during test"""
    queries = []

    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        # Filter out internal queries (pg_catalog, etc.)
        if "pg_catalog" not in statement and "information_schema" not in statement:
            queries.append({
                "statement": statement,
                "parameters": parameters
            })

    event.listen(
        db_session.bind,
        "after_cursor_execute",
        receive_after_cursor_execute
    )

    yield queries

    event.remove(
        db_session.bind,
        "after_cursor_execute",
        receive_after_cursor_execute
    )

@pytest.fixture
async def large_dataset(db_session):
    """Create dataset large enough to expose N+1"""
    # Create 20 technologies, each with 3 repositories
    technologies = []
    for i in range(20):
        tech = await create_technology(
            title=f"Technology {i}",
            domain="test"
        )
        for j in range(3):
            repo = await create_repository(
                owner="test",
                name=f"repo-{i}-{j}"
            )
            tech.repositories.append(repo)
        technologies.append(tech)

    await db_session.commit()
    return technologies
```

**Test Pattern:**

```python
async def test_technologies_list_no_n_plus_one(
    query_counter, large_dataset, client
):
    """Technologies list uses joins, not N+1 queries"""
    # Clear any setup queries
    query_counter.clear()

    # Make request
    response = await client.get("/api/v1/technologies")

    # Analyze queries
    num_queries = len(query_counter)

    # Should be ≤3 queries:
    # 1. SELECT technologies
    # 2. JOIN repositories (if eager loading)
    # 3. JOIN research_tasks (if eager loading)
    assert num_queries <= 3, (
        f"Expected ≤3 queries, got {num_queries}. "
        f"Queries: {[q['statement'][:100] for q in query_counter]}"
    )

    # Verify response still correct
    assert response.status_code == 200
    assert len(response.json()) == 20
```

### 2.2 API Performance Benchmarks (8 tests)

**File:** `backend/tests/performance/test_api_benchmarks.py`

**Tests:**
1. GET /api/v1/technologies - <500ms
2. POST /api/v1/technologies - <300ms
3. GET /api/v1/research - <500ms
4. POST /api/v1/research - <300ms
5. POST /api/v1/knowledge/query - <1500ms
6. GET /api/v1/repositories - <500ms
7. Connection pool handles 50 concurrent requests
8. Database query performance with 1000 records

**Infrastructure:**

```python
# backend/tests/performance/conftest.py

@pytest.fixture
def performance_threshold():
    """Performance thresholds for API endpoints (milliseconds)"""
    return {
        "technologies_list": 500,
        "technologies_create": 300,
        "research_list": 500,
        "research_create": 300,
        "knowledge_query": 1500,
        "repositories_list": 500,
    }

@pytest.fixture
async def performance_dataset(db_session):
    """Create dataset for performance testing"""
    # Create 1000 technologies for stress testing
    for i in range(1000):
        await create_technology(
            title=f"Tech {i}",
            domain="performance-test"
        )
    await db_session.commit()
```

**Test Pattern:**

```python
import time

@pytest.mark.asyncio
async def test_technologies_list_performance(
    client, performance_threshold, large_dataset
):
    """GET /technologies responds in <500ms"""
    start = time.time()
    response = await client.get("/api/v1/technologies?limit=50")
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < performance_threshold["technologies_list"], (
        f"Response took {elapsed_ms:.2f}ms, threshold is "
        f"{performance_threshold['technologies_list']}ms"
    )

@pytest.mark.asyncio
async def test_concurrent_request_handling(client):
    """50 concurrent requests handled without errors"""
    async def make_request():
        return await client.get("/api/v1/technologies")

    start = time.time()
    responses = await asyncio.gather(*[make_request() for _ in range(50)])
    elapsed = time.time() - start

    # All should succeed
    assert all(r.status_code == 200 for r in responses)

    # Average response time acceptable
    avg_time_ms = (elapsed / 50) * 1000
    assert avg_time_ms < 1000, f"Average response time {avg_time_ms:.2f}ms too high"

    # No connection pool errors
    error_responses = [r for r in responses if r.status_code >= 500]
    assert len(error_responses) == 0
```

### Success Criteria

- ✅ All 13 tests passing
- ✅ N+1 queries detected and reported
- ✅ Performance baselines established
- ✅ Regression detection enabled in CI
- ✅ Clear failure messages with query details

---

## Track 3: Docker Test Infrastructure (testing/week2-docker-infra)

**Goal:** Create Docker-based test execution environment for CI/production parity

**Deliverables:**
- Dockerfiles for test execution (backend, frontend, hub-backend, hub-frontend)
- docker-compose.test.yml for orchestration
- CI workflow for Docker testing
- Local development scripts

### 3.1 Backend Test Dockerfile

**File:** `backend/Dockerfile.test`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    pytest-cov==4.1.0 \
    pytest-xdist==3.5.0

# Copy application code
COPY . .

# Create directories for test results
RUN mkdir -p /app/test-results /app/coverage

# Run tests by default
CMD ["pytest", "-v", "--cov=app", "--cov-report=xml:/app/coverage/coverage.xml", "--junitxml=/app/test-results/junit.xml"]
```

### 3.2 Frontend Test Dockerfile

**File:** `frontend/Dockerfile.test`

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Create test results directory
RUN mkdir -p /app/coverage

# Run tests by default
CMD ["npm", "test", "--", "--coverage", "--reporter=junit", "--outputFile=/app/coverage/junit.xml"]
```

### 3.3 Hub Backend Test Dockerfile

**File:** `hub/backend/Dockerfile.test`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    pytest-cov==4.1.0

# Copy application code
COPY . .

# Create test results directory
RUN mkdir -p /app/test-results

CMD ["pytest", "-v", "--cov=app", "--cov-report=xml:/app/test-results/coverage.xml"]
```

### 3.4 Test Orchestration

**File:** `docker-compose.test.yml`

```yaml
version: '3.8'

services:
  postgres-test:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: commandcenter_test
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  test-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.test
    volumes:
      - ./backend:/app
      - backend-test-results:/app/test-results
      - backend-coverage:/app/coverage
    environment:
      DATABASE_URL: postgresql://test:test@postgres-test:5432/commandcenter_test
      REDIS_URL: redis://redis-test:6379
      SECRET_KEY: test-secret-key
      TESTING: "true"
    depends_on:
      postgres-test:
        condition: service_healthy
      redis-test:
        condition: service_healthy
    command: >
      sh -c "
        pytest -v
        --cov=app
        --cov-report=xml:/app/coverage/coverage.xml
        --cov-report=html:/app/coverage/htmlcov
        --junitxml=/app/test-results/junit.xml
      "

  test-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.test
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - frontend-coverage:/app/coverage
    environment:
      CI: "true"
    command: npm test -- --coverage --watchAll=false

  test-hub-backend:
    build:
      context: ./hub/backend
      dockerfile: Dockerfile.test
    volumes:
      - ./hub/backend:/app
      - hub-backend-test-results:/app/test-results
      - /var/run/docker.sock:/var/run/docker.sock  # For Dagger tests
    environment:
      DATABASE_URL: sqlite+aiosqlite:///./test.db
      TESTING: "true"
    command: pytest -v --cov=app --cov-report=xml:/app/test-results/coverage.xml

  test-hub-frontend:
    build:
      context: ./hub/frontend
      dockerfile: Dockerfile.test
    volumes:
      - ./hub/frontend:/app
      - /app/node_modules
      - hub-frontend-coverage:/app/coverage
    environment:
      CI: "true"
    command: npm test -- --coverage --watchAll=false

volumes:
  backend-test-results:
  backend-coverage:
  frontend-coverage:
  hub-backend-test-results:
  hub-frontend-coverage:
```

### 3.5 CI Workflow

**File:** `.github/workflows/test-docker.yml`

```yaml
name: Docker Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test-backend-docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-backend-${{ hashFiles('backend/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-buildx-backend-

      - name: Build test image
        run: |
          docker-compose -f docker-compose.test.yml build test-backend

      - name: Run backend tests in Docker
        run: |
          docker-compose -f docker-compose.test.yml up \
            --abort-on-container-exit \
            --exit-code-from test-backend \
            postgres-test redis-test test-backend

      - name: Copy coverage from container
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml run --rm test-backend \
            sh -c "cp -r /app/coverage ./coverage-output"

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage/coverage.xml
          flags: backend-docker
          fail_ci_if_error: true

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: backend-test-results
          path: backend/test-results/

  test-frontend-docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-frontend-${{ hashFiles('frontend/package-lock.json') }}

      - name: Build and run frontend tests
        run: |
          docker-compose -f docker-compose.test.yml up \
            --abort-on-container-exit \
            --exit-code-from test-frontend \
            test-frontend

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage.xml
          flags: frontend-docker

  test-hub-docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Hub backend tests
        run: |
          docker-compose -f docker-compose.test.yml up \
            --abort-on-container-exit \
            --exit-code-from test-hub-backend \
            test-hub-backend

      - name: Run Hub frontend tests
        run: |
          docker-compose -f docker-compose.test.yml up \
            --abort-on-container-exit \
            --exit-code-from test-hub-frontend \
            test-hub-frontend

      - name: Upload Hub coverage
        uses: codecov/codecov-action@v3
        with:
          files: |
            ./hub/backend/test-results/coverage.xml
            ./hub/frontend/coverage/coverage.xml
          flags: hub-docker
```

### 3.6 Makefile Targets

**File:** `Makefile` (additions)

```makefile
# Docker testing targets
.PHONY: test-docker test-docker-backend test-docker-frontend test-docker-hub

test-docker: ## Run all tests in Docker
	@echo "Running all tests in Docker..."
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit

test-docker-backend: ## Run backend tests in Docker
	@echo "Running backend tests in Docker..."
	docker-compose -f docker-compose.test.yml up \
		--abort-on-container-exit \
		--exit-code-from test-backend \
		postgres-test redis-test test-backend

test-docker-frontend: ## Run frontend tests in Docker
	@echo "Running frontend tests in Docker..."
	docker-compose -f docker-compose.test.yml up \
		--abort-on-container-exit \
		--exit-code-from test-frontend \
		test-frontend

test-docker-hub: ## Run Hub tests in Docker
	@echo "Running Hub backend tests..."
	docker-compose -f docker-compose.test.yml up \
		--abort-on-container-exit \
		--exit-code-from test-hub-backend \
		test-hub-backend
	@echo "Running Hub frontend tests..."
	docker-compose -f docker-compose.test.yml up \
		--abort-on-container-exit \
		--exit-code-from test-hub-frontend \
		test-hub-frontend

test-security: ## Run security tests only
	docker-compose -f docker-compose.test.yml run --rm test-backend \
		pytest tests/security/ -v
	docker-compose -f docker-compose.test.yml run --rm test-hub-backend \
		pytest tests/security/ -v

test-performance: ## Run performance tests only
	docker-compose -f docker-compose.test.yml run --rm test-backend \
		pytest tests/performance/ -v

test-docker-clean: ## Clean up Docker test resources
	docker-compose -f docker-compose.test.yml down -v
	docker volume prune -f
```

### Success Criteria

- ✅ All test Dockerfiles build successfully
- ✅ docker-compose.test.yml orchestrates all services
- ✅ CI workflow runs tests in Docker
- ✅ Local development scripts work (`make test-docker`)
- ✅ Test results and coverage extracted from containers
- ✅ Docker layer caching optimized

---

## Track 4: Hub Security Tests (testing/week2-hub-security)

**Goal:** Implement Hub-specific security tests for multi-instance isolation and Dagger orchestration

**Deliverables:** 16 tests

### 4.1 Multi-Instance Isolation Tests (8 tests)

**File:** `hub/backend/tests/security/test_multi_instance_isolation.py`

**Tests:**
1. Docker volumes are isolated between projects
2. Environment variables not leaked between projects
3. Database files isolated per project
4. Network isolation between project stacks
5. Container names unique per project
6. Secrets (DB_PASSWORD, SECRET_KEY) unique per project
7. Port mappings non-overlapping
8. Log files isolated per project

**Infrastructure:**

```python
# hub/backend/tests/security/conftest.py

from app.models.project import CommandCenterConfig, PortSet

@pytest.fixture
def project_configs():
    """Multiple project configurations for isolation testing"""
    return [
        CommandCenterConfig(
            project_name="project-alpha",
            project_path="/tmp/test-projects/alpha",
            ports=PortSet(
                backend=8000,
                frontend=3000,
                postgres=5432,
                redis=6379
            )
        ),
        CommandCenterConfig(
            project_name="project-beta",
            project_path="/tmp/test-projects/beta",
            ports=PortSet(
                backend=8010,
                frontend=3010,
                postgres=5433,
                redis=6380
            )
        ),
        CommandCenterConfig(
            project_name="project-gamma",
            project_path="/tmp/test-projects/gamma",
            ports=PortSet(
                backend=8020,
                frontend=3020,
                postgres=5434,
                redis=6381
            )
        )
    ]

@pytest.fixture
async def mock_dagger_client():
    """Mock Dagger client for security tests (no real containers)"""
    from unittest.mock import AsyncMock, MagicMock

    client = MagicMock()
    client.container = AsyncMock()
    client.directory = MagicMock()

    # Mock container methods
    mock_container = MagicMock()
    mock_container.with_mounted_directory = MagicMock(return_value=mock_container)
    mock_container.with_env_variable = MagicMock(return_value=mock_container)
    mock_container.with_exposed_port = MagicMock(return_value=mock_container)
    mock_container.start = AsyncMock()

    client.container.return_value = mock_container

    return client

@pytest.fixture
async def orchestration_service(mock_dagger_client):
    """OrchestrationService with mocked Dagger"""
    from app.services.orchestration_service import OrchestrationService

    service = OrchestrationService(db_session=mock_db_session)
    service._dagger_client = mock_dagger_client

    return service
```

**Test Pattern:**

```python
async def test_project_volumes_are_isolated(
    orchestration_service, project_configs
):
    """Each project uses isolated Docker volumes"""
    # Start two projects
    stack_a = await orchestration_service.start_project(project_configs[0])
    stack_b = await orchestration_service.start_project(project_configs[1])

    # Get volume names
    volumes_a = stack_a.get_volume_names()
    volumes_b = stack_b.get_volume_names()

    # Assert no shared volumes
    shared = set(volumes_a).intersection(set(volumes_b))
    assert len(shared) == 0, f"Found shared volumes: {shared}"

    # Assert volumes include project name
    assert all("project-alpha" in v for v in volumes_a)
    assert all("project-beta" in v for v in volumes_b)

async def test_environment_variables_not_leaked(
    orchestration_service, project_configs
):
    """Project A secrets not accessible from Project B"""
    # Start both projects
    stack_a = await orchestration_service.start_project(project_configs[0])
    stack_b = await orchestration_service.start_project(project_configs[1])

    # Get environment variables
    env_a = stack_a.get_environment_variables()
    env_b = stack_b.get_environment_variables()

    # Assert different secrets
    assert env_a["SECRET_KEY"] != env_b["SECRET_KEY"]
    assert env_a["DB_PASSWORD"] != env_b["DB_PASSWORD"]

    # Assert project-specific database URLs
    assert "project-alpha" in env_a["DATABASE_URL"]
    assert "project-beta" in env_b["DATABASE_URL"]
```

### 4.2 Dagger Orchestration Security Tests (5 tests)

**File:** `hub/backend/tests/security/test_dagger_security.py`

**Tests:**
1. Containers run as non-root user
2. Host filesystem not fully exposed (only project folder)
3. Docker socket not exposed to non-privileged containers
4. Secrets passed via environment, not files
5. Container capabilities minimized (no --privileged)

**Test Pattern:**

```python
async def test_containers_run_as_non_root(mock_dagger_client, project_configs):
    """Dagger containers run with non-root user"""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(mock_dagger_client, project_configs[0])
    await stack.start()

    # Verify user set in container config
    calls = mock_dagger_client.container.call_args_list

    # Check that user is set (not root)
    user_calls = [c for c in calls if 'with_user' in str(c)]
    assert len(user_calls) > 0, "No user configuration found"

    # Ensure not running as root (UID 0)
    for call in user_calls:
        user = call[1].get('user', None)
        assert user != '0' and user != 'root'

async def test_host_filesystem_not_exposed(mock_dagger_client, project_configs):
    """Only project folder mounted, not entire host"""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(mock_dagger_client, project_configs[0])
    await stack.start()

    # Get all mount calls
    mount_calls = [
        c for c in mock_dagger_client.container.call_args_list
        if 'with_mounted_directory' in str(c)
    ]

    # Verify only project path mounted
    for call in mount_calls:
        mount_path = call[1].get('path', '')
        # Should not mount /, /home, /root, etc.
        dangerous_mounts = ['/', '/home', '/root', '/etc', '/var']
        assert not any(mount_path.startswith(d) for d in dangerous_mounts)
```

### 4.3 Port Conflict Handling Tests (3 tests)

**File:** `hub/backend/tests/security/test_port_conflicts.py`

**Tests:**
1. Detect port conflict before container creation
2. Suggest alternative ports when conflict detected
3. Graceful error message (not generic failure)

**Test Pattern:**

```python
async def test_detect_port_conflict_before_start(orchestration_service, project_configs):
    """Port conflict detected before container creation"""
    # Start first project on port 8000
    stack_a = await orchestration_service.start_project(project_configs[0])

    # Try to start second project on same port
    conflicting_config = CommandCenterConfig(
        project_name="conflict-project",
        project_path="/tmp/conflict",
        ports=PortSet(backend=8000, frontend=3010, postgres=5433, redis=6380)
    )

    with pytest.raises(PortConflictError) as exc_info:
        await orchestration_service.start_project(conflicting_config)

    # Verify error message
    assert "8000" in str(exc_info.value)
    assert "already in use" in str(exc_info.value).lower()

    # Verify no containers created
    stacks = orchestration_service.get_active_stacks()
    assert len(stacks) == 1  # Only first project

async def test_suggest_alternative_ports(orchestration_service, project_configs):
    """Conflict error suggests available ports"""
    # Start project on 8000
    await orchestration_service.start_project(project_configs[0])

    # Try conflicting project
    try:
        await orchestration_service.start_project_with_ports(8000, 3010, 5433, 6380)
    except PortConflictError as e:
        # Should suggest alternatives
        assert "try" in str(e).lower() or "available" in str(e).lower()
        assert any(str(port) in str(e) for port in [8010, 8020, 8030])
```

### Success Criteria

- ✅ All 16 tests passing
- ✅ Multi-instance isolation verified
- ✅ Dagger security best practices enforced
- ✅ Port conflicts detected early
- ✅ No real containers started during tests (mocked)

---

## Track 5: Docker Functionality Tests (testing/week2-docker-functionality)

**Goal:** Test Hub's Dagger SDK integration and container orchestration

**Deliverables:** 26 tests

### 5.1 Dagger SDK Integration Tests (12 tests)

**File:** `hub/backend/tests/integration/test_dagger_integration.py`

**Tests:**
1. Start complete stack (postgres, redis, backend, frontend)
2. Stop stack removes containers but preserves volumes
3. Restart stack reuses existing volumes
4. Build backend image with Dagger
5. Build frontend image with Dagger
6. Mount project directory into containers
7. Pass environment variables to containers
8. Expose ports correctly
9. Health check waits for container ready
10. Error handling for failed container start
11. Cleanup on partial failure
12. Multiple stacks run simultaneously

**Infrastructure:**

```python
# hub/backend/tests/integration/conftest.py

@pytest.fixture
async def dagger_client():
    """Real Dagger client for integration tests"""
    import dagger

    async with dagger.Connection() as client:
        yield client

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project directory with minimal structure"""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create minimal .env file
    (project_dir / ".env").write_text(
        "DATABASE_URL=postgresql://test:test@postgres:5432/test\n"
        "SECRET_KEY=test-secret\n"
    )

    return str(project_dir)

@pytest.fixture
def project_config(temp_project_dir):
    """Test project configuration"""
    return CommandCenterConfig(
        project_name="integration-test",
        project_path=temp_project_dir,
        ports=PortSet(
            backend=18000,  # Use high ports to avoid conflicts
            frontend=13000,
            postgres=15432,
            redis=16379
        )
    )
```

**Test Pattern:**

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_start_complete_stack(dagger_client, project_config):
    """Start all services: postgres, redis, backend, frontend"""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)

    # Start stack
    await stack.start()

    # Verify all containers running
    assert await stack.postgres.is_running()
    assert await stack.redis.is_running()
    assert await stack.backend.is_running()
    assert await stack.frontend.is_running()

    # Verify health checks pass
    assert await stack.postgres.health_check()
    assert await stack.redis.health_check()

    # Cleanup
    await stack.stop()

@pytest.mark.integration
async def test_stop_preserves_volumes(dagger_client, project_config):
    """Stop removes containers but preserves volumes"""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)

    # Start and write data
    await stack.start()

    # Write test data to postgres
    await stack.postgres.execute_sql(
        "CREATE TABLE test (id INT); INSERT INTO test VALUES (1);"
    )

    # Stop stack
    await stack.stop()

    # Verify containers stopped
    assert not await stack.postgres.is_running()

    # Restart
    await stack.start()

    # Verify data persists
    result = await stack.postgres.execute_sql("SELECT * FROM test;")
    assert len(result) == 1

    # Cleanup
    await stack.stop()
```

### 5.2 Container Lifecycle Tests (8 tests)

**File:** `hub/backend/tests/integration/test_container_lifecycle.py`

**Tests:**
1. Start container from stopped state
2. Stop running container
3. Restart container preserves configuration
4. Container logs accessible after start
5. Container status updates correctly
6. Start handles already-running gracefully
7. Stop handles already-stopped gracefully
8. Force stop (SIGKILL) when graceful fails

**Test Pattern:**

```python
@pytest.mark.integration
async def test_container_lifecycle(dagger_client, project_config):
    """Full lifecycle: create → start → stop → restart → remove"""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)

    # Initial state: not running
    assert not await stack.backend.is_running()

    # Start
    await stack.start()
    assert await stack.backend.is_running()

    # Stop
    await stack.stop()
    assert not await stack.backend.is_running()

    # Restart
    await stack.restart()
    assert await stack.backend.is_running()

    # Remove
    await stack.remove()
    # Verify volumes also removed
    volumes = await stack.get_volumes()
    assert len(volumes) == 0

@pytest.mark.integration
async def test_container_logs_accessible(dagger_client, project_config):
    """Container logs accessible after start"""
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    # Get backend logs
    logs = await stack.backend.logs(tail=50)

    # Verify logs contain startup messages
    assert "Uvicorn running" in logs or "Application startup" in logs

    await stack.stop()
```

### 5.3 Stack Orchestration Tests (6 tests)

**File:** `hub/backend/tests/integration/test_stack_orchestration.py`

**Tests:**
1. Services start in correct order (postgres → redis → backend → frontend)
2. Dependencies verified before starting dependents
3. Partial failure rolls back entire stack
4. Health checks prevent premature "ready" status
5. OrchestrationService tracks multiple active stacks
6. Registry cleanup on stack removal

**Test Pattern:**

```python
@pytest.mark.integration
async def test_services_start_in_order(dagger_client, project_config):
    """Services start in dependency order"""
    from app.dagger_modules.commandcenter import CommandCenterStack

    start_order = []

    # Monkey-patch to track start order
    original_start = CommandCenterStack._start_service

    async def tracked_start(self, service_name):
        start_order.append(service_name)
        return await original_start(self, service_name)

    CommandCenterStack._start_service = tracked_start

    stack = CommandCenterStack(dagger_client, project_config)
    await stack.start()

    # Verify order
    assert start_order.index("postgres") < start_order.index("backend")
    assert start_order.index("redis") < start_order.index("backend")
    assert start_order.index("backend") < start_order.index("frontend")

    await stack.stop()
    CommandCenterStack._start_service = original_start

@pytest.mark.integration
async def test_partial_failure_rolls_back(dagger_client, project_config):
    """Partial failure rolls back entire stack"""
    from app.dagger_modules.commandcenter import CommandCenterStack
    from unittest.mock import patch

    stack = CommandCenterStack(dagger_client, project_config)

    # Make backend fail to start
    with patch.object(stack, '_start_backend', side_effect=Exception("Backend failed")):
        with pytest.raises(StackStartupError) as exc_info:
            await stack.start()

        assert "Backend failed" in str(exc_info.value)

    # Verify rollback: no containers running
    assert not await stack.postgres.is_running()
    assert not await stack.redis.is_running()
    assert not await stack.backend.is_running()
```

### Success Criteria

- ✅ All 26 tests passing
- ✅ Real Dagger SDK integration (not mocked)
- ✅ Container lifecycle fully tested
- ✅ Stack orchestration logic validated
- ✅ Tests run in <2 minutes (parallel execution)
- ✅ Cleanup always happens (no orphaned containers)

---

## Consolidation Strategy

After all 5 tracks complete:

### Consolidation Steps

1. **Verify Each Track:**
   - All tests passing in isolation
   - No merge conflicts with main
   - Documentation complete

2. **Merge Order:**
   ```bash
   # Merge in logical order
   git checkout main
   git merge testing/week2-security
   git merge testing/week2-performance
   git merge testing/week2-docker-infra
   git merge testing/week2-hub-security
   git merge testing/week2-docker-functionality
   ```

3. **Run Full Test Suite:**
   ```bash
   # After all merges
   make test-docker
   pytest backend/tests/security/ backend/tests/performance/ -v
   pytest hub/backend/tests/security/ -v
   ```

4. **Create Results Document:**
   - Copy template to `docs/WEEK2_TESTING_RESULTS.md`
   - Fill in actual deliverables
   - Document any issues or deviations

5. **Clean Up Worktrees:**
   ```bash
   git worktree remove .worktrees/testing-security
   git worktree remove .worktrees/testing-performance
   git worktree remove .worktrees/testing-docker-infra
   git worktree remove .worktrees/testing-hub-security
   git worktree remove .worktrees/testing-docker-func
   ```

---

## Documentation Deliverables

### New Documentation Files

1. **`docs/TESTING_WEEK2.md`**
   - Week 2 testing guide
   - Quick start instructions
   - Test categories and organization
   - Running tests (local and Docker)
   - Troubleshooting

2. **`docs/WEEK2_TESTING_RESULTS.md`**
   - Final results document (filled during execution)
   - Track deliverables
   - Test counts and coverage
   - Issues and resolutions

3. **`hub/backend/tests/README.md`**
   - Hub testing guide
   - Dagger mocking strategy
   - Security test patterns
   - Running Hub tests

### Updated Documentation

1. **`README.md`**
   - Add Docker testing section
   - Update test counts
   - Link to Week 2 docs

2. **`docs/CI_WORKFLOWS.md`**
   - Add test-docker.yml workflow
   - Document Docker test execution
   - Coverage reporting updates

3. **`Makefile`**
   - Add test-docker targets
   - Add security/performance shortcuts
   - Help text for new targets

---

## Success Metrics

### Test Counts

**Target:** ~70 new tests

| Track | Tests |
|-------|-------|
| Security | 18 |
| Performance | 13 |
| Hub Security | 16 |
| Docker Functionality | 26 |
| **Total** | **73** |

### Coverage Goals

| Component | Current | Target |
|-----------|---------|--------|
| Backend | 80% | 85% |
| Frontend | 60% | 65% |
| Hub Backend | 100% | 100% |
| Hub Frontend | 100% | 100% |

### Quality Gates

- ✅ All security tests must pass (no exceptions)
- ✅ Performance tests establish baselines (not block merges initially)
- ✅ Docker tests run in CI successfully
- ✅ No test flakiness (100% pass rate)
- ✅ Tests run in <5 minutes (excluding E2E)

### CI Improvements

| Metric | Before | Target |
|--------|--------|--------|
| Security gate | None | Blocking |
| Performance regression | None | Warning |
| Docker test execution | None | Parallel |
| Total CI time | 20-25 min | 20-25 min (maintained) |

---

## Risk Mitigation

### Risk: Docker tests too slow

**Mitigation:**
- Aggressive layer caching
- Parallel test execution
- Minimal test images (alpine base)

### Risk: Dagger tests unreliable

**Mitigation:**
- Mock for unit/security tests
- Real Dagger only for integration tests
- Proper cleanup in fixtures
- Timeouts on all Dagger operations

### Risk: N+1 detection false positives

**Mitigation:**
- Filter internal queries (pg_catalog)
- Document expected query counts
- Threshold-based (≤3 queries, not exact count)

### Risk: Port conflicts in parallel tests

**Mitigation:**
- Use high port numbers (18000+)
- Unique ports per test fixture
- Port cleanup in teardown

### Risk: Cross-track merge conflicts

**Mitigation:**
- Clear file ownership per track
- No shared test utilities (until consolidation)
- Independent test fixtures

---

## Timeline

**Total Duration:** 5-7 days

| Day | Track Activities | Output |
|-----|------------------|--------|
| 1 | Start all 5 tracks in parallel | Worktrees created, agents dispatched |
| 2-3 | Track implementation | Tests written, infrastructure created |
| 4 | Track verification | All tests passing per track |
| 5 | Consolidation | Merged to main, full suite passing |
| 6-7 | Documentation & CI tuning | Docs complete, CI optimized |

---

## Next Steps (Week 3)

After Week 2 completion:

1. **Balance Test Pyramid** (Week 3 focus)
   - Add more unit tests (target 70% of suite)
   - Consolidate E2E tests (reduce from 134 to ~15)
   - Optimize integration tests

2. **CI/CD Optimization**
   - Test sharding
   - Selective test running
   - Performance monitoring dashboard

3. **Documentation Polish**
   - Testing quickstart guide
   - Team training materials
   - Test review checklist

---

## References

- Week 1 Results: `docs/WEEK1_TESTING_RESULTS.md`
- Testing Strategy: `docs/plans/2025-10-28-streamlined-testing-plan.md`
- Week 1 Consolidation: `docs/plans/2025-10-28-week1-testing-consolidation.md`
- CI Workflows: `docs/CI_WORKFLOWS.md`
- Hub Testing: `hub/TESTING.md`

---

**Document Status:** Complete
**Next Action:** Phase 5 - Worktree Setup
**References:**
- Validated with user through brainstorming skill
- All 5 design sections approved
- Ready for implementation
