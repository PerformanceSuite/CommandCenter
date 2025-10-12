"""
Configuration management for CommandCenter CLI.

Handles loading, saving, and managing CLI configuration from ~/.commandcenter/config.yaml.
"""

from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    """API connection configuration."""

    url: str = Field(
        default="http://localhost:8000", description="CommandCenter API URL"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class AuthConfig(BaseModel):
    """Authentication configuration."""

    token: Optional[str] = Field(default=None, description="API authentication token")


class OutputConfig(BaseModel):
    """Output formatting configuration."""

    format: str = Field(
        default="table", description="Output format (table, json, yaml)"
    )
    color: str = Field(default="auto", description="Color mode (auto, always, never)")
    verbose: bool = Field(default=False, description="Enable verbose output")


class AnalysisConfig(BaseModel):
    """Analysis defaults configuration."""

    cache: bool = Field(default=True, description="Enable analysis caching")
    create_tasks: bool = Field(default=False, description="Auto-create research tasks")
    export_path: str = Field(
        default="./analysis-results", description="Export directory"
    )


class AgentsConfig(BaseModel):
    """Agent orchestration configuration."""

    max_concurrent: int = Field(default=3, description="Maximum concurrent agents")
    retry_failed: bool = Field(default=True, description="Auto-retry failed agents")
    log_level: str = Field(default="info", description="Agent log level")


class Config(BaseModel):
    """CommandCenter CLI configuration."""

    api: APIConfig = Field(default_factory=APIConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)

    @classmethod
    def load(cls, path: Path) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            path: Path to configuration file

        Returns:
            Config: Loaded configuration object
        """
        if not path.exists():
            # Create default config
            config = cls()
            config.save(path)
            return config

        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        return cls(**data)

    def save(self, path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            path: Path to save configuration file
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(
                self.model_dump(),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

    def get(self, key: str):
        """
        Get nested config value by dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'api.url')

        Returns:
            Configuration value

        Raises:
            AttributeError: If key path is invalid
        """
        parts = key.split(".")
        value = self
        for part in parts:
            value = getattr(value, part)
        return value

    def set(self, key: str, value) -> None:
        """
        Set nested config value by dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'api.url')
            value: Value to set

        Raises:
            AttributeError: If key path is invalid
        """
        parts = key.split(".")
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    @classmethod
    def get_default_config_path(cls) -> Path:
        """
        Get default configuration file path.

        Returns:
            Path: Default config path (~/.commandcenter/config.yaml)
        """
        return Path.home() / ".commandcenter" / "config.yaml"
