# Stream B: Skills Foundation

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

CommandCenter is evolving to have **native skills support** - skills as first-class database entities with tracking, search, and effectiveness metrics. This is the Self-Improvement pillar of the platform.

Currently, skills live only in `~/.claude/skills/` as markdown files. We're bridging them into CommandCenter.

## Your Mission

Create the database model, service, and API for CommandCenter-native skills.

## Branch

Create and work on: `feature/skills-native`

## Step-by-Step Implementation

### Step 1: Create Skill Model

Create `backend/app/models/skill.py`:

```python
"""Skill model for self-improving AI workflows."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Skill(Base):
    """
    A skill represents a reusable AI workflow pattern.

    Skills can be:
    - Global (project_id=None) - available across all projects
    - Project-specific - only available within a project
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Content
    content = Column(Text, nullable=False)  # The SKILL.md content
    content_path = Column(String(500))  # Optional: path to external file

    # Taxonomy
    category = Column(String(50), default="workflow")  # workflow, pattern, tool, methodology
    tags = Column(JSON, default=list)  # ["multi-agent", "parallel", "e2b"]

    # Versioning
    version = Column(String(20), default="1.0.0")

    # Metadata
    author = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Effectiveness tracking
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    effectiveness_score = Column(Float, default=0.0)

    # Multi-tenant
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    is_public = Column(Boolean, default=True)  # Visible to other projects?

    # AI Arena validation
    last_validated_at = Column(DateTime, nullable=True)
    validation_score = Column(Float, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="skills")
    usages = relationship("SkillUsage", back_populates="skill", cascade="all, delete-orphan")

    def record_usage(self, success: bool = None):
        """Record a usage of this skill."""
        self.usage_count += 1
        if success is True:
            self.success_count += 1
        elif success is False:
            self.failure_count += 1
        self._update_effectiveness()

    def _update_effectiveness(self):
        """Recalculate effectiveness score."""
        if self.usage_count == 0:
            self.effectiveness_score = 0.0
        else:
            # Simple success rate, can be made more sophisticated
            rated_count = self.success_count + self.failure_count
            if rated_count > 0:
                self.effectiveness_score = self.success_count / rated_count
            else:
                self.effectiveness_score = 0.5  # Unknown


class SkillUsage(Base):
    """Track individual uses of skills for effectiveness measurement."""
    __tablename__ = "skill_usages"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)

    # Context
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100))  # External session identifier

    # Outcome
    used_at = Column(DateTime, default=datetime.utcnow)
    outcome = Column(String(20))  # success, failure, neutral, pending
    outcome_notes = Column(Text)

    # Relationships
    skill = relationship("Skill", back_populates="usages")
```

### Step 2: Create Skill Schemas

Create `backend/app/schemas/skill.py`:

```python
"""Pydantic schemas for skills."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    """Base schema for skills."""
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: str
    category: str = "workflow"
    tags: List[str] = []
    version: str = "1.0.0"
    author: Optional[str] = None
    is_public: bool = True


class SkillCreate(SkillBase):
    """Schema for creating a skill."""
    project_id: Optional[int] = None


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    is_public: Optional[bool] = None


class SkillResponse(SkillBase):
    """Schema for skill responses."""
    id: int
    project_id: Optional[int]
    usage_count: int
    success_count: int
    failure_count: int
    effectiveness_score: float
    last_validated_at: Optional[datetime]
    validation_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SkillUsageCreate(BaseModel):
    """Schema for recording skill usage."""
    skill_id: int
    session_id: Optional[str] = None
    outcome: Optional[str] = None  # success, failure, neutral
    outcome_notes: Optional[str] = None


class SkillUsageResponse(BaseModel):
    """Schema for skill usage responses."""
    id: int
    skill_id: int
    project_id: Optional[int]
    user_id: Optional[int]
    session_id: Optional[str]
    used_at: datetime
    outcome: Optional[str]
    outcome_notes: Optional[str]

    class Config:
        from_attributes = True


class SkillImportRequest(BaseModel):
    """Schema for importing skills from filesystem."""
    path: str = Field(..., description="Path to skills directory (e.g., ~/.claude/skills)")
    overwrite: bool = Field(default=False, description="Overwrite existing skills with same slug")


class SkillSearchRequest(BaseModel):
    """Schema for searching skills."""
    query: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    min_effectiveness: Optional[float] = None
    include_private: bool = False
```

### Step 3: Create Skill Service

Create `backend/app/services/skill_service.py`:

```python
"""Service for managing skills."""
import os
import re
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, SkillUsage
from app.schemas.skill import (
    SkillCreate, SkillUpdate, SkillImportRequest,
    SkillSearchRequest, SkillUsageCreate
)


class SkillService:
    """Service for skill CRUD and tracking operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, skill_data: SkillCreate) -> Skill:
        """Create a new skill."""
        skill = Skill(**skill_data.model_dump())
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def get_by_id(self, skill_id: int) -> Optional[Skill]:
        """Get a skill by ID."""
        result = await self.db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Skill]:
        """Get a skill by slug."""
        result = await self.db.execute(
            select(Skill).where(Skill.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        project_id: Optional[int] = None,
        include_global: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Skill]:
        """List skills with optional project filtering."""
        conditions = []

        if project_id is not None:
            if include_global:
                conditions.append(
                    or_(
                        Skill.project_id == project_id,
                        and_(Skill.project_id.is_(None), Skill.is_public == True)
                    )
                )
            else:
                conditions.append(Skill.project_id == project_id)
        else:
            conditions.append(
                or_(Skill.project_id.is_(None), Skill.is_public == True)
            )

        query = select(Skill).where(*conditions).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, skill_id: int, skill_data: SkillUpdate) -> Optional[Skill]:
        """Update a skill."""
        skill = await self.get_by_id(skill_id)
        if not skill:
            return None

        update_data = skill_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(skill, key, value)

        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def delete(self, skill_id: int) -> bool:
        """Delete a skill."""
        skill = await self.get_by_id(skill_id)
        if not skill:
            return False

        await self.db.delete(skill)
        await self.db.commit()
        return True

    async def search(self, search: SkillSearchRequest, project_id: Optional[int] = None) -> List[Skill]:
        """Search skills by various criteria."""
        conditions = []

        # Access control
        if project_id is not None:
            if search.include_private:
                conditions.append(
                    or_(
                        Skill.project_id == project_id,
                        and_(Skill.project_id.is_(None), Skill.is_public == True)
                    )
                )
            else:
                conditions.append(Skill.is_public == True)
        else:
            conditions.append(Skill.is_public == True)

        # Text search
        if search.query:
            search_term = f"%{search.query}%"
            conditions.append(
                or_(
                    Skill.name.ilike(search_term),
                    Skill.description.ilike(search_term),
                    Skill.content.ilike(search_term)
                )
            )

        # Category filter
        if search.category:
            conditions.append(Skill.category == search.category)

        # Effectiveness filter
        if search.min_effectiveness is not None:
            conditions.append(Skill.effectiveness_score >= search.min_effectiveness)

        # Tag filtering would require JSON operators, simplified here

        query = select(Skill).where(*conditions).order_by(Skill.effectiveness_score.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def record_usage(
        self,
        usage_data: SkillUsageCreate,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> SkillUsage:
        """Record a skill usage."""
        skill = await self.get_by_id(usage_data.skill_id)
        if not skill:
            raise ValueError(f"Skill {usage_data.skill_id} not found")

        # Create usage record
        usage = SkillUsage(
            skill_id=usage_data.skill_id,
            project_id=project_id,
            user_id=user_id,
            session_id=usage_data.session_id,
            outcome=usage_data.outcome,
            outcome_notes=usage_data.outcome_notes
        )
        self.db.add(usage)

        # Update skill stats
        success = usage_data.outcome == "success" if usage_data.outcome else None
        skill.record_usage(success=success)

        await self.db.commit()
        await self.db.refresh(usage)
        return usage

    async def import_from_filesystem(
        self,
        import_request: SkillImportRequest,
        project_id: Optional[int] = None
    ) -> List[Skill]:
        """Import skills from filesystem directory."""
        path = Path(import_request.path).expanduser()
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

        imported = []

        for skill_dir in path.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            content = skill_file.read_text()

            # Parse frontmatter
            metadata = self._parse_skill_frontmatter(content)
            slug = skill_dir.name

            # Check if exists
            existing = await self.get_by_slug(slug)
            if existing and not import_request.overwrite:
                continue

            if existing:
                # Update existing
                existing.content = content
                existing.name = metadata.get("name", slug)
                existing.description = metadata.get("description", "")
                existing.updated_at = datetime.utcnow()
                await self.db.commit()
                imported.append(existing)
            else:
                # Create new
                skill = Skill(
                    slug=slug,
                    name=metadata.get("name", slug),
                    description=metadata.get("description", ""),
                    content=content,
                    content_path=str(skill_file),
                    category=metadata.get("category", "workflow"),
                    tags=metadata.get("tags", []),
                    author=metadata.get("author"),
                    project_id=project_id,
                    is_public=True
                )
                self.db.add(skill)
                await self.db.commit()
                await self.db.refresh(skill)
                imported.append(skill)

        return imported

    def _parse_skill_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from skill content."""
        # Simple frontmatter parser
        if not content.startswith("---"):
            return {}

        try:
            end = content.index("---", 3)
            frontmatter = content[3:end].strip()

            metadata = {}
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

            return metadata
        except ValueError:
            return {}
```

### Step 4: Create Skill Router

Create `backend/app/routers/skills.py`:

```python
"""API router for skills."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.project_context import get_current_project_id
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.skill_service import SkillService
from app.schemas.skill import (
    SkillCreate, SkillUpdate, SkillResponse,
    SkillUsageCreate, SkillUsageResponse,
    SkillImportRequest, SkillSearchRequest
)

router = APIRouter(prefix="/skills", tags=["skills"])


def get_skill_service(db: AsyncSession = Depends(get_db)) -> SkillService:
    return SkillService(db)


@router.get("", response_model=List[SkillResponse])
async def list_skills(
    include_global: bool = True,
    limit: int = 100,
    offset: int = 0,
    project_id: int = Depends(get_current_project_id),
    service: SkillService = Depends(get_skill_service)
):
    """List all available skills."""
    return await service.list_all(
        project_id=project_id,
        include_global=include_global,
        limit=limit,
        offset=offset
    )


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    service: SkillService = Depends(get_skill_service)
):
    """Get a skill by ID."""
    skill = await service.get_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.get("/by-slug/{slug}", response_model=SkillResponse)
async def get_skill_by_slug(
    slug: str,
    service: SkillService = Depends(get_skill_service)
):
    """Get a skill by slug."""
    skill = await service.get_by_slug(slug)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    project_id: int = Depends(get_current_project_id),
    service: SkillService = Depends(get_skill_service)
):
    """Create a new skill."""
    # Check for duplicate slug
    existing = await service.get_by_slug(skill_data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Skill with slug '{skill_data.slug}' already exists"
        )

    if skill_data.project_id is None:
        skill_data.project_id = project_id

    return await service.create(skill_data)


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    service: SkillService = Depends(get_skill_service)
):
    """Update a skill."""
    skill = await service.update(skill_id, skill_data)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    service: SkillService = Depends(get_skill_service)
):
    """Delete a skill."""
    deleted = await service.delete(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")


@router.post("/search", response_model=List[SkillResponse])
async def search_skills(
    search: SkillSearchRequest,
    project_id: int = Depends(get_current_project_id),
    service: SkillService = Depends(get_skill_service)
):
    """Search skills."""
    return await service.search(search, project_id=project_id)


@router.post("/import", response_model=List[SkillResponse])
async def import_skills(
    import_request: SkillImportRequest,
    project_id: int = Depends(get_current_project_id),
    service: SkillService = Depends(get_skill_service)
):
    """Import skills from filesystem."""
    try:
        return await service.import_from_filesystem(import_request, project_id=project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/usage", response_model=SkillUsageResponse, status_code=status.HTTP_201_CREATED)
async def record_skill_usage(
    usage_data: SkillUsageCreate,
    project_id: int = Depends(get_current_project_id),
    user: User = Depends(get_current_user),
    service: SkillService = Depends(get_skill_service)
):
    """Record a skill usage for effectiveness tracking."""
    try:
        return await service.record_usage(
            usage_data,
            project_id=project_id,
            user_id=user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Step 5: Register Router

Edit `backend/app/main.py` to add the skills router:

```python
from app.routers import skills

# Add with other router includes
app.include_router(skills.router, prefix="/api/v1")
```

### Step 6: Update Model Exports

Edit `backend/app/models/__init__.py`:

```python
from app.models.skill import Skill, SkillUsage

# Add to __all__
__all__ = [..., "Skill", "SkillUsage"]
```

### Step 7: Create Migration

```bash
cd backend
alembic revision --autogenerate -m "Add skills and skill_usages tables"
```

### Step 8: Write Tests

Create `backend/tests/test_skills.py`:

```python
"""Tests for skills API."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_skill(client: AsyncClient, authenticated_headers):
    """Can create a skill."""
    response = await client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "slug": "test-skill",
            "name": "Test Skill",
            "description": "A test skill",
            "content": "# Test Skill\n\nThis is a test.",
            "category": "workflow",
            "tags": ["test"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "test-skill"
    assert data["usage_count"] == 0


@pytest.mark.asyncio
async def test_get_skill_by_slug(client: AsyncClient, authenticated_headers):
    """Can get a skill by slug."""
    # First create
    await client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "slug": "findable-skill",
            "name": "Findable Skill",
            "content": "# Content"
        }
    )

    # Then find
    response = await client.get(
        "/api/v1/skills/by-slug/findable-skill",
        headers=authenticated_headers
    )
    assert response.status_code == 200
    assert response.json()["slug"] == "findable-skill"


@pytest.mark.asyncio
async def test_record_usage(client: AsyncClient, authenticated_headers):
    """Can record skill usage."""
    # Create skill
    create_resp = await client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={
            "slug": "usage-test",
            "name": "Usage Test",
            "content": "# Content"
        }
    )
    skill_id = create_resp.json()["id"]

    # Record usage
    response = await client.post(
        "/api/v1/skills/usage",
        headers=authenticated_headers,
        json={
            "skill_id": skill_id,
            "outcome": "success"
        }
    )
    assert response.status_code == 201

    # Check count updated
    skill_resp = await client.get(
        f"/api/v1/skills/{skill_id}",
        headers=authenticated_headers
    )
    assert skill_resp.json()["usage_count"] == 1
    assert skill_resp.json()["success_count"] == 1


@pytest.mark.asyncio
async def test_search_skills(client: AsyncClient, authenticated_headers):
    """Can search skills."""
    # Create skills
    await client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={"slug": "parallel-agent", "name": "Parallel Agents", "content": "Multi-agent patterns", "category": "workflow"}
    )
    await client.post(
        "/api/v1/skills",
        headers=authenticated_headers,
        json={"slug": "single-agent", "name": "Single Agent", "content": "Simple patterns", "category": "pattern"}
    )

    # Search by query
    response = await client.post(
        "/api/v1/skills/search",
        headers=authenticated_headers,
        json={"query": "parallel"}
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["slug"] == "parallel-agent"

    # Search by category
    response = await client.post(
        "/api/v1/skills/search",
        headers=authenticated_headers,
        json={"category": "pattern"}
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["slug"] == "single-agent"
```

## Verification

```bash
cd backend

# Run migration
alembic upgrade head

# Run tests
uv run pytest tests/test_skills.py -v

# Test import endpoint manually
curl -X POST http://localhost:8000/api/v1/skills/import \
  -H "Content-Type: application/json" \
  -d '{"path": "~/.claude/skills"}'
```

## Commit Strategy

1. `feat(skills): add Skill and SkillUsage models`
2. `feat(skills): add skill schemas`
3. `feat(skills): add SkillService with CRUD and import`
4. `feat(skills): add skills API router`
5. `feat(db): add migration for skills tables`
6. `test(skills): add skills API tests`

## Create PR

Title: `feat(skills): add CommandCenter-native skills support`

Body:
```markdown
## Summary
Adds skills as first-class entities in CommandCenter, enabling tracking, search, and effectiveness measurement.

## Features
- Full CRUD for skills
- Import from ~/.claude/skills filesystem
- Usage tracking with outcome recording
- Effectiveness score calculation
- Search by text, category, tags
- Multi-tenant support (global vs project-specific skills)

## API Endpoints
- GET /api/v1/skills - List skills
- GET /api/v1/skills/{id} - Get skill by ID
- GET /api/v1/skills/by-slug/{slug} - Get skill by slug
- POST /api/v1/skills - Create skill
- PATCH /api/v1/skills/{id} - Update skill
- DELETE /api/v1/skills/{id} - Delete skill
- POST /api/v1/skills/search - Search skills
- POST /api/v1/skills/import - Import from filesystem
- POST /api/v1/skills/usage - Record skill usage

## Future Work
- KnowledgeBeast integration for semantic search
- AI Arena validation
- Automatic skill refinement proposals
```

## Completion Criteria

- [ ] Skill and SkillUsage models created
- [ ] Schemas created
- [ ] SkillService with full functionality
- [ ] Router registered and working
- [ ] Migration created and applied
- [ ] Tests written and passing
- [ ] Import from ~/.claude/skills works
- [ ] PR created with clear description
