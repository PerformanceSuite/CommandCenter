"""
Java Maven pom.xml parser
"""

from pathlib import Path
from typing import List

import httpx
from lxml import etree

from app.schemas.project_analysis import Dependency, DependencyType
from app.services.parsers.base_parser import BaseParser


class PomXmlParser(BaseParser):
    """Parser for Java Maven pom.xml files"""

    @property
    def name(self) -> str:
        return "maven"

    @property
    def config_files(self) -> List[str]:
        return ["pom.xml"]

    @property
    def language(self) -> str:
        return "java"

    async def parse(self, project_path: Path) -> List[Dependency]:
        """
        Parse pom.xml dependencies.

        Args:
            project_path: Project root path

        Returns:
            List of detected dependencies
        """
        pom_path = project_path / "pom.xml"

        if not pom_path.exists():
            return []

        content = await self._read_file_async(pom_path)

        # Parse XML with namespace handling
        tree = etree.fromstring(content.encode())
        namespace = {"mvn": "http://maven.apache.org/POM/4.0.0"}

        dependencies = []

        # Parse dependencies
        for dep in tree.xpath(
            "//mvn:dependencies/mvn:dependency", namespaces=namespace
        ):
            group_id = dep.findtext("mvn:groupId", namespaces=namespace)
            artifact_id = dep.findtext("mvn:artifactId", namespaces=namespace)
            version = dep.findtext("mvn:version", namespaces=namespace)
            scope = dep.findtext("mvn:scope", namespaces=namespace) or "compile"

            if group_id and artifact_id:
                name = f"{group_id}:{artifact_id}"
                dep_type = (
                    DependencyType.DEV
                    if scope in ["test", "provided"]
                    else DependencyType.RUNTIME
                )

                dependencies.append(
                    Dependency(
                        name=name,
                        version=version or "unknown",
                        type=dep_type,
                        language=self.language,
                        confidence=1.0 if version else 0.8,
                    )
                )

        # Also check for dependencies without namespace (older POM files)
        if not dependencies:
            for dep in tree.xpath("//dependencies/dependency"):
                group_id = dep.findtext("groupId")
                artifact_id = dep.findtext("artifactId")
                version = dep.findtext("version")
                scope = dep.findtext("scope") or "compile"

                if group_id and artifact_id:
                    name = f"{group_id}:{artifact_id}"
                    dep_type = (
                        DependencyType.DEV
                        if scope in ["test", "provided"]
                        else DependencyType.RUNTIME
                    )

                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version or "unknown",
                            type=dep_type,
                            language=self.language,
                            confidence=1.0 if version else 0.8,
                        )
                    )

        # Enrich with latest versions
        await self._enrich_with_latest_versions(dependencies)

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
        # Maven Central search API
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
