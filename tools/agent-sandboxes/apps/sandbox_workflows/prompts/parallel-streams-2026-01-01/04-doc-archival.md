# Stream D: Documentation Archival

## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
# The GITHUB_TOKEN is available in your environment
# Configure git to use it for push operations
git remote set-url origin https://${GITHUB_TOKEN}@github.com/PerformanceSuite/CommandCenter.git

# Verify it's set (should show https://ghp_...@github.com/...)
git remote -v
```

**You MUST do this before attempting to push.** The sandbox doesn't have SSH keys.

---

## Context

CommandCenter has **~154 markdown files** in the docs directory, with an estimated **25-30% needing archival**. This clutters the documentation and makes it hard to find current information.

Sprint 6b will extract concepts from documents - a clean doc structure makes that more valuable.

## Your Mission

Archive stale documents, organize remaining docs, and create a clear index.

## Branch

Create and work on: `chore/doc-cleanup`

## Classification Criteria

### Archive (move to docs/archive/)
- Session notes older than 30 days
- Completed plans (work is done)
- Superseded documents (replaced by newer versions)
- Stale technical references (outdated stack info)
- Abandoned proposals (never implemented)

### Keep in docs/
- Current roadmaps and plans
- Active architecture docs
- Current API documentation
- Operational guides
- Concept definitions that are still accurate

### Delete (rare)
- Exact duplicates
- Empty files
- Temporary test files

## Step-by-Step Implementation

### Step 1: Create Archive Structure

```bash
mkdir -p docs/archive/2024
mkdir -p docs/archive/2025-H1  # Jan-Jun 2025
mkdir -p docs/archive/2025-H2  # Jul-Dec 2025
mkdir -p docs/archive/superseded
mkdir -p docs/archive/completed-plans
```

### Step 2: Archive Session Files

Session files are point-in-time notes, not persistent documentation:

```bash
# Find and move session files
find docs -maxdepth 1 -name "*SESSION*" -type f -exec mv {} docs/archive/2025-H2/ \;
find docs -maxdepth 1 -name "*NEXT*" -type f -exec mv {} docs/archive/2025-H2/ \;
find docs -maxdepth 1 -name "CURRENT_*.md" -type f -exec mv {} docs/archive/2025-H2/ \;
```

### Step 3: Review and Classify Major Docs

For each document in docs/, determine its fate:

| Document | Decision | Reason |
|----------|----------|--------|
| `ARCHITECTURE.md` | Keep | Core reference |
| `CLAUDE.md` | Keep | AI context |
| `ROADMAP.md` | Update or Archive | Check if current |
| `CAPABILITIES.md` | Archive | Known stale |
| `PRD.md` | Keep | Product requirements |
| Session/Next files | Archive | Ephemeral |

### Step 4: Archive plans/ Subdirectory

```bash
# Plans that are complete - move to archive
# Review each file's status

# Example patterns:
# - *sprint3-completion* → completed-plans (if sprint 3 is done)
# - Plans older than 60 days → review for completion
# - *-v1* files if *-v2* exists → superseded
```

Create `docs/plans/README.md`:

```markdown
# Plans Directory

Active planning documents for CommandCenter development.

## Current Sprint
- [composable-surface-sprint-plan.md](./composable-surface-sprint-plan.md) - VISLZR sprints

## Active Plans
- [2026-01-01-document-intelligence-agents.md](./2026-01-01-document-intelligence-agents.md) - Sprint 6
- [2026-01-01-composable-commandcenter-design.md](./2026-01-01-composable-commandcenter-design.md) - Vision

## Archived
See [../archive/completed-plans/](../archive/completed-plans/) for completed work.
```

### Step 5: Review docs/concepts/

These are core concept definitions - likely to stay:

```bash
ls docs/concepts/
# Concept_Index.md, Fractlzr.md, MRKTZR.md, README.md, ROLLIZR.md, Veria.md
```

Verify each is:
1. Still accurate to current understanding
2. Not duplicated elsewhere
3. Properly linked in Concept_Index.md

### Step 6: Review docs/audits/

These are point-in-time assessments. Keep recent, archive old:

```bash
# Keep recent audits (last 30 days)
# Archive older audits

# Current (keep):
# - 2025-12-29-COMPREHENSIVE-CAPABILITY-AUDIT.md
# - 2025-12-30-COMPREHENSIVE-HEALTH-REPORT.md
# - 2025-12-30-testing-assessment.md

# Older audits → archive/2025-H2/
```

### Step 7: Create Main Index

Create or update `docs/README.md`:

```markdown
# CommandCenter Documentation

## Quick Links

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design and components |
| [CLAUDE.md](./CLAUDE.md) | AI assistant context |
| [PRD.md](./PRD.md) | Product requirements |

## Directories

### [concepts/](./concepts/)
Business and product concept definitions (Veria, MRKTZR, Fractlzr, etc.)

### [plans/](./plans/)
Active development plans and sprint tracking.

### [audits/](./audits/)
Code health and capability assessments.

### [diagrams/](./diagrams/)
Architecture and flow diagrams.

### [cleanup/](./cleanup/)
Document extraction and analysis results.

### [archive/](./archive/)
Historical documents, completed plans, superseded versions.

## Documentation Standards

### File Naming
- Plans: `YYYY-MM-DD-descriptive-name.md`
- Audits: `YYYY-MM-DD-audit-type.md`
- Concepts: `ConceptName.md` (PascalCase)

### When to Archive
- Session notes after 30 days
- Plans after work is complete
- Docs superseded by newer versions

### Before Adding New Docs
1. Check if topic already covered elsewhere
2. Use appropriate directory
3. Follow naming conventions
4. Update relevant index files
```

### Step 8: Update .gitignore

Ensure temp files don't pollute docs:

```bash
# Add to .gitignore if not present
echo "docs/**/*.tmp" >> .gitignore
echo "docs/**/*~" >> .gitignore
echo "docs/**/._*" >> .gitignore
```

### Step 9: Generate Archive Manifest

Create `docs/archive/MANIFEST.md`:

```markdown
# Archive Manifest

Documents moved to archive on YYYY-MM-DD.

## 2025-H2 (July-December 2025)

| Document | Original Location | Reason |
|----------|-------------------|--------|
| SESSION_SUMMARY_*.md | docs/ | Ephemeral session notes |
| CURRENT_SESSION.md | docs/ | Point-in-time |
| NEXT_SESSION*.md | docs/ | Superseded |

## Completed Plans

| Document | Original Location | Completion Date |
|----------|-------------------|-----------------|
| sprint3-completion.md | docs/plans/ | 2025-12-31 |

## Superseded

| Document | Replaced By |
|----------|-------------|
| architecture-v1.md | ARCHITECTURE.md |
```

### Step 10: Final Cleanup

```bash
# Count before and after
echo "Before cleanup:"
find docs -name "*.md" -type f | wc -l

# Run cleanup...

echo "After cleanup:"
find docs -name "*.md" -type f | wc -l
find docs/archive -name "*.md" -type f | wc -l

# Verify no broken links
# (If you have a link checker)
```

## Verification Checklist

```bash
# 1. Archive exists and has content
ls docs/archive/

# 2. Main docs are organized
ls docs/

# 3. README index exists
cat docs/README.md

# 4. No orphan session files in root
find docs -maxdepth 1 -name "*SESSION*" -name "*NEXT*"
# Should return nothing

# 5. Plans directory has README
cat docs/plans/README.md
```

## Commit Strategy

1. `chore(docs): create archive directory structure`
2. `chore(docs): archive session and ephemeral files`
3. `chore(docs): archive completed plans`
4. `chore(docs): organize and index remaining docs`
5. `docs: add README indexes for docs directories`
6. `chore(docs): add archive manifest`

## Create PR

Title: `chore(docs): archive stale docs and create index`

Body:
```markdown
## Summary
Cleans up documentation by archiving stale/completed docs and creating clear indexes.

## Changes
- Created `docs/archive/` with organized subdirectories
- Archived ~40 session/ephemeral files
- Archived completed plans
- Created `docs/README.md` index
- Created `docs/plans/README.md` index
- Created `docs/archive/MANIFEST.md`

## File Counts
- Before: ~154 docs
- Active docs: ~100
- Archived: ~54

## Benefits
- Easier to find current docs
- Clean target for Sprint 6b document extraction
- Clear documentation standards

## No Breaking Changes
All files preserved in archive, just reorganized.
```

## Completion Criteria

- [ ] Archive structure created
- [ ] Session files archived
- [ ] Stale files archived
- [ ] Completed plans archived
- [ ] docs/README.md index created
- [ ] docs/plans/README.md created
- [ ] docs/archive/MANIFEST.md created
- [ ] PR created with clear description
