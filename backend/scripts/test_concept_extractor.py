#!/usr/bin/env python3
"""
Test script for the doc-concept-extractor persona.

Usage:
    python scripts/test_concept_extractor.py [document_path]
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.agent_framework.persona_store import PersonaStore  # noqa: E402


def get_anthropic_client():
    """Get Anthropic client, checking for API key."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Try loading from .env
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found. Set it in environment or .env file.")

    import anthropic

    return anthropic.Anthropic(api_key=api_key)


async def test_concept_extractor(document_path: str) -> dict:
    """Run the concept extractor on a document."""

    # Load persona
    store = PersonaStore()
    persona = store.get("doc-concept-extractor")

    # Read document
    doc_path = Path(document_path)
    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    document_content = doc_path.read_text()

    # Build prompt
    user_message = f"""Analyze the following document and extract all concepts.

## Document Path
{document_path}

## Document Content

{document_content}

---

Extract all concepts following your output schema. Return only valid JSON."""

    # Call Claude API
    client = get_anthropic_client()

    print(f"📄 Analyzing: {document_path}")
    print(f"📏 Document length: {len(document_content)} chars")
    print(f"🤖 Using persona: {persona.display_name}")
    print("-" * 50)

    response = client.messages.create(
        model=persona.model,
        max_tokens=persona.max_tokens,
        temperature=persona.temperature,
        system=persona.system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    # Extract response text
    result_text = response.content[0].text

    # Try to parse as JSON
    try:
        # Find JSON in response (might have markdown code blocks)
        if "```json" in result_text:
            json_start = result_text.find("```json") + 7
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()
        elif "```" in result_text:
            json_start = result_text.find("```") + 3
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()

        result = json.loads(result_text)
        return result
    except json.JSONDecodeError as e:
        print(f"⚠️  Could not parse JSON: {e}")
        print("Raw response:")
        print(result_text)
        return {"error": str(e), "raw": result_text}


def main():
    # Default test document
    default_doc = "docs/archive/legacy-2026-01-02/concepts-old/TheLoop.md"
    doc_path = sys.argv[1] if len(sys.argv) > 1 else default_doc

    # Make path absolute if needed
    if not Path(doc_path).is_absolute():
        doc_path = str(Path(__file__).parent.parent.parent / doc_path)

    result = asyncio.run(test_concept_extractor(doc_path))

    print("\n" + "=" * 50)
    print("📊 EXTRACTION RESULTS")
    print("=" * 50 + "\n")

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return 1

    # Display results
    concepts = result.get("concepts", [])
    meta = result.get("meta", {})

    print(f"Found {len(concepts)} concepts:\n")

    for i, concept in enumerate(concepts, 1):
        print(f"{i}. {concept['name']} ({concept['type']})")
        print(f"   Status: {concept['status']} | Domain: {concept['domain']}")
        print(f"   Definition: {concept['definition'][:100]}...")
        if concept.get("related_entities"):
            print(f"   Related: {', '.join(concept['related_entities'][:5])}")
        print()

    print("-" * 50)
    print(f"📝 Extraction notes: {meta.get('extraction_notes', 'N/A')}")

    # Save full result
    output_path = Path(__file__).parent / "concept_extraction_result.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 Full results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
