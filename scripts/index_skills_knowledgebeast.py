#!/usr/bin/env python3
"""
Index skills into KnowledgeBeast for semantic search.

Skills are indexed into a global collection (project_id=0) so they're
available across all projects.

Usage:
    docker compose exec backend python scripts/index_skills_knowledgebeast.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def index_skills():
    """Index all skills from database into KnowledgeBeast."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text

    try:
        from app.services.knowledgebeast_service import KnowledgeBeastService, KNOWLEDGEBEAST_AVAILABLE
    except ImportError:
        logger.error("KnowledgeBeast not available. Install with: pip install knowledgebeast>=2.3.2")
        return

    if not KNOWLEDGEBEAST_AVAILABLE:
        logger.error("KnowledgeBeast module not installed")
        return

    # Connect to database
    DATABASE_URL = "postgresql+asyncpg://commandcenter:commandcenter@localhost:5432/commandcenter"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Initialize KnowledgeBeast with project_id=0 for global skills
    try:
        kb_service = KnowledgeBeastService(project_id=0)
        logger.info("KnowledgeBeast service initialized (project_id=0 for global skills)")
    except Exception as e:
        logger.error(f"Failed to initialize KnowledgeBeast: {e}")
        return

    async with async_session() as session:
        # Fetch all skills
        result = await session.execute(
            text("SELECT id, slug, name, category, description, content FROM skills")
        )
        skills = result.fetchall()
        logger.info(f"Found {len(skills)} skills to index")

        indexed = 0
        failed = 0

        for skill in skills:
            skill_id, slug, name, category, description, content = skill

            # Build searchable content
            full_content = f"""# {name}

Category: {category}

## Description
{description or 'No description'}

## Content
{content or 'No content'}
"""

            metadata = {
                "title": name,
                "source": f"skill:{slug}",
                "category": f"skill-{category}",
                "skill_id": skill_id,
                "slug": slug,
                "type": "skill",
            }

            try:
                chunks = await kb_service.add_document(
                    content=full_content,
                    metadata=metadata,
                    chunk_size=1500  # Skills are smaller, use larger chunks
                )
                logger.info(f"  ✓ {slug} ({chunks} chunks)")
                indexed += 1
            except Exception as e:
                logger.error(f"  ✗ {slug}: {e}")
                failed += 1

        # Get final stats
        stats = await kb_service.get_statistics()

        print(f"\n{'='*50}")
        print(f"Indexed: {indexed}, Failed: {failed}")
        print(f"Total chunks in KnowledgeBeast: {stats.get('total_chunks', 'unknown')}")
        print(f"Collection: {stats.get('collection_name', 'unknown')}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(index_skills())
