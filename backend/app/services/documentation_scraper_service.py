"""
Documentation scraper service for automated docs ingestion
"""
import logging
import time
import ipaddress
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

    def _is_safe_url(self, url: str) -> bool:
        """
        Validate URL to prevent SSRF attacks.

        Args:
            url: URL to validate

        Returns:
            True if URL is safe, False otherwise

        Raises:
            ValueError: If URL is not safe with detailed reason
        """
        try:
            parsed = urlparse(url)

            # Only allow http and https schemes
            if parsed.scheme not in ('http', 'https'):
                raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed.")

            # Get hostname
            hostname = parsed.hostname
            if not hostname:
                raise ValueError("URL must have a valid hostname")

            # Block localhost variations
            if hostname.lower() in ('localhost', 'localhost.localdomain'):
                raise ValueError("Access to localhost is not allowed")

            # Try to resolve hostname to IP address
            try:
                import socket
                ip_str = socket.gethostbyname(hostname)
                ip = ipaddress.ip_address(ip_str)

                # Block loopback addresses (127.0.0.0/8, ::1)
                if ip.is_loopback:
                    raise ValueError(f"Access to loopback address {ip} is not allowed")

                # Block cloud metadata endpoint (169.254.169.254) - check before link-local
                if str(ip) == '169.254.169.254':
                    raise ValueError("Access to cloud metadata endpoint is not allowed")

                # Block link-local addresses (169.254.0.0/16, fe80::/10)
                if ip.is_link_local:
                    raise ValueError(f"Access to link-local address {ip} is not allowed")

                # Block private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7)
                if ip.is_private:
                    raise ValueError(f"Access to private IP address {ip} is not allowed")

            except socket.gaierror:
                # If hostname cannot be resolved, allow it (will fail naturally on request)
                self.logger.warning(f"Could not resolve hostname: {hostname}")

            return True

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}")

    def fetch_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Fetch and parse sitemap.xml for URLs.

        Args:
            sitemap_url: URL of sitemap

        Returns:
            List of URLs from sitemap
        """
        self.logger.info(f"Fetching sitemap: {sitemap_url}")

        # Validate URL for SSRF protection
        self._is_safe_url(sitemap_url)

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
        # Validate URL for SSRF protection
        self._is_safe_url(url)

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

        # Validate start URL for SSRF protection
        self._is_safe_url(start_url)

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
