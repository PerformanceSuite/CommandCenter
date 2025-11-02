#!/usr/bin/env bash
set -euo pipefail
DEST="/Users/danielconnolly/Projects/CommandCenter/docs"
TARGET_DIR="$DEST/mrktzr-integration"
DOC_INDEX="$DEST/README.md"

echo "📘 Registering integration in docs index..."
mkdir -p "$DEST"
if ! grep -q "MRKTZR Integration" "$DOC_INDEX" 2>/dev/null; then
  echo "- [MRKTZR Integration](./mrktzr-integration/README.md)" >> "$DOC_INDEX"
  echo "✅ Added link to $DOC_INDEX"
else
  echo "ℹ️ Integration already listed in $DOC_INDEX"
fi

echo "🧩 Done. Location: $TARGET_DIR"
