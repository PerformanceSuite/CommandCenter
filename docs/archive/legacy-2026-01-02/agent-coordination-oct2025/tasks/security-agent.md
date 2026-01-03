# Security Hardening Agent - Task Definition

**Mission:** Fix all critical security vulnerabilities
**Worktree:** worktrees/security-agent
**Branch:** feature/security-hardening
**Estimated Time:** 18 hours
**Dependencies:** None (Phase 1 - Independent)

---

## Tasks Checklist

### Task 1: Fix Encryption Key Derivation (1 hour)
- [ ] Read `backend/app/utils/crypto.py`
- [ ] Replace truncate/pad logic with PBKDF2 key derivation
- [ ] Add `ENCRYPTION_SALT` to `.env.template`
- [ ] Update crypto tests
- [ ] Test with various SECRET_KEY lengths

**File:** `backend/app/utils/crypto.py:25-30`

**Expected Changes:**
```python
# Replace this:
key = secret_key[:32].ljust(32, '0')

# With this:
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

kdf = PBKDF2(
    algorithm=hashes.SHA256(),
    length=32,
    salt=settings.encryption_salt.encode(),
    iterations=100000,
)
key = kdf.derive(secret_key.encode())
```

---

### Task 2: Implement JWT Authentication (8 hours)
- [ ] Create `backend/app/auth/` directory
- [ ] Create `auth/jwt.py` - Token creation/validation functions
- [ ] Create `auth/dependencies.py` - FastAPI dependency injection
- [ ] Create `auth/schemas.py` - Login/token Pydantic schemas
- [ ] Add `get_current_user` dependency to all protected routes
- [ ] Create `tests/test_auth.py` with full coverage
- [ ] Update `.env.template` with JWT_SECRET_KEY

**Files to Create:**
```
backend/app/auth/
├── __init__.py
├── jwt.py
├── dependencies.py
└── schemas.py
```

**Implementation Guidance:**
- Use `python-jose` for JWT tokens
- Token expiration: 24 hours
- Include user_id and scopes in token
- All API routes except /health and /docs require auth

---

### Task 3: Encrypt GitHub Tokens (2 hours)
- [ ] Read `backend/app/models/repository.py`
- [ ] Update `access_token` field to encrypt before save
- [ ] Modify `create_repository()` in routers to use encryption
- [ ] Modify `update_repository()` to handle encrypted tokens
- [ ] Create Alembic migration: `alembic revision --autogenerate -m "encrypt_github_tokens"`
- [ ] Write migration script to encrypt existing tokens
- [ ] Test encryption/decryption flow

**Files to Modify:**
- `backend/app/models/repository.py:36-40`
- `backend/app/routers/repositories.py:45-78`

**Implementation:**
```python
# In Repository model
from app.utils.crypto import encrypt_token, decrypt_token

@hybrid_property
def access_token(self):
    if self._access_token:
        return decrypt_token(self._access_token)
    return None

@access_token.setter
def access_token(self, value):
    if value:
        self._access_token = encrypt_token(value)
    else:
        self._access_token = None
```

---

### Task 4: Add Rate Limiting (4 hours)
- [ ] Install: `pip install slowapi`
- [ ] Create `backend/app/middleware/rate_limit.py`
- [ ] Configure global rate limit: 100 requests/minute
- [ ] Configure per-endpoint limits:
  - `/api/v1/repositories`: 20/minute
  - `/api/v1/technologies`: 50/minute
  - `/api/v1/knowledge/query`: 10/minute
- [ ] Add rate limit middleware to `main.py`
- [ ] Test with load testing tool (locust or k6)

**Files to Create:**
- `backend/app/middleware/rate_limit.py`

**Files to Modify:**
- `backend/app/main.py` (add middleware)
- `requirements.txt` (add slowapi)

---

### Task 5: Fix CORS Configuration (1 hour)
- [ ] Read current CORS setup in `backend/app/main.py:48-54`
- [ ] Update to use `ALLOWED_ORIGINS` from environment
- [ ] Remove wildcard `*` permissions
- [ ] Add `ALLOWED_ORIGINS` to `.env.template`
- [ ] Default to `["http://localhost:3000", "http://localhost:8000"]`
- [ ] Test CORS with different origins

**Expected Change:**
```python
# In backend/app/config.py
allowed_origins: List[str] = Field(
    default=["http://localhost:3000"],
    env="ALLOWED_ORIGINS"
)

# In backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

### Task 6: Add Security Headers (2 hours)
- [ ] Create `backend/app/middleware/security_headers.py`
- [ ] Implement middleware to add:
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Content-Security-Policy: default-src 'self'`
- [ ] Add middleware to `main.py`
- [ ] Test headers with curl

**Files to Create:**
- `backend/app/middleware/security_headers.py`

---

## Testing Requirements

### Unit Tests to Write
- [ ] `tests/test_auth.py` - JWT creation, validation, expiration
- [ ] `tests/test_crypto.py` - Encryption with PBKDF2
- [ ] `tests/test_rate_limit.py` - Rate limiting behavior
- [ ] `tests/test_security_headers.py` - Header presence

### Integration Tests
- [ ] Test full auth flow: login → token → protected endpoint
- [ ] Test token encryption on repository CRUD
- [ ] Test rate limiting across multiple requests

---

## Review Checklist

Before creating PR, ensure:
- [ ] All tests pass: `pytest`
- [ ] Linting clean: `black app/ && flake8 app/`
- [ ] No hardcoded secrets
- [ ] All environment variables in `.env.template`
- [ ] Run `/review` until score is 10/10

---

## PR Details

**Title:** "Security: Complete security hardening - authentication, encryption, rate limiting"

**Description:**
```markdown
## Security Hardening Complete ✅

This PR addresses all critical security vulnerabilities identified in the security review.

### Changes
- ✅ Fixed encryption key derivation (PBKDF2)
- ✅ Implemented JWT authentication on all endpoints
- ✅ Encrypted GitHub tokens at rest
- ✅ Added rate limiting (100/min global, per-endpoint limits)
- ✅ Fixed CORS to use allowlist
- ✅ Added security headers (HSTS, CSP, etc.)

### Security Improvements
- **Before:** Tokens in plaintext, no auth, no rate limits
- **After:** Encrypted tokens, JWT auth, rate-limited, secure headers

### Test Coverage
- Auth tests: 15 tests
- Crypto tests: 8 tests
- Rate limit tests: 6 tests
- Coverage: 95% on security modules

### Review Score: 10/10 ✅
```

---

## Success Criteria

- [ ] All 6 tasks completed
- [ ] Zero critical security vulnerabilities remain
- [ ] All tests passing (>95% coverage on security code)
- [ ] Review score 10/10
- [ ] No merge conflicts
- [ ] PR approved and merged

---

**Reference Documents:**
- SECURITY_REVIEW.md (main findings)
- IMPLEMENTATION_ROADMAP.md (Phase 1, Week 1)
