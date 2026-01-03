---
name: repository-hygiene
description: Enforces clean repository structure by preventing root-level clutter, organizing scripts/docs properly, and cleaning up temporary artifacts. Use during any session when creating files, and before commits.
---

# Repository Hygiene

Keep repositories professional and organized. Every file has a proper home.

## Core Rules

### Root Directory - Keep Minimal

**Allowed in root:**
- README.md, LICENSE, CONTRIBUTING.md, SECURITY.md, CLAUDE.md
- Package files (package.json, pyproject.toml, Cargo.toml, etc.)
- Config files (.gitignore, .env.example, tsconfig.json, etc.)
- CI/CD directories (.github/, .claude/)

**Examples of allowed root files:**
```
✅ README.md               # Project documentation
✅ package.json            # Node.js dependencies
✅ .gitignore              # Git configuration
✅ tsconfig.json           # TypeScript config
✅ .env.example            # Example environment variables
```

**NOT allowed in root:**
- Test scripts (`test-*.sh`, `test-*.py`)
- Utility scripts (`fix-*.sh`, `apply-*.ts`, `session-*`)
- SQL files, one-off scripts
- Documentation (except allowed list above)

**Examples of violations:**
```
❌ test-api.sh             # Should be in scripts/tests/
❌ fix-database.py         # Should be in scripts/
❌ session-notes.md        # Should be in docs/ or deleted
❌ migration-001.sql       # Should be in migrations/
❌ API_GUIDE.md            # Should be in docs/
❌ apply-patches.ts        # Should be in scripts/
```

### Proper Locations

| File Type | Location | Example |
|-----------|----------|---------|
| Test scripts | `scripts/tests/` or `tests/` | `scripts/tests/test-api.sh` |
| Utility scripts | `scripts/` | `scripts/fix-database.py` |
| Documentation | `docs/` | `docs/API_GUIDE.md` |
| SQL migrations | `migrations/` or `db/migrations/` | `migrations/001-add-users.sql` |
| Temporary files | `/tmp/` or delete after use | `/tmp/debug-output.log` |

**Real-world examples:**

**Before (❌ Messy):**
```
CommandCenter/
├── README.md
├── test-auth.sh           ❌ Wrong location
├── fix-permissions.py     ❌ Wrong location
├── ARCHITECTURE.md        ❌ Wrong location
├── session-notes.md       ❌ Wrong location
└── src/
```

**After (✅ Clean):**
```
CommandCenter/
├── README.md
├── scripts/
│   ├── tests/
│   │   └── test-auth.sh   ✅ Proper location
│   └── fix-permissions.py ✅ Proper location
├── docs/
│   └── ARCHITECTURE.md    ✅ Proper location
└── src/
```

## Workflow

### Before Creating Files

Ask yourself:
1. **Temporary?** → Create in `/tmp/` or delete immediately after
2. **Test script?** → `scripts/tests/` or `tests/`
3. **Utility?** → `scripts/`
4. **Documentation?** → `docs/`

**Decision tree examples:**

```
"I need to test the authentication flow"
→ Temporary test? YES
→ Location: /tmp/test-auth.sh or scripts/tests/test-auth.sh
→ Delete after use? If in /tmp, YES

"I'm writing a database migration"
→ Temporary? NO
→ Location: migrations/003-add-oauth.sql

"I need a script to fix file permissions"
→ Temporary? Maybe reusable
→ Location: scripts/fix-permissions.py

"I want to document the API"
→ Documentation? YES
→ Location: docs/API.md
```

### Before Committing

Run these checks:
```bash
# Find violations in root
ls -1 *.md 2>/dev/null | grep -vE '^(README|CLAUDE|LICENSE|CONTRIBUTING|SECURITY)\.md$'
ls -1 *.{sh,py,js,ts} 2>/dev/null
ls -1 test-* session-* 2>/dev/null
```

Move or delete any violations before committing.

**Example cleanup process:**
```bash
# Found violations:
# - test-api.sh
# - fix-db.py
# - SETUP_GUIDE.md

# Move to proper locations:
mkdir -p scripts/tests docs
mv test-api.sh scripts/tests/
mv fix-db.py scripts/
mv SETUP_GUIDE.md docs/

# Verify root is clean:
git status
```

## Red Flags

- Creating `test-*.sh` in root
  - **Example**: `touch test-login.sh` in root → Should be in `scripts/tests/`
- "I'll clean it up later" (do it now)
  - **Example**: Leaving `debug-output.txt` → Delete or move to `/tmp/`
- "It's just a quick test" (use `/tmp/` or delete after)
  - **Example**: `quick-test.py` → Use `/tmp/quick-test.py` and delete after
- Leaving utility scripts in root
  - **Example**: `apply-patches.sh` sitting in root → Move to `scripts/`

## Quick Reference Checklist

Use this checklist before every commit:

### File Organization
- [ ] No test scripts in root (e.g., `test-*.sh`, `test-*.py`)
- [ ] No utility scripts in root (e.g., `fix-*.sh`, `apply-*.ts`)
- [ ] No stray .md files in root (except README, LICENSE, CONTRIBUTING, SECURITY, CLAUDE)
- [ ] No SQL files in root (should be in `migrations/`)
- [ ] No session/temporary files in root (e.g., `session-*.md`, `temp-*.txt`)

### Directory Structure
- [ ] Test scripts in `scripts/tests/` or `tests/`
- [ ] Utility scripts in `scripts/`
- [ ] Documentation in `docs/`
- [ ] Migrations in `migrations/` or `db/migrations/`
- [ ] Temporary files deleted or in `/tmp/`

### Git Status
- [ ] `git status` shows only intentional changes
- [ ] No untracked files that should be ignored
- [ ] No accidentally committed temporary files

### Common Violations to Check
- [ ] No files matching pattern: `test-*` in root
- [ ] No files matching pattern: `fix-*` in root
- [ ] No files matching pattern: `session-*` in root
- [ ] No files matching pattern: `*.sql` in root
- [ ] No files matching pattern: `apply-*` in root

**Quick verification command:**
```bash
# Run this to catch most violations:
ls -1 | grep -E '^(test-|fix-|session-|apply-)'
ls -1 *.sql 2>/dev/null
ls -1 *.md | grep -vE '^(README|CLAUDE|LICENSE|CONTRIBUTING|SECURITY)\.md$'
```

If any of these commands return results, you have violations to fix!
