"""
Enhanced GitHub features: PR templates, labels, actions, and settings
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.enhanced_github_service import EnhancedGitHubService
from app.services.redis_service import RedisService, get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["github-features"])


# Pydantic models for requests
class PRTemplateCreate(BaseModel):
    """Schema for creating PR template"""

    owner: str
    name: str
    template_content: str
    template_name: str = "pull_request_template.md"


class LabelCreate(BaseModel):
    """Schema for creating a label"""

    owner: str
    name: str
    label_name: str
    color: str = Field(default="ededed", pattern="^[0-9a-fA-F]{6}$")
    description: Optional[str] = None


class LabelUpdate(BaseModel):
    """Schema for updating a label"""

    owner: str
    name: str
    label_name: str
    new_name: Optional[str] = None
    color: Optional[str] = Field(default=None, pattern="^[0-9a-fA-F]{6}$")
    description: Optional[str] = None


class RepositorySettingsUpdate(BaseModel):
    """Schema for updating repository settings"""

    description: Optional[str] = None
    homepage: Optional[str] = None
    has_issues: Optional[bool] = None
    has_wiki: Optional[bool] = None
    has_pages: Optional[bool] = None
    default_branch: Optional[str] = None


def get_github_service(
    redis: RedisService = Depends(get_redis),
) -> EnhancedGitHubService:
    """Dependency to get enhanced GitHub service"""
    return EnhancedGitHubService(redis_service=redis)


@router.get("/{owner}/{repo}/info")
async def get_repository_info(
    owner: str,
    repo: str,
    use_cache: bool = True,
    github_service: EnhancedGitHubService = Depends(get_github_service),
) -> Dict[str, Any]:
    """
    Get detailed repository information with caching

    Args:
        owner: Repository owner
        repo: Repository name
        use_cache: Whether to use cache
        github_service: GitHub service instance

    Returns:
        Repository information
    """
    try:
        return await github_service.get_repository_info(owner, repo, use_cache=use_cache)
    except Exception as e:
        logger.error(f"Failed to get repository info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{owner}/{repo}/pulls")
async def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    use_cache: bool = True,
    github_service: EnhancedGitHubService = Depends(get_github_service),
) -> List[Dict[str, Any]]:
    """
    List pull requests with caching

    Args:
        owner: Repository owner
        repo: Repository name
        state: PR state (open, closed, all)
        use_cache: Whether to use cache
        github_service: GitHub service instance

    Returns:
        List of pull requests
    """
    try:
        return await github_service.list_pull_requests(
            owner, repo, state=state, use_cache=use_cache
        )
    except Exception as e:
        logger.error(f"Failed to list pull requests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{owner}/{repo}/issues")
async def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    labels: Optional[str] = None,
    github_service: EnhancedGitHubService = Depends(get_github_service),
) -> List[Dict[str, Any]]:
    """
    List repository issues

    Args:
        owner: Repository owner
        repo: Repository name
        state: Issue state (open, closed, all)
        labels: Comma-separated list of labels
        github_service: GitHub service instance

    Returns:
        List of issues
    """
    try:
        label_list = labels.split(",") if labels else None
        return await github_service.list_issues(owner, repo, state=state, labels=label_list)
    except Exception as e:
        logger.error(f"Failed to list issues: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{owner}/{repo}/labels", status_code=status.HTTP_201_CREATED)
async def create_label(
    owner: str,
    repo: str,
    label_data: LabelCreate,
    github_service: EnhancedGitHubService = Depends(get_github_service),
) -> Dict[str, Any]:
    """
    Create a new label

    Args:
        owner: Repository owner
        repo: Repository name
        label_data: Label data
        github_service: GitHub service instance

    Returns:
        Created label information
    """
    try:
        return await github_service.manage_labels(
            owner=owner,
            name=repo,
            action="create",
            label_name=label_data.label_name,
            color=label_data.color,
            description=label_data.description,
        )
    except Exception as e:
        logger.error(f"Failed to create label: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{owner}/{repo}/labels/{label_name}")
async def update_label(
    owner: str,
    repo: str,
    label_name: str,
    label_data: LabelUpdate,
    github_service: EnhancedGitHubService = Depends(get_github_service),
) -> Dict[str, Any]:
    """
    Update an existing label

    Args:
        owner: Repository owner
        repo: Repository name
        label_name: Label name to update
        label_data: Updated label data
        github_service: GitHub service instance

    Returns:
        Updated label information
    """
    try:
        return await github_service.manage_labels(
            owner=owner,
            name=repo,
            action="update",
            label_name=label_name,
            color=label_data.color,
            description=label_data.description,
        )
    except Exception as e:
        logger.error(f"Failed to update label: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{owner}/{repo}/labels/{label_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    owner: str,
    repo: str,
    label_name: str,
    github_service: EnhancedGitHubService = Depends(get_github_service),
) -> None:
    """
    Delete a label

    Args:
        owner: Repository owner
        repo: Repository name
        label_name: Label name to delete
        github_service: GitHub service instance
    """
    try:
        await github_service.manage_labels(
            owner=owner, name=repo, action="delete", label_name=label_name
        )
    except Exception as e:
        logger.error(f"Failed to delete label: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{owner}/{repo}/workflows")
async def list_workflows(
    owner: str,
    repo: str,
    github_service: EnhancedGitHubService = Depends(get_github_service),
) -> List[Dict[str, Any]]:
    """
    List GitHub Actions workflows

    Args:
        owner: Repository owner
        repo: Repository name
        github_service: GitHub service instance

    Returns:
        List of workflows
    """
    try:
        return await github_service.list_workflows(owner, repo)
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{owner}/{repo}/settings")
async def update_repository_settings(
    owner: str,
    repo: str,
    settings: RepositorySettingsUpdate,
    github_service: EnhancedGitHubService = Depends(get_github_service),
) -> Dict[str, Any]:
    """
    Update repository settings

    Args:
        owner: Repository owner
        repo: Repository name
        settings: Settings to update
        github_service: GitHub service instance

    Returns:
        Updated settings
    """
    try:
        settings_dict = settings.model_dump(exclude_unset=True)
        return await github_service.update_repository_settings(owner, repo, settings_dict)
    except Exception as e:
        logger.error(f"Failed to update repository settings: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{owner}/{repo}/cache/invalidate", status_code=status.HTTP_200_OK)
async def invalidate_cache(
    owner: str,
    repo: str,
    github_service: EnhancedGitHubService = Depends(get_github_service),
) -> Dict[str, str]:
    """
    Invalidate all cache entries for a repository

    Args:
        owner: Repository owner
        repo: Repository name
        github_service: GitHub service instance

    Returns:
        Success message
    """
    try:
        await github_service.invalidate_cache(owner, repo)
        return {"status": "success", "message": f"Cache invalidated for {owner}/{repo}"}
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
