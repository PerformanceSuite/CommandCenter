"""
Async GitHub integration service using ThreadPoolExecutor
Wraps PyGithub's synchronous calls to work with async/await
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from github import Github, GithubException, Repository as GithubRepo

from app.config import settings


class GitHubAsyncService:
    """Async service for GitHub API interactions using thread pool"""

    def __init__(
        self, access_token: Optional[str] = None, max_workers: int = 4
    ):
        """
        Initialize async GitHub service

        Args:
            access_token: GitHub personal access token (uses config default if not provided)
            max_workers: Maximum number of worker threads
        """
        self.token = access_token or settings.github_token
        self.github = Github(self.token) if self.token else Github()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def _run_in_executor(self, func, *args, **kwargs):
        """
        Run synchronous function in thread pool executor

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result
        """
        loop = asyncio.get_event_loop()
        if kwargs:
            func = partial(func, **kwargs)
        return await loop.run_in_executor(self.executor, func, *args)

    async def authenticate_repo(self, owner: str, name: str) -> bool:
        """
        Test if we can authenticate with a repository

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            True if authentication successful
        """

        def _auth():
            try:
                repo = self.github.get_repo(f"{owner}/{name}")
                _ = repo.full_name
                return True
            except GithubException as e:
                if e.status == 401:
                    return False
                raise

        return await self._run_in_executor(_auth)

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

        def _list_repos():
            try:
                if username:
                    user = self.github.get_user(username)
                    repos = user.get_repos()
                else:
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

        return await self._run_in_executor(_list_repos)

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

        def _sync():
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

        return await self._run_in_executor(_sync)

    async def get_repository_info(
        self, owner: str, name: str
    ) -> Dict[str, Any]:
        """
        Get detailed repository information

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            Repository information dictionary
        """

        def _get_info():
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

        return await self._run_in_executor(_get_info)

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

        def _search():
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

        return await self._run_in_executor(_search)

    async def get_file_content(
        self, owner: str, name: str, path: str, ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get file content from repository

        Args:
            owner: Repository owner
            name: Repository name
            path: File path
            ref: Git reference (branch, tag, commit SHA)

        Returns:
            Dictionary with file content and metadata
        """

        def _get_file():
            try:
                repo: GithubRepo = self.github.get_repo(f"{owner}/{name}")
                file_content = repo.get_contents(path, ref=ref)

                if isinstance(file_content, list):
                    raise Exception(f"Path {path} is a directory, not a file")

                return {
                    "content": file_content.decoded_content.decode("utf-8"),
                    "path": file_content.path,
                    "sha": file_content.sha,
                    "size": file_content.size,
                    "encoding": file_content.encoding,
                }

            except GithubException as e:
                raise Exception(f"Failed to get file content: {e}")

        return await self._run_in_executor(_get_file)

    def close(self):
        """Shutdown the thread pool executor"""
        self.executor.shutdown(wait=True)

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.close()
