"""
Base parser interface for dependency parsers
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from app.schemas.project_analysis import Dependency


class BaseParser(ABC):
    """
    Abstract base class for dependency parsers.

    All parsers must implement this interface to be compatible with
    the ProjectAnalyzer service.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Parser name (e.g., 'npm', 'pip', 'cargo').

        Returns:
            Parser identifier string
        """

    @property
    @abstractmethod
    def config_files(self) -> List[str]:
        """
        Config files this parser handles (e.g., ['package.json']).

        Returns:
            List of configuration file names to detect
        """

    @property
    @abstractmethod
    def language(self) -> str:
        """
        Programming language this parser handles (e.g., 'javascript', 'python').

        Returns:
            Language identifier string
        """

    def can_parse(self, project_path: Path) -> bool:
        """
        Check if this parser can handle the project.

        Args:
            project_path: Path to project root directory

        Returns:
            True if any config files exist in project
        """
        for config_file in self.config_files:
            if (project_path / config_file).exists():
                return True
        return False

    @abstractmethod
    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse dependencies from project.

        Args:
            project_path: Path to project root directory

        Returns:
            List of detected dependencies with metadata

        Raises:
            FileNotFoundError: If config files don't exist
            ValueError: If config files are malformed
        """

    async def get_latest_version(self, package_name: str) -> str:
        """
        Fetch latest version from package registry.

        Override in subclass to implement registry-specific logic.

        Args:
            package_name: Name of the package

        Returns:
            Latest version string

        Raises:
            NotImplementedError: If registry lookup not implemented
            httpx.HTTPError: If registry request fails
        """
        raise NotImplementedError(f"{self.name} parser does not implement latest version lookup")

    async def _read_file_async(self, file_path: Path) -> str:
        """
        Asynchronously read file contents.

        Args:
            file_path: Path to file

        Returns:
            File contents as string
        """

        def _read():
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        return await asyncio.to_thread(_read)
