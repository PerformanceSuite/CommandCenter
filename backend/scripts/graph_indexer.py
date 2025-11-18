"""
Graph Indexer CLI - Phase 7 Code Indexing Tool

Indexes repository code into the knowledge graph.
Supports Python, TypeScript/JavaScript with incremental updates.
"""

import asyncio
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings  # noqa: E402
from app.models.graph import (  # noqa: E402
    GraphDependency,
    GraphFile,
    GraphRepo,
    GraphSpecItem,
    GraphSymbol,
    SpecItemSource,
    SpecItemStatus,
)
from app.nats_client import NATSClient  # noqa: E402
from app.parsers.python_parser import PythonParser  # noqa: E402
from app.schemas.graph_events import GraphIndexedEvent  # noqa: E402

logger = logging.getLogger(__name__)

# Supported file extensions by language
LANGUAGE_EXTENSIONS = {
    "python": {".py"},
    "typescript": {".ts", ".tsx"},
    "javascript": {".js", ".jsx"},
}

# Directories to exclude from scanning
EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".env",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    "coverage",
}


class GraphIndexer:
    """Index repository code into knowledge graph"""

    def __init__(
        self,
        project_id: int,
        repo_path: str,
        repo_url: Optional[str] = None,
        languages: Optional[List[str]] = None,
    ):
        self.project_id = project_id
        self.repo_path = Path(repo_path).resolve()
        self.repo_url = repo_url or str(self.repo_path)
        self.languages = languages or ["python"]  # Default to Python only

        # Parse owner/name from URL or path
        self.owner, self.name = self._parse_repo_identifier(self.repo_url)

        # Statistics
        self.stats = {
            "files_scanned": 0,
            "files_processed": 0,
            "files_skipped": 0,
            "symbols_extracted": 0,
            "dependencies_extracted": 0,
            "todos_extracted": 0,
            "errors": 0,
        }

    def _parse_repo_identifier(self, url: str) -> Tuple[str, str]:
        """Parse owner/name from repository URL or path"""
        # Try to extract from GitHub URL format
        if "github.com/" in url:
            parts = url.split("github.com/")[1].split("/")
            if len(parts) >= 2:
                return parts[0], parts[1].replace(".git", "")

        # Fall back to directory name
        path = Path(url)
        name = path.name
        owner = path.parent.name if path.parent.name != path.root else "local"
        return owner, name

    def _should_process_file(self, file_path: Path) -> Optional[str]:
        """
        Check if file should be processed.

        Returns:
            Language name if should process, None otherwise
        """
        ext = file_path.suffix.lower()

        for lang, extensions in LANGUAGE_EXTENSIONS.items():
            if lang in self.languages and ext in extensions:
                return lang

        return None

    def _should_exclude_dir(self, dir_name: str) -> bool:
        """Check if directory should be excluded"""
        return dir_name in EXCLUDE_DIRS or dir_name.startswith(".")

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file contents"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _scan_directory(self) -> List[Tuple[Path, str]]:
        """
        Scan directory and collect files to process.

        Returns:
            List of (file_path, language) tuples
        """
        files_to_process = []

        for root, dirs, files in os.walk(self.repo_path):
            # Exclude certain directories
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d)]

            for file_name in files:
                file_path = Path(root) / file_name
                lang = self._should_process_file(file_path)

                if lang:
                    files_to_process.append((file_path, lang))
                    self.stats["files_scanned"] += 1

        return files_to_process

    async def index(self, incremental: bool = True) -> Dict:
        """
        Index repository into knowledge graph.

        Args:
            incremental: Only process changed files (default True)

        Returns:
            Statistics dictionary
        """
        # Create async engine
        engine = create_async_engine(settings.database_url)
        async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session_factory() as session:
            try:
                # Get or create repository
                repo = await self._get_or_create_repo(session)

                # Scan directory
                click.echo(f"Scanning {self.repo_path}...")
                files_to_process = self._scan_directory()
                click.echo(f"Found {len(files_to_process)} files to scan")

                # Process files
                for file_path, lang in files_to_process:
                    try:
                        # Get relative path from repo root
                        rel_path = str(file_path.relative_to(self.repo_path))

                        # Compute file hash
                        file_hash = self._compute_file_hash(file_path)

                        # Check if file needs reprocessing (incremental mode)
                        if incremental:
                            stmt = select(GraphFile).filter(
                                GraphFile.repo_id == repo.id, GraphFile.path == rel_path
                            )
                            result = await session.execute(stmt)
                            existing_file = result.scalar_one_or_none()

                            if existing_file and existing_file.hash == file_hash:
                                self.stats["files_skipped"] += 1
                                continue  # Skip unchanged file

                        # Parse file
                        await self._process_file(
                            session, repo, file_path, rel_path, file_hash, lang
                        )
                        self.stats["files_processed"] += 1

                    except Exception as e:
                        click.echo(f"Error processing {file_path}: {e}", err=True)
                        self.stats["errors"] += 1

                # Update repository metadata
                from datetime import datetime

                repo.last_indexed_at = datetime.utcnow()
                await session.commit()

                click.echo("\n✅ Indexing complete!")
                click.echo(f"  Files scanned: {self.stats['files_scanned']}")
                click.echo(f"  Files processed: {self.stats['files_processed']}")
                click.echo(f"  Files skipped: {self.stats['files_skipped']}")
                click.echo(f"  Symbols extracted: {self.stats['symbols_extracted']}")
                click.echo(f"  Dependencies: {self.stats['dependencies_extracted']}")
                click.echo(f"  TODOs extracted: {self.stats['todos_extracted']}")
                if self.stats["errors"] > 0:
                    click.echo(f"  ⚠️  Errors: {self.stats['errors']}", err=True)

                # Publish indexing completion event to NATS
                await self._publish_indexed_event(repo)

            finally:
                await engine.dispose()

        return self.stats

    async def _publish_indexed_event(self, repo: GraphRepo) -> None:
        """Publish graph.indexed event to NATS after indexing completes."""
        try:
            # Connect to NATS
            nats_client = NATSClient(settings.nats_url)
            await nats_client.connect()

            try:
                # Create event
                event = GraphIndexedEvent(
                    project_id=self.project_id,
                    repo_id=repo.id,
                    files_processed=self.stats["files_processed"],
                    symbols_extracted=self.stats["symbols_extracted"],
                    todos_extracted=self.stats["todos_extracted"],
                    incremental=self.stats["files_skipped"] > 0,
                )

                # Publish to project-specific subject
                subject = f"graph.indexed.{self.project_id}"
                await nats_client.publish(subject, event.model_dump(mode="json"))
                click.echo(f"  📡 Published indexing event to NATS: {subject}")
            finally:
                await nats_client.disconnect()

        except Exception as e:
            # Don't fail indexing if NATS publishing fails
            click.echo(f"  ⚠️  Failed to publish to NATS: {e}", err=True)

    async def _get_or_create_repo(self, session: AsyncSession) -> GraphRepo:
        """Get existing repository or create new one"""
        stmt = select(GraphRepo).filter(
            GraphRepo.project_id == self.project_id,
            GraphRepo.full_name == f"{self.owner}/{self.name}",
        )
        result = await session.execute(stmt)
        repo = result.scalar_one_or_none()

        if not repo:
            repo = GraphRepo(
                project_id=self.project_id,
                provider="github",
                owner=self.owner,
                name=self.name,
                full_name=f"{self.owner}/{self.name}",
                default_branch="main",
                root_path=str(self.repo_path),
            )
            session.add(repo)
            await session.flush()
            click.echo(f"Created repository: {repo.full_name}")
        else:
            click.echo(f"Using existing repository: {repo.full_name}")

        return repo

    async def _process_file(
        self,
        session: AsyncSession,
        repo: GraphRepo,
        file_path: Path,
        rel_path: str,
        file_hash: str,
        lang: str,
    ):
        """Process a single file"""
        # Read file contents
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        # Create or update GraphFile
        stmt = select(GraphFile).filter(GraphFile.repo_id == repo.id, GraphFile.path == rel_path)
        result = await session.execute(stmt)
        graph_file = result.scalar_one_or_none()

        if not graph_file:
            graph_file = GraphFile(
                repo_id=repo.id,
                path=rel_path,
                lang=lang,
                hash=file_hash,
                size=len(source),
                lines=source.count("\n") + 1,
            )
            session.add(graph_file)
        else:
            # Update existing file
            graph_file.hash = file_hash
            graph_file.size = len(source)
            graph_file.lines = source.count("\n") + 1

        await session.flush()

        # Delete old symbols for this file (will be recreated)
        stmt = select(GraphSymbol).filter(GraphSymbol.file_id == graph_file.id)
        result = await session.execute(stmt)
        old_symbols = result.scalars().all()
        for symbol in old_symbols:
            await session.delete(symbol)

        # Parse based on language
        if lang == "python":
            await self._parse_python(session, graph_file, source, rel_path)
        # elif lang in ["typescript", "javascript"]:
        #     await self._parse_typescript(session, graph_file, source, rel_path)

        await session.flush()

    async def _parse_python(
        self, session: AsyncSession, graph_file: GraphFile, source: str, rel_path: str
    ):
        """Parse Python file using AST"""
        parser = PythonParser()
        symbols, dependencies = parser.parse(source, rel_path)
        todos = parser.get_todos()

        # Symbol ID mapping (name -> id)
        symbol_map: Dict[str, int] = {}

        # Create GraphSymbol entities
        for parsed_symbol in symbols:
            graph_symbol = GraphSymbol(
                file_id=graph_file.id,
                kind=parsed_symbol.kind,
                name=parsed_symbol.name,
                qualified_name=parsed_symbol.qualified_name,
                signature=parsed_symbol.signature,
                range_start=parsed_symbol.range_start,
                range_end=parsed_symbol.range_end,
                exports=parsed_symbol.exports,
                is_async=parsed_symbol.is_async,
                is_generator=parsed_symbol.is_generator,
                metadata_={"docstring": parsed_symbol.docstring}
                if parsed_symbol.docstring
                else None,
            )
            session.add(graph_symbol)
            await session.flush()

            # Map qualified name to ID for dependency resolution
            symbol_map[parsed_symbol.qualified_name] = graph_symbol.id
            self.stats["symbols_extracted"] += 1

        # Create GraphDependency entities
        for parsed_dep in dependencies:
            # Only create dependency if both symbols exist in this file
            from_id = symbol_map.get(parsed_dep.from_symbol)
            to_id = symbol_map.get(parsed_dep.to_symbol)

            if from_id and to_id:
                graph_dep = GraphDependency(
                    from_symbol_id=from_id,
                    to_symbol_id=to_id,
                    type=parsed_dep.type,
                    weight=1.0,
                )
                session.add(graph_dep)
                self.stats["dependencies_extracted"] += 1

        # Create GraphSpecItem entities from TODOs
        for todo in todos:
            spec_item = GraphSpecItem(
                project_id=self.project_id,
                source=SpecItemSource.FILE,
                ref=f"{rel_path}:{todo.line_number}",
                title=f"{todo.kind}: {todo.title}",
                description=todo.description,
                priority=5 if todo.kind == "FIXME" else 3,  # FIXME = higher priority
                status=SpecItemStatus.PLANNED,
            )
            session.add(spec_item)
            self.stats["todos_extracted"] += 1


# CLI Commands


@click.group()
def cli():
    """Graph Indexer CLI - Index repository code into knowledge graph"""
    pass


@cli.command()
@click.option("--project-id", required=True, type=int, help="Project ID")
@click.option("--repo-path", required=True, type=click.Path(exists=True), help="Repository path")
@click.option("--repo-url", help="Repository URL (e.g., github.com/owner/repo)")
@click.option(
    "--languages",
    default="python",
    help="Comma-separated languages to index (default: python)",
)
@click.option(
    "--incremental/--full",
    default=True,
    help="Incremental index (skip unchanged files) or full reindex",
)
def index(
    project_id: int, repo_path: str, repo_url: Optional[str], languages: str, incremental: bool
):
    """Index repository code into knowledge graph"""
    langs = [lang.strip() for lang in languages.split(",")]

    indexer = GraphIndexer(
        project_id=project_id,
        repo_path=repo_path,
        repo_url=repo_url,
        languages=langs,
    )

    asyncio.run(indexer.index(incremental=incremental))


@cli.command()
@click.option("--project-id", required=True, type=int, help="Project ID")
def stats(project_id: int):
    """Show indexing statistics for a project"""
    click.echo(f"Statistics for project {project_id}")
    click.echo("(Not yet implemented)")


if __name__ == "__main__":
    cli()
