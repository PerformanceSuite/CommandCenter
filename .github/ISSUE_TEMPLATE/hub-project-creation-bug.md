# Hub Project Creation Issue

## Bug Description
When attempting to create a new project through the CommandCenter Hub UI, the project appears in "Your Projects" list BEFORE the user clicks "Create Project", and the system shows an "Internal Server Error" message briefly.

## Steps to Reproduce
1. Navigate to http://localhost:9000 (Hub UI)
2. Click "+ Add New Project"
3. Select a project folder (e.g., `/projects/Performia`)
4. Enter project name (e.g., "Performia")
5. **WITHOUT clicking "Create Project"**, the project already appears in "Your Projects" section below
6. Click "Create Project" → Shows "Internal Server Error" briefly
7. Project remains in the list with correct ports assigned

## Expected Behavior
- Project should NOT appear in "Your Projects" until "Create Project" is clicked
- No error message should be shown
- Project should be created successfully with CommandCenter cloned to the target directory

## Current Behavior
- Project appears in list before creation
- "Internal Server Error" flashes briefly
- Project record is created but setup may be incomplete

## Technical Details

### Root Cause Hypotheses
1. **Frontend polling issue**: Dashboard polls `/api/projects/` every 5 seconds. If project creation starts and takes >5s, the partially created project appears before the POST completes
2. **Database transaction issue**: Project record created before setup completes, making it visible to GET requests
3. **Error handling**: POST /api/projects/ may be failing but leaving a database record

### Files Involved
- `hub/frontend/src/pages/Dashboard.tsx` (lines 33-38: polling logic)
- `hub/backend/app/services/project_service.py` (lines 112-141: create_project method)
- `hub/backend/app/services/setup_service.py` (lines 19-35: setup_commandcenter method)

### Recent Changes
- Commit `727fd67`: Fixed CC_SOURCE path from host path to container mount path
- Commit `694d7a7`: Added project deletion feature
- Commit `a9bd558`: Fixed sidebar alignment

## Environment
- Docker Compose setup
- Hub Backend: Python 3.11, FastAPI, SQLite
- Hub Frontend: Node 20, React, TypeScript
- OS: macOS (Darwin 24.6.0)

## Proposed Solutions

### Option 1: Transaction-based Creation
```python
async def create_project(self, project_data: ProjectCreate) -> Project:
    # Create project record with status='creating'
    project = Project(..., status="creating")
    self.db.add(project)
    await self.db.commit()

    try:
        # Setup CommandCenter
        await self.setup_service.setup_commandcenter(project)

        # Update status to 'stopped' only after success
        project.status = "stopped"
        project.is_configured = True
        await self.db.commit()
    except Exception as e:
        # Mark as error if setup fails
        project.status = "error"
        await self.db.commit()
        raise

    return project
```

### Option 2: Filter Incomplete Projects in API
```python
async def list_projects(self) -> List[Project]:
    """List all projects (exclude ones being created)"""
    result = await self.db.execute(
        select(Project).where(Project.status != "creating")
    )
    return list(result.scalars().all())
```

### Option 3: Disable Polling During Creation
```typescript
const handleCreateProject = async () => {
    setCreatingProject(true);
    clearInterval(pollingIntervalRef.current); // Stop polling

    try {
        await projectsApi.create({...});
        await loadProjects(); // Manual refresh
    } finally {
        setCreatingProject(false);
        // Restart polling after creation completes
        pollingIntervalRef.current = setInterval(loadProjects, 5000);
    }
};
```

## Priority
**Medium** - Functionality works but UX is confusing and error message is misleading

## Labels
`bug`, `hub`, `ui`, `backend`
