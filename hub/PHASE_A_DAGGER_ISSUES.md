# Phase A Dagger Implementation Issues

**Date**: 2025-11-02
**Session**: Hub Testing & Dagger Debugging

## Summary

Phase A "Dagger Production Hardening" was merged but never actually tested with real Dagger containers. All tests were mocked, so critical compatibility issues went undetected. The implementation has multiple breaking issues that prevent containers from starting.

## Issues Found

### 1. ✅ FIXED: `with_resource_limit()` Method Doesn't Exist
**Status**: Fixed by commenting out calls
**File**: `hub/backend/app/dagger_modules/commandcenter.py`

**Problem**:
- Code calls `.with_resource_limit("cpu", ...)` and `.with_resource_limit("memory", ...)`
- This method does not exist in dagger-io SDK 0.19.4
- Verified by inspecting Container class methods - no resource limit APIs available

**Evidence**:
```python
# Checked available methods:
python3 -c "import dagger; print([m for m in dir(dagger.Container) if not m.startswith('_')])"
# Result: No with_resource_limit method exists
```

**Fix Applied**:
```python
# Commented out all resource limit calls (lines 95-96, 112-113, 147-148, 171-172)
# TODO: Resource limits not available in dagger-io 0.19.4
# .with_resource_limit("cpu", str(limits.postgres_cpu))
# .with_resource_limit("memory", f"{limits.postgres_memory_mb}m")
```

---

### 2. ✅ FIXED: `with_user()` Breaks Container Initialization
**Status**: Fixed by commenting out calls
**File**: `hub/backend/app/dagger_modules/commandcenter.py`

**Problem**:
- All containers call `.with_user(str(USER_ID))` to run as non-root
- Postgres: `.with_user("999")` - breaks postgres initialization (needs postgres user)
- Redis: `.with_user("999")` - breaks redis startup
- Backend: `.with_user("1000")` - breaks pip install (permission issues)
- Frontend: `.with_user("1000")` - breaks npm install (permission issues)

**Root Cause**:
- Phase A design assumed UID 999/1000 would work, but:
  - Postgres requires specific user setup and data directory permissions
  - Changing user BEFORE package installation breaks permission assumptions
  - Official images expect to run as their default users

**Error Observed**:
```
failed to start host service: start upstream: exit code: 1
```

**Fix Applied**:
```python
# Commented out all with_user() calls (lines 90, 111, 132, 165)
# TODO: with_user breaks postgres initialization - need to fix
# .with_user(str(self.POSTGRES_USER_ID))  # Run as non-root
```

---

### 3. ❌ CURRENT ISSUE: Port Mapping Not Implemented
**Status**: Not fixed - architectural issue
**File**: `hub/backend/app/dagger_modules/commandcenter.py`

**Problem**:
- Containers use `.with_exposed_port()` but this only declares internal ports
- No port mapping/forwarding from container ports to host ports
- Project configured for ports 8010, 3010, 5442, 6389
- Containers try to bind to default ports 8000, 3000, 5432, 6379
- Results in "address already in use" errors when default ports occupied

**Error Observed**:
```json
{
  "detail": "Failed to start project with Dagger: failed to start host service: host to container: failed to receive listen response: rpc error: code = Unknown desc = listen tcp 0.0.0.0:5432: bind: address already in use"
}
```

**Missing Implementation**:
- Need port tunneling/forwarding API to map:
  - Container 5432 → Host 5442 (postgres)
  - Container 6379 → Host 6389 (redis)
  - Container 8000 → Host 8010 (backend)
  - Container 3000 → Host 3010 (frontend)

**Research Needed**:
- Check Dagger SDK for port forwarding/tunneling methods
- May need `.tunnel()` or similar API
- Alternative: Use `Service.endpoint()` to get dynamic ports

---

### 4. ❌ ARCHITECTURAL: Services Don't Persist
**Status**: Partially addressed with `.up()` calls
**File**: `hub/backend/app/dagger_modules/commandcenter.py` (lines 203-206)

**Problem**:
- Containers created with `.as_service()` but no mechanism to keep them running
- Added `.up()` calls but services still may not persist after function returns
- May need terminal sessions or persistent bindings

**Current Code**:
```python
postgres_svc = postgres.as_service()
redis_svc = redis.as_service()
backend_svc = backend.as_service()
frontend_svc = frontend.as_service()

# Keep services running by calling up() and storing endpoints
await postgres_svc.up()
await redis_svc.up()
await backend_svc.up()
await frontend_svc.up()
```

**Issue**:
- Services may terminate when Dagger context closes
- Need long-running service management
- May need to export containers to Docker instead of running in Dagger engine

---

### 5. ❌ DESIGN FLAW: Frontend/Backend Build Approach Wrong
**Status**: Not addressed
**File**: `hub/backend/app/dagger_modules/commandcenter.py` (lines 134-136, 167)

**Problem**:
- Backend: Tries to `pip install` packages then run uvicorn with `.with_exec()`
- Frontend: Tries to globally install vite/react then run `npm run dev`
- This approach won't work because:
  - No package.json or requirements.txt being used
  - Can't run `npm run dev` without project dependencies
  - Mount happens AFTER install, so can't access project files during install

**Current Code**:
```python
# Backend
.with_exec(["pip", "install", "fastapi", "uvicorn[standard]", ...])
.with_mounted_directory("/workspace", project_dir)
.with_exec(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])

# Frontend
.with_exec(["npm", "install", "-g", "vite", "react", "react-dom"])
.with_exec(["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"])
```

**Should Be**:
```python
# Backend
.with_mounted_directory("/workspace", project_dir)
.with_workdir("/workspace/backend")
.with_exec(["pip", "install", "-r", "requirements.txt"])
.with_exec(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])

# Frontend
.with_mounted_directory("/workspace", project_dir)
.with_workdir("/workspace/frontend")
.with_exec(["npm", "install"])
.with_exec(["npm", "run", "dev", "--", "--host", "0.0.0.0"])
```

---

## Root Cause Analysis

### Why These Issues Went Undetected

1. **All tests were mocked** - No actual Dagger containers were ever started
2. **No integration tests** - Only unit tests with MagicMock
3. **Assumed API availability** - resource_limit methods don't exist
4. **Assumed user switching works** - breaks container initialization
5. **No port mapping implementation** - critical feature missing
6. **Wrong build approach** - doesn't use actual project files correctly

### Test Coverage Gaps

The Phase A tests (`hub/backend/tests/unit/test_dagger_*.py`) mock everything:
```python
mock_container = MagicMock()
mock_container.with_user = MagicMock(return_value=mock_container)
mock_container.with_resource_limit = MagicMock(return_value=mock_container)
```

These tests pass but don't validate:
- Whether methods actually exist in Dagger SDK
- Whether containers can actually start
- Whether port mapping works
- Whether services persist

---

## Recommendations

### Immediate Fixes Needed

1. **Port Mapping** (Critical)
   - Research Dagger SDK port forwarding API
   - Implement host port → container port mapping
   - Test with actual port conflicts

2. **Service Persistence** (Critical)
   - Investigate proper service lifecycle management
   - Consider exporting to Docker containers instead of Dagger engine
   - Implement health checks and monitoring

3. **Build Process** (High Priority)
   - Fix backend/frontend builds to use project files
   - Mount directory FIRST, then install dependencies
   - Use requirements.txt and package.json

4. **Non-Root Execution** (Medium Priority)
   - Research proper non-root container configuration
   - May need custom Dockerfiles with proper user setup
   - Can't just call .with_user() on standard images

### Long-Term Solutions

1. **Integration Testing**
   - Add tests that actually start Dagger containers
   - Test full stack startup end-to-end
   - Validate port mapping and service persistence

2. **Alternative Architecture**
   - Consider using docker-compose via subprocess instead
   - More mature, better documented, widely used
   - Dagger may be too experimental for this use case

3. **Dagger Version Upgrade**
   - Check if newer Dagger versions have:
     - Resource limit APIs
     - Better port forwarding
     - Improved service management

---

## Files Modified This Session

```
hub/backend/app/dagger_modules/commandcenter.py
- Commented out all .with_resource_limit() calls (doesn't exist in SDK)
- Commented out all .with_user() calls (breaks initialization)
- Added .up() calls to try keeping services running
- Added TODO comments explaining issues

hub/backend/app/main.py
- Added port 9003 to CORS allowed origins (frontend auto-selected this port)

hub/backend/data/hub.db
- Deleted and recreated (schema mismatch: cc_path vs path column)
```

---

## Session Summary

**Goal**: Test CommandCenter Hub with Dagger orchestration
**Outcome**: Discovered Phase A implementation is non-functional
**Status**: Hub UI running, backend running, but Dagger orchestration broken

**Progress Made**:
- ✅ Hub backend running on port 9002
- ✅ Hub frontend running on port 9003
- ✅ Fixed database schema issues
- ✅ Fixed resource_limit compatibility
- ✅ Fixed with_user() breaking containers
- ❌ Port mapping still not working
- ❌ Services don't persist properly
- ❌ Build process doesn't use project files correctly

**Next Steps**:
1. Research Dagger port forwarding API
2. Implement proper port mapping
3. Fix service persistence
4. Add real integration tests
5. OR: Switch to docker-compose approach

---

## Developer Notes

The Phase A merge was premature. While the code follows good patterns and has extensive unit test coverage, it was never validated against actual Dagger containers. This is a reminder that:

1. **Mocked tests can give false confidence** - They pass even when APIs don't exist
2. **Integration tests are essential** - Especially for infrastructure code
3. **Assumptions must be validated** - Don't assume SDK methods exist
4. **Incremental testing matters** - Test each component with real dependencies

The Hub architecture is sound, but the Dagger orchestration layer needs significant rework or replacement before it can be used in production.
