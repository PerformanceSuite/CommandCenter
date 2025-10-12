"""
API client for CommandCenter backend.

Provides a high-level interface for interacting with the CommandCenter API.
"""

import httpx
from typing import Optional, Dict, Any, List


class APIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class APIClient:
    """
    HTTP client for CommandCenter API.

    Handles authentication, error handling, and response parsing.
    """

    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 30):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (e.g., http://localhost:8000)
            token: Authentication token (optional)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        """
        Handle API response and raise errors for non-2xx status codes.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response

        Raises:
            APIError: If response status is not 2xx
        """
        try:
            response.raise_for_status()
            return response.json() if response.content else None
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", error_detail)
            except Exception:
                error_detail = e.response.text or error_detail

            raise APIError(
                f"API request failed: {error_detail}",
                status_code=e.response.status_code,
            )

    # Analysis endpoints
    def analyze_project(self, path: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Analyze a local project directory.

        Args:
            path: Path to project directory
            use_cache: Use cached results if available

        Returns:
            Analysis results dictionary
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/analysis/project",
            headers=self._get_headers(),
            json={"path": path, "use_cache": use_cache},
        )
        return self._handle_response(response)

    def analyze_github_repo(self, repo: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Analyze a GitHub repository.

        Args:
            repo: Repository in format 'owner/repo'
            use_cache: Use cached results if available

        Returns:
            Analysis results dictionary
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/analysis/github",
            headers=self._get_headers(),
            json={"repo": repo, "use_cache": use_cache},
        )
        return self._handle_response(response)

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        Get analysis statistics.

        Returns:
            Statistics dictionary
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/analysis/statistics",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # Agent orchestration endpoints
    def launch_agents(
        self, workflow: str = "full", max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Launch agent orchestration workflow.

        Args:
            workflow: Workflow type (full, analyze-only, custom)
            max_concurrent: Maximum concurrent agents

        Returns:
            Orchestration details dictionary
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/agents/launch",
            headers=self._get_headers(),
            json={"workflow": workflow, "max_concurrent": max_concurrent},
        )
        return self._handle_response(response)

    def get_orchestration_status(self, orchestration_id: str) -> Dict[str, Any]:
        """
        Get status of an orchestration.

        Args:
            orchestration_id: Orchestration ID

        Returns:
            Orchestration status dictionary
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/agents/orchestration/{orchestration_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def list_orchestrations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent orchestrations.

        Args:
            limit: Maximum number of orchestrations to return

        Returns:
            List of orchestration dictionaries
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/agents/orchestrations",
            headers=self._get_headers(),
            params={"limit": limit},
        )
        return self._handle_response(response)

    def get_agent_logs(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get logs for a specific agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of log entries
        """
        response = self.client.get(
            f"{self.base_url}/api/v1/agents/{agent_id}/logs",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def stop_orchestration(self, orchestration_id: str) -> Dict[str, Any]:
        """
        Stop a running orchestration.

        Args:
            orchestration_id: Orchestration ID

        Returns:
            Status dictionary
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/agents/orchestration/{orchestration_id}/stop",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    def retry_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Retry a failed agent.

        Args:
            agent_id: Agent ID

        Returns:
            Retry status dictionary
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/agents/{agent_id}/retry",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # Search endpoints
    def search_knowledge(
        self, query: str, filter_type: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search knowledge base using RAG.

        Args:
            query: Search query
            filter_type: Filter by type (technology, research)
            limit: Maximum number of results

        Returns:
            Search results dictionary
        """
        params = {"query": query, "limit": limit}
        if filter_type:
            params["filter_type"] = filter_type

        response = self.client.get(
            f"{self.base_url}/api/v1/knowledge/search",
            headers=self._get_headers(),
            params=params,
        )
        return self._handle_response(response)

    # Research tasks endpoints
    def create_research_tasks_from_analysis(
        self, analysis_id: str
    ) -> List[Dict[str, Any]]:
        """
        Create research tasks from analysis results.

        Args:
            analysis_id: Analysis ID

        Returns:
            List of created research tasks
        """
        response = self.client.post(
            f"{self.base_url}/api/v1/research/tasks/from-analysis/{analysis_id}",
            headers=self._get_headers(),
        )
        return self._handle_response(response)

    # Health check
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health.

        Returns:
            Health status dictionary
        """
        response = self.client.get(
            f"{self.base_url}/health",
            headers=self._get_headers(),
        )
        return self._handle_response(response)
