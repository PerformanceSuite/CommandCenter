"""Analysis Tools

Tools for project structure analysis and insights.
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


class AnalysisTools:
    """Project analysis tools"""

    def __init__(self, config):
        """Initialize analysis tools

        Args:
            config: ProjectManagerConfig instance
        """
        self.config = config
        self.project_root = get_project_root()

    async def analyze_project(self) -> Dict[str, Any]:
        """Analyze current project structure

        Returns:
            Project analysis results
        """
        logger.info("Analyzing project structure")

        analysis = {
            'project_type': self._detect_project_type(),
            'structure': await self._analyze_structure(),
            'technologies': await self._detect_technologies(),
            'metrics': await self._calculate_metrics(),
            'recommended_workflows': await self._recommend_workflows()
        }

        return analysis

    def _detect_project_type(self) -> str:
        """Detect project type based on files present

        Returns:
            Project type (fullstack, backend, frontend, etc.)
        """
        has_backend = (self.project_root / 'backend').exists()
        has_frontend = (self.project_root / 'frontend').exists()
        has_docker = (self.project_root / 'docker-compose.yml').exists()

        if has_backend and has_frontend:
            return 'fullstack'
        elif has_backend:
            return 'backend'
        elif has_frontend:
            return 'frontend'
        elif has_docker:
            return 'docker'
        else:
            return 'unknown'

    async def _analyze_structure(self) -> Dict[str, Any]:
        """Analyze directory structure

        Returns:
            Structure analysis
        """
        structure = {
            'directories': [],
            'key_files': [],
            'config_files': []
        }

        # Get top-level directories
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                structure['directories'].append(item.name)

        # Find key files
        key_patterns = [
            'README.md', 'CLAUDE.md', 'package.json', 'requirements.txt',
            'Dockerfile', 'docker-compose.yml', 'Makefile'
        ]
        for pattern in key_patterns:
            file_path = self.project_root / pattern
            if file_path.exists():
                structure['key_files'].append(pattern)

        # Find config files
        config_patterns = ['.env', '.env.template', 'config.json', '.gitignore']
        for pattern in config_patterns:
            file_path = self.project_root / pattern
            if file_path.exists():
                structure['config_files'].append(pattern)

        return structure

    async def _detect_technologies(self) -> Dict[str, List[str]]:
        """Detect technologies used in project

        Returns:
            Technologies by category
        """
        technologies = {
            'backend': [],
            'frontend': [],
            'database': [],
            'infrastructure': []
        }

        # Backend
        if (self.project_root / 'backend' / 'requirements.txt').exists():
            technologies['backend'].append('Python')
            with open(self.project_root / 'backend' / 'requirements.txt', 'r') as f:
                content = f.read().lower()
                if 'fastapi' in content:
                    technologies['backend'].append('FastAPI')
                if 'flask' in content:
                    technologies['backend'].append('Flask')
                if 'django' in content:
                    technologies['backend'].append('Django')

        # Frontend
        if (self.project_root / 'frontend' / 'package.json').exists():
            with open(self.project_root / 'frontend' / 'package.json', 'r') as f:
                package_data = json.load(f)
                deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}

                if 'react' in deps:
                    technologies['frontend'].append('React')
                if 'vue' in deps:
                    technologies['frontend'].append('Vue')
                if 'angular' in deps:
                    technologies['frontend'].append('Angular')
                if 'typescript' in deps:
                    technologies['frontend'].append('TypeScript')

        # Database
        if (self.project_root / 'docker-compose.yml').exists():
            with open(self.project_root / 'docker-compose.yml', 'r') as f:
                content = f.read().lower()
                if 'postgres' in content:
                    technologies['database'].append('PostgreSQL')
                if 'mysql' in content:
                    technologies['database'].append('MySQL')
                if 'mongodb' in content:
                    technologies['database'].append('MongoDB')
                if 'redis' in content:
                    technologies['database'].append('Redis')

        # Infrastructure
        if (self.project_root / 'docker-compose.yml').exists():
            technologies['infrastructure'].append('Docker')
        if (self.project_root / '.github' / 'workflows').exists():
            technologies['infrastructure'].append('GitHub Actions')
        if (self.project_root / 'Makefile').exists():
            technologies['infrastructure'].append('Make')

        return technologies

    async def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate project metrics

        Returns:
            Project metrics
        """
        metrics = {
            'file_count': 0,
            'directory_count': 0,
            'code_files': 0
        }

        code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.vue', '.go', '.rs'}

        for item in self.project_root.rglob('*'):
            # Skip hidden and node_modules/venv
            if any(part.startswith('.') or part in ['node_modules', 'venv', '__pycache__']
                   for part in item.parts):
                continue

            if item.is_file():
                metrics['file_count'] += 1
                if item.suffix in code_extensions:
                    metrics['code_files'] += 1
            elif item.is_dir():
                metrics['directory_count'] += 1

        return metrics

    async def _recommend_workflows(self) -> List[str]:
        """Recommend workflows based on project analysis

        Returns:
            List of recommended workflow types
        """
        recommendations = []

        project_type = self._detect_project_type()

        if project_type == 'fullstack':
            recommendations.extend([
                'backend-improvement',
                'frontend-improvement',
                'integration-testing',
                'devops-enhancement'
            ])
        elif project_type == 'backend':
            recommendations.extend([
                'api-development',
                'testing-enhancement',
                'performance-optimization'
            ])
        elif project_type == 'frontend':
            recommendations.extend([
                'ui-improvement',
                'ux-enhancement',
                'component-library'
            ])

        # Check for existing agent coordination
        if (self.project_root / '.agent-coordination').exists():
            recommendations.append('multi-agent-coordination')

        return recommendations

    async def get_file_tree(self, max_depth: int = 3) -> Dict[str, Any]:
        """Get file tree representation

        Args:
            max_depth: Maximum depth to traverse

        Returns:
            File tree structure
        """
        def build_tree(path: Path, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {'name': path.name, 'type': 'directory', 'truncated': True}

            if path.is_file():
                return {'name': path.name, 'type': 'file'}

            children = []
            try:
                for item in sorted(path.iterdir()):
                    # Skip hidden files and common ignore patterns
                    if item.name.startswith('.') or item.name in ['node_modules', 'venv', '__pycache__', 'dist', 'build']:
                        continue
                    children.append(build_tree(item, current_depth + 1))
            except PermissionError:
                pass

            return {'name': path.name, 'type': 'directory', 'children': children}

        return build_tree(self.project_root)
