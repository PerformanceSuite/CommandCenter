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

### 3. ✅ FIXED: Port Mapping Implementation
**Status**: Fixed 2025-11-02
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

**Solution Found**:
- Use `Service.up(ports=[...])` with `dagger.PortForward` objects
- `PortForward(backend=5432, frontend=5442)` maps container:5432 → host:5442
- Note: "frontend" = host port, "backend" = container port (opposite of docker-compose!)

**Fix Applied** (lines 210-223):
```python
import dagger

await postgres_svc.up(ports=[
    dagger.PortForward(backend=5432, frontend=self.config.postgres_port)
])
await redis_svc.up(ports=[
    dagger.PortForward(backend=6379, frontend=self.config.redis_port)
])
await backend_svc.up(ports=[
    dagger.PortForward(backend=8000, frontend=self.config.backend_port)
])
await frontend_svc.up(ports=[
    dagger.PortForward(backend=3000, frontend=self.config.frontend_port)
])
```

---

### 4. ✅ FIXED: Service Persistence
**Status**: Fixed 2025-11-02
**File**: `hub/backend/app/dagger_modules/commandcenter.py`

**Problem**:
- Containers created with `.as_service()` but no mechanism to keep them running
- Added `.up()` calls but services still may not persist after function returns
- Services terminated when Python garbage collected Service objects

**Root Cause**:
- Service references were local variables, garbage collected at end of function
- Without references, Dagger engine terminates the services

**Solution**:
- Store Service references in instance variable `self._services` dict
- Keeps Python references alive as long as CommandCenterStack instance exists
- Services persist for entire stack lifecycle

**Fix Applied**:

Line 67 (in `__init__`):
```python
self._services: dict[str, dagger.Service] = {}  # Track running services to keep them alive
```

Lines 225-231 (in `start()` method):
```python
# Store service references to keep them alive
self._services = {
    "postgres": postgres_svc,
    "redis": redis_svc,
    "backend": backend_svc,
    "frontend": frontend_svc,
}
```

Lines 507-508 (in `restart_service()` method):
```python
self._services[service_name] = new_service
```

---

### 5. ✅ FIXED: Frontend/Backend Build Process
**Status**: Fixed 2025-11-02
**File**: `hub/backend/app/dagger_modules/commandcenter.py`

**Problem**:
- Backend: Tried to `pip install` packages globally BEFORE mounting project directory
- Frontend: Tried to globally install vite/react BEFORE mounting project directory
- This approach didn't work because:
  - No access to requirements.txt or package.json during install
  - Can't run `npm run dev` without project dependencies installed
  - Mount happened AFTER install, so couldn't access project files

**Old Code (broken)**:
```python
# Backend
.with_exec(["pip", "install", "fastapi", "uvicorn[standard]", ...])  # No requirements.txt!
.with_mounted_directory("/workspace", project_dir)  # Mount AFTER install
.with_exec(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])

# Frontend
.with_exec(["npm", "install", "-g", "vite", "react", "react-dom"])  # Global install!
.with_exec(["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"])  # No package.json!
```

**New Code (working)**:

Backend (lines 125-150):
```python
# Mount project directory FIRST
project_dir = self.client.host().directory(self.config.project_path)

.from_("python:3.11-slim")
# Mount project directory BEFORE installing dependencies
.with_mounted_directory("/workspace", project_dir)
.with_workdir("/workspace/backend")
# Install from requirements.txt in the mounted project
.with_exec(["pip", "install", "-r", "requirements.txt"])
.with_exec(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
```

Frontend (lines 159-181):
```python
# Mount project directory FIRST
project_dir = self.client.host().directory(self.config.project_path)

.from_("node:18-alpine")
# Mount project directory BEFORE installing dependencies
.with_mounted_directory("/workspace", project_dir)
.with_workdir("/workspace/frontend")
# Install from package.json in the mounted project
.with_exec(["npm", "install"])
.with_exec(["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"])
```

**Key Changes**:
1. Mount project directory BEFORE running install commands
2. Set workdir to backend/frontend subdirectories
3. Use project's requirements.txt and package.json instead of global installs

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

## Status Update: 2025-11-02

### ✅ All Critical Issues Fixed

1. **Port Mapping** (Critical) - ✅ FIXED
   - Implemented using `Service.up(ports=[PortForward(...)])`
   - All services now map custom ports correctly
   - No more "address already in use" errors

2. **Service Persistence** (Critical) - ✅ FIXED
   - Store Service references in `self._services` dict
   - Services persist as long as CommandCenterStack instance exists
   - Verified with integration tests

3. **Build Process** (High Priority) - ✅ FIXED
   - Mount project directory BEFORE installing dependencies
   - Backend uses requirements.txt, frontend uses package.json
   - Set workdir to backend/frontend subdirectories

4. **Integration Testing** (High Priority) - ✅ COMPLETE
   - Created 6 integration tests with real Dagger containers
   - Created standalone test script for quick validation
   - Tests verify port forwarding, persistence, and build process

### ⏸️ Deferred Issues

4. **Non-Root Execution** (Medium Priority) - DEFERRED
   - `.with_user()` breaks container initialization
   - Would require custom Dockerfiles with proper user setup
   - Not critical for initial deployment
   - Can be addressed in future iteration

5. **Resource Limits** (Low Priority) - DEFERRED
   - `.with_resource_limit()` not available in dagger-io 0.19.4
   - Not essential for development/testing
   - Can be implemented when SDK supports it or via Docker export

### Next Steps

1. ✅ Verify fixes with integration tests
2. ⏳ Update documentation (in progress)
3. ⏳ Test full Hub orchestration flow
4. ⏳ Commit fixes with detailed message
5. ⏳ Update Phase A status in PROJECT.md

---

## Files Modified - 2025-11-02 Session

### Previous Session (Issues Discovery)
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

### Current Session (Fixes Implementation)
```
hub/backend/app/dagger_modules/commandcenter.py
- Line 67: Added _services dict to __init__ (service persistence)
- Lines 125-150: Fixed backend build (mount before install, use requirements.txt)
- Lines 159-181: Fixed frontend build (mount before install, use package.json)
- Lines 210-223: Implemented port forwarding in start()
- Lines 225-231: Store service references to keep alive
- Lines 493-508: Implemented port forwarding in restart_service()

hub/backend/tests/integration/test_dagger_port_forwarding.py
- NEW: 6 integration tests with real Dagger containers
- Tests: port forwarding, service persistence, build process

hub/backend/test_port_forwarding_standalone.py
- NEW: Standalone test script (no pytest dependencies)
- 3 focused tests for quick validation

hub/PHASE_A_FIXES_2025-11-02.md
- NEW: Comprehensive documentation of all fixes

hub/PHASE_A_DAGGER_ISSUES.md
- Updated issues #3, #4, #5 from "❌" to "✅ FIXED"
- Added fix details with code examples
- Added status update section
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
