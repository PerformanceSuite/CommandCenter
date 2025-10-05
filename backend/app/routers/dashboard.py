"""
Dashboard and analytics endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Repository, Technology, ResearchTask, TechnologyStatus, TaskStatus
from app.services import RAGService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get dashboard statistics"""

    # Repository stats
    repo_count = await db.scalar(select(func.count()).select_from(Repository))

    # Technology stats
    tech_count = await db.scalar(select(func.count()).select_from(Technology))

    # Technology by status
    tech_by_status = {}
    for status in TechnologyStatus:
        count = await db.scalar(
            select(func.count())
            .select_from(Technology)
            .where(Technology.status == status)
        )
        tech_by_status[status.value] = count

    # Research task stats
    task_count = await db.scalar(select(func.count()).select_from(ResearchTask))

    # Tasks by status
    tasks_by_status = {}
    for status in TaskStatus:
        count = await db.scalar(
            select(func.count())
            .select_from(ResearchTask)
            .where(ResearchTask.status == status)
        )
        tasks_by_status[status.value] = count

    # Knowledge base stats
    try:
        rag_service = RAGService()
        kb_stats = await rag_service.get_statistics()
    except Exception as e:
        kb_stats = {"error": str(e)}

    return {
        "repositories": {
            "total": repo_count,
        },
        "technologies": {
            "total": tech_count,
            "by_status": tech_by_status,
        },
        "research_tasks": {
            "total": task_count,
            "by_status": tasks_by_status,
        },
        "knowledge_base": kb_stats,
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get recent activity across the platform"""

    # Recent repositories
    recent_repos_result = await db.execute(
        select(Repository)
        .order_by(Repository.updated_at.desc())
        .limit(limit)
    )
    recent_repos = recent_repos_result.scalars().all()

    # Recent technologies
    recent_tech_result = await db.execute(
        select(Technology)
        .order_by(Technology.updated_at.desc())
        .limit(limit)
    )
    recent_tech = recent_tech_result.scalars().all()

    # Recent research tasks
    recent_tasks_result = await db.execute(
        select(ResearchTask)
        .order_by(ResearchTask.updated_at.desc())
        .limit(limit)
    )
    recent_tasks = recent_tasks_result.scalars().all()

    return {
        "recent_repositories": [
            {
                "id": r.id,
                "full_name": r.full_name,
                "updated_at": r.updated_at,
            }
            for r in recent_repos
        ],
        "recent_technologies": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "updated_at": t.updated_at,
            }
            for t in recent_tech
        ],
        "recent_tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "updated_at": t.updated_at,
            }
            for t in recent_tasks
        ],
    }
