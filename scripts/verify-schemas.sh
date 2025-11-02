#!/usr/bin/env bash
# CommandCenter Schema Validation Harness
set -euo pipefail

SCHEMA_DIR="schemas"
FIXTURE_DIR="fixtures"

echo "🔍 Validating CommandCenter JSON fixtures..."
echo

if ! command -v npx >/dev/null; then
  echo "❌ npx not found. Please install Node.js ≥18." >&2
  exit 1
fi

npx ajv validate \
  -s "$SCHEMA_DIR/event.schema.json" \
  -d "$FIXTURE_DIR"/*.json \
  --strict=false \
  --errors=text

echo
echo "✅ All fixture files validated successfully."
echo
