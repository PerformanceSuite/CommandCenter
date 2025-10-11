#!/bin/bash
# CommandCenter - Claude Code Session Cleanup Script
# Auto-generated for Python (FastAPI) + TypeScript (React) project

set -e

echo "🧹 Starting CommandCenter cleanup..."

# Python cleanup
echo "  → Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# Node.js cleanup
if [ -f "frontend/package.json" ]; then
    echo "  → Cleaning Node.js cache files..."
    rm -rf frontend/node_modules/.cache 2>/dev/null || true
    rm -rf frontend/.npm 2>/dev/null || true
    rm -rf frontend/.vite 2>/dev/null || true
fi

# Common temporary files
echo "  → Removing common temporary files..."
find . -type f -name "*.tmp" -delete 2>/dev/null || true
find . -type f -name "*.log" -delete 2>/dev/null || true
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*.swo" -delete 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
find . -type f -name "Thumbs.db" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true

# Remove empty directories
echo "  → Removing empty directories..."
find . -type d -empty -delete 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "Session Summary:"
echo "  - Branch: $(git branch --show-current)"
echo "  - Commits this session: 2 (Phase 1 Research Workflow + memory.md update)"
echo "  - Files tracked: $(git ls-files | wc -l | tr -d ' ')"
echo ""
echo "👋 Session 10 cleanup finished. Safe to exit Claude Code!"
