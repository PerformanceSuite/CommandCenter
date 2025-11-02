"""
Research gap identification from dependencies and technologies
"""

from typing import List

from packaging import version as version_pkg

from app.schemas.project_analysis import (
    Dependency,
    DetectedTechnology,
    ResearchGap,
)


class ResearchGapAnalyzer:
    """
    Identify outdated dependencies and research gaps.

    Analyzes dependencies to find upgrade opportunities and
    suggest research tasks with priority scoring.
    """

    # Severity thresholds (major version behind)
    SEVERITY_THRESHOLDS = {
        "critical": 3,  # 3+ major versions behind
        "high": 2,  # 2 major versions behind
        "medium": 1,  # 1 major version behind
        "low": 0,  # Minor/patch version behind
    }

    # Effort estimation by severity
    EFFORT_ESTIMATES = {
        "critical": "2-4 weeks",
        "high": "1-2 weeks",
        "medium": "3-5 days",
        "low": "1-2 days",
    }

    async def analyze(
        self,
        dependencies: List[Dependency],
        technologies: List[DetectedTechnology],
    ) -> List[ResearchGap]:
        """
        Identify research gaps.

        Args:
            dependencies: Detected dependencies with versions
            technologies: Detected technologies

        Returns:
            List of research gaps with priorities
        """
        gaps = []

        # Analyze each dependency
        for dep in dependencies:
            if dep.latest_version and dep.is_outdated:
                gap = self._create_gap_from_dependency(dep)
                if gap:
                    gaps.append(gap)

        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gaps.sort(key=lambda g: severity_order.get(g.severity, 4))

        return gaps

    def _create_gap_from_dependency(self, dep: Dependency) -> ResearchGap:
        """
        Create research gap from outdated dependency.

        Args:
            dep: Dependency object

        Returns:
            ResearchGap object or None
        """
        if not dep.latest_version or not dep.is_outdated:
            return None

        # Calculate severity
        severity = self._calculate_severity(dep.version, dep.latest_version)

        # Generate description
        description = self._generate_description(dep, severity)

        # Generate suggested task
        suggested_task = self._generate_suggested_task(dep, severity)

        return ResearchGap(
            technology=f"{dep.name} ({dep.language})",
            current_version=dep.version,
            latest_version=dep.latest_version,
            severity=severity,
            description=description,
            suggested_task=suggested_task,
            estimated_effort=self.EFFORT_ESTIMATES[severity],
        )

    def _calculate_severity(self, current: str, latest: str) -> str:
        """
        Calculate severity based on version difference.

        Args:
            current: Current version string
            latest: Latest version string

        Returns:
            Severity level (critical, high, medium, low)
        """
        try:
            # Parse versions
            current_ver = version_pkg.parse(current)
            latest_ver = version_pkg.parse(latest)

            # Handle versions without major/minor/patch
            if not hasattr(current_ver, "major") or not hasattr(
                latest_ver, "major"
            ):
                return "low"

            # Calculate major version difference
            major_diff = latest_ver.major - current_ver.major

            # Determine severity
            if major_diff >= self.SEVERITY_THRESHOLDS["critical"]:
                return "critical"
            elif major_diff >= self.SEVERITY_THRESHOLDS["high"]:
                return "high"
            elif major_diff >= self.SEVERITY_THRESHOLDS["medium"]:
                return "high"
            else:
                return "low"

        except Exception:
            # If version parsing fails, default to medium
            return "medium"

    def _generate_description(self, dep: Dependency, severity: str) -> str:
        """
        Generate gap description.

        Args:
            dep: Dependency object
            severity: Severity level

        Returns:
            Description string
        """
        descriptions = {
            "critical": (
                f"{dep.name} is severely outdated (v{dep.version} → v{dep.latest_version}). "
                f"Multiple major versions behind with potential security vulnerabilities "
                f"and missing critical features."
            ),
            "high": (
                f"{dep.name} is significantly outdated (v{dep.version} → v{dep.latest_version}). "
                f"Missing important features and bug fixes. Upgrade recommended."
            ),
            "medium": (
                f"{dep.name} is one major version behind (v{dep.version} → v{dep.latest_version}). "
                f"Consider upgrading for new features and improvements."
            ),
            "low": (
                f"{dep.name} has minor updates available (v{dep.version} → v{dep.latest_version}). "
                f"Upgrade when convenient for bug fixes and patches."
            ),
        }

        return descriptions.get(severity, f"{dep.name} is outdated.")

    def _generate_suggested_task(self, dep: Dependency, severity: str) -> str:
        """
        Generate suggested research task.

        Args:
            dep: Dependency object
            severity: Severity level

        Returns:
            Suggested task description
        """
        tasks = {
            "critical": (
                f"URGENT: Research migration path for {dep.name} v{dep.version} → v{dep.latest_version}. "
                f"Review breaking changes, update dependencies, and plan gradual rollout."
            ),
            "high": (
                f"Research {dep.name} upgrade to v{dep.latest_version}. "
                f"Review changelog, assess breaking changes, and create upgrade plan."
            ),
            "medium": (
                f"Evaluate {dep.name} upgrade to v{dep.latest_version}. "
                f"Test compatibility and plan upgrade timeline."
            ),
            "low": (
                f"Schedule minor update for {dep.name} to v{dep.latest_version}. "
                f"Quick compatibility check and update."
            ),
        }

        return tasks.get(
            severity, f"Upgrade {dep.name} to v{dep.latest_version}"
        )
