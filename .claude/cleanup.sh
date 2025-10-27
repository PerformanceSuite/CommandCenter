#!/bin/bash
# Universal Auto-Cleanup - Runs automatically on session end
# No prompts, no interaction, just clean

set -e

# Silent mode - no output unless errors
SILENT=true

log() {
    if [ "$SILENT" != "true" ]; then
        echo "$1"
    fi
}

# 1. Remove temporary files
log "Cleaning temporary files..."
find . -type f \( \
    -name "*.tmp" \
    -o -name "*.log" \
    -o -name ".DS_Store" \
    -o -name "*.pyc" \
    -o -name "*.pyo" \
    -o -name "*~" \
    -o -name "*.swp" \
    -o -name "*.swo" \
    -o -name "*.orig" \
    \) \
    -not -path "./node_modules/*" \
    -not -path "./.git/*" \
    -not -path "./venv/*" \
    -not -path "./.venv/*" \
    -not -path "./target/*" \
    -not -path "./.claude/logs/*" \
    -delete 2>/dev/null || true

# 2. Remove Python cache directories
log "Cleaning Python cache..."
find . -type d -name "__pycache__" \
    -not -path "./venv/*" \
    -not -path "./.venv/*" \
    -exec rm -rf {} + 2>/dev/null || true

# 3. Update .gitignore timestamp
log "Updating timestamps..."
DATE=$(date +"%B %d, %Y")

# Update memory.md timestamp
if [ -f ".claude/memory.md" ]; then
    if grep -q "Last Updated" .claude/memory.md; then
        sed -i.bak "s/\*Last Updated\*:.*/\*Last Updated\*: $DATE/" .claude/memory.md 2>/dev/null || \
        sed -i '' "s/\*Last Updated\*:.*/\*Last Updated\*: $DATE/" .claude/memory.md 2>/dev/null || true
        rm .claude/memory.md.bak 2>/dev/null || true
    fi
fi

# Update STATUS.md timestamp
if [ -f "docs/STATUS.md" ]; then
    if grep -q "Last Updated" docs/STATUS.md; then
        sed -i.bak "s/\*\*Last Updated\*\*:.*/\*\*Last Updated:\*\* $DATE/" docs/STATUS.md 2>/dev/null || \
        sed -i '' "s/\*\*Last Updated\*\*:.*/\*\*Last Updated:\*\* $DATE/" docs/STATUS.md 2>/dev/null || true
        rm docs/STATUS.md.bak 2>/dev/null || true
    fi
fi

# 4. Clean empty directories (except protected ones)
log "Removing empty directories..."
find . -type d -empty \
    -not -path "./.git/*" \
    -not -path "./node_modules/*" \
    -not -path "./venv/*" \
    -not -path "./.venv/*" \
    -not -path "./.claude/logs/*" \
    -not -path "./target/*" \
    -delete 2>/dev/null || true

# 5. Clean backup and temporary files from root
log "Removing backup and temporary files from root..."

# Remove old backup tarballs (older than 7 days)
find . -maxdepth 1 -type f -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true

# Remove temporary text files
find . -maxdepth 1 -type f \( \
    -name "*_enforcer.txt" \
    -o -name "*.bak" \
    -o -name "*.backup" \
    \) -delete 2>/dev/null || true

# 6. Organize documentation files
log "Organizing documentation..."

# Create docs directory if it doesn't exist
mkdir -p docs 2>/dev/null || true

# Files that should stay in root
KEEP_IN_ROOT=(
    "README.md"
    "LICENSE"
    "CONTRIBUTING.md"
    ".gitignore"
    "CHANGELOG.md"
    "CODE_OF_CONDUCT.md"
)

# Move markdown files to docs/ unless they should stay in root
for file in *.md; do
    if [ -f "$file" ]; then
        SHOULD_KEEP=false
        for keep_file in "${KEEP_IN_ROOT[@]}"; do
            if [ "$file" = "$keep_file" ]; then
                SHOULD_KEEP=true
                break
            fi
        done

        if [ "$SHOULD_KEEP" = false ]; then
            # Move to docs/ if it's not already there
            if [ ! -f "docs/$file" ]; then
                log "Moving $file to docs/"
                mv "$file" "docs/" 2>/dev/null || true
            else
                log "Removing duplicate $file (already exists in docs/)"
                rm "$file" 2>/dev/null || true
            fi
        fi
    fi
done

# 7. Archive old documentation files
log "Archiving old documentation..."
DATE_CUTOFF=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d '30 days ago' +%Y-%m-%d 2>/dev/null || echo "2024-09-01")

# Create archive directory if it doesn't exist
mkdir -p docs/archive 2>/dev/null || true

# Archive old markdown files in docs/ (except important ones)
KEEP_IN_DOCS=(
    "STATUS.md"
    "ARCHITECTURE.md"
    "API.md"
    "DEPLOYMENT.md"
)

if [ -d "docs" ]; then
    for file in docs/*.md; do
        if [ -f "$file" ]; then
            basename_file=$(basename "$file")
            SHOULD_KEEP=false

            for keep_file in "${KEEP_IN_DOCS[@]}"; do
                if [ "$basename_file" = "$keep_file" ]; then
                    SHOULD_KEEP=true
                    break
                fi
            done

            if [ "$SHOULD_KEEP" = false ]; then
                # Check if file is older than 30 days (if stat command available)
                if command -v stat >/dev/null 2>&1; then
                    FILE_DATE=$(stat -f %Sm -t %Y-%m-%d "$file" 2>/dev/null || stat -c %y "$file" 2>/dev/null | cut -d' ' -f1)
                    if [ "$FILE_DATE" \< "$DATE_CUTOFF" ]; then
                        log "Archiving old file: $basename_file"
                        mv "$file" "docs/archive/" 2>/dev/null || true
                    fi
                fi
            fi
        fi
    done
fi

log "Cleanup complete"
exit 0
