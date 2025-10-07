"""Configuration Validator

Validates CommandCenter configuration against JSON schema.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from .utils import get_logger

logger = get_logger(__name__)


class ConfigValidator:
    """Configuration validator"""

    def __init__(self, schema_path: str = None):
        """Initialize validator

        Args:
            schema_path: Path to config.schema.json (optional)
        """
        if schema_path:
            self.schema_path = Path(schema_path)
        else:
            # Default to .commandcenter/config.schema.json
            from .utils import find_commandcenter_root
            commandcenter_root = find_commandcenter_root()
            self.schema_path = commandcenter_root / 'config.schema.json'

        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema

        Returns:
            Schema dictionary

        Raises:
            FileNotFoundError: If schema file not found
        """
        if not self.schema_path.exists():
            logger.warning(f"Schema file not found: {self.schema_path}")
            return {}

        with open(self.schema_path, 'r') as f:
            return json.load(f)

    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration against schema

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        # Check required top-level keys
        required_keys = self.schema.get('required', [])
        for key in required_keys:
            if key not in config:
                errors.append(f"Missing required top-level key: {key}")

        # Validate project section
        if 'project' in config:
            project_errors = self._validate_project(config['project'])
            errors.extend(project_errors)

        # Validate mcp_servers section
        if 'mcp_servers' in config:
            server_errors = self._validate_mcp_servers(config['mcp_servers'])
            errors.extend(server_errors)

        # Validate ai_providers section
        if 'ai_providers' in config:
            provider_errors = self._validate_ai_providers(config['ai_providers'])
            errors.extend(provider_errors)

        is_valid = len(errors) == 0
        return is_valid, errors

    def _validate_project(self, project: Dict[str, Any]) -> List[str]:
        """Validate project configuration

        Args:
            project: Project configuration

        Returns:
            List of error messages
        """
        errors = []

        # Required fields
        required = ['id', 'name', 'type']
        for field in required:
            if field not in project:
                errors.append(f"Missing required project field: {field}")

        # Validate project type
        if 'type' in project:
            valid_types = ['fullstack', 'backend', 'frontend', 'library', 'tool']
            if project['type'] not in valid_types:
                errors.append(
                    f"Invalid project type: {project['type']}. "
                    f"Must be one of: {valid_types}"
                )

        # Validate ID format
        if 'id' in project:
            project_id = project['id']
            if not isinstance(project_id, str) or not project_id:
                errors.append("Project ID must be a non-empty string")
            elif not project_id.replace('-', '').replace('_', '').isalnum():
                errors.append(
                    "Project ID must contain only alphanumeric characters, "
                    "hyphens, and underscores"
                )

        return errors

    def _validate_mcp_servers(self, servers: Dict[str, Any]) -> List[str]:
        """Validate MCP servers configuration

        Args:
            servers: MCP servers configuration

        Returns:
            List of error messages
        """
        errors = []

        if not isinstance(servers, dict):
            errors.append("mcp_servers must be an object")
            return errors

        # Validate each server config
        for server_name, server_config in servers.items():
            if not isinstance(server_config, dict):
                errors.append(f"Server config for '{server_name}' must be an object")
                continue

            # Validate transport
            if 'transport' in server_config:
                valid_transports = ['stdio', 'http', 'websocket']
                if server_config['transport'] not in valid_transports:
                    errors.append(
                        f"Invalid transport for '{server_name}': "
                        f"{server_config['transport']}. "
                        f"Must be one of: {valid_transports}"
                    )

            # Validate port
            if 'port' in server_config:
                port = server_config['port']
                if port is not None:
                    if not isinstance(port, int) or port < 1 or port > 65535:
                        errors.append(
                            f"Invalid port for '{server_name}': {port}. "
                            f"Must be between 1 and 65535 or null"
                        )

        return errors

    def _validate_ai_providers(self, providers: Dict[str, Any]) -> List[str]:
        """Validate AI providers configuration

        Args:
            providers: AI providers configuration

        Returns:
            List of error messages
        """
        errors = []

        valid_providers = ['anthropic', 'openai', 'google', 'local']

        # Validate primary provider
        if 'primary' in providers:
            if providers['primary'] not in valid_providers:
                errors.append(
                    f"Invalid primary provider: {providers['primary']}. "
                    f"Must be one of: {valid_providers}"
                )

        # Validate fallback providers
        if 'fallback' in providers:
            if not isinstance(providers['fallback'], list):
                errors.append("fallback must be an array")
            else:
                for provider in providers['fallback']:
                    if provider not in valid_providers:
                        errors.append(
                            f"Invalid fallback provider: {provider}. "
                            f"Must be one of: {valid_providers}"
                        )

        return errors

    def validate_file(self, config_path: str) -> Tuple[bool, List[str]]:
        """Validate configuration file

        Args:
            config_path: Path to configuration file

        Returns:
            Tuple of (is_valid, errors)
        """
        config_path = Path(config_path)

        if not config_path.exists():
            return False, [f"Configuration file not found: {config_path}"]

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON in configuration file: {e}"]

        return self.validate(config)


def validate_config(config_path: str = None) -> bool:
    """Validate configuration file

    Args:
        config_path: Path to config.json (optional)

    Returns:
        True if valid

    Raises:
        ValueError: If configuration is invalid
    """
    validator = ConfigValidator()

    if config_path:
        is_valid, errors = validator.validate_file(config_path)
    else:
        from .utils import load_config
        config = load_config()
        is_valid, errors = validator.validate(config)

    if not is_valid:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    logger.info("Configuration validated successfully")
    return True
