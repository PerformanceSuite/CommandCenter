"""
Unit tests for FeedScraperService
"""
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.feed_scraper_service import FeedEntry, FeedScraperService


@pytest.fixture
def feed_scraper():
    """Create FeedScraperService instance"""
    return FeedScraperService()


def test_parse_rss_feed(feed_scraper):
    """Test parsing RSS 2.0 feed"""
    mock_feed_data = {
        "entries": [
            {
                "title": "Test Article",
                "link": "https://example.com/article",
                "summary": "This is a test article summary",
                "published_parsed": (2024, 1, 15, 10, 30, 0, 0, 0, 0),
                "author": "John Doe",
                "tags": [{"term": "python"}, {"term": "testing"}],
            }
        ],
        "feed": {"title": "Test Blog"},
        "bozo": False,
    }

    with patch("feedparser.parse", return_value=mock_feed_data):
        entries = feed_scraper.parse_feed("https://example.com/feed.xml")

    assert len(entries) == 1
    assert entries[0].title == "Test Article"
    assert entries[0].url == "https://example.com/article"
    assert entries[0].author == "John Doe"
    assert entries[0].tags == ["python", "testing"]


def test_parse_atom_feed(feed_scraper):
    """Test parsing Atom feed"""
    mock_feed_data = {
        "entries": [
            {
                "title": "Atom Article",
                "link": "https://example.com/atom-article",
                "summary": "Atom feed article",
                "updated_parsed": (2024, 1, 20, 14, 0, 0, 0, 0, 0),
                "author": "Jane Smith",
            }
        ],
        "feed": {"title": "Atom Feed"},
        "bozo": False,
    }

    with patch("feedparser.parse", return_value=mock_feed_data):
        entries = feed_scraper.parse_feed("https://example.com/atom.xml")

    assert len(entries) == 1
    assert entries[0].title == "Atom Article"


def test_extract_full_content(feed_scraper):
    """Test extracting full article content"""
    mock_article = Mock()
    mock_article.text = "This is the full article content with multiple paragraphs."
    mock_article.download.return_value = None
    mock_article.parse.return_value = None

    with patch("app.services.feed_scraper_service.Article", return_value=mock_article):
        content = feed_scraper.extract_full_content("https://example.com/article")

    assert content == "This is the full article content with multiple paragraphs."
    mock_article.download.assert_called_once()
    mock_article.parse.assert_called_once()


def test_extract_full_content_fallback(feed_scraper):
    """Test fallback when content extraction fails"""
    with patch(
        "app.services.feed_scraper_service.Article", side_effect=Exception("Download failed")
    ):
        content = feed_scraper.extract_full_content(
            "https://example.com/article", summary_fallback="Summary content"
        )

    assert content == "Summary content"


def test_deduplicate_entries(feed_scraper):
    """Test deduplication by URL"""
    entries = [
        FeedEntry(
            title="Article 1",
            url="https://example.com/article1",
            content="Content 1",
            published=datetime(2024, 1, 15),
        ),
        FeedEntry(
            title="Article 1 Duplicate",
            url="https://example.com/article1",  # Same URL
            content="Content 1 duplicate",
            published=datetime(2024, 1, 16),
        ),
        FeedEntry(
            title="Article 2",
            url="https://example.com/article2",
            content="Content 2",
            published=datetime(2024, 1, 17),
        ),
    ]

    deduped = feed_scraper.deduplicate_entries(entries)

    assert len(deduped) == 2
    assert deduped[0].url == "https://example.com/article1"
    assert deduped[1].url == "https://example.com/article2"
    # Should keep most recent duplicate
    assert deduped[0].published == datetime(2024, 1, 16)


def test_parse_feed_with_authentication(feed_scraper):
    """Test parsing feed with HTTP Basic auth"""
    mock_feed_data = {
        "entries": [{"title": "Authenticated Article", "link": "https://example.com/auth"}],
        "feed": {"title": "Private Feed"},
        "bozo": False,
    }

    with patch("feedparser.parse", return_value=mock_feed_data) as mock_parse:
        entries = feed_scraper.parse_feed(
            "https://example.com/feed.xml", auth=("username", "password")
        )

    assert len(entries) == 1
    # Verify auth was passed to feedparser
    call_args = mock_parse.call_args
    assert "username" in str(call_args)


def test_handle_malformed_feed(feed_scraper):
    """Test handling malformed/invalid feed"""
    mock_feed_data = {"entries": [], "bozo": True, "bozo_exception": Exception("Feed is malformed")}

    with patch("feedparser.parse", return_value=mock_feed_data):
        with pytest.raises(ValueError, match="Feed is malformed or invalid"):
            feed_scraper.parse_feed("https://example.com/bad-feed.xml")
