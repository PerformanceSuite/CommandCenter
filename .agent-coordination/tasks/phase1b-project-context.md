# Phase 1b: Project Context Agent

## Mission
Add ProjectContextMiddleware to extract project_id from requests and enforce access control.

## Priority
HIGH - Enables all other isolation mechanisms

## Estimated Time
2 hours

## Tasks

### 1. Create ProjectContextMiddleware (1 hour)
```python
# backend/app/middleware/project_context.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class ProjectContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract project_id from:
        # 1. Header: X-Project-ID (priority)
        # 2. JWT token claim: project_id
        # 3. Query param: ?project_id=123 (fallback)
        
        project_id = request.headers.get("X-Project-ID")
        
        if not project_id and hasattr(request.state, "user"):
            # Get from JWT token
            project_id = request.state.user.get("project_id")
        
        if not project_id:
            # Get from query params
            project_id = request.query_params.get("project_id")
        
        if not project_id:
            raise HTTPException(
                status_code=400,
                detail="project_id required (X-Project-ID header or query param)"
            )
        
        # Validate project exists and user has access
        # (Add your auth logic here)
        
        # Attach to request state
        request.state.project_id = int(project_id)
        
        response = await call_next(request)
        return response
```

### 2. Add to FastAPI App (15 min)
```python
# backend/app/main.py

from app.middleware.project_context import ProjectContextMiddleware

app.add_middleware(ProjectContextMiddleware)
```

### 3. Add Frontend Project Selector (30 min)
```tsx
// frontend/src/components/common/ProjectSelector.tsx

export const ProjectSelector = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(
    localStorage.getItem('project_id')
  );
  
  // Fetch projects on mount
  // On selection change: localStorage + axios default header
  
  return (
    <select value={selectedProject} onChange={handleChange}>
      {projects.map(p => <option value={p.id}>{p.name}</option>)}
    </select>
  );
};
```

Add to Header component and configure axios to send X-Project-ID header.

### 4. Add Tests (15 min)
- Test project_id extraction from header
- Test project_id extraction from JWT
- Test missing project_id returns 400
- Test invalid project_id returns 403

## Success Criteria
- ✅ Middleware extracts project_id from requests
- ✅ Invalid requests blocked
- ✅ Frontend sends X-Project-ID header
- ✅ All services receive project_id
- ✅ Tests pass
