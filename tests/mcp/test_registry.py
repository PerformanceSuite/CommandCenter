"""Tests for Tool and Resource Registry"""

import pytest
import sys
from pathlib import Path

# Add MCP base to path
mcp_base = Path(__file__).parent.parent.parent / '.commandcenter' / 'mcp-servers' / 'base'
sys.path.insert(0, str(mcp_base))

from registry import ToolRegistry, ResourceRegistry, ToolParameter, ToolDefinition


class TestToolRegistry:
    """Test ToolRegistry class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.registry = ToolRegistry()

    async def sample_handler(self, param1: str, param2: int = 0) -> dict:
        """Sample async handler for testing"""
        return {'param1': param1, 'param2': param2}

    def test_register_tool(self):
        """Test registering a tool"""
        self.registry.register_tool(
            name='test_tool',
            description='A test tool',
            parameters=[
                ToolParameter(name='param1', type='string', description='First param', required=True)
            ],
            handler=self.sample_handler
        )

        assert self.registry.has_tool('test_tool')
        assert len(self.registry.tools) == 1

    def test_register_duplicate_tool(self):
        """Test registering duplicate tool name"""
        self.registry.register_tool(
            name='test_tool',
            description='First tool',
            parameters=[],
            handler=self.sample_handler
        )

        with pytest.raises(ValueError, match="already registered"):
            self.registry.register_tool(
                name='test_tool',
                description='Duplicate tool',
                parameters=[],
                handler=self.sample_handler
            )

    def test_register_non_async_handler(self):
        """Test registering non-async handler fails"""
        def sync_handler():
            return {}

        with pytest.raises(ValueError, match="must be an async function"):
            self.registry.register_tool(
                name='sync_tool',
                description='Sync tool',
                parameters=[],
                handler=sync_handler
            )

    def test_get_tool(self):
        """Test getting a tool"""
        self.registry.register_tool(
            name='test_tool',
            description='Test',
            parameters=[],
            handler=self.sample_handler
        )

        tool = self.registry.get_tool('test_tool')
        assert tool is not None
        assert tool.name == 'test_tool'

    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool"""
        tool = self.registry.get_tool('nonexistent')
        assert tool is None

    def test_list_tools(self):
        """Test listing tools"""
        self.registry.register_tool(
            name='tool1',
            description='First tool',
            parameters=[
                ToolParameter(name='param1', type='string', description='Param', required=True)
            ],
            handler=self.sample_handler
        )

        tools = self.registry.list_tools()
        assert len(tools) == 1
        assert tools[0]['name'] == 'tool1'
        assert tools[0]['description'] == 'First tool'
        assert 'inputSchema' in tools[0]

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test calling a tool successfully"""
        self.registry.register_tool(
            name='test_tool',
            description='Test',
            parameters=[
                ToolParameter(name='param1', type='string', description='Param', required=True)
            ],
            handler=self.sample_handler
        )

        result = await self.registry.call_tool('test_tool', {'param1': 'value'})
        assert result['param1'] == 'value'

    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self):
        """Test calling non-existent tool"""
        with pytest.raises(ValueError, match="not found"):
            await self.registry.call_tool('nonexistent', {})

    @pytest.mark.asyncio
    async def test_call_tool_missing_params(self):
        """Test calling tool with missing parameters"""
        self.registry.register_tool(
            name='test_tool',
            description='Test',
            parameters=[
                ToolParameter(name='required_param', type='string', description='Required', required=True)
            ],
            handler=self.sample_handler
        )

        with pytest.raises(ValueError, match="Missing required parameters"):
            await self.registry.call_tool('test_tool', {})

    def test_unregister_tool(self):
        """Test unregistering a tool"""
        self.registry.register_tool(
            name='test_tool',
            description='Test',
            parameters=[],
            handler=self.sample_handler
        )

        assert self.registry.has_tool('test_tool')
        self.registry.unregister_tool('test_tool')
        assert not self.registry.has_tool('test_tool')


class TestResourceRegistry:
    """Test ResourceRegistry class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.registry = ResourceRegistry()

    async def sample_resource_handler(self) -> str:
        """Sample async resource handler"""
        return '{"data": "value"}'

    def test_register_resource(self):
        """Test registering a resource"""
        self.registry.register_resource(
            uri='test://resource',
            name='Test Resource',
            description='A test resource',
            mime_type='application/json',
            handler=self.sample_resource_handler
        )

        assert self.registry.has_resource('test://resource')
        assert len(self.registry.resources) == 1

    def test_register_duplicate_resource(self):
        """Test registering duplicate resource URI"""
        self.registry.register_resource(
            uri='test://resource',
            name='First',
            description='First resource',
            mime_type='application/json',
            handler=self.sample_resource_handler
        )

        with pytest.raises(ValueError, match="already registered"):
            self.registry.register_resource(
                uri='test://resource',
                name='Second',
                description='Duplicate resource',
                mime_type='application/json',
                handler=self.sample_resource_handler
            )

    def test_get_resource(self):
        """Test getting a resource"""
        self.registry.register_resource(
            uri='test://resource',
            name='Test',
            description='Test resource',
            mime_type='application/json',
            handler=self.sample_resource_handler
        )

        resource = self.registry.get_resource('test://resource')
        assert resource is not None
        assert resource.uri == 'test://resource'
        assert resource.name == 'Test'

    def test_list_resources(self):
        """Test listing resources"""
        self.registry.register_resource(
            uri='test://resource1',
            name='Resource 1',
            description='First resource',
            mime_type='application/json',
            handler=self.sample_resource_handler
        )

        resources = self.registry.list_resources()
        assert len(resources) == 1
        assert resources[0]['uri'] == 'test://resource1'
        assert resources[0]['name'] == 'Resource 1'
        assert resources[0]['mimeType'] == 'application/json'

    @pytest.mark.asyncio
    async def test_read_resource_success(self):
        """Test reading a resource successfully"""
        self.registry.register_resource(
            uri='test://resource',
            name='Test',
            description='Test resource',
            mime_type='application/json',
            handler=self.sample_resource_handler
        )

        result = await self.registry.read_resource('test://resource')
        assert 'contents' in result
        assert len(result['contents']) == 1
        assert result['contents'][0]['uri'] == 'test://resource'
        assert result['contents'][0]['mimeType'] == 'application/json'

    @pytest.mark.asyncio
    async def test_read_nonexistent_resource(self):
        """Test reading non-existent resource"""
        with pytest.raises(ValueError, match="not found"):
            await self.registry.read_resource('nonexistent://resource')

    def test_unregister_resource(self):
        """Test unregistering a resource"""
        self.registry.register_resource(
            uri='test://resource',
            name='Test',
            description='Test',
            mime_type='application/json',
            handler=self.sample_resource_handler
        )

        assert self.registry.has_resource('test://resource')
        self.registry.unregister_resource('test://resource')
        assert not self.registry.has_resource('test://resource')


class TestToolParameter:
    """Test ToolParameter class"""

    def test_parameter_to_schema(self):
        """Test converting parameter to JSON schema"""
        param = ToolParameter(
            name='test_param',
            type='string',
            description='A test parameter',
            required=True,
            default='default_value'
        )

        schema = param.to_schema()
        assert schema['type'] == 'string'
        assert schema['description'] == 'A test parameter'
        assert schema['default'] == 'default_value'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
