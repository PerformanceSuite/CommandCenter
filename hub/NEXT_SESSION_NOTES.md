# Next Session Notes - Hub Development

## What We Accomplished Today ✅

### 1. Fixed Hub Folder Browser
- **Issue**: Folder picker showed "Not Found" with no directories
- **Root causes found**:
  - Vite proxy configured for port 9001, backend running on 9002
  - `VITE_API_URL` environment variable set to wrong port (8000)
  - Missing `asyncpg` dependency in backend
  - `DATABASE_URL` env var pointing to PostgreSQL instead of SQLite
- **Fixes applied**:
  - Updated `hub/frontend/vite.config.ts` proxy to port 9002
  - Installed `asyncpg` in backend venv
  - Created `hub/backend/data/` directory for SQLite
  - Started backend with correct `DATABASE_URL="sqlite+aiosqlite:///./data/hub.db"`
  - Started frontend with `VITE_API_URL=http://localhost:9002`
- **Result**: Folder browser now works perfectly! ✅

### 2. Cleaned Up Docker Containers
- Identified and removed old CommandCenter containers that were causing restart loops
- Stopped `commandcenter_celery_beat` (was crashing due to missing Redis)
- Removed 11 old/unused CommandCenter containers
- Docker environment now clean with only active Hub containers

### 3. Investigated Dagger Performance Issue
- **Discovery**: Dagger orchestration is extremely slow (20-30+ minutes for first start)
- **Root cause**: Synchronous API design - endpoint blocks until Dagger completes
- **Created**: Comprehensive issue document at `hub/ISSUE_DAGGER_PERFORMANCE.md`
- **Proposed solutions**: Background tasks with Celery, WebSocket progress, hybrid docker-compose approach

## Current Status

### ✅ Working
- **Hub Frontend**: `http://localhost:9000` (Vite dev server)
- **Hub Backend**: `http://localhost:9002` (uvicorn)
- **Folder Browser**: Fully functional, shows directories correctly
- **Project Creation**: Creates projects in database successfully

### ⚠️ Issues
- **Dagger Orchestration**: Unusably slow (20-30 min blocking operations)
- **No Background Tasks**: All operations run synchronously in request cycle
- **No Progress Feedback**: Users can't see what's happening during long operations

### 🔄 In Progress
- None (Dagger start operation was cancelled)

## Running Services (Keep These Running)

To restart Hub for next session:

### Backend
```bash
cd /Users/danielconnolly/Projects/CommandCenter/hub/backend
export DATABASE_URL="sqlite+aiosqlite:///./data/hub.db"
export VITE_API_URL=http://localhost:9002  # Important!
source venv/bin/activate
uvicorn app.main:app --reload --port 9002 --host 0.0.0.0
```

### Frontend
```bash
cd /Users/danielconnolly/Projects/CommandCenter/hub/frontend
export VITE_API_URL=http://localhost:9002  # Important!
npm run dev  # Runs on port 9000
```

**Critical**: Always set `VITE_API_URL=http://localhost:9002` before starting frontend!

## Next Session Priorities

### High Priority
1. **File GitHub Issue** - Create issue from `ISSUE_DAGGER_PERFORMANCE.md`
2. **Implement Background Tasks** - Add Celery for async Dagger operations
3. **Add Progress Feedback** - WebSocket or polling for build status
4. **Test docker-compose Alternative** - Verify faster orchestration path

### Medium Priority
5. **Optimize Dagger Builds** - Pre-build base images, improve caching
6. **Add Timeouts** - Prevent 30-minute blocking calls
7. **Better Error Handling** - User-friendly error messages

### Low Priority
8. **Documentation** - Add workaround instructions for direct docker-compose
9. **Testing** - Add integration tests for orchestration
10. **UI Polish** - Loading states, progress bars

## Known Issues

1. **Hub startup requires specific env vars** - `DATABASE_URL` and `VITE_API_URL` must be set correctly or services fail
2. **No .env file for Hub** - Consider adding `.env.local` for development
3. **Old containers linger** - Need periodic cleanup or better container naming
4. **Dagger blocks API** - Critical blocker for production use

## Files Changed Today

### Modified
- `hub/frontend/vite.config.ts` - Fixed proxy port (9001 → 9002)

### Created
- `hub/backend/data/hub.db` - SQLite database for Hub
- `hub/ISSUE_DAGGER_PERFORMANCE.md` - Detailed performance issue documentation
- `hub/NEXT_SESSION_NOTES.md` - This file

### Installed Dependencies
- `hub/backend`: `asyncpg` (for async PostgreSQL support)

## Quick Reference

### Hub URLs
- Frontend: http://localhost:9000
- Backend API: http://localhost:9002
- API Docs: http://localhost:9002/docs

### Projects Created
1. ROLLIZR (ID: 1, ports: 8010/3010/5442/6389) - Status: error
2. Test CommandCenter (ID: 2, ports: 8020/3020/5452/6399) - Status: starting
3. Performia (ID: 3, ports: 8030/3030/5462/6409) - Status: error

### Docker Containers
- `dagger-engine-v0.19.4` - Dagger orchestration engine (running)
- `commandcenter-hub-backend` - Hub backend container (running)
- `commandcenter-hub-frontend` - Hub frontend container (running)

## Questions for Next Session

1. Should we switch to docker-compose for orchestration instead of Dagger?
2. Do we need Celery infrastructure for background tasks?
3. Should Hub manage docker-compose.yml files or use Dagger SDK?
4. What's the timeline for fixing Dagger performance vs. using workarounds?

## Session Duration
Approximately 3 hours of debugging, fixing, and documentation.
