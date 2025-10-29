# Week 3 CI/CD Optimization - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce CI runtime by 50%+ through test sharding, caching, selective running, and performance monitoring

**Architecture:** Modify GitHub Actions workflows to add matrix strategy for sharding, implement multi-layer caching, add selective test detection, and create performance monitoring

**Tech Stack:** GitHub Actions, pytest, Playwright, npm, Docker

---

## Task 1: E2E Test Sharding

**Files:**
- Modify: `.github/workflows/ci.yml`

### Step 1: Back up current CI workflow

```bash
cp .github/workflows/ci.yml .github/workflows/ci.yml.backup
```

### Step 2: Add E2E sharding to workflow

**File:** `.github/workflows/ci.yml` (modify e2e-tests job)

```yaml
  e2e-tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests (shard ${{ matrix.shard }}/4)
        run: |
          npx playwright test --shard=${{ matrix.shard }}/4

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-results-${{ matrix.shard }}
          path: frontend/test-results/
```

### Step 3: Test sharding locally

```bash
# Test each shard
npx playwright test --shard=1/4
npx playwright test --shard=2/4
npx playwright test --shard=3/4
npx playwright test --shard=4/4
```

**Expected:** Each shard runs ~1/4 of total tests

### Step 4: Commit E2E sharding

```bash
git add .github/workflows/ci.yml
git commit -m "ci: Add E2E test sharding (4-way parallel)"
```

---

## Task 2: Backend Integration Test Sharding

**Files:**
- Modify: `.github/workflows/ci.yml`

### Step 1: Add backend test sharding

**File:** `.github/workflows/ci.yml` (modify backend-tests job)

```yaml
  backend-integration:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        test-group: ['api', 'services', 'db']

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run integration tests - ${{ matrix.test-group }}
        run: |
          cd backend
          pytest tests/integration/ -k "${{ matrix.test-group }}" -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend-${{ matrix.test-group }}
```

### Step 2: Verify test grouping

```bash
cd backend
pytest tests/integration/ -k "api" --collect-only
pytest tests/integration/ -k "services" --collect-only
pytest tests/integration/ -k "db" --collect-only
```

### Step 3: Commit backend sharding

```bash
git add .github/workflows/ci.yml
git commit -m "ci: Add backend integration test sharding by category"
```

---

## Task 3: Python Dependency Caching

**Files:**
- Modify: `.github/workflows/ci.yml`

### Step 1: Add pip caching

**File:** `.github/workflows/ci.yml` (add to backend jobs)

```yaml
      - name: Cache Python dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
```

### Step 2: Test cache locally

Push and observe GitHub Actions to verify cache is created and used.

### Step 3: Commit pip caching

```bash
git add .github/workflows/ci.yml
git commit -m "ci: Add pip dependency caching"
```

---

## Task 4: Node.js Dependency Caching

**Files:**
- Modify: `.github/workflows/ci.yml`

### Step 1: Add npm caching

**File:** `.github/workflows/ci.yml` (add to frontend/E2E jobs)

```yaml
      - name: Cache npm dependencies
        uses: actions/cache@v3
        with:
          path: ~/.npm
          key: ${{ runner.os }}-npm-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-npm-

      - name: Install dependencies
        run: |
          cd frontend
          npm ci
```

### Step 2: Commit npm caching

```bash
git add .github/workflows/ci.yml
git commit -m "ci: Add npm dependency caching"
```

---

## Task 5: Playwright Browser Caching

**Files:**
- Modify: `.github/workflows/ci.yml`

### Step 1: Add Playwright browser caching

**File:** `.github/workflows/ci.yml` (add to E2E job)

```yaml
      - name: Get Playwright version
        id: playwright-version
        run: echo "PLAYWRIGHT_VERSION=$(node -e "console.log(require('./frontend/package-lock.json').packages['node_modules/@playwright/test'].version)")" >> $GITHUB_OUTPUT

      - name: Cache Playwright browsers
        uses: actions/cache@v3
        id: playwright-cache
        with:
          path: ~/.cache/ms-playwright
          key: ${{ runner.os }}-playwright-${{ steps.playwright-version.outputs.PLAYWRIGHT_VERSION }}

      - name: Install Playwright browsers
        if: steps.playwright-cache.outputs.cache-hit != 'true'
        run: npx playwright install --with-deps
```

### Step 2: Commit Playwright caching

```bash
git add .github/workflows/ci.yml
git commit -m "ci: Add Playwright browser caching"
```

---

## Task 6: Docker Layer Caching

**Files:**
- Modify: `.github/workflows/test-docker.yml`

### Step 1: Add Docker Buildx caching

**File:** `.github/workflows/test-docker.yml` (modify)

```yaml
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Cache Docker layers
        uses: actions/cache@v3
        with:
          path: /tmp/.buildx-cache
          key: ${{ runner.os }}-buildx-${{ hashFiles('backend/requirements.txt', 'frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-buildx-

      - name: Build backend test image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          file: ./backend/Dockerfile.test
          push: false
          cache-from: type=local,src=/tmp/.buildx-cache
          cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max

      - name: Move cache
        run: |
          rm -rf /tmp/.buildx-cache
          mv /tmp/.buildx-cache-new /tmp/.buildx-cache
```

### Step 2: Commit Docker caching

```bash
git add .github/workflows/test-docker.yml
git commit -m "ci: Add Docker layer caching for test images"
```

---

## Task 7: Selective Test Running (pytest-picked)

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `.github/workflows/ci.yml`

### Step 1: Add pytest-picked to requirements

**File:** `backend/requirements.txt` (append)

```
pytest-picked==0.5.0
```

### Step 2: Add selective test job for PRs

**File:** `.github/workflows/ci.yml` (add new job)

```yaml
  backend-affected-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'

    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Need full history for git diff

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache pip
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run affected tests only
        run: |
          cd backend
          git diff --name-only origin/${{ github.base_ref }}...HEAD | grep "\.py$" || true
          pytest --picked --mode=branch -v
```

### Step 3: Test locally

```bash
cd backend
# Make a change to a file
touch app/services/test_change.py
pytest --picked --mode=unstaged
```

### Step 4: Commit selective testing

```bash
git add backend/requirements.txt .github/workflows/ci.yml
git commit -m "ci: Add selective test running with pytest-picked"
```

---

## Task 8: Smoke Test Job (Fast Feedback)

**Files:**
- Modify: `.github/workflows/ci.yml`

### Step 1: Add smoke test job

**File:** `.github/workflows/ci.yml` (add new job at top)

```yaml
  smoke-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache pip
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements.txt') }}

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run health check test
        run: |
          cd backend
          pytest tests/integration/test_health_check.py -v

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Cache npm
        uses: actions/cache@v3
        with:
          path: ~/.npm
          key: ${{ runner.os }}-npm-${{ hashFiles('frontend/package-lock.json') }}

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - name: Run frontend smoke tests
        run: |
          cd frontend
          npm test -- --run Dashboard.test
```

### Step 2: Commit smoke tests

```bash
git add .github/workflows/ci.yml
git commit -m "ci: Add smoke test job for fast PR feedback (<5 min)"
```

---

## Task 9: Performance Monitoring

**Files:**
- Create: `backend/tests/conftest.py` (modifications)
- Modify: `.github/workflows/ci.yml`

### Step 1: Add test duration tracking

**File:** `backend/tests/conftest.py` (append)

```python
import time
import pytest
import json
from pathlib import Path

# Track slow tests
@pytest.fixture(scope="function", autouse=True)
def track_test_duration(request):
    """Track test duration and flag slow tests."""
    start = time.time()
    yield
    duration = time.time() - start

    if duration > 5.0:
        print(f"\n⚠️  Slow test: {request.node.name} took {duration:.2f}s")

    # Save timing data
    timing_file = Path("test-timings.json")
    timings = {}
    if timing_file.exists():
        with open(timing_file, 'r') as f:
            timings = json.load(f)

    timings[request.node.nodeid] = duration

    with open(timing_file, 'w') as f:
        json.dump(timings, f, indent=2)
```

### Step 2: Add duration reporting to CI

**File:** `.github/workflows/ci.yml` (add to backend jobs)

```yaml
      - name: Run tests with duration tracking
        run: |
          cd backend
          pytest --durations=10 --durations-min=1.0

      - name: Upload timing data
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-timings
          path: backend/test-timings.json
```

### Step 3: Create performance regression check

**File:** `.github/workflows/ci.yml` (add job)

```yaml
  performance-check:
    runs-on: ubuntu-latest
    needs: [backend-tests]
    if: always()

    steps:
      - name: Download timing data
        uses: actions/download-artifact@v3
        with:
          name: test-timings

      - name: Check for performance regressions
        run: |
          # Simple check: fail if any test > 10 seconds
          python3 << 'EOF'
          import json
          with open('test-timings.json', 'r') as f:
              timings = json.load(f)

          slow_tests = {k: v for k, v in timings.items() if v > 10.0}

          if slow_tests:
              print("❌ Performance regression detected!")
              for test, duration in slow_tests.items():
                  print(f"  {test}: {duration:.2f}s (limit: 10s)")
              exit(1)
          else:
              print("✅ No performance regressions")
          EOF
```

### Step 4: Commit performance monitoring

```bash
git add backend/tests/conftest.py .github/workflows/ci.yml
git commit -m "ci: Add performance monitoring and regression detection"
```

---

## Task 10: Workflow Optimization

**Files:**
- Modify: `.github/workflows/ci.yml`

### Step 1: Add job dependencies

Optimize job ordering to provide fast feedback:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Fast feedback first
  smoke-tests:
    runs-on: ubuntu-latest
    # ... (defined earlier)

  # Parallel test execution
  backend-unit:
    needs: [smoke-tests]
    runs-on: ubuntu-latest
    # ... unit tests only

  backend-integration:
    needs: [smoke-tests]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-group: ['api', 'services', 'db']
    # ... (defined earlier)

  e2e-tests:
    needs: [smoke-tests]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    # ... (defined earlier)

  # Performance check runs after all tests
  performance-check:
    needs: [backend-unit, backend-integration, e2e-tests]
    runs-on: ubuntu-latest
    # ... (defined earlier)
```

### Step 2: Add concurrency limits

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### Step 3: Commit workflow optimization

```bash
git add .github/workflows/ci.yml
git commit -m "ci: Optimize workflow with job dependencies and concurrency"
```

---

## Task 11: Documentation

**Files:**
- Create: `docs/CI_OPTIMIZATION.md`

### Step 1: Document CI improvements

**File:** `docs/CI_OPTIMIZATION.md`

```markdown
# CI/CD Optimization - Week 3

## Improvements Implemented

### Test Sharding
- **E2E Tests**: 4-way parallel sharding (30min → 8-10min)
- **Backend Integration**: 3-way sharding by category (api, services, db)

### Caching Strategy
- **Python**: pip cache (~2min saved per run)
- **Node.js**: npm cache (~1min saved per run)
- **Playwright**: Browser cache (~3min saved per run)
- **Docker**: Layer caching (~5min saved per run)

### Selective Testing
- **pytest-picked**: Run only affected tests on PRs
- **Smoke tests**: <5min fast feedback job

### Performance Monitoring
- **Duration tracking**: All tests timed automatically
- **Regression detection**: Fail if any test >10s
- **Reporting**: Test timings uploaded as artifacts

## Target Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| E2E runtime | ~30 min | <10 min | 67% faster |
| Total CI time | ~45 min | <25 min | 44% faster |
| Cache hit rate | 0% | >80% | Significant |
| Smoke tests | N/A | <5 min | Fast feedback |

## Usage

### Running Locally

```bash
# Test sharding
npx playwright test --shard=1/4

# Selective tests
pytest --picked --mode=branch

# Duration tracking
pytest --durations=10
```

### CI Workflow

1. **Smoke tests** run first (5min)
2. **Parallel test suites** run simultaneously
3. **Performance check** validates no regressions
4. **Artifacts** uploaded for analysis
```

### Step 2: Commit documentation

```bash
git add docs/CI_OPTIMIZATION.md
git commit -m "docs: Document CI/CD optimization improvements"
```

---

## Task 12: Verification

### Step 1: Push to feature branch

```bash
git push origin testing/week3-cicd
```

### Step 2: Create test PR

Create a PR to verify:
- Smoke tests run in <5min
- Test sharding works correctly
- Caching is effective
- Performance monitoring triggers

### Step 3: Monitor CI run

Check GitHub Actions to verify:
- [ ] Smoke test job completes in <5min
- [ ] E2E tests run in 4 parallel shards
- [ ] Backend integration tests shard by category
- [ ] Cache hit rates >80%
- [ ] Performance check passes
- [ ] Total runtime <25min

### Step 4: Document actual results

Update `docs/CI_OPTIMIZATION.md` with actual metrics from CI run.

### Step 5: Final commit

```bash
git add docs/CI_OPTIMIZATION.md
git commit -m "docs: Add actual CI performance metrics from test run"
```

---

## Verification Checklist

- [ ] E2E tests shard 4 ways
- [ ] Backend tests shard by category
- [ ] All caching implemented (pip, npm, Playwright, Docker)
- [ ] Selective test running works
- [ ] Smoke test job <5min
- [ ] Performance monitoring active
- [ ] Workflow optimized with dependencies
- [ ] Documentation complete
- [ ] Actual metrics recorded

---

## Success Criteria

✅ **E2E runtime <10 minutes** (from ~30 min)
✅ **Total CI time <25 minutes** (from ~45 min)
✅ **Cache hit rate >80%**
✅ **Smoke tests <5 minutes**
✅ **Performance regressions detected**
✅ **Documentation complete**

**Ready to merge to main!**
