"""
Celery tasks for automated knowledge ingestion
"""
import logging
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from celery import Task
from sqlalchemy import select

from app.tasks import celery_app
from app.models.ingestion_source import IngestionSource, SourceType, SourceStatus
from app.services.feed_scraper_service import FeedScraperService
from app.services.documentation_scraper_service import DocumentationScraperService
from app.services.rag_service import RAGService
from app.services.file_watcher_service import FileWatcherService, FileChangeEvent

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


@celery_app.task(base=IngestionTask, bind=True)
def process_webhook_payload(
    self,
    source_id: Optional[int],
    payload: Dict[str, Any],
    event_type: str,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process webhook payload and ingest into RAG system.

    Args:
        source_id: ID of IngestionSource (None for generic webhooks)
        payload: Webhook payload
        event_type: Type of event (release, push, generic, etc.)
        project_id: Project ID (for generic webhooks)

    Returns:
        Dict with status and documents_ingested
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.config import settings

    # Create async database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _process_webhook():
        async with async_session_maker() as db:
            source = None
            try:
                # Load source if provided
                if source_id:
                    result = await db.execute(
                        select(IngestionSource).where(IngestionSource.id == source_id)
                    )
                    source = result.scalar_one_or_none()

                    if not source:
                        return {'status': 'error', 'error': 'Source not found'}

                    project_id_to_use = source.project_id
                else:
                    project_id_to_use = project_id

                if not project_id_to_use:
                    return {'status': 'error', 'error': 'Project ID required'}

                # Update source status if exists
                if source:
                    source.status = SourceStatus.RUNNING
                    source.last_run = datetime.utcnow()
                    await db.commit()

                # Extract content based on event type
                documents = []

                if event_type == 'release':
                    # GitHub release event
                    release = payload.get('release', {})
                    documents.append({
                        'title': f"Release: {release.get('name', release.get('tag_name'))}",
                        'content': release.get('body', ''),
                        'url': release.get('html_url'),
                        'metadata': {
                            'event_type': 'release',
                            'tag': release.get('tag_name'),
                            'repository': payload.get('repository', {}).get('full_name'),
                            'published_at': release.get('published_at')
                        }
                    })

                elif event_type == 'push':
                    # GitHub push event
                    for commit in payload.get('commits', []):
                        documents.append({
                            'title': f"Commit: {commit.get('message', '').split(chr(10))[0]}",
                            'content': commit.get('message', ''),
                            'url': commit.get('url'),
                            'metadata': {
                                'event_type': 'commit',
                                'sha': commit.get('id'),
                                'author': commit.get('author', {}).get('name'),
                                'repository': payload.get('repository', {}).get('full_name')
                            }
                        })

                elif event_type == 'generic':
                    # Generic webhook
                    documents.append({
                        'title': payload.get('title'),
                        'content': payload.get('content'),
                        'url': payload.get('url'),
                        'metadata': payload.get('metadata', {})
                    })

                # Ingest documents
                rag_service = RAGService(repository_id=project_id_to_use)
                await rag_service.initialize()
                documents_ingested = 0

                for doc in documents:
                    try:
                        metadata = doc.get('metadata', {})
                        metadata.update({
                            'source_type': 'webhook',
                            'event_type': event_type
                        })

                        if source:
                            metadata.update({
                                'source_id': source.id,
                                'source_name': source.name,
                                'priority': source.priority
                            })

                        await rag_service.add_document(
                            content=doc['content'],
                            metadata=metadata
                        )
                        documents_ingested += 1

                    except Exception as e:
                        logger.error(f"Failed to ingest webhook document: {e}")
                        continue

                # Update source status
                if source:
                    source.status = SourceStatus.SUCCESS
                    source.last_success = datetime.utcnow()
                    source.documents_ingested += documents_ingested
                    source.error_count = 0
                    source.last_error = None
                    await db.commit()

                logger.info(f"Webhook processing complete: {documents_ingested} documents ingested")

                return {
                    'status': 'success',
                    'documents_ingested': documents_ingested,
                    'event_type': event_type
                }

            except Exception as e:
                logger.error(f"Webhook processing failed: {e}")

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
            return loop.run_until_complete(_process_webhook())
    except RuntimeError:
        pass

    # Create new event loop
    return asyncio.run(_process_webhook())


@celery_app.task(base=IngestionTask, bind=True)
def process_file_change(
    self,
    source_id: int,
    event: FileChangeEvent
) -> Dict[str, Any]:
    """
    Process file system change and ingest document.

    Args:
        source_id: ID of IngestionSource
        event: FileChangeEvent with file path and event type

    Returns:
        Dict with status and documents_ingested
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.config import settings

    # Create async database connection
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _process_file():
        async with async_session_maker() as db:
            source = None
            try:
                # Load source
                result = await db.execute(
                    select(IngestionSource).filter(IngestionSource.id == source_id)
                )
                source = result.scalar_one_or_none()

                if not source:
                    return {'status': 'error', 'error': 'Source not found'}

                if not source.enabled:
                    return {'status': 'skipped', 'message': 'Source is disabled'}

                # Get config
                config = source.config or {}
                patterns = config.get('patterns', ['*'])
                ignore_patterns = config.get('ignore', [])

                # Initialize file watcher service
                file_watcher = FileWatcherService()

                # Get file path from event (handle both FileChangeEvent and dict)
                file_path = event.file_path if hasattr(event, 'file_path') else event['file_path']
                event_type = event.event_type if hasattr(event, 'event_type') else event['event_type']

                # Check patterns
                if not file_watcher.should_process_file(file_path, patterns):
                    return {'status': 'skipped', 'message': 'File does not match patterns'}

                if file_watcher.should_ignore_file(file_path, ignore_patterns):
                    return {'status': 'skipped', 'message': 'File matches ignore patterns'}

                # Update source status
                source.status = SourceStatus.RUNNING
                source.last_run = datetime.utcnow()
                await db.commit()

                # Extract content
                content = file_watcher.extract_text_from_file(file_path)

                if not content:
                    return {'status': 'skipped', 'message': 'No content extracted'}

                # Ingest into RAG
                rag_service = RAGService()

                filename = os.path.basename(file_path)

                await rag_service.add_document(
                    project_id=source.project_id,
                    content=content,
                    metadata={
                        'title': filename,
                        'file_path': file_path,
                        'file_type': Path(file_path).suffix,
                        'event_type': event_type,
                        'source_type': 'file_watcher',
                        'source_id': source.id,
                        'source_name': source.name,
                        'priority': source.priority
                    }
                )

                # Update source status
                source.status = SourceStatus.SUCCESS
                source.last_success = datetime.utcnow()
                source.documents_ingested += 1
                source.error_count = 0
                source.last_error = None
                await db.commit()

                logger.info(f"File ingested: {filename}")

                return {
                    'status': 'success',
                    'documents_ingested': 1,
                    'file_path': file_path
                }

            except Exception as e:
                logger.error(f"File processing failed: {e}")

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
            return loop.run_until_complete(_process_file())
    except RuntimeError:
        pass

    # Create new event loop
    return asyncio.run(_process_file())
