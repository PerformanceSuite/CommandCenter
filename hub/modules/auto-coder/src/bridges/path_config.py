"""Safe path configuration for external dependencies.

Provides a controlled way to locate and validate external paths,
avoiding magic parent directory traversal and ensuring existence checks.
"""
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Marker file that must exist in auto-claude-core for validation
AUTO_CLAUDE_MARKER = "pyproject.toml"


def get_auto_claude_path() -> Path | None:
    """Get the path to auto-claude-core using configuration or discovery.

    Resolution order:
    1. AUTO_CLAUDE_PATH environment variable (explicit configuration)
    2. Relative discovery from this package's location

    Returns:
        Path to auto-claude-core if found and valid, None otherwise.
    """
    # Prefer explicit configuration
    env_path = os.environ.get("AUTO_CLAUDE_PATH")
    if env_path:
        path = Path(env_path)
        if _validate_auto_claude_path(path):
            return path
        logger.warning(
            f"AUTO_CLAUDE_PATH={env_path} is set but path is invalid or missing marker"
        )

    # Fall back to relative discovery
    # This module is at: hub/modules/auto-coder/src/bridges/path_config.py
    # auto-claude-core is at: integrations/auto-claude-core
    module_root = Path(__file__).resolve().parent
    project_root = module_root.parents[4]  # Go up to CommandCenter root
    discovered_path = project_root / "integrations" / "auto-claude-core"

    if _validate_auto_claude_path(discovered_path):
        return discovered_path

    logger.debug(
        f"auto-claude-core not found at {discovered_path}. "
        "Set AUTO_CLAUDE_PATH environment variable to configure."
    )
    return None


def _validate_auto_claude_path(path: Path) -> bool:
    """Validate that path is a legitimate auto-claude-core installation.

    Checks for existence and presence of marker file to prevent
    using arbitrary directories.
    """
    if not path.exists():
        return False
    if not path.is_dir():
        return False
    # Check for marker file as basic integrity verification
    marker = path / AUTO_CLAUDE_MARKER
    return marker.exists()


def configure_auto_claude_imports() -> bool:
    """Configure sys.path for auto-claude-core imports if available.

    This should be called once at module initialization. It validates
    the path before modifying sys.path.

    Returns:
        True if auto-claude-core was found and configured, False otherwise.
    """
    path = get_auto_claude_path()
    if path is None:
        return False

    path_str = str(path)
    if path_str not in sys.path:
        # Insert at position 1 (after script directory) rather than 0
        # to avoid overriding the running script's imports
        sys.path.insert(1, path_str)
        logger.debug(f"Added {path_str} to sys.path")

    return True


# Module-level flag to track if configuration has been attempted
_configured = False


def ensure_auto_claude_configured() -> bool:
    """Ensure auto-claude-core imports are configured (idempotent).

    Safe to call multiple times; will only configure once.
    """
    global _configured
    if not _configured:
        _configured = configure_auto_claude_imports()
    return _configured
