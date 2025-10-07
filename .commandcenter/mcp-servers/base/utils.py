"""MCP Utilities

Logging, configuration loading, and utility functions for MCP servers.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional


# Configure logging
def get_logger(name: str) -> logging.Logger:
    """Get or create a logger

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Create handler that writes to stderr (stdout is for MCP messages)
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from JSON file

    Args:
        config_path: Path to config.json, defaults to .commandcenter/config.json

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    if config_path is None:
        # Default to .commandcenter/config.json in project root
        config_path = find_commandcenter_root() / 'config.json'
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    return config


def find_commandcenter_root() -> Path:
    """Find .commandcenter directory by walking up from current directory

    Returns:
        Path to .commandcenter directory

    Raises:
        FileNotFoundError: If .commandcenter directory not found
    """
    current = Path.cwd()

    # Walk up to find .commandcenter
    for parent in [current] + list(current.parents):
        commandcenter_dir = parent / '.commandcenter'
        if commandcenter_dir.exists() and commandcenter_dir.is_dir():
            return commandcenter_dir

    raise FileNotFoundError(
        "Could not find .commandcenter directory. "
        "Make sure you're running from within a CommandCenter project."
    )


def validate_config_schema(config: Dict[str, Any]) -> bool:
    """Validate configuration against schema

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if valid

    Raises:
        ValueError: If configuration is invalid
    """
    # Required top-level keys
    required_keys = ['project', 'mcp_servers']
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Missing required configuration keys: {missing}")

    # Validate project section
    project = config['project']
    project_required = ['id', 'name', 'type']
    missing = [k for k in project_required if k not in project]
    if missing:
        raise ValueError(f"Missing required project configuration keys: {missing}")

    # Validate mcp_servers section
    if not isinstance(config['mcp_servers'], dict):
        raise ValueError("mcp_servers must be an object")

    return True


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two configuration dictionaries

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        Merged configuration
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def get_project_root() -> Path:
    """Get project root directory (parent of .commandcenter)

    Returns:
        Path to project root
    """
    commandcenter_dir = find_commandcenter_root()
    return commandcenter_dir.parent


class ConfigurationError(Exception):
    """Configuration-related error"""
    pass
