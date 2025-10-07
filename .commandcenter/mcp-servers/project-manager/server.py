"""Project Manager MCP Server

Main orchestration server for CommandCenter.
Provides tools for workflow coordination, agent spawning, and project management.
"""

import asyncio
from pathlib import Path
import sys

# Add base server to path
base_path = Path(__file__).parent.parent / 'base'
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

from server import BaseMCPServer
from registry import ToolParameter
from utils import get_logger

from .config import ProjectManagerConfig
from .tools import WorkflowTools, AgentTools, GitTools, AnalysisTools, ProgressTools
from .resources import ProjectStateResource, WorkflowsResource

logger = get_logger(__name__)


class ProjectManagerServer(BaseMCPServer):
    """Project Manager MCP Server

    Orchestrates multi-agent workflows, manages git operations,
    and provides project analysis capabilities.
    """

    def __init__(self, config_path: str = None):
        """Initialize Project Manager server

        Args:
            config_path: Path to config.json (optional)
        """
        super().__init__('project-manager', '1.0.0', config_path)

        # Load configuration
        self.pm_config = ProjectManagerConfig(config_path)

        # Initialize tools
        self.workflow_tools = WorkflowTools(self.pm_config)
        self.agent_tools = AgentTools(self.pm_config)
        self.git_tools = GitTools(self.pm_config)
        self.analysis_tools = AnalysisTools(self.pm_config)
        self.progress_tools = ProgressTools(self.pm_config)

        # Initialize resources
        self.project_state_resource = ProjectStateResource(self.pm_config)
        self.workflows_resource = WorkflowsResource(self.pm_config)

        # Register tools
        self._register_tools()

        # Register resources
        self._register_resources()

        logger.info("Project Manager MCP server initialized")

    def _register_tools(self):
        """Register all MCP tools"""

        # 1. analyze_project
        self.tool_registry.register_tool(
            name='analyze_project',
            description='Analyze current project structure, technologies, and metrics',
            parameters=[],
            handler=self.analysis_tools.analyze_project
        )

        # 2. create_workflow
        self.tool_registry.register_tool(
            name='create_workflow',
            description='Create a new agent workflow from template',
            parameters=[
                ToolParameter(
                    name='workflow_type',
                    type='string',
                    description='Type of workflow: parallel, sequential, or phased',
                    required=True
                ),
                ToolParameter(
                    name='agents',
                    type='array',
                    description='List of agent names to include in workflow',
                    required=True
                ),
                ToolParameter(
                    name='description',
                    type='string',
                    description='Workflow description',
                    required=False,
                    default=''
                )
            ],
            handler=self.workflow_tools.create_workflow
        )

        # 3. spawn_agent
        self.tool_registry.register_tool(
            name='spawn_agent',
            description='Launch a specialized agent in a git worktree',
            parameters=[
                ToolParameter(
                    name='agent_name',
                    type='string',
                    description='Name of agent (e.g., mcp-infrastructure-agent)',
                    required=True
                ),
                ToolParameter(
                    name='branch',
                    type='string',
                    description='Git branch name for agent',
                    required=True
                ),
                ToolParameter(
                    name='task_file',
                    type='string',
                    description='Path to task definition file',
                    required=True
                ),
                ToolParameter(
                    name='dependencies',
                    type='array',
                    description='List of agent names this agent depends on',
                    required=False,
                    default=None
                )
            ],
            handler=self.agent_tools.spawn_agent
        )

        # 4. track_progress
        self.tool_registry.register_tool(
            name='track_progress',
            description='Monitor agent progress and generate status reports',
            parameters=[
                ToolParameter(
                    name='agent_name',
                    type='string',
                    description='Specific agent to track (optional, tracks all if not provided)',
                    required=False,
                    default=None
                )
            ],
            handler=self.progress_tools.track_progress
        )

        # 5. merge_results
        self.tool_registry.register_tool(
            name='merge_results',
            description='Merge an agent branch into target branch',
            parameters=[
                ToolParameter(
                    name='branch_name',
                    type='string',
                    description='Branch to merge',
                    required=True
                ),
                ToolParameter(
                    name='target_branch',
                    type='string',
                    description='Target branch (default: main)',
                    required=False,
                    default='main'
                )
            ],
            handler=self.git_tools.merge_branch
        )

        # 6. generate_command
        self.tool_registry.register_tool(
            name='generate_command',
            description='Generate CLI command for common operations',
            parameters=[
                ToolParameter(
                    name='operation',
                    type='string',
                    description='Operation type: setup_worktrees, run_tests, deploy, etc.',
                    required=True
                ),
                ToolParameter(
                    name='params',
                    type='object',
                    description='Operation-specific parameters',
                    required=False,
                    default={}
                )
            ],
            handler=self._generate_command
        )

        logger.info(f"Registered {len(self.tool_registry.tools)} tools")

    def _register_resources(self):
        """Register all MCP resources"""

        # project://state
        self.resource_registry.register_resource(
            uri='project://state',
            name='Project State',
            description='Current project state including agents, workflows, and git status',
            mime_type='application/json',
            handler=self.project_state_resource.get_state
        )

        # project://workflows
        self.resource_registry.register_resource(
            uri='project://workflows',
            name='Workflow Templates',
            description='Available workflow templates for agent coordination',
            mime_type='application/json',
            handler=self.workflows_resource.get_workflows
        )

        # project://agents (alias to state)
        self.resource_registry.register_resource(
            uri='project://agents',
            name='Active Agents',
            description='Status of all active agents',
            mime_type='application/json',
            handler=self._get_agents_resource
        )

        logger.info(f"Registered {len(self.resource_registry.resources)} resources")

    async def _generate_command(self, operation: str, params: dict = None) -> dict:
        """Generate CLI command for operation

        Args:
            operation: Operation type
            params: Operation parameters

        Returns:
            Generated command information
        """
        params = params or {}

        commands = {
            'setup_worktrees': {
                'command': 'bash scripts/setup-worktrees.sh',
                'description': 'Set up git worktrees for all agents',
                'requires': ['scripts/setup-worktrees.sh']
            },
            'run_tests': {
                'command': 'make test',
                'description': 'Run all tests (backend + frontend)',
                'requires': ['Makefile']
            },
            'start_dev': {
                'command': 'make dev',
                'description': 'Start development environment',
                'requires': ['docker-compose.yml']
            },
            'create_pr': {
                'command': f"gh pr create --title \"{params.get('title', 'Feature')}\" --body \"{params.get('body', '')}\"",
                'description': 'Create GitHub pull request',
                'requires': ['gh CLI']
            },
            'merge_pr': {
                'command': f"gh pr merge {params.get('pr_number', '')} --squash",
                'description': 'Merge pull request',
                'requires': ['gh CLI']
            },
            'check_status': {
                'command': 'cat .agent-coordination/mcp-status.json',
                'description': 'Check agent coordination status',
                'requires': ['.agent-coordination/mcp-status.json']
            }
        }

        if operation not in commands:
            return {
                'error': f"Unknown operation: {operation}",
                'available_operations': list(commands.keys())
            }

        return {
            'operation': operation,
            **commands[operation]
        }

    async def _get_agents_resource(self) -> str:
        """Get agents as resource

        Returns:
            JSON string of agent statuses
        """
        import json
        agents = await self.agent_tools.list_agents()
        return json.dumps({'agents': agents}, indent=2)


async def main():
    """Main entry point for Project Manager server"""
    server = ProjectManagerServer()
    await server.run()


if __name__ == '__main__':
    asyncio.run(main())
