"""
Java/Kotlin Gradle build.gradle parser
"""

import re
from pathlib import Path
from typing import List

import httpx

from app.schemas.project_analysis import Dependency, DependencyType
from app.services.parsers.base_parser import BaseParser


class BuildGradleParser(BaseParser):
    """Parser for Gradle build.gradle and build.gradle.kts files"""

    @property
    def name(self) -> str:
        return "gradle"

    @property
    def config_files(self) -> List[str]:
        return ["build.gradle", "build.gradle.kts"]

    @property
    def language(self) -> str:
        return "java"

    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse build.gradle dependencies.

        Args:
            project_path: Project root path

        Returns:
            List of detected dependencies
        """
        dependencies = []

        # Try Groovy syntax first
        gradle_path = project_path / "build.gradle"
        if gradle_path.exists():
            content = await self._read_file_async(gradle_path)
            dependencies.extend(self._parse_groovy_syntax(content))

        # Try Kotlin DSL syntax
        gradle_kts_path = project_path / "build.gradle.kts"
        if gradle_kts_path.exists():
            content = await self._read_file_async(gradle_kts_path)
            dependencies.extend(self._parse_kotlin_syntax(content))

        # Enrich with latest versions
        await self._enrich_with_latest_versions(dependencies)

        return dependencies

    def _parse_groovy_syntax(self, content: str) -> List[Dependency]:
        """
        Parse Groovy-style build.gradle.

        Args:
            content: File content

        Returns:
            List of dependencies
        """
        dependencies = []

        # Match patterns like: implementation 'group:artifact:version'
        patterns = [
            r"(implementation|api|compileOnly|runtimeOnly|testImplementation)\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
            r"(implementation|api|compileOnly|runtimeOnly|testImplementation)\s*\(\s*['\"]([^:]+):([^:]+):([^'\"]+)['\"]\s*\)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                config_type = match.group(1)
                group_id = match.group(2)
                artifact_id = match.group(3)
                version = match.group(4)

                name = f"{group_id}:{artifact_id}"
                dep_type = (
                    DependencyType.DEV
                    if "test" in config_type.lower()
                    else DependencyType.RUNTIME
                )

                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        type=dep_type,
                        language=self.language,
                        confidence=1.0,
                    )
                )

        return dependencies

    def _parse_kotlin_syntax(self, content: str) -> List[Dependency]:
        """
        Parse Kotlin DSL build.gradle.kts.

        Args:
            content: File content

        Returns:
            List of dependencies
        """
        dependencies = []

        # Match patterns like: implementation("group:artifact:version")
        patterns = [
            r"(implementation|api|compileOnly|runtimeOnly|testImplementation)\s*\(\s*\"([^:]+):([^:]+):([^\"]+)\"\s*\)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                config_type = match.group(1)
                group_id = match.group(2)
                artifact_id = match.group(3)
                version = match.group(4)

                name = f"{group_id}:{artifact_id}"
                dep_type = (
                    DependencyType.DEV
                    if "test" in config_type.lower()
                    else DependencyType.RUNTIME
                )

                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        type=dep_type,
                        language=self.language,
                        confidence=1.0,
                    )
                )

        return dependencies

    async def _enrich_with_latest_versions(
        self, dependencies: List[Dependency]
    ) -> None:
        """
        Fetch latest versions from Maven Central.

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
                    # Silently fail for missing/private artifacts
                    pass

    async def get_latest_version(
        self, package_name: str, client: httpx.AsyncClient = None
    ) -> str:
        """
        Fetch latest version from Maven Central.

        Args:
            package_name: Artifact name in format "groupId:artifactId"
            client: Optional httpx client

        Returns:
            Latest version string
        """
        parts = package_name.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid Maven artifact name: {package_name}")

        group_id, artifact_id = parts
        url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&rows=1&wt=json"

        if client:
            response = await client.get(url)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(url)

        response.raise_for_status()
        data = response.json()

        if data["response"]["numFound"] > 0:
            return data["response"]["docs"][0]["latestVersion"]

        raise ValueError(f"No version found for {package_name}")
