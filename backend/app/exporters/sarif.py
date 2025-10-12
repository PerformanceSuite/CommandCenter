"""
SARIF (Static Analysis Results Interchange Format) exporter.

Implements SARIF 2.1.0 specification for GitHub code scanning integration.
Reference: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib

from app.exporters import BaseExporter


class SARIFExporter(BaseExporter):
    """
    Export analysis results to SARIF 2.1.0 format.

    SARIF is consumed by:
    - GitHub Code Scanning
    - GitLab SAST
    - Azure DevOps
    - VS Code and other IDEs
    """

    # SARIF severity levels
    SARIF_LEVEL_ERROR = "error"
    SARIF_LEVEL_WARNING = "warning"
    SARIF_LEVEL_NOTE = "note"
    SARIF_LEVEL_NONE = "none"

    # SARIF result kinds
    SARIF_KIND_FAIL = "fail"
    SARIF_KIND_PASS = "pass"
    SARIF_KIND_REVIEW = "review"
    SARIF_KIND_NOTAPPLICABLE = "notApplicable"

    def __init__(self, project_analysis: Dict[str, Any], tool_name: str = "CommandCenter"):
        """
        Initialize SARIF exporter.

        Args:
            project_analysis: Analysis results dictionary
            tool_name: Name of the analysis tool
        """
        super().__init__(project_analysis)
        self.tool_name = tool_name
        self.tool_version = "2.0.0"  # Phase 2 version

    def export(self) -> Dict[str, Any]:
        """
        Export analysis to SARIF 2.1.0 format.

        Returns:
            SARIF document as dictionary
        """
        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [self._create_run()],
        }

    def _create_run(self) -> Dict[str, Any]:
        """
        Create SARIF run object.

        Returns:
            SARIF run dictionary
        """
        return {
            "tool": self._create_tool(),
            "invocations": [self._create_invocation()],
            "artifacts": self._create_artifacts(),
            "results": self._create_results(),
            "properties": {
                "commandCenter": {
                    "projectPath": self.project_path,
                    "analyzedAt": self.analyzed_at,
                    "analysisVersion": self.analysis.get("analysis_version", "2.0.0"),
                }
            },
        }

    def _create_tool(self) -> Dict[str, Any]:
        """
        Create SARIF tool object.

        Returns:
            SARIF tool dictionary
        """
        return {
            "driver": {
                "name": self.tool_name,
                "semanticVersion": self.tool_version,
                "informationUri": "https://github.com/PerformanceSuite/CommandCenter",
                "rules": self._create_rules(),
            }
        }

    def _create_rules(self) -> List[Dict[str, Any]]:
        """
        Create SARIF rule definitions.

        Rules describe the types of issues detected.

        Returns:
            List of SARIF rule dictionaries
        """
        rules = [
            {
                "id": "CC001",
                "name": "OutdatedDependency",
                "shortDescription": {"text": "Outdated dependency detected"},
                "fullDescription": {
                    "text": "A dependency is significantly outdated and may have security vulnerabilities or missing features."
                },
                "helpUri": "https://github.com/PerformanceSuite/CommandCenter/docs/rules/CC001",
                "defaultConfiguration": {"level": self.SARIF_LEVEL_WARNING},
            },
            {
                "id": "CC002",
                "name": "MissingDependency",
                "shortDescription": {"text": "Missing recommended dependency"},
                "fullDescription": {
                    "text": "A recommended dependency is missing that could improve the project."
                },
                "helpUri": "https://github.com/PerformanceSuite/CommandCenter/docs/rules/CC002",
                "defaultConfiguration": {"level": self.SARIF_LEVEL_NOTE},
            },
            {
                "id": "CC003",
                "name": "ResearchGap",
                "shortDescription": {"text": "Research gap identified"},
                "fullDescription": {
                    "text": "An area requiring research or evaluation has been identified."
                },
                "helpUri": "https://github.com/PerformanceSuite/CommandCenter/docs/rules/CC003",
                "defaultConfiguration": {"level": self.SARIF_LEVEL_NOTE},
            },
            {
                "id": "CC004",
                "name": "TechnologyDetection",
                "shortDescription": {"text": "Technology detected"},
                "fullDescription": {
                    "text": "A technology or framework has been detected in the project."
                },
                "helpUri": "https://github.com/PerformanceSuite/CommandCenter/docs/rules/CC004",
                "defaultConfiguration": {"level": self.SARIF_LEVEL_NONE},
            },
        ]
        return rules

    def _create_invocation(self) -> Dict[str, Any]:
        """
        Create SARIF invocation object.

        Returns:
            SARIF invocation dictionary
        """
        return {
            "executionSuccessful": True,
            "endTimeUtc": self.analyzed_at,
            "workingDirectory": {"uri": self._path_to_uri(self.project_path)},
        }

    def _create_artifacts(self) -> List[Dict[str, Any]]:
        """
        Create SARIF artifacts (files analyzed).

        Returns:
            List of SARIF artifact dictionaries
        """
        artifacts = []

        # Add package manager files
        metrics = self._get_metrics()
        if "files" in metrics:
            for file_info in metrics.get("files", []):
                if isinstance(file_info, dict) and "path" in file_info:
                    artifacts.append({
                        "location": {"uri": self._path_to_uri(file_info["path"])},
                        "length": file_info.get("size", -1),
                    })

        # If no specific files, add project root
        if not artifacts:
            artifacts.append({
                "location": {"uri": self._path_to_uri(self.project_path)},
            })

        return artifacts

    def _create_results(self) -> List[Dict[str, Any]]:
        """
        Create SARIF results (findings).

        Returns:
            List of SARIF result dictionaries
        """
        results = []

        # Add technology detections
        for tech in self._get_technology_list():
            results.append(self._create_technology_result(tech))

        # Add dependency issues
        for dep in self._get_dependency_list():
            if self._is_outdated_dependency(dep):
                results.append(self._create_dependency_result(dep))

        # Add research gaps
        for gap in self._get_research_gaps_list():
            results.append(self._create_research_gap_result(gap))

        return results

    def _create_technology_result(self, tech: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create SARIF result for detected technology.

        Args:
            tech: Technology dictionary

        Returns:
            SARIF result dictionary
        """
        name = tech.get("name", "Unknown Technology")
        version = tech.get("version", "unknown")
        confidence = tech.get("confidence", 50)

        return {
            "ruleId": "CC004",
            "level": self.SARIF_LEVEL_NONE,
            "kind": self.SARIF_KIND_PASS,
            "message": {
                "text": f"Detected {name} {version} (confidence: {confidence}%)"
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": self._path_to_uri(self.project_path)
                        },
                    }
                }
            ],
            "fingerprints": {
                "commandCenter/v1": self._generate_fingerprint(f"tech-{name}-{version}")
            },
            "properties": {
                "technology": name,
                "version": version,
                "confidence": confidence,
                "category": tech.get("category", "unknown"),
            },
        }

    def _create_dependency_result(self, dep: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create SARIF result for outdated dependency.

        Args:
            dep: Dependency dictionary

        Returns:
            SARIF result dictionary
        """
        name = dep.get("name", "Unknown Dependency")
        current = dep.get("current_version", "unknown")
        latest = dep.get("latest_version", "unknown")

        return {
            "ruleId": "CC001",
            "level": self.SARIF_LEVEL_WARNING,
            "kind": self.SARIF_KIND_REVIEW,
            "message": {
                "text": f"Dependency '{name}' is outdated: {current} → {latest} available"
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": self._path_to_uri(dep.get("file", "package.json"))
                        },
                    }
                }
            ],
            "fingerprints": {
                "commandCenter/v1": self._generate_fingerprint(f"dep-{name}-{current}")
            },
            "properties": {
                "dependency": name,
                "currentVersion": current,
                "latestVersion": latest,
                "severity": dep.get("severity", "medium"),
            },
        }

    def _create_research_gap_result(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create SARIF result for research gap.

        Args:
            gap: Research gap dictionary

        Returns:
            SARIF result dictionary
        """
        title = gap.get("title", "Research Gap")
        description = gap.get("description", "No description")
        category = gap.get("category", "general")

        return {
            "ruleId": "CC003",
            "level": self.SARIF_LEVEL_NOTE,
            "kind": self.SARIF_KIND_REVIEW,
            "message": {"text": f"Research Gap: {title} - {description}"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": self._path_to_uri(self.project_path)
                        },
                    }
                }
            ],
            "fingerprints": {
                "commandCenter/v1": self._generate_fingerprint(f"gap-{title}")
            },
            "properties": {
                "category": category,
                "priority": gap.get("priority", 3),
            },
        }

    def _is_outdated_dependency(self, dep: Dict[str, Any]) -> bool:
        """
        Check if dependency is outdated.

        Args:
            dep: Dependency dictionary

        Returns:
            True if outdated
        """
        return dep.get("is_outdated", False) or dep.get("needs_update", False)

    def _path_to_uri(self, path: str) -> str:
        """
        Convert file path to URI format.

        Args:
            path: File path

        Returns:
            URI string
        """
        # Remove leading slashes and convert to URI
        clean_path = path.lstrip("/")
        return f"file:///{clean_path}"

    def _generate_fingerprint(self, key: str) -> str:
        """
        Generate stable fingerprint for result.

        Fingerprints help track issues across runs.

        Args:
            key: Unique key for this result

        Returns:
            Fingerprint hash
        """
        return hashlib.sha256(key.encode()).hexdigest()[:16]


def export_to_sarif(project_analysis: Dict[str, Any], tool_name: str = "CommandCenter") -> Dict[str, Any]:
    """
    Convenience function to export analysis to SARIF format.

    Args:
        project_analysis: Analysis results dictionary
        tool_name: Name of the analysis tool

    Returns:
        SARIF document as dictionary
    """
    exporter = SARIFExporter(project_analysis, tool_name)
    return exporter.export()
