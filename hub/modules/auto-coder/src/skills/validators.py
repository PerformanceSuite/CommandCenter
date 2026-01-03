"""Shared validators for skill input schemas."""
import os
from pathlib import Path


def get_allowed_base_dir() -> str:
    """Get the base directory that project paths must be within.

    Uses AUTO_CODER_ALLOWED_BASE env var if set, otherwise user home.
    """
    return os.environ.get("AUTO_CODER_ALLOWED_BASE", os.path.expanduser("~"))


def validate_project_dir(v: str) -> str:
    """Validate and resolve a project directory path.

    Ensures the path:
    - Is resolved to an absolute path
    - Is within allowed boundaries (prevents path traversal)
    - Uses the resolved path for all operations

    Args:
        v: The project directory path to validate

    Returns:
        The resolved absolute path

    Raises:
        ValueError: If path is outside allowed boundaries
    """
    # Resolve to absolute path (handles .., ~, symlinks)
    resolved = os.path.realpath(os.path.expanduser(v))
    allowed_base = get_allowed_base_dir()

    # Check path is within allowed boundaries
    if not resolved.startswith(allowed_base):
        raise ValueError(
            f"project_dir must be within {allowed_base}. "
            f"Got: {resolved}"
        )

    return resolved
