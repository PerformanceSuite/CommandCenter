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

**NOT allowed in root:**
- Test scripts (`test-*.sh`, `test-*.py`)
- Utility scripts (`fix-*.sh`, `apply-*.ts`, `session-*`)
- SQL files, one-off scripts
- Documentation (except allowed list above)

### Proper Locations

| File Type | Location |
|-----------|----------|
| Test scripts | `scripts/tests/` or `tests/` |
| Utility scripts | `scripts/` |
| Documentation | `docs/` |
| SQL migrations | `migrations/` or `db/migrations/` |
| Temporary files | `/tmp/` or delete after use |

## Workflow

### Before Creating Files

Ask yourself:
1. **Temporary?** → Create in `/tmp/` or delete immediately after
2. **Test script?** → `scripts/tests/` or `tests/`
3. **Utility?** → `scripts/`
4. **Documentation?** → `docs/`

### Before Committing

Run these checks:
```bash
# Find violations in root
ls -1 *.md 2>/dev/null | grep -vE '^(README|CLAUDE|LICENSE|CONTRIBUTING|SECURITY)\.md$'
ls -1 *.{sh,py,js,ts} 2>/dev/null
ls -1 test-* session-* 2>/dev/null
```

Move or delete any violations before committing.

## Red Flags

- Creating `test-*.sh` in root
- "I'll clean it up later" (do it now)
- "It's just a quick test" (use `/tmp/` or delete after)
- Leaving utility scripts in root

## Checklist

- [ ] No test scripts in root
- [ ] No utility scripts in root
- [ ] No stray .md files in root (except allowed)
- [ ] No SQL files in root
- [ ] `git status` is clean or intentional
