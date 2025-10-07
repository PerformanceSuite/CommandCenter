"""
Path Security Utilities

Validates file paths to prevent path traversal attacks.

Security Features:
- Path traversal detection and prevention
- Base directory boundary enforcement
- Symlink resolution safety
- Comprehensive path validation
"""

from pathlib import Path
from typing import Union, List
import os


class PathValidator:
    """Validate file paths for security"""

    @staticmethod
    def validate_path(
        path: Union[str, Path], base_dir: Union[str, Path], must_exist: bool = False
    ) -> Path:
        """
        Validate that path is within base directory

        Args:
            path: File or directory path to validate
            base_dir: Base directory that path must be within
            must_exist: If True, raise error if path doesn't exist

        Returns:
            Absolute Path object within base_dir

        Raises:
            ValueError: If path traversal detected, path invalid, or doesn't exist (when required)
        """
        if not path:
            raise ValueError("Path cannot be empty")

        if not base_dir:
            raise ValueError("Base directory cannot be empty")

        # Convert to Path objects
        try:
            path_obj = Path(path)
            base_obj = Path(base_dir)
        except Exception as e:
            raise ValueError(f"Invalid path or base directory: {e}") from e

        # Resolve base directory to absolute path
        base_abs = base_obj.resolve()

        if not base_abs.exists():
            raise ValueError(f"Base directory does not exist: {base_dir}")

        if not base_abs.is_dir():
            raise ValueError(f"Base path is not a directory: {base_dir}")

        # Resolve target path
        if path_obj.is_absolute():
            target_abs = path_obj.resolve()
        else:
            # Resolve relative to base directory
            target_abs = (base_abs / path_obj).resolve()

        # Security check: ensure target is within base directory
        try:
            target_abs.relative_to(base_abs)
        except ValueError:
            raise ValueError(
                f"Path traversal blocked: '{path}' resolves outside base directory '{base_dir}'"
            ) from None

        # Optional existence check
        if must_exist and not target_abs.exists():
            raise ValueError(f"Path does not exist: {path}")

        return target_abs

    @staticmethod
    def validate_paths(
        paths: List[Union[str, Path]],
        base_dir: Union[str, Path],
        must_exist: bool = False,
    ) -> List[Path]:
        """
        Validate multiple paths

        Args:
            paths: List of file or directory paths to validate
            base_dir: Base directory that all paths must be within
            must_exist: If True, raise error if any path doesn't exist

        Returns:
            List of absolute Path objects within base_dir

        Raises:
            ValueError: If any path is invalid
        """
        if not paths:
            return []

        validated = []
        for path in paths:
            validated.append(
                PathValidator.validate_path(path, base_dir, must_exist=must_exist)
            )

        return validated

    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """
        Check if filename is safe (no path separators or dangerous chars)

        Args:
            filename: Filename to check

        Returns:
            True if filename is safe
        """
        if not filename:
            return False

        # Check for path separators
        if os.sep in filename or (os.altsep and os.altsep in filename):
            return False

        # Check for parent directory references
        if filename in ('.', '..'):
            return False

        # Check for null bytes
        if '\0' in filename:
            return False

        # Check for dangerous patterns
        dangerous_patterns = ['..', '/', '\\', '\x00']
        if any(pattern in filename for pattern in dangerous_patterns):
            return False

        return True

    @staticmethod
    def sanitize_filename(filename: str, replacement: str = '_') -> str:
        """
        Sanitize filename by removing/replacing dangerous characters

        Args:
            filename: Filename to sanitize
            replacement: Character to replace dangerous chars with

        Returns:
            Sanitized filename

        Raises:
            ValueError: If filename is empty after sanitization
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Remove path separators
        sanitized = filename.replace(os.sep, replacement)
        if os.altsep:
            sanitized = sanitized.replace(os.altsep, replacement)

        # Remove null bytes
        sanitized = sanitized.replace('\0', '')

        # Remove parent directory references
        sanitized = sanitized.replace('..', replacement)

        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip('. ')

        if not sanitized:
            raise ValueError("Filename is empty after sanitization")

        return sanitized

    @staticmethod
    def get_safe_path_components(path: Union[str, Path]) -> List[str]:
        """
        Get path components, validating each for safety

        Args:
            path: Path to decompose

        Returns:
            List of safe path components

        Raises:
            ValueError: If any component is unsafe
        """
        path_obj = Path(path)
        components = []

        for part in path_obj.parts:
            if part in ('/', '\\'):
                continue  # Skip root separators

            if not PathValidator.is_safe_filename(part):
                raise ValueError(f"Unsafe path component: {part}")

            components.append(part)

        return components

    @staticmethod
    def create_safe_path(base_dir: Union[str, Path], *components: str) -> Path:
        """
        Create safe path by joining components

        Args:
            base_dir: Base directory
            *components: Path components to join

        Returns:
            Safe absolute path

        Raises:
            ValueError: If any component is unsafe or result is outside base
        """
        base = Path(base_dir).resolve()

        # Validate each component
        for component in components:
            if not PathValidator.is_safe_filename(component):
                raise ValueError(f"Unsafe path component: {component}")

        # Build path
        result = base
        for component in components:
            result = result / component

        # Validate final path is within base
        return PathValidator.validate_path(result, base)
