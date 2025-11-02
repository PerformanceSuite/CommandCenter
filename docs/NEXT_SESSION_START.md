# Next Session: Execute Phase C Week 1

## Quick Start Commands

```bash
# 1. Navigate to Phase C worktree
cd /Users/danielconnolly/Projects/CommandCenter/.worktrees/phase-c-observability

# 2. Open new Claude Code session in this directory

# 3. Run this command:
/superpowers:execute-plan

# 4. When prompted, provide the plan file:
docs/plans/2025-11-02-week1-correlation-and-errors.md
```

## Context for Next Session

**Current State:**
- Worktree created and configured
- Branch: `feature/phase-c-observability`
- Design document: `docs/plans/2025-11-01-phase-c-observability-design.md` (committed)
- Implementation plan: `docs/plans/2025-11-02-week1-correlation-and-errors.md` (ready)
- Environment configured with Phase C ports (.env created)

**What to Execute:**
- Week 1: Correlation IDs & Error Tracking (8 tasks)
- Each task follows TDD: Write test → Watch fail → Implement → Watch pass → Commit
- Expected duration: 2-4 hours for all 8 tasks

**Success Criteria:**
- ✅ All 8 tasks committed
- ✅ All tests passing
- ✅ Correlation IDs in all API responses
- ✅ Error metrics exposed
- ✅ Middleware overhead < 1ms
- ✅ Documentation complete

**Key Files to Be Created:**
1. `backend/app/middleware/correlation.py` - Correlation ID middleware
2. `backend/tests/middleware/test_correlation.py` - Middleware tests
3. Enhanced exception handler in `backend/app/main.py`
4. `backend/tests/integration/test_error_tracking.py` - Error tracking tests
5. `backend/tests/performance/test_middleware_overhead.py` - Performance tests
6. `docs/observability/correlation-ids.md` - Documentation

**Important Notes:**
- Use TDD discipline: test-first always
- Commit after each task completion
- Run verification before claiming complete
- Docker-based project (use `docker-compose` for testing)
- Phase C uses ports: 8100 (backend), 3100 (frontend), 5532 (postgres)

## Execution Flow

The `executing-plans` skill will:
1. Load the plan from `docs/plans/2025-11-02-week1-correlation-and-errors.md`
2. Execute tasks in batches (typically 3-4 tasks per batch)
3. Pause for review between batches
4. Verify tests pass before proceeding
5. Commit after each task

After each batch review, you can:
- Approve and continue
- Request changes
- Adjust approach

## After Execution Complete

When all 8 tasks are done:
1. Run full test suite: `docker-compose exec backend pytest -v`
2. Run smoke tests (documented in Task 8)
3. Verify deployment to dev environment
4. Return to main repo and report completion

---

**Ready for parallel execution in next session!** 🚀
