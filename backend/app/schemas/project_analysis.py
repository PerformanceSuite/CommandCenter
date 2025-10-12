"""
Project analysis schemas for request/response validation
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DependencyType(str, Enum):
    """Dependency type enum"""

    RUNTIME = "runtime"
    DEV = "dev"
    BUILD = "build"
    PEER = "peer"


class Dependency(BaseModel):
    """Dependency information"""

    name: str = Field(..., description="Package/dependency name")
    version: str = Field(..., description="Current version")
    type: DependencyType = Field(..., description="Dependency type")
    language: str = Field(..., description="Programming language")
    latest_version: Optional[str] = Field(None, description="Latest available version")
    is_outdated: bool = Field(default=False, description="Whether version is outdated")
    has_vulnerabilities: bool = Field(
        default=False, description="Whether package has known vulnerabilities"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")


class DetectedTechnology(BaseModel):
    """Detected technology information"""

    name: str = Field(..., description="Technology name")
    category: str = Field(
        ..., description="Category (framework, database, build_tool, etc.)"
    )
    version: Optional[str] = Field(None, description="Detected version")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    file_path: str = Field(..., description="File where detected")


class CodeMetrics(BaseModel):
    """Code structure metrics"""

    total_files: int = Field(..., ge=0, description="Total number of files")
    lines_of_code: int = Field(..., ge=0, description="Total lines of code")
    languages: Dict[str, int] = Field(
        default_factory=dict, description="Lines of code per language"
    )
    complexity_score: float = Field(..., ge=0.0, description="Code complexity score")
    architecture_pattern: Optional[str] = Field(
        None, description="Detected architecture pattern"
    )
    cyclomatic_complexity: Optional[float] = Field(
        None,
        ge=0.0,
        description="Average cyclomatic complexity per file (AST-based, Python only)",
    )
    total_functions: Optional[int] = Field(
        None, ge=0, description="Total number of functions detected"
    )
    total_classes: Optional[int] = Field(
        None, ge=0, description="Total number of classes detected"
    )


class ResearchGap(BaseModel):
    """Identified research gap"""

    technology: str = Field(..., description="Technology name")
    current_version: str = Field(..., description="Current version in use")
    latest_version: str = Field(..., description="Latest available version")
    severity: str = Field(
        ..., description="Severity level (critical, high, medium, low)"
    )
    description: str = Field(..., description="Gap description")
    suggested_task: str = Field(..., description="Suggested research task")
    estimated_effort: str = Field(
        ..., description="Estimated effort (e.g., '1-2 hours', '1-2 days')"
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level"""
        valid_severities = ["critical", "high", "medium", "low"]
        if v.lower() not in valid_severities:
            raise ValueError(f"Severity must be one of: {', '.join(valid_severities)}")
        return v.lower()


class ProjectAnalysisRequest(BaseModel):
    """Request schema for project analysis"""

    project_path: str = Field(..., description="Absolute path to project root")
    use_cache: bool = Field(
        default=True, description="Use cached analysis if available"
    )


class GitHubAnalysisRequest(BaseModel):
    """Request schema for GitHub repository analysis"""

    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    branch: Optional[str] = Field(None, description="Branch to analyze (default: main)")
    use_cache: bool = Field(
        default=True, description="Use cached analysis if available"
    )


class ProjectAnalysisResult(BaseModel):
    """Complete project analysis result"""

    project_path: str = Field(..., description="Analyzed project path")
    analyzed_at: datetime = Field(..., description="Analysis timestamp")
    dependencies: List[Dependency] = Field(
        default_factory=list, description="Detected dependencies"
    )
    technologies: List[DetectedTechnology] = Field(
        default_factory=list, description="Detected technologies"
    )
    code_metrics: CodeMetrics = Field(..., description="Code structure metrics")
    research_gaps: List[ResearchGap] = Field(
        default_factory=list, description="Identified research gaps"
    )
    analysis_duration_ms: int = Field(..., ge=0, description="Analysis duration in ms")


class ProjectAnalysisResponse(BaseModel):
    """API response for project analysis"""

    id: int = Field(..., description="Analysis ID")
    project_path: str = Field(..., description="Analyzed project path")
    analyzed_at: datetime = Field(..., description="Analysis timestamp")
    dependencies: List[Dependency] = Field(
        default_factory=list, description="Detected dependencies"
    )
    technologies: List[DetectedTechnology] = Field(
        default_factory=list, description="Detected technologies"
    )
    code_metrics: CodeMetrics = Field(..., description="Code structure metrics")
    research_gaps: List[ResearchGap] = Field(
        default_factory=list, description="Identified research gaps"
    )
    analysis_duration_ms: int = Field(..., ge=0, description="Analysis duration in ms")
    analysis_version: str = Field(..., description="Analysis version for cache")

    model_config = {"from_attributes": True}


class AnalysisStatistics(BaseModel):
    """Analysis statistics"""

    total_analyses: int = Field(..., ge=0, description="Total number of analyses")
    unique_projects: int = Field(..., ge=0, description="Unique projects analyzed")
    total_dependencies: int = Field(..., ge=0, description="Total dependencies tracked")
    total_technologies: int = Field(
        ..., ge=0, description="Total technologies detected"
    )
    total_gaps: int = Field(..., ge=0, description="Total research gaps identified")
    critical_gaps: int = Field(..., ge=0, description="Critical severity gaps")
    high_gaps: int = Field(..., ge=0, description="High severity gaps")
    outdated_dependencies: int = Field(
        ..., ge=0, description="Outdated dependencies count"
    )


class GenerateTasksRequest(BaseModel):
    """Request schema for generating research tasks from gaps"""

    analysis_id: int = Field(..., description="Analysis ID")
    severity_threshold: Optional[str] = Field(
        None, description="Only generate tasks for gaps at or above this severity"
    )
    auto_assign: bool = Field(
        default=False, description="Automatically assign tasks to users"
    )
