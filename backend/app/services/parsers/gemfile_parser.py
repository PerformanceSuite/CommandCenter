"""
Ruby Gemfile parser
"""

import re
from pathlib import Path
from typing import List

import httpx

from app.schemas.project_analysis import Dependency, DependencyType
from app.services.parsers.base_parser import BaseParser


class GemfileParser(BaseParser):
    """Parser for Ruby Gemfile files"""

    @property
    def name(self) -> str:
        return "bundler"

    @property
    def config_files(self) -> List[str]:
        return ["Gemfile"]

    @property
    def language(self) -> str:
        return "ruby"

    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse Gemfile dependencies.

        Args:
            project_path: Project root path

        Returns:
            List of detected dependencies
        """
        gemfile_path = project_path / "Gemfile"

        if not gemfile_path.exists():
            return []

        content = await self._read_file_async(gemfile_path)
        dependencies = []

        in_group = None

        for line in content.splitlines():
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Track gem groups (development, test, etc.)
            group_match = re.match(r"group\s+:(\w+)", line)
            if group_match:
                in_group = group_match.group(1)
                continue

            # End of group
            if line == "end" and in_group:
                in_group = None
                continue

            # Parse gem declarations
            # Match patterns: gem 'name', 'version' or gem 'name', version: 'version'
            gem_match = re.match(
                r"gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?",
                line,
            )
            if gem_match:
                name = gem_match.group(1)
                version = gem_match.group(2) or "unknown"

                # If no explicit version, try to find version constraint
                if version == "unknown":
                    version_match = re.search(
                        r"['\"]~>\s*([0-9.]+)['\"]", line
                    )
                    if version_match:
                        version = version_match.group(1)

                dep_type = (
                    DependencyType.DEV
                    if in_group in ["development", "test"]
                    else DependencyType.RUNTIME
                )

                dependencies.append(
                    Dependency(
                        name=name,
                        version=version.lstrip("~>>=<"),
                        type=dep_type,
                        language=self.language,
                        confidence=1.0 if version != "unknown" else 0.8,
                    )
                )

        # Enrich with latest versions
        await self._enrich_with_latest_versions(dependencies)

        return dependencies

    async def _enrich_with_latest_versions(
        self, dependencies: List[Dependency]
    ) -> None:
        """
        Fetch latest versions from RubyGems.

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
                    dep.is_outdated = latest != dep.version
                except Exception:
                    # Silently fail for missing/private gems
                    pass

    async def get_latest_version(
        self, package_name: str, client: httpx.AsyncClient = None
    ) -> str:
        """
        Fetch latest version from RubyGems.

        Args:
            package_name: Gem name
            client: Optional httpx client

        Returns:
            Latest version string
        """
        url = f"https://rubygems.org/api/v1/gems/{package_name}.json"

        if client:
            response = await client.get(url)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(url)

        response.raise_for_status()
        data = response.json()
        return data["version"]
