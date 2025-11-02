"""
Rust Cargo.toml parser
"""

from pathlib import Path
from typing import List

import httpx
import toml

from app.schemas.project_analysis import Dependency, DependencyType
from app.services.parsers.base_parser import BaseParser


class CargoTomlParser(BaseParser):
    """Parser for Rust Cargo.toml files"""

    @property
    def name(self) -> str:
        return "cargo"

    @property
    def config_files(self) -> List[str]:
        return ["Cargo.toml"]

    @property
    def language(self) -> str:
        return "rust"

    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse Cargo.toml dependencies.

        Args:
            project_path: Project root path

        Returns:
            List of detected dependencies
        """
        cargo_path = project_path / "Cargo.toml"

        if not cargo_path.exists():
            return []

        content = await self._read_file_async(cargo_path)
        data = toml.loads(content)

        dependencies = []

        # Parse runtime dependencies
        for name, spec in data.get("dependencies", {}).items():
            version = self._extract_version(spec)
            if version:
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        type=DependencyType.RUNTIME,
                        language=self.language,
                        confidence=1.0,
                    )
                )

        # Parse dev dependencies
        for name, spec in data.get("dev-dependencies", {}).items():
            version = self._extract_version(spec)
            if version:
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        type=DependencyType.DEV,
                        language=self.language,
                        confidence=1.0,
                    )
                )

        # Parse build dependencies
        for name, spec in data.get("build-dependencies", {}).items():
            version = self._extract_version(spec)
            if version:
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        type=DependencyType.BUILD,
                        language=self.language,
                        confidence=1.0,
                    )
                )

        # Enrich with latest versions
        await self._enrich_with_latest_versions(dependencies)

        return dependencies

    def _extract_version(self, spec) -> str:
        """
        Extract version from dependency specification.

        Args:
            spec: Can be string version or dict with 'version' key

        Returns:
            Version string or None
        """
        if isinstance(spec, str):
            return spec.lstrip("^~>=<")
        elif isinstance(spec, dict):
            version = spec.get("version", "")
            return version.lstrip("^~>=<")
        return None

    async def _enrich_with_latest_versions(
        self, dependencies: List[Dependency]
    ) -> None:
        """
        Fetch latest versions from crates.io.

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
                    # Silently fail for missing/private crates
                    pass

    async def get_latest_version(
        self, package_name: str, client: httpx.AsyncClient = None
    ) -> str:
        """
        Fetch latest version from crates.io.

        Args:
            package_name: Crate name
            client: Optional httpx client

        Returns:
            Latest version string
        """
        url = f"https://crates.io/api/v1/crates/{package_name}"

        if client:
            response = await client.get(url)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(url)

        response.raise_for_status()
        data = response.json()
        return data["crate"]["max_version"]
