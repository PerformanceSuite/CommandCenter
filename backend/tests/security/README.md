# Security Tests

## Overview

Security tests validate application security across project isolation, injection attacks, XSS prevention, and authentication.

## Test Structure

### Project Isolation Tests (`test_project_isolation.py`)

**Goal:** Ensure complete data isolation between projects.

**Tests (9 total):**
- User cannot read other user's technologies (1)
- User cannot modify other user's technologies (1)
- User cannot delete other user's technologies (1)
- User cannot read other user's repositories (1)
- User cannot read other user's research tasks (1)
- User cannot read other user's knowledge entries (1)
- Technology list filtered by project (1)
- Repository list filtered by project (1)
- Research list filtered by project (1)

**Critical Security Requirements:**
- All database queries must filter by `project_id`
- Users can only access their own project's data
- API endpoints enforce project-based access control

### SQL Injection Tests (`test_sql_injection.py`)

**Goal:** Prevent SQL injection attacks in query parameters.

**Tests (3 total):**
- Technology search prevents SQL injection (1)
- Repository owner filter prevents SQL injection (1)
- Research task search prevents SQL injection (1)

**Security Principles:**
- Use parameterized queries or ORM (never string concatenation)
- Validate and sanitize all user input
- Return safe errors (don't expose SQL details)

### XSS Prevention Tests (`test_xss.py`)

**Goal:** Prevent Cross-Site Scripting attacks.

**Tests (3 total):**
- Technology title escapes HTML/JS (1)
- Research description escapes HTML (1)
- Knowledge entry source escapes HTML (1)

**Security Principles:**
- Escape HTML in API responses
- Sanitize user-provided content
- Content Security Policy headers recommended

### Authentication Tests (`test_authentication.py`)

**Goal:** Validate authentication and authorization.

**Tests (6 total):**
- Endpoints require authentication (1)
- Invalid token rejected (1)
- Tampered token rejected (1)
- Expired token rejected (1)
- CSRF token required for mutations (1)
- User cannot use another user's token (1)

**Security Principles:**
- JWT tokens for stateless authentication
- Token validation on every request
- CSRF protection for state-changing operations
- Token expiration and revocation

## Running Security Tests

**All security tests:**
```bash
cd backend
pytest tests/security/ -v
```

**Specific test file:**
```bash
pytest tests/security/test_project_isolation.py -v
```

**Specific test:**
```bash
pytest tests/security/test_sql_injection.py::test_technology_search_prevents_sql_injection -v
```

**In Docker:**
```bash
make test-security
```

## Test Count

**Total: 18 tests**
- Project isolation: 9 tests
- SQL injection prevention: 3 tests
- XSS prevention: 3 tests
- Authentication/Authorization: 6 tests (includes CSRF)

## Security Best Practices

### 1. Project Isolation (Multi-Tenancy)

**Every database model must have `project_id`:**
```python
class Technology(Base):
    __tablename__ = "technologies"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)  # REQUIRED
```

**Every query must filter by project_id:**
```python
# ❌ WRONG - No project filtering
technologies = session.query(Technology).all()

# ✅ CORRECT - Filter by authenticated user's project
technologies = session.query(Technology).filter(
    Technology.project_id == current_user.project_id
).all()
```

### 2. SQL Injection Prevention

**Use ORM or parameterized queries:**
```python
# ❌ WRONG - String concatenation
query = f"SELECT * FROM technologies WHERE title = '{user_input}'"

# ✅ CORRECT - Parameterized query
technologies = session.query(Technology).filter(
    Technology.title == user_input
).all()
```

### 3. XSS Prevention

**Escape HTML in responses:**
```python
from html import escape

# ✅ Escape user-provided content
tech_response = {
    "title": escape(technology.title),
    "description": escape(technology.description)
}
```

### 4. Authentication

**Verify JWT on every request:**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        return User(id=payload["user_id"], project_id=payload["project_id"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## Common Vulnerabilities

### ❌ Broken Access Control
```python
# User can access any technology by ID
@app.get("/technologies/{tech_id}")
async def get_technology(tech_id: int):
    return db.query(Technology).filter(Technology.id == tech_id).first()
```

### ✅ Fixed with Project Filtering
```python
@app.get("/technologies/{tech_id}")
async def get_technology(tech_id: int, user: User = Depends(get_current_user)):
    tech = db.query(Technology).filter(
        Technology.id == tech_id,
        Technology.project_id == user.project_id  # Enforce isolation
    ).first()
    if not tech:
        raise HTTPException(status_code=404)
    return tech
```

## OWASP Top 10 Coverage

| Vulnerability | Coverage |
|---------------|----------|
| A01:2021 – Broken Access Control | ✅ Project isolation tests |
| A02:2021 – Cryptographic Failures | ⚠️ Partial (JWT validation) |
| A03:2021 – Injection | ✅ SQL injection tests |
| A04:2021 – Insecure Design | ⚠️ Partial |
| A05:2021 – Security Misconfiguration | ⚠️ Not covered |
| A06:2021 – Vulnerable Components | ⚠️ Not covered |
| A07:2021 – Identification and Authentication Failures | ✅ Auth tests |
| A08:2021 – Software and Data Integrity Failures | ⚠️ Not covered |
| A09:2021 – Security Logging and Monitoring Failures | ⚠️ Not covered |
| A10:2021 – Server-Side Request Forgery (SSRF) | ⚠️ Not covered |

## Next Steps

1. **Implement security features:**
   - Add `project_id` to all models
   - Add project filtering to all queries
   - Implement JWT authentication
   - Add HTML escaping to API responses

2. **Run tests after implementation:**
   ```bash
   pytest backend/tests/security/ -v
   ```
   Expected: All tests should PASS after security implementation

3. **Add missing coverage:**
   - Rate limiting tests
   - File upload validation tests
   - API key rotation tests
   - Audit logging tests

4. **Security scanning:**
   - Run `bandit` for Python security issues
   - Run `safety check` for vulnerable dependencies
   - Add SAST/DAST to CI pipeline
