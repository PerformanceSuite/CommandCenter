"""
MCP utilities - logging, validation, and exceptions.

Provides common utilities used throughout the MCP implementation.
"""

import logging
from typing import Any, Dict, Optional


# Configure MCP logging
def get_mcp_logger(name: str) -> logging.Logger:
    """
    Get logger for MCP components.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(f"mcp.{name}")
    return logger


# Custom exceptions for MCP protocol
class MCPException(Exception):
    """
    Base exception for MCP errors.

    Attributes:
        code: Error code
        message: Error message
        data: Optional additional error data
    """

    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        """
        Initialize MCP exception.

        Args:
            code: Error code
            message: Error message
            data: Optional additional error data
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class ParseError(MCPException):
    """JSON parsing error (-32700)."""

    def __init__(self, message: str = "Parse error", data: Optional[Any] = None):
        """Initialize parse error."""
        super().__init__(-32700, message, data)


class InvalidRequestError(MCPException):
    """Invalid request structure error (-32600)."""

    def __init__(self, message: str = "Invalid Request", data: Optional[Any] = None):
        """Initialize invalid request error."""
        super().__init__(-32600, message, data)


class MethodNotFoundError(MCPException):
    """Method not found error (-32601)."""

    def __init__(
        self, method: str, message: Optional[str] = None, data: Optional[Any] = None
    ):
        """
        Initialize method not found error.

        Args:
            method: Method name that was not found
            message: Optional custom message
            data: Optional additional error data
        """
        self.method = method
        msg = message or f"Method '{method}' not found"
        super().__init__(-32601, msg, data)


class InvalidParamsError(MCPException):
    """Invalid method parameters error (-32602)."""

    def __init__(self, message: str = "Invalid params", data: Optional[Any] = None):
        """Initialize invalid params error."""
        super().__init__(-32602, message, data)


class InternalError(MCPException):
    """Internal error (-32603)."""

    def __init__(self, message: str = "Internal error", data: Optional[Any] = None):
        """Initialize internal error."""
        super().__init__(-32603, message, data)


class ResourceNotFoundError(MCPException):
    """Resource not found error (-32001)."""

    def __init__(
        self, uri: str, message: Optional[str] = None, data: Optional[Any] = None
    ):
        """
        Initialize resource not found error.

        Args:
            uri: Resource URI that was not found
            message: Optional custom message
            data: Optional additional error data
        """
        self.uri = uri
        msg = message or f"Resource '{uri}' not found"
        super().__init__(-32001, msg, data)


class ToolNotFoundError(MCPException):
    """Tool not found error (-32002)."""

    def __init__(
        self, tool_name: str, message: Optional[str] = None, data: Optional[Any] = None
    ):
        """
        Initialize tool not found error.

        Args:
            tool_name: Tool name that was not found
            message: Optional custom message
            data: Optional additional error data
        """
        self.tool_name = tool_name
        msg = message or f"Tool '{tool_name}' not found"
        super().__init__(-32002, msg, data)


class PromptNotFoundError(MCPException):
    """Prompt not found error (-32003)."""

    def __init__(
        self,
        prompt_name: str,
        message: Optional[str] = None,
        data: Optional[Any] = None,
    ):
        """
        Initialize prompt not found error.

        Args:
            prompt_name: Prompt name that was not found
            message: Optional custom message
            data: Optional additional error data
        """
        self.prompt_name = prompt_name
        msg = message or f"Prompt '{prompt_name}' not found"
        super().__init__(-32003, msg, data)


# Validation utilities
def validate_uri(uri: str) -> bool:
    """
    Validate resource URI format.

    Args:
        uri: URI to validate

    Returns:
        True if valid, False otherwise
    """
    if not uri or not isinstance(uri, str):
        return False
    # Basic validation - URIs should have a scheme
    return ":" in uri and len(uri.split(":", 1)[0]) > 0


def validate_tool_name(name: str) -> bool:
    """
    Validate tool name format.

    Args:
        name: Tool name to validate

    Returns:
        True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    # Tool names should be valid identifiers
    return name.replace("_", "").replace("-", "").isalnum()


def validate_prompt_name(name: str) -> bool:
    """
    Validate prompt name format.

    Args:
        name: Prompt name to validate

    Returns:
        True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    # Prompt names should be valid identifiers
    return name.replace("_", "").replace("-", "").isalnum()


def format_error_data(error: Exception) -> Dict[str, Any]:
    """
    Format exception data for error responses.

    Args:
        error: Exception to format

    Returns:
        Dictionary with error details
    """
    return {
        "type": type(error).__name__,
        "message": str(error),
        "details": getattr(error, "__dict__", {}),
    }
