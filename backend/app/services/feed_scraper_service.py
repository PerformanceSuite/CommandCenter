"""
Feed scraper service for RSS/Atom feed ingestion
"""
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass
import feedparser
from newspaper import Article
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class FeedEntry:
    """Represents a parsed feed entry"""
    title: str
    url: str
    content: str
    summary: str = ""
    published: Optional[datetime] = None
    author: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class FeedScraperService:
    """Service for scraping and parsing RSS/Atom feeds"""

    def __init__(self, max_workers: int = 4):
        """
        Initialize feed scraper service.

        Args:
            max_workers: Maximum number of threads for blocking I/O operations
        """
        self.logger = logger
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def parse_feed(
        self,
        feed_url: str,
        auth: Optional[Tuple[str, str]] = None
    ) -> List[FeedEntry]:
        """
        Parse RSS or Atom feed and extract entries.

        Args:
            feed_url: URL of the feed
            auth: Optional (username, password) for HTTP Basic auth

        Returns:
            List of FeedEntry objects

        Raises:
            ValueError: If feed is malformed or invalid
        """
        self.logger.info(f"Parsing feed: {feed_url}")

        # Parse feed with feedparser
        if auth:
            # Add auth to URL for feedparser
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(feed_url)
            netloc_with_auth = f"{auth[0]}:{auth[1]}@{parsed.netloc}"
            feed_url_with_auth = urlunparse((
                parsed.scheme, netloc_with_auth, parsed.path,
                parsed.params, parsed.query, parsed.fragment
            ))
            feed_data = feedparser.parse(feed_url_with_auth)
        else:
            feed_data = feedparser.parse(feed_url)

        # Check for errors
        if feed_data.get('bozo', False):
            error_msg = str(feed_data.get('bozo_exception', 'Unknown error'))
            self.logger.error(f"Feed parsing error: {error_msg}")
            raise ValueError(f"Feed is malformed or invalid: {error_msg}")

        entries = []
        for entry in feed_data.get('entries', []):
            # Extract basic metadata
            title = entry.get('title', 'Untitled')
            url = entry.get('link', '')
            summary = entry.get('summary', '')

            # Extract published date (RSS uses 'published_parsed', Atom uses 'updated_parsed')
            published = None
            if 'published_parsed' in entry and entry['published_parsed']:
                published = datetime(*entry['published_parsed'][:6])
            elif 'updated_parsed' in entry and entry['updated_parsed']:
                published = datetime(*entry['updated_parsed'][:6])

            # Extract author
            author = entry.get('author', None)

            # Extract tags
            tags = []
            if 'tags' in entry:
                tags = [tag['term'] for tag in entry['tags'] if 'term' in tag]

            # Attempt to extract full content
            content = await self.extract_full_content(url, summary_fallback=summary)

            feed_entry = FeedEntry(
                title=title,
                url=url,
                content=content,
                summary=summary,
                published=published,
                author=author,
                tags=tags
            )
            entries.append(feed_entry)

        self.logger.info(f"Parsed {len(entries)} entries from feed")
        return entries

    def _extract_full_content_blocking(
        self,
        article_url: str,
        summary_fallback: str = ""
    ) -> str:
        """
        Extract full article content from URL (blocking I/O).

        This is a synchronous helper called from executor.

        Args:
            article_url: URL of the article
            summary_fallback: Summary to use if extraction fails

        Returns:
            Full article text or fallback summary
        """
        try:
            article = Article(article_url)
            article.download()
            article.parse()

            if article.text:
                return article.text
            else:
                self.logger.warning(f"No content extracted from {article_url}, using summary")
                return summary_fallback

        except Exception as e:
            self.logger.error(f"Failed to extract content from {article_url}: {e}")
            return summary_fallback

    async def extract_full_content(
        self,
        article_url: str,
        summary_fallback: str = ""
    ) -> str:
        """
        Extract full article content from URL (async-safe).

        Args:
            article_url: URL of the article
            summary_fallback: Summary to use if extraction fails

        Returns:
            Full article text or fallback summary
        """
        # Run blocking newspaper3k calls in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._extract_full_content_blocking,
            article_url,
            summary_fallback
        )

    def deduplicate_entries(self, entries: List[FeedEntry]) -> List[FeedEntry]:
        """
        Remove duplicate entries based on URL, keeping most recent.

        Args:
            entries: List of feed entries

        Returns:
            Deduplicated list of entries
        """
        seen_urls = {}
        for entry in entries:
            if entry.url not in seen_urls:
                seen_urls[entry.url] = entry
            else:
                # Keep entry with most recent published date
                existing = seen_urls[entry.url]
                if entry.published and existing.published:
                    if entry.published > existing.published:
                        seen_urls[entry.url] = entry

        return list(seen_urls.values())
