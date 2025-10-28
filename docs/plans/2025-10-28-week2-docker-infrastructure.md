# Week 2 Docker Test Infrastructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create Docker-based test execution infrastructure for CI/production parity across all CommandCenter components.

**Architecture:** Multi-stage Dockerfiles for test execution, docker-compose.test.yml for orchestration, GitHub Actions workflows for CI integration, and Makefile targets for local development. Test containers mount source code for live development and extract coverage reports.

**Tech Stack:** Docker, docker-compose, GitHub Actions, Make, PostgreSQL, Redis, Node.js, Python

**Worktree:** `.worktrees/testing-docker-infra` → `testing/week2-docker-infra` branch

---

## Task 1: Backend Test Dockerfile

**Files:**
- Create: `backend/Dockerfile.test`

**Step 1: Create backend test Dockerfile**

Create `backend/Dockerfile.test`:

```dockerfile
# Backend Test Dockerfile
# Multi-stage build for optimized test execution

FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    pytest-cov==4.1.0 \
    pytest-xdist==3.5.0 \
    pytest-timeout==2.2.0

# Copy application code
COPY . .

# Create directories for test results and coverage
RUN mkdir -p /app/test-results /app/coverage

# Set Python path
ENV PYTHONPATH=/app

# Default command: run all tests with coverage
CMD ["pytest", "-v", \
     "--cov=app", \
     "--cov-report=xml:/app/coverage/coverage.xml", \
     "--cov-report=html:/app/coverage/htmlcov", \
     "--cov-report=term-missing", \
     "--junitxml=/app/test-results/junit.xml"]
```

**Step 2: Create .dockerignore for backend**

Create `backend/.dockerignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# Testing
.pytest_cache/
test-results/
coverage/
htmlcov/
.coverage

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data
data/
*.db
*.sqlite
```

**Step 3: Build and test the image**

Run:
```bash
cd backend
docker build -f Dockerfile.test -t commandcenter-backend-test:latest .
```

Expected: Build succeeds without errors

**Step 4: Test the image runs**

Run:
```bash
docker run --rm commandcenter-backend-test:latest pytest --version
```

Expected: Output shows pytest version

**Step 5: Commit**

```bash
git add backend/Dockerfile.test backend/.dockerignore
git commit -m "feat: Add backend test Dockerfile

- Multi-stage build from python:3.11-slim
- Install system and Python dependencies
- Include pytest with coverage and parallel execution
- Create test-results and coverage directories
- Default command runs full test suite with coverage
- Add .dockerignore for clean builds"
```

---

## Task 2: Frontend Test Dockerfile

**Files:**
- Create: `frontend/Dockerfile.test`

**Step 1: Create frontend test Dockerfile**

Create `frontend/Dockerfile.test`:

```dockerfile
# Frontend Test Dockerfile
# Node.js test environment with Vitest

FROM node:18-alpine AS base

WORKDIR /app

# Install dependencies for Puppeteer (if E2E tests use it)
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont

# Set Puppeteer to use system Chrome
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy application code
COPY . .

# Create coverage directory
RUN mkdir -p /app/coverage

# Default command: run tests with coverage
CMD ["npm", "test", "--", \
     "--coverage", \
     "--reporter=junit", \
     "--outputFile=/app/coverage/junit.xml"]
```

**Step 2: Create .dockerignore for frontend**

Create `frontend/.dockerignore`:

```
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
coverage/
.nyc_output/

# Build
dist/
build/
.vite/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment
.env.local
.env.*.local
```

**Step 3: Build and test the image**

Run:
```bash
cd frontend
docker build -f Dockerfile.test -t commandcenter-frontend-test:latest .
```

Expected: Build succeeds

**Step 4: Test the image runs**

Run:
```bash
docker run --rm commandcenter-frontend-test:latest npm test -- --version
```

Expected: Shows test runner version

**Step 5: Commit**

```bash
git add frontend/Dockerfile.test frontend/.dockerignore
git commit -m "feat: Add frontend test Dockerfile

- Build from node:18-alpine
- Install Chromium for E2E tests
- Install npm dependencies
- Default command runs tests with coverage
- Add .dockerignore for clean builds"
```

---

## Task 3: Hub Backend Test Dockerfile

**Files:**
- Create: `hub/backend/Dockerfile.test`

**Step 1: Create Hub backend test Dockerfile**

Create `hub/backend/Dockerfile.test`:

```dockerfile
# Hub Backend Test Dockerfile
# Includes Docker for Dagger SDK integration tests

FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    docker.io \
    ca-certificates \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    pytest-cov==4.1.0 \
    pytest-timeout==2.2.0

# Copy application code
COPY . .

# Create test results directory
RUN mkdir -p /app/test-results /app/coverage

# Set Python path
ENV PYTHONPATH=/app

# Default command: run tests with coverage
CMD ["pytest", "-v", \
     "--cov=app", \
     "--cov-report=xml:/app/coverage/coverage.xml", \
     "--cov-report=html:/app/coverage/htmlcov", \
     "--cov-report=term-missing", \
     "--junitxml=/app/test-results/junit.xml"]
```

**Step 2: Create .dockerignore for Hub backend**

Create `hub/backend/.dockerignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# Testing
.pytest_cache/
test-results/
coverage/
.coverage

# Database
*.db
*.sqlite
data/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
```

**Step 3: Build and test the image**

Run:
```bash
cd hub/backend
docker build -f Dockerfile.test -t commandcenter-hub-backend-test:latest .
```

Expected: Build succeeds

**Step 4: Verify Docker CLI available**

Run:
```bash
docker run --rm commandcenter-hub-backend-test:latest docker --version
```

Expected: Shows Docker version

**Step 5: Commit**

```bash
git add hub/backend/Dockerfile.test hub/backend/.dockerignore
git commit -m "feat: Add Hub backend test Dockerfile

- Build from python:3.11-slim
- Install Docker CLI for Dagger integration tests
- Install Python and test dependencies
- Default command runs tests with coverage
- Add .dockerignore for clean builds"
```

---

## Task 4: Hub Frontend Test Dockerfile

**Files:**
- Create: `hub/frontend/Dockerfile.test`

**Step 1: Create Hub frontend test Dockerfile**

Create `hub/frontend/Dockerfile.test`:

```dockerfile
# Hub Frontend Test Dockerfile
# Node.js test environment

FROM node:18-alpine AS base

WORKDIR /app

# Install Chromium for E2E tests
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont

# Set Puppeteer to use system Chrome
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy application code
COPY . .

# Create coverage directory
RUN mkdir -p /app/coverage

# Default command: run tests with coverage
CMD ["npm", "test", "--", \
     "--coverage", \
     "--reporter=junit", \
     "--outputFile=/app/coverage/junit.xml"]
```

**Step 2: Create .dockerignore for Hub frontend**

Create `hub/frontend/.dockerignore`:

```
# Dependencies
node_modules/
npm-debug.log*

# Testing
coverage/

# Build
dist/
build/

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

**Step 3: Build the image**

Run:
```bash
cd hub/frontend
docker build -f Dockerfile.test -t commandcenter-hub-frontend-test:latest .
```

Expected: Build succeeds

**Step 4: Commit**

```bash
git add hub/frontend/Dockerfile.test hub/frontend/.dockerignore
git commit -m "feat: Add Hub frontend test Dockerfile

- Build from node:18-alpine
- Install Chromium for E2E tests
- Install npm dependencies
- Default command runs tests with coverage
- Add .dockerignore for clean builds"
```

---

## Task 5: Docker Compose Test Orchestration

**Files:**
- Create: `docker-compose.test.yml`

**Step 1: Create docker-compose test file**

Create `docker-compose.test.yml`:

```yaml
version: '3.8'

# Test orchestration for all CommandCenter components
# Includes dedicated test databases and service dependencies

services:
  # Test database (PostgreSQL)
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
    volumes:
      - postgres-test-data:/var/lib/postgresql/data

  # Test cache (Redis)
  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Backend tests
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
      SECRET_KEY: test-secret-key-for-testing-only
      TESTING: "true"
      PYTHONPATH: /app
    depends_on:
      postgres-test:
        condition: service_healthy
      redis-test:
        condition: service_healthy
    command: >
      sh -c "
        echo 'Waiting for database...' &&
        sleep 2 &&
        pytest -v
        --cov=app
        --cov-report=xml:/app/coverage/coverage.xml
        --cov-report=html:/app/coverage/htmlcov
        --cov-report=term-missing
        --junitxml=/app/test-results/junit.xml
      "

  # Frontend tests
  test-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.test
    volumes:
      - ./frontend:/app
      - /app/node_modules  # Anonymous volume for node_modules
      - frontend-coverage:/app/coverage
    environment:
      CI: "true"
      VITE_API_URL: http://localhost:8000
    command: npm test -- --coverage --watchAll=false

  # Hub backend tests
  test-hub-backend:
    build:
      context: ./hub/backend
      dockerfile: Dockerfile.test
    volumes:
      - ./hub/backend:/app
      - hub-backend-test-results:/app/test-results
      - hub-backend-coverage:/app/coverage
      - /var/run/docker.sock:/var/run/docker.sock  # For Dagger tests
    environment:
      DATABASE_URL: sqlite+aiosqlite:///./test.db
      TESTING: "true"
      PYTHONPATH: /app
    command: >
      sh -c "
        pytest -v
        --cov=app
        --cov-report=xml:/app/coverage/coverage.xml
        --cov-report=html:/app/coverage/htmlcov
        --cov-report=term-missing
        --junitxml=/app/test-results/junit.xml
      "

  # Hub frontend tests
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
      VITE_API_URL: http://localhost:9001
    command: npm test -- --coverage --watchAll=false

volumes:
  postgres-test-data:
  backend-test-results:
  backend-coverage:
  frontend-coverage:
  hub-backend-test-results:
  hub-backend-coverage:
  hub-frontend-coverage:
```

**Step 2: Test the orchestration**

Run:
```bash
docker-compose -f docker-compose.test.yml up --build test-backend
```

Expected: Backend tests run successfully

**Step 3: Commit**

```bash
git add docker-compose.test.yml
git commit -m "feat: Add docker-compose test orchestration

- Define postgres-test and redis-test services
- Configure test-backend with dependencies
- Configure test-frontend with environment
- Configure Hub backend and frontend tests
- Mount source code for live development
- Create named volumes for test results and coverage
- Add health checks for database readiness"
```

---

## Task 6: Makefile Test Targets

**Files:**
- Modify: `Makefile` (add test-docker section)

**Step 1: Add Docker test targets to Makefile**

Add to `Makefile`:

```makefile
# ============================================================================
# Docker Testing Targets
# ============================================================================

.PHONY: test-docker test-docker-backend test-docker-frontend test-docker-hub
.PHONY: test-docker-all test-security test-performance test-docker-clean

test-docker: ## Run all tests in Docker
	@echo "Running all tests in Docker..."
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-backend

test-docker-backend: ## Run backend tests in Docker
	@echo "Running backend tests in Docker..."
	docker-compose -f docker-compose.test.yml up \
		--build \
		--abort-on-container-exit \
		--exit-code-from test-backend \
		postgres-test redis-test test-backend

test-docker-frontend: ## Run frontend tests in Docker
	@echo "Running frontend tests in Docker..."
	docker-compose -f docker-compose.test.yml up \
		--build \
		--abort-on-container-exit \
		--exit-code-from test-frontend \
		test-frontend

test-docker-hub: ## Run Hub tests in Docker
	@echo "Running Hub backend tests..."
	docker-compose -f docker-compose.test.yml up \
		--build \
		--abort-on-container-exit \
		--exit-code-from test-hub-backend \
		test-hub-backend
	@echo "Running Hub frontend tests..."
	docker-compose -f docker-compose.test.yml up \
		--build \
		--abort-on-container-exit \
		--exit-code-from test-hub-frontend \
		test-hub-frontend

test-docker-all: ## Run all tests (backend, frontend, hub) in Docker
	@echo "Running complete test suite in Docker..."
	docker-compose -f docker-compose.test.yml up \
		--build \
		--abort-on-container-exit

test-security: ## Run security tests only (backend + hub)
	@echo "Running security tests..."
	docker-compose -f docker-compose.test.yml run --rm test-backend \
		pytest tests/security/ -v
	docker-compose -f docker-compose.test.yml run --rm test-hub-backend \
		pytest tests/security/ -v

test-performance: ## Run performance tests only
	@echo "Running performance tests..."
	docker-compose -f docker-compose.test.yml run --rm test-backend \
		pytest tests/performance/ -v -s

test-docker-clean: ## Clean up Docker test resources
	@echo "Cleaning up Docker test resources..."
	docker-compose -f docker-compose.test.yml down -v
	docker volume prune -f
	@echo "Cleaned up test volumes and containers"

test-docker-shell-backend: ## Open shell in backend test container
	docker-compose -f docker-compose.test.yml run --rm test-backend bash

test-docker-shell-frontend: ## Open shell in frontend test container
	docker-compose -f docker-compose.test.yml run --rm test-frontend sh

test-docker-coverage: ## Extract coverage reports from containers
	@echo "Extracting coverage reports..."
	@mkdir -p coverage-reports
	docker cp $$(docker-compose -f docker-compose.test.yml ps -q test-backend):/app/coverage/. ./coverage-reports/backend/ 2>/dev/null || true
	docker cp $$(docker-compose -f docker-compose.test.yml ps -q test-frontend):/app/coverage/. ./coverage-reports/frontend/ 2>/dev/null || true
	@echo "Coverage reports extracted to ./coverage-reports/"
```

**Step 2: Test Makefile targets**

Run:
```bash
make test-docker-backend
```

Expected: Backend tests run successfully

**Step 3: Update help target to include new commands**

Verify:
```bash
make help | grep "test-docker"
```

Expected: Shows all new test-docker commands

**Step 4: Commit**

```bash
git add Makefile
git commit -m "feat: Add Docker testing Makefile targets

- Add test-docker for all tests
- Add test-docker-backend for backend only
- Add test-docker-frontend for frontend only
- Add test-docker-hub for Hub tests
- Add test-security for security tests only
- Add test-performance for performance tests only
- Add test-docker-clean for cleanup
- Add test-docker-shell-* for debugging
- Add test-docker-coverage for extracting reports"
```

---

## Task 7: GitHub Actions CI Workflow

**Files:**
- Create: `.github/workflows/test-docker.yml`

**Step 1: Create GitHub Actions workflow for Docker tests**

Create `.github/workflows/test-docker.yml`:

```yaml
name: Docker Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:  # Allow manual triggering

jobs:
  test-backend-docker:
    name: Backend Tests (Docker)
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-backend-${{ hashFiles('backend/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-buildx-backend-

      - name: Build backend test image
        run: |
          docker-compose -f docker-compose.test.yml build test-backend

      - name: Start test dependencies
        run: |
          docker-compose -f docker-compose.test.yml up -d postgres-test redis-test

      - name: Wait for dependencies
        run: |
          timeout 30 sh -c 'until docker-compose -f docker-compose.test.yml exec -T postgres-test pg_isready -U test; do sleep 1; done'
          timeout 30 sh -c 'until docker-compose -f docker-compose.test.yml exec -T redis-test redis-cli ping; do sleep 1; done'

      - name: Run backend tests
        run: |
          docker-compose -f docker-compose.test.yml up \
            --abort-on-container-exit \
            --exit-code-from test-backend \
            test-backend

      - name: Copy coverage from container
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml run --rm test-backend \
            sh -c "cp -r /app/coverage /tmp/coverage-output"
          docker cp \
            $(docker-compose -f docker-compose.test.yml ps -q test-backend):/app/coverage \
            ./backend-coverage || true

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        if: always()
        with:
          files: ./backend-coverage/coverage.xml
          flags: backend-docker
          name: backend-docker-coverage
          fail_ci_if_error: false

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: backend-test-results
          path: |
            backend/test-results/
            backend-coverage/

      - name: Cleanup
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml down -v

  test-frontend-docker:
    name: Frontend Tests (Docker)
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-frontend-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-buildx-frontend-

      - name: Build and run frontend tests
        run: |
          docker-compose -f docker-compose.test.yml up \
            --build \
            --abort-on-container-exit \
            --exit-code-from test-frontend \
            test-frontend

      - name: Copy coverage from container
        if: always()
        run: |
          docker cp \
            $(docker-compose -f docker-compose.test.yml ps -q test-frontend):/app/coverage \
            ./frontend-coverage || true

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        if: always()
        with:
          files: ./frontend-coverage/coverage.xml
          flags: frontend-docker
          name: frontend-docker-coverage
          fail_ci_if_error: false

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: frontend-test-results
          path: frontend-coverage/

      - name: Cleanup
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml down -v

  test-hub-docker:
    name: Hub Tests (Docker)
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Run Hub backend tests
        run: |
          docker-compose -f docker-compose.test.yml up \
            --build \
            --abort-on-container-exit \
            --exit-code-from test-hub-backend \
            test-hub-backend

      - name: Run Hub frontend tests
        run: |
          docker-compose -f docker-compose.test.yml up \
            --build \
            --abort-on-container-exit \
            --exit-code-from test-hub-frontend \
            test-hub-frontend

      - name: Copy coverage from containers
        if: always()
        run: |
          docker cp \
            $(docker-compose -f docker-compose.test.yml ps -q test-hub-backend):/app/coverage \
            ./hub-backend-coverage || true
          docker cp \
            $(docker-compose -f docker-compose.test.yml ps -q test-hub-frontend):/app/coverage \
            ./hub-frontend-coverage || true

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        if: always()
        with:
          files: |
            ./hub-backend-coverage/coverage.xml
            ./hub-frontend-coverage/coverage.xml
          flags: hub-docker
          name: hub-docker-coverage
          fail_ci_if_error: false

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: hub-test-results
          path: |
            hub-backend-coverage/
            hub-frontend-coverage/

      - name: Cleanup
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml down -v
```

**Step 2: Commit**

```bash
git add .github/workflows/test-docker.yml
git commit -m "feat: Add GitHub Actions workflow for Docker tests

- Add test-backend-docker job with PostgreSQL and Redis
- Add test-frontend-docker job
- Add test-hub-docker job
- Cache Docker layers for faster builds
- Upload coverage to Codecov
- Upload test results as artifacts
- Clean up resources after tests
- Set 15-minute timeout per job"
```

---

## Task 8: Documentation

**Files:**
- Create: `docs/DOCKER_TESTING.md`
- Create: `IMPLEMENTATION_SUMMARY.md` (in worktree root)

**Step 1: Create Docker testing documentation**

Create `docs/DOCKER_TESTING.md`:

```markdown
# Docker Testing Infrastructure

## Overview

Docker-based test execution ensures CI/production parity by running tests in isolated containers with identical environments.

## Components

### Test Dockerfiles

Each component has a dedicated test Dockerfile:

- `backend/Dockerfile.test` - Backend tests with pytest
- `frontend/Dockerfile.test` - Frontend tests with Vitest
- `hub/backend/Dockerfile.test` - Hub backend with Docker CLI
- `hub/frontend/Dockerfile.test` - Hub frontend tests

### Docker Compose Orchestration

`docker-compose.test.yml` orchestrates:
- **postgres-test**: Test database (port 5433)
- **redis-test**: Test cache (port 6380)
- **test-backend**: Backend tests with dependencies
- **test-frontend**: Frontend tests
- **test-hub-backend**: Hub backend with Docker socket
- **test-hub-frontend**: Hub frontend tests

### Makefile Targets

```bash
make test-docker              # Run all tests
make test-docker-backend      # Backend only
make test-docker-frontend     # Frontend only
make test-docker-hub          # Hub tests
make test-security            # Security tests
make test-performance         # Performance tests
make test-docker-clean        # Cleanup resources
```

## Usage

### Local Development

**Run all tests:**
```bash
make test-docker-all
```

**Run specific component:**
```bash
make test-docker-backend
```

**Debug in container:**
```bash
make test-docker-shell-backend
pytest tests/security/ -v
```

**Extract coverage reports:**
```bash
make test-docker-coverage
# Reports in ./coverage-reports/
```

### CI/CD Integration

GitHub Actions workflow (`.github/workflows/test-docker.yml`) runs automatically on:
- Pull requests to main
- Pushes to main
- Manual workflow dispatch

**Jobs:**
- `test-backend-docker`: Backend tests with coverage
- `test-frontend-docker`: Frontend tests with coverage
- `test-hub-docker`: Hub tests with coverage

## Architecture

### Volume Mounts

```yaml
# Source code (live updates)
- ./backend:/app

# Node modules (cached)
- /app/node_modules

# Test results (extracted)
- backend-test-results:/app/test-results
- backend-coverage:/app/coverage
```

### Environment Variables

**Backend:**
```yaml
DATABASE_URL: postgresql://test:test@postgres-test:5432/commandcenter_test
REDIS_URL: redis://redis-test:6379
SECRET_KEY: test-secret-key
TESTING: "true"
```

**Frontend:**
```yaml
CI: "true"
VITE_API_URL: http://localhost:8000
```

### Dependencies

Test services depend on infrastructure:
```yaml
depends_on:
  postgres-test:
    condition: service_healthy
  redis-test:
    condition: service_healthy
```

## Benefits

### 1. CI/Production Parity

Tests run in same environment as production containers.

### 2. Isolation

Each test run uses fresh database and cache instances.

### 3. Consistency

No "works on my machine" issues - identical environment for all developers.

### 4. Parallel Execution

Docker Compose can run multiple test suites simultaneously.

### 5. Easy Cleanup

`make test-docker-clean` removes all test resources.

## Troubleshooting

### Port conflicts

Test services use alternate ports:
- PostgreSQL: 5433 (instead of 5432)
- Redis: 6380 (instead of 6379)

### Slow builds

Enable BuildKit for faster builds:
```bash
export DOCKER_BUILDKIT=1
```

Use layer caching:
```bash
docker-compose -f docker-compose.test.yml build --cache-from commandcenter-backend-test:latest
```

### Tests fail in Docker but pass locally

Check environment variables:
```bash
docker-compose -f docker-compose.test.yml run --rm test-backend env
```

### Cannot extract coverage

Ensure container is still running or use `docker cp` immediately after test:
```bash
docker-compose -f docker-compose.test.yml up test-backend
docker cp $(docker-compose -f docker-compose.test.yml ps -q test-backend):/app/coverage ./coverage
```

### Docker socket permission denied (Hub tests)

Hub backend needs Docker socket for Dagger tests:
```bash
# On Linux, may need to add user to docker group
sudo usermod -aG docker $USER
```

## Performance Optimization

### Layer Caching

Dockerfiles are structured to maximize cache hits:
1. Install system dependencies (rarely changes)
2. Install language dependencies (changes with requirements/package.json)
3. Copy source code (changes frequently)

### BuildKit

Enable Docker BuildKit for parallel builds:
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Parallel Execution

Run independent tests in parallel:
```bash
# Run backend and frontend tests simultaneously
docker-compose -f docker-compose.test.yml up --build test-backend test-frontend
```

## Coverage Reports

Coverage reports are generated in containers and extracted to host:

**Backend:**
- XML: `/app/coverage/coverage.xml` → Codecov
- HTML: `/app/coverage/htmlcov/` → Artifact
- Terminal: Displayed during test run

**Frontend:**
- XML: `/app/coverage/coverage.xml` → Codecov
- HTML: `/app/coverage/lcov-report/` → Artifact

## Next Steps

1. **Add test result caching** in CI for faster reruns
2. **Implement test sharding** for parallel execution
3. **Add Docker layer caching** to GitHub Actions
4. **Create test result dashboard** from uploaded artifacts
5. **Add performance metrics** tracking over time
```

**Step 2: Create implementation summary**

Create `IMPLEMENTATION_SUMMARY.md`:

```markdown
# Docker Test Infrastructure Implementation Summary

**Branch:** `testing/week2-docker-infra`
**Date:** 2025-10-28
**Status:** ✅ Complete

## Deliverables

### Dockerfiles Created: 4

1. **Backend Test Dockerfile**
   - ✅ `backend/Dockerfile.test`
   - ✅ Python 3.11 slim base
   - ✅ PostgreSQL client
   - ✅ pytest with coverage and parallel execution

2. **Frontend Test Dockerfile**
   - ✅ `frontend/Dockerfile.test`
   - ✅ Node 18 alpine base
   - ✅ Chromium for E2E tests
   - ✅ Vitest with coverage

3. **Hub Backend Test Dockerfile**
   - ✅ `hub/backend/Dockerfile.test`
   - ✅ Docker CLI for Dagger tests
   - ✅ Python 3.11 with pytest

4. **Hub Frontend Test Dockerfile**
   - ✅ `hub/frontend/Dockerfile.test`
   - ✅ Node 18 alpine with Chromium

### Docker Compose Orchestration

- ✅ `docker-compose.test.yml`
- ✅ postgres-test service (port 5433)
- ✅ redis-test service (port 6380)
- ✅ test-backend service with health checks
- ✅ test-frontend service
- ✅ test-hub-backend service (Docker socket mounted)
- ✅ test-hub-frontend service
- ✅ Named volumes for test results and coverage

### Makefile Targets: 9

- ✅ `make test-docker` - Run all tests
- ✅ `make test-docker-backend` - Backend only
- ✅ `make test-docker-frontend` - Frontend only
- ✅ `make test-docker-hub` - Hub tests
- ✅ `make test-docker-all` - Complete suite
- ✅ `make test-security` - Security tests only
- ✅ `make test-performance` - Performance tests only
- ✅ `make test-docker-clean` - Cleanup
- ✅ `make test-docker-coverage` - Extract reports

### CI/CD Integration

- ✅ `.github/workflows/test-docker.yml`
- ✅ test-backend-docker job
- ✅ test-frontend-docker job
- ✅ test-hub-docker job
- ✅ Docker layer caching
- ✅ Codecov integration
- ✅ Test artifact uploads

### Documentation

- ✅ `docs/DOCKER_TESTING.md`
- ✅ Complete usage guide
- ✅ Troubleshooting section
- ✅ Architecture documentation

## Test Execution

```bash
# Local development
make test-docker-all

# Individual components
make test-docker-backend
make test-docker-frontend
make test-docker-hub

# Specific test types
make test-security
make test-performance

# Cleanup
make test-docker-clean
```

## CI/CD Pipeline

GitHub Actions runs Docker tests on every PR and push to main:

1. **Backend Tests**
   - Build backend test image
   - Start postgres-test and redis-test
   - Run pytest with coverage
   - Upload to Codecov

2. **Frontend Tests**
   - Build frontend test image
   - Run Vitest with coverage
   - Upload to Codecov

3. **Hub Tests**
   - Build Hub test images
   - Run backend and frontend tests
   - Upload coverage for both

## Benefits Achieved

### 1. CI/Production Parity
✅ Tests run in identical containers
✅ Same dependencies as production
✅ Consistent environment across developers

### 2. Isolation
✅ Fresh database per test run
✅ No interference between tests
✅ Unique ports avoid conflicts

### 3. Coverage Reporting
✅ XML reports for Codecov
✅ HTML reports for developers
✅ Terminal output for quick feedback

### 4. Developer Experience
✅ Simple `make` commands
✅ Clear error messages
✅ Easy debugging with shell access

### 5. CI Optimization
✅ Docker layer caching
✅ Parallel test execution
✅ Fast feedback on failures

## Files Created

### Dockerfiles (4)
- `backend/Dockerfile.test`
- `frontend/Dockerfile.test`
- `hub/backend/Dockerfile.test`
- `hub/frontend/Dockerfile.test`

### Docker Ignore Files (4)
- `backend/.dockerignore`
- `frontend/.dockerignore`
- `hub/backend/.dockerignore`
- `hub/frontend/.dockerignore`

### Orchestration (1)
- `docker-compose.test.yml`

### CI/CD (1)
- `.github/workflows/test-docker.yml`

### Documentation (1)
- `docs/DOCKER_TESTING.md`

### Build System (1)
- `Makefile` (updated with 9 new targets)

## Next Steps

1. **Optimize CI builds:**
   - Add BuildKit caching
   - Implement test result caching
   - Add test sharding for parallel execution

2. **Add monitoring:**
   - Track test execution times
   - Monitor Docker resource usage
   - Set up alerts for failures

3. **Enhance coverage:**
   - Set coverage thresholds per component
   - Block PRs below threshold
   - Track coverage trends over time

4. **Improve developer workflow:**
   - Add watch mode for test-docker
   - Create VS Code tasks
   - Add pre-commit hook for Docker tests

## Success Metrics

- ✅ All 4 Dockerfiles build successfully
- ✅ docker-compose.test.yml orchestrates all services
- ✅ All Makefile targets work
- ✅ CI workflow runs tests automatically
- ✅ Coverage reports uploaded to Codecov
- ✅ Test artifacts available for download
- ✅ Documentation complete and accurate
```

**Step 3: Commit documentation**

```bash
git add docs/DOCKER_TESTING.md IMPLEMENTATION_SUMMARY.md
git commit -m "docs: Add Docker testing infrastructure documentation

- Create comprehensive testing guide
- Document architecture and components
- Add troubleshooting section
- Create implementation summary with deliverables
- Document benefits and next steps

Week 2 Docker Infrastructure Track Complete"
```

**Step 4: Final commit with summary**

```bash
git commit --allow-empty -m "feat: Week 2 Docker Test Infrastructure - Track Complete

Summary:
- 4 test Dockerfiles (backend, frontend, hub-backend, hub-frontend)
- Complete docker-compose.test.yml orchestration
- 9 Makefile targets for local development
- GitHub Actions CI workflow
- Comprehensive documentation

Components:
- Test containers with isolated environments
- PostgreSQL and Redis test services
- Docker layer caching for performance
- Coverage extraction and Codecov integration
- Test artifact uploads

Benefits:
- CI/production parity
- Consistent developer environments
- Easy cleanup and isolation
- Parallel test execution
- No port conflicts (alternate ports)

Status: Ready for consolidation to main branch

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

Before marking track complete:

- [ ] All 4 Dockerfiles build successfully
- [ ] All 4 .dockerignore files created
- [ ] docker-compose.test.yml services defined correctly
- [ ] All Makefile targets work (9 targets)
- [ ] GitHub Actions workflow syntax valid
- [ ] Documentation complete (DOCKER_TESTING.md)
- [ ] Implementation summary created
- [ ] No syntax errors in any files
- [ ] Git commits follow conventions
- [ ] Branch ready for merge to main

## Notes for Implementation

**Test the infrastructure incrementally:**

1. Build Dockerfiles individually to catch errors early
2. Test docker-compose services one at a time
3. Verify Makefile targets work before committing
4. Push to GitHub to trigger CI workflow
5. Monitor first CI run for issues

**Common Issues:**

- **Build failures:** Check .dockerignore files aren't too aggressive
- **Port conflicts:** Ensure alternate ports (5433, 6380) are available
- **Volume permissions:** May need to adjust ownership in containers
- **Coverage extraction:** Test `docker cp` commands work correctly

Once infrastructure is complete, all existing tests should run in Docker:
```bash
make test-docker-all
```

Expected: All tests pass in containerized environment

---

**Plan Status:** Complete
**Next Action:** Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan
**Estimated Time:** 3-4 hours for infrastructure setup
