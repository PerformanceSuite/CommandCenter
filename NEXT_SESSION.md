# Next Session: Fix Container Startup Issue

**Date**: October 16, 2025
**PR**: #52 - Hub Auto-Start Improvements
**Status**: 🔴 CRITICAL BUG - Containers don't actually start properly

## What We Accomplished

✅ Auto-start containers on project creation
✅ Cache-busting in Hub (PR #51 fix)
✅ Port conflict detection
✅ Improved UX (persistent toasts, bottom-center position)
✅ Auto-open in new tab attempt

## The Problem

**User creates project through Hub:**
1. ✅ Project files created successfully
2. ✅ Auto-start triggered
3. ✅ Health check passes (`status: 'running', health: 'healthy'`)
4. ✅ New tab opens automatically
5. ❌ **Browser shows "Project not started" page**

**Root Cause**: Health check reports healthy but backend isn't actually responding.

## Evidence

```bash
# What orchestration service reports:
{
  "status": "running",
  "health": "healthy",
  "containers": [...],
  "running_count": 4,
  "total_count": 4
}

# What actually happens:
curl http://localhost:3010  # Connection refused
# OR
curl http://localhost:3010  # Shows ProjectNotStarted component
```

## Hypotheses

### 1. Docker Health Check vs Application Health
- Docker reports container as "healthy"
- But backend `/health` endpoint not responding yet
- Race condition between container start and app ready

**Test**: Poll backend `/health` directly instead of Docker status

### 2. Port Binding Delay
- Containers start successfully
- But ports not actually listening yet when health check passes
- Network initialization lag

**Test**: Use `lsof -i :PORT` to verify actual port binding

### 3. Port Conflict (Despite Detection)
- Port conflict detection checks port before starting
- But something grabs the port during startup
- Previous server still shutting down

**Test**: Add delay after conflict check, re-check before open

### 4. Database/Redis Not Ready
- Frontend/backend containers start
- But can't connect to postgres/redis yet
- Health check passes but app crashes on first request

**Test**: Check container logs for connection errors

## Debugging Steps for Next Session

### Step 1: Verify Container State
```bash
# After "healthy" status reported:
docker ps --filter "name=<project>"
docker logs <project>_backend --tail 50
docker logs <project>_frontend --tail 50

# Check actual port binding:
lsof -i :3010
lsof -i :8010

# Try curling backend directly:
curl http://localhost:8010/health
curl http://localhost:3010
```

### Step 2: Add Backend Health Polling
Instead of:
```typescript
const status = await api.orchestration.status(newProject.id);
if (status.status === 'running' && status.health === 'healthy') {
  // Open tab
}
```

Try:
```typescript
const status = await api.orchestration.status(newProject.id);
if (status.status === 'running' && status.health === 'healthy') {
  // Additional check: poll backend directly
  const backendHealthy = await fetch(
    `http://localhost:${newProject.backend_port}/health`
  );
  if (backendHealthy.ok) {
    // NOW open tab
  }
}
```

### Step 3: Increase Startup Wait Time
Current: 90 seconds max, 1 second polls
Try: Add 5-10 second delay after "healthy" before opening

### Step 4: Check Port Availability
```typescript
// Before opening tab:
const portCheck = await fetch(`http://localhost:${newProject.frontend_port}`);
if (portCheck.ok) {
  // Port is actually responding
  window.open(...);
} else {
  // Wait more or show error
}
```

## Files to Review

1. **orchestration_service.py** - Line 237-296
   Health check logic - what does it actually verify?

2. **docker-compose.yml** - Frontend/backend health checks
   Are they correct? Too optimistic?

3. **Dashboard.tsx** - Line 87-141
   Health polling loop - needs backend verification

## Quick Wins to Try

1. **Add 10-second delay** after health check passes before opening
2. **Poll backend `/health`** directly (not Docker status)
3. **Check `docker ps`** output - are containers ACTUALLY running?
4. **Verify .env file** in created project has correct ports
5. **Check for zombie processes** on ports

## Questions to Answer

- Does the project work if you manually wait 30 seconds then refresh?
- Do containers show in `docker ps`?
- What do the backend/frontend logs show?
- Is postgres/redis accessible from backend?
- Are environment variables correct in created project?

## Remember

The PR #52 has all the UX improvements working. The ONLY issue is:
> **Containers report healthy but backend doesn't respond**

Fix that one thing and everything else works perfectly.

---

## Session End Checklist

- [x] PR #52 created: https://github.com/PerformanceSuite/CommandCenter/pull/52
- [x] All code committed and pushed
- [x] Known issues documented
- [x] Next session plan created
- [ ] Fix the container health check issue (NEXT SESSION)
