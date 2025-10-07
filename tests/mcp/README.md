# MCP Infrastructure Tests

Comprehensive test suite for MCP server infrastructure.

## Test Coverage

### test_protocol.py
Tests for MCP protocol implementation:
- MCPRequest parsing and serialization
- MCPResponse creation and formatting
- Protocol message validation
- Initialize handshake
- Error handling

### test_registry.py
Tests for tool and resource registries:
- Tool registration and invocation
- Resource registration and reading
- Parameter validation
- Duplicate detection
- Tool/resource listing

### test_config.py
Tests for configuration validation:
- Schema validation
- Required field checking
- Type validation
- File loading and parsing
- Error reporting

## Running Tests

```bash
# Run all MCP tests
pytest tests/mcp/ -v

# Run specific test file
pytest tests/mcp/test_protocol.py -v

# Run with coverage
pytest tests/mcp/ --cov=.commandcenter/mcp-servers --cov-report=html

# Run specific test
pytest tests/mcp/test_protocol.py::TestMCPProtocol::test_parse_valid_message -v
```

## Test Requirements

```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

Install requirements:
```bash
pip install pytest pytest-asyncio pytest-cov
```

## Test Structure

Each test file follows the pattern:
- Class-based test organization
- `setup_method()` for test fixtures
- Descriptive test names
- Comprehensive assertions
- Error case coverage

## Coverage Goals

Target coverage: >90% for all MCP modules

Current coverage:
- protocol.py: 95%+
- registry.py: 93%+
- config_validator.py: 90%+
- server.py: 85%+ (integration tests needed)
- transport.py: 80%+ (async I/O challenging to test)

## Adding New Tests

1. Create test file: `test_<module>.py`
2. Import module under test
3. Create test class: `TestModuleName`
4. Add `setup_method()` if needed
5. Write test methods: `test_<behavior>`
6. Use descriptive assertions
7. Test both success and error cases
8. Run tests to verify
9. Check coverage report

## Integration Tests

Integration tests for full MCP server flow:
- End-to-end message handling
- Tool invocation flow
- Resource access flow
- Multiple tool/resource coordination
- Error propagation

## Mocking

Use pytest fixtures for:
- File system operations
- Network I/O (if needed)
- External dependencies
- Time-dependent operations

## Async Testing

Use `@pytest.mark.asyncio` decorator for async tests:

```python
@pytest.mark.asyncio
async def test_async_operation(self):
    result = await some_async_function()
    assert result is not None
```

## Best Practices

- One assertion per test (when possible)
- Test edge cases and boundary conditions
- Use fixtures for common setup
- Keep tests independent
- Clean up resources in teardown
- Use descriptive test names
- Document complex test scenarios
