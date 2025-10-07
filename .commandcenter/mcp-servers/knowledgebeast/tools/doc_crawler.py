"""
Documentation Crawler

Context7-style documentation integration for ingesting and auto-updating
documentation from various sources (Anthropic docs, GitHub repos, local docs).
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.rag_service import RAGService


class DocumentationCrawler:
    """
    Documentation crawler for KnowledgeBeast

    Provides Context7-style documentation integration with:
    - Anthropic docs crawling
    - GitHub repository documentation
    - Local documentation monitoring
    - Automatic updates and versioning
    """

    def __init__(self, rag_service: RAGService, config_path: Optional[str] = None):
        """
        Initialize documentation crawler

        Args:
            rag_service: RAG service instance
            config_path: Path to sources configuration file
        """
        self.rag_service = rag_service
        self.config_path = config_path or ".commandcenter/knowledge/sources.json"
        self.sources_config = self._load_sources_config()

    def _load_sources_config(self) -> Dict[str, Any]:
        """
        Load documentation sources configuration

        Returns:
            Sources configuration
        """
        config_file = Path(self.config_path)

        if not config_file.exists():
            # Return default configuration
            return {
                "sources": [
                    {
                        "type": "anthropic_docs",
                        "url": "https://docs.anthropic.com",
                        "auto_update": True,
                        "priority": "high",
                        "enabled": False  # Disabled by default
                    }
                ],
                "update_interval_hours": 24,
                "last_update": None
            }

        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sources config: {e}")
            return {"sources": []}

    def _save_sources_config(self):
        """Save sources configuration to file"""
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w") as f:
            json.dump(self.sources_config, indent=2, fp=f)

    async def crawl_anthropic_docs(
        self,
        base_url: str = "https://docs.anthropic.com",
        max_pages: int = 100
    ) -> Dict[str, Any]:
        """
        Crawl Anthropic documentation

        Note: This is a placeholder implementation.
        A production version would use proper web scraping.

        Args:
            base_url: Base URL for Anthropic docs
            max_pages: Maximum pages to crawl

        Returns:
            Crawl results
        """
        # This is a simplified implementation
        # In production, you would use:
        # - requests/httpx for HTTP requests
        # - BeautifulSoup for HTML parsing
        # - Sitemap parsing for structured crawling
        # - Rate limiting to respect robots.txt

        results = {
            "source_type": "anthropic_docs",
            "base_url": base_url,
            "pages_crawled": 0,
            "pages_ingested": 0,
            "total_chunks": 0,
            "status": "not_implemented",
            "message": (
                "Anthropic docs crawling requires additional dependencies. "
                "Install with: pip install beautifulsoup4 requests"
            )
        }

        try:
            import requests
            from bs4 import BeautifulSoup

            results["status"] = "ready"
            results["message"] = "Ready to crawl Anthropic documentation"

            # TODO: Implement actual crawling logic
            # 1. Fetch sitemap or main page
            # 2. Extract documentation links
            # 3. Crawl each page
            # 4. Extract content
            # 5. Ingest into knowledge base

        except ImportError:
            pass

        return results

    async def crawl_github_repo_docs(
        self,
        owner: str,
        repo: str,
        paths: Optional[List[str]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crawl documentation from a GitHub repository

        Args:
            owner: Repository owner
            repo: Repository name
            paths: Specific paths to crawl (e.g., ["docs/", "README.md"])
            token: GitHub access token (optional)

        Returns:
            Crawl results
        """
        if not paths:
            paths = ["docs/", "README.md", "CONTRIBUTING.md"]

        results = {
            "source_type": "github_repo",
            "repo": f"{owner}/{repo}",
            "paths": paths,
            "files_crawled": 0,
            "files_ingested": 0,
            "total_chunks": 0,
            "errors": []
        }

        try:
            from github import Github

            # Initialize GitHub client
            gh = Github(token) if token else Github()
            repository = gh.get_repo(f"{owner}/{repo}")

            # Process each path
            for path in paths:
                try:
                    # Check if path is a directory or file
                    contents = repository.get_contents(path)

                    if isinstance(contents, list):
                        # Directory - process all files
                        for content_file in contents:
                            if content_file.type == "file" and content_file.name.endswith((".md", ".txt")):
                                await self._ingest_github_file(
                                    repository,
                                    content_file,
                                    results
                                )
                    else:
                        # Single file
                        if contents.type == "file":
                            await self._ingest_github_file(
                                repository,
                                contents,
                                results
                            )

                except Exception as e:
                    results["errors"].append({
                        "path": path,
                        "error": str(e)
                    })

            results["status"] = "completed"
            return results

        except ImportError:
            return {
                "status": "error",
                "message": "PyGithub not installed. Install with: pip install PyGithub"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    async def _ingest_github_file(
        self,
        repo: Any,
        content_file: Any,
        results: Dict[str, Any]
    ):
        """
        Ingest a single file from GitHub repository

        Args:
            repo: GitHub repository object
            content_file: GitHub content file object
            results: Results dictionary to update
        """
        try:
            # Decode content
            content = content_file.decoded_content.decode("utf-8")

            # Prepare metadata
            metadata = {
                "source": f"github:{repo.full_name}/{content_file.path}",
                "category": "github_docs",
                "filename": content_file.name,
                "repo": repo.full_name,
                "path": content_file.path,
                "url": content_file.html_url,
                "sha": content_file.sha
            }

            # Ingest document
            chunks_added = await self.rag_service.add_document(
                content=content,
                metadata=metadata
            )

            results["files_crawled"] += 1
            results["files_ingested"] += 1
            results["total_chunks"] += chunks_added

        except Exception as e:
            results["errors"].append({
                "file": content_file.path,
                "error": str(e)
            })

    async def crawl_local_docs(
        self,
        directory: str,
        category: str = "local_docs",
        watch: bool = False
    ) -> Dict[str, Any]:
        """
        Crawl local documentation directory

        Args:
            directory: Path to documentation directory
            category: Category for documents
            watch: Enable file watching for auto-updates (not implemented)

        Returns:
            Crawl results
        """
        dir_path = Path(directory)

        if not dir_path.exists() or not dir_path.is_dir():
            return {
                "status": "error",
                "message": f"Invalid directory: {directory}"
            }

        results = {
            "source_type": "local",
            "directory": str(dir_path),
            "files_found": 0,
            "files_ingested": 0,
            "total_chunks": 0,
            "errors": []
        }

        # Find all documentation files
        doc_extensions = [".md", ".txt", ".rst"]
        files = []

        for ext in doc_extensions:
            files.extend(dir_path.rglob(f"*{ext}"))

        results["files_found"] = len(files)

        # Ingest each file
        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8")

                metadata = {
                    "source": f"local:{file_path}",
                    "category": category,
                    "filename": file_path.name,
                    "path": str(file_path),
                    "relative_path": str(file_path.relative_to(dir_path))
                }

                chunks_added = await self.rag_service.add_document(
                    content=content,
                    metadata=metadata
                )

                results["files_ingested"] += 1
                results["total_chunks"] += chunks_added

            except Exception as e:
                results["errors"].append({
                    "file": str(file_path),
                    "error": str(e)
                })

        results["status"] = "completed"

        if watch:
            results["watch_note"] = "File watching not yet implemented"

        return results

    async def add_source(
        self,
        source_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a new documentation source

        Args:
            source_type: Type of source (anthropic_docs, github_repo, local)
            config: Source configuration

        Returns:
            Result of adding source
        """
        source = {
            "type": source_type,
            **config,
            "added_at": datetime.now().isoformat(),
            "enabled": config.get("enabled", True)
        }

        self.sources_config["sources"].append(source)
        self._save_sources_config()

        return {
            "success": True,
            "source_type": source_type,
            "message": "Source added successfully"
        }

    async def update_all_sources(self) -> Dict[str, Any]:
        """
        Update documentation from all enabled sources

        Returns:
            Update results
        """
        results = {
            "total_sources": len(self.sources_config["sources"]),
            "updated": 0,
            "failed": 0,
            "sources": []
        }

        for source in self.sources_config["sources"]:
            if not source.get("enabled", True):
                continue

            try:
                if source["type"] == "anthropic_docs":
                    result = await self.crawl_anthropic_docs(
                        base_url=source.get("url", "https://docs.anthropic.com")
                    )
                elif source["type"] == "github_repo":
                    result = await self.crawl_github_repo_docs(
                        owner=source["owner"],
                        repo=source["repo"],
                        paths=source.get("paths"),
                        token=source.get("token")
                    )
                elif source["type"] == "local":
                    result = await self.crawl_local_docs(
                        directory=source["path"],
                        category=source.get("category", "local_docs")
                    )
                else:
                    result = {
                        "status": "error",
                        "message": f"Unknown source type: {source['type']}"
                    }

                results["sources"].append(result)

                if result.get("status") == "completed":
                    results["updated"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                results["failed"] += 1
                results["sources"].append({
                    "type": source["type"],
                    "status": "error",
                    "error": str(e)
                })

        # Update last_update timestamp
        self.sources_config["last_update"] = datetime.now().isoformat()
        self._save_sources_config()

        return results

    def get_sources(self) -> List[Dict[str, Any]]:
        """
        Get list of configured documentation sources

        Returns:
            List of sources
        """
        return self.sources_config.get("sources", [])

    async def remove_source(self, index: int) -> Dict[str, Any]:
        """
        Remove a documentation source by index

        Args:
            index: Index of source to remove

        Returns:
            Removal result
        """
        if 0 <= index < len(self.sources_config["sources"]):
            removed = self.sources_config["sources"].pop(index)
            self._save_sources_config()

            return {
                "success": True,
                "removed_source": removed
            }
        else:
            return {
                "success": False,
                "error": f"Invalid index: {index}"
            }
