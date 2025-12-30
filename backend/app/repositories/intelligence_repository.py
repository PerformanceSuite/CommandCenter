"""
Repository for Intelligence Integration models

Provides database access for:
- Hypothesis
- Evidence
- Debate
- ResearchFinding
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Debate, DebateStatus, Evidence, Hypothesis, HypothesisStatus, ResearchFinding


class HypothesisRepository:
    """Repository for Hypothesis CRUD operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, hypothesis_id: int, load_relations: bool = False
    ) -> Optional[Hypothesis]:
        """Get hypothesis by ID, optionally with relations"""
        stmt = select(Hypothesis).where(Hypothesis.id == hypothesis_id)

        if load_relations:
            stmt = stmt.options(
                selectinload(Hypothesis.evidence),
                selectinload(Hypothesis.debates),
            )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_task(
        self,
        task_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[HypothesisStatus] = None,
    ) -> list[Hypothesis]:
        """Get hypotheses for a research task"""
        stmt = select(Hypothesis).where(Hypothesis.research_task_id == task_id)

        if status:
            stmt = stmt.where(Hypothesis.status == status)

        stmt = stmt.order_by(Hypothesis.priority_score.desc(), Hypothesis.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[HypothesisStatus] = None,
    ) -> list[Hypothesis]:
        """Get all hypotheses for a project"""
        stmt = select(Hypothesis).where(Hypothesis.project_id == project_id)

        if status:
            stmt = stmt.where(Hypothesis.status == status)

        stmt = stmt.order_by(Hypothesis.priority_score.desc(), Hypothesis.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_task(self, task_id: int, status: Optional[HypothesisStatus] = None) -> int:
        """Count hypotheses for a task"""
        stmt = select(func.count(Hypothesis.id)).where(Hypothesis.research_task_id == task_id)
        if status:
            stmt = stmt.where(Hypothesis.status == status)

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_by_project(
        self, project_id: int, status: Optional[HypothesisStatus] = None
    ) -> int:
        """Count hypotheses for a project"""
        stmt = select(func.count(Hypothesis.id)).where(Hypothesis.project_id == project_id)
        if status:
            stmt = stmt.where(Hypothesis.status == status)

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(
        self,
        project_id: int,
        research_task_id: int,
        **kwargs: Any,
    ) -> Hypothesis:
        """Create a new hypothesis"""
        hypothesis = Hypothesis(
            project_id=project_id,
            research_task_id=research_task_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs,
        )
        self.db.add(hypothesis)
        return hypothesis

    async def update(self, hypothesis: Hypothesis, **kwargs: Any) -> Hypothesis:
        """Update a hypothesis"""
        for key, value in kwargs.items():
            if hasattr(hypothesis, key):
                setattr(hypothesis, key, value)
        hypothesis.updated_at = datetime.utcnow()
        return hypothesis

    async def delete(self, hypothesis: Hypothesis) -> None:
        """Delete a hypothesis"""
        await self.db.delete(hypothesis)

    async def get_statistics_by_project(self, project_id: int) -> dict[str, Any]:
        """Get hypothesis statistics for a project"""
        # Count by status
        stmt = (
            select(Hypothesis.status, func.count(Hypothesis.id))
            .where(Hypothesis.project_id == project_id)
            .group_by(Hypothesis.status)
        )
        result = await self.db.execute(stmt)
        by_status = {row[0].value: row[1] for row in result.all()}

        # Total count
        total_stmt = select(func.count(Hypothesis.id)).where(Hypothesis.project_id == project_id)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()

        return {
            "total": total,
            "by_status": by_status,
            "validated": by_status.get("validated", 0),
            "invalidated": by_status.get("invalidated", 0),
            "needs_more_data": by_status.get("needs_more_data", 0),
            "untested": by_status.get("untested", 0),
            "validating": by_status.get("validating", 0),
        }

    async def get_needing_attention(self, project_id: int, limit: int = 10) -> list[Hypothesis]:
        """Get hypotheses that need attention (untested with high priority or stale)"""
        stmt = (
            select(Hypothesis)
            .where(Hypothesis.project_id == project_id)
            .where(
                Hypothesis.status.in_([HypothesisStatus.UNTESTED, HypothesisStatus.NEEDS_MORE_DATA])
            )
            .order_by(Hypothesis.priority_score.desc(), Hypothesis.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class EvidenceRepository:
    """Repository for Evidence CRUD operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, evidence_id: int) -> Optional[Evidence]:
        """Get evidence by ID"""
        stmt = select(Evidence).where(Evidence.id == evidence_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_hypothesis(
        self, hypothesis_id: int, skip: int = 0, limit: int = 50
    ) -> list[Evidence]:
        """Get evidence for a hypothesis"""
        stmt = (
            select(Evidence)
            .where(Evidence.hypothesis_id == hypothesis_id)
            .order_by(Evidence.confidence.desc(), Evidence.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_hypothesis(self, hypothesis_id: int) -> int:
        """Count evidence for a hypothesis"""
        stmt = select(func.count(Evidence.id)).where(Evidence.hypothesis_id == hypothesis_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, hypothesis_id: int, **kwargs: Any) -> Evidence:
        """Create new evidence"""
        evidence = Evidence(
            hypothesis_id=hypothesis_id,
            created_at=datetime.utcnow(),
            **kwargs,
        )
        self.db.add(evidence)
        return evidence

    async def delete(self, evidence: Evidence) -> None:
        """Delete evidence"""
        await self.db.delete(evidence)


class DebateRepository:
    """Repository for Debate CRUD operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, debate_id: int) -> Optional[Debate]:
        """Get debate by ID"""
        stmt = select(Debate).where(Debate.id == debate_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_hypothesis(
        self, hypothesis_id: int, skip: int = 0, limit: int = 10
    ) -> list[Debate]:
        """Get debates for a hypothesis"""
        stmt = (
            select(Debate)
            .where(Debate.hypothesis_id == hypothesis_id)
            .order_by(Debate.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_by_hypothesis(self, hypothesis_id: int) -> Optional[Debate]:
        """Get active (running) debate for a hypothesis"""
        stmt = (
            select(Debate)
            .where(Debate.hypothesis_id == hypothesis_id)
            .where(Debate.status.in_([DebateStatus.PENDING, DebateStatus.RUNNING]))
            .order_by(Debate.started_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_hypothesis(self, hypothesis_id: int) -> int:
        """Count debates for a hypothesis"""
        stmt = select(func.count(Debate.id)).where(Debate.hypothesis_id == hypothesis_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, hypothesis_id: int, **kwargs: Any) -> Debate:
        """Create a new debate"""
        debate = Debate(
            hypothesis_id=hypothesis_id,
            started_at=datetime.utcnow(),
            **kwargs,
        )
        self.db.add(debate)
        return debate

    async def update(self, debate: Debate, **kwargs: Any) -> Debate:
        """Update a debate"""
        for key, value in kwargs.items():
            if hasattr(debate, key):
                setattr(debate, key, value)
        return debate

    async def get_recent_completed(self, project_id: int, limit: int = 10) -> list[Debate]:
        """Get recently completed debates for a project"""
        stmt = (
            select(Debate)
            .join(Hypothesis)
            .where(Hypothesis.project_id == project_id)
            .where(Debate.status == DebateStatus.COMPLETED)
            .order_by(Debate.completed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class ResearchFindingRepository:
    """Repository for ResearchFinding CRUD operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, finding_id: int) -> Optional[ResearchFinding]:
        """Get finding by ID"""
        stmt = select(ResearchFinding).where(ResearchFinding.id == finding_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_task(
        self, task_id: int, skip: int = 0, limit: int = 100
    ) -> list[ResearchFinding]:
        """Get findings for a research task"""
        stmt = (
            select(ResearchFinding)
            .where(ResearchFinding.research_task_id == task_id)
            .order_by(ResearchFinding.confidence.desc(), ResearchFinding.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unindexed_by_task(self, task_id: int) -> list[ResearchFinding]:
        """Get findings not yet indexed to KB"""
        stmt = (
            select(ResearchFinding)
            .where(ResearchFinding.research_task_id == task_id)
            .where(ResearchFinding.knowledge_entry_id.is_(None))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_task(self, task_id: int) -> int:
        """Count findings for a task"""
        stmt = select(func.count(ResearchFinding.id)).where(
            ResearchFinding.research_task_id == task_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, research_task_id: int, **kwargs: Any) -> ResearchFinding:
        """Create a new finding"""
        finding = ResearchFinding(
            research_task_id=research_task_id,
            created_at=datetime.utcnow(),
            **kwargs,
        )
        self.db.add(finding)
        return finding

    async def update(self, finding: ResearchFinding, **kwargs: Any) -> ResearchFinding:
        """Update a finding"""
        for key, value in kwargs.items():
            if hasattr(finding, key):
                setattr(finding, key, value)
        return finding

    async def delete(self, finding: ResearchFinding) -> None:
        """Delete a finding"""
        await self.db.delete(finding)
