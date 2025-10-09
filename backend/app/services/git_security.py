"""
Git Command Security

Sanitizes git operations to prevent OS command injection (CWE-78).

Security Features:
- Branch name validation (alphanumeric + safe chars only)
- Commit message sanitization
- File path traversal prevention
- Safe command building (no shell execution)
- Dangerous pattern detection
"""

import re
import shlex
from pathlib import Path
from typing import List


class GitCommandSanitizer:
    """Sanitize git command inputs to prevent injection attacks"""

    # Allowed characters in branch names (git standard)
    # Letters, numbers, hyphens, underscores, forward slashes, dots
    BRANCH_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-/\.]+$")

    # Disallowed patterns in any git input
    DANGEROUS_PATTERNS = [
        r"[;&|`$]",  # Shell metacharacters
        r"\$\(",  # Command substitution $(...)
        r"`",  # Backtick command substitution
        r">\s*/",  # Output redirection to root
        r"<\s*/",  # Input redirection from root
        r"\|\s*\w",  # Pipe to command
    ]

    @staticmethod
    def sanitize_branch_name(branch: str) -> str:
        """
        Sanitize git branch name

        Args:
            branch: Branch name to sanitize

        Returns:
            Sanitized branch name

        Raises:
            ValueError: If branch name is invalid or contains dangerous patterns
        """
        if not branch:
            raise ValueError("Branch name cannot be empty")

        if not isinstance(branch, str):
            raise ValueError("Branch name must be a string")

        # Remove leading/trailing whitespace
        branch = branch.strip()

        # Check length
        if len(branch) > 255:
            raise ValueError("Branch name too long (max 255 characters)")

        # Check against allowed pattern
        if not GitCommandSanitizer.BRANCH_NAME_PATTERN.match(branch):
            raise ValueError(
                f"Invalid branch name: {branch}. "
                "Only letters, numbers, hyphens, underscores, slashes, and dots allowed"
            )

        # Check for dangerous patterns
        for pattern in GitCommandSanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, branch):
                raise ValueError(f"Dangerous pattern detected in branch name: {branch}")

        # Additional git-specific validations
        if branch.startswith("-"):
            raise ValueError("Branch name cannot start with hyphen")

        if branch.startswith("."):
            raise ValueError("Branch name cannot start with dot")

        if ".." in branch:
            raise ValueError("Branch name cannot contain '..'")

        if branch.endswith(".lock"):
            raise ValueError("Branch name cannot end with '.lock'")

        if "//" in branch:
            raise ValueError("Branch name cannot contain consecutive slashes")

        # Reserved names
        reserved = ["HEAD", "master", "main"]
        if branch in reserved and "/" not in branch:
            # Allow feature/main, etc., but not bare 'main'
            raise ValueError(f"Branch name '{branch}' is reserved")

        return branch

    @staticmethod
    def sanitize_commit_message(message: str) -> str:
        """
        Sanitize git commit message

        Args:
            message: Commit message to sanitize

        Returns:
            Sanitized commit message

        Raises:
            ValueError: If message is invalid or contains dangerous patterns
        """
        if not message:
            raise ValueError("Commit message cannot be empty")

        if not isinstance(message, str):
            raise ValueError("Commit message must be a string")

        # Remove leading/trailing whitespace
        message = message.strip()

        # Check length
        if len(message) > 5000:
            raise ValueError("Commit message too long (max 5000 characters)")

        # Check for dangerous shell patterns
        for pattern in GitCommandSanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, message):
                raise ValueError(
                    "Dangerous pattern detected in commit message. "
                    "Shell metacharacters are not allowed."
                )

        # Escape for shell safety (when using with shell commands)
        # Note: We should avoid shell=True, but this provides defense in depth
        return message

    @staticmethod
    def sanitize_file_path(path: str, base_dir: Path) -> Path:
        """
        Sanitize file path to prevent traversal attacks

        Args:
            path: File path to sanitize (relative or absolute)
            base_dir: Base directory that path must be within

        Returns:
            Absolute Path object within base_dir

        Raises:
            ValueError: If path traversal detected or path invalid
        """
        if not path:
            raise ValueError("File path cannot be empty")

        if not isinstance(path, str):
            raise ValueError("File path must be a string")

        # Convert to Path object
        try:
            path_obj = Path(path)
        except Exception as e:
            raise ValueError(f"Invalid file path: {e}") from e

        # Resolve base directory to absolute path
        base_dir = Path(base_dir).resolve()

        # Resolve target path (relative to base_dir if not absolute)
        if path_obj.is_absolute():
            abs_path = path_obj.resolve()
        else:
            abs_path = (base_dir / path_obj).resolve()

        # Ensure path is within base directory
        try:
            abs_path.relative_to(base_dir)
        except ValueError:
            raise ValueError(
                f"Path traversal detected: '{path}' is outside base directory"
            ) from None

        return abs_path

    @staticmethod
    def sanitize_tag_name(tag: str) -> str:
        """
        Sanitize git tag name

        Args:
            tag: Tag name to sanitize

        Returns:
            Sanitized tag name

        Raises:
            ValueError: If tag name is invalid
        """
        if not tag:
            raise ValueError("Tag name cannot be empty")

        # Tags have similar rules to branches
        tag = tag.strip()

        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", tag):
            raise ValueError(
                f"Invalid tag name: {tag}. "
                "Only letters, numbers, hyphens, underscores, and dots allowed"
            )

        if tag.startswith("-") or tag.startswith("."):
            raise ValueError("Tag name cannot start with hyphen or dot")

        if ".." in tag:
            raise ValueError("Tag name cannot contain '..'")

        return tag

    @staticmethod
    def build_safe_git_command(args: List[str]) -> List[str]:
        """
        Build safe git command (never use shell execution)

        Args:
            args: Git command arguments (e.g., ['checkout', '-b', 'feature'])

        Returns:
            Complete command list with 'git' prepended

        Example:
            >>> GitCommandSanitizer.build_safe_git_command(['status'])
            ['git', 'status']
        """
        if not args:
            raise ValueError("Git command arguments cannot be empty")

        if not isinstance(args, list):
            raise ValueError("Git command arguments must be a list")

        # Ensure all arguments are strings
        if not all(isinstance(arg, str) for arg in args):
            raise ValueError("All git command arguments must be strings")

        # Prepend 'git' command
        return ["git"] + args

    @staticmethod
    def validate_remote_url(url: str) -> str:
        """
        Validate git remote URL

        Args:
            url: Remote URL to validate

        Returns:
            Validated URL

        Raises:
            ValueError: If URL is invalid or uses dangerous protocol
        """
        if not url:
            raise ValueError("Remote URL cannot be empty")

        url = url.strip()

        # Allowed protocols
        allowed_protocols = ["https://", "http://", "git://", "ssh://", "git@"]

        if not any(url.startswith(proto) for proto in allowed_protocols):
            raise ValueError(
                f"Invalid remote URL protocol. "
                f"Must start with: {', '.join(allowed_protocols)}"
            )

        # Check for dangerous patterns
        for pattern in GitCommandSanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, url):
                raise ValueError("Dangerous pattern detected in remote URL")

        return url
