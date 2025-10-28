# CI/CD Workflows Documentation

This document explains the CI/CD workflows for CommandCenter, including how to run tests locally, debug failures, and understand the pipeline.

## Table of Contents

- [Overview](#overview)
- [Workflows](#workflows)
- [Running Tests Locally](#running-tests-locally)
- [Debugging CI Failures](#debugging-ci-failures)
- [Expected Runtimes](#expected-runtimes)
- [Caching Strategy](#caching-strategy)
- [Coverage Tracking](#coverage-tracking)

## Overview

CommandCenter uses GitHub Actions for continuous integration and testing. The CI pipeline is designed for:

- **Fast Feedback**: Smoke tests provide results in 3-5 minutes
- **Comprehensive Testing**: Full CI pipeline covers all test layers
- **Parallel Execution**: Backend, frontend, and E2E tests run in parallel
- **Efficient Caching**: Dependencies and build artifacts are cached

## Workflows

### 1. Smoke Tests (`.github/workflows/smoke-tests.yml`)

**Purpose**: Fast feedback on PRs

**Triggers**:
- Pull request creation/update
- Push to main/develop

**What it does**:
- Backend: Black, Flake8, MyPy, unit tests only
- Frontend: ESLint, TypeScript check, unit tests only
- **Skips**: Integration tests, E2E tests, database setup

**Expected runtime**: 3-5 minutes

**When to use**:
- Quick validation before requesting review
- Pre-commit checks for fast iteration
- Verifying code style and basic correctness

**How to run locally**:

```bash
# Backend smoke checks
cd backend
black --check app/
flake8 app/ --max-line-length=100 --exclude=__pycache__,migrations --ignore=E203,W503
mypy app/ --ignore-missing-imports --no-strict-optional
pytest -v -m "not integration and not e2e" tests/unit/

# Frontend smoke checks
cd frontend
npm run lint
npm run type-check
npm test -- --run
```

### 2. Full CI Pipeline (`.github/workflows/ci.yml`)

**Purpose**: Comprehensive quality checks and testing

**Triggers**:
- Push to main/develop
- Pull request to main/develop

**Jobs** (run in parallel):

#### Backend Tests (8-10 minutes)
- Code formatting (Black)
- Linting (Flake8)
- Type checking (MyPy)
- Security scanning (Bandit, Safety)
- Unit + Integration tests with coverage
- Coverage upload to Codecov

#### Frontend Tests (5-7 minutes)
- Linting (ESLint)
- Type checking (TypeScript)
- Unit tests with coverage
- Build verification
- Coverage upload to Codecov

#### Docker Build (3-5 minutes)
- Build backend image
- Build frontend image
- Layer caching via GitHub Actions cache

#### Integration Tests (5-7 minutes)
- Full docker-compose stack
- Health checks
- End-to-end API tests

#### Security Scan (2-3 minutes)
- Trivy vulnerability scanning
- Results uploaded to GitHub Security tab

**Total runtime**: ~20-25 minutes (jobs run in parallel)

**How to run locally**:

```bash
# Backend tests
cd backend
pip install -r requirements-dev.txt
pytest -v --cov=app --cov-report=xml --cov-report=html

# Frontend tests
cd frontend
npm ci
npm test -- --run --coverage
npm run build

# Integration tests
docker-compose up -d
# Wait for services to be healthy
docker-compose exec backend pytest test_api.py -v
docker-compose down -v
```

### 3. E2E Tests (`.github/workflows/e2e-tests.yml`)

**Purpose**: End-to-end browser testing with Playwright

**Triggers**:
- Push to main/develop
- Pull request to main/develop
- Manual trigger (workflow_dispatch)

**Browser matrix**:
- Chromium
- Firefox
- WebKit

**Mobile testing**: Separate job for mobile viewports

**Expected runtime**: 10-15 minutes per browser (parallelized)

**What it tests**:
- Complete user workflows
- Cross-browser compatibility
- Mobile responsiveness
- Real browser rendering

**How to run locally**:

```bash
# Start services
docker-compose up -d

# Run E2E tests
cd e2e
npm ci
npx playwright install
npx playwright test

# Run specific browser
npx playwright test --project=chromium

# Run in headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

## Debugging CI Failures

### 1. Check Workflow Summary

- Go to the Actions tab in GitHub
- Click on the failed workflow run
- Review the job summary to see which jobs failed

### 2. Download Artifacts

For failed runs, download artifacts to investigate:

- **Backend test results**: `pytest-results.xml`, HTML coverage report
- **Frontend test results**: Coverage reports
- **E2E test results**: Screenshots, videos, HTML reports
- **Security reports**: Bandit and Safety scan results

### 3. Common Failure Scenarios

#### Backend Tests Failing

**Symptom**: Backend job fails

**Possible causes**:
- Code style issues (Black, Flake8)
- Type errors (MyPy)
- Test failures
- Security vulnerabilities

**How to debug**:

```bash
cd backend

# Check formatting
black --check --diff app/

# Check linting
flake8 app/ --max-line-length=100

# Check types
mypy app/ --ignore-missing-imports --no-strict-optional

# Run tests locally
pytest -v --cov=app
```

#### Frontend Tests Failing

**Symptom**: Frontend job fails

**Possible causes**:
- Linting errors
- TypeScript type errors
- Component test failures
- Build errors

**How to debug**:

```bash
cd frontend

# Check linting
npm run lint

# Check types
npm run type-check

# Run tests
npm test

# Try building
npm run build
```

#### E2E Tests Failing

**Symptom**: E2E job fails

**Possible causes**:
- Services not starting properly
- Timing issues (race conditions)
- UI changes breaking selectors
- Browser-specific issues

**How to debug**:

```bash
# 1. Download artifacts from failed run
# 2. Review screenshots in playwright-report/
# 3. Check test-results/ for detailed logs

# Run locally in debug mode
cd e2e
npx playwright test --debug

# Run with headed browser
npx playwright test --headed

# Run specific test
npx playwright test tests/smoke.spec.ts
```

#### Docker Build Failing

**Symptom**: Docker build job fails

**Possible causes**:
- Dockerfile syntax errors
- Missing dependencies
- Build context issues

**How to debug**:

```bash
# Build backend locally
docker build -f backend/Dockerfile -t test-backend backend/

# Build frontend locally
docker build -f frontend/Dockerfile --target production -t test-frontend frontend/

# Check docker-compose
docker-compose config
```

### 4. Viewing Logs

**In GitHub Actions**:
- Click on the failed step to expand logs
- Use the search box to find specific errors
- Download raw logs for offline viewing

**Locally**:

```bash
# Backend logs
docker-compose logs backend

# Frontend logs
docker-compose logs frontend

# All logs
docker-compose logs

# Follow logs
docker-compose logs -f
```

## Expected Runtimes

### Before Improvements (Baseline)

- **Full CI**: ~45 minutes
- **E2E Tests**: ~30 minutes
- **No smoke tests**: Had to run full CI for every PR

### After Improvements (Current)

| Workflow | Runtime | Improvement |
|----------|---------|-------------|
| Smoke Tests | 3-5 min | New (fast feedback) |
| Backend Tests | 8-10 min | 40% faster (caching) |
| Frontend Tests | 5-7 min | 30% faster (caching) |
| Docker Build | 3-5 min | 50% faster (layer caching) |
| E2E Tests | 10-15 min | 50% faster (browser caching) |
| **Total CI** | **20-25 min** | **~50% reduction** |

### Runtime Breakdown by Stage

**Smoke Tests (3-5 min)**:
- Backend: 2-3 min
- Frontend: 1-2 min

**Full CI Pipeline (20-25 min, parallel)**:
- Backend tests: 8-10 min
- Frontend tests: 5-7 min
- Docker builds: 3-5 min
- Integration tests: 5-7 min
- Security scan: 2-3 min

**E2E Tests (10-15 min per browser)**:
- Service startup: 2-3 min
- Test execution: 8-12 min

## Caching Strategy

### Dependency Caching

**Python (pip)**:
```yaml
uses: actions/setup-python@v5
with:
  cache: 'pip'
  cache-dependency-path: |
    backend/requirements.txt
    backend/requirements-dev.txt
```

**Node.js (npm)**:
```yaml
uses: actions/setup-node@v4
with:
  cache: 'npm'
  cache-dependency-path: frontend/package-lock.json
```

### Docker Layer Caching

```yaml
uses: docker/build-push-action@v5
with:
  cache-from: type=gha
  cache-to: type=gha,mode=max
```

### Playwright Browser Caching

```yaml
uses: actions/cache@v4
with:
  path: ~/.cache/ms-playwright
  key: playwright-${{ runner.os }}-${{ version }}-${{ browser }}
```

### Cache Invalidation

Caches are automatically invalidated when:
- Dependency files change (requirements.txt, package-lock.json)
- Playwright version changes
- Cache expires (7 days of inactivity)

## Coverage Tracking

### Codecov Integration

Coverage is tracked using Codecov with separate flags for backend and frontend.

**Configuration**: `codecov.yml`

**Coverage targets**:
- Backend: 80% (project), 85% (patch)
- Frontend: 60% (project), 70% (patch)
- Overall: 70% (project), 80% (patch)

**How it works**:
1. Tests run with coverage enabled
2. Coverage reports uploaded to Codecov
3. Codecov comments on PRs with coverage changes
4. CI fails if coverage drops below threshold

### Viewing Coverage

**In Codecov dashboard**:
- https://codecov.io/gh/your-org/commandcenter
- View overall coverage
- See coverage by file and component
- Track coverage trends over time

**In PR comments**:
- Codecov bot comments on PRs
- Shows coverage changes for the PR
- Highlights uncovered lines

**Locally**:

```bash
# Backend
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

### Coverage Reports as Artifacts

Coverage reports are uploaded as GitHub Actions artifacts:

- **Backend**: HTML coverage report in `backend/htmlcov/`
- **Frontend**: Coverage reports in `frontend/coverage/`

Download from the Actions tab → Artifacts section.

## Best Practices

### For Developers

1. **Run smoke tests locally** before pushing
2. **Use pre-commit hooks** to catch issues early
3. **Review coverage reports** for new code
4. **Fix failing tests immediately** - don't accumulate technical debt

### For Reviewers

1. **Check CI status** before reviewing code
2. **Review coverage changes** in Codecov comments
3. **Require passing tests** before merging
4. **Look for security warnings** in scan results

### For CI Maintenance

1. **Monitor runtime trends** - optimize if jobs slow down
2. **Update dependencies** regularly in workflows
3. **Clear old caches** if builds behave strangely
4. **Review security scan results** weekly

## Troubleshooting

### Caching Issues

**Problem**: Dependencies not being cached

**Solution**:
```bash
# Clear cache manually in GitHub
# Settings → Actions → Caches → Delete cache

# Or update cache key by modifying dependency files
```

**Problem**: Stale cache causing test failures

**Solution**:
```bash
# Update dependency versions to invalidate cache
# Or modify cache key in workflow file
```

### Flaky Tests

**Problem**: Tests pass/fail randomly

**Solutions**:
1. Add proper waits instead of arbitrary sleeps
2. Use retry logic for flaky E2E tests
3. Mark tests as flaky with `pytest.mark.flaky`
4. Investigate race conditions

### Slow Tests

**Problem**: CI runtime increasing over time

**Solutions**:
1. Profile tests to find slow ones
2. Use database fixtures instead of migrations
3. Mock external API calls
4. Parallelize test execution
5. Split large test files

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [Playwright Documentation](https://playwright.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)

---

**Last Updated**: 2025-10-28
**Maintainer**: Development Team
**Next Review**: After Week 1 of testing implementation
