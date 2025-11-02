#!/usr/bin/env bash
set -e
HUB_PKG="hub/package.json"

echo "🔧 Adding project CLI commands to $HUB_PKG ..."

# use jq if available; fallback to sed
if command -v jq >/dev/null 2>&1; then
  tmp=$(mktemp)
  jq '.scripts["projects"]="tsx src/cli.ts projects" | .scripts["projects:refresh"]="tsx src/cli.ts projects:refresh"' "$HUB_PKG" > "$tmp"
  mv "$tmp" "$HUB_PKG"
else
  # crude fallback: insert manually before the closing brace of scripts
  sed -i '' '/"events":/a\
  \  "projects": "tsx src/cli.ts projects",\
  \  "projects:refresh": "tsx src/cli.ts projects:refresh",' "$HUB_PKG"
fi

echo "✅ Done. New commands registered:"
echo ""
echo "  pnpm hub:projects:refresh"
echo "  pnpm hub:projects"
echo ""
echo "Test them now:"
echo "  pnpm hub:projects:refresh && pnpm hub:projects"

