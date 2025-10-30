"""
Integration tests for RSS feed ingestion
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_source import IngestionSource, SourceType, SourceStatus
from app.models.project import Project
from app.tasks.ingestion_tasks import scrape_rss_feed
from app.services.feed_scraper_service import FeedEntry


@pytest.fixture
async def rss_source(db_session: AsyncSession, sample_project: Project) -> IngestionSource:
    """Create an RSS ingestion source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Test RSS Feed",
        url="https://example.com/feed.xml",
        priority=7,
        enabled=True
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)
    return source


@pytest.mark.asyncio
async def test_scrape_rss_feed_success(db_session: AsyncSession, rss_source: IngestionSource):
    """Test successful RSS feed scraping"""
    mock_entries = [
        FeedEntry(
            title="Test Article 1",
            url="https://example.com/article1",
            content="Full content of article 1",
            summary="Summary 1",
            published=datetime(2024, 1, 15, 10, 30),
            author="John Doe",
            tags=["python", "testing"]
        ),
        FeedEntry(
            title="Test Article 2",
            url="https://example.com/article2",
            content="Full content of article 2",
            summary="Summary 2",
            published=datetime(2024, 1, 16, 14, 0),
            author="Jane Smith",
            tags=["fastapi"]
        )
    ]

    with patch('app.services.feed_scraper_service.FeedScraperService.parse_feed',
               return_value=mock_entries):
        with patch('app.services.rag_service.RAGService.add_document') as mock_add_doc:
            # Execute task
            result = scrape_rss_feed(rss_source.id)

    # Verify result
    assert result['status'] == 'success'
    assert result['documents_ingested'] == 2

    # Verify source status updated
    await db_session.refresh(rss_source)
    assert rss_source.status == SourceStatus.SUCCESS
    assert rss_source.documents_ingested == 2
    assert rss_source.last_run is not None
    assert rss_source.last_success is not None

    # Verify RAG service called for each entry
    assert mock_add_doc.call_count == 2


@pytest.mark.asyncio
async def test_scrape_rss_feed_with_errors(db_session: AsyncSession, rss_source: IngestionSource):
    """Test RSS feed scraping with errors"""
    with patch('app.services.feed_scraper_service.FeedScraperService.parse_feed',
               side_effect=ValueError("Feed is malformed")):
        result = scrape_rss_feed(rss_source.id)

    # Verify error handling
    assert result['status'] == 'error'
    assert 'Feed is malformed' in result['error']

    # Verify source status updated
    await db_session.refresh(rss_source)
    assert rss_source.status == SourceStatus.ERROR
    assert rss_source.error_count == 1
    assert rss_source.last_error is not None


@pytest.mark.asyncio
async def test_scrape_disabled_source(db_session: AsyncSession, rss_source: IngestionSource):
    """Test that disabled sources are not scraped"""
    rss_source.enabled = False
    await db_session.commit()

    result = scrape_rss_feed(rss_source.id)

    assert result['status'] == 'skipped'
    assert 'disabled' in result['message'].lower()
