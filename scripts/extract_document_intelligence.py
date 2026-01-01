#!/usr/bin/env python3
"""
Document Intelligence Batch Extraction Script

Processes all markdown documents using LLM-powered agent personas to extract:
- Concepts (products, modules, features)
- Requirements (must/should/could statements)
- Relationships (integrations, dependencies)
- Staleness indicators
- Classifications

Usage:
    python scripts/extract_document_intelligence.py --input docs/ --output docs/cleanup/
    python scripts/extract_document_intelligence.py --input docs/plans/ --limit 10
    python scripts/extract_document_intelligence.py --resume  # Continue from last run

Requirements:
    pip install anthropic pyyaml tqdm

Environment:
    ANTHROPIC_API_KEY=sk-ant-...
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

try:
    import anthropic
except ImportError:
    print("ERROR: Please install anthropic: pip install anthropic")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm not installed
    def tqdm(iterable, **kwargs):
        return iterable


# =============================================================================
# AGENT PERSONAS
# =============================================================================

CONCEPT_EXTRACTOR_PROMPT = """You are a Concept Extraction specialist. Read this document and identify all named concepts - products, platforms, features, processes, or ideas that have a distinct identity.

For each concept:
1. NAME: The specific term used
2. TYPE: product | feature | module | process | technology | framework | capability | integration
3. DEFINITION: How the document describes it (1-2 sentences)
4. STATUS: proposed | active | implemented | deprecated | unknown
5. DOMAIN: Business domain (compliance, marketing, finance, development, etc.)
6. RELATED_ENTITIES: Other concepts it connects to

Focus on concepts that have proper names and are described with some detail.

Output as JSON:
{
  "concepts": [
    {
      "name": "...",
      "type": "...",
      "definition": "...",
      "status": "...",
      "domain": "...",
      "related_entities": ["..."]
    }
  ]
}

Only output valid JSON, no other text."""

REQUIREMENT_MINER_PROMPT = """You are a Requirements Mining specialist. Read this document and extract all requirements - explicit or implicit statements about what a system MUST, SHOULD, or COULD do.

Look for:
- Explicit requirements ("must...", "should be able to...")
- Implicit requirements (described capabilities, success criteria)
- Constraints ("must comply with...", "cannot exceed...")
- Dependencies ("requires...", "depends on...")

For each requirement:
1. ID: Generate as REQ-XXX (where XXX is sequential)
2. TEXT: Normalized to "System must..." form
3. TYPE: functional | non-functional | constraint | dependency
4. PRIORITY: critical | high | medium | low | unknown
5. SOURCE_CONCEPT: Which concept this relates to
6. STATUS: proposed | implemented | unknown

Output as JSON:
{
  "requirements": [
    {
      "id": "REQ-001",
      "text": "...",
      "type": "...",
      "priority": "...",
      "source_concept": "...",
      "status": "..."
    }
  ]
}

Only output valid JSON, no other text."""

CLASSIFIER_PROMPT = """You are a Document Classification specialist. Analyze this document and determine:

1. TYPE: plan | concept | guide | reference | report | session | archive
2. SUBTYPE: More specific (e.g., "strategic-roadmap", "feature-spec", "developer-guide")
3. STATUS: active | completed | superseded | abandoned | stale
4. VALUE: high | medium | low | none
5. ACTION: keep | update | archive | merge | delete
6. STALENESS_SCORE: 0-100 (0=current, 100=completely outdated)
7. KEY_TOPICS: List of 3-5 main topics

Output as JSON:
{
  "classification": {
    "type": "...",
    "subtype": "...",
    "status": "...",
    "value": "...",
    "action": "...",
    "staleness_score": 0,
    "key_topics": ["...", "..."]
  }
}

Only output valid JSON, no other text."""


# =============================================================================
# EXTRACTION ENGINE
# =============================================================================

class DocumentIntelligenceExtractor:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.results = {
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "model": model,
                "documents_processed": 0,
                "documents_failed": 0
            },
            "documents": [],
            "all_concepts": [],
            "all_requirements": []
        }
        self.processed_files = set()

    def load_progress(self, progress_file: Path) -> None:
        """Load previous progress to resume extraction."""
        if progress_file.exists():
            with open(progress_file) as f:
                data = yaml.safe_load(f)
                if data:
                    self.results = data
                    self.processed_files = {d["path"] for d in data.get("documents", [])}
                    print(f"Resumed from {len(self.processed_files)} previously processed documents")

    def save_progress(self, output_file: Path) -> None:
        """Save current progress."""
        with open(output_file, 'w') as f:
            yaml.dump(self.results, f, default_flow_style=False, allow_unicode=True, width=120)

    def call_llm(self, system_prompt: str, document_content: str) -> Optional[dict]:
        """Call Claude API with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Truncate very long documents
                if len(document_content) > 50000:
                    document_content = document_content[:25000] + "\n\n[... truncated ...]\n\n" + document_content[-25000:]

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[
                        {"role": "user", "content": f"Document to analyze:\n\n{document_content}"}
                    ],
                    system=system_prompt
                )

                # Parse JSON response
                text = response.content[0].text.strip()
                # Handle markdown code blocks
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]

                return json.loads(text)

            except json.JSONDecodeError as e:
                print(f"  JSON parse error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
            except anthropic.RateLimitError:
                wait_time = 60 * (attempt + 1)
                print(f"  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            except Exception as e:
                print(f"  API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)

        return None

    def extract_from_document(self, file_path: Path) -> dict:
        """Run all agent personas on a single document."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        result = {
            "path": str(file_path),
            "filename": file_path.name,
            "size_bytes": len(content),
            "extracted_at": datetime.now().isoformat(),
            "concepts": [],
            "requirements": [],
            "classification": None
        }

        # Skip very small files
        if len(content) < 100:
            result["skipped"] = "Too short"
            return result

        # Extract concepts
        concepts_result = self.call_llm(CONCEPT_EXTRACTOR_PROMPT, content)
        if concepts_result and "concepts" in concepts_result:
            result["concepts"] = concepts_result["concepts"]
            for c in result["concepts"]:
                c["source_doc"] = str(file_path)

        # Small delay to avoid rate limits
        time.sleep(0.5)

        # Extract requirements
        req_result = self.call_llm(REQUIREMENT_MINER_PROMPT, content)
        if req_result and "requirements" in req_result:
            result["requirements"] = req_result["requirements"]
            for r in result["requirements"]:
                r["source_doc"] = str(file_path)

        time.sleep(0.5)

        # Classify document
        class_result = self.call_llm(CLASSIFIER_PROMPT, content)
        if class_result and "classification" in class_result:
            result["classification"] = class_result["classification"]

        return result

    def process_directory(self, input_dir: Path, limit: Optional[int] = None) -> None:
        """Process all markdown files in directory."""
        # Find all markdown files
        md_files = list(input_dir.rglob("*.md"))

        # Filter out already processed
        md_files = [f for f in md_files if str(f) not in self.processed_files]

        # Skip archive and cleanup directories (already processed or not needed)
        md_files = [f for f in md_files if "/archive/" not in str(f)]

        if limit:
            md_files = md_files[:limit]

        print(f"Processing {len(md_files)} documents...")

        for file_path in tqdm(md_files, desc="Extracting"):
            try:
                print(f"\n  Processing: {file_path.name}")
                result = self.extract_from_document(file_path)

                self.results["documents"].append(result)
                self.results["all_concepts"].extend(result.get("concepts", []))
                self.results["all_requirements"].extend(result.get("requirements", []))
                self.results["metadata"]["documents_processed"] += 1

                print(f"    Found: {len(result.get('concepts', []))} concepts, {len(result.get('requirements', []))} requirements")

            except Exception as e:
                print(f"    ERROR: {e}")
                self.results["metadata"]["documents_failed"] += 1
                self.results["documents"].append({
                    "path": str(file_path),
                    "error": str(e)
                })

    def generate_summary(self) -> dict:
        """Generate summary statistics."""
        concepts = self.results["all_concepts"]
        requirements = self.results["all_requirements"]

        # Count by type
        concept_types = {}
        for c in concepts:
            t = c.get("type", "unknown")
            concept_types[t] = concept_types.get(t, 0) + 1

        req_priorities = {}
        for r in requirements:
            p = r.get("priority", "unknown")
            req_priorities[p] = req_priorities.get(p, 0) + 1

        # Find unique concept names
        unique_concepts = list(set(c.get("name", "") for c in concepts if c.get("name")))

        return {
            "total_documents": self.results["metadata"]["documents_processed"],
            "failed_documents": self.results["metadata"]["documents_failed"],
            "total_concepts": len(concepts),
            "unique_concepts": len(unique_concepts),
            "concept_types": concept_types,
            "total_requirements": len(requirements),
            "requirement_priorities": req_priorities,
            "top_concepts": unique_concepts[:20]
        }


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Extract document intelligence using LLM agents")
    parser.add_argument("--input", "-i", type=Path, default=Path("docs"),
                        help="Input directory containing markdown files")
    parser.add_argument("--output", "-o", type=Path, default=Path("docs/cleanup"),
                        help="Output directory for results")
    parser.add_argument("--limit", "-l", type=int, default=None,
                        help="Limit number of documents to process")
    parser.add_argument("--resume", "-r", action="store_true",
                        help="Resume from previous run")
    parser.add_argument("--model", "-m", type=str, default="claude-sonnet-4-20250514",
                        help="Claude model to use")
    args = parser.parse_args()

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Try loading from common locations
        key_files = [
            Path.home() / ".config/api-keys/.env.api-keys",
            Path.home() / ".anthropic/api_key",
            Path(".env")
        ]
        for kf in key_files:
            if kf.exists():
                with open(kf) as f:
                    for line in f:
                        if "ANTHROPIC_API_KEY" in line:
                            api_key = line.split("=", 1)[1].strip().strip('"\'')
                            break
                if api_key:
                    break

    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found")
        print("Set it via environment variable or in ~/.config/api-keys/.env.api-keys")
        sys.exit(1)

    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)

    output_file = args.output / "extraction-results.yaml"
    summary_file = args.output / "extraction-summary.yaml"

    # Initialize extractor
    extractor = DocumentIntelligenceExtractor(api_key, model=args.model)

    # Resume if requested
    if args.resume:
        extractor.load_progress(output_file)

    # Process documents
    try:
        extractor.process_directory(args.input, limit=args.limit)
    except KeyboardInterrupt:
        print("\n\nInterrupted! Saving progress...")
    finally:
        # Always save progress
        extractor.save_progress(output_file)

        # Generate and save summary
        summary = extractor.generate_summary()
        with open(summary_file, 'w') as f:
            yaml.dump(summary, f, default_flow_style=False)

        print(f"\n{'='*60}")
        print("EXTRACTION COMPLETE")
        print(f"{'='*60}")
        print(f"Documents processed: {summary['total_documents']}")
        print(f"Documents failed: {summary['failed_documents']}")
        print(f"Total concepts: {summary['total_concepts']} ({summary['unique_concepts']} unique)")
        print(f"Total requirements: {summary['total_requirements']}")
        print(f"\nResults saved to: {output_file}")
        print(f"Summary saved to: {summary_file}")


if __name__ == "__main__":
    main()
