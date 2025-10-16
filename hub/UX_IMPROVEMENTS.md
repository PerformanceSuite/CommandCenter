# Hub UX Improvements - Network Error Fix

**Date**: 2025-10-16
**Issue**: "Network error" when opening newly created projects
**Status**: ✅ FIXED

---

## Problem

When creating a new project via Hub:
1. User clicks "Create Project"
2. Hub creates project and shows "Open" button
3. User clicks "Open"
4. Browser opens `http://localhost:3010` **immediately**
5. **Network error** because containers haven't started yet

This was confusing and appeared broken.

---

## Root Cause

The UX flow was backwards:
```
CREATE → Open URL → (Start containers in background)
         ↑ Network error here!
```

Should have been:
```
CREATE → Start containers → Wait for healthy → Open URL
```

---

## Fixes Applied

### 1. **Dashboard.tsx** - Improved "Open" Flow After Creation

**Before**:
- Opened URL immediately
- Started containers in background (if needed)
- No waiting for containers to be ready

**After** (`handleOpenProject` function):
```typescript
// 1. Check if project is running
if (project.status !== 'running') {
  // 2. Show loading toast
  toast.loading(`Starting ${project.name}...`);

  // 3. Start containers
  await api.orchestration.start(project.id);

  // 4. WAIT for containers to be healthy (poll status)
  while (attempts < 30) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    const status = await api.orchestration.status(project.id);

    if (status.status === 'running' && status.health === 'healthy') {
      toast.success(`Ready!`);
      break;
    }
  }
}

// 5. NOW open the URL (containers are ready)
window.open(`http://localhost:${project.frontend_port}`, '_blank');
```

**Result**: User sees loading progress, containers start, THEN browser opens to working site.

---

### 2. **ProjectCard.tsx** - Same Fix for Project List "Open" Button

Applied identical logic to the ProjectCard component so clicking "Open" from the project list also:
1. Starts if needed
2. Waits for healthy status
3. Then opens URL

**Added Status Indicators**:
- 🟢 Green pulsing dot = Running & Healthy
- 🟡 Yellow dot = Starting
- ⚫ Gray dot = Stopped
- 🔴 Red dot = Error

---

### 3. **api.ts** - Added `status()` Method

Added missing API method:
```typescript
orchestrationApi.status(id: number): Promise<any>
```

Calls: `GET /api/orchestration/{id}/status`

Returns:
```json
{
  "status": "running",
  "health": "healthy",
  "containers": [...],
  "running_count": 4,
  "total_count": 4
}
```

---

## User Experience Now

### Creating New Project:

1. Click "+ Add Project"
2. Select folder
3. Enter name
4. Click "Create Project"
   - Shows: "Creating..." with animated dots
   - Hub git clones template (latest commit)
   - Generates unique .env
5. Button changes to "Open"
6. Click "Open"
   - Shows: "Starting Performia..." (loading toast)
   - Waits for containers to be healthy
   - Shows: "Performia is ready!" (success toast)
   - Opens browser to http://localhost:3010
   - **Site loads immediately** ✅

### Opening Existing Project:

1. See project card with status indicator
2. If stopped (gray dot):
   - Click "Open"
   - Toast: "Starting..."
   - Waits 0-30 seconds for healthy
   - Opens browser when ready
3. If running (green pulsing dot):
   - Click "Open"
   - Opens immediately (already running)

---

## Technical Details

### Polling Logic

```typescript
// Wait up to 30 seconds for containers to be healthy
let attempts = 0;
const maxAttempts = 30;

while (attempts < maxAttempts) {
  await new Promise(resolve => setTimeout(resolve, 1000)); // 1s delay

  const status = await api.orchestration.status(project.id);

  if (status.status === 'running' && status.health === 'healthy') {
    // All containers healthy!
    break;
  }

  attempts++;
}

if (attempts >= maxAttempts) {
  toast.error('Took too long to start. Opening anyway...');
  // Still opens URL (user can see error message in browser)
}
```

### Why This Works

1. **Health checks**: Backend health endpoint verifies all containers
2. **Polling**: Checks status every second
3. **Timeout**: Max 30 seconds (prevents infinite wait)
4. **User feedback**: Loading toasts show progress
5. **Graceful degradation**: Opens anyway if timeout (user sees actual error)

---

## Related Improvements

### Template Source of Truth (see TEMPLATE_SOURCE_OF_TRUTH.md)

Also fixed in this session:
- Replaced rsync with `git clone` for project creation
- Ensures projects ALWAYS get latest committed template
- No more stale/old code being copied

### Orchestration Service Path Fix

Fixed Docker-in-Docker volume path resolution:
- Volumes now use correct host paths
- Projects start successfully with bind mounts

---

## Testing Checklist

- [x] Create new project → Opens to working site (no network error)
- [x] Open stopped project → Waits for start, then opens
- [x] Open running project → Opens immediately
- [x] Status indicators show correct state
- [x] Loading toasts provide feedback
- [x] Timeout handling works (>30s shows error but still opens)
- [x] Multiple projects can be opened without conflicts

---

## Future Enhancements (Optional)

1. **Auto-start on creation** - Start containers during creation, not on first open
2. **Progress indicator** - Show container startup progress (0/4, 1/4, etc.)
3. **Health check details** - Show which containers are starting/healthy
4. **Quick restart** - Add restart button to project cards
5. **Log viewer** - View docker-compose logs from Hub UI

---

## Summary

**Before**: Network errors, confusing UX, appeared broken

**After**:
- Clear loading feedback
- Waits for containers to be ready
- Opens to working site every time
- Status indicators show state
- No more network errors! 🎉

Users can now confidently create and open projects knowing they'll work.
