"""
Integration tests for documentation ingestion
"""
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_source import IngestionSource, SourceStatus, SourceType
from app.models.project import Project
from app.services.documentation_scraper_service import DocumentationPage
from app.tasks.ingestion_tasks import scrape_documentation


@pytest.fixture
async def docs_source(db_session: AsyncSession, sample_project: Project) -> IngestionSource:
    """Create a documentation ingestion source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.DOCUMENTATION,
        name="FastAPI Docs",
        url="https://fastapi.tiangolo.com",
        priority=9,
        enabled=True,
        config={"max_depth": 2, "max_pages": 50},
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


@pytest.mark.asyncio
async def test_scrape_documentation_success(db_session: AsyncSession, docs_source: IngestionSource):
    """Test successful documentation scraping"""
    mock_pages = [
        DocumentationPage(
            url="https://fastapi.tiangolo.com/tutorial",
            title="Tutorial - FastAPI",
            content="FastAPI is a modern web framework...",
            headings=["Introduction", "Installation"],
            code_blocks=["pip install fastapi"],
        ),
        DocumentationPage(
            url="https://fastapi.tiangolo.com/features",
            title="Features - FastAPI",
            content="FastAPI provides automatic API documentation...",
            headings=["Automatic Docs", "Type Hints"],
            code_blocks=[],
        ),
    ]

    with patch(
        "app.services.documentation_scraper_service.DocumentationScraperService.scrape_documentation",
        return_value=mock_pages,
    ):
        with patch(
            "app.services.rag_service.RAGService.add_document", new_callable=AsyncMock
        ) as mock_add_doc:
            result = scrape_documentation(docs_source.id)

    assert result["status"] == "success"
    assert result["documents_ingested"] == 2

    # Verify source status
    await db_session.refresh(docs_source)
    assert docs_source.status == SourceStatus.SUCCESS
    assert docs_source.documents_ingested == 2


@pytest.mark.asyncio
async def test_scrape_documentation_with_sitemap(
    db_session: AsyncSession, docs_source: IngestionSource
):
    """Test documentation scraping using sitemap"""
    docs_source.config = {
        "use_sitemap": True,
        "sitemap_url": "https://fastapi.tiangolo.com/sitemap.xml",
    }
    await db_session.commit()

    mock_pages = [
        DocumentationPage(
            url="https://fastapi.tiangolo.com/page1",
            title="Page 1",
            content="Content 1",
            headings=["H1"],
        )
    ]

    with patch(
        "app.services.documentation_scraper_service.DocumentationScraperService.fetch_sitemap",
        return_value=["https://fastapi.tiangolo.com/page1"],
    ):
        with patch(
            "app.services.documentation_scraper_service.DocumentationScraperService.scrape_page",
            return_value=mock_pages[0],
        ):
            with patch("app.services.rag_service.RAGService.add_document", new_callable=AsyncMock):
                result = scrape_documentation(docs_source.id)

    assert result["status"] == "success"
