# GitHub Actions Workflows

Quick reference for CommandCenter CI/CD workflows.

## Workflows

| Workflow | File | Trigger | Runtime | Purpose |
|----------|------|---------|---------|---------|
| **Smoke Tests** | `smoke-tests.yml` | PR create/update | 3-5 min | Fast feedback - linting + basic tests |
| **Full CI** | `ci.yml` | Push/PR to main/develop | 20-25 min | Comprehensive testing + coverage |
| **E2E Tests** | `e2e-tests.yml` | Push/PR to main/develop | 10-15 min | Browser testing (3 browsers) |
| **Integration Tests** | `integration-tests.yml` | Push/PR to main/develop | 5-7 min | Full stack integration |

## Quick Commands

### Run Smoke Tests Locally

```bash
# Backend
cd backend && black --check app/ && flake8 app/ && pytest -m "not integration" tests/unit/

# Frontend
cd frontend && npm run lint && npm run type-check && npm test
```

### Run Full CI Locally

```bash
# Backend
cd backend && pytest --cov=app --cov-report=html

# Frontend
cd frontend && npm test -- --coverage && npm run build

# E2E
docker-compose up -d && cd e2e && npx playwright test
```

## Expected Runtimes

### With Caching (warm cache)
- Smoke tests: **3-5 minutes**
- Backend tests: **8-10 minutes**
- Frontend tests: **5-7 minutes**
- E2E tests: **10-15 minutes**
- Full CI: **20-25 minutes**

### Without Caching (cold cache)
- Smoke tests: **5-7 minutes**
- Backend tests: **12-15 minutes**
- Frontend tests: **8-10 minutes**
- E2E tests: **15-20 minutes**
- Full CI: **35-40 minutes**

## Debugging Failures

1. **Check the Actions tab** - Review job summary
2. **Download artifacts** - Screenshots, coverage reports, logs
3. **Run locally** - Use commands above to reproduce
4. **Check cache** - May need to clear if stale

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Black fails | Code not formatted | Run `black app/` locally |
| Flake8 fails | Linting errors | Run `flake8 app/` and fix |
| MyPy fails | Type errors | Run `mypy app/` and fix |
| Tests fail | Logic errors | Run `pytest -v` locally |
| E2E fails | Timing/selectors | Run `npx playwright test --debug` |
| Docker build fails | Dockerfile errors | Build locally with `docker build` |

## Coverage Thresholds

| Component | Target | Threshold |
|-----------|--------|-----------|
| Backend (project) | 80% | ±2% |
| Backend (patch) | 85% | ±3% |
| Frontend (project) | 60% | ±3% |
| Frontend (patch) | 70% | ±5% |

## Caching Strategy

- **pip**: Cached by requirements.txt hash
- **npm**: Cached by package-lock.json hash
- **Docker layers**: Cached via GitHub Actions cache
- **Playwright browsers**: Cached by version + browser type

## Documentation

For detailed information, see:
- **Full documentation**: `docs/CI_WORKFLOWS.md`
- **Testing plan**: `docs/plans/2025-10-28-streamlined-testing-plan.md`
- **Codecov config**: `codecov.yml`

---

**Quick Links**:
- [Actions Tab](../../actions)
- [Security Tab](../../security)
- [Codecov Dashboard](https://codecov.io/gh/your-org/commandcenter)
