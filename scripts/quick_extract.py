#!/usr/bin/env python3
"""Quick extraction test - processes 5 docs."""
import anthropic
import os
import json
import yaml
from pathlib import Path
from datetime import datetime

# Get API key
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    with open(Path.home() / ".config/api-keys/.env.api-keys") as f:
        for line in f:
            if "ANTHROPIC_API_KEY" in line:
                api_key = line.split("=", 1)[1].strip().strip('"\'').replace("export ", "")
                break

client = anthropic.Anthropic(api_key=api_key)

PROMPT = """Extract from this document:
1. Concepts (products, modules, features)
2. Requirements (must/should/could statements)

Return ONLY valid JSON (no markdown):
{
  "concepts": [{"name": "...", "type": "product|module|feature|capability", "definition": "...", "status": "proposed|implemented|unknown"}],
  "requirements": [{"id": "REQ-001", "text": "System must...", "priority": "high|medium|low"}]
}

Document:
"""

docs_dir = Path.home() / "Projects/CommandCenter/docs"
results = {"extracted_at": datetime.now().isoformat(), "documents": []}

# Process 5 small docs
targets = [
    "CHECKLIST.md",
    "KNOWN_ISSUES.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "CAPABILITIES.md"
]

for fname in targets:
    fpath = docs_dir / fname
    if not fpath.exists():
        print(f"SKIP: {fname} not found")
        continue

    with open(fpath) as f:
        content = f.read()[:8000]

    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": PROMPT + content}]
        )
        text = r.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        results["documents"].append({"file": fname, **data})
        print(f"OK: {fname} - {len(data.get('concepts',[]))} concepts, {len(data.get('requirements',[]))} reqs")
    except Exception as e:
        print(f"ERR: {fname} - {e}")
        results["documents"].append({"file": fname, "error": str(e)})

# Save results
out_path = docs_dir / "cleanup/batch-extraction-test.yaml"
with open(out_path, "w") as f:
    yaml.dump(results, f, default_flow_style=False, allow_unicode=True)

print(f"\nSaved to {out_path}")
print(f"Total: {sum(len(d.get('concepts', [])) for d in results['documents'])} concepts")
