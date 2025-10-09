"""
GitHub integration service for repository management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from github import Github, GithubException, Repository as GithubRepo

from app.config import settings


class GitHubService:
    """Service for GitHub API interactions"""

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize GitHub service

        Args:
            access_token: GitHub personal access token (uses config default if not provided)
        """
        self.token = access_token or settings.github_token
        self.github = Github(self.token) if self.token else Github()

    async def authenticate_repo(self, owner: str, name: str) -> bool:
        """
        Test if we can authenticate with a repository

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            True if authentication successful
        """
        try:
            repo = self.github.get_repo(f"{owner}/{name}")
            # Try to access a property to verify authentication
            _ = repo.full_name
            return True
        except GithubException as e:
            if e.status == 401:
                return False
            raise

    async def list_user_repos(
        self, username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List repositories for a user

        Args:
            username: GitHub username (uses authenticated user if not provided)

        Returns:
            List of repository metadata dictionaries
        """
        try:
            if username:
                user = self.github.get_user(username)
                repos = user.get_repos()
            else:
                # Get authenticated user's repos
                repos = self.github.get_user().get_repos()

            repo_list = []
            for repo in repos:
                repo_list.append(
                    {
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
                    }
                )

            return repo_list

        except GithubException as e:
            raise Exception(f"Failed to list repositories: {e}")

    async def sync_repository(
        self, owner: str, name: str, last_known_sha: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync repository information and check for changes

        Args:
            owner: Repository owner
            name: Repository name
            last_known_sha: Last known commit SHA (to detect changes)

        Returns:
            Dictionary with sync information
        """
        try:
            repo: GithubRepo = self.github.get_repo(f"{owner}/{name}")

            # Get latest commit from default branch
            commits = repo.get_commits()
            latest_commit = commits[0] if commits.totalCount > 0 else None

            sync_info = {
                "synced": True,
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
                "last_synced_at": datetime.utcnow(),
                "changes_detected": False,
            }

            if latest_commit:
                sync_info.update(
                    {
                        "last_commit_sha": latest_commit.sha,
                        "last_commit_message": latest_commit.commit.message,
                        "last_commit_author": latest_commit.commit.author.name,
                        "last_commit_date": latest_commit.commit.author.date,
                    }
                )

                # Check if there are new commits
                if last_known_sha and latest_commit.sha != last_known_sha:
                    sync_info["changes_detected"] = True

            return sync_info

        except GithubException as e:
            raise Exception(f"Failed to sync repository: {e}")

    async def get_repository_info(self, owner: str, name: str) -> Dict[str, Any]:
        """
        Get detailed repository information

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            Repository information dictionary
        """
        try:
            repo: GithubRepo = self.github.get_repo(f"{owner}/{name}")

            return {
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
                "created_at": repo.created_at,
                "updated_at": repo.updated_at,
                "topics": repo.get_topics(),
            }

        except GithubException as e:
            raise Exception(f"Failed to get repository info: {e}")

    async def search_repositories(
        self, query: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for repositories on GitHub

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of repository metadata dictionaries
        """
        try:
            repos = self.github.search_repositories(query=query)

            repo_list = []
            for i, repo in enumerate(repos):
                if i >= max_results:
                    break

                repo_list.append(
                    {
                        "owner": repo.owner.login,
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description,
                        "url": repo.html_url,
                        "stars": repo.stargazers_count,
                        "language": repo.language,
                    }
                )

            return repo_list

        except GithubException as e:
            raise Exception(f"Failed to search repositories: {e}")
