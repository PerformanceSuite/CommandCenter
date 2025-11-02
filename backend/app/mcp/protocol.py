"""
MCP Protocol Handler - JSON-RPC 2.0 implementation.

Handles parsing, validation, and formatting of MCP protocol messages
according to the JSON-RPC 2.0 specification.
"""

import json
import logging
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator

from app.mcp.utils import InvalidRequestError, MCPException, MethodNotFoundError, ParseError

logger = logging.getLogger(__name__)


class JSONRPCRequest(BaseModel):
    """
    JSON-RPC 2.0 request model.

    Attributes:
        jsonrpc: Protocol version (must be "2.0")
        id: Request ID (can be string, number, or None for notifications)
        method: Method name to invoke
        params: Optional parameters (dict or list)
    """

    jsonrpc: str = Field(default="2.0", pattern="^2\\.0$")
    id: Optional[Union[int, str]] = None
    method: str
    params: Optional[Union[Dict[str, Any], list]] = None

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate method name is not empty."""
        if not v or not v.strip():
            raise ValueError("Method name cannot be empty")
        return v

    def is_notification(self) -> bool:
        """Check if this request is a notification (no response expected)."""
        return self.id is None


class JSONRPCError(BaseModel):
    """
    JSON-RPC 2.0 error object.

    Attributes:
        code: Error code (standard codes defined in JSON-RPC 2.0)
        message: Error message
        data: Optional additional error data
    """

    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """
    JSON-RPC 2.0 response model.

    Attributes:
        jsonrpc: Protocol version (must be "2.0")
        id: Request ID (matches the request)
        result: Result data (present on success)
        error: Error object (present on failure)
    """

    jsonrpc: str = Field(default="2.0")
    id: Optional[Union[int, str]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None

    @field_validator("error")
    @classmethod
    def validate_error_result_exclusion(
        cls, v: Optional[JSONRPCError], info
    ) -> Optional[JSONRPCError]:
        """Validate that result and error are mutually exclusive."""
        if v is not None and info.data.get("result") is not None:
            raise ValueError("Response cannot have both result and error")
        return v


class MCPProtocolHandler:
    """
    Handles MCP protocol message parsing and validation.

    This class implements the JSON-RPC 2.0 protocol for MCP communication,
    handling request/response serialization and error handling.
    """

    # Standard JSON-RPC 2.0 error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    def __init__(self):
        """Initialize protocol handler."""
        self._logger = logger

    async def parse_request(self, raw_message: str) -> JSONRPCRequest:
        """
        Parse raw JSON message into JSONRPCRequest.

        Args:
            raw_message: Raw JSON string

        Returns:
            Parsed JSONRPCRequest object

        Raises:
            ParseError: If JSON is invalid
            InvalidRequestError: If request structure is invalid
        """
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError as e:
            self._logger.error(f"JSON parse error: {e}")
            raise ParseError(f"Invalid JSON: {str(e)}")

        try:
            request = JSONRPCRequest.model_validate(data)
            self._logger.debug(f"Parsed request: method={request.method}, id={request.id}")
            return request
        except Exception as e:
            self._logger.error(f"Request validation error: {e}")
            raise InvalidRequestError(f"Invalid request structure: {str(e)}")

    def create_response(
        self, request_id: Optional[Union[int, str]], result: Any
    ) -> JSONRPCResponse:
        """
        Create successful JSON-RPC response.

        Args:
            request_id: ID from the original request
            result: Result data to return

        Returns:
            JSONRPCResponse with result
        """
        response = JSONRPCResponse(id=request_id, result=result)
        self._logger.debug(f"Created success response for request {request_id}")
        return response

    def create_error_response(
        self,
        request_id: Optional[Union[int, str]],
        code: int,
        message: str,
        data: Optional[Any] = None,
    ) -> JSONRPCResponse:
        """
        Create error JSON-RPC response.

        Args:
            request_id: ID from the original request
            code: Error code (standard JSON-RPC or custom)
            message: Error message
            data: Optional additional error data

        Returns:
            JSONRPCResponse with error
        """
        error = JSONRPCError(code=code, message=message, data=data)
        response = JSONRPCResponse(id=request_id, error=error)
        self._logger.debug(f"Created error response for request {request_id}: {code} - {message}")
        return response

    def create_parse_error(self) -> JSONRPCResponse:
        """
        Create parse error response.

        Returns:
            JSONRPCResponse with parse error
        """
        return self.create_error_response(
            None, self.PARSE_ERROR, "Parse error", "Invalid JSON was received"
        )

    def create_invalid_request_error(
        self, request_id: Optional[Union[int, str]] = None
    ) -> JSONRPCResponse:
        """
        Create invalid request error response.

        Args:
            request_id: Optional request ID

        Returns:
            JSONRPCResponse with invalid request error
        """
        return self.create_error_response(
            request_id,
            self.INVALID_REQUEST,
            "Invalid Request",
            "Request validation failed",
        )

    def create_method_not_found_error(
        self, request_id: Optional[Union[int, str]], method: str
    ) -> JSONRPCResponse:
        """
        Create method not found error response.

        Args:
            request_id: Request ID
            method: Method name that was not found

        Returns:
            JSONRPCResponse with method not found error
        """
        return self.create_error_response(
            request_id,
            self.METHOD_NOT_FOUND,
            "Method not found",
            f"Method '{method}' not found",
        )

    def create_invalid_params_error(
        self, request_id: Optional[Union[int, str]], details: str
    ) -> JSONRPCResponse:
        """
        Create invalid params error response.

        Args:
            request_id: Request ID
            details: Details about invalid parameters

        Returns:
            JSONRPCResponse with invalid params error
        """
        return self.create_error_response(
            request_id, self.INVALID_PARAMS, "Invalid params", details
        )

    def create_internal_error(
        self, request_id: Optional[Union[int, str]], details: Optional[str] = None
    ) -> JSONRPCResponse:
        """
        Create internal error response.

        Args:
            request_id: Request ID
            details: Optional error details

        Returns:
            JSONRPCResponse with internal error
        """
        return self.create_error_response(
            request_id, self.INTERNAL_ERROR, "Internal error", details
        )

    def serialize_response(self, response: JSONRPCResponse) -> str:
        """
        Serialize JSONRPCResponse to JSON string.

        Args:
            response: Response object to serialize

        Returns:
            JSON string
        """
        return response.model_dump_json(exclude_none=True)

    async def handle_exception(
        self, exception: Exception, request_id: Optional[Union[int, str]] = None
    ) -> JSONRPCResponse:
        """
        Convert exception to appropriate JSON-RPC error response.

        Args:
            exception: Exception that occurred
            request_id: Optional request ID

        Returns:
            JSONRPCResponse with appropriate error
        """
        if isinstance(exception, ParseError):
            return self.create_parse_error()
        elif isinstance(exception, InvalidRequestError):
            return self.create_invalid_request_error(request_id)
        elif isinstance(exception, MethodNotFoundError):
            return self.create_method_not_found_error(
                request_id, getattr(exception, "method", "unknown")
            )
        elif isinstance(exception, MCPException):
            return self.create_error_response(
                request_id, exception.code, str(exception), exception.data
            )
        else:
            # Unexpected error
            # Security: Log full exception details for debugging, but only return
            # error type to client to prevent information disclosure
            self._logger.exception(f"Unexpected error handling request {request_id}")
            error_data = {"type": type(exception).__name__}
            return self.create_error_response(
                request_id, self.INTERNAL_ERROR, "Internal server error", error_data
            )
