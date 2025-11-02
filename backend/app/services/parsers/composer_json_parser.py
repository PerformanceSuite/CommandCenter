"""
PHP composer.json parser
"""

import json
import re
from pathlib import Path
from typing import List

import httpx

from app.schemas.project_analysis import Dependency, DependencyType
from app.services.parsers.base_parser import BaseParser


class ComposerJsonParser(BaseParser):
    """Parser for PHP composer.json files"""

    @property
    def name(self) -> str:
        return "composer"

    @property
    def config_files(self) -> List[str]:
        return ["composer.json"]

    @property
    def language(self) -> str:
        return "php"

    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse composer.json dependencies.

        Args:
            project_path: Project root path

        Returns:
            List of detected dependencies
        """
        composer_path = project_path / "composer.json"

        if not composer_path.exists():
            return []

        content = await self._read_file_async(composer_path)
        data = json.loads(content)

        dependencies = []

        # Parse runtime dependencies
        for name, version in data.get("require", {}).items():
            # Skip PHP itself
            if name == "php":
                continue

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
        for name, version in data.get("require-dev", {}).items():
            dependencies.append(
                Dependency(
                    name=name,
                    version=self._clean_version(version),
                    type=DependencyType.DEV,
                    language=self.language,
                    confidence=1.0,
                )
            )

        # Enrich with latest versions
        await self._enrich_with_latest_versions(dependencies)

        return dependencies

    def _clean_version(self, version: str) -> str:
        """
        Remove version constraint operators.

        Args:
            version: Raw version string

        Returns:
            Cleaned version string
        """
        # Remove common constraint operators
        cleaned = re.sub(r"^[\^~>=<*]+", "", version)
        # Handle version ranges (take first version)
        cleaned = cleaned.split("||")[0].strip()
        cleaned = cleaned.split(" - ")[0].strip()
        cleaned = cleaned.split("|")[0].strip()
        return cleaned

    async def _enrich_with_latest_versions(self, dependencies: List[Dependency]) -> None:
        """
        Fetch latest versions from Packagist.

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

    async def get_latest_version(self, package_name: str, client: httpx.AsyncClient = None) -> str:
        """
        Fetch latest version from Packagist.

        Args:
            package_name: Package name
            client: Optional httpx client

        Returns:
            Latest version string
        """
        url = f"https://repo.packagist.org/p2/{package_name}.json"

        if client:
            response = await client.get(url)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(url)

        response.raise_for_status()
        data = response.json()

        # Get latest version from packages list
        packages = data.get("packages", {}).get(package_name, [])
        if packages:
            # Versions are ordered, first one is latest
            versions = [p["version"] for p in packages if not p["version"].startswith("dev-")]
            if versions:
                return versions[0].lstrip("v")

        raise ValueError(f"No version found for {package_name}")
