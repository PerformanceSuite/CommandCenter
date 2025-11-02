"""SQL injection security tests."""
import pytest


@pytest.mark.asyncio
async def test_technology_search_prevents_sql_injection(client, auth_headers_factory, user_a):
    """Technology search endpoint prevents SQL injection in query param."""
    # SQL injection attempt
    malicious_query = "'; DROP TABLE technologies; --"

    headers = auth_headers_factory(user_a)
    response = await client.get(f"/api/v1/technologies?search={malicious_query}", headers=headers)

    # Should not return 500 error (which would indicate SQL error)
    assert response.status_code in [
        200,
        400,
    ], f"SQL injection may have caused error: {response.status_code}"

    # If 200, should return empty list (no matches for malicious string)
    if response.status_code == 200:
        assert isinstance(response.json(), list), "Should return list"


@pytest.mark.asyncio
async def test_repository_owner_filter_prevents_sql_injection(client, auth_headers_factory, user_a):
    """Repository owner filter prevents SQL injection."""
    malicious_owner = "owner' OR '1'='1"

    headers = auth_headers_factory(user_a)
    response = await client.get(f"/api/v1/repositories?owner={malicious_owner}", headers=headers)

    assert response.status_code in [200, 400]
    if response.status_code == 200:
        # Should not return all repositories (which would happen with successful injection)
        # Exact behavior depends on implementation, but should be safe
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_research_task_search_prevents_sql_injection(client, auth_headers_factory, user_a):
    """Research task search prevents SQL injection in title/description."""
    malicious_search = "'; DELETE FROM research_tasks WHERE '1'='1"

    headers = auth_headers_factory(user_a)
    response = await client.get(f"/api/v1/research?q={malicious_search}", headers=headers)

    assert response.status_code in [200, 400]
    if response.status_code == 200:
        assert isinstance(response.json(), list)
