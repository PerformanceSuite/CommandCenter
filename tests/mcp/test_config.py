"""Tests for Configuration Validation"""

import pytest
import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

# Add MCP base to path
mcp_base = Path(__file__).parent.parent.parent / '.commandcenter' / 'mcp-servers' / 'base'
sys.path.insert(0, str(mcp_base))

from config_validator import ConfigValidator


class TestConfigValidator:
    """Test ConfigValidator class"""

    def setup_method(self):
        """Set up test fixtures"""
        # Create minimal valid configuration
        self.valid_config = {
            "project": {
                "id": "test-project",
                "name": "Test Project",
                "type": "fullstack"
            },
            "mcp_servers": {
                "project_manager": {
                    "enabled": True,
                    "transport": "stdio"
                }
            }
        }

        # Create validator (without schema file for unit tests)
        self.validator = ConfigValidator()
        self.validator.schema = {
            "required": ["project", "mcp_servers"],
            "properties": {}
        }

    def test_validate_valid_config(self):
        """Test validating a valid configuration"""
        is_valid, errors = self.validator.validate(self.valid_config)

        assert is_valid
        assert len(errors) == 0

    def test_validate_missing_required_keys(self):
        """Test validation with missing required keys"""
        invalid_config = {
            "project": {"id": "test", "name": "Test", "type": "fullstack"}
            # Missing mcp_servers
        }

        is_valid, errors = self.validator.validate(invalid_config)

        assert not is_valid
        assert len(errors) > 0
        assert any('mcp_servers' in error for error in errors)

    def test_validate_project_missing_fields(self):
        """Test validation with missing project fields"""
        config = {
            "project": {
                "id": "test"
                # Missing name and type
            },
            "mcp_servers": {}
        }

        is_valid, errors = self.validator.validate(config)

        assert not is_valid
        assert any('name' in error for error in errors)
        assert any('type' in error for error in errors)

    def test_validate_invalid_project_type(self):
        """Test validation with invalid project type"""
        config = {
            "project": {
                "id": "test",
                "name": "Test",
                "type": "invalid_type"
            },
            "mcp_servers": {}
        }

        is_valid, errors = self.validator.validate(config)

        assert not is_valid
        assert any('Invalid project type' in error for error in errors)

    def test_validate_invalid_project_id(self):
        """Test validation with invalid project ID"""
        config = {
            "project": {
                "id": "invalid id with spaces!",
                "name": "Test",
                "type": "fullstack"
            },
            "mcp_servers": {}
        }

        is_valid, errors = self.validator.validate(config)

        assert not is_valid
        assert any('Project ID' in error for error in errors)

    def test_validate_invalid_transport(self):
        """Test validation with invalid transport"""
        config = {
            "project": {"id": "test", "name": "Test", "type": "fullstack"},
            "mcp_servers": {
                "project_manager": {
                    "enabled": True,
                    "transport": "invalid_transport"
                }
            }
        }

        is_valid, errors = self.validator.validate(config)

        assert not is_valid
        assert any('Invalid transport' in error for error in errors)

    def test_validate_invalid_port(self):
        """Test validation with invalid port"""
        config = {
            "project": {"id": "test", "name": "Test", "type": "fullstack"},
            "mcp_servers": {
                "project_manager": {
                    "enabled": True,
                    "port": 99999  # Invalid port
                }
            }
        }

        is_valid, errors = self.validator.validate(config)

        assert not is_valid
        assert any('Invalid port' in error for error in errors)

    def test_validate_invalid_ai_provider(self):
        """Test validation with invalid AI provider"""
        config = {
            "project": {"id": "test", "name": "Test", "type": "fullstack"},
            "mcp_servers": {},
            "ai_providers": {
                "primary": "invalid_provider"
            }
        }

        is_valid, errors = self.validator.validate(config)

        assert not is_valid
        assert any('Invalid primary provider' in error for error in errors)

    def test_validate_invalid_fallback_providers(self):
        """Test validation with invalid fallback providers"""
        config = {
            "project": {"id": "test", "name": "Test", "type": "fullstack"},
            "mcp_servers": {},
            "ai_providers": {
                "primary": "anthropic",
                "fallback": ["invalid_provider"]
            }
        }

        is_valid, errors = self.validator.validate(config)

        assert not is_valid
        assert any('Invalid fallback provider' in error for error in errors)

    def test_validate_file_success(self):
        """Test validating a configuration file"""
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            config_path = f.name

        try:
            is_valid, errors = self.validator.validate_file(config_path)
            assert is_valid
            assert len(errors) == 0
        finally:
            Path(config_path).unlink()

    def test_validate_file_not_found(self):
        """Test validating non-existent file"""
        is_valid, errors = self.validator.validate_file('/nonexistent/config.json')

        assert not is_valid
        assert len(errors) > 0
        assert any('not found' in error for error in errors)

    def test_validate_file_invalid_json(self):
        """Test validating file with invalid JSON"""
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('not valid json')
            config_path = f.name

        try:
            is_valid, errors = self.validator.validate_file(config_path)
            assert not is_valid
            assert any('Invalid JSON' in error for error in errors)
        finally:
            Path(config_path).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
