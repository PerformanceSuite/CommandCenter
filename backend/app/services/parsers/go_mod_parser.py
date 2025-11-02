"""
Go modules (go.mod) parser
"""

import re
from pathlib import Path
from typing import List

import httpx

from app.schemas.project_analysis import Dependency, DependencyType
from app.services.parsers.base_parser import BaseParser


class GoModParser(BaseParser):
    """Parser for Go go.mod files"""

    @property
    def name(self) -> str:
        return "go-modules"

    @property
    def config_files(self) -> List[str]:
        return ["go.mod"]

    @property
    def language(self) -> str:
        return "go"

    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse go.mod dependencies.

        Args:
            project_path: Project root path

        Returns:
            List of detected dependencies
        """
        go_mod_path = project_path / "go.mod"

        if not go_mod_path.exists():
            return []

        content = await self._read_file_async(go_mod_path)
        dependencies = []

        # Parse require blocks
        in_require_block = False
        for line in content.splitlines():
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("//"):
                continue

            # Detect require blocks
            if line.startswith("require ("):
                in_require_block = True
                continue
            elif line.startswith(")"):
                in_require_block = False
                continue

            # Parse single-line require
            if line.startswith("require "):
                line = line.replace("require ", "").strip()
                dep = self._parse_dependency_line(line)
                if dep:
                    dependencies.append(dep)

            # Parse require block entries
            elif in_require_block:
                dep = self._parse_dependency_line(line)
                if dep:
                    dependencies.append(dep)

        # Enrich with latest versions
        await self._enrich_with_latest_versions(dependencies)

        return dependencies

    def _parse_dependency_line(self, line: str) -> Dependency:
        """
        Parse a single dependency line.

        Args:
            line: Dependency line from go.mod

        Returns:
            Dependency object or None
        """
        # Remove "// indirect" comments
        line = line.split("//")[0].strip()

        # Match pattern: module_path version
        match = re.match(r"([^\s]+)\s+v([0-9.]+(?:-[a-zA-Z0-9.]+)?)", line)
        if match:
            module = match.group(1)
            version = match.group(2)

            return Dependency(
                name=module,
                version=version,
                type=DependencyType.RUNTIME,
                language=self.language,
                confidence=1.0,
            )

        return None

    async def _enrich_with_latest_versions(
        self, dependencies: List[Dependency]
    ) -> None:
        """
        Fetch latest versions from Go proxy.

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
                    # Silently fail for missing/private modules
                    pass

    async def get_latest_version(
        self, package_name: str, client: httpx.AsyncClient = None
    ) -> str:
        """
        Fetch latest version from Go proxy.

        Args:
            package_name: Module name
            client: Optional httpx client

        Returns:
            Latest version string
        """
        # Use Go proxy for version lookup
        url = f"https://proxy.golang.org/{package_name}/@latest"

        if client:
            response = await client.get(url)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(url)

        response.raise_for_status()
        data = response.json()
        # Remove 'v' prefix if present
        version = data["Version"].lstrip("v")
        return version
