"""
Celery tasks for automated knowledge ingestion
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any
from celery import Task
from sqlalchemy import select

from app.tasks import celery_app
from app.models.ingestion_source import IngestionSource, SourceType, SourceStatus
from app.services.feed_scraper_service import FeedScraperService
from app.services.documentation_scraper_service import DocumentationScraperService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class IngestionTask(Task):
    """Base task for ingestion with error handling"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True


@celery_app.task(base=IngestionTask, bind=True)
def scrape_rss_feed(self, source_id: int) -> Dict[str, Any]:
    """
    Scrape RSS feed and ingest documents into RAG system.

    Args:
        source_id: ID of IngestionSource

    Returns:
        Dict with status, documents_ingested, and optional error
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.config import settings

    # Create async database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _scrape_feed():
        async with async_session_maker() as db:
            source = None
            try:
                # Load source
                result = await db.execute(
                    select(IngestionSource).where(IngestionSource.id == source_id)
                )
                source = result.scalar_one_or_none()

                if not source:
                    logger.error(f"Ingestion source {source_id} not found")
                    return {'status': 'error', 'error': 'Source not found'}

                # Check if enabled
                if not source.enabled:
                    logger.info(f"Skipping disabled source: {source.name}")
                    return {'status': 'skipped', 'message': 'Source is disabled'}

                # Update status to running
                source.status = SourceStatus.RUNNING
                source.last_run = datetime.utcnow()
                await db.commit()

                # Parse feed
                feed_scraper = FeedScraperService()
                entries = feed_scraper.parse_feed(source.url)

                # Deduplicate
                entries = feed_scraper.deduplicate_entries(entries)

                # Ingest into RAG
                rag_service = RAGService(repository_id=source.project_id)
                await rag_service.initialize()
                documents_ingested = 0

                for entry in entries:
                    try:
                        # Add document to RAG system
                        await rag_service.add_document(
                            content=entry.content,
                            metadata={
                                'title': entry.title,
                                'url': entry.url,
                                'author': entry.author,
                                'published': entry.published.isoformat() if entry.published else None,
                                'tags': entry.tags,
                                'source_type': 'rss',
                                'source_id': source.id,
                                'source_name': source.name,
                                'priority': source.priority
                            }
                        )
                        documents_ingested += 1
                    except Exception as e:
                        logger.error(f"Failed to ingest entry '{entry.title}': {e}")
                        continue

                # Update source status
                source.status = SourceStatus.SUCCESS
                source.last_success = datetime.utcnow()
                source.documents_ingested += documents_ingested
                source.error_count = 0  # Reset error count on success
                source.last_error = None
                await db.commit()

                logger.info(f"RSS scraping complete: {documents_ingested} documents ingested from {source.name}")

                return {
                    'status': 'success',
                    'documents_ingested': documents_ingested,
                    'source_name': source.name
                }

            except Exception as e:
                logger.error(f"RSS scraping failed for source {source_id}: {e}")

                # Update source status
                if source:
                    source.status = SourceStatus.ERROR
                    source.error_count += 1
                    source.last_error = str(e)
                    await db.commit()

                return {
                    'status': 'error',
                    'error': str(e),
                    'source_id': source_id
                }
            finally:
                await engine.dispose()

    # Run the async function
    # Apply nest_asyncio to allow nested event loops (needed for testing)
    import nest_asyncio
    nest_asyncio.apply()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create task in existing loop
            return loop.run_until_complete(_scrape_feed())
    except RuntimeError:
        pass

    # Create new event loop
    return asyncio.run(_scrape_feed())


@celery_app.task(base=IngestionTask, bind=True)
def scrape_documentation(self, source_id: int) -> Dict[str, Any]:
    """
    Scrape documentation website and ingest into RAG system.

    Args:
        source_id: ID of IngestionSource

    Returns:
        Dict with status, documents_ingested, and optional error
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.config import settings

    # Create async database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _scrape_docs():
        async with async_session_maker() as db:
            source = None
            try:
                # Load source
                result = await db.execute(
                    select(IngestionSource).where(IngestionSource.id == source_id)
                )
                source = result.scalar_one_or_none()

                if not source:
                    logger.error(f"Ingestion source {source_id} not found")
                    return {'status': 'error', 'error': 'Source not found'}

                if not source.enabled:
                    logger.info(f"Skipping disabled source: {source.name}")
                    return {'status': 'skipped', 'message': 'Source is disabled'}

                # Update status
                source.status = SourceStatus.RUNNING
                source.last_run = datetime.utcnow()
                await db.commit()

                # Get config
                config = source.config or {}
                max_depth = config.get('max_depth', 3)
                max_pages = config.get('max_pages', 100)
                use_sitemap = config.get('use_sitemap', False)

                # Initialize scraper
                doc_scraper = DocumentationScraperService(rate_limit=1.0)

                # Validate URLs for SSRF protection before starting
                doc_scraper._is_safe_url(source.url)
                if use_sitemap and 'sitemap_url' in config:
                    doc_scraper._is_safe_url(config['sitemap_url'])

                # Scrape pages
                if use_sitemap and 'sitemap_url' in config:
                    # Use sitemap
                    sitemap_urls = doc_scraper.fetch_sitemap(config['sitemap_url'])
                    pages = []
                    for url in sitemap_urls[:max_pages]:
                        if doc_scraper.is_allowed(url):
                            page = doc_scraper.scrape_page(url)
                            if page:
                                pages.append(page)
                else:
                    # Crawl recursively
                    pages = doc_scraper.scrape_documentation(
                        source.url,
                        max_depth=max_depth,
                        max_pages=max_pages
                    )

                # Ingest into RAG
                rag_service = RAGService(repository_id=source.project_id)
                await rag_service.initialize()
                documents_ingested = 0

                for page in pages:
                    try:
                        await rag_service.add_document(
                            content=page.content,
                            metadata={
                                'title': page.title,
                                'url': page.url,
                                'headings': page.headings,
                                'code_blocks': page.code_blocks,
                                'source_type': 'documentation',
                                'source_id': source.id,
                                'source_name': source.name,
                                'priority': source.priority
                            }
                        )
                        documents_ingested += 1
                    except Exception as e:
                        logger.error(f"Failed to ingest page '{page.title}': {e}")
                        continue

                # Update source status
                source.status = SourceStatus.SUCCESS
                source.last_success = datetime.utcnow()
                source.documents_ingested += documents_ingested
                source.error_count = 0
                source.last_error = None
                await db.commit()

                logger.info(f"Documentation scraping complete: {documents_ingested} pages from {source.name}")

                return {
                    'status': 'success',
                    'documents_ingested': documents_ingested,
                    'source_name': source.name
                }

            except Exception as e:
                logger.error(f"Documentation scraping failed: {e}")

                if source:
                    source.status = SourceStatus.ERROR
                    source.error_count += 1
                    source.last_error = str(e)
                    await db.commit()

                return {'status': 'error', 'error': str(e)}

            finally:
                await engine.dispose()

    # Run the async function
    # Apply nest_asyncio to allow nested event loops (needed for testing)
    import nest_asyncio
    nest_asyncio.apply()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create task in existing loop
            return loop.run_until_complete(_scrape_docs())
    except RuntimeError:
        pass

    # Create new event loop
    return asyncio.run(_scrape_docs())
