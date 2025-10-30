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
                rag_service = RAGService()
                documents_ingested = 0

                for entry in entries:
                    try:
                        # Add document to RAG system
                        rag_service.add_document(
                            project_id=source.project_id,
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
