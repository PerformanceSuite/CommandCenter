---
name: project-health
description: Comprehensive project assessment methodology for understanding current state, identifying stale artifacts, synthesizing vision, and planning cleanup. Use before major work phases, quarterly reviews, or when project state is unclear.
---

# Project Health Assessment

Get an accurate snapshot of where a project is NOW before making decisions.

## When to Use

- Before starting major development work
- When project state is unclear or stale
- Quarterly health reviews
- Before creating project-specific skills
- After long gaps in development

## Assessment Phases

### Phase 1: Code Reality

Understand what actually exists in the codebase.

```bash
# Structure overview
find . -type f -name "*.py" | head -50
find . -type f -name "*.ts" | head -50

# Test count
find . -name "test_*.py" -o -name "*.test.ts" | wc -l

# Recent commits
git log --oneline -20

# Branch status
git branch -a
git worktree list
```

**Document:**
- Services/modules that exist
- Test coverage (rough count)
- Active vs stale branches
- Uncommitted/unpushed work

### Phase 2: Documentation Reality

Audit documentation freshness.

```bash
# List all docs
find docs/ -name "*.md" -type f

# Find stale session docs
ls -la docs/*SESSION* docs/*session* 2>/dev/null

# Check doc ages
find docs/ -name "*.md" -mtime +30 -type f  # Modified 30+ days ago
```

**Classify docs as:**
- **Current**: Actively maintained, accurate
- **Stale**: Outdated but potentially useful content
- **Archive**: Should be moved to docs/archive/
- **Delete**: No longer relevant

### Phase 3: Vision Synthesis

Extract and reconcile the intended direction.

**Key files to review:**
- `README.md` - Project overview
- `docs/ROADMAP.md` or similar - Planned phases
- `docs/plans/` - Detailed implementation plans
- `docs/concepts/` - Feature/product concepts
- `CLAUDE.md` / `AGENTS.md` - AI context

**Questions to answer:**
1. What is this project supposed to become?
2. What phases/milestones were planned?
3. Which are complete, in-progress, abandoned?
4. Has the vision changed since plans were written?

### Phase 4: Artifact Cleanup

Identify what needs cleaning.

**Stale Worktrees:**
```bash
git worktree list
# Check each: when was last commit? Is work merged?
```

**Stale Branches:**
```bash
git branch -a --sort=-committerdate | head -20
# Identify branches with no recent activity
```

**Stale Documentation:**
```bash
# Session files that should be archived
ls docs/CURRENT_SESSION* docs/NEXT_SESSION* 2>/dev/null

# Dated docs older than 60 days
find docs/ -name "*2025-10*" -o -name "*2025-09*" 2>/dev/null
```

**Duplicate/Conflicting Docs:**
- Multiple files covering same topic
- Plans that contradict each other
- Outdated capability lists

### Phase 5: Health Report

Generate a summary document.

```markdown
# Project Health Report - [Date]

## Current State
- **Code**: X services, Y tests, Z% coverage estimate
- **Branches**: N active, M stale
- **Documentation**: X current, Y stale, Z to archive

## Vision Status
- **Original Goal**: [from roadmap]
- **Current Reality**: [what's actually built]
- **Gap Analysis**: [what's missing]

## Cleanup Required
- [ ] Archive N stale docs
- [ ] Delete/merge M stale branches
- [ ] Clean N stale worktrees
- [ ] Update X outdated docs

## Recommendations
1. Priority 1: ...
2. Priority 2: ...
3. Priority 3: ...
```

## Cleanup Protocol

### Documentation Cleanup

```bash
# Create archive if needed
mkdir -p docs/archive

# Move stale session docs
mv docs/CURRENT_SESSION*.md docs/archive/
mv docs/NEXT_SESSION*.md docs/archive/

# Move old dated docs (review first)
mv docs/*2025-10*.md docs/archive/
```

### Branch Cleanup

```bash
# Delete merged local branches
git branch --merged | grep -v main | xargs git branch -d

# List remote branches to review
git branch -r --sort=-committerdate

# Delete stale remote (careful!)
git push origin --delete branch-name
```

### Worktree Cleanup

```bash
# List worktrees
git worktree list

# Remove stale worktree
git worktree remove path/to/worktree

# Or force if dirty
git worktree remove --force path/to/worktree
```

## Integration with Self-Improving Skills

After completing a health assessment:

1. **Create/update project-specific skill** with accurate baseline
2. **Document patterns** discovered during assessment
3. **Document failures** or anti-patterns found
4. **Set up retrospective** to capture future learnings

## Automation with Ralph Loop

For comprehensive assessment:

```bash
/ralph loop "Execute project-health assessment for this project:
1. Audit code structure and tests
2. Audit documentation freshness
3. Synthesize vision from roadmap and plans
4. Identify all cleanup needed
5. Generate health report

Write results to docs/audits/YYYY-MM-DD-health-report.md" \
  --max-iterations 15 \
  --completion-promise "docs/audits/YYYY-MM-DD-health-report.md exists with all sections complete"
```

## Checklist

### Assessment
- [ ] Code structure documented
- [ ] Test coverage estimated
- [ ] Branch/worktree status checked
- [ ] Documentation audited for freshness
- [ ] Vision synthesized from plans
- [ ] Gaps identified

### Cleanup
- [ ] Stale docs archived
- [ ] Stale branches deleted/merged
- [ ] Stale worktrees removed
- [ ] Duplicate docs consolidated
- [ ] Outdated docs updated or archived

### Output
- [ ] Health report written
- [ ] Cleanup tasks listed
- [ ] Recommendations prioritized
- [ ] Project skill updated (if exists)
