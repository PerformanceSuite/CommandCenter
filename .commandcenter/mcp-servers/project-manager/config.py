"""Project Manager Configuration

Configuration management for Project Manager MCP server.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add base server to path
base_path = Path(__file__).parent.parent / 'base'
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

from utils import get_logger, load_config

logger = get_logger(__name__)


class ProjectManagerConfig:
    """Configuration for Project Manager"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration

        Args:
            config_path: Path to config.json (optional)
        """
        self.config = {}
        if config_path:
            try:
                self.config = load_config(config_path)
            except Exception as e:
                logger.warning(f"Could not load configuration: {e}")
                self.config = self._get_default_config()
        else:
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'project': {
                'id': 'commandcenter',
                'name': 'CommandCenter',
                'type': 'fullstack',
                'isolation_id': 'cc-main'
            },
            'mcp_servers': {
                'project_manager': {
                    'enabled': True,
                    'transport': 'stdio',
                    'max_parallel_agents': 8
                }
            },
            'workflows': {
                'templates_dir': '.commandcenter/.agent-coordination/workflows'
            },
            'agents': {
                'worktree_base': 'worktrees',
                'coordination_dir': '.agent-coordination'
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value

        Args:
            key: Configuration key (dot notation supported, e.g., 'project.id')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value

        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    @property
    def project_id(self) -> str:
        """Get project ID"""
        return self.get('project.id', 'unknown')

    @property
    def project_name(self) -> str:
        """Get project name"""
        return self.get('project.name', 'Unknown Project')

    @property
    def max_parallel_agents(self) -> int:
        """Get max parallel agents"""
        return self.get('mcp_servers.project_manager.max_parallel_agents', 8)

    @property
    def worktree_base(self) -> str:
        """Get worktree base directory"""
        return self.get('agents.worktree_base', 'worktrees')

    @property
    def coordination_dir(self) -> str:
        """Get coordination directory"""
        return self.get('agents.coordination_dir', '.agent-coordination')
