"""MCP Protocol Implementation

Implements the Model Context Protocol (MCP) JSON-RPC 2.0 message format.
Handles protocol-level message parsing, validation, and formatting.
"""

import json
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum


class MCPMethod(str, Enum):
    """Standard MCP methods"""
    # Server initialization
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"

    # Tool operations
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"

    # Resource operations
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"

    # Prompt operations
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"

    # Notifications
    PROGRESS = "notifications/progress"
    MESSAGE = "notifications/message"

    # Lifecycle
    PING = "ping"
    SHUTDOWN = "shutdown"


@dataclass
class MCPRequest:
    """MCP JSON-RPC 2.0 Request"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPRequest':
        """Create MCPRequest from dictionary"""
        return cls(
            jsonrpc=data.get('jsonrpc', '2.0'),
            method=data.get('method', ''),
            params=data.get('params'),
            id=data.get('id')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'jsonrpc': self.jsonrpc,
            'method': self.method,
        }
        if self.params is not None:
            result['params'] = self.params
        if self.id is not None:
            result['id'] = self.id
        return result

    def is_notification(self) -> bool:
        """Check if request is a notification (no id)"""
        return self.id is None


@dataclass
class MCPError:
    """MCP JSON-RPC 2.0 Error"""
    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'code': self.code,
            'message': self.message,
        }
        if self.data is not None:
            result['data'] = self.data
        return result


class MCPErrorCode:
    """Standard MCP error codes"""
    # JSON-RPC 2.0 standard errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP-specific errors
    TOOL_NOT_FOUND = -32001
    TOOL_EXECUTION_ERROR = -32002
    RESOURCE_NOT_FOUND = -32003
    RESOURCE_READ_ERROR = -32004
    PROMPT_NOT_FOUND = -32005

    # Server errors
    SERVER_NOT_INITIALIZED = -32010
    SERVER_ALREADY_INITIALIZED = -32011
    CAPABILITY_NOT_SUPPORTED = -32012


@dataclass
class MCPResponse:
    """MCP JSON-RPC 2.0 Response"""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[MCPError] = None

    @classmethod
    def success(cls, id: Any, result: Any) -> 'MCPResponse':
        """Create success response"""
        return cls(id=id, result=result)

    @classmethod
    def error_response(cls, id: Any, code: int, message: str, data: Any = None) -> 'MCPResponse':
        """Create error response"""
        return cls(id=id, error=MCPError(code=code, message=message, data=data))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {'jsonrpc': self.jsonrpc}
        if self.id is not None:
            result['id'] = self.id
        if self.error is not None:
            result['error'] = self.error.to_dict()
        elif self.result is not None:
            result['result'] = self.result
        return result


class MCPProtocol:
    """MCP Protocol Handler

    Handles parsing and formatting of MCP protocol messages.
    Validates JSON-RPC 2.0 compliance and MCP method signatures.
    """

    def __init__(self):
        self.initialized = False
        self.client_info: Optional[Dict[str, Any]] = None
        self.server_info: Dict[str, Any] = {
            'name': 'base-mcp-server',
            'version': '1.0.0'
        }
        self.capabilities: Dict[str, Any] = {
            'tools': {},
            'resources': {},
            'prompts': {}
        }

    def parse_message(self, message: str) -> MCPRequest:
        """Parse incoming JSON-RPC message

        Args:
            message: Raw JSON string

        Returns:
            MCPRequest object

        Raises:
            ValueError: If message is invalid JSON or not valid JSON-RPC 2.0
        """
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        # Validate JSON-RPC 2.0 structure
        if not isinstance(data, dict):
            raise ValueError("Message must be a JSON object")

        if data.get('jsonrpc') != '2.0':
            raise ValueError("Invalid jsonrpc version, must be '2.0'")

        if 'method' not in data:
            raise ValueError("Missing required field: method")

        return MCPRequest.from_dict(data)

    def format_response(self, response: MCPResponse) -> str:
        """Format response as JSON string

        Args:
            response: MCPResponse object

        Returns:
            JSON string
        """
        return json.dumps(response.to_dict())

    def validate_params(self, params: Any, required_fields: List[str]) -> None:
        """Validate request parameters

        Args:
            params: Parameters to validate
            required_fields: List of required field names

        Raises:
            ValueError: If validation fails
        """
        if params is None and required_fields:
            raise ValueError(f"Missing required parameters: {required_fields}")

        if not isinstance(params, dict):
            raise ValueError("Parameters must be an object")

        missing = [f for f in required_fields if f not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request

        Args:
            params: Initialization parameters including client info

        Returns:
            Server info and capabilities

        Raises:
            ValueError: If already initialized
        """
        if self.initialized:
            raise ValueError("Server already initialized")

        self.client_info = params.get('clientInfo', {})
        self.initialized = True

        return {
            'protocolVersion': '2024-11-05',
            'serverInfo': self.server_info,
            'capabilities': self.capabilities
        }

    def set_server_info(self, name: str, version: str) -> None:
        """Set server information

        Args:
            name: Server name
            version: Server version
        """
        self.server_info = {
            'name': name,
            'version': version
        }

    def set_capabilities(self, capabilities: Dict[str, Any]) -> None:
        """Set server capabilities

        Args:
            capabilities: Capabilities dictionary
        """
        self.capabilities = capabilities

    def require_initialized(self) -> None:
        """Check if server is initialized

        Raises:
            ValueError: If server not initialized
        """
        if not self.initialized:
            raise ValueError("Server not initialized")
