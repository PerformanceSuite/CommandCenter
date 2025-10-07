"""Project State Resource

Provides current project state as an MCP resource.
"""

import json
from pathlib import Path
from typing import Dict, Any
import sys

# Add base server to path
base_path = Path(__file__).parent.parent.parent / 'base'
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

from utils import get_logger, get_project_root

logger = get_logger(__name__)


class ProjectStateResource:
    """Project state resource provider"""

    def __init__(self, config):
        """Initialize project state resource

        Args:
            config: ProjectManagerConfig instance
        """
        self.config = config
        self.project_root = get_project_root()
        self.coordination_dir = self.project_root / config.coordination_dir

    async def get_state(self) -> str:
        """Get current project state

        Returns:
            JSON string of project state
        """
        logger.debug("Getting project state")

        state = {
            'project': {
                'id': self.config.project_id,
                'name': self.config.project_name,
                'root': str(self.project_root)
            },
            'agents': await self._get_agents_state(),
            'workflows': await self._get_workflows_state(),
            'git': await self._get_git_state()
        }

        return json.dumps(state, indent=2)

    async def _get_agents_state(self) -> Dict[str, Any]:
        """Get agents state"""
        status_file = self.coordination_dir / 'mcp-status.json'

        if not status_file.exists():
            return {
                'total': 0,
                'active': [],
                'completed': [],
                'failed': []
            }

        with open(status_file, 'r') as f:
            status_data = json.load(f)

        agents = status_data.get('agents', {})

        return {
            'total': len(agents),
            'active': [
                name for name, info in agents.items()
                if info.get('status') in ['pending', 'in_progress']
            ],
            'completed': status_data.get('completed', []),
            'failed': status_data.get('failed', []),
            'details': agents
        }

    async def _get_workflows_state(self) -> Dict[str, Any]:
        """Get workflows state"""
        workflows_dir = self.project_root / '.commandcenter' / '.agent-coordination' / 'workflows'

        if not workflows_dir.exists():
            return {
                'total': 0,
                'active': []
            }

        workflows = []
        for workflow_file in workflows_dir.glob('*.json'):
            try:
                with open(workflow_file, 'r') as f:
                    workflow = json.load(f)
                    workflows.append({
                        'id': workflow_file.stem,
                        'type': workflow.get('type'),
                        'status': workflow.get('status')
                    })
            except Exception as e:
                logger.error(f"Error reading workflow {workflow_file}: {e}")

        return {
            'total': len(workflows),
            'active': [w for w in workflows if w.get('status') in ['created', 'running']],
            'all': workflows
        }

    async def _get_git_state(self) -> Dict[str, Any]:
        """Get git state"""
        import subprocess

        try:
            # Get current branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            # Get status
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            return {
                'branch': branch_result.stdout.strip(),
                'clean': len(status_result.stdout.strip()) == 0,
                'has_changes': len(status_result.stdout.strip()) > 0
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            return {
                'error': 'Failed to get git state'
            }
