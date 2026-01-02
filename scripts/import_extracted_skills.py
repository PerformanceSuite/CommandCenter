#!/usr/bin/env python3
"""Import extracted skills from JSON batch files into CommandCenter Skills API."""
import json
import httpx
import asyncio
from pathlib import Path


API_BASE = "http://localhost:8000/api/v1"
EXTRACTED_DIR = Path(__file__).parent.parent / "docs" / "extracted"


def slugify(text: str) -> str:
    """Convert text to valid slug."""
    return text.lower().replace(" ", "-").replace("_", "-")


async def import_skills():
    """Import all extracted skills."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check API health
        try:
            health = await client.get(f"{API_BASE}/health")
            if health.status_code != 200:
                print(f"API not healthy: {health.status_code}")
                return
        except Exception as e:
            print(f"Cannot connect to API: {e}")
            print("Make sure backend is running: docker compose up -d")
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
                slug = skill.get("id", slugify(skill.get("name", "")))
                name = skill.get("name", slug)
                skill_type = skill.get("type", "pattern")
                domain = skill.get("domain", "general")
                description = skill.get("description", "")
                source = skill.get("source", "")

                # Build content from skill data
                content_parts = [f"# {name}\n"]
                content_parts.append(f"**Type:** {skill_type}\n")
                content_parts.append(f"**Domain:** {domain}\n")
                content_parts.append(f"**Source:** {source}\n\n")
                content_parts.append(f"## Description\n{description}\n")

                # Add any additional structured data
                for key in ["components", "flow", "phases", "endpoints", "models", "principles"]:
                    if key in skill:
                        content_parts.append(f"\n## {key.title()}\n```json\n{json.dumps(skill[key], indent=2)}\n```\n")

                content = "".join(content_parts)

                # Create skill via API
                payload = {
                    "slug": slug,
                    "name": name,
                    "description": description[:500] if description else None,
                    "content": content,
                    "category": skill_type,
                    "tags": [domain, skill_type],
                    "version": "1.0.0",
                    "author": "doc-intelligence",
                    "is_public": True
                }

                try:
                    response = await client.post(f"{API_BASE}/skills", json=payload)
                    if response.status_code == 201:
                        print(f"  ✓ {slug}")
                        imported += 1
                    elif response.status_code == 409:
                        print(f"  - {slug} (exists)")
                        skipped += 1
                    else:
                        print(f"  ✗ {slug}: {response.status_code} {response.text[:100]}")
                        failed += 1
                except Exception as e:
                    print(f"  ✗ {slug}: {e}")
                    failed += 1

        print(f"\n{'='*50}")
        print(f"Imported: {imported}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    asyncio.run(import_skills())
