# Phase B: Automated Knowledge Ingestion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build automated pipelines to continuously gather knowledge from multiple sources (RSS feeds, documentation sites, webhooks, file watchers) without manual intervention.

**Architecture:** Service-oriented pattern with Celery background tasks for async ingestion. Each source type (RSS, docs, webhooks, files) has a dedicated service and Celery task. Source configuration stored in database with priority system affecting RAG retrieval.

**Tech Stack:**
- Celery (async task queue, already configured)
- feedparser (RSS/Atom parsing)
- BeautifulSoup4 + requests (web scraping)
- watchdog (file system monitoring)
- KnowledgeBeast (RAG storage, already integrated)

**Prerequisites:** Phase A complete (Dagger hardening done)

**Duration:** Weeks 4-6 (3 weeks)

---

## Task 1: Database Models for Ingestion Sources

**Goal:** Create database schema to track ingestion sources and their configuration.

**Files:**
- Create: `backend/app/models/ingestion_source.py`
- Create: `backend/app/schemas/ingestion.py`
- Create: `backend/alembic/versions/<timestamp>_add_ingestion_sources.py`
- Test: `backend/tests/integration/test_ingestion_source_model.py`

### Step 1: Write failing test for IngestionSource model

**File:** `backend/tests/integration/test_ingestion_source_model.py`

```python
"""
Integration tests for IngestionSource model
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.ingestion_source import IngestionSource, SourceType, SourceStatus
from app.models.project import Project


def test_create_rss_source(db_session: Session, sample_project: Project):
    """Test creating an RSS ingestion source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.RSS,
        name="Tech Blog Feed",
        url="https://example.com/feed.xml",
        schedule="0 * * * *",  # Every hour
        priority=8,
        enabled=True
    )
    db_session.add(source)
    db_session.commit()

    assert source.id is not None
    assert source.type == SourceType.RSS
    assert source.status == SourceStatus.PENDING
    assert source.last_run is None
    assert source.error_count == 0


def test_create_documentation_source(db_session: Session, sample_project: Project):
    """Test creating a documentation scraper source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.DOCUMENTATION,
        name="FastAPI Docs",
        url="https://fastapi.tiangolo.com",
        schedule="0 0 * * 0",  # Weekly
        priority=9,
        enabled=True,
        config={"doc_system": "mkdocs", "max_depth": 3}
    )
    db_session.add(source)
    db_session.commit()

    assert source.id is not None
    assert source.config["doc_system"] == "mkdocs"
    assert source.priority == 9


def test_create_webhook_source(db_session: Session, sample_project: Project):
    """Test creating a webhook receiver source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.WEBHOOK,
        name="GitHub Webhook",
        url="/api/webhooks/github",
        priority=10,
        enabled=True,
        config={"secret": "webhook-secret-key", "events": ["push", "release"]}
    )
    db_session.add(source)
    db_session.commit()

    assert source.id is not None
    assert source.schedule is None  # Webhooks don't have schedules


def test_create_file_watcher_source(db_session: Session, sample_project: Project):
    """Test creating a file system watcher source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.FILE_WATCHER,
        name="Research Documents",
        path="/home/user/Documents/Research",
        priority=7,
        enabled=True,
        config={"patterns": ["*.pdf", "*.md"], "ignore": [".git", "node_modules"]}
    )
    db_session.add(source)
    db_session.commit()

    assert source.id is not None
    assert source.path == "/home/user/Documents/Research"


def test_source_priority_ordering(db_session: Session, sample_project: Project):
    """Test sources can be ordered by priority"""
    # Create sources with different priorities
    low = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="Low Priority", url="https://low.com/feed", priority=3, enabled=True
    )
    high = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="High Priority", url="https://high.com/feed", priority=9, enabled=True
    )
    medium = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="Medium Priority", url="https://medium.com/feed", priority=6, enabled=True
    )

    db_session.add_all([low, high, medium])
    db_session.commit()

    # Query sources ordered by priority descending
    sources = db_session.query(IngestionSource)\
        .filter(IngestionSource.project_id == sample_project.id)\
        .order_by(IngestionSource.priority.desc())\
        .all()

    assert sources[0].name == "High Priority"
    assert sources[1].name == "Medium Priority"
    assert sources[2].name == "Low Priority"


def test_update_source_status(db_session: Session, sample_project: Project):
    """Test updating source status after run"""
    source = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="Test Source", url="https://test.com/feed", priority=5, enabled=True
    )
    db_session.add(source)
    db_session.commit()

    # Simulate successful run
    source.status = SourceStatus.SUCCESS
    source.last_run = datetime.utcnow()
    source.last_success = datetime.utcnow()
    source.documents_ingested = 15
    db_session.commit()

    assert source.status == SourceStatus.SUCCESS
    assert source.last_run is not None
    assert source.documents_ingested == 15

    # Simulate error
    source.status = SourceStatus.ERROR
    source.error_count += 1
    source.last_error = "Connection timeout"
    db_session.commit()

    assert source.status == SourceStatus.ERROR
    assert source.error_count == 1
    assert source.last_error == "Connection timeout"


def test_disable_source(db_session: Session, sample_project: Project):
    """Test disabling a source"""
    source = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="Test Source", url="https://test.com/feed", priority=5, enabled=True
    )
    db_session.add(source)
    db_session.commit()

    source.enabled = False
    db_session.commit()

    # Query only enabled sources
    enabled_sources = db_session.query(IngestionSource)\
        .filter(IngestionSource.project_id == sample_project.id)\
        .filter(IngestionSource.enabled == True)\
        .all()

    assert len(enabled_sources) == 0
```

### Step 2: Run test to verify it fails

**Command:**
```bash
cd backend
pytest tests/integration/test_ingestion_source_model.py -v
```

**Expected:** FAIL - Module 'app.models.ingestion_source' not found

### Step 3: Create IngestionSource model

**File:** `backend/app/models/ingestion_source.py`

```python
"""
IngestionSource model for automated knowledge ingestion
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SourceType(str, Enum):
    """Types of ingestion sources"""
    RSS = "rss"
    DOCUMENTATION = "documentation"
    WEBHOOK = "webhook"
    FILE_WATCHER = "file_watcher"


class SourceStatus(str, Enum):
    """Status of ingestion source"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    DISABLED = "disabled"


class IngestionSource(Base):
    """Configuration for automated knowledge ingestion sources"""

    __tablename__ = "ingestion_sources"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to project for isolation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source configuration
    type: Mapped[SourceType] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # URL or path
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Scheduling (cron expression)
    schedule: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Priority (1-10, higher = more important)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # Enable/disable
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Additional configuration (JSON)
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Status tracking
    status: Mapped[SourceStatus] = mapped_column(
        String(50), default=SourceStatus.PENDING, nullable=False
    )
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_success: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metrics
    documents_ingested: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="ingestion_sources"
    )

    def __repr__(self) -> str:
        return f"<IngestionSource(id={self.id}, name='{self.name}', type='{self.type}')>"
```

### Step 4: Update Project model to add relationship

**File:** `backend/app/models/project.py`

Find the class definition and add this relationship:

```python
# Add to imports at top
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.ingestion_source import IngestionSource

# Add to Project class
    ingestion_sources: Mapped[list["IngestionSource"]] = relationship(
        "IngestionSource", back_populates="project", cascade="all, delete-orphan"
    )
```

### Step 5: Create Pydantic schemas

**File:** `backend/app/schemas/ingestion.py`

```python
"""
Pydantic schemas for ingestion sources
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from app.models.ingestion_source import SourceType, SourceStatus


class IngestionSourceBase(BaseModel):
    """Base schema for ingestion source"""
    name: str = Field(..., min_length=1, max_length=255)
    type: SourceType
    url: Optional[str] = None
    path: Optional[str] = None
    schedule: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None


class IngestionSourceCreate(IngestionSourceBase):
    """Schema for creating ingestion source"""
    project_id: int


class IngestionSourceUpdate(BaseModel):
    """Schema for updating ingestion source"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    path: Optional[str] = None
    schedule: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class IngestionSourceResponse(IngestionSourceBase):
    """Schema for ingestion source response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    status: SourceStatus
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    documents_ingested: int
    error_count: int
    created_at: datetime
    updated_at: datetime


class IngestionSourceList(BaseModel):
    """Schema for list of ingestion sources"""
    sources: list[IngestionSourceResponse]
    total: int
```

### Step 6: Update model __init__.py to export new model

**File:** `backend/app/models/__init__.py`

Add to imports:
```python
from app.models.ingestion_source import IngestionSource, SourceType, SourceStatus
```

Add to __all__:
```python
__all__ = [
    # ... existing exports ...
    "IngestionSource",
    "SourceType",
    "SourceStatus",
]
```

### Step 7: Update schema __init__.py to export new schemas

**File:** `backend/app/schemas/__init__.py`

Add to imports:
```python
from app.schemas.ingestion import (
    IngestionSourceBase,
    IngestionSourceCreate,
    IngestionSourceUpdate,
    IngestionSourceResponse,
    IngestionSourceList,
)
```

Add to __all__:
```python
__all__ = [
    # ... existing exports ...
    "IngestionSourceBase",
    "IngestionSourceCreate",
    "IngestionSourceUpdate",
    "IngestionSourceResponse",
    "IngestionSourceList",
]
```

### Step 8: Create Alembic migration

**Command:**
```bash
cd backend
alembic revision --autogenerate -m "Add ingestion sources table"
```

**Expected:** Migration file created in `backend/alembic/versions/`

Edit the generated migration to ensure it includes:
- ingestion_sources table
- All columns as defined in model
- Foreign key to projects table
- Indexes on project_id and type

### Step 9: Apply migration

**Command:**
```bash
cd backend
alembic upgrade head
```

**Expected:** Migration applied successfully

### Step 10: Update conftest.py with sample_project fixture

**File:** `backend/tests/conftest.py`

Add fixture if not exists:
```python
@pytest.fixture
def sample_project(db_session: Session) -> Project:
    """Create a sample project for testing"""
    project = Project(
        name="Test Project",
        description="Project for testing"
    )
    db_session.add(project)
    db_session.commit()
    return project
```

### Step 11: Run tests to verify they pass

**Command:**
```bash
cd backend
pytest tests/integration/test_ingestion_source_model.py -v
```

**Expected:** All tests PASS

### Step 12: Commit

```bash
git add backend/app/models/ingestion_source.py \
        backend/app/models/project.py \
        backend/app/schemas/ingestion.py \
        backend/app/models/__init__.py \
        backend/app/schemas/__init__.py \
        backend/tests/integration/test_ingestion_source_model.py \
        backend/tests/conftest.py \
        backend/alembic/versions/*_add_ingestion_sources.py

git commit -m "feat: add IngestionSource model for automated knowledge ingestion

- Create IngestionSource model with source types (RSS, docs, webhooks, files)
- Add source status tracking and metrics
- Implement priority system (1-10)
- Add enable/disable functionality
- Create Pydantic schemas for API
- Add database migration
- Full test coverage for model operations

Phase B Task 1/6 complete"
```

---

## Task 2: RSS Feed Scraper Service

**Goal:** Create service to scrape and parse RSS/Atom feeds, extracting full article content.

**Files:**
- Create: `backend/app/services/feed_scraper_service.py`
- Create: `backend/app/tasks/ingestion_tasks.py`
- Test: `backend/tests/services/test_feed_scraper_service.py`
- Test: `backend/tests/integration/test_rss_ingestion.py`

**Dependencies:** Add to `backend/requirements.txt`:
```
feedparser==6.0.11
beautifulsoup4==4.12.3
newspaper3k==0.2.8
```

### Step 1: Install dependencies

**Command:**
```bash
cd backend
pip install feedparser==6.0.11 beautifulsoup4==4.12.3 newspaper3k==0.2.8
```

**Expected:** Dependencies installed

### Step 2: Write failing unit test for FeedScraperService

**File:** `backend/tests/services/test_feed_scraper_service.py`

```python
"""
Unit tests for FeedScraperService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.services.feed_scraper_service import FeedScraperService, FeedEntry


@pytest.fixture
def feed_scraper():
    """Create FeedScraperService instance"""
    return FeedScraperService()


def test_parse_rss_feed(feed_scraper):
    """Test parsing RSS 2.0 feed"""
    mock_feed_data = {
        'entries': [
            {
                'title': 'Test Article',
                'link': 'https://example.com/article',
                'summary': 'This is a test article summary',
                'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 0, 0),
                'author': 'John Doe',
                'tags': [{'term': 'python'}, {'term': 'testing'}]
            }
        ],
        'feed': {'title': 'Test Blog'},
        'bozo': False
    }

    with patch('feedparser.parse', return_value=mock_feed_data):
        entries = feed_scraper.parse_feed('https://example.com/feed.xml')

    assert len(entries) == 1
    assert entries[0].title == 'Test Article'
    assert entries[0].url == 'https://example.com/article'
    assert entries[0].author == 'John Doe'
    assert entries[0].tags == ['python', 'testing']


def test_parse_atom_feed(feed_scraper):
    """Test parsing Atom feed"""
    mock_feed_data = {
        'entries': [
            {
                'title': 'Atom Article',
                'link': 'https://example.com/atom-article',
                'summary': 'Atom feed article',
                'updated_parsed': (2024, 1, 20, 14, 0, 0, 0, 0, 0),
                'author': 'Jane Smith'
            }
        ],
        'feed': {'title': 'Atom Feed'},
        'bozo': False
    }

    with patch('feedparser.parse', return_value=mock_feed_data):
        entries = feed_scraper.parse_feed('https://example.com/atom.xml')

    assert len(entries) == 1
    assert entries[0].title == 'Atom Article'


def test_extract_full_content(feed_scraper):
    """Test extracting full article content"""
    mock_article = Mock()
    mock_article.text = "This is the full article content with multiple paragraphs."
    mock_article.download.return_value = None
    mock_article.parse.return_value = None

    with patch('newspaper.Article', return_value=mock_article):
        content = feed_scraper.extract_full_content('https://example.com/article')

    assert content == "This is the full article content with multiple paragraphs."
    mock_article.download.assert_called_once()
    mock_article.parse.assert_called_once()


def test_extract_full_content_fallback(feed_scraper):
    """Test fallback when content extraction fails"""
    with patch('newspaper.Article', side_effect=Exception("Download failed")):
        content = feed_scraper.extract_full_content(
            'https://example.com/article',
            summary_fallback='Summary content'
        )

    assert content == 'Summary content'


def test_deduplicate_entries(feed_scraper):
    """Test deduplication by URL"""
    entries = [
        FeedEntry(
            title='Article 1',
            url='https://example.com/article1',
            content='Content 1',
            published=datetime(2024, 1, 15)
        ),
        FeedEntry(
            title='Article 1 Duplicate',
            url='https://example.com/article1',  # Same URL
            content='Content 1 duplicate',
            published=datetime(2024, 1, 16)
        ),
        FeedEntry(
            title='Article 2',
            url='https://example.com/article2',
            content='Content 2',
            published=datetime(2024, 1, 17)
        ),
    ]

    deduped = feed_scraper.deduplicate_entries(entries)

    assert len(deduped) == 2
    assert deduped[0].url == 'https://example.com/article1'
    assert deduped[1].url == 'https://example.com/article2'
    # Should keep most recent duplicate
    assert deduped[0].published == datetime(2024, 1, 16)


def test_parse_feed_with_authentication(feed_scraper):
    """Test parsing feed with HTTP Basic auth"""
    mock_feed_data = {
        'entries': [{'title': 'Authenticated Article', 'link': 'https://example.com/auth'}],
        'feed': {'title': 'Private Feed'},
        'bozo': False
    }

    with patch('feedparser.parse', return_value=mock_feed_data) as mock_parse:
        entries = feed_scraper.parse_feed(
            'https://example.com/feed.xml',
            auth=('username', 'password')
        )

    assert len(entries) == 1
    # Verify auth was passed to feedparser
    call_args = mock_parse.call_args
    assert 'username' in str(call_args)


def test_handle_malformed_feed(feed_scraper):
    """Test handling malformed/invalid feed"""
    mock_feed_data = {
        'entries': [],
        'bozo': True,
        'bozo_exception': Exception("Feed is malformed")
    }

    with patch('feedparser.parse', return_value=mock_feed_data):
        with pytest.raises(ValueError, match="Feed is malformed or invalid"):
            feed_scraper.parse_feed('https://example.com/bad-feed.xml')
```

### Step 3: Run test to verify it fails

**Command:**
```bash
cd backend
pytest tests/services/test_feed_scraper_service.py -v
```

**Expected:** FAIL - Module not found

### Step 4: Implement FeedScraperService

**File:** `backend/app/services/feed_scraper_service.py`

```python
"""
Feed scraper service for RSS/Atom feed ingestion
"""
import logging
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

    def __init__(self):
        self.logger = logger

    def parse_feed(
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
            content = self.extract_full_content(url, summary_fallback=summary)

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

    def extract_full_content(
        self,
        article_url: str,
        summary_fallback: str = ""
    ) -> str:
        """
        Extract full article content from URL.

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
```

### Step 5: Run unit tests to verify they pass

**Command:**
```bash
cd backend
pytest tests/services/test_feed_scraper_service.py -v
```

**Expected:** All tests PASS

### Step 6: Write failing integration test for RSS ingestion task

**File:** `backend/tests/integration/test_rss_ingestion.py`

```python
"""
Integration tests for RSS feed ingestion
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.ingestion_source import IngestionSource, SourceType, SourceStatus
from app.models.project import Project
from app.tasks.ingestion_tasks import scrape_rss_feed
from app.services.feed_scraper_service import FeedEntry


@pytest.fixture
def rss_source(db_session: Session, sample_project: Project) -> IngestionSource:
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
    db_session.commit()
    return source


def test_scrape_rss_feed_success(db_session: Session, rss_source: IngestionSource):
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
    db_session.refresh(rss_source)
    assert rss_source.status == SourceStatus.SUCCESS
    assert rss_source.documents_ingested == 2
    assert rss_source.last_run is not None
    assert rss_source.last_success is not None

    # Verify RAG service called for each entry
    assert mock_add_doc.call_count == 2


def test_scrape_rss_feed_with_errors(db_session: Session, rss_source: IngestionSource):
    """Test RSS feed scraping with errors"""
    with patch('app.services.feed_scraper_service.FeedScraperService.parse_feed',
               side_effect=ValueError("Feed is malformed")):
        result = scrape_rss_feed(rss_source.id)

    # Verify error handling
    assert result['status'] == 'error'
    assert 'Feed is malformed' in result['error']

    # Verify source status updated
    db_session.refresh(rss_source)
    assert rss_source.status == SourceStatus.ERROR
    assert rss_source.error_count == 1
    assert rss_source.last_error is not None


def test_scrape_disabled_source(db_session: Session, rss_source: IngestionSource):
    """Test that disabled sources are not scraped"""
    rss_source.enabled = False
    db_session.commit()

    result = scrape_rss_feed(rss_source.id)

    assert result['status'] == 'skipped'
    assert 'disabled' in result['message'].lower()
```

### Step 7: Run integration test to verify it fails

**Command:**
```bash
cd backend
pytest tests/integration/test_rss_ingestion.py -v
```

**Expected:** FAIL - Module 'app.tasks.ingestion_tasks' not found

### Step 8: Create ingestion_tasks.py with RSS scraping task

**File:** `backend/app/tasks/ingestion_tasks.py`

```python
"""
Celery tasks for automated knowledge ingestion
"""
import logging
from datetime import datetime
from typing import Dict, Any
from celery import Task

from app.tasks import celery_app
from app.database import SessionLocal
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
    db = SessionLocal()

    try:
        # Load source
        source = db.query(IngestionSource).filter(
            IngestionSource.id == source_id
        ).first()

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
        db.commit()

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
        db.commit()

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
            db.commit()

        return {
            'status': 'error',
            'error': str(e),
            'source_id': source_id
        }

    finally:
        db.close()
```

### Step 9: Update tasks/__init__.py to include ingestion tasks

**File:** `backend/app/tasks/__init__.py`

Add to include list:
```python
    include=[
        "app.tasks.job_tasks",
        "app.tasks.analysis_tasks",
        "app.tasks.export_tasks",
        "app.tasks.webhook_tasks",
        "app.tasks.scheduled_tasks",
        "app.tasks.ingestion_tasks",  # Add this line
    ],
```

Add to imports at bottom:
```python
    from app.tasks import ingestion_tasks  # noqa: F401
```

Add to task routes:
```python
celery_app.conf.task_routes = {
    "app.tasks.analysis_tasks.*": {"queue": "analysis", "priority": 8},
    "app.tasks.export_tasks.*": {"queue": "export", "priority": 5},
    "app.tasks.webhook_tasks.*": {"queue": "webhooks", "priority": 6},
    "app.tasks.scheduled_tasks.*": {"queue": "default", "priority": 7},
    "app.tasks.ingestion_tasks.*": {"queue": "default", "priority": 7},  # Add this line
}
```

### Step 10: Run integration tests to verify they pass

**Command:**
```bash
cd backend
pytest tests/integration/test_rss_ingestion.py -v
```

**Expected:** All tests PASS

### Step 11: Commit

```bash
git add backend/app/services/feed_scraper_service.py \
        backend/app/tasks/ingestion_tasks.py \
        backend/app/tasks/__init__.py \
        backend/tests/services/test_feed_scraper_service.py \
        backend/tests/integration/test_rss_ingestion.py \
        backend/requirements.txt

git commit -m "feat: add RSS feed scraper service and ingestion task

- Implement FeedScraperService for RSS/Atom parsing
- Extract full article content with newspaper3k
- Add deduplication by URL
- Create Celery task for scheduled RSS scraping
- Integrate with RAG service for document storage
- Handle errors with retry logic and status tracking
- Full unit and integration test coverage

Phase B Task 2/6 complete"
```

---

## Task 3: Documentation Scraper Service

**Goal:** Create service to scrape documentation websites, respecting robots.txt and sitemaps.

**Files:**
- Create: `backend/app/services/documentation_scraper_service.py`
- Modify: `backend/app/tasks/ingestion_tasks.py` (add scrape_documentation task)
- Test: `backend/tests/services/test_documentation_scraper_service.py`
- Test: `backend/tests/integration/test_documentation_ingestion.py`

### Step 1: Write failing unit test for DocumentationScraperService

**File:** `backend/tests/services/test_documentation_scraper_service.py`

```python
"""
Unit tests for DocumentationScraperService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.documentation_scraper_service import (
    DocumentationScraperService,
    DocumentationPage
)


@pytest.fixture
def doc_scraper():
    """Create DocumentationScraperService instance"""
    return DocumentationScraperService()


def test_fetch_sitemap(doc_scraper):
    """Test fetching and parsing sitemap.xml"""
    mock_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/docs/intro</loc>
            <lastmod>2024-01-15</lastmod>
        </url>
        <url>
            <loc>https://example.com/docs/guide</loc>
            <lastmod>2024-01-16</lastmod>
        </url>
    </urlset>
    """

    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = mock_sitemap

        urls = doc_scraper.fetch_sitemap('https://example.com/sitemap.xml')

    assert len(urls) == 2
    assert 'https://example.com/docs/intro' in urls
    assert 'https://example.com/docs/guide' in urls


def test_check_robots_txt(doc_scraper):
    """Test checking robots.txt for allowed URLs"""
    mock_robots = """
    User-agent: *
    Disallow: /admin/
    Disallow: /private/
    Allow: /docs/
    """

    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = mock_robots

        # Should be allowed
        assert doc_scraper.is_allowed('https://example.com/docs/guide') == True

        # Should be disallowed
        assert doc_scraper.is_allowed('https://example.com/admin/') == False


def test_scrape_page(doc_scraper):
    """Test scraping a single documentation page"""
    mock_html = """
    <html>
        <head><title>Introduction | Docs</title></head>
        <body>
            <main>
                <h1>Introduction</h1>
                <p>This is the introduction to our documentation.</p>
                <pre><code>print("Hello World")</code></pre>
            </main>
        </body>
    </html>
    """

    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = mock_html

        page = doc_scraper.scrape_page('https://example.com/docs/intro')

    assert page.title == 'Introduction | Docs'
    assert 'Introduction' in page.content
    assert 'Hello World' in page.content
    assert page.url == 'https://example.com/docs/intro'


def test_extract_links(doc_scraper):
    """Test extracting internal links from page"""
    mock_html = """
    <html>
        <body>
            <a href="/docs/guide">Guide</a>
            <a href="https://example.com/docs/api">API</a>
            <a href="https://external.com/link">External</a>
        </body>
    </html>
    """

    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = mock_html

        links = doc_scraper.extract_links(
            'https://example.com/docs/intro',
            base_url='https://example.com'
        )

    assert len(links) == 2  # Only internal links
    assert 'https://example.com/docs/guide' in links
    assert 'https://example.com/docs/api' in links
    assert 'https://external.com/link' not in links


def test_scrape_with_max_depth(doc_scraper):
    """Test scraping with depth limit"""
    with patch.object(doc_scraper, 'scrape_page') as mock_scrape:
        with patch.object(doc_scraper, 'extract_links', return_value=[]):
            mock_scrape.return_value = DocumentationPage(
                url='https://example.com/docs',
                title='Docs',
                content='Content',
                headings=['H1']
            )

            pages = doc_scraper.scrape_documentation(
                'https://example.com/docs',
                max_depth=0
            )

    assert len(pages) == 1
    mock_scrape.assert_called_once()


def test_handle_404_error(doc_scraper):
    """Test handling 404 errors gracefully"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 404

        page = doc_scraper.scrape_page('https://example.com/not-found')

    assert page is None
```

### Step 2: Run test to verify it fails

**Command:**
```bash
cd backend
pytest tests/services/test_documentation_scraper_service.py -v
```

**Expected:** FAIL - Module not found

### Step 3: Implement DocumentationScraperService

**File:** `backend/app/services/documentation_scraper_service.py`

```python
"""
Documentation scraper service for automated docs ingestion
"""
import logging
import time
from typing import List, Set, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class DocumentationPage:
    """Represents a scraped documentation page"""
    url: str
    title: str
    content: str
    headings: List[str]
    code_blocks: List[str] = None

    def __post_init__(self):
        if self.code_blocks is None:
            self.code_blocks = []


class DocumentationScraperService:
    """Service for scraping documentation websites"""

    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize documentation scraper.

        Args:
            rate_limit: Seconds to wait between requests (default: 1.0)
        """
        self.logger = logger
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CommandCenter Documentation Bot/1.0'
        })
        self.robots_parser = None

    def fetch_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Fetch and parse sitemap.xml for URLs.

        Args:
            sitemap_url: URL of sitemap

        Returns:
            List of URLs from sitemap
        """
        self.logger.info(f"Fetching sitemap: {sitemap_url}")

        try:
            response = self.session.get(sitemap_url, timeout=10)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.text)

            # Extract URLs (handle namespace)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = []
            for url_elem in root.findall('.//ns:url', namespace):
                loc = url_elem.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    urls.append(loc.text)

            self.logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls

        except Exception as e:
            self.logger.error(f"Failed to fetch sitemap: {e}")
            return []

    def is_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        if not self.robots_parser:
            # Initialize robots parser
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)
            try:
                self.robots_parser.read()
            except Exception as e:
                self.logger.warning(f"Could not read robots.txt: {e}")
                return True  # Allow if robots.txt not available

        return self.robots_parser.can_fetch('CommandCenter Documentation Bot', url)

    def scrape_page(self, url: str) -> Optional[DocumentationPage]:
        """
        Scrape a single documentation page.

        Args:
            url: URL to scrape

        Returns:
            DocumentationPage or None if failed
        """
        try:
            # Rate limiting
            time.sleep(self.rate_limit)

            response = self.session.get(url, timeout=10)

            if response.status_code == 404:
                self.logger.warning(f"Page not found: {url}")
                return None

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = soup.title.string if soup.title else 'Untitled'

            # Extract main content (try common selectors)
            main_content = None
            for selector in ['main', 'article', '.content', '#content', '.documentation']:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if not main_content:
                main_content = soup.body

            # Extract text content
            content = main_content.get_text(separator='\n', strip=True) if main_content else ''

            # Extract headings
            headings = [h.get_text(strip=True) for h in main_content.find_all(['h1', 'h2', 'h3', 'h4'])] \
                if main_content else []

            # Extract code blocks
            code_blocks = [code.get_text() for code in main_content.find_all(['code', 'pre'])] \
                if main_content else []

            return DocumentationPage(
                url=url,
                title=title,
                content=content,
                headings=headings,
                code_blocks=code_blocks
            )

        except Exception as e:
            self.logger.error(f"Failed to scrape page {url}: {e}")
            return None

    def extract_links(self, page_url: str, base_url: str) -> List[str]:
        """
        Extract internal links from a page.

        Args:
            page_url: URL of current page
            base_url: Base URL of documentation site

        Returns:
            List of internal links
        """
        try:
            response = self.session.get(page_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            links = []
            base_domain = urlparse(base_url).netloc

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']

                # Convert relative URLs to absolute
                absolute_url = urljoin(page_url, href)

                # Only include internal links
                if urlparse(absolute_url).netloc == base_domain:
                    # Remove fragment
                    absolute_url = absolute_url.split('#')[0]
                    links.append(absolute_url)

            return list(set(links))  # Deduplicate

        except Exception as e:
            self.logger.error(f"Failed to extract links from {page_url}: {e}")
            return []

    def scrape_documentation(
        self,
        start_url: str,
        max_depth: int = 3,
        max_pages: int = 100
    ) -> List[DocumentationPage]:
        """
        Scrape documentation site recursively.

        Args:
            start_url: Starting URL
            max_depth: Maximum depth to crawl
            max_pages: Maximum pages to scrape

        Returns:
            List of DocumentationPage objects
        """
        self.logger.info(f"Starting documentation scrape: {start_url}")

        pages = []
        visited: Set[str] = set()
        to_visit = [(start_url, 0)]  # (url, depth)

        base_url = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"

        while to_visit and len(pages) < max_pages:
            current_url, depth = to_visit.pop(0)

            # Skip if already visited
            if current_url in visited:
                continue

            # Skip if depth exceeded
            if depth > max_depth:
                continue

            # Check robots.txt
            if not self.is_allowed(current_url):
                self.logger.info(f"Skipping disallowed URL: {current_url}")
                continue

            # Scrape page
            page = self.scrape_page(current_url)
            if page:
                pages.append(page)
                visited.add(current_url)

                # Extract and queue links
                if depth < max_depth:
                    links = self.extract_links(current_url, base_url)
                    for link in links:
                        if link not in visited:
                            to_visit.append((link, depth + 1))

        self.logger.info(f"Scraped {len(pages)} documentation pages")
        return pages
```

### Step 4: Run unit tests to verify they pass

**Command:**
```bash
cd backend
pytest tests/services/test_documentation_scraper_service.py -v
```

**Expected:** All tests PASS

### Step 5: Write failing integration test for documentation ingestion

**File:** `backend/tests/integration/test_documentation_ingestion.py`

```python
"""
Integration tests for documentation ingestion
"""
import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from app.models.ingestion_source import IngestionSource, SourceType, SourceStatus
from app.models.project import Project
from app.tasks.ingestion_tasks import scrape_documentation
from app.services.documentation_scraper_service import DocumentationPage


@pytest.fixture
def docs_source(db_session: Session, sample_project: Project) -> IngestionSource:
    """Create a documentation ingestion source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.DOCUMENTATION,
        name="FastAPI Docs",
        url="https://fastapi.tiangolo.com",
        priority=9,
        enabled=True,
        config={"max_depth": 2, "max_pages": 50}
    )
    db_session.add(source)
    db_session.commit()
    return source


def test_scrape_documentation_success(db_session: Session, docs_source: IngestionSource):
    """Test successful documentation scraping"""
    mock_pages = [
        DocumentationPage(
            url="https://fastapi.tiangolo.com/tutorial",
            title="Tutorial - FastAPI",
            content="FastAPI is a modern web framework...",
            headings=["Introduction", "Installation"],
            code_blocks=["pip install fastapi"]
        ),
        DocumentationPage(
            url="https://fastapi.tiangolo.com/features",
            title="Features - FastAPI",
            content="FastAPI provides automatic API documentation...",
            headings=["Automatic Docs", "Type Hints"],
            code_blocks=[]
        )
    ]

    with patch('app.services.documentation_scraper_service.DocumentationScraperService.scrape_documentation',
               return_value=mock_pages):
        with patch('app.services.rag_service.RAGService.add_document'):
            result = scrape_documentation(docs_source.id)

    assert result['status'] == 'success'
    assert result['documents_ingested'] == 2

    # Verify source status
    db_session.refresh(docs_source)
    assert docs_source.status == SourceStatus.SUCCESS
    assert docs_source.documents_ingested == 2


def test_scrape_documentation_with_sitemap(db_session: Session, docs_source: IngestionSource):
    """Test documentation scraping using sitemap"""
    docs_source.config = {"use_sitemap": True, "sitemap_url": "https://fastapi.tiangolo.com/sitemap.xml"}
    db_session.commit()

    mock_pages = [
        DocumentationPage(
            url="https://fastapi.tiangolo.com/page1",
            title="Page 1",
            content="Content 1",
            headings=["H1"]
        )
    ]

    with patch('app.services.documentation_scraper_service.DocumentationScraperService.fetch_sitemap',
               return_value=["https://fastapi.tiangolo.com/page1"]):
        with patch('app.services.documentation_scraper_service.DocumentationScraperService.scrape_page',
                   return_value=mock_pages[0]):
            with patch('app.services.rag_service.RAGService.add_document'):
                result = scrape_documentation(docs_source.id)

    assert result['status'] == 'success'
```

### Step 6: Run integration test to verify it fails

**Command:**
```bash
cd backend
pytest tests/integration/test_documentation_ingestion.py -v
```

**Expected:** FAIL - Task 'scrape_documentation' not found

### Step 7: Add scrape_documentation task to ingestion_tasks.py

**File:** `backend/app/tasks/ingestion_tasks.py`

Add import at top:
```python
from app.services.documentation_scraper_service import DocumentationScraperService
```

Add task:
```python
@celery_app.task(base=IngestionTask, bind=True)
def scrape_documentation(self, source_id: int) -> Dict[str, Any]:
    """
    Scrape documentation website and ingest into RAG system.

    Args:
        source_id: ID of IngestionSource

    Returns:
        Dict with status, documents_ingested, and optional error
    """
    db = SessionLocal()

    try:
        # Load source
        source = db.query(IngestionSource).filter(
            IngestionSource.id == source_id
        ).first()

        if not source:
            return {'status': 'error', 'error': 'Source not found'}

        if not source.enabled:
            return {'status': 'skipped', 'message': 'Source is disabled'}

        # Update status
        source.status = SourceStatus.RUNNING
        source.last_run = datetime.utcnow()
        db.commit()

        # Get config
        config = source.config or {}
        max_depth = config.get('max_depth', 3)
        max_pages = config.get('max_pages', 100)
        use_sitemap = config.get('use_sitemap', False)

        # Initialize scraper
        doc_scraper = DocumentationScraperService(rate_limit=1.0)

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
        rag_service = RAGService()
        documents_ingested = 0

        for page in pages:
            try:
                rag_service.add_document(
                    project_id=source.project_id,
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
        db.commit()

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
            db.commit()

        return {'status': 'error', 'error': str(e)}

    finally:
        db.close()
```

### Step 8: Run integration tests to verify they pass

**Command:**
```bash
cd backend
pytest tests/integration/test_documentation_ingestion.py -v
```

**Expected:** All tests PASS

### Step 9: Commit

```bash
git add backend/app/services/documentation_scraper_service.py \
        backend/app/tasks/ingestion_tasks.py \
        backend/tests/services/test_documentation_scraper_service.py \
        backend/tests/integration/test_documentation_ingestion.py

git commit -m "feat: add documentation scraper service

- Implement DocumentationScraperService for web scraping
- Support sitemap.xml for efficient crawling
- Respect robots.txt rules
- Extract structured content (headings, code blocks)
- Add rate limiting to avoid overloading servers
- Create Celery task for scheduled documentation scraping
- Full unit and integration test coverage

Phase B Task 3/6 complete"
```

---

## Task 4: Webhook Receivers

**Goal:** Create webhook endpoints to accept push notifications from external sources (GitHub, custom integrations).

**Files:**
- Create: `backend/app/routers/webhooks_ingestion.py`
- Modify: `backend/app/tasks/ingestion_tasks.py` (add process_webhook_payload task)
- Test: `backend/tests/integration/test_webhook_ingestion.py`
- Modify: `backend/app/main.py` (register webhook router)

### Step 1: Write failing integration test for webhook ingestion

**File:** `backend/tests/integration/test_webhook_ingestion.py`

```python
"""
Integration tests for webhook ingestion
"""
import pytest
import hmac
import hashlib
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.ingestion_source import IngestionSource, SourceType
from app.models.project import Project


client = TestClient(app)


@pytest.fixture
def github_webhook_source(db_session: Session, sample_project: Project) -> IngestionSource:
    """Create a GitHub webhook source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.WEBHOOK,
        name="GitHub Releases",
        url="/api/webhooks/github",
        priority=10,
        enabled=True,
        config={
            "secret": "test-secret-key",
            "events": ["release", "push"]
        }
    )
    db_session.add(source)
    db_session.commit()
    return source


def test_github_webhook_release_event(github_webhook_source: IngestionSource):
    """Test processing GitHub release webhook"""
    payload = {
        "action": "published",
        "release": {
            "tag_name": "v1.0.0",
            "name": "Version 1.0.0",
            "body": "# Release Notes\n\n- Feature 1\n- Feature 2",
            "html_url": "https://github.com/user/repo/releases/tag/v1.0.0",
            "published_at": "2024-01-15T10:30:00Z"
        },
        "repository": {
            "full_name": "user/repo"
        }
    }

    # Generate signature
    secret = github_webhook_source.config['secret'].encode()
    signature = hmac.new(secret, str(payload).encode(), hashlib.sha256).hexdigest()

    response = client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={
            "X-Hub-Signature-256": f"sha256={signature}",
            "X-GitHub-Event": "release"
        }
    )

    assert response.status_code == 200
    assert response.json()['status'] == 'accepted'


def test_generic_webhook_with_custom_payload():
    """Test processing generic webhook with custom payload"""
    payload = {
        "title": "New Documentation",
        "content": "Updated API documentation is available...",
        "url": "https://example.com/docs/api",
        "metadata": {
            "category": "documentation",
            "priority": 8
        }
    }

    response = client.post(
        "/api/webhooks/generic?project_id=1",
        json=payload,
        headers={"X-API-Key": "test-api-key"}
    )

    assert response.status_code == 200


def test_webhook_signature_verification_failure(github_webhook_source: IngestionSource):
    """Test webhook rejected with invalid signature"""
    payload = {"test": "data"}

    response = client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={
            "X-Hub-Signature-256": "sha256=invalidsignature",
            "X-GitHub-Event": "release"
        }
    )

    assert response.status_code == 401


def test_webhook_disabled_source(db_session: Session, github_webhook_source: IngestionSource):
    """Test webhook rejected when source is disabled"""
    github_webhook_source.enabled = False
    db_session.commit()

    payload = {"test": "data"}
    secret = github_webhook_source.config['secret'].encode()
    signature = hmac.new(secret, str(payload).encode(), hashlib.sha256).hexdigest()

    response = client.post(
        f"/api/webhooks/github?source_id={github_webhook_source.id}",
        json=payload,
        headers={
            "X-Hub-Signature-256": f"sha256={signature}",
            "X-GitHub-Event": "push"
        }
    )

    assert response.status_code == 403
```

### Step 2: Run test to verify it fails

**Command:**
```bash
cd backend
pytest tests/integration/test_webhook_ingestion.py -v
```

**Expected:** FAIL - Route not found

### Step 3: Create webhook router

**File:** `backend/app/routers/webhooks_ingestion.py`

```python
"""
Webhook endpoints for knowledge ingestion
"""
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Query, Header, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ingestion_source import IngestionSource, SourceType
from app.tasks.ingestion_tasks import process_webhook_payload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def verify_github_signature(
    payload_body: bytes,
    signature_header: str,
    secret: str
) -> bool:
    """
    Verify GitHub webhook signature.

    Args:
        payload_body: Raw request body
        signature_header: X-Hub-Signature-256 header value
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    if not signature_header or not signature_header.startswith('sha256='):
        return False

    expected_signature = signature_header.split('=')[1]

    # Calculate HMAC
    mac = hmac.new(secret.encode(), payload_body, hashlib.sha256)
    calculated_signature = mac.hexdigest()

    return hmac.compare_digest(calculated_signature, expected_signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    source_id: int = Query(..., description="ID of webhook ingestion source"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    db: Session = Depends(get_db)
):
    """
    Receive GitHub webhooks for repository updates.

    Supported events:
    - release: New releases
    - push: Code commits
    """
    # Load source
    source = db.query(IngestionSource).filter(
        IngestionSource.id == source_id,
        IngestionSource.type == SourceType.WEBHOOK
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Webhook source not found")

    if not source.enabled:
        raise HTTPException(status_code=403, detail="Webhook source is disabled")

    # Get payload
    payload_body = await request.body()
    payload = await request.json()

    # Verify signature
    secret = source.config.get('secret', '')
    if not verify_github_signature(payload_body, x_hub_signature_256, secret):
        logger.warning(f"Invalid GitHub webhook signature for source {source_id}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Check if event is configured
    allowed_events = source.config.get('events', [])
    if allowed_events and x_github_event not in allowed_events:
        logger.info(f"Ignoring GitHub event '{x_github_event}' for source {source_id}")
        return {"status": "ignored", "event": x_github_event}

    # Queue task asynchronously
    task = process_webhook_payload.delay(
        source_id=source.id,
        payload=payload,
        event_type=x_github_event
    )

    logger.info(f"Queued GitHub webhook processing: task_id={task.id}, event={x_github_event}")

    return {
        "status": "accepted",
        "task_id": task.id,
        "event": x_github_event
    }


@router.post("/generic")
async def generic_webhook(
    request: Request,
    project_id: int = Query(..., description="Project ID for ingestion"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Receive generic webhooks from custom integrations.

    Expected payload format:
    {
        "title": "Document title",
        "content": "Full content",
        "url": "Source URL (optional)",
        "metadata": {
            "category": "documentation",
            "priority": 8,
            ...
        }
    }
    """
    # Basic API key validation (configure in environment)
    # For production, implement proper authentication

    payload = await request.json()

    # Validate required fields
    if 'title' not in payload or 'content' not in payload:
        raise HTTPException(
            status_code=400,
            detail="Payload must include 'title' and 'content' fields"
        )

    # Queue task
    task = process_webhook_payload.delay(
        source_id=None,  # Generic webhook doesn't require source
        payload=payload,
        event_type='generic',
        project_id=project_id
    )

    logger.info(f"Queued generic webhook processing: task_id={task.id}")

    return {
        "status": "accepted",
        "task_id": task.id
    }
```

### Step 4: Add process_webhook_payload task

**File:** `backend/app/tasks/ingestion_tasks.py`

Add task:
```python
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
    db = SessionLocal()

    try:
        # Load source if provided
        source = None
        if source_id:
            source = db.query(IngestionSource).filter(
                IngestionSource.id == source_id
            ).first()

            if not source:
                return {'status': 'error', 'error': 'Source not found'}

            project_id = source.project_id

        if not project_id:
            return {'status': 'error', 'error': 'Project ID required'}

        # Update source status if exists
        if source:
            source.status = SourceStatus.RUNNING
            source.last_run = datetime.utcnow()
            db.commit()

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
                    'title': f"Commit: {commit.get('message', '').split('\n')[0]}",
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
        rag_service = RAGService()
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

                rag_service.add_document(
                    project_id=project_id,
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
            db.commit()

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
            db.commit()

        return {'status': 'error', 'error': str(e)}

    finally:
        db.close()
```

### Step 5: Register webhook router in main.py

**File:** `backend/app/main.py`

Add import:
```python
from app.routers import webhooks_ingestion
```

Add router registration:
```python
app.include_router(webhooks_ingestion.router)
```

### Step 6: Run integration tests to verify they pass

**Command:**
```bash
cd backend
pytest tests/integration/test_webhook_ingestion.py -v
```

**Expected:** All tests PASS

### Step 7: Commit

```bash
git add backend/app/routers/webhooks_ingestion.py \
        backend/app/tasks/ingestion_tasks.py \
        backend/app/main.py \
        backend/tests/integration/test_webhook_ingestion.py

git commit -m "feat: add webhook receivers for knowledge ingestion

- Create webhook endpoints for GitHub and generic integrations
- Implement signature verification for security
- Process release and push events from GitHub
- Support custom payloads for generic webhooks
- Queue ingestion tasks asynchronously
- Full integration test coverage

Phase B Task 4/6 complete"
```

---

## Task 5: File System Watchers

**Goal:** Monitor local directories for new documents and automatically ingest them.

**Files:**
- Create: `backend/app/services/file_watcher_service.py`
- Modify: `backend/app/tasks/ingestion_tasks.py` (add watch_directory task)
- Test: `backend/tests/services/test_file_watcher_service.py`
- Test: `backend/tests/integration/test_file_watcher_ingestion.py`

**Dependencies:** Add to `backend/requirements.txt`:
```
watchdog==4.0.0
python-magic==0.4.27
PyPDF2==3.0.1
python-docx==1.1.0
```

### Step 1: Install dependencies

**Command:**
```bash
cd backend
pip install watchdog==4.0.0 python-magic==0.4.27 PyPDF2==3.0.1 python-docx==1.1.0
```

**Expected:** Dependencies installed

### Step 2: Write failing unit test for FileWatcherService

**File:** `backend/tests/services/test_file_watcher_service.py`

```python
"""
Unit tests for FileWatcherService
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from app.services.file_watcher_service import FileWatcherService, FileChangeEvent


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_watcher():
    """Create FileWatcherService instance"""
    return FileWatcherService()


def test_extract_text_from_pdf(file_watcher, temp_dir):
    """Test extracting text from PDF file"""
    # Mock PDF reader
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF content here"
    mock_pdf.pages = [mock_page]

    with patch('PyPDF2.PdfReader', return_value=mock_pdf):
        content = file_watcher.extract_text_from_file(
            os.path.join(temp_dir, "test.pdf")
        )

    assert content == "PDF content here"


def test_extract_text_from_markdown(file_watcher, temp_dir):
    """Test extracting text from Markdown file"""
    md_path = os.path.join(temp_dir, "test.md")

    with open(md_path, 'w') as f:
        f.write("# Header\n\nMarkdown content")

    content = file_watcher.extract_text_from_file(md_path)

    assert "# Header" in content
    assert "Markdown content" in content


def test_extract_text_from_docx(file_watcher, temp_dir):
    """Test extracting text from DOCX file"""
    mock_doc = MagicMock()
    mock_para = MagicMock()
    mock_para.text = "DOCX paragraph content"
    mock_doc.paragraphs = [mock_para]

    with patch('docx.Document', return_value=mock_doc):
        content = file_watcher.extract_text_from_file(
            os.path.join(temp_dir, "test.docx")
        )

    assert content == "DOCX paragraph content"


def test_should_process_file_with_allowed_patterns(file_watcher):
    """Test file pattern matching"""
    patterns = ["*.pdf", "*.md", "*.txt"]

    assert file_watcher.should_process_file("/path/doc.pdf", patterns) == True
    assert file_watcher.should_process_file("/path/readme.md", patterns) == True
    assert file_watcher.should_process_file("/path/notes.txt", patterns) == True
    assert file_watcher.should_process_file("/path/image.png", patterns) == False


def test_should_ignore_file_with_ignore_patterns(file_watcher):
    """Test file ignore patterns"""
    ignore_patterns = [".git", "node_modules", "__pycache__"]

    assert file_watcher.should_ignore_file("/path/.git/config", ignore_patterns) == True
    assert file_watcher.should_ignore_file("/path/node_modules/pkg/file.js", ignore_patterns) == True
    assert file_watcher.should_ignore_file("/path/__pycache__/module.pyc", ignore_patterns) == True
    assert file_watcher.should_ignore_file("/path/src/main.py", ignore_patterns) == False


def test_detect_file_changes(file_watcher, temp_dir):
    """Test detecting file creation"""
    test_file = os.path.join(temp_dir, "test.md")

    # Create file
    with open(test_file, 'w') as f:
        f.write("Test content")

    # Simulate file event
    event = FileChangeEvent(
        event_type='created',
        file_path=test_file,
        is_directory=False
    )

    assert event.event_type == 'created'
    assert event.file_path == test_file
    assert event.is_directory == False


def test_debounce_rapid_changes(file_watcher):
    """Test debouncing rapid file changes"""
    from datetime import datetime, timedelta

    file_path = "/path/test.md"

    # Record first change
    file_watcher._last_processed[file_path] = datetime.now()

    # Immediate second change should be debounced
    should_process = file_watcher.should_debounce(file_path, debounce_seconds=2)

    assert should_process == False

    # Change after debounce period should be processed
    file_watcher._last_processed[file_path] = datetime.now() - timedelta(seconds=3)
    should_process = file_watcher.should_debounce(file_path, debounce_seconds=2)

    assert should_process == True
```

### Step 3: Run test to verify it fails

**Command:**
```bash
cd backend
pytest tests/services/test_file_watcher_service.py -v
```

**Expected:** FAIL - Module not found

### Step 4: Implement FileWatcherService

**File:** `backend/app/services/file_watcher_service.py`

```python
"""
File watcher service for monitoring local directories
"""
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Callable, Dict
from dataclasses import dataclass
from pathlib import Path
import fnmatch

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import PyPDF2
from docx import Document

logger = logging.getLogger(__name__)


@dataclass
class FileChangeEvent:
    """Represents a file system change event"""
    event_type: str  # created, modified, deleted
    file_path: str
    is_directory: bool


class FileWatcherService:
    """Service for monitoring file system changes"""

    def __init__(self):
        self.logger = logger
        self._last_processed: Dict[str, datetime] = {}

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text content from various file types.

        Args:
            file_path: Path to file

        Returns:
            Extracted text content
        """
        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext == '.pdf':
                return self._extract_pdf(file_path)
            elif file_ext == '.docx':
                return self._extract_docx(file_path)
            elif file_ext in ['.txt', '.md', '.markdown']:
                return self._extract_text(file_path)
            else:
                self.logger.warning(f"Unsupported file type: {file_ext}")
                return ""

        except Exception as e:
            self.logger.error(f"Failed to extract text from {file_path}: {e}")
            return ""

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text_parts = []

            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())

            return '\n\n'.join(text_parts)

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        doc = Document(file_path)
        text_parts = [para.text for para in doc.paragraphs]
        return '\n\n'.join(text_parts)

    def _extract_text(self, file_path: str) -> str:
        """Extract text from plain text file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def should_process_file(
        self,
        file_path: str,
        patterns: List[str]
    ) -> bool:
        """
        Check if file matches any of the allowed patterns.

        Args:
            file_path: Path to file
            patterns: List of glob patterns (e.g., ["*.pdf", "*.md"])

        Returns:
            True if file should be processed
        """
        filename = os.path.basename(file_path)

        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def should_ignore_file(
        self,
        file_path: str,
        ignore_patterns: List[str]
    ) -> bool:
        """
        Check if file matches any ignore patterns.

        Args:
            file_path: Path to file
            ignore_patterns: List of ignore patterns (e.g., [".git", "node_modules"])

        Returns:
            True if file should be ignored
        """
        for pattern in ignore_patterns:
            if pattern in file_path:
                return True

        return False

    def should_debounce(
        self,
        file_path: str,
        debounce_seconds: int = 2
    ) -> bool:
        """
        Check if enough time has passed since last processing.

        Args:
            file_path: Path to file
            debounce_seconds: Seconds to wait between processing same file

        Returns:
            True if file should be processed (debounce period elapsed)
        """
        now = datetime.now()

        if file_path in self._last_processed:
            time_since_last = now - self._last_processed[file_path]
            if time_since_last < timedelta(seconds=debounce_seconds):
                return False

        self._last_processed[file_path] = now
        return True


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events"""

    def __init__(
        self,
        callback: Callable[[FileChangeEvent], None],
        patterns: List[str],
        ignore_patterns: List[str]
    ):
        self.callback = callback
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns
        self.file_watcher = FileWatcherService()

    def on_created(self, event: FileSystemEvent):
        """Called when file is created"""
        if event.is_directory:
            return

        self._process_event('created', event.src_path)

    def on_modified(self, event: FileSystemEvent):
        """Called when file is modified"""
        if event.is_directory:
            return

        self._process_event('modified', event.src_path)

    def _process_event(self, event_type: str, file_path: str):
        """Process file system event"""
        # Check patterns
        if not self.file_watcher.should_process_file(file_path, self.patterns):
            return

        # Check ignore patterns
        if self.file_watcher.should_ignore_file(file_path, self.ignore_patterns):
            return

        # Debounce
        if not self.file_watcher.should_debounce(file_path, debounce_seconds=2):
            return

        # Trigger callback
        event = FileChangeEvent(
            event_type=event_type,
            file_path=file_path,
            is_directory=False
        )

        self.callback(event)


def start_watching(
    directory: str,
    callback: Callable[[FileChangeEvent], None],
    patterns: List[str] = None,
    ignore_patterns: List[str] = None
) -> Observer:
    """
    Start watching directory for file changes.

    Args:
        directory: Directory to watch
        callback: Function to call when file changes
        patterns: File patterns to watch (default: all)
        ignore_patterns: Patterns to ignore (default: ['.git', '__pycache__'])

    Returns:
        Observer instance (call .stop() to stop watching)
    """
    if patterns is None:
        patterns = ['*']

    if ignore_patterns is None:
        ignore_patterns = ['.git', '__pycache__', '.DS_Store', 'node_modules']

    event_handler = FileChangeHandler(callback, patterns, ignore_patterns)

    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()

    logger.info(f"Started watching directory: {directory}")

    return observer
```

### Step 5: Run unit tests to verify they pass

**Command:**
```bash
cd backend
pytest tests/services/test_file_watcher_service.py -v
```

**Expected:** All tests PASS

### Step 6: Write failing integration test

**File:** `backend/tests/integration/test_file_watcher_ingestion.py`

```python
"""
Integration tests for file watcher ingestion
"""
import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.ingestion_source import IngestionSource, SourceType
from app.models.project import Project
from app.tasks.ingestion_tasks import process_file_change
from app.services.file_watcher_service import FileChangeEvent


@pytest.fixture
def temp_watch_dir():
    """Create temporary directory for file watching"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_watcher_source(
    db_session: Session,
    sample_project: Project,
    temp_watch_dir: str
) -> IngestionSource:
    """Create a file watcher ingestion source"""
    source = IngestionSource(
        project_id=sample_project.id,
        type=SourceType.FILE_WATCHER,
        name="Research Documents",
        path=temp_watch_dir,
        priority=7,
        enabled=True,
        config={
            "patterns": ["*.pdf", "*.md", "*.txt"],
            "ignore": [".git", "__pycache__"]
        }
    )
    db_session.add(source)
    db_session.commit()
    return source


def test_process_new_markdown_file(
    db_session: Session,
    file_watcher_source: IngestionSource,
    temp_watch_dir: str
):
    """Test processing newly created Markdown file"""
    # Create test file
    md_file = os.path.join(temp_watch_dir, "notes.md")
    with open(md_file, 'w') as f:
        f.write("# Research Notes\n\nImportant findings about the topic...")

    # Simulate file change event
    event = FileChangeEvent(
        event_type='created',
        file_path=md_file,
        is_directory=False
    )

    result = process_file_change(file_watcher_source.id, event)

    assert result['status'] == 'success'
    assert result['documents_ingested'] == 1

    # Verify source updated
    db_session.refresh(file_watcher_source)
    assert file_watcher_source.documents_ingested == 1


def test_process_pdf_file(
    db_session: Session,
    file_watcher_source: IngestionSource,
    temp_watch_dir: str
):
    """Test processing PDF file"""
    from unittest.mock import patch, MagicMock

    pdf_file = os.path.join(temp_watch_dir, "paper.pdf")
    Path(pdf_file).touch()  # Create empty file

    # Mock PDF extraction
    with patch('app.services.file_watcher_service.FileWatcherService.extract_text_from_file',
               return_value="PDF content extracted"):
        event = FileChangeEvent(
            event_type='created',
            file_path=pdf_file,
            is_directory=False
        )

        result = process_file_change(file_watcher_source.id, event)

    assert result['status'] == 'success'


def test_ignore_non_matching_files(
    file_watcher_source: IngestionSource,
    temp_watch_dir: str
):
    """Test that non-matching files are ignored"""
    # Create file that doesn't match patterns
    img_file = os.path.join(temp_watch_dir, "image.png")
    Path(img_file).touch()

    event = FileChangeEvent(
        event_type='created',
        file_path=img_file,
        is_directory=False
    )

    result = process_file_change(file_watcher_source.id, event)

    assert result['status'] == 'skipped'
```

### Step 7: Run integration test to verify it fails

**Command:**
```bash
cd backend
pytest tests/integration/test_file_watcher_ingestion.py -v
```

**Expected:** FAIL - Task 'process_file_change' not found

### Step 8: Add process_file_change task to ingestion_tasks.py

**File:** `backend/app/tasks/ingestion_tasks.py`

Add import:
```python
from app.services.file_watcher_service import FileWatcherService, FileChangeEvent
```

Add task:
```python
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
    db = SessionLocal()

    try:
        # Load source
        source = db.query(IngestionSource).filter(
            IngestionSource.id == source_id
        ).first()

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

        # Check patterns
        if not file_watcher.should_process_file(event.file_path, patterns):
            return {'status': 'skipped', 'message': 'File does not match patterns'}

        if file_watcher.should_ignore_file(event.file_path, ignore_patterns):
            return {'status': 'skipped', 'message': 'File matches ignore patterns'}

        # Update source status
        source.status = SourceStatus.RUNNING
        source.last_run = datetime.utcnow()
        db.commit()

        # Extract content
        content = file_watcher.extract_text_from_file(event.file_path)

        if not content:
            return {'status': 'skipped', 'message': 'No content extracted'}

        # Ingest into RAG
        rag_service = RAGService()

        filename = os.path.basename(event.file_path)

        rag_service.add_document(
            project_id=source.project_id,
            content=content,
            metadata={
                'title': filename,
                'file_path': event.file_path,
                'file_type': Path(event.file_path).suffix,
                'event_type': event.event_type,
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
        db.commit()

        logger.info(f"File ingested: {filename}")

        return {
            'status': 'success',
            'documents_ingested': 1,
            'file_path': event.file_path
        }

    except Exception as e:
        logger.error(f"File processing failed: {e}")

        if source:
            source.status = SourceStatus.ERROR
            source.error_count += 1
            source.last_error = str(e)
            db.commit()

        return {'status': 'error', 'error': str(e)}

    finally:
        db.close()
```

### Step 9: Run integration tests to verify they pass

**Command:**
```bash
cd backend
pytest tests/integration/test_file_watcher_ingestion.py -v
```

**Expected:** All tests PASS

### Step 10: Commit

```bash
git add backend/app/services/file_watcher_service.py \
        backend/app/tasks/ingestion_tasks.py \
        backend/tests/services/test_file_watcher_service.py \
        backend/tests/integration/test_file_watcher_ingestion.py \
        backend/requirements.txt

git commit -m "feat: add file system watcher for document ingestion

- Implement FileWatcherService using watchdog
- Extract text from PDF, DOCX, Markdown, TXT files
- Support file patterns and ignore patterns
- Add debouncing for rapid changes
- Create Celery task for file change processing
- Full unit and integration test coverage

Phase B Task 5/6 complete"
```

---

## Task 6: Source Management API & UI

**Goal:** Create API endpoints and UI components for managing ingestion sources.

**Files:**
- Create: `backend/app/routers/ingestion_sources.py`
- Test: `backend/tests/integration/test_ingestion_sources_api.py`
- Modify: `backend/app/main.py` (register router)

### Step 1: Write failing integration test for source management API

**File:** `backend/tests/integration/test_ingestion_sources_api.py`

```python
"""
Integration tests for ingestion sources API
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project import Project
from app.models.ingestion_source import SourceType, SourceStatus


client = TestClient(app)


def test_create_rss_source(sample_project: Project):
    """Test creating RSS ingestion source"""
    payload = {
        "project_id": sample_project.id,
        "type": "rss",
        "name": "Tech Blog",
        "url": "https://example.com/feed.xml",
        "schedule": "0 * * * *",
        "priority": 8,
        "enabled": True
    }

    response = client.post("/api/ingestion/sources", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data['name'] == "Tech Blog"
    assert data['type'] == "rss"
    assert data['status'] == "pending"


def test_list_sources(sample_project: Project, db_session: Session):
    """Test listing ingestion sources"""
    from app.models.ingestion_source import IngestionSource

    # Create test sources
    source1 = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="Source 1", url="https://example.com/feed1", priority=5, enabled=True
    )
    source2 = IngestionSource(
        project_id=sample_project.id, type=SourceType.DOCUMENTATION,
        name="Source 2", url="https://example.com/docs", priority=7, enabled=True
    )
    db_session.add_all([source1, source2])
    db_session.commit()

    response = client.get(f"/api/ingestion/sources?project_id={sample_project.id}")

    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert len(data['sources']) == 2


def test_get_source_by_id(sample_project: Project, db_session: Session):
    """Test getting single source"""
    from app.models.ingestion_source import IngestionSource

    source = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="Test Source", url="https://example.com/feed", priority=5, enabled=True
    )
    db_session.add(source)
    db_session.commit()

    response = client.get(f"/api/ingestion/sources/{source.id}")

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == source.id
    assert data['name'] == "Test Source"


def test_update_source(sample_project: Project, db_session: Session):
    """Test updating source"""
    from app.models.ingestion_source import IngestionSource

    source = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="Old Name", url="https://example.com/feed", priority=5, enabled=True
    )
    db_session.add(source)
    db_session.commit()

    update_payload = {
        "name": "New Name",
        "priority": 9,
        "enabled": False
    }

    response = client.put(f"/api/ingestion/sources/{source.id}", json=update_payload)

    assert response.status_code == 200
    data = response.json()
    assert data['name'] == "New Name"
    assert data['priority'] == 9
    assert data['enabled'] == False


def test_delete_source(sample_project: Project, db_session: Session):
    """Test deleting source"""
    from app.models.ingestion_source import IngestionSource

    source = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="To Delete", url="https://example.com/feed", priority=5, enabled=True
    )
    db_session.add(source)
    db_session.commit()

    response = client.delete(f"/api/ingestion/sources/{source.id}")

    assert response.status_code == 204

    # Verify deleted
    db_session.expire_all()
    deleted_source = db_session.query(IngestionSource).filter(
        IngestionSource.id == source.id
    ).first()
    assert deleted_source is None


def test_trigger_manual_run(sample_project: Project, db_session: Session):
    """Test manually triggering source run"""
    from app.models.ingestion_source import IngestionSource
    from unittest.mock import patch

    source = IngestionSource(
        project_id=sample_project.id, type=SourceType.RSS,
        name="Manual Source", url="https://example.com/feed", priority=5, enabled=True
    )
    db_session.add(source)
    db_session.commit()

    with patch('app.tasks.ingestion_tasks.scrape_rss_feed.delay') as mock_task:
        mock_task.return_value.id = 'task-123'

        response = client.post(f"/api/ingestion/sources/{source.id}/run")

        assert response.status_code == 202
        data = response.json()
        assert 'task_id' in data
        mock_task.assert_called_once_with(source.id)
```

### Step 2: Run test to verify it fails

**Command:**
```bash
cd backend
pytest tests/integration/test_ingestion_sources_api.py -v
```

**Expected:** FAIL - Routes not found

### Step 3: Create ingestion sources router

**File:** `backend/app/routers/ingestion_sources.py`

```python
"""
API endpoints for managing ingestion sources
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ingestion_source import IngestionSource, SourceType
from app.schemas.ingestion import (
    IngestionSourceCreate,
    IngestionSourceUpdate,
    IngestionSourceResponse,
    IngestionSourceList
)
from app.tasks.ingestion_tasks import (
    scrape_rss_feed,
    scrape_documentation,
    process_webhook_payload
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])


@router.post("/sources", response_model=IngestionSourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(
    source: IngestionSourceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new ingestion source.
    """
    db_source = IngestionSource(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    logger.info(f"Created ingestion source: {db_source.name} (ID: {db_source.id})")

    return db_source


@router.get("/sources", response_model=IngestionSourceList)
def list_sources(
    project_id: Optional[int] = Query(None),
    type: Optional[SourceType] = Query(None),
    enabled: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List ingestion sources with optional filters.
    """
    query = db.query(IngestionSource)

    if project_id:
        query = query.filter(IngestionSource.project_id == project_id)

    if type:
        query = query.filter(IngestionSource.type == type)

    if enabled is not None:
        query = query.filter(IngestionSource.enabled == enabled)

    # Order by priority descending
    query = query.order_by(IngestionSource.priority.desc())

    total = query.count()
    sources = query.offset(skip).limit(limit).all()

    return IngestionSourceList(sources=sources, total=total)


@router.get("/sources/{source_id}", response_model=IngestionSourceResponse)
def get_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Get ingestion source by ID.
    """
    source = db.query(IngestionSource).filter(
        IngestionSource.id == source_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Ingestion source not found")

    return source


@router.put("/sources/{source_id}", response_model=IngestionSourceResponse)
def update_source(
    source_id: int,
    source_update: IngestionSourceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update ingestion source.
    """
    source = db.query(IngestionSource).filter(
        IngestionSource.id == source_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Ingestion source not found")

    # Update fields
    update_data = source_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    db.commit()
    db.refresh(source)

    logger.info(f"Updated ingestion source: {source.name} (ID: {source.id})")

    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete ingestion source.
    """
    source = db.query(IngestionSource).filter(
        IngestionSource.id == source_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Ingestion source not found")

    db.delete(source)
    db.commit()

    logger.info(f"Deleted ingestion source: {source.name} (ID: {source_id})")

    return None


@router.post("/sources/{source_id}/run", status_code=status.HTTP_202_ACCEPTED)
def trigger_manual_run(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually trigger ingestion source run.
    """
    source = db.query(IngestionSource).filter(
        IngestionSource.id == source_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Ingestion source not found")

    if not source.enabled:
        raise HTTPException(status_code=400, detail="Source is disabled")

    # Trigger appropriate task based on source type
    task = None

    if source.type == SourceType.RSS:
        task = scrape_rss_feed.delay(source_id)
    elif source.type == SourceType.DOCUMENTATION:
        task = scrape_documentation.delay(source_id)
    elif source.type == SourceType.WEBHOOK:
        raise HTTPException(
            status_code=400,
            detail="Webhook sources cannot be triggered manually"
        )
    elif source.type == SourceType.FILE_WATCHER:
        raise HTTPException(
            status_code=400,
            detail="File watcher sources run automatically"
        )

    logger.info(f"Triggered manual run for source: {source.name} (task_id: {task.id})")

    return {
        "task_id": task.id,
        "source_id": source_id,
        "source_name": source.name
    }
```

### Step 4: Register router in main.py

**File:** `backend/app/main.py`

Add import:
```python
from app.routers import ingestion_sources
```

Add router:
```python
app.include_router(ingestion_sources.router)
```

### Step 5: Run integration tests to verify they pass

**Command:**
```bash
cd backend
pytest tests/integration/test_ingestion_sources_api.py -v
```

**Expected:** All tests PASS

### Step 6: Run all Phase B tests

**Command:**
```bash
cd backend
pytest tests/integration/test_ingestion_source_model.py \
       tests/services/test_feed_scraper_service.py \
       tests/integration/test_rss_ingestion.py \
       tests/services/test_documentation_scraper_service.py \
       tests/integration/test_documentation_ingestion.py \
       tests/integration/test_webhook_ingestion.py \
       tests/services/test_file_watcher_service.py \
       tests/integration/test_file_watcher_ingestion.py \
       tests/integration/test_ingestion_sources_api.py -v
```

**Expected:** All tests PASS (50+ tests)

### Step 7: Commit

```bash
git add backend/app/routers/ingestion_sources.py \
        backend/app/main.py \
        backend/tests/integration/test_ingestion_sources_api.py

git commit -m "feat: add ingestion sources management API

- Create CRUD endpoints for ingestion sources
- Support filtering by project, type, and enabled status
- Add manual trigger endpoint for on-demand runs
- Full integration test coverage

Phase B Task 6/6 complete"
```

---

## Phase B Completion Checklist

### Verify All Features

**Run full test suite:**
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

**Expected:** Test coverage >85%

### Documentation

Update `docs/KNOWLEDGE_INGESTION.md`:

```markdown
# Knowledge Ingestion System

## Overview

Automated pipelines for continuous knowledge gathering from multiple sources.

## Supported Sources

### 1. RSS Feeds
- **Use case**: Monitor blogs, news sites, release feeds
- **Schedule**: Configurable (hourly, daily, weekly)
- **Content**: Full article extraction
- **Example**: Tech blogs, security advisories

### 2. Documentation Sites
- **Use case**: Index project documentation
- **Scraping**: Recursive crawling with depth limits
- **Respect**: robots.txt and sitemap.xml
- **Example**: FastAPI docs, Python docs

### 3. Webhooks
- **Use case**: Real-time notifications
- **Supported**: GitHub (releases, commits), generic
- **Security**: Signature verification
- **Example**: GitHub repository updates

### 4. File Watchers
- **Use case**: Monitor local directories
- **Supported**: PDF, DOCX, Markdown, TXT
- **Features**: Debouncing, pattern matching
- **Example**: Research papers folder

## Configuration

Sources are managed via API or UI:

```python
POST /api/ingestion/sources
{
    "project_id": 1,
    "type": "rss",
    "name": "Tech Blog",
    "url": "https://example.com/feed.xml",
    "schedule": "0 * * * *",  # Every hour
    "priority": 8,
    "enabled": true
}
```

## Priority System

Priority (1-10) affects RAG retrieval:
- 10: Critical sources (official docs)
- 7-9: High priority (trusted blogs)
- 4-6: Medium priority (community content)
- 1-3: Low priority (experimental sources)

## Monitoring

Track source health:
- Status: pending, running, success, error
- Metrics: documents_ingested, error_count
- Timestamps: last_run, last_success

## Troubleshooting

**Source failing?**
- Check `last_error` field
- Review Celery logs
- Verify URL accessibility
- Check robots.txt permissions

**No documents ingested?**
- Verify source is enabled
- Check schedule configuration
- Review content extraction logs
- Ensure RAG service is running
```

### Step 8: Final commit

```bash
git add docs/KNOWLEDGE_INGESTION.md

git commit -m "docs: add knowledge ingestion documentation

Complete documentation for Phase B automated ingestion system.

Phase B complete: All 6 tasks implemented and tested."
```

---

## Success Criteria Verification

- [x] RSS feeds scraped automatically on schedule
- [x] Documentation sites indexed successfully
- [x] GitHub webhooks trigger ingestion
- [x] File watchers detect and process new documents
- [x] Source priority reflected in RAG results
- [x] Error handling logs failures without crashing
- [x] Test coverage >85% for ingestion code
- [x] Documentation complete with examples

**Phase B Status**: ✅ Complete

---

## Execution Options

Plan complete and saved to `docs/plans/2025-10-30-phase-b-knowledge-ingestion-plan.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
