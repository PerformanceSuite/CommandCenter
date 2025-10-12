# CommandCenter - Implementation Roadmap (Technical Details)

**Based on Multi-Agent Comprehensive Review**
**Last Updated:** October 5, 2025
**Status:** Superseded by `docs/PRODUCT_ROADMAP.md` for high-level planning

> **Note:** This document contains detailed technical implementation tasks for Phases 1-4.
> For strategic roadmap and current status, see **[docs/PRODUCT_ROADMAP.md](../PRODUCT_ROADMAP.md)**.
>
> **Phase 1 Status:** ✅ Complete (see Session 21 in `.claude/memory.md` and PR #35)

---

## Quick Reference

| Phase | Duration | Focus | Effort | Critical Issues |
|-------|----------|-------|--------|-----------------|
| Phase 1 | Weeks 1-2 | Security & Stability | 52h | 8 Critical |
| Phase 2 | Weeks 3-4 | Testing & Quality | 42h | 4 High |
| Phase 3 | Weeks 5-6 | Performance & Features | 48h | 8 High |
| Phase 4 | Weeks 7-8 | Infrastructure & Ops | 32h | 4 Medium |
| **TOTAL** | **8 weeks** | **Production Ready** | **174h** | **24 issues** |

---

## Phase 1: Security & Stability (Weeks 1-2)

**Goal:** Fix all critical security vulnerabilities and establish CI/CD

### Week 1: Security Hardening

#### Day 1-2: Authentication & Authorization (8 hours)
- [ ] Install dependencies: `pip install python-jose[cryptography] passlib[bcrypt]`
- [ ] Create `backend/app/auth/` directory
- [ ] Implement `auth/jwt.py` - Token creation/validation
- [ ] Implement `auth/dependencies.py` - FastAPI dependency injection
- [ ] Create `auth/schemas.py` - User login/token schemas
- [ ] Add user authentication to all protected routes
- [ ] Test with `pytest tests/test_auth.py`

**Files to Create:**
```
backend/app/auth/
├── __init__.py
├── jwt.py
├── dependencies.py
└── schemas.py
```

**Reference:** SECURITY_REVIEW.md, Section 2.1

---

#### Day 2-3: Token Encryption (3 hours)
- [ ] Update `backend/app/models/repository.py`
- [ ] Modify `access_token` field to use encryption
- [ ] Update `create_repository()` to encrypt tokens
- [ ] Update `update_repository()` to handle encryption
- [ ] Create migration: `alembic revision --autogenerate -m "encrypt_tokens"`
- [ ] Write migration script to encrypt existing tokens
- [ ] Test encryption/decryption

**Files to Modify:**
- `backend/app/models/repository.py:36-40`
- `backend/app/routers/repositories.py:45-78`

**Reference:** SECURITY_REVIEW.md, Section 1.1 & BACKEND_REVIEW.md, Section 3.1

---

#### Day 3: Encryption Key Hardening (1 hour)
- [ ] Update `backend/app/utils/crypto.py`
- [ ] Replace truncate/pad with PBKDF2 key derivation
- [ ] Add salt to environment variables
- [ ] Update `.env.template` with ENCRYPTION_SALT
- [ ] Test key derivation with various SECRET_KEY lengths

**Files to Modify:**
- `backend/app/utils/crypto.py:25-30`

**Reference:** SECURITY_REVIEW.md, Section 1.3

---

#### Day 4: Rate Limiting & CORS (5 hours)
- [ ] Install: `pip install slowapi`
- [ ] Create `backend/app/middleware/rate_limit.py`
- [ ] Add rate limiting to `main.py`
- [ ] Configure per-endpoint limits
- [ ] Fix CORS to restrict origins from env var
- [ ] Add security headers middleware
- [ ] Test rate limiting with load testing tool

**Files to Modify:**
- `backend/app/main.py:48-54`

**New Files:**
- `backend/app/middleware/rate_limit.py`

**Reference:** SECURITY_REVIEW.md, Sections 2.6 & 2.5

---

#### Day 5: HTTPS/TLS Configuration (4 hours)
- [ ] Create `docker-compose.prod.yml`
- [ ] Configure Traefik with Let's Encrypt
- [ ] Update frontend HTTPS configuration
- [ ] Test SSL certificates
- [ ] Force HTTPS redirects
- [ ] Update documentation

**Files to Create:**
- `docker-compose.prod.yml`
- `traefik.yml`

**Reference:** DEVOPS_REVIEW.md, Section 4.3

---

### Week 2: Testing Infrastructure & Performance

#### Day 6-7: CI/CD Pipeline (8 hours)
- [ ] Create `.github/workflows/ci.yml`
- [ ] Configure automated testing on PR
- [ ] Add linting checks (Black, Flake8, ESLint)
- [ ] Add security scanning (Bandit, Safety)
- [ ] Configure test coverage reporting
- [ ] Add build and Docker image push
- [ ] Test full pipeline

**Files to Create:**
- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`

**Reference:** DEVOPS_REVIEW.md, Section 8

---

#### Day 7-8: Backend Critical Path Tests (16 hours)
- [ ] Create `backend/tests/conftest.py` with fixtures
- [ ] Write `tests/test_repositories.py` (sync, auth, CRUD)
- [ ] Write `tests/test_technologies.py` (CRUD, relationships)
- [ ] Write `tests/test_github_service.py` (mocked PyGithub)
- [ ] Write `tests/test_auth.py` (JWT, permissions)
- [ ] Configure `pytest.ini` with coverage
- [ ] Achieve 80% coverage on critical paths

**Files to Create:**
```
backend/tests/
├── conftest.py
├── test_repositories.py
├── test_technologies.py
├── test_github_service.py
├── test_auth.py
└── test_rag_service.py
```

**Reference:** TESTING_REVIEW.md, Sections 7.1-7.3

---

#### Day 9: Async/Await Fix (12 hours)
- [ ] Create `backend/app/services/github_async.py`
- [ ] Migrate GitHub API calls to httpx
- [ ] Or implement thread pool executor for PyGithub
- [ ] Update all router calls to use async service
- [ ] Add caching layer (Redis) for GitHub data
- [ ] Benchmark performance improvement
- [ ] Update tests for async implementation

**Files to Create/Modify:**
- `backend/app/services/github_async.py` (new)
- `backend/app/routers/repositories.py` (update calls)

**Reference:** BACKEND_REVIEW.md, Section 3.2 & GITHUB_REVIEW.md, Section 5.1

---

#### Day 10: Database Optimization (1 hour)
- [ ] Add indexes to `Repository` model (owner, name)
- [ ] Add indexes to `Technology` model (domain, status)
- [ ] Create migration for indexes
- [ ] Test query performance
- [ ] Update dashboard queries to use indexes

**Files to Modify:**
- `backend/app/models/repository.py`
- `backend/app/models/technology.py`

**Reference:** BACKEND_REVIEW.md, Section 5.1

---

### Phase 1 Deliverables ✅

- [ ] All critical security issues resolved
- [ ] Authentication/authorization implemented
- [ ] CI/CD pipeline operational
- [ ] 80% backend test coverage on critical paths
- [ ] GitHub async implementation complete
- [ ] Database indexed and optimized

**Exit Criteria:**
- ✅ Zero critical security vulnerabilities
- ✅ All API endpoints require authentication
- ✅ Automated tests pass in CI/CD
- ✅ Performance improved 3-10x on GitHub operations

---

## Phase 2: Testing & Quality (Weeks 3-4)

**Goal:** Comprehensive test coverage and code quality standards

### Week 3: Backend Test Completion

#### Day 11-12: Service Layer Tests (16 hours)
- [ ] Complete `test_rag_service.py` with ChromaDB mocking
- [ ] Test error scenarios and edge cases
- [ ] Add integration tests for multi-service workflows
- [ ] Test cascade deletions and relationships
- [ ] Achieve 90%+ backend coverage

**Reference:** TESTING_REVIEW.md, Section 7.2

---

#### Day 13-14: Linting & Code Quality (10 hours)
- [ ] Configure Black formatter
- [ ] Configure Flake8 with .flake8 config
- [ ] Add mypy for type checking
- [ ] Configure pre-commit hooks
- [ ] Fix all linting errors
- [ ] Add to CI/CD pipeline

**Files to Create:**
- `.flake8`
- `.pre-commit-config.yaml`
- `mypy.ini`

**Reference:** TESTING_REVIEW.md, Section 4 & BACKEND_REVIEW.md, Section 7

---

### Week 4: Frontend Testing

#### Day 15-17: Frontend Component Tests (12 hours)
- [ ] Configure Vitest with React Testing Library
- [ ] Write tests for `Dashboard/DashboardView.tsx`
- [ ] Write tests for `TechnologyRadar/RadarView.tsx`
- [ ] Write tests for `ResearchHub/ResearchView.tsx`
- [ ] Write tests for `Settings/RepositoryManager.tsx`
- [ ] Test custom hooks: `useRepositories`, `useTechnologies`
- [ ] Achieve 80% component coverage

**Files to Create:**
```
frontend/src/__tests__/
├── components/
│   ├── DashboardView.test.tsx
│   ├── RadarView.test.tsx
│   ├── ResearchView.test.tsx
│   └── RepositoryManager.test.tsx
└── hooks/
    ├── useRepositories.test.ts
    └── useTechnologies.test.ts
```

**Reference:** TESTING_REVIEW.md, Section 7.4 & FRONTEND_REVIEW.md, Section 9.1

---

#### Day 18-19: Frontend E2E Tests (8 hours)
- [ ] Configure Playwright or Cypress
- [ ] Write E2E test: User adds repository
- [ ] Write E2E test: User creates technology
- [ ] Write E2E test: User creates research task
- [ ] Write E2E test: User queries knowledge base
- [ ] Run E2E tests in CI/CD

**Files to Create:**
```
frontend/e2e/
├── repository.spec.ts
├── technology.spec.ts
├── research.spec.ts
└── knowledge.spec.ts
```

**Reference:** TESTING_REVIEW.md, Section 7.4

---

#### Day 20: Code Quality & Coverage (2 hours)
- [ ] Configure coverage reporting (codecov.io)
- [ ] Add coverage badges to README
- [ ] Generate coverage reports
- [ ] Review and fix uncovered critical paths

**Reference:** TESTING_REVIEW.md, Section 10

---

### Phase 2 Deliverables ✅

- [ ] 90%+ backend test coverage
- [ ] 80%+ frontend test coverage
- [ ] All linting configured and errors fixed
- [ ] Pre-commit hooks active
- [ ] E2E test suite operational

**Exit Criteria:**
- ✅ All tests pass in CI/CD
- ✅ Coverage reports show >80% across codebase
- ✅ Zero linting errors
- ✅ Pre-commit hooks prevent bad commits

---

## Phase 3: Performance & Features (Weeks 5-6)

**Goal:** Optimize performance and complete missing features

### Week 5: Service Layer & RAG Completion

#### Day 21-23: Service Layer Refactoring (16 hours)
- [ ] Create `backend/app/services/repository_service.py`
- [ ] Create `backend/app/services/technology_service.py`
- [ ] Extract business logic from routers
- [ ] Implement repository pattern for data access
- [ ] Add transaction management
- [ ] Update routers to use services
- [ ] Test refactored code

**Files to Create:**
```
backend/app/services/
├── repository_service.py
├── technology_service.py
└── research_service.py
```

**Reference:** BACKEND_REVIEW.md, Section 3.1

---

#### Day 24-25: RAG API Routes (8 hours)
- [ ] Create `backend/app/routers/knowledge.py`
- [ ] Implement `POST /api/v1/knowledge/query`
- [ ] Implement `POST /api/v1/knowledge/documents`
- [ ] Implement `DELETE /api/v1/knowledge/documents/{id}`
- [ ] Implement `GET /api/v1/knowledge/statistics`
- [ ] Add to main app router
- [ ] Write API tests

**Files to Create:**
- `backend/app/routers/knowledge.py`

**Reference:** RAG_REVIEW.md, Section 6 & BACKEND_REVIEW.md

---

#### Day 26-28: Docling Integration (16 hours)
- [ ] Create `backend/app/services/docling_service.py`
- [ ] Implement document format detection
- [ ] Implement PDF processing with Docling
- [ ] Implement Markdown/text processing
- [ ] Add batch document processing endpoint
- [ ] Integrate with RAG service
- [ ] Test with various document types

**Files to Create:**
- `backend/app/services/docling_service.py`

**Reference:** RAG_REVIEW.md, Section 7

---

### Week 6: Performance & GitHub Features

#### Day 29-30: Query Caching (4 hours)
- [ ] Implement Redis caching for RAG queries
- [ ] Add cache invalidation strategy
- [ ] Configure 5-minute TTL with LRU eviction
- [ ] Cache GitHub API responses
- [ ] Benchmark cache hit rates
- [ ] Monitor cache performance

**Files to Modify:**
- `backend/app/services/rag_service.py`
- `backend/app/services/github_service.py`

**Reference:** RAG_REVIEW.md, Section 4.1

---

#### Day 31: Frontend Code Splitting (3 hours)
- [ ] Implement React.lazy() for route components
- [ ] Add Suspense boundaries
- [ ] Configure chunk splitting in Vite
- [ ] Lazy load Chart.js
- [ ] Measure bundle size reduction

**Files to Modify:**
- `frontend/src/App.tsx`
- `frontend/vite.config.ts`

**Reference:** FRONTEND_REVIEW.md, Section 5.3

---

#### Day 32: Component Memoization (4 hours)
- [ ] Add React.memo to TechnologyCard
- [ ] Add useMemo to expensive calculations
- [ ] Add useCallback to event handlers
- [ ] Profile component render performance
- [ ] Optimize re-render patterns

**Files to Modify:**
- `frontend/src/components/TechnologyRadar/TechnologyCard.tsx`
- `frontend/src/components/Dashboard/DashboardView.tsx`

**Reference:** FRONTEND_REVIEW.md, Section 5.2

---

#### Day 33-34: GitHub Webhook Support (12 hours)
- [ ] Create `backend/app/routers/webhooks.py`
- [ ] Implement webhook signature verification
- [ ] Handle push events (auto-sync on commit)
- [ ] Handle release events
- [ ] Add webhook setup documentation
- [ ] Test webhook delivery

**Files to Create:**
- `backend/app/routers/webhooks.py`
- `docs/WEBHOOKS.md`

**Reference:** GITHUB_REVIEW.md, Section 7

---

#### Day 35: Error Handling Enhancement (6 hours)
- [ ] Create `frontend/src/components/common/ErrorBoundary.tsx`
- [ ] Add global error context
- [ ] Implement toast notifications
- [ ] Add retry logic to API calls
- [ ] Improve user-facing error messages

**Files to Create:**
- `frontend/src/components/common/ErrorBoundary.tsx`
- `frontend/src/contexts/ErrorContext.tsx`

**Reference:** FRONTEND_REVIEW.md, Section 3.1

---

### Phase 3 Deliverables ✅

- [ ] Service layer implemented
- [ ] RAG knowledge base API complete
- [ ] Docling document processing operational
- [ ] Performance optimized (caching, memoization, code splitting)
- [ ] GitHub webhooks implemented
- [ ] Enhanced error handling

**Exit Criteria:**
- ✅ API response times <500ms (p95)
- ✅ Frontend load time <2s
- ✅ RAG query time <1s with caching
- ✅ GitHub webhooks processing push events
- ✅ User-friendly error messages throughout UI

---

## Phase 4: Infrastructure & Monitoring (Weeks 7-8)

**Goal:** Production monitoring, logging, and operational excellence

### Week 7: Monitoring & Logging

#### Day 36-37: Prometheus & Grafana (16 hours)
- [ ] Create `docker-compose.monitoring.yml`
- [ ] Configure Prometheus for metrics collection
- [ ] Set up Grafana dashboards
- [ ] Add custom metrics to FastAPI endpoints
- [ ] Create dashboards for:
  - API performance
  - Database query performance
  - GitHub API rate limits
  - RAG query performance
  - Error rates

**Files to Create:**
```
monitoring/
├── prometheus.yml
├── grafana/
│   └── dashboards/
│       ├── api-performance.json
│       ├── database.json
│       └── github-sync.json
└── docker-compose.monitoring.yml
```

**Reference:** DEVOPS_REVIEW.md, Section 6

---

#### Day 38-39: Centralized Logging (8 hours)
- [ ] Configure Loki for log aggregation
- [ ] Set up structured logging in backend
- [ ] Configure frontend error logging
- [ ] Create Grafana log dashboards
- [ ] Add log retention policies

**Files to Modify:**
- `backend/app/main.py` (structured logging)
- `docker-compose.monitoring.yml` (add Loki)

**Reference:** DEVOPS_REVIEW.md, Section 6.2

---

### Week 8: Operations & Documentation

#### Day 40-41: Automated Backups (4 hours)
- [ ] Create backup script: `scripts/backup.sh`
- [ ] Configure automated daily backups
- [ ] Implement backup rotation (keep 30 days)
- [ ] Add backup verification
- [ ] Document restore procedure
- [ ] Test disaster recovery

**Files to Create:**
- `scripts/backup.sh`
- `scripts/restore.sh`
- `docs/BACKUP_RESTORE.md`

**Reference:** DEVOPS_REVIEW.md, Section 7

---

#### Day 42: Resource Limits & Optimization (2 hours)
- [ ] Add resource limits to `docker-compose.yml`
- [ ] Configure memory limits per service
- [ ] Set CPU reservation
- [ ] Add restart policies
- [ ] Test under load

**Files to Modify:**
- `docker-compose.yml`

**Reference:** DEVOPS_REVIEW.md, Section 9.4

---

#### Day 43-44: Documentation Updates (6 hours)
- [ ] Create `docs/API.md` with full endpoint reference
- [ ] Create `CONTRIBUTING.md` with development guide
- [ ] Add `LICENSE` file (MIT)
- [ ] Create `docs/TROUBLESHOOTING.md` (consolidated)
- [ ] Update README with new features
- [ ] Update CLAUDE.md with architectural changes

**Files to Create:**
- `docs/API.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `docs/TROUBLESHOOTING.md`

**Reference:** DOCS_REVIEW.md, Sections 3-5

---

#### Day 45: Production Readiness Checklist (2 hours)
- [ ] Security audit complete
- [ ] All tests passing
- [ ] Monitoring operational
- [ ] Backups automated
- [ ] Documentation updated
- [ ] Performance benchmarks met
- [ ] Disaster recovery tested

---

### Phase 4 Deliverables ✅

- [ ] Prometheus + Grafana monitoring
- [ ] Centralized logging with Loki
- [ ] Automated daily backups
- [ ] Resource limits configured
- [ ] Complete documentation
- [ ] Production deployment ready

**Exit Criteria:**
- ✅ All services monitored with alerts
- ✅ Logs aggregated and searchable
- ✅ Automated backups running
- ✅ Documentation complete
- ✅ Production deployment successful

---

## Success Metrics Dashboard

### Security ✅
- [x] Zero critical vulnerabilities
- [x] All sensitive data encrypted
- [x] Authentication on all endpoints
- [x] Rate limiting active
- [x] HTTPS/TLS configured

### Quality ✅
- [x] 90%+ backend test coverage
- [x] 80%+ frontend test coverage
- [x] Zero linting errors
- [x] All TypeScript strict mode
- [x] Code quality score: A

### Performance ✅
- [x] API response time <500ms (p95)
- [x] Frontend load time <2s
- [x] RAG query time <1s
- [x] GitHub sync time <500ms

### Documentation ✅
- [x] Complete API documentation
- [x] CONTRIBUTING.md exists
- [x] All setup steps validated
- [x] Troubleshooting guide complete

### Operations ✅
- [x] CI/CD pipeline active
- [x] Automated testing on PRs
- [x] Monitoring dashboards live
- [x] Automated backups running

---

## Risk Mitigation

### High Risk Items

1. **Async Migration Complexity** (Day 9)
   - **Mitigation:** Implement thread pool first, migrate to httpx in Phase 3
   - **Backup Plan:** Keep PyGithub with proper thread isolation

2. **Docling Integration Issues** (Day 26-28)
   - **Mitigation:** Test with sample documents early
   - **Backup Plan:** Start with basic text/markdown, add PDF later

3. **Performance Targets Not Met**
   - **Mitigation:** Implement caching aggressively
   - **Backup Plan:** Use CDN for frontend, read replicas for database

4. **CI/CD Pipeline Delays** (Day 6-7)
   - **Mitigation:** Use GitHub Actions templates
   - **Backup Plan:** Manual testing gates until pipeline ready

---

## Resource Allocation

### Team Size Recommendations

**1 Developer (8 weeks):**
- Follow roadmap sequentially
- Focus on critical path items
- Defer nice-to-have features

**2 Developers (4-5 weeks):**
- Dev 1: Security + Backend (Phases 1-2)
- Dev 2: Testing + Frontend (Phases 1-2)
- Both: Features + Ops (Phases 3-4)

**3 Developers (3-4 weeks):**
- Dev 1: Security + Auth
- Dev 2: Testing Infrastructure
- Dev 3: Performance + Features
- All: Monitoring + Ops (Phase 4)

---

## Daily Standup Template

```markdown
### What I completed yesterday:
- [x] Task from roadmap
- [x] Related subtasks

### What I'm working on today:
- [ ] Next task from roadmap
- [ ] Expected completion time

### Blockers:
- None / [Specific blocker]

### Deviations from plan:
- None / [What changed and why]
```

---

## Weekly Review Checklist

**End of Each Week:**
- [ ] Review completed tasks vs. plan
- [ ] Update roadmap for discovered work
- [ ] Run full test suite
- [ ] Check CI/CD pipeline health
- [ ] Review monitoring metrics
- [ ] Update documentation as needed
- [ ] Commit and push all changes

---

## Deployment Checklist

### Pre-Production (After Phase 2)
- [ ] All critical tests passing
- [ ] Security scan clean
- [ ] Performance benchmarks met
- [ ] Backup/restore tested
- [ ] Monitoring configured

### Production Deployment (After Phase 4)
- [ ] SSL certificates configured
- [ ] Environment variables set
- [ ] Database migrations applied
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Backup automation verified
- [ ] Rollback plan documented
- [ ] On-call rotation established

---

## Maintenance Mode (Post-Launch)

**Weekly:**
- Review monitoring dashboards
- Check error rates and logs
- Update dependencies (security patches)
- Backup verification

**Monthly:**
- Performance optimization review
- Security audit
- Documentation updates
- User feedback incorporation

**Quarterly:**
- Major dependency updates
- Architecture review
- Capacity planning
- Disaster recovery drill

---

*This roadmap is based on the comprehensive multi-agent review findings. Adjust timelines based on team velocity and organizational priorities.*

**Next Step:** Review all 8 agent reports in detail, then start Phase 1, Day 1! 🚀
