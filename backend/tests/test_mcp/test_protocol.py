"""Tests for MCP protocol handler."""

import json

import pytest

from app.mcp.protocol import JSONRPCError, JSONRPCRequest, JSONRPCResponse, MCPProtocolHandler
from app.mcp.utils import InvalidRequestError, MethodNotFoundError, ParseError


class TestJSONRPCRequest:
    """Tests for JSONRPCRequest model."""

    def test_valid_request(self):
        """Test creating valid JSON-RPC request."""
        req = JSONRPCRequest(id=1, method="test/method", params={"key": "value"})
        assert req.jsonrpc == "2.0"
        assert req.id == 1
        assert req.method == "test/method"
        assert req.params == {"key": "value"}

    def test_notification_request(self):
        """Test notification (no ID)."""
        req = JSONRPCRequest(method="test/notification")
        assert req.id is None
        assert req.is_notification()

    def test_request_with_string_id(self):
        """Test request with string ID."""
        req = JSONRPCRequest(id="abc-123", method="test/method")
        assert req.id == "abc-123"

    def test_empty_method_validation(self):
        """Test that empty method name is rejected."""
        with pytest.raises(Exception):
            JSONRPCRequest(id=1, method="")

    def test_params_optional(self):
        """Test that params is optional."""
        req = JSONRPCRequest(id=1, method="test/method")
        assert req.params is None


class TestJSONRPCResponse:
    """Tests for JSONRPCResponse model."""

    def test_success_response(self):
        """Test success response."""
        resp = JSONRPCResponse(id=1, result={"data": "value"})
        assert resp.jsonrpc == "2.0"
        assert resp.id == 1
        assert resp.result == {"data": "value"}
        assert resp.error is None

    def test_error_response(self):
        """Test error response."""
        error = JSONRPCError(code=-32600, message="Invalid Request")
        resp = JSONRPCResponse(id=1, error=error)
        assert resp.id == 1
        assert resp.error.code == -32600
        assert resp.error.message == "Invalid Request"
        assert resp.result is None


class TestMCPProtocolHandler:
    """Tests for MCPProtocolHandler."""

    @pytest.fixture
    def handler(self):
        """Create protocol handler instance."""
        return MCPProtocolHandler()

    @pytest.mark.asyncio
    async def test_parse_valid_request(self, handler):
        """Test parsing valid JSON-RPC request."""
        message = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "resources/list", "params": {}})

        request = await handler.parse_request(message)

        assert request.jsonrpc == "2.0"
        assert request.id == 1
        assert request.method == "resources/list"
        assert request.params == {}

    @pytest.mark.asyncio
    async def test_parse_invalid_json(self, handler):
        """Test parsing invalid JSON."""
        with pytest.raises(ParseError):
            await handler.parse_request("not valid json")

    @pytest.mark.asyncio
    async def test_parse_missing_method(self, handler):
        """Test parsing request without method."""
        message = json.dumps({"jsonrpc": "2.0", "id": 1})

        with pytest.raises(InvalidRequestError):
            await handler.parse_request(message)

    @pytest.mark.asyncio
    async def test_parse_notification(self, handler):
        """Test parsing notification (no ID)."""
        message = json.dumps({"jsonrpc": "2.0", "method": "test/notify", "params": {}})

        request = await handler.parse_request(message)

        assert request.id is None
        assert request.is_notification()

    def test_create_response(self, handler):
        """Test creating success response."""
        response = handler.create_response(1, {"data": "test"})

        assert response.id == 1
        assert response.result == {"data": "test"}
        assert response.error is None

    def test_create_error_response(self, handler):
        """Test creating error response."""
        response = handler.create_error_response(1, -32600, "Invalid Request", "Additional data")

        assert response.id == 1
        assert response.error.code == -32600
        assert response.error.message == "Invalid Request"
        assert response.error.data == "Additional data"
        assert response.result is None

    def test_create_parse_error(self, handler):
        """Test creating parse error."""
        response = handler.create_parse_error()

        assert response.id is None
        assert response.error.code == MCPProtocolHandler.PARSE_ERROR

    def test_create_invalid_request_error(self, handler):
        """Test creating invalid request error."""
        response = handler.create_invalid_request_error(1)

        assert response.id == 1
        assert response.error.code == MCPProtocolHandler.INVALID_REQUEST

    def test_create_method_not_found_error(self, handler):
        """Test creating method not found error."""
        response = handler.create_method_not_found_error(1, "unknown/method")

        assert response.id == 1
        assert response.error.code == MCPProtocolHandler.METHOD_NOT_FOUND
        assert "unknown/method" in response.error.data

    def test_create_invalid_params_error(self, handler):
        """Test creating invalid params error."""
        response = handler.create_invalid_params_error(1, "Missing required param")

        assert response.id == 1
        assert response.error.code == MCPProtocolHandler.INVALID_PARAMS
        assert response.error.data == "Missing required param"

    def test_create_internal_error(self, handler):
        """Test creating internal error."""
        response = handler.create_internal_error(1, "Something went wrong")

        assert response.id == 1
        assert response.error.code == MCPProtocolHandler.INTERNAL_ERROR
        assert response.error.data == "Something went wrong"

    def test_serialize_response(self, handler):
        """Test serializing response to JSON."""
        response = JSONRPCResponse(id=1, result={"test": "data"})
        serialized = handler.serialize_response(response)

        parsed = json.loads(serialized)
        assert parsed["jsonrpc"] == "2.0"
        assert parsed["id"] == 1
        assert parsed["result"] == {"test": "data"}

    @pytest.mark.asyncio
    async def test_handle_parse_error_exception(self, handler):
        """Test handling parse error exception."""
        exception = ParseError("Bad JSON")
        response = await handler.handle_exception(exception)

        assert response.error.code == MCPProtocolHandler.PARSE_ERROR

    @pytest.mark.asyncio
    async def test_handle_invalid_request_exception(self, handler):
        """Test handling invalid request exception."""
        exception = InvalidRequestError("Bad structure")
        response = await handler.handle_exception(exception, 1)

        assert response.id == 1
        assert response.error.code == MCPProtocolHandler.INVALID_REQUEST

    @pytest.mark.asyncio
    async def test_handle_method_not_found_exception(self, handler):
        """Test handling method not found exception."""
        exception = MethodNotFoundError("test/method")
        response = await handler.handle_exception(exception, 1)

        assert response.id == 1
        assert response.error.code == MCPProtocolHandler.METHOD_NOT_FOUND

    @pytest.mark.asyncio
    async def test_handle_generic_exception(self, handler):
        """Test handling unexpected exception."""
        exception = RuntimeError("Unexpected error")
        response = await handler.handle_exception(exception, 1)

        assert response.id == 1
        assert response.error.code == MCPProtocolHandler.INTERNAL_ERROR
