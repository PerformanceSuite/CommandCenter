"""
Setup service - Clones CommandCenter and configures it for a project
"""

import os
import subprocess
import secrets
from pathlib import Path

from app.models import Project


class SetupService:
    """Service for setting up new CommandCenter instances"""

    # CommandCenter source (configurable via env, defaults to Docker mount path)
    CC_SOURCE = os.environ.get("CC_SOURCE_PATH", "/projects/CommandCenter")

    @classmethod
    def get_template_version(cls) -> dict:
        """
        Get template version info to verify freshness

        Returns commit hash, branch, and last modified time
        """
        try:
            # Get current commit hash
            result = subprocess.run(
                ["git", "-C", cls.CC_SOURCE, "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            commit_hash = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Get current branch
            result = subprocess.run(
                ["git", "-C", cls.CC_SOURCE, "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            branch = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Get last commit message
            result = subprocess.run(
                ["git", "-C", cls.CC_SOURCE, "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            last_commit = result.stdout.strip() if result.returncode == 0 else "unknown"

            return {
                "commit": commit_hash[:8],  # Short hash
                "full_commit": commit_hash,
                "branch": branch,
                "last_commit_message": last_commit,
                "source_path": cls.CC_SOURCE,
            }
        except Exception as e:
            return {
                "error": str(e),
                "source_path": cls.CC_SOURCE,
            }

    async def setup_commandcenter(self, project: Project) -> None:
        """
        Setup CommandCenter for a project

        Steps:
        1. Copy CommandCenter from local source
        2. Create .env file with unique configuration
        3. Create necessary directories
        """
        # Copy CommandCenter from local source
        await self._copy_commandcenter(project.cc_path)

        # Generate .env file
        await self._generate_env_file(project)

        # Create data directories
        await self._create_directories(project.cc_path)

    async def _copy_commandcenter(self, cc_path: str) -> None:
        """
        Copy CommandCenter from local source using git clone

        This ensures we ALWAYS get the latest committed state from the template,
        preventing old/stale code from being copied to new projects.
        """
        if os.path.exists(cc_path):
            # Already exists, skip
            return

        # Ensure source exists and is a git repository
        if not os.path.exists(self.CC_SOURCE):
            raise RuntimeError(f"CommandCenter source not found at {self.CC_SOURCE}")

        git_dir = os.path.join(self.CC_SOURCE, ".git")
        if not os.path.exists(git_dir):
            raise RuntimeError(f"CommandCenter source is not a git repository: {self.CC_SOURCE}")

        try:
            # Use git clone with depth 1 for faster copying
            # This gets the exact committed state of the template
            result = subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth", "1",  # Single commit (faster)
                    "--single-branch",  # Only current branch
                    self.CC_SOURCE,
                    cc_path,
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to clone CommandCenter: {result.stderr}")

            # Remove .git directory from the copy (project doesn't need git history)
            cloned_git_dir = os.path.join(cc_path, ".git")
            if os.path.exists(cloned_git_dir):
                subprocess.run(
                    ["rm", "-rf", cloned_git_dir],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

            # Remove hub directory from the copy (projects don't need hub)
            hub_dir = os.path.join(cc_path, "hub")
            if os.path.exists(hub_dir):
                subprocess.run(
                    ["rm", "-rf", hub_dir],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout while cloning CommandCenter template")
        except Exception as e:
            raise RuntimeError(f"Failed to copy CommandCenter: {str(e)}")

    async def _generate_env_file(self, project: Project) -> None:
        """Generate .env file with project-specific configuration"""
        env_path = os.path.join(project.cc_path, ".env")

        # Generate secrets
        secret_key = secrets.token_hex(32)
        db_password = secrets.token_urlsafe(32)

        env_content = f"""# CommandCenter Configuration
# Auto-generated by Hub for project: {project.name}
# Generated: {project.created_at}

# Project Isolation
COMPOSE_PROJECT_NAME={project.compose_project_name}

# Ports
BACKEND_PORT={project.backend_port}
FRONTEND_PORT={project.frontend_port}
POSTGRES_PORT={project.postgres_port}
REDIS_PORT={project.redis_port}

# Security
SECRET_KEY={secret_key}
DB_PASSWORD={db_password}
ENCRYPT_TOKENS=true

# Database (internal port - 5432 inside Docker network)
DATABASE_URL=postgresql://commandcenter:${{DB_PASSWORD}}@postgres:5432/commandcenter

# Redis & Celery (internal port - 6379 inside Docker network)
REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Optional: Add your API keys here
# GITHUB_TOKEN=ghp_...
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# CORS
CORS_ORIGINS=["http://localhost:{project.frontend_port}"]

# Frontend Configuration
VITE_PROJECT_NAME={project.name}
VITE_API_BASE_URL=http://localhost:{project.backend_port}
"""

        try:
            with open(env_path, "w") as f:
                f.write(env_content)
        except Exception as e:
            raise RuntimeError(f"Failed to write .env file: {str(e)}")

    async def _create_directories(self, cc_path: str) -> None:
        """Create necessary data directories"""
        directories = [
            os.path.join(cc_path, "rag_storage"),
            os.path.join(cc_path, "backups"),
            os.path.join(cc_path, "hub_data"),
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
