# Audit Implementation Plan

**Date**: 2025-12-04
**Based On**: Architecture Review + Code Health Audit
**Branch**: feature/mrktzr-module
**Status**: Ready for Execution

---

## Executive Summary

Three parallel audits identified **4 P0 critical issues**, **8 P1 high-priority items**, and multiple P2 improvements. This plan prioritizes fixes by impact and effort.

### Health Scores
- **Code Health**: B+ (82/100)
- **Architecture**: GOOD with critical areas

### Key Metrics
- **242,853** lines of code
- **993** Python files, **378** TypeScript files
- **244** test files, **1,700+** tests passing
- **22** TODO/FIXME items
- **3.17%** code duplication (minimal)

---

## Phase 1: Critical Fixes (Week 1)

### P0-1: Multi-Tenant Isolation Bypass
**Impact**: HIGH - Data leakage between projects
**Effort**: 6 hours
**Files**:
- `backend/app/services/technology_service.py`
- `backend/app/services/repository_service.py`
- `backend/app/routers/webhooks.py`

**Action**: Remove all hardcoded `project_id=1` defaults, require explicit project_id

**Status**: ✅ Partially fixed (2025-11-18), verify completeness

---

### P0-2: Missing Output Schema Validation
**Impact**: HIGH - Runtime errors from unvalidated agent outputs
**Effort**: 1 hour
**File**: `hub/orchestration/src/dagger/executor.ts:70`

**Action**:
```typescript
// Add Zod validation
import { z } from 'zod';

const validateOutput = (output: unknown, schema: z.ZodSchema) => {
  const result = schema.safeParse(output);
  if (!result.success) {
    throw new AgentOutputValidationError(result.error);
  }
  return result.data;
};
```

---

### P0-3: In-Memory Task Persistence
**Impact**: HIGH - Data loss on backend restart
**Effort**: 2 hours
**File**: `backend/app/routers/research_orchestration.py:40`

**Action**: Replace in-memory dict with Redis or database persistence

---

### P0-4: Generate Coverage Reports
**Impact**: HIGH - Cannot verify test coverage
**Effort**: 2 hours

**Actions**:
```bash
# Backend
cd backend && pytest --cov=app --cov-report=html

# Frontend
cd frontend && npm run test:coverage

# Hub
cd hub/frontend && npm run test:coverage
```

Add to CI pipeline.

---

## Phase 2: High Priority (Week 2)

### P1-1: API Authentication Middleware
**Impact**: HIGH - No auth currently enforced
**Effort**: 14 hours
**Reference**: Phase 10 authentication design

**Action**: Implement JWT/API key authentication across all endpoints

---

### P1-2: TypeScript Type Safety
**Impact**: MEDIUM - 289 `any/unknown` usages
**Effort**: 8 hours
**Files**: Hub orchestration, frontend components

**Action**: Replace `any` with proper types, enable strict mode

---

### P1-3: Dependency Updates
**Impact**: MEDIUM - Security and compatibility
**Effort**: 4 hours

**Critical Updates**:
| Package | Current | Target |
|---------|---------|--------|
| FastAPI | 0.103.x | 0.115.x |
| dagger-io | 0.14.x | 0.19.x |
| Prisma | 5.x | 6.x |

---

### P1-4: Large File Refactoring
**Impact**: MEDIUM - Maintainability
**Effort**: 4 hours
**File**: `libs/knowledgebeast/knowledgebeast/routes.py` (1,709 lines)

**Action**: Split into domain-specific route modules

---

### P1-5: Debug Logging Cleanup
**Impact**: LOW - Performance, log noise
**Effort**: 4 hours
**Scope**: 1,046+ console.log/print statements

**Action**: Replace with proper logger, remove debug statements

---

## Phase 3: Architecture Improvements (Week 3-4)

### P1-6: Hub High Availability
**Impact**: MEDIUM - Single point of failure
**Effort**: 16 hours

**Actions**:
- Add state persistence for workflows
- Implement leader election
- Add health-based failover

---

### P1-7: Database Connection Pooling
**Impact**: MEDIUM - Scalability
**Effort**: 4 hours

**Actions**:
- Configure SQLAlchemy pool size
- Add pgBouncer for production
- Monitor connection usage

---

### P1-8: GitHub API Circuit Breaker
**Impact**: MEDIUM - Resilience
**Effort**: 2 hours

**Action**: Add circuit breaker pattern to GitHubService

---

## Phase 4: Technical Debt (Ongoing)

### P2 Items

| Item | Effort | Priority |
|------|--------|----------|
| Resolve 22 TODO/FIXME comments | 8h | P2 |
| Event schema versioning | 8h | P2 |
| API rate limiting | 4h | P2 |
| Frontend component tests | 8h | P2 |
| Documentation updates | 4h | P2 |

---

## Quick Wins (Can Do Today)

1. ✅ MRKTZR auth duplication - **FIXED** (removed auth.ts entirely)
2. Generate coverage reports - 2 hours
3. Remove remaining `project_id=1` defaults - 2 hours
4. Add Zod validation to executor - 1 hour

---

## Architecture Diagrams Generated

| Diagram | Location | Description |
|---------|----------|-------------|
| High-Level Architecture | `docs/diagrams/commandcenter-architecture.mmd` | Services, databases, integrations |
| Hub Internal | `docs/diagrams/hub-internal-architecture.mmd` | Hub service details |
| Hub Modules | `docs/diagrams/hub-modules.mmd` | Module relationships |
| Data Flow | `docs/diagrams/data-flow.mmd` | Event and data paths |

---

## Success Criteria

### Week 1
- [ ] All P0 issues resolved
- [ ] Coverage reports generated
- [ ] No hardcoded project_id defaults

### Week 2
- [ ] Auth middleware implemented
- [ ] TypeScript strict mode enabled
- [ ] Dependencies updated

### Week 3-4
- [ ] Hub HA design documented
- [ ] Connection pooling configured
- [ ] Circuit breakers added

### Ongoing
- [ ] TODO count < 10
- [ ] Test coverage > 80%
- [ ] Zero `any` types

---

## Appendix: Audit Artifacts

| File | Description |
|------|-------------|
| `docs/audits/CODE_HEALTH_AUDIT_2025-12-04.md` | Full code health analysis |
| `docs/audits/ARCHITECTURE_REVIEW_2025-12-04.md` | Architecture review |
| `docs/diagrams/README.md` | Diagram documentation |
| `report/jscpd-report.json` | Code duplication data |

---

*Generated from parallel audit execution using E2B sandbox tooling*
