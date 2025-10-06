#!/bin/bash
# Claude Code Session Cleanup Script
# Auto-generated for CommandCenter project

set -e

echo "🧹 Starting CommandCenter session cleanup..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Remove common temporary files
echo "Removing temporary files..."
find . -type f -name "*.tmp" -delete 2>/dev/null || true
find . -type f -name "*.log" -delete 2>/dev/null || true
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*.swo" -delete 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
find . -type f -name "Thumbs.db" -delete 2>/dev/null || true

# Clean Python cache files
echo "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# Clean Node.js cache (if applicable)
if [ -f "frontend/package.json" ]; then
    echo "Cleaning Node.js cache..."
    rm -rf frontend/node_modules/.cache 2>/dev/null || true
    rm -rf frontend/.vite 2>/dev/null || true
    rm -rf frontend/dist 2>/dev/null || true
fi

# Clean test coverage reports
echo "Cleaning test coverage files..."
rm -rf backend/htmlcov 2>/dev/null || true
rm -rf backend/.coverage 2>/dev/null || true
rm -rf frontend/coverage 2>/dev/null || true

# Clean build artifacts
echo "Cleaning build artifacts..."
rm -rf backend/build 2>/dev/null || true
rm -rf backend/dist 2>/dev/null || true

# Remove empty directories
echo "Removing empty directories..."
find . -type d -empty -delete 2>/dev/null || true

# Update timestamp in memory.md
if [ -f ".claude/memory.md" ]; then
    echo "Updating memory.md timestamp..."
    sed -i.bak "s/Last Updated: .*/Last Updated: $(date +%Y-%m-%d)/" .claude/memory.md
    rm -f .claude/memory.md.bak
fi

# Clean up coordination files (optional - keep for historical record)
# Uncomment if you want to clean these after session
# rm -rf .agent-coordination/status.json.bak 2>/dev/null || true
# rm -rf .agent-coordination/merge-queue.json.bak 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "Summary:"
echo "  - Removed temporary files (.tmp, .log, .swp, .DS_Store)"
echo "  - Cleaned Python cache (__pycache__, *.pyc)"
echo "  - Cleaned Node.js cache (.vite, node_modules/.cache)"
echo "  - Cleaned test coverage reports"
echo "  - Removed empty directories"
echo "  - Updated memory.md timestamp"
echo ""
echo "Session cleanup finished successfully."
