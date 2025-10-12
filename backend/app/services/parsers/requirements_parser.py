"""
Python requirements.txt parser
"""

import re
from pathlib import Path
from typing import List

import httpx

from app.schemas.project_analysis import Dependency, DependencyType
from app.services.parsers.base_parser import BaseParser


class RequirementsParser(BaseParser):
    """Parser for Python requirements.txt files"""

    @property
    def name(self) -> str:
        return "pip"

    @property
    def config_files(self) -> List[str]:
        return ["requirements.txt", "requirements-dev.txt", "requirements.in"]

    @property
    def language(self) -> str:
        return "python"

    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse requirements.txt dependencies.

        Args:
            project_path: Project root path

        Returns:
            List of detected dependencies
        """
        dependencies = []

        # Check all possible requirements files
        for config_file in self.config_files:
            req_path = project_path / config_file
            if not req_path.exists():
                continue

            content = await self._read_file_async(req_path)
            dep_type = (
                DependencyType.DEV if "dev" in config_file else DependencyType.RUNTIME
            )

            for line in content.splitlines():
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Skip -r includes and other flags
                if line.startswith("-"):
                    continue

                # Parse package specification
                match = re.match(r"([a-zA-Z0-9\-_.]+)(==|>=|<=|>|<|~=)([0-9.]+)", line)
                if match:
                    name = match.group(1)
                    version = match.group(3)

                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            type=dep_type,
                            language=self.language,
                            confidence=1.0,
                        )
                    )
                else:
                    # Package without version specifier
                    package_name = line.split("[")[0].strip()
                    if package_name:
                        dependencies.append(
                            Dependency(
                                name=package_name,
                                version="unknown",
                                type=dep_type,
                                language=self.language,
                                confidence=0.8,
                            )
                        )

        # Enrich with latest versions
        await self._enrich_with_latest_versions(dependencies)

        return dependencies

    async def _enrich_with_latest_versions(
        self, dependencies: List[Dependency]
    ) -> None:
        """
        Fetch latest versions from PyPI.

        Args:
            dependencies: List of dependencies to enrich
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            for dep in dependencies:
                try:
                    latest = await self.get_latest_version(dep.name, client=client)
                    dep.latest_version = latest
                    dep.is_outdated = latest != dep.version
                except Exception:
                    # Silently fail for missing/private packages
                    pass

    async def get_latest_version(
        self, package_name: str, client: httpx.AsyncClient = None
    ) -> str:
        """
        Fetch latest version from PyPI.

        Args:
            package_name: Package name
            client: Optional httpx client

        Returns:
            Latest version string
        """
        url = f"https://pypi.org/pypi/{package_name}/json"

        if client:
            response = await client.get(url)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(url)

        response.raise_for_status()
        data = response.json()
        return data["info"]["version"]
