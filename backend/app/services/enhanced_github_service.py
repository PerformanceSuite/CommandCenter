"""
Enhanced GitHub service with rate limiting, caching, and advanced features
"""

from typing import Optional, List, Dict, Any
import logging
from github import Github, GithubException, Repository as GithubRepo

from app.config import settings
from app.services.redis_service import RedisService
from app.services.rate_limit_service import with_rate_limit_retry
from app.services.metrics_service import track_github_api_call, metrics_service

logger = logging.getLogger(__name__)


class EnhancedGitHubService:
    """Enhanced GitHub service with caching and rate limiting"""

    def __init__(
        self,
        access_token: Optional[str] = None,
        redis_service: Optional[RedisService] = None,
    ):
        """
        Initialize enhanced GitHub service

        Args:
            access_token: GitHub personal access token
            redis_service: Redis service for caching
        """
        self.token = access_token or settings.github_token
        self.github = Github(self.token) if self.token else Github()
        self.redis = redis_service
        self.cache_ttl = 300  # 5 minutes default cache TTL

    @track_github_api_call("get_repository", "GET")
    @with_rate_limit_retry(max_attempts=3)
    async def get_repository_info(
        self, owner: str, name: str, use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get repository information with caching

        Args:
            owner: Repository owner
            name: Repository name
            use_cache: Whether to use cache

        Returns:
            Repository information dictionary
        """
        cache_key = f"github:repo:{owner}:{name}"

        # Try cache first
        if use_cache and self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                metrics_service.record_cache_hit("github")
                logger.info(f"Cache hit for repository {owner}/{name}")
                return cached
            metrics_service.record_cache_miss("github")

        try:
            repo: GithubRepo = self.github.get_repo(f"{owner}/{name}")

            repo_info = {
                "owner": repo.owner.login,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "clone_url": repo.clone_url,
                "default_branch": repo.default_branch,
                "is_private": repo.private,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language,
                "github_id": repo.id,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "topics": repo.get_topics(),
                "has_issues": repo.has_issues,
                "has_wiki": repo.has_wiki,
                "has_pages": repo.has_pages,
                "open_issues_count": repo.open_issues_count,
            }

            # Cache the result
            if self.redis:
                await self.redis.set(cache_key, repo_info, ttl=self.cache_ttl)

            return repo_info

        except GithubException as e:
            logger.error(f"Failed to get repository info for {owner}/{name}: {e}")
            raise Exception(f"Failed to get repository info: {e}")

    @track_github_api_call("list_pull_requests", "GET")
    @with_rate_limit_retry(max_attempts=3)
    async def list_pull_requests(
        self, owner: str, name: str, state: str = "open", use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List pull requests with caching

        Args:
            owner: Repository owner
            name: Repository name
            state: PR state (open, closed, all)
            use_cache: Whether to use cache

        Returns:
            List of pull request dictionaries
        """
        cache_key = f"github:prs:{owner}:{name}:{state}"

        # Try cache first (shorter TTL for PRs as they change frequently)
        if use_cache and self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                metrics_service.record_cache_hit("github")
                return cached
            metrics_service.record_cache_miss("github")

        try:
            repo: GithubRepo = self.github.get_repo(f"{owner}/{name}")
            pulls = repo.get_pulls(state=state)

            pr_list = []
            for pr in pulls:
                pr_list.append(
                    {
                        "number": pr.number,
                        "title": pr.title,
                        "state": pr.state,
                        "user": pr.user.login if pr.user else None,
                        "created_at": (
                            pr.created_at.isoformat() if pr.created_at else None
                        ),
                        "updated_at": (
                            pr.updated_at.isoformat() if pr.updated_at else None
                        ),
                        "merged": pr.merged,
                        "mergeable": pr.mergeable,
                        "head": pr.head.ref if pr.head else None,
                        "base": pr.base.ref if pr.base else None,
                        "html_url": pr.html_url,
                    }
                )

            # Cache with shorter TTL
            if self.redis:
                await self.redis.set(cache_key, pr_list, ttl=60)

            return pr_list

        except GithubException as e:
            logger.error(f"Failed to list pull requests for {owner}/{name}: {e}")
            raise Exception(f"Failed to list pull requests: {e}")

    @track_github_api_call("list_issues", "GET")
    @with_rate_limit_retry(max_attempts=3)
    async def list_issues(
        self,
        owner: str,
        name: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List repository issues

        Args:
            owner: Repository owner
            name: Repository name
            state: Issue state (open, closed, all)
            labels: Filter by labels

        Returns:
            List of issue dictionaries
        """
        try:
            repo: GithubRepo = self.github.get_repo(f"{owner}/{name}")
            issues = repo.get_issues(state=state, labels=labels or [])

            issue_list = []
            for issue in issues:
                # Skip pull requests (they appear in issues API)
                if issue.pull_request:
                    continue

                issue_list.append(
                    {
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "user": issue.user.login if issue.user else None,
                        "labels": [label.name for label in issue.labels],
                        "created_at": (
                            issue.created_at.isoformat() if issue.created_at else None
                        ),
                        "updated_at": (
                            issue.updated_at.isoformat() if issue.updated_at else None
                        ),
                        "closed_at": (
                            issue.closed_at.isoformat() if issue.closed_at else None
                        ),
                        "html_url": issue.html_url,
                        "comments": issue.comments,
                    }
                )

            return issue_list

        except GithubException as e:
            logger.error(f"Failed to list issues for {owner}/{name}: {e}")
            raise Exception(f"Failed to list issues: {e}")

    @track_github_api_call("manage_labels", "POST")
    @with_rate_limit_retry(max_attempts=3)
    async def manage_labels(
        self,
        owner: str,
        name: str,
        action: str,
        label_name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Manage repository labels

        Args:
            owner: Repository owner
            name: Repository name
            action: Action to perform (create, update, delete)
            label_name: Label name
            color: Label color (hex without #)
            description: Label description

        Returns:
            Result dictionary
        """
        try:
            repo: GithubRepo = self.github.get_repo(f"{owner}/{name}")

            if action == "create":
                label = repo.create_label(
                    name=label_name,
                    color=color or "ededed",
                    description=description or "",
                )
                return {
                    "action": "created",
                    "label": {
                        "name": label.name,
                        "color": label.color,
                        "description": label.description,
                    },
                }

            elif action == "update":
                label = repo.get_label(label_name)
                label.edit(
                    name=label_name,
                    color=color or label.color,
                    description=description or label.description,
                )
                return {
                    "action": "updated",
                    "label": {
                        "name": label.name,
                        "color": label.color,
                        "description": label.description,
                    },
                }

            elif action == "delete":
                label = repo.get_label(label_name)
                label.delete()
                return {"action": "deleted", "label": label_name}

            else:
                raise ValueError(f"Invalid action: {action}")

        except GithubException as e:
            logger.error(f"Failed to manage label {label_name} for {owner}/{name}: {e}")
            raise Exception(f"Failed to manage label: {e}")

    @track_github_api_call("get_actions_workflows", "GET")
    @with_rate_limit_retry(max_attempts=3)
    async def list_workflows(self, owner: str, name: str) -> List[Dict[str, Any]]:
        """
        List GitHub Actions workflows

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            List of workflow dictionaries
        """
        try:
            repo: GithubRepo = self.github.get_repo(f"{owner}/{name}")
            workflows = repo.get_workflows()

            workflow_list = []
            for workflow in workflows:
                workflow_list.append(
                    {
                        "id": workflow.id,
                        "name": workflow.name,
                        "path": workflow.path,
                        "state": workflow.state,
                        "created_at": (
                            workflow.created_at.isoformat()
                            if workflow.created_at
                            else None
                        ),
                        "updated_at": (
                            workflow.updated_at.isoformat()
                            if workflow.updated_at
                            else None
                        ),
                        "url": workflow.html_url,
                        "badge_url": workflow.badge_url,
                    }
                )

            return workflow_list

        except GithubException as e:
            logger.error(f"Failed to list workflows for {owner}/{name}: {e}")
            raise Exception(f"Failed to list workflows: {e}")

    @track_github_api_call("update_repository_settings", "PATCH")
    @with_rate_limit_retry(max_attempts=3)
    async def update_repository_settings(
        self, owner: str, name: str, settings_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update repository settings

        Args:
            owner: Repository owner
            name: Repository name
            settings_update: Dictionary of settings to update

        Returns:
            Updated settings dictionary
        """
        try:
            repo: GithubRepo = self.github.get_repo(f"{owner}/{name}")

            # Update allowed settings
            if "description" in settings_update:
                repo.edit(description=settings_update["description"])

            if "homepage" in settings_update:
                repo.edit(homepage=settings_update["homepage"])

            if "has_issues" in settings_update:
                repo.edit(has_issues=settings_update["has_issues"])

            if "has_wiki" in settings_update:
                repo.edit(has_wiki=settings_update["has_wiki"])

            if "has_pages" in settings_update:
                repo.edit(has_pages=settings_update["has_pages"])

            if "default_branch" in settings_update:
                repo.edit(default_branch=settings_update["default_branch"])

            # Invalidate cache
            if self.redis:
                cache_key = f"github:repo:{owner}:{name}"
                await self.redis.delete(cache_key)

            return {"updated": True, "settings": settings_update}

        except GithubException as e:
            logger.error(f"Failed to update settings for {owner}/{name}: {e}")
            raise Exception(f"Failed to update repository settings: {e}")

    async def invalidate_cache(self, owner: str, name: str):
        """
        Invalidate all cache entries for a repository

        Args:
            owner: Repository owner
            name: Repository name
        """
        if self.redis:
            pattern = f"github:*:{owner}:{name}*"
            deleted = await self.redis.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted} cache entries for {owner}/{name}")
