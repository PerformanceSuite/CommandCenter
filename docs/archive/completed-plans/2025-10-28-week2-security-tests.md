# Week 2 Security Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement CommandCenter security tests for project isolation, JWT validation, and basic RBAC (18 tests total).

**Architecture:** Test-driven security validation using pytest fixtures for user isolation, JWT token factories for authentication testing, and FastAPI TestClient for API endpoint testing. All tests use mocked dependencies (no real GitHub API or external services).

**Tech Stack:** pytest, pytest-asyncio, FastAPI TestClient, PyJWT, bcrypt

**Worktree:** `.worktrees/testing-security` → `testing/week2-security` branch

---

## Task 1: Security Test Infrastructure

**Files:**
- Create: `backend/tests/security/conftest.py`
- Create: `backend/tests/security/__init__.py`

**Step 1: Create security test directory structure**

```bash
mkdir -p backend/tests/security
touch backend/tests/security/__init__.py
```

**Step 2: Write security fixtures**

Create `backend/tests/security/conftest.py`:

```python
"""Security test fixtures."""
import pytest
from datetime import timedelta
from app.utils.auth import create_access_token
from tests.utils.factories import UserFactory, ProjectFactory


@pytest.fixture
async def user_a(db_session):
    """Create isolated user A with project-a."""
    user = await UserFactory.create(
        db_session,
        email="user_a@test.com",
        project_id="project-a"
    )
    return user


@pytest.fixture
async def user_b(db_session):
    """Create isolated user B with project-b."""
    user = await UserFactory.create(
        db_session,
        email="user_b@test.com",
        project_id="project-b"
    )
    return user


@pytest.fixture
def jwt_token_factory():
    """Factory for creating test JWT tokens.

    Args:
        user_id: User ID to encode in token
        expires_delta: Token expiration time (default: 30 minutes)
        tampered: Whether to tamper with token
        tamper_type: Type of tampering ("signature" or "payload")

    Returns:
        JWT token string
    """
    def _create_token(
        user_id: str,
        expires_delta: timedelta = None,
        tampered: bool = False,
        tamper_type: str = "signature"
    ):
        if expires_delta is None:
            expires_delta = timedelta(minutes=30)

        token = create_access_token(
            data={"sub": user_id},
            expires_delta=expires_delta
        )

        if tampered:
            parts = token.split(".")
            if tamper_type == "signature":
                # Modify signature (last part)
                parts[2] = parts[2][:-5] + "XXXXX"
            elif tamper_type == "payload":
                # Modify payload (middle part)
                parts[1] = parts[1][:-5] + "XXXXX"
            token = ".".join(parts)

        return token

    return _create_token


@pytest.fixture
def auth_headers_factory(jwt_token_factory):
    """Create authorization headers for user.

    Args:
        user: User object to create token for

    Returns:
        Dictionary with Authorization header
    """
    def _create_headers(user):
        token = jwt_token_factory(user_id=str(user.id))
        return {"Authorization": f"Bearer {token}"}

    return _create_headers
```

**Step 3: Verify fixtures import correctly**

Run:
```bash
cd backend
python -c "from tests.security.conftest import *; print('Fixtures loaded successfully')"
```

Expected: "Fixtures loaded successfully"

**Step 4: Commit**

```bash
git add backend/tests/security/
git commit -m "test: Add security test infrastructure and fixtures

- Create security test directory structure
- Add user_a and user_b fixtures for isolation testing
- Add jwt_token_factory for JWT security tests
- Add auth_headers_factory for API authentication"
```

---

## Task 2: Project Isolation Tests (Part 1 - Technologies)

**Files:**
- Create: `backend/tests/security/test_project_isolation.py`

**Step 1: Write failing test for technology read isolation**

Create `backend/tests/security/test_project_isolation.py`:

```python
"""Project isolation security tests."""
import pytest
from tests.utils.factories import TechnologyFactory


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_technologies(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's technologies."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session,
        title="Secret Tech B",
        domain="ai",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries technologies
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/technologies", headers=headers)

    # Assert User B's technology not in results
    assert response.status_code == 200
    tech_ids = [t["id"] for t in response.json()]
    assert tech_b.id not in tech_ids, "User A should not see User B's technology"
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd backend
pytest tests/security/test_project_isolation.py::test_user_cannot_read_other_user_technologies -v
```

Expected: FAIL (project isolation not yet implemented in API)

**Step 3: Write test for technology modification isolation**

Add to `backend/tests/security/test_project_isolation.py`:

```python
@pytest.mark.asyncio
async def test_user_cannot_modify_other_user_technologies(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot update User B's technology."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session,
        title="Tech B",
        domain="cloud",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A tries to modify User B's technology
    headers = auth_headers_factory(user_a)
    response = await client.put(
        f"/api/v1/technologies/{tech_b.id}",
        headers=headers,
        json={"title": "Hacked Title"}
    )

    # Should return 403 Forbidden or 404 Not Found
    assert response.status_code in [403, 404], (
        "User A should not be able to modify User B's technology"
    )
```

**Step 4: Write test for technology deletion isolation**

Add to `backend/tests/security/test_project_isolation.py`:

```python
@pytest.mark.asyncio
async def test_user_cannot_delete_other_user_technologies(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot delete User B's technology."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session,
        title="Tech B Delete",
        domain="audio",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A tries to delete User B's technology
    headers = auth_headers_factory(user_a)
    response = await client.delete(
        f"/api/v1/technologies/{tech_b.id}",
        headers=headers
    )

    # Should return 403 Forbidden or 404 Not Found
    assert response.status_code in [403, 404], (
        "User A should not be able to delete User B's technology"
    )
```

**Step 5: Run tests to verify they fail**

Run:
```bash
cd backend
pytest tests/security/test_project_isolation.py -v
```

Expected: 3 FAIL (isolation not yet implemented)

**Step 6: Commit**

```bash
git add backend/tests/security/test_project_isolation.py
git commit -m "test: Add technology isolation tests (3 tests, failing)

- Test user cannot read other user's technologies
- Test user cannot modify other user's technologies
- Test user cannot delete other user's technologies

Tests are failing as expected (TDD red phase)"
```

---

## Task 3: Project Isolation Tests (Part 2 - Repositories & Research)

**Files:**
- Modify: `backend/tests/security/test_project_isolation.py`

**Step 1: Write test for repository read isolation**

Add to `backend/tests/security/test_project_isolation.py`:

```python
from tests.utils.factories import RepositoryFactory


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_repositories(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's repositories."""
    # Create repository for User B
    repo_b = await RepositoryFactory.create(
        db_session,
        owner="user-b",
        name="secret-repo",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries repositories
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/repositories", headers=headers)

    # Assert User B's repository not in results
    assert response.status_code == 200
    repo_ids = [r["id"] for r in response.json()]
    assert repo_b.id not in repo_ids, "User A should not see User B's repository"
```

**Step 2: Write test for research task read isolation**

Add to `backend/tests/security/test_project_isolation.py`:

```python
from tests.utils.factories import ResearchTaskFactory


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_research_tasks(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's research tasks."""
    # Create research task for User B
    research_b = await ResearchTaskFactory.create(
        db_session,
        title="Secret Research",
        description="Confidential",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries research tasks
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/research", headers=headers)

    # Assert User B's research not in results
    assert response.status_code == 200
    research_ids = [r["id"] for r in response.json()]
    assert research_b.id not in research_ids, "User A should not see User B's research"
```

**Step 3: Write test for knowledge entry read isolation**

Add to `backend/tests/security/test_project_isolation.py`:

```python
from tests.utils.factories import KnowledgeEntryFactory


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_knowledge_entries(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """User A cannot see User B's knowledge entries."""
    # Create knowledge entry for User B
    knowledge_b = await KnowledgeEntryFactory.create(
        db_session,
        source="confidential.pdf",
        category="research",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries knowledge base
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/knowledge/entries", headers=headers)

    # Assert User B's knowledge not in results
    assert response.status_code == 200
    entry_ids = [e["id"] for e in response.json()]
    assert knowledge_b.id not in entry_ids, "User A should not see User B's knowledge"
```

**Step 4: Run tests to verify they fail**

Run:
```bash
cd backend
pytest tests/security/test_project_isolation.py -v -k "repository or research or knowledge"
```

Expected: 3 FAIL (isolation not yet implemented)

**Step 5: Commit**

```bash
git add backend/tests/security/test_project_isolation.py
git commit -m "test: Add repository, research, and knowledge isolation tests (3 tests)

- Test user cannot read other user's repositories
- Test user cannot read other user's research tasks
- Test user cannot read other user's knowledge entries

Tests failing as expected (TDD red phase)"
```

---

## Task 4: Project Isolation Tests (Part 3 - List Filtering)

**Files:**
- Modify: `backend/tests/security/test_project_isolation.py`

**Step 1: Write test for technology list filtering**

Add to `backend/tests/security/test_project_isolation.py`:

```python
@pytest.mark.asyncio
async def test_technology_list_filtered_by_project(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """Technology list is filtered by user's project_id."""
    # Create technologies for both users
    tech_a1 = await TechnologyFactory.create(
        db_session, title="Tech A1", project_id=user_a.project_id
    )
    tech_a2 = await TechnologyFactory.create(
        db_session, title="Tech A2", project_id=user_a.project_id
    )
    tech_b1 = await TechnologyFactory.create(
        db_session, title="Tech B1", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries technologies
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/technologies", headers=headers)

    assert response.status_code == 200
    tech_ids = [t["id"] for t in response.json()]

    # Should only see User A's technologies
    assert tech_a1.id in tech_ids
    assert tech_a2.id in tech_ids
    assert tech_b1.id not in tech_ids
```

**Step 2: Write test for repository list filtering**

Add to `backend/tests/security/test_project_isolation.py`:

```python
@pytest.mark.asyncio
async def test_repository_list_filtered_by_project(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """Repository list is filtered by user's project_id."""
    # Create repositories for both users
    repo_a = await RepositoryFactory.create(
        db_session, owner="user-a", name="repo-a", project_id=user_a.project_id
    )
    repo_b = await RepositoryFactory.create(
        db_session, owner="user-b", name="repo-b", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries repositories
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/repositories", headers=headers)

    assert response.status_code == 200
    repo_ids = [r["id"] for r in response.json()]

    # Should only see User A's repositories
    assert repo_a.id in repo_ids
    assert repo_b.id not in repo_ids
```

**Step 3: Write test for research list filtering**

Add to `backend/tests/security/test_project_isolation.py`:

```python
@pytest.mark.asyncio
async def test_research_list_filtered_by_project(
    user_a, user_b, client, auth_headers_factory, db_session
):
    """Research task list is filtered by user's project_id."""
    # Create research tasks for both users
    research_a = await ResearchTaskFactory.create(
        db_session, title="Research A", project_id=user_a.project_id
    )
    research_b = await ResearchTaskFactory.create(
        db_session, title="Research B", project_id=user_b.project_id
    )
    await db_session.commit()

    # User A queries research tasks
    headers = auth_headers_factory(user_a)
    response = await client.get("/api/v1/research", headers=headers)

    assert response.status_code == 200
    research_ids = [r["id"] for r in response.json()]

    # Should only see User A's research
    assert research_a.id in research_ids
    assert research_b.id not in research_ids
```

**Step 4: Run tests to verify they fail**

Run:
```bash
cd backend
pytest tests/security/test_project_isolation.py -v -k "filtered"
```

Expected: 3 FAIL (filtering not yet implemented)

**Step 5: Commit**

```bash
git add backend/tests/security/test_project_isolation.py
git commit -m "test: Add list filtering isolation tests (3 tests)

- Test technology list filtered by project_id
- Test repository list filtered by project_id
- Test research list filtered by project_id

Tests failing as expected (TDD red phase)"
```

---

## Task 5: Project Isolation Tests (Part 4 - Foreign Key Validation)

**Files:**
- Modify: `backend/tests/security/test_project_isolation.py`

**Step 1: Write test for cross-project foreign key rejection**

Add to `backend/tests/security/test_project_isolation.py`:

```python
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_cross_project_foreign_key_rejected(
    user_a, user_b, db_session
):
    """Cannot create ResearchTask with another user's technology."""
    # Create technology for User B
    tech_b = await TechnologyFactory.create(
        db_session,
        title="Tech B",
        project_id=user_b.project_id
    )
    await db_session.commit()

    # Try to create ResearchTask for User A with User B's technology
    with pytest.raises((IntegrityError, ValueError)):
        research = await ResearchTaskFactory.create(
            db_session,
            title="My Research",
            project_id=user_a.project_id,
            technology_id=tech_b.id  # Cross-project reference
        )
        await db_session.commit()
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd backend
pytest tests/security/test_project_isolation.py::test_cross_project_foreign_key_rejected -v
```

Expected: FAIL (validation not yet implemented)

**Step 3: Commit**

```bash
git add backend/tests/security/test_project_isolation.py
git commit -m "test: Add cross-project foreign key validation test (1 test)

Test that cross-project foreign key references are rejected

Total project isolation tests: 10 (all failing as expected)"
```

---

## Task 6: JWT Security Tests (Part 1 - Token Tampering)

**Files:**
- Create: `backend/tests/security/test_jwt_security.py`

**Step 1: Write test for tampered signature rejection**

Create `backend/tests/security/test_jwt_security.py`:

```python
"""JWT security tests."""
import pytest
from datetime import timedelta


@pytest.mark.asyncio
async def test_tampered_signature_rejected(jwt_token_factory, client):
    """Token with modified signature is rejected."""
    token = jwt_token_factory(
        user_id="user1",
        tampered=True,
        tamper_type="signature"
    )

    response = await client.get(
        "/api/v1/technologies",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower() or \
           "signature" in response.json()["detail"].lower()
```

**Step 2: Write test for tampered payload rejection**

Add to `backend/tests/security/test_jwt_security.py`:

```python
@pytest.mark.asyncio
async def test_tampered_payload_rejected(jwt_token_factory, client):
    """Token with modified payload is rejected."""
    token = jwt_token_factory(
        user_id="user1",
        tampered=True,
        tamper_type="payload"
    )

    response = await client.get(
        "/api/v1/technologies",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()
```

**Step 3: Run tests to verify they fail**

Run:
```bash
cd backend
pytest tests/security/test_jwt_security.py -v -k "tampered"
```

Expected: FAIL if JWT validation not strict (or PASS if already implemented)

**Step 4: Commit**

```bash
git add backend/tests/security/test_jwt_security.py
git commit -m "test: Add JWT tampering tests (2 tests)

- Test token with tampered signature rejected
- Test token with tampered payload rejected"
```

---

## Task 7: JWT Security Tests (Part 2 - Expiration & Format)

**Files:**
- Modify: `backend/tests/security/test_jwt_security.py`

**Step 1: Write test for expired token rejection**

Add to `backend/tests/security/test_jwt_security.py`:

```python
import time


@pytest.mark.asyncio
async def test_expired_token_rejected(jwt_token_factory, client):
    """Expired token returns 401."""
    # Create token that expires in 1 second
    token = jwt_token_factory(
        user_id="user1",
        expires_delta=timedelta(seconds=1)
    )

    # Wait for expiration
    time.sleep(2)

    response = await client.get(
        "/api/v1/technologies",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
```

**Step 2: Write test for invalid token format rejection**

Add to `backend/tests/security/test_jwt_security.py`:

```python
@pytest.mark.asyncio
async def test_invalid_token_format_rejected(client):
    """Token with invalid format is rejected."""
    invalid_tokens = [
        "not.a.token",
        "only-one-part",
        "two.parts",
        "invalid-base64!@#$",
        "",
    ]

    for token in invalid_tokens:
        response = await client.get(
            "/api/v1/technologies",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401, f"Invalid token '{token}' should return 401"
```

**Step 3: Write test for malformed token rejection**

Add to `backend/tests/security/test_jwt_security.py`:

```python
@pytest.mark.asyncio
async def test_malformed_token_returns_401_not_500(client):
    """Malformed JWT returns 401, not 500 internal error."""
    response = await client.get(
        "/api/v1/technologies",
        headers={"Authorization": "Bearer completely-invalid-token"}
    )

    # Should return 401 (authentication error), not 500 (server error)
    assert response.status_code == 401

    # Should have meaningful error message
    detail = response.json().get("detail", "").lower()
    assert "invalid" in detail or "token" in detail
```

**Step 4: Run tests to verify behavior**

Run:
```bash
cd backend
pytest tests/security/test_jwt_security.py -v
```

Expected: PASS or FAIL depending on current JWT validation implementation

**Step 5: Commit**

```bash
git add backend/tests/security/test_jwt_security.py
git commit -m "test: Add JWT expiration and format tests (3 tests)

- Test expired token rejected
- Test invalid token format rejected
- Test malformed token returns 401 not 500

Total JWT security tests: 5"
```

---

## Task 8: RBAC Basic Tests

**Files:**
- Create: `backend/tests/security/test_rbac_basic.py`

**Step 1: Write test for user deletion restriction**

Create `backend/tests/security/test_rbac_basic.py`:

```python
"""Basic RBAC authorization tests."""
import pytest


@pytest.mark.asyncio
async def test_regular_user_cannot_delete_other_users(
    user_a, user_b, client, auth_headers_factory
):
    """Non-admin user cannot delete other users."""
    headers = auth_headers_factory(user_a)
    response = await client.delete(
        f"/api/v1/users/{user_b.id}",
        headers=headers
    )

    # Should return 403 Forbidden
    assert response.status_code == 403
    assert "forbidden" in response.json()["detail"].lower() or \
           "permission" in response.json()["detail"].lower()
```

**Step 2: Write test for project owner access**

Add to `backend/tests/security/test_rbac_basic.py`:

```python
@pytest.mark.asyncio
async def test_project_owner_has_full_access(
    user_a, client, auth_headers_factory, db_session
):
    """Project owner has full access to their project resources."""
    # Create technology as project owner
    tech = await TechnologyFactory.create(
        db_session,
        title="Owner Tech",
        project_id=user_a.project_id
    )
    await db_session.commit()

    headers = auth_headers_factory(user_a)

    # Should be able to read
    response = await client.get(f"/api/v1/technologies/{tech.id}", headers=headers)
    assert response.status_code == 200

    # Should be able to update
    response = await client.put(
        f"/api/v1/technologies/{tech.id}",
        headers=headers,
        json={"title": "Updated Title"}
    )
    assert response.status_code == 200

    # Should be able to delete
    response = await client.delete(f"/api/v1/technologies/{tech.id}", headers=headers)
    assert response.status_code == 204 or response.status_code == 200
```

**Step 3: Write test for non-owner read-only access (if roles exist)**

Add to `backend/tests/security/test_rbac_basic.py`:

```python
@pytest.mark.asyncio
async def test_non_owner_has_read_only_access(
    user_a, client, auth_headers_factory, db_session
):
    """Non-owner has read-only access to shared project resources.

    Note: This test assumes role-based access is implemented.
    If not, this test will be skipped or modified.
    """
    # Create a viewer/member user for same project
    viewer = await UserFactory.create(
        db_session,
        email="viewer@test.com",
        project_id=user_a.project_id,
        role="viewer"  # If roles not implemented, use "member"
    )

    # Create technology as owner
    tech = await TechnologyFactory.create(
        db_session,
        title="Shared Tech",
        project_id=user_a.project_id
    )
    await db_session.commit()

    headers = auth_headers_factory(viewer)

    # Should be able to read
    response = await client.get(f"/api/v1/technologies/{tech.id}", headers=headers)
    assert response.status_code == 200

    # Should NOT be able to update
    response = await client.put(
        f"/api/v1/technologies/{tech.id}",
        headers=headers,
        json={"title": "Hacked"}
    )
    assert response.status_code == 403

    # Should NOT be able to delete
    response = await client.delete(f"/api/v1/technologies/{tech.id}", headers=headers)
    assert response.status_code == 403
```

**Step 4: Run tests to verify behavior**

Run:
```bash
cd backend
pytest tests/security/test_rbac_basic.py -v
```

Expected: FAIL if RBAC not implemented, PASS if already in place

**Step 5: Commit**

```bash
git add backend/tests/security/test_rbac_basic.py
git commit -m "test: Add basic RBAC tests (3 tests)

- Test regular user cannot delete other users
- Test project owner has full access
- Test non-owner has read-only access (if roles implemented)

Total RBAC tests: 3"
```

---

## Task 9: Documentation & Summary

**Files:**
- Create: `backend/tests/security/README.md`
- Modify: `docs/TESTING_WEEK2.md` (if doesn't exist, reference design doc)

**Step 1: Write security tests README**

Create `backend/tests/security/README.md`:

```markdown
# Security Tests

## Overview

Security tests validate project isolation, JWT authentication, and basic RBAC authorization.

## Test Structure

### Project Isolation Tests (`test_project_isolation.py`)

**Goal:** Ensure users can only access their own project data.

**Tests (10 total):**
- User cannot read other user's technologies (3 tests: read, modify, delete)
- User cannot read other user's repositories (1 test)
- User cannot read other user's research tasks (1 test)
- User cannot read other user's knowledge entries (1 test)
- List endpoints filtered by project_id (3 tests)
- Cross-project foreign key references rejected (1 test)

**Key Fixtures:**
- `user_a`: User with project-a
- `user_b`: User with project-b
- `auth_headers_factory`: Creates auth headers for user

### JWT Security Tests (`test_jwt_security.py`)

**Goal:** Validate JWT token security and proper error handling.

**Tests (5 total):**
- Tampered signature rejected (1 test)
- Tampered payload rejected (1 test)
- Expired token rejected (1 test)
- Invalid token format rejected (1 test)
- Malformed token returns 401 not 500 (1 test)

**Key Fixtures:**
- `jwt_token_factory`: Creates tokens with optional tampering

### RBAC Basic Tests (`test_rbac_basic.py`)

**Goal:** Validate basic role-based access control.

**Tests (3 total):**
- Regular user cannot delete other users (1 test)
- Project owner has full access (1 test)
- Non-owner has read-only access (1 test)

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
pytest tests/security/test_jwt_security.py::test_expired_token_rejected -v
```

**In Docker:**
```bash
make test-security
```

## Test Count

**Total: 18 tests**
- Project isolation: 10 tests
- JWT security: 5 tests
- RBAC basic: 3 tests

## Notes

- All tests use mocked dependencies (no real external services)
- Tests follow TDD approach (written before implementation)
- Tests are designed to fail initially (red phase)
- Implementation should make tests pass (green phase)
```

**Step 2: Create summary document**

Create `backend/tests/security/IMPLEMENTATION_SUMMARY.md`:

```markdown
# Security Tests Implementation Summary

**Branch:** `testing/week2-security`
**Date:** 2025-10-28
**Status:** ✅ Complete

## Deliverables

### Tests Implemented: 18

1. **Project Isolation (10 tests)**
   - ✅ User cannot read other user's technologies
   - ✅ User cannot modify other user's technologies
   - ✅ User cannot delete other user's technologies
   - ✅ User cannot read other user's repositories
   - ✅ User cannot read other user's research tasks
   - ✅ User cannot read other user's knowledge entries
   - ✅ Technology list filtered by project_id
   - ✅ Repository list filtered by project_id
   - ✅ Research list filtered by project_id
   - ✅ Cross-project foreign key references rejected

2. **JWT Security (5 tests)**
   - ✅ Tampered signature rejected
   - ✅ Tampered payload rejected
   - ✅ Expired token rejected
   - ✅ Invalid token format rejected
   - ✅ Malformed token returns 401 not 500

3. **RBAC Basic (3 tests)**
   - ✅ Regular user cannot delete other users
   - ✅ Project owner has full access
   - ✅ Non-owner has read-only access

### Infrastructure Created

- ✅ `backend/tests/security/conftest.py` - Security fixtures
- ✅ `backend/tests/security/test_project_isolation.py` - 10 tests
- ✅ `backend/tests/security/test_jwt_security.py` - 5 tests
- ✅ `backend/tests/security/test_rbac_basic.py` - 3 tests
- ✅ `backend/tests/security/README.md` - Documentation

### Test Execution

```bash
# Run all security tests
cd backend
pytest tests/security/ -v

# Expected: Tests may FAIL initially (TDD red phase)
# Implementation needed to make tests pass
```

## Next Steps

1. **Implement project isolation in API endpoints:**
   - Add project_id filtering to all list endpoints
   - Add project_id validation to all detail endpoints
   - Add database-level constraints

2. **Verify JWT security:**
   - Ensure JWT validation is strict
   - Handle all error cases gracefully
   - Return 401 for all auth failures

3. **Implement basic RBAC:**
   - Add role field to User model (if not exists)
   - Implement role checking in endpoints
   - Add permission decorators/middleware

4. **Run tests after implementation:**
   ```bash
   pytest tests/security/ -v
   ```
   Expected: All 18 tests PASS

## Files Created

- `backend/tests/security/__init__.py`
- `backend/tests/security/conftest.py`
- `backend/tests/security/test_project_isolation.py`
- `backend/tests/security/test_jwt_security.py`
- `backend/tests/security/test_rbac_basic.py`
- `backend/tests/security/README.md`
- `backend/tests/security/IMPLEMENTATION_SUMMARY.md`

## Commits

Total commits: 9
- Infrastructure setup (1)
- Project isolation tests (4)
- JWT security tests (2)
- RBAC tests (1)
- Documentation (1)

## Success Metrics

- ✅ 18 tests implemented
- ✅ Test infrastructure complete
- ✅ All tests syntactically valid
- ✅ Documentation complete
- ✅ Ready for consolidation
```

**Step 3: Commit documentation**

```bash
git add backend/tests/security/README.md backend/tests/security/IMPLEMENTATION_SUMMARY.md
git commit -m "docs: Add security tests documentation

- Create README with test overview and running instructions
- Create implementation summary with deliverables checklist
- Document test structure and next steps

Week 2 Security Track Complete: 18 tests + infrastructure + docs"
```

**Step 4: Verify all tests are discoverable**

Run:
```bash
cd backend
pytest tests/security/ --collect-only
```

Expected output showing 18 tests collected

**Step 5: Final commit with summary**

```bash
git commit --allow-empty -m "test: Week 2 Security Tests - Track Complete

Summary:
- 18 security tests implemented
- Project isolation: 10 tests
- JWT security: 5 tests
- RBAC basic: 3 tests

Infrastructure:
- Security test fixtures (user_a, user_b, jwt_token_factory)
- Auth headers factory
- Complete test documentation

Status: Ready for consolidation to main branch

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

Before marking track complete:

- [ ] All 18 tests implemented and syntactically valid
- [ ] Tests organized in 3 files (isolation, JWT, RBAC)
- [ ] Security fixtures complete (user_a, user_b, jwt_token_factory)
- [ ] README.md created with test overview
- [ ] IMPLEMENTATION_SUMMARY.md created with deliverables
- [ ] All tests discoverable via pytest --collect-only
- [ ] No syntax errors in test files
- [ ] Git commits follow conventions
- [ ] Branch ready for merge to main

## Notes for Implementation

**These tests are designed to FAIL initially** (TDD red phase). This is expected and correct.

After tests are written, implementation work is needed:

1. **API Layer:** Add project_id filtering to all endpoints
2. **Service Layer:** Add project_id validation
3. **Database:** Add project_id constraints
4. **Auth:** Ensure strict JWT validation
5. **RBAC:** Implement role-based permissions

Once implementation is complete, re-run tests:
```bash
pytest tests/security/ -v
```

Expected: All 18 tests PASS (TDD green phase)

---

**Plan Status:** Complete
**Next Action:** Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan
**Estimated Time:** 3-4 hours for test implementation
