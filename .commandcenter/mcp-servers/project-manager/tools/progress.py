"""Progress Tracking Tools

Tools for monitoring and reporting agent progress.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

# Add base server to path
base_path = Path(__file__).parent.parent.parent / 'base'
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

from utils import get_logger, get_project_root

logger = get_logger(__name__)


class ProgressTools:
    """Progress tracking and monitoring tools"""

    def __init__(self, config):
        """Initialize progress tools

        Args:
            config: ProjectManagerConfig instance
        """
        self.config = config
        self.project_root = get_project_root()
        self.coordination_dir = self.project_root / config.coordination_dir

    async def track_progress(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Track overall or specific agent progress

        Args:
            agent_name: Optional agent name to track specifically

        Returns:
            Progress information
        """
        status_file = self.coordination_dir / 'mcp-status.json'

        if not status_file.exists():
            return {
                'total_agents': 0,
                'progress': 0.0,
                'agents': []
            }

        with open(status_file, 'r') as f:
            status_data = json.load(f)

        if agent_name:
            # Track specific agent
            agent_info = status_data.get('agents', {}).get(agent_name)
            if not agent_info:
                raise ValueError(f"Agent not found: {agent_name}")

            return {
                'agent_name': agent_name,
                **agent_info
            }
        else:
            # Track all agents
            agents = status_data.get('agents', {})
            total_agents = len(agents)
            completed = len(status_data.get('completed', []))
            failed = len(status_data.get('failed', []))

            if total_agents == 0:
                overall_progress = 0.0
            else:
                # Calculate weighted progress
                total_progress = sum(agent.get('progress', 0.0) for agent in agents.values())
                overall_progress = total_progress / total_agents

            return {
                'total_agents': total_agents,
                'completed': completed,
                'failed': failed,
                'in_progress': total_agents - completed - failed,
                'overall_progress': overall_progress,
                'agents': [
                    {'name': name, **info}
                    for name, info in agents.items()
                ]
            }

    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive progress report

        Returns:
            Detailed progress report
        """
        logger.info("Generating progress report")

        status_file = self.coordination_dir / 'mcp-status.json'

        if not status_file.exists():
            return {
                'timestamp': datetime.now().isoformat(),
                'summary': 'No agents found',
                'agents': []
            }

        with open(status_file, 'r') as f:
            status_data = json.load(f)

        agents = status_data.get('agents', {})
        completed = status_data.get('completed', [])
        failed = status_data.get('failed', [])
        blocked = status_data.get('blocked', [])

        # Calculate statistics
        total_agents = len(agents)
        total_progress = sum(agent.get('progress', 0.0) for agent in agents.values())
        avg_progress = total_progress / total_agents if total_agents > 0 else 0.0

        # Agent breakdown by status
        pending = [name for name, info in agents.items() if info.get('status') == 'pending']
        in_progress = [name for name, info in agents.items() if info.get('status') == 'in_progress']

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_agents': total_agents,
                'completed': len(completed),
                'failed': len(failed),
                'blocked': len(blocked),
                'pending': len(pending),
                'in_progress': len(in_progress),
                'average_progress': avg_progress
            },
            'agents': {
                'completed': completed,
                'failed': failed,
                'blocked': blocked,
                'pending': pending,
                'in_progress': in_progress
            },
            'detailed_status': [
                {
                    'name': name,
                    'status': info.get('status'),
                    'progress': info.get('progress', 0.0),
                    'current_task': info.get('current_task'),
                    'review_score': info.get('review_score'),
                    'tests_passing': info.get('tests_passing'),
                    'pr_url': info.get('pr_url')
                }
                for name, info in agents.items()
            ]
        }

        return report

    async def get_blockers(self) -> List[Dict[str, Any]]:
        """Get list of blocked agents and their blockers

        Returns:
            List of blocked agents with blocker information
        """
        status_file = self.coordination_dir / 'mcp-status.json'

        if not status_file.exists():
            return []

        with open(status_file, 'r') as f:
            status_data = json.load(f)

        blocked_agents = []
        agents = status_data.get('agents', {})

        for name, info in agents.items():
            blocked_by = info.get('blocked_by', [])
            if blocked_by:
                # Check if blockers are completed
                unresolved_blockers = []
                for blocker in blocked_by:
                    blocker_info = agents.get(blocker, {})
                    if blocker_info.get('status') != 'completed':
                        unresolved_blockers.append({
                            'name': blocker,
                            'status': blocker_info.get('status', 'unknown')
                        })

                if unresolved_blockers:
                    blocked_agents.append({
                        'agent': name,
                        'blocked_by': unresolved_blockers
                    })

        return blocked_agents

    async def estimate_completion(self) -> Dict[str, Any]:
        """Estimate completion time based on current progress

        Returns:
            Completion estimate
        """
        status_file = self.coordination_dir / 'mcp-status.json'

        if not status_file.exists():
            return {
                'estimated_hours': 0,
                'estimated_completion': 'unknown'
            }

        with open(status_file, 'r') as f:
            status_data = json.load(f)

        agents = status_data.get('agents', {})

        # Calculate remaining hours
        total_remaining = 0.0
        for info in agents.values():
            estimated_hours = info.get('estimated_hours', 0)
            progress = info.get('progress', 0.0)
            remaining = estimated_hours * (1.0 - progress)
            total_remaining += remaining

        # Estimate based on parallel execution
        max_parallel = self.config.max_parallel_agents
        if max_parallel > 0:
            estimated_days = (total_remaining / max_parallel) / 8  # 8 hours per day
        else:
            estimated_days = total_remaining / 8

        return {
            'total_remaining_hours': total_remaining,
            'estimated_days': estimated_days,
            'max_parallel_agents': max_parallel,
            'note': 'Estimate assumes optimal parallel execution'
        }

    async def get_review_scores(self) -> List[Dict[str, Any]]:
        """Get review scores for all agents

        Returns:
            List of agents with review scores
        """
        status_file = self.coordination_dir / 'mcp-status.json'

        if not status_file.exists():
            return []

        with open(status_file, 'r') as f:
            status_data = json.load(f)

        agents = status_data.get('agents', {})

        scores = []
        for name, info in agents.items():
            review_score = info.get('review_score')
            if review_score is not None:
                scores.append({
                    'agent': name,
                    'score': review_score,
                    'status': info.get('status'),
                    'pr_url': info.get('pr_url')
                })

        return scores
