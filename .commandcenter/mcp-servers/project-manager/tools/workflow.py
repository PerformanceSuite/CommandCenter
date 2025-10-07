"""Workflow Tools

Tools for creating and managing agent workflows.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add base server to path
base_path = Path(__file__).parent.parent.parent / 'base'
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

from utils import get_logger, get_project_root

logger = get_logger(__name__)


class WorkflowTools:
    """Workflow management tools"""

    def __init__(self, config):
        """Initialize workflow tools

        Args:
            config: ProjectManagerConfig instance
        """
        self.config = config
        self.project_root = get_project_root()
        self.workflows_dir = self.project_root / '.commandcenter' / '.agent-coordination' / 'workflows'
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    async def create_workflow(self, workflow_type: str, agents: List[str], description: str = "") -> Dict[str, Any]:
        """Create a new agent workflow

        Args:
            workflow_type: Type of workflow (parallel, sequential, phased)
            agents: List of agent names to include
            description: Workflow description

        Returns:
            Created workflow definition
        """
        logger.info(f"Creating workflow: {workflow_type} with {len(agents)} agents")

        workflow = {
            'type': workflow_type,
            'description': description,
            'agents': agents,
            'created_at': self._get_timestamp(),
            'status': 'created'
        }

        # Validate workflow type
        valid_types = ['parallel', 'sequential', 'phased']
        if workflow_type not in valid_types:
            raise ValueError(f"Invalid workflow type. Must be one of: {valid_types}")

        # Create workflow file
        workflow_id = f"{workflow_type}_{self._get_timestamp()}"
        workflow_path = self.workflows_dir / f"{workflow_id}.json"

        with open(workflow_path, 'w') as f:
            json.dump(workflow, f, indent=2)

        logger.info(f"Created workflow: {workflow_id}")

        return {
            'workflow_id': workflow_id,
            'workflow': workflow,
            'path': str(workflow_path)
        }

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows

        Returns:
            List of workflow definitions
        """
        workflows = []

        # Read all workflow files
        for workflow_file in self.workflows_dir.glob('*.json'):
            try:
                with open(workflow_file, 'r') as f:
                    workflow = json.load(f)
                    workflows.append({
                        'id': workflow_file.stem,
                        'workflow': workflow
                    })
            except Exception as e:
                logger.error(f"Error reading workflow {workflow_file}: {e}")

        return workflows

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get specific workflow by ID

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow definition

        Raises:
            ValueError: If workflow not found
        """
        workflow_path = self.workflows_dir / f"{workflow_id}.json"

        if not workflow_path.exists():
            raise ValueError(f"Workflow not found: {workflow_id}")

        with open(workflow_path, 'r') as f:
            workflow = json.load(f)

        return {
            'workflow_id': workflow_id,
            'workflow': workflow,
            'path': str(workflow_path)
        }

    async def update_workflow_status(self, workflow_id: str, status: str) -> Dict[str, Any]:
        """Update workflow status

        Args:
            workflow_id: Workflow ID
            status: New status (created, running, completed, failed)

        Returns:
            Updated workflow
        """
        workflow_path = self.workflows_dir / f"{workflow_id}.json"

        if not workflow_path.exists():
            raise ValueError(f"Workflow not found: {workflow_id}")

        with open(workflow_path, 'r') as f:
            workflow = json.load(f)

        workflow['status'] = status
        workflow['updated_at'] = self._get_timestamp()

        with open(workflow_path, 'w') as f:
            json.dump(workflow, f, indent=2)

        return {
            'workflow_id': workflow_id,
            'workflow': workflow
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
