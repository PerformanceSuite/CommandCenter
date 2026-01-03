# Phase 1 Agent: Security Critical Fixes

**Agent Name:** phase1-security-critical-agent
**Branch:** phase1/security-critical-fixes
**Estimated Time:** 6 hours
**Priority:** CRITICAL - Blocks Production
**Blocks:** VIZTRTR production deployment, all MCP servers

---

## Mission

Fix the 2 critical security vulnerabilities (CVE-level) and 5 high-risk issues found in Phase 0 MCP Architecture Security Review. These fixes are **mandatory** before any MCP server can go to production.

---

## Context from Phase 0 Review

**MCP Security Review Score:** 7/10 - Needs Hardening

**Critical Vulnerabilities (2):**
1. ❌ **CWE-306: Missing Authentication** - MCP servers have no auth on stdio
2. ❌ **CWE-78: OS Command Injection** - Git ops don't sanitize branch names

**High Risk Issues (5):**
- Path traversal vulnerabilities
- No API key rotation
- No code execution sandboxing
- Insufficient access logging
- Puppeteer sandbox unclear

**From MCP_ARCHITECTURE_SECURITY_REVIEW.md:**
- Location: `/Users/danielconnolly/Projects/CommandCenter`
- Estimated fix time: 66 hours total (this task covers Phase 1: 6 hours)
- Focus: Critical vulnerabilities only (defer medium/low to Phase 2)

---

## Tasks

### Task 1: Implement MCP Authentication (CWE-306) - 3 hours

**Goal:** Add authentication to MCP stdio transport to prevent unauthorized access

**Problem:**
- MCP servers use stdio transport with no authentication
- Any process that can spawn the server can access it
- No validation of client identity
- No access control

**Solution Architecture:**

```python
# backend/app/mcp/auth.py
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict

class MCPAuthManager:
    """Authentication manager for MCP stdio servers"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.session_tokens: Dict[str, dict] = {}

    def generate_session_token(self, client_id: str, ttl_hours: int = 24) -> str:
        """Generate time-limited session token for MCP client"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        self.session_tokens[token] = {
            "client_id": client_id,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }

        return token

    def validate_token(self, token: str) -> tuple[bool, Optional[str]]:
        """Validate MCP session token"""
        if token not in self.session_tokens:
            return False, None

        session = self.session_tokens[token]

        if datetime.utcnow() > session["expires_at"]:
            del self.session_tokens[token]
            return False, None

        return True, session["client_id"]

    def revoke_token(self, token: str):
        """Revoke MCP session token"""
        self.session_tokens.pop(token, None)
```

**Implementation Steps:**

1. Create `backend/app/mcp/auth.py`:
   - Implement MCPAuthManager class
   - Session token generation (32-byte secure random)
   - Token validation with TTL
   - Token revocation

2. Update MCP server startup to require authentication:
   ```python
   # backend/app/mcp/server.py (or wherever MCP servers are initialized)

   from app.mcp.auth import MCPAuthManager
   from app.core.config import settings

   auth_manager = MCPAuthManager(settings.SECRET_KEY)

   # Before processing any MCP request:
   def validate_mcp_request(request):
       token = request.headers.get("X-MCP-Auth-Token")
       if not token:
           raise ValueError("Missing MCP authentication token")

       valid, client_id = auth_manager.validate_token(token)
       if not valid:
           raise ValueError("Invalid or expired MCP token")

       return client_id
   ```

3. Create token generation endpoint:
   ```python
   # backend/app/routers/mcp.py

   @router.post("/mcp/tokens")
   async def create_mcp_token(
       request: MCPTokenRequest,
       current_user: User = Depends(get_current_user)
   ) -> MCPTokenResponse:
       """Generate MCP authentication token for client"""

       # Generate token for this user's project
       client_id = f"{current_user.id}:{request.project_id}"
       token = auth_manager.generate_session_token(client_id, ttl_hours=24)

       return MCPTokenResponse(
           token=token,
           expires_at=...,
           client_id=client_id
       )
   ```

4. Update MCP client configuration:
   ```json
   // .commandcenter/mcp.json
   {
     "mcpServers": {
       "knowledgebeast": {
         "command": "python",
         "args": ["-m", "backend.mcp.knowledgebeast"],
         "env": {
           "MCP_AUTH_TOKEN": "${MCP_TOKEN}"  // Injected from secure store
         }
       }
     }
   }
   ```

5. Add authentication to all MCP servers:
   - Knowledge Beast MCP server
   - VIZTRTR MCP server (when created)
   - AgentFlow MCP server (when created)
   - API Manager MCP server (when created)

6. Write tests:
   ```python
   # backend/tests/test_mcp_auth.py

   def test_generate_token():
       """Test MCP token generation"""
       auth = MCPAuthManager("test-secret")
       token = auth.generate_session_token("test-client")
       assert len(token) == 43  # urlsafe_b64 with 32 bytes

   def test_validate_token():
       """Test MCP token validation"""
       auth = MCPAuthManager("test-secret")
       token = auth.generate_session_token("test-client")
       valid, client_id = auth.validate_token(token)
       assert valid
       assert client_id == "test-client"

   def test_expired_token():
       """Test expired token rejection"""
       # Test with TTL=0.001 hours

   def test_invalid_token():
       """Test invalid token rejection"""
   ```

**Success Criteria:**
- [ ] MCPAuthManager implemented with session tokens
- [ ] Token generation endpoint created
- [ ] All MCP servers require authentication
- [ ] Tests pass (token generation, validation, expiration, revocation)
- [ ] Documentation updated

---

### Task 2: Fix Command Injection (CWE-78) - 2 hours

**Goal:** Sanitize all git operations to prevent OS command injection

**Problem:**
- Git operations don't sanitize branch names, commit messages, file paths
- Attacker could inject shell commands via malicious input
- Example: `branch_name = "; rm -rf / #"` would execute deletion

**Solution:**

```python
# backend/app/services/git_security.py
import re
import shlex
from pathlib import Path
from typing import List, Optional

class GitCommandSanitizer:
    """Sanitize git command inputs to prevent injection"""

    # Allowed characters in branch names (git standard)
    BRANCH_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-/\.]+$')

    # Disallowed patterns in any git input
    DANGEROUS_PATTERNS = [
        r'[;&|`$]',  # Shell metacharacters
        r'\$\(',     # Command substitution
        r'\.\.',     # Path traversal
        r'^/',       # Absolute paths
        r'~',        # Home directory
    ]

    @staticmethod
    def sanitize_branch_name(branch: str) -> str:
        """Sanitize git branch name"""
        if not branch:
            raise ValueError("Branch name cannot be empty")

        if not GitCommandSanitizer.BRANCH_NAME_PATTERN.match(branch):
            raise ValueError(f"Invalid branch name: {branch}")

        for pattern in GitCommandSanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, branch):
                raise ValueError(f"Dangerous pattern in branch name: {branch}")

        # Additional git-specific validations
        if branch.startswith('-'):
            raise ValueError("Branch name cannot start with hyphen")
        if '..' in branch:
            raise ValueError("Branch name cannot contain '..'")

        return branch

    @staticmethod
    def sanitize_commit_message(message: str) -> str:
        """Sanitize git commit message"""
        if not message:
            raise ValueError("Commit message cannot be empty")

        # Check for dangerous patterns
        for pattern in GitCommandSanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, message):
                raise ValueError(f"Dangerous pattern in commit message")

        # Escape for shell safety
        return shlex.quote(message)

    @staticmethod
    def sanitize_file_path(path: str, base_dir: Path) -> Path:
        """Sanitize file path to prevent traversal"""
        if not path:
            raise ValueError("File path cannot be empty")

        # Resolve to absolute path
        abs_path = (base_dir / path).resolve()

        # Ensure it's within base directory
        if not str(abs_path).startswith(str(base_dir.resolve())):
            raise ValueError(f"Path traversal detected: {path}")

        return abs_path

    @staticmethod
    def build_safe_git_command(args: List[str]) -> List[str]:
        """Build safe git command (no shell execution)"""
        # Use subprocess.run with list args (never shell=True)
        # Prepend 'git' command
        return ['git'] + args
```

**Implementation Steps:**

1. Create `backend/app/services/git_security.py`:
   - Implement GitCommandSanitizer class
   - Branch name validation
   - Commit message sanitization
   - File path traversal prevention
   - Safe command building

2. Update GitHubService to use sanitizer:
   ```python
   # backend/app/services/github_service.py

   from app.services.git_security import GitCommandSanitizer

   class GitHubService:
       def create_branch(self, branch_name: str):
           # BEFORE (VULNERABLE):
           # os.system(f"git checkout -b {branch_name}")

           # AFTER (SECURE):
           safe_branch = GitCommandSanitizer.sanitize_branch_name(branch_name)
           cmd = GitCommandSanitizer.build_safe_git_command(['checkout', '-b', safe_branch])
           subprocess.run(cmd, check=True, cwd=self.repo_path)
   ```

3. Find and fix all git operations:
   ```bash
   cd /Users/danielconnolly/Projects/CommandCenter/backend

   # Find all git command executions
   grep -r "os.system.*git" --include="*.py"
   grep -r "subprocess.*shell=True" --include="*.py" | grep git
   grep -r "\.run\(.*git" --include="*.py"
   ```

4. Update coordination scripts (if any):
   ```bash
   cd /Users/danielconnolly/Projects/CommandCenter/scripts

   # Find shell scripts with git commands
   find . -name "*.sh" -exec grep -l "git " {} \;
   ```

5. Write tests:
   ```python
   # backend/tests/test_git_security.py

   def test_sanitize_valid_branch():
       """Test valid branch name sanitization"""
       assert GitCommandSanitizer.sanitize_branch_name("feature/test") == "feature/test"

   def test_reject_injection_attempt():
       """Test command injection rejection"""
       with pytest.raises(ValueError):
           GitCommandSanitizer.sanitize_branch_name("test; rm -rf /")

   def test_prevent_path_traversal():
       """Test path traversal prevention"""
       base = Path("/safe/dir")
       with pytest.raises(ValueError):
           GitCommandSanitizer.sanitize_file_path("../../etc/passwd", base)
   ```

**Success Criteria:**
- [ ] GitCommandSanitizer implemented
- [ ] All git operations use sanitizer
- [ ] No `shell=True` in subprocess calls
- [ ] Tests pass (injection prevention, path traversal)
- [ ] Security scan passes

---

### Task 3: Path Traversal Prevention - 1 hour

**Goal:** Prevent path traversal attacks in file operations

**Problem:**
- File operations may not validate paths
- Attacker could access files outside allowed directories
- Example: `../../etc/passwd` could read sensitive files

**Solution:**

Already partially covered in GitCommandSanitizer.sanitize_file_path(), but need to apply broadly.

**Implementation Steps:**

1. Create path validation utility:
   ```python
   # backend/app/utils/path_security.py

   from pathlib import Path
   from typing import Union

   class PathValidator:
       """Validate file paths for security"""

       @staticmethod
       def validate_path(path: Union[str, Path], base_dir: Union[str, Path]) -> Path:
           """Validate path is within base directory"""
           base = Path(base_dir).resolve()
           target = (base / path).resolve()

           if not str(target).startswith(str(base)):
               raise ValueError(f"Path traversal blocked: {path}")

           return target
   ```

2. Apply to all file operations:
   - RAG service document uploads
   - Repository file access
   - Configuration file reads
   - Log file access

3. Update affected services:
   ```python
   # backend/app/services/rag_service.py

   from app.utils.path_security import PathValidator

   def add_document(self, file_path: str):
       # Validate path before opening
       safe_path = PathValidator.validate_path(file_path, self.documents_dir)
       with open(safe_path, 'r') as f:
           content = f.read()
   ```

4. Write tests:
   ```python
   def test_path_traversal_blocked():
       """Test path traversal is blocked"""
       with pytest.raises(ValueError):
           PathValidator.validate_path("../../etc/passwd", "/safe/dir")
   ```

**Success Criteria:**
- [ ] PathValidator implemented
- [ ] All file operations use validation
- [ ] Tests pass
- [ ] No path traversal vulnerabilities

---

### Task 4: Security Testing and Validation - 0.5 hours

**Goal:** Validate all security fixes work correctly

**Steps:**

1. Run security test suite:
   ```bash
   pytest backend/tests/test_*security*.py -v
   ```

2. Attempt penetration tests:
   - Try MCP access without auth token
   - Try command injection in branch names
   - Try path traversal attacks
   - All should be blocked

3. Run static analysis:
   ```bash
   bandit -r backend/app/
   ```

4. Check for common vulnerabilities:
   ```bash
   safety check
   ```

**Success Criteria:**
- [ ] All security tests pass
- [ ] Penetration tests blocked
- [ ] No critical findings from bandit
- [ ] No vulnerable dependencies

---

### Task 5: Documentation and Deployment Guide - 0.5 hours

**Goal:** Document security fixes and deployment requirements

**Steps:**

1. Update MCP_ARCHITECTURE_SECURITY_REVIEW.md:
   - Mark CWE-306 and CWE-78 as ✅ FIXED
   - Update security score
   - Document new authentication system

2. Create SECURITY.md:
   - MCP authentication requirements
   - Token generation process
   - Git operation security
   - Path validation rules

3. Update deployment docs:
   - Add MCP token generation step
   - Document security environment variables
   - Note that all clients need tokens

4. Create security checklist:
   ```markdown
   # Production Security Checklist

   - [ ] MCP authentication tokens generated
   - [ ] SECRET_KEY is strong (32+ bytes)
   - [ ] All git operations sanitized
   - [ ] Path validation enabled
   - [ ] Security tests passing
   - [ ] No shell=True in subprocess calls
   ```

**Success Criteria:**
- [ ] Documentation updated
- [ ] SECURITY.md created
- [ ] Deployment guide includes security steps
- [ ] Security checklist complete

---

### Task 6: Commit and PR - 0.5 hours

**Goal:** Create clean commits and PR for security fixes

**Steps:**

1. Create atomic commits:
   ```bash
   git add backend/app/mcp/auth.py backend/tests/test_mcp_auth.py
   git commit -m "security: Implement MCP authentication (CWE-306)"

   git add backend/app/services/git_security.py backend/tests/test_git_security.py
   git commit -m "security: Prevent OS command injection (CWE-78)"

   git add backend/app/utils/path_security.py backend/tests/test_path_security.py
   git commit -m "security: Prevent path traversal attacks"

   git add SECURITY.md MCP_ARCHITECTURE_SECURITY_REVIEW.md
   git commit -m "docs: Document security fixes and requirements"
   ```

2. Push and create PR:
   ```bash
   git push -u origin phase1/security-critical-fixes
   ```

3. PR with security focus:

```markdown
# Phase 1: Security Critical Fixes 🔒

## Summary
Fixes 2 critical CVE-level vulnerabilities and 1 high-risk issue found in Phase 0 security review. **Blocks all production deployments** until merged.

## Critical Vulnerabilities Fixed

### CWE-306: Missing Authentication ✅
- Implemented MCP authentication with session tokens
- 32-byte secure random tokens with TTL
- Token generation endpoint for authorized clients
- All MCP servers now require authentication

### CWE-78: OS Command Injection ✅
- Created GitCommandSanitizer for all git operations
- Branch name validation (alphanumeric + safe chars only)
- Commit message sanitization
- Eliminated all shell=True subprocess calls
- Safe command building with list args

### Path Traversal Prevention ✅
- PathValidator for all file operations
- Ensures paths stay within allowed directories
- Applied to RAG uploads, repo access, config files

## Test Results
- ✅ All security tests pass
- ✅ Penetration tests blocked correctly
- ✅ Bandit static analysis clean
- ✅ No vulnerable dependencies (safety check)

## Phase 0 → Phase 1
**Before:** 7/10 (Needs Hardening) - 2 critical CVEs
**After:** 9/10 (Production Safe) - Critical CVEs fixed

## Impact
- **Blocks:** VIZTRTR production deployment (until this merges)
- **Enables:** Safe deployment of all MCP servers
- **Prevents:** Authentication bypass, command injection, file access attacks

## Security Checklist
- [x] CWE-306 (Missing Auth) fixed
- [x] CWE-78 (Command Injection) fixed
- [x] Path traversal prevented
- [x] Security tests passing
- [x] Static analysis clean
- [x] Documentation updated

## Next Steps
- Merge this PR immediately
- Deploy security fixes to all environments
- Generate MCP tokens for authorized clients
- Proceed with VIZTRTR production deployment

## Links
- Security Review: MCP_ARCHITECTURE_SECURITY_REVIEW.md
- Security Guide: SECURITY.md
- Consolidated Findings: PHASE0_CONSOLIDATED_FINDINGS.md

🔒 **SECURITY**: This PR must be reviewed and merged before any MCP server deployment

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Success Criteria:**
- [ ] Clean atomic commits
- [ ] PR created with security focus
- [ ] Self-review score: 10/10
- [ ] Ready for immediate merge

---

## Definition of Done

- [ ] CWE-306 (Missing Authentication) fixed and tested
- [ ] CWE-78 (OS Command Injection) fixed and tested
- [ ] Path traversal prevention implemented and tested
- [ ] All security tests pass
- [ ] Static analysis clean (bandit)
- [ ] Documentation updated (SECURITY.md, deployment guides)
- [ ] PR created and ready for merge
- [ ] No security vulnerabilities remain

---

## Success Metrics

**Time:** 6 hours (3h auth + 2h injection + 1h paths + 0.5h testing + 0.5h docs + 0.5h PR)
**CVEs Fixed:** 2 critical
**Score:** 7/10 → 9/10 security
**Impact:** Unblocks VIZTRTR production deployment

---

## Notes

- **CRITICAL:** This blocks all production deployments
- Must be completed in parallel with VIZTRTR fixes
- Both must merge before VIZTRTR can go to production
- Security fixes are non-negotiable
- Phase 2 security hardening (19 hours) can come later

---

**Priority:** 🔴 CRITICAL - Blocks Production
**Blocking:** All MCP server deployments
**Dependencies:** None - can start immediately
**Merge Order:** Must merge before VIZTRTR PR
