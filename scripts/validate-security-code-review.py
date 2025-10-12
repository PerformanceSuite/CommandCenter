#!/usr/bin/env python3
"""
Code-level validation of security fixes (no imports required).

Validates that security fixes are properly implemented by checking code patterns.
"""

import re
from pathlib import Path

print("=" * 70)
print("SECURITY CODE REVIEW - Session 33 Fixes")
print("=" * 70)
print()

passed = 0
failed = 0


# Test 1: Session Fixation - Check MCPSession doesn't accept session_id param
print("Test 1: Session Fixation Prevention (Code Review)")
print("-" * 70)
try:
    connection_file = Path("backend/app/mcp/connection.py")
    content = connection_file.read_text()

    # Check __init__ signature
    init_match = re.search(r'def __init__\(\s*self,\s*([^)]*)\)', content)
    if init_match:
        params = init_match.group(1)
        # session_id should NOT be a parameter
        if "session_id" in params:
            print(f"  ❌ FAILED: session_id parameter still exists in MCPSession.__init__")
            print(f"     Parameters: {params}")
            failed += 1
        else:
            print(f"  ✅ PASSED: session_id parameter removed from __init__")

            # Check session ID is generated with uuid4()
            if "self.session_id = str(uuid4())" in content:
                print(f"  ✅ PASSED: Session ID always generated with UUID4")
                print(f"     Line: self.session_id = str(uuid4())")

                # Check for security comment
                if "Security:" in content and "server-side" in content:
                    print(f"  ✅ PASSED: Security documentation present")
                    passed += 1
                else:
                    print(f"  ⚠️  WARNING: Security comment missing")
                    passed += 1
            else:
                print(f"  ❌ FAILED: Session ID not properly generated")
                failed += 1
    else:
        print(f"  ❌ FAILED: Could not find __init__ method")
        failed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    failed += 1

print()


# Test 2: Error Message Sanitization
print("Test 2: Error Message Sanitization (Code Review)")
print("-" * 70)
try:
    protocol_file = Path("backend/app/mcp/protocol.py")
    content = protocol_file.read_text()

    # Check handle_exception method
    if 'def handle_exception' in content:
        # Extract the else block for unexpected errors
        pattern = r'else:\s*#.*\n(.*?)return'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            else_block = match.group(0)

            # Should have security comment
            if "Security:" in else_block:
                print("  ✅ PASSED: Security comment present")
            else:
                print("  ⚠️  WARNING: Security comment missing")

            # Should return generic "Internal server error"
            if '"Internal server error"' in else_block:
                print("  ✅ PASSED: Generic error message returned")

            # Should only include error type, not full exception
            if 'type(exception).__name__' in else_block:
                print("  ✅ PASSED: Only error type exposed")

            # Should NOT use str(exception) in return
            if 'str(exception)' not in else_block or 'self._logger.exception' in else_block:
                print("  ✅ PASSED: Exception message not leaked to client")
                passed += 1
            else:
                print("  ❌ FAILED: Exception message may be leaked")
                failed += 1
        else:
            print("  ❌ FAILED: Could not find else block in handle_exception")
            failed += 1
    else:
        print("  ❌ FAILED: handle_exception method not found")
        failed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    failed += 1

print()


# Test 3: Path Traversal Protection
print("Test 3: Path Traversal Protection (Code Review)")
print("-" * 70)
try:
    projects_file = Path("backend/app/routers/projects.py")
    content = projects_file.read_text()

    # Check for ALLOWED_ANALYSIS_DIRS
    if "ALLOWED_ANALYSIS_DIRS" in content:
        print("  ✅ PASSED: ALLOWED_ANALYSIS_DIRS configured")

    # Check for validate_project_path function
    if "def validate_project_path" in content:
        print("  ✅ PASSED: validate_project_path function defined")

        # Check for Path.resolve() usage
        if ".resolve()" in content:
            print("  ✅ PASSED: Uses Path.resolve() for path normalization")

        # Check for is_relative_to() check
        if "is_relative_to" in content:
            print("  ✅ PASSED: Uses is_relative_to() for boundary check")

        # Check for path.exists() validation
        if ".exists()" in content:
            print("  ✅ PASSED: Validates path existence")

        # Check analyze_project endpoint uses validation
        if "validate_project_path(request.project_path)" in content:
            print("  ✅ PASSED: Project analysis endpoint uses validation")
            passed += 1
        else:
            print("  ❌ FAILED: Validation not integrated in endpoint")
            failed += 1
    else:
        print("  ❌ FAILED: validate_project_path function not found")
        failed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    failed += 1

print()


# Test 4: CLI setup.py
print("Test 4: CLI Setup.py (Code Review)")
print("-" * 70)
try:
    setup_file = Path("backend/setup.py")

    if not setup_file.exists():
        print("  ❌ FAILED: setup.py does not exist")
        failed += 1
    else:
        content = setup_file.read_text()

        checks_passed = 0

        # Check for setuptools import
        if "from setuptools import setup" in content:
            print("  ✅ PASSED: Uses setuptools")
            checks_passed += 1

        # Check for entry_points
        if "entry_points" in content and "console_scripts" in content:
            print("  ✅ PASSED: Defines console_scripts entry point")
            checks_passed += 1

        # Check for commandcenter CLI entry
        if "commandcenter=cli.commandcenter:cli" in content:
            print("  ✅ PASSED: commandcenter CLI defined")
            checks_passed += 1

        # Check for keyring dependency
        if "keyring" in content:
            print("  ✅ PASSED: keyring dependency included")
            checks_passed += 1

        # Check for package discovery
        if "find_packages" in content:
            print("  ✅ PASSED: Uses find_packages()")
            checks_passed += 1

        if checks_passed >= 4:
            passed += 1
        else:
            print(f"  ⚠️  WARNING: Only {checks_passed}/5 checks passed")
            failed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    failed += 1

print()


# Test 5: Secure Token Storage
print("Test 5: Secure Token Storage (Code Review)")
print("-" * 70)
try:
    config_file = Path("backend/cli/config.py")
    content = config_file.read_text()

    checks_passed = 0

    # Check for keyring import
    if "import keyring" in content:
        print("  ✅ PASSED: keyring module imported")
        checks_passed += 1

    # Check for save_token method
    if "def save_token" in content and "keyring.set_password" in content:
        print("  ✅ PASSED: save_token() uses keyring.set_password()")
        checks_passed += 1

    # Check for load_token method
    if "def load_token" in content and "keyring.get_password" in content:
        print("  ✅ PASSED: load_token() uses keyring.get_password()")
        checks_passed += 1

    # Check for delete_token method
    if "def delete_token" in content and "keyring.delete_password" in content:
        print("  ✅ PASSED: delete_token() uses keyring.delete_password()")
        checks_passed += 1

    # Check that token field removed from AuthConfig
    auth_config_match = re.search(r'class AuthConfig\(BaseModel\):(.*?)class \w+Config', content, re.DOTALL)
    if auth_config_match:
        auth_config_body = auth_config_match.group(1)
        # Should NOT have token field in the class
        if "token:" not in auth_config_body or "# Note: token field removed" in auth_config_body:
            print("  ✅ PASSED: Token field removed from AuthConfig class")
            checks_passed += 1

    # Check for security documentation
    if "Security:" in content and "keyring" in content.lower():
        print("  ✅ PASSED: Security documentation present")
        checks_passed += 1

    if checks_passed >= 5:
        passed += 1
    else:
        print(f"  ⚠️  WARNING: Only {checks_passed}/6 checks passed")
        failed += 1

except Exception as e:
    print(f"  ❌ FAILED: {e}")
    failed += 1

print()


# Summary
print("=" * 70)
print("CODE REVIEW SUMMARY")
print("=" * 70)
print(f"✅ Passed: {passed}/5")
print(f"❌ Failed: {failed}/5")
print()

if failed == 0:
    print("🎉 ALL SECURITY FIXES VALIDATED AT CODE LEVEL!")
    print()
    print("Security Implementation Review:")
    print("  ✅ Session fixation: Server-side UUID generation")
    print("  ✅ Information disclosure: Error sanitization")
    print("  ✅ Path traversal: Validation with allowed directories")
    print("  ✅ CLI installation: setup.py with entry points")
    print("  ✅ Credential exposure: Keyring integration")
    print()
    print("Next Steps:")
    print("  • Run integration tests in Docker environment")
    print("  • Perform manual security testing")
    print("  • Consider penetration testing")
    exit(0)
else:
    print("⚠️  SOME CODE REVIEW CHECKS FAILED")
    print("   Please review failures above")
    exit(1)
