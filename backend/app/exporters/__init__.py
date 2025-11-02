"""
Export system for analysis results.

Supports multiple export formats:
- SARIF: Static Analysis Results Interchange Format (GitHub code scanning)
- HTML: Self-contained interactive reports
- CSV: Spreadsheet-friendly data
- Markdown: GitHub-ready documentation (implemented separately)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from datetime import datetime


class BaseExporter(ABC):
    """
    Abstract base class for all exporters.

    Provides common functionality for formatting analysis results
    into different export formats.
    """

    def __init__(self, project_analysis: Dict[str, Any]):
        """
        Initialize exporter with analysis data.

        Args:
            project_analysis: Complete analysis results dictionary
        """
        self.analysis = project_analysis
        self.project_path = project_analysis.get("project_path", "unknown")
        self.analyzed_at = project_analysis.get("analyzed_at", datetime.utcnow().isoformat())
        self.detected_technologies = project_analysis.get("detected_technologies", {})
        self.dependencies = project_analysis.get("dependencies", {})
        self.code_metrics = project_analysis.get("code_metrics", {})
        self.research_gaps = project_analysis.get("research_gaps", {})

    @abstractmethod
    def export(self) -> Any:
        """
        Export analysis to target format.

        Returns:
            Exported data in target format
        """

    def _get_technology_list(self) -> List[Dict[str, Any]]:
        """
        Extract normalized technology list from analysis.

        Returns:
            List of technology dictionaries
        """
        if isinstance(self.detected_technologies, dict):
            return self.detected_technologies.get("technologies", [])
        elif isinstance(self.detected_technologies, list):
            return self.detected_technologies
        return []

    def _get_dependency_list(self) -> List[Dict[str, Any]]:
        """
        Extract normalized dependency list from analysis.

        Returns:
            List of dependency dictionaries
        """
        if isinstance(self.dependencies, dict):
            return self.dependencies.get("dependencies", [])
        elif isinstance(self.dependencies, list):
            return self.dependencies
        return []

    def _get_metrics(self) -> Dict[str, Any]:
        """
        Extract normalized metrics from analysis.

        Returns:
            Dictionary of code metrics
        """
        return self.code_metrics if isinstance(self.code_metrics, dict) else {}

    def _get_research_gaps_list(self) -> List[Dict[str, Any]]:
        """
        Extract normalized research gaps from analysis.

        Returns:
            List of research gap dictionaries
        """
        if isinstance(self.research_gaps, dict):
            return self.research_gaps.get("gaps", [])
        elif isinstance(self.research_gaps, list):
            return self.research_gaps
        return []


class ExportFormat:
    """Export format constants."""

    SARIF = "sarif"
    HTML = "html"
    CSV = "csv"
    MARKDOWN = "markdown"
    JSON = "json"


class ExportError(Exception):
    """Base exception for export errors."""



class UnsupportedFormatError(ExportError):
    """Raised when export format is not supported."""



class ExportDataError(ExportError):
    """Raised when export data is invalid or incomplete."""



__all__ = [
    "BaseExporter",
    "ExportFormat",
    "ExportError",
    "UnsupportedFormatError",
    "ExportDataError",
]
