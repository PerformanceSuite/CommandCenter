"""Tests for MCP Protocol Implementation"""

import pytest
import json
import sys
from pathlib import Path

# Add MCP base to path
mcp_base = Path(__file__).parent.parent.parent / '.commandcenter' / 'mcp-servers' / 'base'
sys.path.insert(0, str(mcp_base))

from protocol import (
    MCPProtocol, MCPRequest, MCPResponse, MCPError,
    MCPMethod, MCPErrorCode
)


class TestMCPRequest:
    """Test MCPRequest class"""

    def test_from_dict(self):
        """Test creating request from dictionary"""
        data = {
            'jsonrpc': '2.0',
            'method': 'test_method',
            'params': {'key': 'value'},
            'id': 1
        }
        request = MCPRequest.from_dict(data)

        assert request.jsonrpc == '2.0'
        assert request.method == 'test_method'
        assert request.params == {'key': 'value'}
        assert request.id == 1

    def test_to_dict(self):
        """Test converting request to dictionary"""
        request = MCPRequest(
            method='test_method',
            params={'key': 'value'},
            id=1
        )
        data = request.to_dict()

        assert data['jsonrpc'] == '2.0'
        assert data['method'] == 'test_method'
        assert data['params'] == {'key': 'value'}
        assert data['id'] == 1

    def test_is_notification(self):
        """Test notification detection"""
        # Request with ID is not a notification
        request = MCPRequest(method='test', id=1)
        assert not request.is_notification()

        # Request without ID is a notification
        notification = MCPRequest(method='test')
        assert notification.is_notification()


class TestMCPResponse:
    """Test MCPResponse class"""

    def test_success_response(self):
        """Test creating success response"""
        response = MCPResponse.success(id=1, result={'data': 'value'})

        assert response.jsonrpc == '2.0'
        assert response.id == 1
        assert response.result == {'data': 'value'}
        assert response.error is None

    def test_error_response(self):
        """Test creating error response"""
        response = MCPResponse.error_response(
            id=1,
            code=MCPErrorCode.INTERNAL_ERROR,
            message='Test error'
        )

        assert response.jsonrpc == '2.0'
        assert response.id == 1
        assert response.result is None
        assert response.error is not None
        assert response.error.code == MCPErrorCode.INTERNAL_ERROR
        assert response.error.message == 'Test error'

    def test_to_dict_success(self):
        """Test converting success response to dictionary"""
        response = MCPResponse.success(id=1, result={'data': 'value'})
        data = response.to_dict()

        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 1
        assert data['result'] == {'data': 'value'}
        assert 'error' not in data

    def test_to_dict_error(self):
        """Test converting error response to dictionary"""
        response = MCPResponse.error_response(
            id=1,
            code=-32603,
            message='Internal error'
        )
        data = response.to_dict()

        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 1
        assert 'result' not in data
        assert data['error']['code'] == -32603
        assert data['error']['message'] == 'Internal error'


class TestMCPProtocol:
    """Test MCPProtocol class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.protocol = MCPProtocol()

    def test_initialization(self):
        """Test protocol initialization"""
        assert not self.protocol.initialized
        assert self.protocol.client_info is None
        assert self.protocol.server_info['name'] == 'base-mcp-server'
        assert self.protocol.capabilities is not None

    def test_parse_valid_message(self):
        """Test parsing valid JSON-RPC message"""
        message = json.dumps({
            'jsonrpc': '2.0',
            'method': 'test_method',
            'params': {'key': 'value'},
            'id': 1
        })

        request = self.protocol.parse_message(message)
        assert request.method == 'test_method'
        assert request.params == {'key': 'value'}
        assert request.id == 1

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON"""
        with pytest.raises(ValueError, match="Invalid JSON"):
            self.protocol.parse_message('not valid json')

    def test_parse_invalid_jsonrpc_version(self):
        """Test parsing message with invalid JSON-RPC version"""
        message = json.dumps({
            'jsonrpc': '1.0',
            'method': 'test'
        })

        with pytest.raises(ValueError, match="Invalid jsonrpc version"):
            self.protocol.parse_message(message)

    def test_parse_missing_method(self):
        """Test parsing message without method"""
        message = json.dumps({
            'jsonrpc': '2.0',
            'id': 1
        })

        with pytest.raises(ValueError, match="Missing required field: method"):
            self.protocol.parse_message(message)

    def test_format_response(self):
        """Test formatting response"""
        response = MCPResponse.success(id=1, result={'data': 'value'})
        formatted = self.protocol.format_response(response)

        data = json.loads(formatted)
        assert data['jsonrpc'] == '2.0'
        assert data['id'] == 1
        assert data['result'] == {'data': 'value'}

    def test_validate_params_success(self):
        """Test parameter validation success"""
        params = {'required_field': 'value', 'optional': 'data'}
        self.protocol.validate_params(params, ['required_field'])
        # Should not raise

    def test_validate_params_missing(self):
        """Test parameter validation with missing field"""
        params = {'other_field': 'value'}

        with pytest.raises(ValueError, match="Missing required parameters"):
            self.protocol.validate_params(params, ['required_field'])

    def test_validate_params_none(self):
        """Test parameter validation with None params"""
        with pytest.raises(ValueError, match="Missing required parameters"):
            self.protocol.validate_params(None, ['required_field'])

    def test_handle_initialize(self):
        """Test initialize request handling"""
        params = {
            'clientInfo': {
                'name': 'test-client',
                'version': '1.0.0'
            }
        }

        result = self.protocol.handle_initialize(params)

        assert self.protocol.initialized
        assert self.protocol.client_info == params['clientInfo']
        assert 'protocolVersion' in result
        assert 'serverInfo' in result
        assert 'capabilities' in result

    def test_handle_initialize_already_initialized(self):
        """Test initialize when already initialized"""
        self.protocol.initialized = True

        with pytest.raises(ValueError, match="already initialized"):
            self.protocol.handle_initialize({})

    def test_set_server_info(self):
        """Test setting server info"""
        self.protocol.set_server_info('custom-server', '2.0.0')

        assert self.protocol.server_info['name'] == 'custom-server'
        assert self.protocol.server_info['version'] == '2.0.0'

    def test_set_capabilities(self):
        """Test setting capabilities"""
        caps = {'tools': {'enabled': True}}
        self.protocol.set_capabilities(caps)

        assert self.protocol.capabilities == caps

    def test_require_initialized_success(self):
        """Test require_initialized when initialized"""
        self.protocol.initialized = True
        self.protocol.require_initialized()
        # Should not raise

    def test_require_initialized_failure(self):
        """Test require_initialized when not initialized"""
        with pytest.raises(ValueError, match="not initialized"):
            self.protocol.require_initialized()


class TestMCPError:
    """Test MCPError class"""

    def test_error_creation(self):
        """Test creating error"""
        error = MCPError(
            code=-32603,
            message='Internal error',
            data={'detail': 'Something went wrong'}
        )

        assert error.code == -32603
        assert error.message == 'Internal error'
        assert error.data == {'detail': 'Something went wrong'}

    def test_error_to_dict(self):
        """Test converting error to dictionary"""
        error = MCPError(code=-32603, message='Internal error')
        data = error.to_dict()

        assert data['code'] == -32603
        assert data['message'] == 'Internal error'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
