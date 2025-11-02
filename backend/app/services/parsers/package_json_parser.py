"""
Node.js package.json parser
"""

import json
import re
from pathlib import Path
from typing import List

import httpx

from app.schemas.project_analysis import Dependency, DependencyType
from app.services.parsers.base_parser import BaseParser


class PackageJsonParser(BaseParser):
    """Parser for Node.js package.json files"""

    @property
    def name(self) -> str:
        return "npm"

    @property
    def config_files(self) -> List[str]:
        return ["package.json"]

    @property
    def language(self) -> str:
        return "javascript"

    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse package.json dependencies.

        Args:
            project_path: Project root path

        Returns:
            List of detected dependencies
        """
        package_json_path = project_path / "package.json"

        if not package_json_path.exists():
            return []

        content = await self._read_file_async(package_json_path)
        data = json.loads(content)

        dependencies = []

        # Parse runtime dependencies
        for name, version in data.get("dependencies", {}).items():
            dependencies.append(
                Dependency(
                    name=name,
                    version=self._clean_version(version),
                    type=DependencyType.RUNTIME,
                    language=self.language,
                    confidence=1.0,
                )
            )

        # Parse dev dependencies
        for name, version in data.get("devDependencies", {}).items():
            dependencies.append(
                Dependency(
                    name=name,
                    version=self._clean_version(version),
                    type=DependencyType.DEV,
                    language=self.language,
                    confidence=1.0,
                )
            )

        # Parse peer dependencies
        for name, version in data.get("peerDependencies", {}).items():
            dependencies.append(
                Dependency(
                    name=name,
                    version=self._clean_version(version),
                    type=DependencyType.PEER,
                    language=self.language,
                    confidence=1.0,
                )
            )

        # Enrich with latest versions (async batch)
        await self._enrich_with_latest_versions(dependencies)

        return dependencies

    def _clean_version(self, version: str) -> str:
        """
        Remove semver operators (^, ~, >=, etc.).

        Args:
            version: Raw version string

        Returns:
            Cleaned version string
        """
        # Remove common semver prefixes
        cleaned = re.sub(r"^[\^~>=<]+", "", version)
        # Handle version ranges (take first version)
        cleaned = cleaned.split("||")[0].strip()
        cleaned = cleaned.split(" - ")[0].strip()
        return cleaned

    async def _enrich_with_latest_versions(
        self, dependencies: List[Dependency]
    ) -> None:
        """
        Fetch latest versions from npm registry in batch.

        Args:
            dependencies: List of dependencies to enrich
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            for dep in dependencies:
                try:
                    latest = await self.get_latest_version(
                        dep.name, client=client
                    )
                    dep.latest_version = latest
                    # Simple version comparison (needs proper semver comparison)
                    dep.is_outdated = latest != dep.version
                except Exception:
                    # Silently fail for missing/private packages
                    pass

    async def get_latest_version(
        self, package_name: str, client: httpx.AsyncClient = None
    ) -> str:
        """
        Fetch latest version from npm registry.

        Args:
            package_name: Package name
            client: Optional httpx client (for connection reuse)

        Returns:
            Latest version string

        Raises:
            httpx.HTTPError: If registry request fails
        """
        url = f"https://registry.npmjs.org/{package_name}/latest"

        if client:
            response = await client.get(url)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(url)

        response.raise_for_status()
        data = response.json()
        return data["version"]
