#!/usr/bin/env python3
"""
Quick validation script for Session 33 security fixes.

Validates that all 5 critical security fixes are working correctly.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

print("=" * 70)
print("SECURITY VALIDATION - Session 33 Fixes")
print("=" * 70)
print()

passed = 0
failed = 0


# Test 1: Session Fixation Prevention
print("Test 1: Session Fixation Prevention")
print("-" * 70)
try:
    from app.mcp.connection import MCPSession

    # Create two sessions
    session1 = MCPSession(client_info={"test": "1"})
    session2 = MCPSession(client_info={"test": "2"})

    # Check session IDs are generated
    assert session1.session_id is not None, "Session ID should be generated"
    assert session2.session_id is not None, "Session ID should be generated"

    # Check they're unique
    assert session1.session_id != session2.session_id, "Session IDs should be unique"

    # Check they're UUIDs (36 chars with dashes)
    assert len(session1.session_id) == 36, "Session ID should be UUID format"
    assert "-" in session1.session_id, "Session ID should contain dashes"

    # Try to provide session_id (should fail)
    try:
        bad_session = MCPSession(session_id="attacker-id", client_info={})
        print("  ❌ FAILED: session_id parameter should not be accepted")
        failed += 1
    except TypeError:
        print("  ✅ PASSED: Session IDs are server-generated only")
        print(f"     Session 1 ID: {session1.session_id[:8]}...")
        print(f"     Session 2 ID: {session2.session_id[:8]}...")
        passed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    failed += 1

print()

# Test 2: Error Message Sanitization
print("Test 2: Error Message Sanitization")
print("-" * 70)
try:
    import asyncio
    from app.mcp.protocol import MCPProtocolHandler

    async def test_error_sanitization():
        handler = MCPProtocolHandler()

        # Create exception with sensitive data
        sensitive_error = ValueError("Database password=secret123 user=admin host=internal-db")

        # Handle exception
        response = await handler.handle_exception(sensitive_error, request_id=1)

        # Check sanitization
        assert response.error is not None, "Should return error response"
        assert response.error.message == "Internal server error", "Should use generic message"
        assert "password" not in response.error.message.lower(), "Should not leak password"
        assert "secret123" not in str(response.error.data), "Should not leak sensitive data"
        assert response.error.data.get("type") == "ValueError", "Should include error type only"

        return True

    result = asyncio.run(test_error_sanitization())
    print("  ✅ PASSED: Error messages are sanitized")
    print("     Exception details not leaked to clients")
    print("     Only error type exposed, not message")
    passed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    failed += 1

print()

# Test 3: Path Traversal Protection
print("Test 3: Path Traversal Protection")
print("-" * 70)
try:
    from app.routers.projects import validate_project_path
    import tempfile

    # Test 1: Reject path outside allowed dirs
    try:
        validate_project_path("/etc/passwd")
        print("  ❌ FAILED: Should reject /etc/passwd")
        failed += 1
    except ValueError as e:
        if "not within allowed" in str(e).lower():
            print("  ✅ PASSED: Rejects paths outside allowed directories")
            print(f"     Rejected: /etc/passwd")
        else:
            raise

    # Test 2: Reject non-existent paths
    try:
        validate_project_path("/tmp/nonexistent-12345")
        print("  ❌ FAILED: Should reject non-existent paths")
        failed += 1
    except ValueError as e:
        if "does not exist" in str(e).lower():
            print("  ✅ PASSED: Rejects non-existent paths")
        else:
            raise

    # Test 3: Accept valid paths (if allowed)
    with tempfile.TemporaryDirectory() as tmpdir:
        from app.routers import projects
        original_dirs = projects.ALLOWED_ANALYSIS_DIRS

        try:
            # Temporarily allow tmpdir
            projects.ALLOWED_ANALYSIS_DIRS = [Path(tmpdir)]

            # Create valid project
            project_dir = Path(tmpdir) / "test-project"
            project_dir.mkdir()

            validated = validate_project_path(str(project_dir))
            assert validated == project_dir.resolve()
            print("  ✅ PASSED: Accepts valid paths within allowed directories")

        finally:
            projects.ALLOWED_ANALYSIS_DIRS = original_dirs

    passed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    failed += 1

print()

# Test 4: CLI Setup.py
print("Test 4: CLI Setup.py Installation")
print("-" * 70)
try:
    setup_path = Path(__file__).parent.parent / "backend" / "setup.py"

    assert setup_path.exists(), "setup.py not found"
    print("  ✅ PASSED: setup.py exists")

    setup_content = setup_path.read_text()

    assert "entry_points" in setup_content, "No entry_points defined"
    assert "console_scripts" in setup_content, "No console_scripts defined"
    assert "commandcenter=cli.commandcenter:cli" in setup_content, "No CLI entry point"
    print("  ✅ PASSED: Entry point configured")
    print("     Entry: commandcenter=cli.commandcenter:cli")

    assert "keyring" in setup_content, "keyring dependency missing"
    print("  ✅ PASSED: keyring dependency included")

    passed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    failed += 1

print()

# Test 5: Secure Token Storage
print("Test 5: Secure Token Storage (Keyring)")
print("-" * 70)
try:
    from unittest.mock import patch, MagicMock
    from cli.config import Config

    # Test save_token
    with patch('keyring.set_password') as mock_set:
        config = Config()
        config.save_token("test-token-123")

        mock_set.assert_called_once_with("commandcenter", "api_token", "test-token-123")
        print("  ✅ PASSED: Tokens saved to system keyring")

    # Test load_token
    with patch('keyring.get_password', return_value="stored-token") as mock_get:
        config = Config()
        token = config.load_token()

        assert token == "stored-token"
        mock_get.assert_called_once_with("commandcenter", "api_token")
        print("  ✅ PASSED: Tokens loaded from system keyring")

    # Test token not in config file
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config = Config()
        config.save(config_path)

        config_content = config_path.read_text()
        assert "token" not in config_content.lower()
        print("  ✅ PASSED: Tokens NOT saved to config file")
        print("     Config file does not contain token data")

    passed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    failed += 1

print()

# Summary
print("=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
print(f"✅ Passed: {passed}/5")
print(f"❌ Failed: {failed}/5")
print()

if failed == 0:
    print("🎉 ALL SECURITY FIXES VALIDATED SUCCESSFULLY!")
    print()
    print("Security Posture:")
    print("  • Session fixation attacks: PREVENTED")
    print("  • Information disclosure: PREVENTED")
    print("  • Path traversal attacks: PREVENTED")
    print("  • CLI installation: READY")
    print("  • Credential exposure: PREVENTED")
    sys.exit(0)
else:
    print("⚠️  SOME SECURITY VALIDATIONS FAILED")
    print("   Please review failures above")
    sys.exit(1)
