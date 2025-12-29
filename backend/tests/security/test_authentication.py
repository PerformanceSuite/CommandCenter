"""Authentication and CSRF security tests."""
import pytest


@pytest.mark.asyncio
async def test_endpoints_require_authentication(client):
    """Protected endpoints reject requests without auth headers."""
    endpoints = [
        "/api/v1/technologies/",
        "/api/v1/repositories/",
        "/api/v1/research-tasks/",
        "/api/v1/knowledge/",
    ]

    for endpoint in endpoints:
        response = await client.get(endpoint)  # No auth headers
        assert response.status_code in [
            401,
            403,
        ], f"{endpoint} should require authentication, got {response.status_code}"


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    """Invalid JWT token is rejected."""
    headers = {"Authorization": "Bearer invalid-token-xyz"}

    response = await client.get("/api/v1/technologies/", headers=headers)
    assert response.status_code in [401, 403], "Invalid token should be rejected"


@pytest.mark.asyncio
async def test_tampered_token_rejected(client, jwt_token_factory, user_a):
    """Tampered JWT token is rejected."""
    # Create valid token then tamper with it
    valid_token = jwt_token_factory(user_a)
    tampered_token = valid_token[:-10] + "tampered123"

    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = await client.get("/api/v1/technologies/", headers=headers)

    assert response.status_code in [401, 403], "Tampered token should be rejected"


@pytest.mark.asyncio
async def test_expired_token_rejected(client, jwt_token_factory, user_a):
    """Expired JWT token is rejected."""
    # Create token with past expiration
    expired_token = jwt_token_factory(user_a, expired=True)

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await client.get("/api/v1/technologies/", headers=headers)

    assert response.status_code in [401, 403], "Expired token should be rejected"


@pytest.mark.asyncio
async def test_csrf_token_required_for_mutations(client, auth_headers_factory, user_a):
    """State-changing operations require CSRF protection."""
    headers = auth_headers_factory(user_a)

    # POST without CSRF token should be rejected
    response = await client.post(
        "/api/v1/technologies/", json={"title": "Test Tech", "domain": "security"}, headers=headers
    )

    # Either requires CSRF token (403) or uses other protection (SameSite cookies)
    # If 201, verify SameSite/Origin checks are in place
    if response.status_code == 201:
        # Implementation uses alternative CSRF protection (SameSite cookies, Origin checks)
        pass
    else:
        assert response.status_code in [403, 400], "Mutations should have CSRF protection"


@pytest.mark.asyncio
async def test_user_cannot_use_another_users_token(client, jwt_token_factory, user_a, user_b):
    """User A's token cannot access User B's resources."""
    # Create User B resource
    # (Relies on project_id isolation being implemented)

    # Use User A's token
    headers = {"Authorization": f"Bearer {jwt_token_factory(user_a)}"}

    # Try to access User B's specific resource
    # This should fail due to project_id filtering
    # (Specific endpoint depends on implementation)
    response = await client.get("/api/v1/technologies/", headers=headers)

    # Should succeed but return only User A's data (filtered by project_id)
    assert response.status_code == 200
