"""Cross-Site Scripting (XSS) security tests."""
import pytest


@pytest.mark.asyncio
async def test_technology_title_escapes_html(client, auth_headers_factory, user_a, db_session):
    """Technology title with HTML/JS is escaped in API response."""
    from app.services.technology_service import TechnologyService

    # Create technology with XSS payload
    xss_payload = "<script>alert('XSS')</script>"

    service = TechnologyService(db_session)
    tech = await service.create_technology(
        title=xss_payload, domain="security", project_id=user_a.project_id
    )
    await db_session.commit()

    # Retrieve via API
    headers = auth_headers_factory(user_a)
    response = await client.get(f"/api/v1/technologies/{tech.id}", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Verify script tags are escaped or stripped
    assert (
        "<script>" not in data["title"]
    ), "XSS payload should be escaped/sanitized in API response"


@pytest.mark.asyncio
async def test_research_task_description_escapes_html(
    client, auth_headers_factory, user_a, db_session
):
    """Research task description with HTML is escaped."""
    from app.services.research_service import ResearchService

    xss_payload = "<img src=x onerror='alert(1)'>"

    service = ResearchService(db_session)
    research = await service.create_research_task(
        title="Test", description=xss_payload, project_id=user_a.project_id
    )
    await db_session.commit()

    headers = auth_headers_factory(user_a)
    response = await client.get(f"/api/v1/research/{research.id}", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Verify HTML tags are escaped
    assert (
        "<img" not in data["description"] or "onerror" not in data["description"]
    ), "XSS payload should be escaped/sanitized"


@pytest.mark.asyncio
async def test_knowledge_entry_source_escapes_html(
    client, auth_headers_factory, user_a, db_session
):
    """Knowledge entry source with HTML is escaped."""
    from app.models.knowledge_entry import KnowledgeEntry

    xss_payload = "<iframe src='javascript:alert(1)'></iframe>"

    entry = KnowledgeEntry(source=xss_payload, category="test", project_id=user_a.project_id)
    db_session.add(entry)
    await db_session.commit()

    headers = auth_headers_factory(user_a)
    response = await client.get(f"/api/v1/knowledge/entries/{entry.id}", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Verify iframe tags are escaped
    assert "<iframe" not in data["source"], "XSS payload should be escaped/sanitized"
