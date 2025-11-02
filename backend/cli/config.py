"""
Configuration management for CommandCenter CLI.

Handles loading, saving, and managing CLI configuration from ~/.commandcenter/config.yaml.

Security: API tokens are stored securely in the system keyring, not in plain text config files.
"""

from pathlib import Path
from typing import Optional
import yaml
import keyring
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class APIConfig(BaseModel):
    """API connection configuration."""

    url: str = Field(default="http://localhost:8000", description="CommandCenter API URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class AuthConfig(BaseModel):
    """
    Authentication configuration.

    Security Note: API tokens are stored in the system keyring for secure storage.
    The token field is excluded from config file serialization.
    """

    # Note: token field removed - stored in keyring instead
    # Use Config.save_token() and Config.load_token() methods

    @staticmethod
    def save_token(token: str) -> None:
        """
        Save API token securely to system keyring.

        Args:
            token: API authentication token

        Raises:
            keyring.errors.KeyringError: If keyring storage fails
        """
        try:
            keyring.set_password("commandcenter", "api_token", token)
            logger.info("API token saved securely to system keyring")
        except Exception as e:
            logger.error(f"Failed to save token to keyring: {e}")
            raise

    @staticmethod
    def load_token() -> Optional[str]:
        """
        Load API token from system keyring.

        Returns:
            str or None: API token if found, None otherwise

        Raises:
            keyring.errors.KeyringError: If keyring access fails
        """
        try:
            token = keyring.get_password("commandcenter", "api_token")
            if token:
                logger.debug("API token loaded from system keyring")
            return token
        except Exception as e:
            logger.error(f"Failed to load token from keyring: {e}")
            return None

    @staticmethod
    def delete_token() -> bool:
        """
        Delete API token from system keyring.

        Returns:
            bool: True if deleted, False if token didn't exist

        Raises:
            keyring.errors.KeyringError: If keyring access fails
        """
        try:
            keyring.delete_password("commandcenter", "api_token")
            logger.info("API token deleted from system keyring")
            return True
        except keyring.errors.PasswordDeleteError:
            logger.debug("No token found in keyring to delete")
            return False
        except Exception as e:
            logger.error(f"Failed to delete token from keyring: {e}")
            raise


class OutputConfig(BaseModel):
    """Output formatting configuration."""

    format: str = Field(default="table", description="Output format (table, json, yaml)")
    color: str = Field(default="auto", description="Color mode (auto, always, never)")
    verbose: bool = Field(default=False, description="Enable verbose output")


class AnalysisConfig(BaseModel):
    """Analysis defaults configuration."""

    cache: bool = Field(default=True, description="Enable analysis caching")
    create_tasks: bool = Field(default=False, description="Auto-create research tasks")
    export_path: str = Field(default="./analysis-results", description="Export directory")


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

        Security Note: API tokens are NOT saved to the YAML file. They are stored
        separately in the system keyring using save_token() method.

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

    # Token management convenience methods (delegate to AuthConfig)

    def save_token(self, token: str) -> None:
        """
        Save API token securely to system keyring.

        Convenience wrapper for AuthConfig.save_token().

        Args:
            token: API authentication token

        Example:
            config = Config.load(config_path)
            config.save_token("sk-...")
        """
        AuthConfig.save_token(token)

    def load_token(self) -> Optional[str]:
        """
        Load API token from system keyring.

        Convenience wrapper for AuthConfig.load_token().

        Returns:
            str or None: API token if found, None otherwise

        Example:
            config = Config.load(config_path)
            token = config.load_token()
        """
        return AuthConfig.load_token()

    def delete_token(self) -> bool:
        """
        Delete API token from system keyring.

        Convenience wrapper for AuthConfig.delete_token().

        Returns:
            bool: True if deleted, False if token didn't exist

        Example:
            config = Config.load(config_path)
            config.delete_token()
        """
        return AuthConfig.delete_token()

    def has_token(self) -> bool:
        """
        Check if API token exists in system keyring.

        Returns:
            bool: True if token exists, False otherwise

        Example:
            config = Config.load(config_path)
            if not config.has_token():
                print("Please configure your API token")
        """
        return self.load_token() is not None
