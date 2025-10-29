# Authentication Simplification Design

**Date:** 2025-10-27
**Status:** Approved
**Decision:** Single-Project-Per-Instance Model

---

## Problem

Current codebase has TODOs suggesting complex project_id validation:
- `technology_service.py:100,110` - "TODO: Replace default with authenticated user's project_id"
- `knowledge.py:30,72` - "TODO: Get from auth context"
- `webhooks.py:458` - "TODO: Get project_id from auth context"

These TODOs suggest multi-project tenancy within a single CommandCenter instance.

---

## Architecture Context

**CommandCenter Hub** manages multiple isolated instances:

```
Hub (Port 9000/9001) - Dagger SDK orchestration
├── Instance A: Performia        (Port 8000, isolated DB/volumes)
├── Instance B: AI Research      (Port 8010, isolated DB/volumes)
└── Instance C: E-commerce       (Port 8020, isolated DB/volumes)
```

**Key Insight:** Multi-tenancy happens at the **Hub level** (separate instances), not within each CommandCenter instance.

---

## Design Decision

### Single-Project-Per-Instance Model

Each CommandCenter instance represents exactly **one project**:
- `project_id` is always `1` within each instance
- Hub orchestrates cross-project operations by calling multiple instance APIs
- Auth validates: "Is user authenticated for THIS instance?"
- No project ownership validation needed

---

## Implementation

### 1. Instance Configuration

```python
# app/config.py
INSTANCE_PROJECT_ID = 1  # Constant for this instance
```

### 2. Authentication Pattern

Endpoints only need user authentication, not project validation:

```python
@router.get("/technologies")
async def list_technologies(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Always use INSTANCE_PROJECT_ID
    technologies = await service.list_technologies(
        db, project_id=INSTANCE_PROJECT_ID
    )
```

### 3. Remove Misleading TODOs

The following TODOs are based on incorrect multi-project assumptions and should be removed:

- ✅ `backend/app/services/technology_service.py:100,110` - Remove "TODO (Rec 2.4)" comments
- ✅ `backend/app/routers/knowledge.py:30,72` - Change `project_id: int = 1` to use `INSTANCE_PROJECT_ID`
- ✅ `backend/app/routers/webhooks.py:458` - Use `INSTANCE_PROJECT_ID` constant

### 4. User Authentication Enforcement

Ensure all endpoints use `Depends(get_current_active_user)` where appropriate:
- Technology endpoints
- Knowledge base endpoints
- Webhook endpoints
- Repository endpoints

---

## Rationale

**Why Single-Project-Per-Instance?**

1. **Matches Hub Architecture**: Hub already provides multi-project management via isolated instances
2. **Maintains Strong Isolation**: Separate databases, volumes, networks per project (security best practice)
3. **Simplifies Auth**: No complex project ownership validation needed
4. **YAGNI Principle**: Multi-project within instance is not a requirement
5. **Clear Boundaries**: Instance = Project = Security Boundary

**Why NOT Multi-Project-Per-Instance?**

1. Would duplicate Hub's purpose
2. Weakens isolation guarantees
3. Adds unnecessary complexity
4. Contradicts DATA_ISOLATION.md documentation

---

## Migration Path

### Phase 1: Cleanup (Immediate)
1. Add `INSTANCE_PROJECT_ID = 1` to `app/config.py`
2. Remove misleading TODO comments
3. Replace hardcoded `project_id = 1` with `INSTANCE_PROJECT_ID`

### Phase 2: Auth Enforcement (Next)
1. Audit endpoints for missing `get_current_active_user` dependency
2. Add authentication where missing
3. Test all protected endpoints require valid JWT

### Phase 3: Documentation (Next)
1. Update CLAUDE.md to explain single-project model
2. Add architecture diagram showing Hub → Instances relationship
3. Update DATA_ISOLATION.md to clarify project_id usage

---

## Security Model

**Per-Instance Isolation** (maintained):
- ✅ Separate Docker containers
- ✅ Separate PostgreSQL databases
- ✅ Separate Docker volumes
- ✅ Separate network namespaces
- ✅ Unique secrets per instance

**User Authentication** (enforced):
- ✅ JWT-based authentication
- ✅ Per-endpoint validation via `get_current_active_user`
- ✅ Token encryption in database
- ✅ Rate limiting on auth endpoints

**Hub Orchestration** (future):
- Hub authenticates users at Hub level
- Hub proxies requests to appropriate instance APIs
- Each instance validates its own authentication
- Hub aggregates cross-instance results

---

## Alternative Approaches Considered

### ❌ Multi-Project-Per-Instance
- Would require `X-Project-ID` header validation
- User → Project ownership validation
- Complex auth middleware
- **Rejected:** Conflicts with Hub's isolation model

### ❌ Remove Project Model Entirely
- Simplest possible approach
- No project metadata stored
- **Rejected:** Loss of useful metadata (project name, description, owner)

---

## Open Questions

1. **Hub Authentication**: Should Hub manage user authentication centrally, or does each instance authenticate independently?
2. **Cross-Instance Queries**: Does Hub need read-only access to instance databases, or only via APIs?
3. **User Registration**: Where do users register - Hub or individual instances?

**Recommendation:** Defer these questions to Hub design. This design focuses on single-instance auth only.

---

## Success Criteria

- ✅ All TODOs related to project_id validation removed
- ✅ `INSTANCE_PROJECT_ID` constant used consistently
- ✅ All protected endpoints require authentication
- ✅ No breaking changes to existing API contracts
- ✅ Documentation updated to reflect single-project model

---

## References

- `hub/README.md` - Hub architecture and multi-instance management
- `docs/DATA_ISOLATION.md` - Per-instance isolation requirements
- `docs/UNIVERSAL_DAGGER_PATTERN.md` - Dagger SDK orchestration pattern
- `backend/app/routers/auth.py` - Current JWT authentication implementation
