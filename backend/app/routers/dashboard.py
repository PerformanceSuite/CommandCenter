"""
Dashboard and analytics endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import RepositoryService, TechnologyService, ResearchService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_repository_service(db: AsyncSession = Depends(get_db)) -> RepositoryService:
    """Dependency to get repository service instance"""
    return RepositoryService(db)


def get_technology_service(db: AsyncSession = Depends(get_db)) -> TechnologyService:
    """Dependency to get technology service instance"""
    return TechnologyService(db)


def get_research_service(db: AsyncSession = Depends(get_db)) -> ResearchService:
    """Dependency to get research service instance"""
    return ResearchService(db)


@router.get("/stats")
async def get_dashboard_stats(
    repo_service: RepositoryService = Depends(get_repository_service),
    tech_service: TechnologyService = Depends(get_technology_service),
    research_service: ResearchService = Depends(get_research_service),
) -> Dict[str, Any]:
    """Get dashboard statistics"""

    # Get stats from services
    repo_stats = await repo_service.get_statistics()
    tech_stats = await tech_service.get_statistics()
    research_stats = await research_service.get_statistics()

    # Knowledge base stats - skip to avoid 8+ second initialization delay
    # RAG service is initialized lazily only when actually needed (e.g., when querying)
    kb_stats = {"total_documents": 0, "total_chunks": 0, "status": "available"}

    return {
        "repositories": repo_stats,
        "technologies": tech_stats,
        "research_tasks": research_stats,
        "knowledge_base": kb_stats,
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    repo_service: RepositoryService = Depends(get_repository_service),
    tech_service: TechnologyService = Depends(get_technology_service),
    research_service: ResearchService = Depends(get_research_service),
) -> Dict[str, Any]:
    """Get recent activity across the platform"""

    # Get recent items from services (using their get_all methods with ordering)
    recent_repos = await repo_service.list_repositories(skip=0, limit=limit)
    recent_tech, _ = await tech_service.list_technologies(skip=0, limit=limit)
    recent_tasks = await research_service.list_research_tasks(skip=0, limit=limit)

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
