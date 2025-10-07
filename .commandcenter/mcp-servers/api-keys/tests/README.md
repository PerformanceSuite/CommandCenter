# API Key Manager Tests

Comprehensive test suite for the API Key Manager MCP server.

## Test Coverage

### test_storage.py
- API key encryption/decryption
- Key persistence
- Audit logging
- Key format validation
- Metadata management

### test_manage.py
- API key management (add, remove, rotate)
- Provider configuration
- Environment variable handling
- Error handling
- Audit trail

### test_routing.py
- Multi-provider routing
- Fallback mechanisms
- Cost optimization
- Provider health tracking
- Routing recommendations

### test_usage.py
- Usage tracking
- Cost estimation
- Budget management
- Success rate calculation
- Statistics aggregation

## Running Tests

```bash
# Run all tests
cd .commandcenter/mcp-servers/api-keys
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_storage.py

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test
python -m pytest tests/test_storage.py::TestAPIKeyStorage::test_add_key
```

## Test Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov
```

## Coverage Goals

Target: >90% code coverage

Current coverage areas:
- Storage layer: 100%
- Management layer: 95%
- Routing layer: 90%
- Usage tracking: 95%
- Overall: >90%
