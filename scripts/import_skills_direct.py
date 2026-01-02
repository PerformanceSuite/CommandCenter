#!/usr/bin/env python3
"""Direct database import of extracted skills - bypasses API auth."""
import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

EXTRACTED_DIR = Path(__file__).parent.parent / "docs" / "extracted"
DATABASE_URL = "postgresql+asyncpg://commandcenter:commandcenter@localhost:5432/commandcenter"


async def import_skills():
    """Import all extracted skills directly to database."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check connection
        try:
            await session.execute(text("SELECT 1"))
            print("Database connected")
        except Exception as e:
            print(f"Cannot connect to database: {e}")
            return

        # Load all batch files
        batch_files = sorted(EXTRACTED_DIR.glob("skills-2026-01-02-batch*.json"))
        print(f"Found {len(batch_files)} batch files")

        imported = 0
        skipped = 0
        failed = 0

        for batch_file in batch_files:
            print(f"\nProcessing {batch_file.name}...")
            with open(batch_file) as f:
                data = json.load(f)

            skills = data.get("skills", [])
            for skill in skills:
                slug = skill.get("id", skill.get("name", "").lower().replace(" ", "-"))
                name = skill.get("name", slug)
                skill_type = skill.get("type", "pattern")
                domain = skill.get("domain", "general")
                description = skill.get("description", "")[:500] if skill.get("description") else None
                source = skill.get("source", "")

                # Build content from skill data
                content_parts = [f"# {name}\n"]
                content_parts.append(f"**Type:** {skill_type}\n")
                content_parts.append(f"**Domain:** {domain}\n")
                content_parts.append(f"**Source:** {source}\n\n")
                content_parts.append(f"## Description\n{skill.get('description', '')}\n")

                for key in ["components", "flow", "phases", "endpoints", "models", "principles"]:
                    if key in skill:
                        content_parts.append(f"\n## {key.title()}\n```json\n{json.dumps(skill[key], indent=2)}\n```\n")

                content = "".join(content_parts)
                tags = json.dumps([domain, skill_type])
                now = datetime.utcnow()

                try:
                    # Check if exists
                    result = await session.execute(
                        text("SELECT id FROM skills WHERE slug = :slug"),
                        {"slug": slug}
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        print(f"  - {slug} (exists)")
                        skipped += 1
                        continue

                    # Insert new skill
                    await session.execute(
                        text("""
                            INSERT INTO skills (slug, name, description, content, category, tags, version, author, is_public, usage_count, success_count, failure_count, effectiveness_score, created_at, updated_at)
                            VALUES (:slug, :name, :description, :content, :category, :tags, :version, :author, :is_public, 0, 0, 0, 0.0, :created_at, :updated_at)
                        """),
                        {
                            "slug": slug,
                            "name": name,
                            "description": description,
                            "content": content,
                            "category": skill_type,
                            "tags": tags,
                            "version": "1.0.0",
                            "author": "doc-intelligence",
                            "is_public": True,
                            "created_at": now,
                            "updated_at": now
                        }
                    )
                    await session.commit()
                    print(f"  ✓ {slug}")
                    imported += 1

                except Exception as e:
                    print(f"  ✗ {slug}: {e}")
                    failed += 1
                    await session.rollback()

        print(f"\n{'='*50}")
        print(f"Imported: {imported}, Skipped: {skipped}, Failed: {failed}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(import_skills())
