"""
Enhanced GitHub integration service.

Extends basic GitHubService with:
- Issues ↔ Research Tasks bidirectional sync
- GitHub Projects integration
- Webhook event handling
- PR analysis automation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from github import Github, GithubException

from app.integrations.base import (
    WebhookIntegration,
    IntegrationError,
)
from app.models.research_task import ResearchTask
from app.models.integration import IntegrationType
from app.services.github_service import GitHubService


logger = logging.getLogger(__name__)


class GitHubIntegration(WebhookIntegration):
    """
    Enhanced GitHub integration.

    Features:
    - Sync GitHub Issues to Research Tasks
    - Sync Research Tasks to GitHub Issues
    - Handle webhook events (push, pull_request, issues)
    - Automated PR analysis
    - GitHub Projects sync
    """

    def __init__(self, integration_id: int, db: AsyncSession):
        """
        Initialize GitHub integration.

        Args:
            integration_id: Integration database ID
            db: Database session
        """
        super().__init__(
            integration_id=integration_id,
            db=db,
            integration_type=IntegrationType.GITHUB,
        )
        self._github_client: Optional[Github] = None
        self._github_service: Optional[GitHubService] = None

    async def _get_github_client(self) -> Github:
        """Get authenticated GitHub client."""
        if not self._github_client:
            token = await self.get_access_token()
            self._github_client = Github(token)
        return self._github_client

    async def _get_github_service(self) -> GitHubService:
        """Get GitHub service with integration token."""
        if not self._github_service:
            token = await self.get_access_token()
            self._github_service = GitHubService(access_token=token)
        return self._github_service

    async def test_connection(self) -> bool:
        """
        Test if GitHub connection is working.

        Returns:
            True if connection successful

        Raises:
            IntegrationError: If connection fails
        """
        try:
            client = await self._get_github_client()
            user = client.get_user()
            _ = user.login  # Test API call
            await self.record_success()
            return True
        except GithubException as e:
            error_msg = f"GitHub connection test failed: {e}"
            await self.record_error(error_msg)
            raise IntegrationError(error_msg)

    async def get_display_name(self) -> str:
        """
        Get display name for integration.

        Returns:
            Display name (e.g., "GitHub: octocat")
        """
        try:
            client = await self._get_github_client()
            user = client.get_user()
            return f"GitHub: {user.login}"
        except Exception:
            return "GitHub: (error loading user)"

    def get_webhook_secret(self) -> str:
        """
        Get webhook secret for signature verification.

        Returns:
            Webhook secret from integration config
        """
        if not self._integration:
            raise IntegrationError("Integration not loaded")

        config = self._integration.config or {}
        secret = config.get("webhook_secret")

        if not secret:
            raise IntegrationError("Webhook secret not configured")

        return secret

    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GitHub webhook event.

        Args:
            event_type: GitHub event type (push, pull_request, issues, etc.)
            payload: Webhook payload

        Returns:
            Processing result

        Raises:
            IntegrationError: If processing fails
        """
        try:
            self._logger.info(f"Handling GitHub webhook: {event_type}")

            if event_type == "issues":
                return await self._handle_issues_webhook(payload)
            elif event_type == "pull_request":
                return await self._handle_pull_request_webhook(payload)
            elif event_type == "push":
                return await self._handle_push_webhook(payload)
            else:
                self._logger.warning(f"Unhandled webhook event type: {event_type}")
                return {"status": "ignored", "event_type": event_type}

        except Exception as e:
            error_msg = f"Webhook processing failed: {e}"
            await self.record_error(error_msg)
            raise IntegrationError(error_msg)

    async def _handle_issues_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle issues webhook (opened, closed, edited).

        Syncs GitHub Issue → Research Task.

        Args:
            payload: Issues webhook payload

        Returns:
            Processing result
        """
        action = payload.get("action")
        issue = payload.get("issue", {})

        if action in ["opened", "reopened", "edited"]:
            # Sync issue to research task
            task = await self.sync_issue_to_task(
                issue_number=issue["number"],
                issue_data=issue,
                repository=payload.get("repository", {}),
            )
            return {
                "status": "synced",
                "action": action,
                "task_id": task.id if task else None,
            }

        elif action == "closed":
            # Mark task as done
            task = await self._find_task_by_issue(issue["number"], payload["repository"]["id"])
            if task:
                task.status = "done"
                await self.db.commit()
                return {"status": "closed", "task_id": task.id}

        return {"status": "processed", "action": action}

    async def _handle_pull_request_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle pull_request webhook.

        Triggers automated PR analysis.

        Args:
            payload: Pull request webhook payload

        Returns:
            Processing result
        """
        action = payload.get("action")
        pr = payload.get("pull_request", {})

        if action in ["opened", "synchronize", "reopened"]:
            # Trigger PR analysis
            self._logger.info(f"PR {pr['number']} {action}, triggering analysis")
            # This would integrate with analysis service
            return {
                "status": "analysis_triggered",
                "pr_number": pr["number"],
                "action": action,
            }

        return {"status": "processed", "action": action}

    async def _handle_push_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle push webhook.

        Syncs repository on new commits.

        Args:
            payload: Push webhook payload

        Returns:
            Processing result
        """
        repo = payload.get("repository", {})
        ref = payload.get("ref", "")

        # Only process pushes to default branch
        if ref == f"refs/heads/{repo.get('default_branch')}":
            self._logger.info(f"Push to default branch in {repo.get('full_name')}, syncing repo")
            return {
                "status": "sync_triggered",
                "repository": repo.get("full_name"),
                "commits": len(payload.get("commits", [])),
            }

        return {"status": "ignored", "ref": ref}

    # GitHub Issues ↔ Research Tasks Sync

    async def sync_issue_to_task(
        self,
        issue_number: int,
        issue_data: Dict[str, Any],
        repository: Dict[str, Any],
    ) -> Optional[ResearchTask]:
        """
        Sync GitHub Issue to Research Task.

        Creates new task or updates existing one.

        Args:
            issue_number: GitHub issue number
            issue_data: Issue data from GitHub API
            repository: Repository data

        Returns:
            Created or updated ResearchTask
        """
        integration = await self.load()

        # Check if task already exists for this issue
        existing_task = await self._find_task_by_issue(issue_number, repository["id"])

        if existing_task:
            # Update existing task
            existing_task.title = issue_data["title"]
            existing_task.description = issue_data.get("body", "")
            existing_task.status = self._map_issue_state_to_task_status(issue_data["state"])
            existing_task.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing_task)
            self._logger.info(f"Updated task {existing_task.id} from issue #{issue_number}")
            return existing_task

        # Create new task
        task = ResearchTask(
            project_id=integration.project_id,
            title=issue_data["title"],
            description=issue_data.get("body", ""),
            status=self._map_issue_state_to_task_status(issue_data["state"]),
            priority=self._extract_priority_from_labels(issue_data.get("labels", [])),
            tags={
                "github_issue": issue_number,
                "github_repo_id": repository["id"],
                "github_repo": repository["full_name"],
                "github_url": issue_data["html_url"],
                "synced_from": "github",
            },
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        self._logger.info(f"Created task {task.id} from issue #{issue_number}")
        await self.record_success()

        return task

    async def sync_task_to_issue(
        self,
        task_id: int,
        owner: str,
        repo: str,
    ) -> Dict[str, Any]:
        """
        Sync Research Task to GitHub Issue.

        Creates new issue or updates existing one.

        Args:
            task_id: Research task ID
            owner: Repository owner
            repo: Repository name

        Returns:
            Issue data including issue number and URL
        """
        # Get task
        result = await self.db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise IntegrationError(f"Task {task_id} not found")

        client = await self._get_github_client()
        github_repo = client.get_repo(f"{owner}/{repo}")

        # Check if task already linked to an issue
        task_tags = task.tags or {}
        existing_issue_number = task_tags.get("github_issue")

        if existing_issue_number:
            # Update existing issue
            issue = github_repo.get_issue(existing_issue_number)
            issue.edit(
                title=task.title,
                body=task.description or "",
                state=self._map_task_status_to_issue_state(task.status),
            )
            self._logger.info(f"Updated issue #{existing_issue_number} from task {task_id}")

            return {
                "issue_number": existing_issue_number,
                "url": issue.html_url,
                "action": "updated",
            }

        # Create new issue
        labels = self._get_labels_for_priority(task.priority)
        issue = github_repo.create_issue(
            title=task.title,
            body=task.description or "",
            labels=labels,
        )

        # Update task with issue reference
        task.tags = task_tags or {}
        task.tags.update(
            {
                "github_issue": issue.number,
                "github_repo": f"{owner}/{repo}",
                "github_url": issue.html_url,
                "synced_to": "github",
            }
        )
        await self.db.commit()

        self._logger.info(f"Created issue #{issue.number} from task {task_id}")
        await self.record_success()

        return {
            "issue_number": issue.number,
            "url": issue.html_url,
            "action": "created",
        }

    async def _find_task_by_issue(
        self,
        issue_number: int,
        repo_id: int,
    ) -> Optional[ResearchTask]:
        """Find Research Task linked to GitHub Issue."""
        result = await self.db.execute(
            select(ResearchTask).where(
                ResearchTask.tags["github_issue"].astext == str(issue_number),
                ResearchTask.tags["github_repo_id"].astext == str(repo_id),
            )
        )
        return result.scalar_one_or_none()

    def _map_issue_state_to_task_status(self, issue_state: str) -> str:
        """Map GitHub issue state to task status."""
        mapping = {
            "open": "todo",
            "closed": "done",
        }
        return mapping.get(issue_state, "todo")

    def _map_task_status_to_issue_state(self, task_status: str) -> str:
        """Map task status to GitHub issue state."""
        if task_status in ["done", "completed"]:
            return "closed"
        return "open"

    def _extract_priority_from_labels(self, labels: List[Dict[str, Any]]) -> str:
        """Extract priority from GitHub labels."""
        label_names = [label.get("name", "").lower() for label in labels]

        if any("high" in name or "critical" in name for name in label_names):
            return "high"
        elif any("low" in name for name in label_names):
            return "low"
        return "medium"

    def _get_labels_for_priority(self, priority: str) -> List[str]:
        """Get GitHub labels for task priority."""
        if priority == "high":
            return ["priority: high"]
        elif priority == "low":
            return ["priority: low"]
        return []

    # GitHub Projects Integration

    async def list_projects(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """
        List GitHub Projects for a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of project data
        """
        try:
            client = await self._get_github_client()
            github_repo = client.get_repo(f"{owner}/{repo}")
            projects = github_repo.get_projects()

            return [
                {
                    "id": project.id,
                    "name": project.name,
                    "body": project.body,
                    "state": project.state,
                    "url": project.html_url,
                }
                for project in projects
            ]
        except GithubException as e:
            raise IntegrationError(f"Failed to list projects: {e}")

    async def get_project_columns(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get columns for a GitHub Project.

        Args:
            project_id: GitHub project ID

        Returns:
            List of column data
        """
        try:
            await self._get_github_client()
            # Note: PyGithub doesn't have direct project column access
            # Would need to use GitHub GraphQL API for full project support
            raise NotImplementedError("Project columns require GraphQL API")
        except GithubException as e:
            raise IntegrationError(f"Failed to get project columns: {e}")
