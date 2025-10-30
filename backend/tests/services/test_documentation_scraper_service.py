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

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_sitemap
    doc_scraper.session.get = Mock(return_value=mock_response)

    urls = doc_scraper.fetch_sitemap('https://example.com/sitemap.xml')

    assert len(urls) == 2
    assert 'https://example.com/docs/intro' in urls
    assert 'https://example.com/docs/guide' in urls


def test_check_robots_txt(doc_scraper):
    """Test checking robots.txt for allowed URLs"""
    mock_robots = """User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /docs/
"""

    # Mock the robots.txt fetch
    with patch('urllib.robotparser.RobotFileParser.read') as mock_read:
        with patch('urllib.robotparser.RobotFileParser.can_fetch') as mock_can_fetch:
            # Set up the mock to allow /docs/ and disallow /admin/
            def can_fetch_side_effect(user_agent, url):
                if '/admin/' in url:
                    return False
                if '/docs/' in url:
                    return True
                return True

            mock_can_fetch.side_effect = can_fetch_side_effect

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

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    doc_scraper.session.get = Mock(return_value=mock_response)

    with patch('time.sleep'):  # Skip rate limiting delay
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

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    doc_scraper.session.get = Mock(return_value=mock_response)

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
    mock_response = Mock()
    mock_response.status_code = 404
    doc_scraper.session.get = Mock(return_value=mock_response)

    with patch('time.sleep'):  # Skip rate limiting delay
        page = doc_scraper.scrape_page('https://example.com/not-found')

    assert page is None
