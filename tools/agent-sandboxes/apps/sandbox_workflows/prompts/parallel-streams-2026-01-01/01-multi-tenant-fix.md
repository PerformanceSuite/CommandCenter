# Stream A: Multi-Tenant Isolation Fix

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
# The GITHUB_TOKEN is available in your environment
# Configure git to use it for push operations
git remote set-url origin https://${GITHUB_TOKEN}@github.com/PerformanceSuite/CommandCenter.git

# Verify it's set (should show https://ghp_...@github.com/...)
git remote -v
```

**You MUST do this before attempting to push.** The sandbox doesn't have SSH keys.

---

## Context

CommandCenter has a **critical bug**: `backend/app/auth/project_context.py` hardcodes `project_id=1`, bypassing multi-tenant isolation. All users see the same project data regardless of permissions.

## Your Mission

Fix the multi-tenant isolation so each user accesses only their authorized projects.

## Branch

Create and work on: `fix/multi-tenant-isolation`

## Step-by-Step Implementation

### Step 1: Create UserProject Association Model

Create `backend/app/models/user_project.py`:

```python
"""User-Project association for multi-tenant isolation."""
from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class UserProject(Base):
    """Association table linking users to their authorized projects."""
    __tablename__ = "user_projects"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    role = Column(String(20), default="member")  # owner, admin, member
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="project_associations")
    project = relationship("Project", back_populates="user_associations")
```

### Step 2: Update User Model

Edit `backend/app/models/user.py` to add the relationship:

```python
# Add to imports
from sqlalchemy.orm import relationship

# Add to User class
project_associations = relationship(
    "UserProject",
    back_populates="user",
    cascade="all, delete-orphan"
)

@property
def projects(self):
    """Get all projects this user has access to."""
    return [assoc.project for assoc in self.project_associations]

@property
def default_project(self):
    """Get user's default project."""
    for assoc in self.project_associations:
        if assoc.is_default:
            return assoc.project
    # Fall back to first project
    if self.project_associations:
        return self.project_associations[0].project
    return None
```

### Step 3: Update Project Model

Edit `backend/app/models/project.py` to add the relationship:

```python
# Add to Project class
user_associations = relationship(
    "UserProject",
    back_populates="project",
    cascade="all, delete-orphan"
)

@property
def users(self):
    """Get all users with access to this project."""
    return [assoc.user for assoc in self.user_associations]
```

### Step 4: Fix project_context.py

Replace `backend/app/auth/project_context.py`:

```python
"""Project context dependency for multi-tenant isolation."""
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.user_project import UserProject


async def get_current_project_id(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_project_id: Optional[int] = Header(None, alias="X-Project-ID")
) -> int:
    """
    Get the current project ID for the authenticated user.

    Priority:
    1. X-Project-ID header (if user has access)
    2. User's default project
    3. First project user has access to

    Raises HTTPException 403 if user has no project access.
    """
    # If header provided, validate access
    if x_project_id is not None:
        has_access = await _check_project_access(db, user.id, x_project_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No access to project {x_project_id}"
            )
        return x_project_id

    # Get user's default or first project
    project_id = await _get_default_project_id(db, user.id)
    if project_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No project assigned. Contact administrator."
        )
    return project_id


async def _check_project_access(
    db: AsyncSession,
    user_id: int,
    project_id: int
) -> bool:
    """Check if user has access to a specific project."""
    result = await db.execute(
        select(UserProject).where(
            UserProject.user_id == user_id,
            UserProject.project_id == project_id
        )
    )
    return result.scalar_one_or_none() is not None


async def _get_default_project_id(
    db: AsyncSession,
    user_id: int
) -> Optional[int]:
    """Get user's default project ID."""
    # Try default first
    result = await db.execute(
        select(UserProject.project_id).where(
            UserProject.user_id == user_id,
            UserProject.is_default == True
        )
    )
    project_id = result.scalar_one_or_none()
    if project_id:
        return project_id

    # Fall back to first project
    result = await db.execute(
        select(UserProject.project_id).where(
            UserProject.user_id == user_id
        ).limit(1)
    )
    return result.scalar_one_or_none()
```

### Step 5: Create Database Migration

Create migration using alembic:

```bash
cd backend
alembic revision --autogenerate -m "Add user_projects table for multi-tenant isolation"
```

If alembic isn't set up, create manual migration in `backend/app/migrations/`:

```python
"""Add user_projects table for multi-tenant isolation.

Revision ID: add_user_projects
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'user_projects',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), primary_key=True),
        sa.Column('role', sa.String(20), server_default='member'),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Migrate existing users to project 1 (preserves current behavior during transition)
    op.execute("""
        INSERT INTO user_projects (user_id, project_id, role, is_default)
        SELECT id, 1, 'member', true FROM users
        WHERE NOT EXISTS (
            SELECT 1 FROM user_projects WHERE user_projects.user_id = users.id
        )
    """)

def downgrade():
    op.drop_table('user_projects')
```

### Step 6: Update Model Exports

Edit `backend/app/models/__init__.py`:

```python
from app.models.user_project import UserProject

# Add to __all__
__all__ = [..., "UserProject"]
```

### Step 7: Write Tests

Create `backend/tests/test_multi_tenant.py`:

```python
"""Tests for multi-tenant isolation."""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.project import Project
from app.models.user_project import UserProject


@pytest.mark.asyncio
async def test_user_can_access_assigned_project(
    client: AsyncClient,
    db_session,
    authenticated_user: User
):
    """User can access projects they're assigned to."""
    # Create project and assign user
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    user_project = UserProject(
        user_id=authenticated_user.id,
        project_id=project.id,
        is_default=True
    )
    db_session.add(user_project)
    await db_session.commit()

    # Access should work
    response = await client.get("/api/v1/projects/current")
    assert response.status_code == 200
    assert response.json()["id"] == project.id


@pytest.mark.asyncio
async def test_user_cannot_access_unassigned_project(
    client: AsyncClient,
    db_session,
    authenticated_user: User
):
    """User cannot access projects they're not assigned to."""
    # Create project but don't assign user
    project = Project(name="Forbidden Project")
    db_session.add(project)
    await db_session.commit()

    # Try to access via header
    response = await client.get(
        "/api/v1/projects/current",
        headers={"X-Project-ID": str(project.id)}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_x_project_id_header_overrides_default(
    client: AsyncClient,
    db_session,
    authenticated_user: User
):
    """X-Project-ID header overrides default project."""
    # Create two projects, assign both to user
    project1 = Project(name="Default Project")
    project2 = Project(name="Other Project")
    db_session.add_all([project1, project2])
    await db_session.commit()

    db_session.add(UserProject(
        user_id=authenticated_user.id,
        project_id=project1.id,
        is_default=True
    ))
    db_session.add(UserProject(
        user_id=authenticated_user.id,
        project_id=project2.id,
        is_default=False
    ))
    await db_session.commit()

    # Without header, get default
    response = await client.get("/api/v1/projects/current")
    assert response.json()["id"] == project1.id

    # With header, get specified
    response = await client.get(
        "/api/v1/projects/current",
        headers={"X-Project-ID": str(project2.id)}
    )
    assert response.json()["id"] == project2.id
```

## Verification

```bash
cd backend

# Run migration
alembic upgrade head

# Run tests
uv run pytest tests/test_multi_tenant.py -v

# Run full test suite to check for regressions
uv run pytest --tb=short
```

## Commit Strategy

1. `feat(auth): add UserProject model for multi-tenant isolation`
2. `feat(auth): update User and Project models with associations`
3. `fix(auth): replace hardcoded project_id with proper isolation`
4. `feat(db): add migration for user_projects table`
5. `test(auth): add multi-tenant isolation tests`

## Push and Create PR

After committing, push with authentication:

```bash
# Ensure remote uses token
git remote set-url origin https://${GITHUB_TOKEN}@github.com/PerformanceSuite/CommandCenter.git

# Push
git push -u origin fix/multi-tenant-isolation
```

Then create PR with:

Title: `fix(auth): implement proper multi-tenant project isolation`

Body:
```markdown
## Summary
Fixes critical multi-tenant isolation bypass where all users were seeing project_id=1.

## Changes
- Added `UserProject` association table
- Updated `User` and `Project` models with relationships
- Replaced hardcoded `project_id=1` with proper lookup
- Added X-Project-ID header support for project switching
- Migration preserves existing users by assigning them to project 1

## Testing
- Added unit tests for access control
- All existing tests pass

## Breaking Changes
- Frontend may need to send X-Project-ID header for multi-project users
```

## Completion Criteria

- [ ] UserProject model created
- [ ] User and Project models updated
- [ ] project_context.py fixed
- [ ] Migration created and applied
- [ ] Tests written and passing
- [ ] Branch pushed to GitHub
- [ ] PR created with clear description
