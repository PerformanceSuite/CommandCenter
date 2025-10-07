"""Agent Tools

Tools for spawning and managing specialized agents in worktrees.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# Add base server to path
base_path = Path(__file__).parent.parent.parent / 'base'
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

from utils import get_logger, get_project_root

logger = get_logger(__name__)


class AgentTools:
    """Agent spawning and management tools"""

    def __init__(self, config):
        """Initialize agent tools

        Args:
            config: ProjectManagerConfig instance
        """
        self.config = config
        self.project_root = get_project_root()
        self.worktrees_dir = self.project_root / config.worktree_base
        self.coordination_dir = self.project_root / config.coordination_dir

    async def spawn_agent(
        self,
        agent_name: str,
        branch: str,
        task_file: str,
        dependencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Spawn a specialized agent in a git worktree

        Args:
            agent_name: Name of agent (e.g., 'mcp-infrastructure-agent')
            branch: Git branch name for agent
            task_file: Path to task definition file
            dependencies: List of agent names this agent depends on

        Returns:
            Agent spawn information
        """
        logger.info(f"Spawning agent: {agent_name} on branch {branch}")

        # Validate worktree doesn't already exist
        worktree_path = self.worktrees_dir / agent_name
        if worktree_path.exists():
            raise ValueError(f"Worktree already exists: {worktree_path}")

        # Create git worktree
        try:
            result = subprocess.run(
                ['git', 'worktree', 'add', str(worktree_path), '-b', branch],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Created worktree: {worktree_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree: {e.stderr}")
            raise ValueError(f"Failed to create worktree: {e.stderr}")

        # Update agent status
        status = await self._update_agent_status(
            agent_name,
            {
                'status': 'pending',
                'branch': branch,
                'worktree': str(worktree_path.relative_to(self.project_root)),
                'task_file': task_file,
                'dependencies': dependencies or [],
                'progress': 0.0,
                'current_task': None,
                'tests_passing': None,
                'review_score': None,
                'pr_url': None
            }
        )

        return {
            'agent_name': agent_name,
            'worktree': str(worktree_path),
            'branch': branch,
            'status': status
        }

    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all active agents

        Returns:
            List of agent statuses
        """
        status_file = self.coordination_dir / 'mcp-status.json'

        if not status_file.exists():
            return []

        with open(status_file, 'r') as f:
            status_data = json.load(f)

        agents = []
        for agent_name, agent_info in status_data.get('agents', {}).items():
            agents.append({
                'name': agent_name,
                **agent_info
            })

        return agents

    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status of specific agent

        Args:
            agent_name: Agent name

        Returns:
            Agent status information

        Raises:
            ValueError: If agent not found
        """
        status_file = self.coordination_dir / 'mcp-status.json'

        if not status_file.exists():
            raise ValueError(f"Status file not found: {status_file}")

        with open(status_file, 'r') as f:
            status_data = json.load(f)

        agent_info = status_data.get('agents', {}).get(agent_name)
        if not agent_info:
            raise ValueError(f"Agent not found: {agent_name}")

        return {
            'name': agent_name,
            **agent_info
        }

    async def update_agent_progress(
        self,
        agent_name: str,
        progress: float,
        current_task: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update agent progress

        Args:
            agent_name: Agent name
            progress: Progress percentage (0.0 to 1.0)
            current_task: Optional current task description

        Returns:
            Updated agent status
        """
        updates = {'progress': progress}
        if current_task:
            updates['current_task'] = current_task

        return await self._update_agent_status(agent_name, updates)

    async def terminate_agent(self, agent_name: str) -> Dict[str, Any]:
        """Terminate an agent and remove its worktree

        Args:
            agent_name: Agent name

        Returns:
            Termination result
        """
        logger.info(f"Terminating agent: {agent_name}")

        worktree_path = self.worktrees_dir / agent_name

        if not worktree_path.exists():
            raise ValueError(f"Worktree not found: {worktree_path}")

        # Remove worktree
        try:
            result = subprocess.run(
                ['git', 'worktree', 'remove', str(worktree_path), '--force'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Removed worktree: {worktree_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to remove worktree: {e.stderr}")
            raise ValueError(f"Failed to remove worktree: {e.stderr}")

        # Update status to terminated
        await self._update_agent_status(agent_name, {'status': 'terminated'})

        return {
            'agent_name': agent_name,
            'status': 'terminated',
            'worktree_removed': True
        }

    async def _update_agent_status(self, agent_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent status in mcp-status.json

        Args:
            agent_name: Agent name
            updates: Status updates to apply

        Returns:
            Updated agent status
        """
        status_file = self.coordination_dir / 'mcp-status.json'
        status_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing status
        if status_file.exists():
            with open(status_file, 'r') as f:
                status_data = json.load(f)
        else:
            status_data = {'agents': {}, 'completed': [], 'failed': [], 'blocked': []}

        # Update agent status
        if agent_name not in status_data['agents']:
            status_data['agents'][agent_name] = {}

        status_data['agents'][agent_name].update(updates)

        # Write back
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

        return status_data['agents'][agent_name]
