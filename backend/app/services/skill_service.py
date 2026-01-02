"""Service for managing skills."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, SkillUsage
from app.schemas.skill import (
    SkillCreate,
    SkillImportRequest,
    SkillSearchRequest,
    SkillUpdate,
    SkillUsageCreate,
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
        result = await self.db.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Skill]:
        """Get a skill by slug."""
        result = await self.db.execute(select(Skill).where(Skill.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(
        self,
        project_id: Optional[int] = None,
        include_global: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Skill]:
        """List skills with optional project filtering."""
        conditions = []

        if project_id is not None:
            if include_global:
                conditions.append(
                    or_(
                        Skill.project_id == project_id,
                        and_(Skill.project_id.is_(None), Skill.is_public.is_(True)),
                    )
                )
            else:
                conditions.append(Skill.project_id == project_id)
        else:
            conditions.append(or_(Skill.project_id.is_(None), Skill.is_public.is_(True)))

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

    async def search(
        self, search: SkillSearchRequest, project_id: Optional[int] = None
    ) -> List[Skill]:
        """Search skills by various criteria."""
        conditions = []

        # Access control
        if project_id is not None:
            if search.include_private:
                conditions.append(
                    or_(
                        Skill.project_id == project_id,
                        and_(Skill.project_id.is_(None), Skill.is_public.is_(True)),
                    )
                )
            else:
                conditions.append(Skill.is_public.is_(True))
        else:
            conditions.append(Skill.is_public.is_(True))

        # Text search
        if search.query:
            search_term = f"%{search.query}%"
            conditions.append(
                or_(
                    Skill.name.ilike(search_term),
                    Skill.description.ilike(search_term),
                    Skill.content.ilike(search_term),
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
        user_id: Optional[int] = None,
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
            outcome_notes=usage_data.outcome_notes,
        )
        self.db.add(usage)

        # Update skill stats
        success = usage_data.outcome == "success" if usage_data.outcome else None
        skill.record_usage(success=success)

        await self.db.commit()
        await self.db.refresh(usage)
        return usage

    async def import_from_filesystem(
        self, import_request: SkillImportRequest, project_id: Optional[int] = None
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
                    is_public=True,
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
