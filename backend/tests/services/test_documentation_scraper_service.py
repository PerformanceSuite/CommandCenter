"""
Unit tests for DocumentationScraperService
"""
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.documentation_scraper_service import (
    DocumentationPage,
    DocumentationScraperService,
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

    urls = doc_scraper.fetch_sitemap("https://example.com/sitemap.xml")

    assert len(urls) == 2
    assert "https://example.com/docs/intro" in urls
    assert "https://example.com/docs/guide" in urls


def test_check_robots_txt(doc_scraper):
    """Test checking robots.txt for allowed URLs"""
    mock_robots = """User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /docs/
"""

    # Mock the robots.txt fetch
    with patch("urllib.robotparser.RobotFileParser.read") as mock_read:
        with patch("urllib.robotparser.RobotFileParser.can_fetch") as mock_can_fetch:
            # Set up the mock to allow /docs/ and disallow /admin/
            def can_fetch_side_effect(user_agent, url):
                if "/admin/" in url:
                    return False
                if "/docs/" in url:
                    return True
                return True

            mock_can_fetch.side_effect = can_fetch_side_effect

            # Should be allowed
            assert doc_scraper.is_allowed("https://example.com/docs/guide") == True

            # Should be disallowed
            assert doc_scraper.is_allowed("https://example.com/admin/") == False


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

    with patch("time.sleep"):  # Skip rate limiting delay
        page = doc_scraper.scrape_page("https://example.com/docs/intro")

    assert page.title == "Introduction | Docs"
    assert "Introduction" in page.content
    assert "Hello World" in page.content
    assert page.url == "https://example.com/docs/intro"


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
        "https://example.com/docs/intro", base_url="https://example.com"
    )

    assert len(links) == 2  # Only internal links
    assert "https://example.com/docs/guide" in links
    assert "https://example.com/docs/api" in links
    assert "https://external.com/link" not in links


def test_scrape_with_max_depth(doc_scraper):
    """Test scraping with depth limit"""
    with patch.object(doc_scraper, "scrape_page") as mock_scrape:
        with patch.object(doc_scraper, "extract_links", return_value=[]):
            mock_scrape.return_value = DocumentationPage(
                url="https://example.com/docs", title="Docs", content="Content", headings=["H1"]
            )

            pages = doc_scraper.scrape_documentation("https://example.com/docs", max_depth=0)

    assert len(pages) == 1
    mock_scrape.assert_called_once()


def test_handle_404_error(doc_scraper):
    """Test handling 404 errors gracefully"""
    mock_response = Mock()
    mock_response.status_code = 404
    doc_scraper.session.get = Mock(return_value=mock_response)

    with patch("time.sleep"):  # Skip rate limiting delay
        page = doc_scraper.scrape_page("https://example.com/not-found")

    assert page is None


def test_ssrf_protection_localhost(doc_scraper):
    """Test SSRF protection blocks localhost URLs"""
    with pytest.raises(ValueError, match="Access to localhost is not allowed"):
        doc_scraper._is_safe_url("http://localhost:8080/admin")

    with pytest.raises(ValueError, match="Access to localhost is not allowed"):
        doc_scraper._is_safe_url("https://localhost/api")


def test_ssrf_protection_loopback_ip(doc_scraper):
    """Test SSRF protection blocks loopback IP addresses"""
    with pytest.raises(ValueError, match="Access to loopback address"):
        doc_scraper._is_safe_url("http://127.0.0.1/admin")

    with pytest.raises(ValueError, match="Access to loopback address"):
        doc_scraper._is_safe_url("http://127.0.0.2:8080/internal")


def test_ssrf_protection_private_ip(doc_scraper):
    """Test SSRF protection blocks private IP addresses"""
    # 192.168.x.x range
    with pytest.raises(ValueError, match="Access to private IP address"):
        doc_scraper._is_safe_url("http://192.168.1.1/router")

    # 10.x.x.x range
    with pytest.raises(ValueError, match="Access to private IP address"):
        doc_scraper._is_safe_url("http://10.0.0.1/internal")

    # 172.16-31.x.x range
    with pytest.raises(ValueError, match="Access to private IP address"):
        doc_scraper._is_safe_url("http://172.16.0.1/internal")


def test_ssrf_protection_cloud_metadata(doc_scraper):
    """Test SSRF protection blocks cloud metadata endpoint"""
    with pytest.raises(ValueError, match="Access to cloud metadata endpoint is not allowed"):
        doc_scraper._is_safe_url("http://169.254.169.254/latest/meta-data/")


def test_ssrf_protection_link_local(doc_scraper):
    """Test SSRF protection blocks link-local addresses"""
    with pytest.raises(ValueError, match="Access to link-local address"):
        doc_scraper._is_safe_url("http://169.254.1.1/service")


def test_ssrf_protection_invalid_scheme(doc_scraper):
    """Test SSRF protection blocks non-http(s) schemes"""
    with pytest.raises(ValueError, match="Invalid URL scheme.*Only http and https are allowed"):
        doc_scraper._is_safe_url("file:///etc/passwd")

    with pytest.raises(ValueError, match="Invalid URL scheme.*Only http and https are allowed"):
        doc_scraper._is_safe_url("ftp://example.com/file")


def test_ssrf_protection_valid_url(doc_scraper):
    """Test SSRF protection allows valid public URLs"""
    # Should not raise any exception
    assert doc_scraper._is_safe_url("https://example.com/docs") == True
    assert doc_scraper._is_safe_url("http://docs.python.org/api") == True


def test_scrape_page_ssrf_protection(doc_scraper):
    """Test that scrape_page validates URLs for SSRF"""
    with pytest.raises(ValueError, match="Access to localhost is not allowed"):
        with patch("time.sleep"):
            doc_scraper.scrape_page("http://localhost:8080/admin")


def test_fetch_sitemap_ssrf_protection(doc_scraper):
    """Test that fetch_sitemap validates URLs for SSRF"""
    with pytest.raises(ValueError, match="Access to private IP address"):
        doc_scraper.fetch_sitemap("http://192.168.1.1/sitemap.xml")


def test_scrape_documentation_ssrf_protection(doc_scraper):
    """Test that scrape_documentation validates start URL for SSRF"""
    with pytest.raises(ValueError, match="Access to loopback address"):
        doc_scraper.scrape_documentation("http://127.0.0.1:8000/docs")
