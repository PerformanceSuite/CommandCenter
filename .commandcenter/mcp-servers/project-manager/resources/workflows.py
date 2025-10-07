"""Workflows Resource

Provides available workflow templates as an MCP resource.
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


class WorkflowsResource:
    """Workflow templates resource provider"""

    def __init__(self, config):
        """Initialize workflows resource

        Args:
            config: ProjectManagerConfig instance
        """
        self.config = config
        self.project_root = get_project_root()
        self.templates_dir = self.project_root / '.commandcenter' / '.agent-coordination' / 'workflows' / 'templates'
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    async def get_workflows(self) -> str:
        """Get available workflow templates

        Returns:
            JSON string of workflow templates
        """
        logger.debug("Getting workflow templates")

        # Built-in templates
        templates = self._get_builtin_templates()

        # Custom templates from disk
        custom_templates = await self._get_custom_templates()
        templates.extend(custom_templates)

        result = {
            'total': len(templates),
            'templates': templates
        }

        return json.dumps(result, indent=2)

    def _get_builtin_templates(self) -> List[Dict[str, Any]]:
        """Get built-in workflow templates

        Returns:
            List of built-in templates
        """
        return [
            {
                'id': 'parallel-improvement',
                'name': 'Parallel Improvement',
                'description': 'Run multiple improvement agents in parallel',
                'type': 'parallel',
                'agents': [
                    'security-agent',
                    'backend-agent',
                    'frontend-agent',
                    'testing-agent',
                    'docs-agent'
                ],
                'builtin': True
            },
            {
                'id': 'phased-development',
                'name': 'Phased Development',
                'description': 'Execute agents in phases with dependencies',
                'type': 'phased',
                'phases': [
                    {
                        'phase': 1,
                        'agents': ['mcp-infrastructure-agent', 'knowledgebeast-mcp-agent', 'api-manager-agent']
                    },
                    {
                        'phase': 2,
                        'agents': ['agentflow-coordinator-agent', 'viztrtr-mcp-agent']
                    }
                ],
                'builtin': True
            },
            {
                'id': 'sequential-feature',
                'name': 'Sequential Feature Development',
                'description': 'Build feature components in sequence',
                'type': 'sequential',
                'agents': [
                    'backend-api-agent',
                    'frontend-ui-agent',
                    'integration-test-agent',
                    'documentation-agent'
                ],
                'builtin': True
            },
            {
                'id': 'hotfix-workflow',
                'name': 'Hotfix Workflow',
                'description': 'Quick fix and test workflow',
                'type': 'sequential',
                'agents': [
                    'bugfix-agent',
                    'testing-agent'
                ],
                'builtin': True
            },
            {
                'id': 'quality-audit',
                'name': 'Quality Audit',
                'description': 'Comprehensive quality review',
                'type': 'parallel',
                'agents': [
                    'security-audit-agent',
                    'code-quality-agent',
                    'performance-agent',
                    'accessibility-agent'
                ],
                'builtin': True
            }
        ]

    async def _get_custom_templates(self) -> List[Dict[str, Any]]:
        """Get custom workflow templates from disk

        Returns:
            List of custom templates
        """
        templates = []

        if not self.templates_dir.exists():
            return templates

        for template_file in self.templates_dir.glob('*.json'):
            try:
                with open(template_file, 'r') as f:
                    template = json.load(f)
                    template['id'] = template_file.stem
                    template['builtin'] = False
                    templates.append(template)
            except Exception as e:
                logger.error(f"Error reading template {template_file}: {e}")

        return templates
