"""Git Tools

Tools for git operations and repository management.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add base server to path
base_path = Path(__file__).parent.parent.parent / 'base'
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

from utils import get_logger, get_project_root

logger = get_logger(__name__)


class GitTools:
    """Git operation tools"""

    def __init__(self, config):
        """Initialize git tools

        Args:
            config: ProjectManagerConfig instance
        """
        self.config = config
        self.project_root = get_project_root()

    async def get_repo_status(self) -> Dict[str, Any]:
        """Get current git repository status

        Returns:
            Repository status information
        """
        logger.debug("Getting repository status")

        try:
            # Get current branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = branch_result.stdout.strip()

            # Get status
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            status_lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []

            # Get recent commits
            log_result = subprocess.run(
                ['git', 'log', '--oneline', '-n', '5'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            recent_commits = log_result.stdout.strip().split('\n') if log_result.stdout.strip() else []

            # Parse status
            modified = [line[3:] for line in status_lines if line.startswith(' M')]
            added = [line[3:] for line in status_lines if line.startswith('A ')]
            deleted = [line[3:] for line in status_lines if line.startswith('D ')]
            untracked = [line[3:] for line in status_lines if line.startswith('??')]

            return {
                'current_branch': current_branch,
                'clean': len(status_lines) == 0,
                'modified': modified,
                'added': added,
                'deleted': deleted,
                'untracked': untracked,
                'recent_commits': recent_commits
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise ValueError(f"Git operation failed: {e.stderr}")

    async def create_branch(self, branch_name: str, from_branch: str = 'main') -> Dict[str, Any]:
        """Create a new git branch

        Args:
            branch_name: Name of new branch
            from_branch: Base branch to create from (default: main)

        Returns:
            Branch creation result
        """
        logger.info(f"Creating branch: {branch_name} from {from_branch}")

        try:
            # Create branch
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name, from_branch],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            return {
                'branch': branch_name,
                'from_branch': from_branch,
                'created': True
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch: {e.stderr}")
            raise ValueError(f"Failed to create branch: {e.stderr}")

    async def merge_branch(self, branch_name: str, target_branch: str = 'main') -> Dict[str, Any]:
        """Merge a branch into target branch

        Args:
            branch_name: Branch to merge
            target_branch: Target branch (default: main)

        Returns:
            Merge result
        """
        logger.info(f"Merging {branch_name} into {target_branch}")

        try:
            # Checkout target branch
            subprocess.run(
                ['git', 'checkout', target_branch],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            # Merge branch
            result = subprocess.run(
                ['git', 'merge', branch_name, '--no-ff'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            return {
                'branch': branch_name,
                'target_branch': target_branch,
                'merged': True,
                'output': result.stdout
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Merge failed: {e.stderr}")
            # Check if it's a conflict
            if 'CONFLICT' in e.stderr or 'CONFLICT' in e.stdout:
                return {
                    'branch': branch_name,
                    'target_branch': target_branch,
                    'merged': False,
                    'conflict': True,
                    'output': e.stderr or e.stdout
                }
            raise ValueError(f"Merge failed: {e.stderr}")

    async def list_branches(self) -> List[str]:
        """List all git branches

        Returns:
            List of branch names
        """
        try:
            result = subprocess.run(
                ['git', 'branch', '--list'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            branches = [
                line.strip().replace('* ', '')
                for line in result.stdout.strip().split('\n')
                if line.strip()
            ]

            return branches

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list branches: {e.stderr}")
            raise ValueError(f"Failed to list branches: {e.stderr}")

    async def get_diff(self, branch1: str, branch2: str = 'main') -> Dict[str, Any]:
        """Get diff between two branches

        Args:
            branch1: First branch
            branch2: Second branch (default: main)

        Returns:
            Diff information
        """
        try:
            # Get diff stats
            stats_result = subprocess.run(
                ['git', 'diff', '--stat', f'{branch2}...{branch1}'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            # Get file list
            files_result = subprocess.run(
                ['git', 'diff', '--name-only', f'{branch2}...{branch1}'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            files = files_result.stdout.strip().split('\n') if files_result.stdout.strip() else []

            return {
                'branch1': branch1,
                'branch2': branch2,
                'stats': stats_result.stdout,
                'files_changed': files,
                'file_count': len(files)
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get diff: {e.stderr}")
            raise ValueError(f"Failed to get diff: {e.stderr}")
