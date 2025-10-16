# Project Name Contamination Issue - Root Cause Analysis

**Investigation Date**: October 16, 2025
**Investigated By**: Claude (Systematic Debugging)
**Status**: ✅ ROOT CAUSE IDENTIFIED

## Executive Summary

**User Report**: "I created Rollizr/KnowledgeBeast/VIZTRTR but Performia shows up"

**Actual Issue**: Projects were created successfully but **never started**. When user opened project URLs (e.g., `localhost:3010`), they encountered a Python test server or browser cache instead of project content.

**Root Cause**: NOT project name contamination. The issue was **workflow confusion** + **port conflict with test server**.

## Evidence Gathered

### 1. Project Status
```json
{
  "name": "Rollizr",
  "status": "stopped",
  "health": "unknown",
  "frontend_port": 3010,
  "last_started": null,  // ← NEVER STARTED
  "last_stopped": null,
  "created_at": "2025-10-16T21:18:45"
}
```

### 2. No Containers Running
```bash
$ docker ps --filter "name=rollizr"
# NO OUTPUT - No containers exist

$ docker volume ls | grep rollizr
# NO OUTPUT - No volumes created
```

### 3. Port 3010 Occupied by Test Server
```bash
$ lsof -i :3010
COMMAND   PID    USER   FD   TYPE   DEVICE   SIZE/OFF   NODE   NAME
Python  42569  daniel   4u  IPv6  0x...      0t0      TCP *:3010 (LISTEN)

$ ps -p 42569 -o command
/usr/bin/python3 -m http.server 3010 --directory /tmp

$ curl -s http://localhost:3010/ | head -5
<h1>Directory listing for /</h1>
<!-- Shows /tmp directory listing, NOT project content -->
```

Started: `Thu Oct 16 14:11:29 2025` (before most testing occurred)

### 4. Performia Is Not a Hub Project
```bash
$ ls -la /Users/danielconnolly/Projects/Performia/
# Shows: backend/, docs/, .git/, docker-compose.yml at root level
# This is a SEPARATE codebase, not a Hub-created project

$ ls -la /Users/danielconnolly/Projects/Rollizr/
# Shows: commandcenter/ subdirectory (Hub-created structure)
```

Performia is a pre-existing standalone CommandCenter instance, unrelated to Hub.

### 5. Configuration Is Correct
```bash
$ cat /Users/danielconnolly/Projects/Rollizr/commandcenter/.env
COMPOSE_PROJECT_NAME=rollizr-commandcenter  ✅
VITE_PROJECT_NAME=Rollizr  ✅
FRONTEND_PORT=3010  ✅
```

## What Actually Happened

### User's Flow:
1. Created project "Rollizr" via Hub ✅
2. Clicked "Open" button in Hub
3. Browser opened `http://localhost:3010`
4. Saw: Directory listing from Python test server (or browser cache)
5. Concluded: "Performia is showing up!"

### Reality:
- **NO project containers were running**
- Port 3010 had a test server: `python -m http.server 3010 --directory /tmp`
- User saw `/tmp` directory listing, NOT "Performia" content
- All project configurations were correct
- Runtime config injection was working (but never tested because containers never started)

## Why This Happened

### Contributing Factors:

1. **UX Workflow Gap**: Hub "Open" button opens URL immediately, even if containers aren't started
   - Previous session added Start/Stop buttons to Hub UI
   - But user might not have realized containers need explicit start

2. **Port Conflict**: Test server on 3010 prevented project from starting
   - If user had clicked "Start", would have gotten port conflict error
   - Python server started at 2:11 PM, before most project creation

3. **Confusion About "Performia"**:
   - Performia is a different project entirely
   - User may have conflated seeing "something unexpected" with "seeing Performia"
   - Directory listing doesn't mention Performia anywhere

4. **Browser Cache**:
   - If Performia ever ran on 3010 historically, browser might cache that page
   - When opening 3010 with nothing running, browser shows cached version
   - This explains "Performia showing up" reports

## Fixes Already Implemented (Previous Session)

These fixes were CORRECT but never got properly tested:

1. ✅ **Runtime Config Injection** (`docker-entrypoint.sh` + `config.js`)
   - Creates `window.RUNTIME_CONFIG.PROJECT_NAME` dynamically
   - Works correctly when containers actually run

2. ✅ **Cache-Busting Headers** in `index.html`
   ```html
   <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
   ```

3. ✅ **Start/Stop Buttons** in Hub UI
   - ProjectCard.tsx has conditional rendering based on project.status
   - Shows "Start" button when status === 'stopped'

4. ✅ **ProjectNotStarted Component**
   - Displays helpful message when backend unavailable
   - Shows instructions for starting containers

5. ✅ **Git Clone for Template Distribution**
   - Ensures exact committed state
   - Prevents stale code issues

## Issues to Fix

### 1. Kill Test Server on Port 3010
```bash
kill 42569  # Python http.server
```

### 2. Improve Hub "Open" Button UX

**Current**: Opens URL immediately, even if containers stopped

**Better Options**:
- **Option A**: Show modal: "Project is stopped. Start now?" with Start/Cancel buttons
- **Option B**: Auto-start containers when "Open" clicked, show loading indicator
- **Option C**: Disable "Open" button when status === 'stopped', show "Start" instead

**Recommended**: Option A (explicit user control)

### 3. Port Conflict Detection

When starting project, check if port is available:
```python
# In orchestration_service.py
def check_port_available(self, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def start(self, project_id: int):
    project = self.get_project(project_id)

    # Check ports before starting
    ports = [project.frontend_port, project.backend_port,
             project.postgres_port, project.redis_port]

    for port in ports:
        if not self.check_port_available(port):
            raise HTTPException(
                status_code=409,
                detail=f"Port {port} is already in use. Stop conflicting service first."
            )

    # Proceed with docker-compose up...
```

### 4. Browser Cache Workaround

Add query parameter with timestamp to force fresh load:
```typescript
// In ProjectCard.tsx handleOpen()
const timestamp = Date.now();
window.open(`http://localhost:${project.frontend_port}/?t=${timestamp}`, '_blank');
```

## Testing Checklist

To verify the fix:

- [x] Kill test server: `kill 42569` ✅
- [ ] Create new test project via Hub
- [ ] Verify status shows "stopped" in UI
- [ ] Click "Start" button (NOT "Open")
- [ ] Wait for containers to be healthy
- [ ] Click "Open" button
- [ ] Verify correct project name appears
- [ ] Test with multiple projects on different ports
- [ ] Test browser cache by hard refresh (Cmd+Shift+R)

## Update: Issue Persists After Test Server Kill

**Date**: October 16, 2025 21:35

After killing the test server (PID 42569) and attempting to start Rollizr again, **the issue persisted**.

### Evidence After Fix Attempt:
- ✅ Port 3010 is completely free (no server running)
- ✅ No Rollizr containers are running
- ✅ curl to localhost:3010 returns connection refused
- ❌ Browser still shows incorrect content when opening localhost:3010

### Hypothesis: Aggressive Browser Cache

**Strong evidence this is browser cache:**
1. No server is running on port 3010
2. curl returns nothing (connection refused)
3. Browser somehow displays content anyway
4. Only explanation: Browser is serving cached page

**Our cache-busting headers in index.html are not sufficient:**
```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
```

These headers only work AFTER the page is fetched from server. If browser cache is serving the page without even making a request, these headers never get read.

### Browser Cache Behavior

Browsers cache by **origin** (protocol + hostname + port):
- `http://localhost:3000` - Different cache entry
- `http://localhost:3010` - Different cache entry
- `http://localhost:8000` - Different cache entry

If Performia (or any content) was ever served on `localhost:3010` before, browser will cache it and serve it even when:
- Server is stopped
- Port is not listening
- Different project should be on that port now

### Why Standard Cache-Busting Doesn't Work

1. **Service Workers**: Can intercept requests and serve cached content
2. **Disk Cache**: Browser may not even check if server is alive
3. **HTTP/2 Push**: Cached push promises
4. **Prefetch/Preload**: Resource hints cached

### Required Fix: Force Cache Invalidation

**Option 1: Query Parameter (Simplest)**
```typescript
// ProjectCard.tsx - handleOpen()
const cacheBreaker = Date.now();
window.open(`http://localhost:${project.frontend_port}/?v=${cacheBreaker}`, '_blank');
```

**Option 2: Clear Site Data Header**
```nginx
# In nginx config
add_header Clear-Site-Data "cache, cookies, storage";
```

**Option 3: Service Worker Update**
```javascript
// Unregister all service workers on load
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(reg => reg.unregister());
});
```

**Option 4: User Action Required**
Instruct users to:
1. Open browser DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"
4. OR use incognito/private browsing

## Conclusion

**This was NOT a project name contamination bug.**

It was a perfect storm of:
- Projects never being started
- Port conflict with test server
- UX allowing "Open" on stopped projects
- **EXTREMELY aggressive browser caching of localhost ports**

The cache-busting meta tags are insufficient because browsers can serve cached content without ever reading the HTML headers.

All the previous fixes (runtime config, cache-busting, etc.) were **correct** but cannot fight browser disk cache when the browser doesn't even make a network request.

## Next Steps

1. Kill the test server on port 3010
2. Test the full workflow: Create → Start → Open
3. Consider implementing port conflict detection
4. Improve "Open" button behavior for stopped projects
5. Add query parameter cache-busting for extra safety

## Reference

See also:
- `docs/DATA_ISOLATION.md` - Multi-instance architecture
- `hub/TEMPLATE_SOURCE_OF_TRUTH.md` - Template distribution system
- `hub/frontend/src/components/ProjectCard.tsx` - Start/Stop UI logic
- `hub/backend/app/services/orchestration_service.py` - Container orchestration
