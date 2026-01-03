# Backend Architecture Agent - Task Definition

**Mission:** Refactor backend architecture and optimize performance
**Worktree:** worktrees/backend-agent
**Branch:** feature/backend-architecture
**Estimated Time:** 37 hours
**Dependencies:** None (Phase 1 - Independent)

## Tasks

### 1. Create Service Layer (16h)
- Read BACKEND_REVIEW.md Section 3.1
- Create `backend/app/services/repository_service.py`
- Create `backend/app/services/technology_service.py`
- Create `backend/app/services/research_service.py`
- Extract all business logic from routers
- Implement transaction management
- Update routers to use services

### 2. Add Database Indexes (1h)
- Add index on Repository(owner, name)
- Add index on Technology(domain, status)
- Create Alembic migration
- Test query performance

### 3. Fix Async/Await Blocking (12h)
- Create `backend/app/services/github_async.py`
- Use ThreadPoolExecutor for PyGithub calls
- Update all GitHub service calls
- Benchmark 3-10x improvement

### 4. Implement Repository Pattern (8h)
- Create base repository class
- Implement specific repositories
- Add proper error handling
- Write comprehensive tests

**Review until 10/10, create PR, auto-merge when approved**
