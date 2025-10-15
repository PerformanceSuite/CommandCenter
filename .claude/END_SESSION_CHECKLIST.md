# End Session Checklist

This checklist MUST be followed completely when ending a Claude Code session.

## ✅ Required Steps (DO NOT SKIP ANY)

### 1. Document Session in memory.md
- [ ] Run `git log --oneline -10` to see recent commits
- [ ] Run `git status` to see uncommitted work
- [ ] Update `.claude/memory.md` with new dated section:
  - What was accomplished
  - What was tested/verified
  - Key decisions made
  - Files created/modified with line numbers
  - Commits made during session
  - What's left to do
- [ ] Update "Last Updated" timestamp
- [ ] Update "Next Session Recommendations"

### 2. Check Memory Management
- [ ] Run `bash .claude/cleanup.sh` to see memory stats
- [ ] If memory.md > 1200 lines OR > 15 sessions:
  - Archive old sessions to `.claude/archives/YYYY-MM-sessions-XX-YY.md`
  - Keep last 5-10 sessions in memory.md
  - Update "Historical Sessions" section with archive reference
- [ ] If memory.md > 800 lines: Note for next session to consider archiving

### 3. Commit Session Documentation
- [ ] Run `git add .claude/memory.md` (and archives if created)
- [ ] Commit with format: `docs: session [date] - [brief summary]`
- [ ] Verify commit succeeded

### 4. Run Cleanup Script
- [ ] Execute `bash .claude/cleanup.sh`
- [ ] Review memory management warnings
- [ ] Verify cleanup completed successfully
- [ ] Check if cleanup modified any files (timestamp updates)

### 5. Commit Cleanup Changes
- [ ] Run `git status` to check for cleanup modifications
- [ ] If files modified: `git add -A && git commit -m "docs: update timestamp after session cleanup"`
- [ ] Verify commit succeeded

### 6. Kill Background Processes
- [ ] Check for running background shells with `/bashes` or similar
- [ ] Kill ALL background shells before pushing
- [ ] Verify no servers running on localhost (3000, 5173, 8000, etc.)

### 7. Push to Origin
- [ ] Check current branch: `git branch --show-current`
- [ ] If on `main`/`master`: Push with `git push origin main`
- [ ] If on feature branch: Offer to create PR (see step 8)
- [ ] Verify push succeeded (check output)
- [ ] Run `git status` to confirm "up to date with origin"

### 8. Create PR (Feature Branches Only)
- [ ] Only if NOT on `main`/`master`
- [ ] Ask user: "Create PR for this work? (y/n)"
- [ ] If yes: Use session summary for PR description
- [ ] Use `gh pr create --title "[title]" --body "[description]"`

### 9. Final Verification
- [ ] Run `git status` - should show "working tree clean" and "up to date"
- [ ] Confirm all background processes killed
- [ ] Provide session summary to user:
  - What was accomplished
  - Commits pushed
  - Current branch status
  - Memory management status
  - Next actions

## 🚨 Common Mistakes to Avoid

1. **DON'T skip pushing** - Session is not complete until commits are on origin
2. **DON'T leave background processes running** - Kill them BEFORE pushing
3. **DON'T forget to document** - Memory.md MUST be updated every session
4. **DON'T assume cleanup is optional** - Always run cleanup.sh
5. **DON'T ignore memory warnings** - Archive when cleanup.sh shows warnings
6. **DON'T batch updates** - Commit memory.md separately from code changes

## 📋 Memory Management Guidelines

### When to Archive
Archive memory.md when **ANY** of these conditions are met:
- memory.md exceeds **1200 lines** (warning threshold)
- More than **15 sessions** in memory.md
- cleanup.sh shows warning or critical status
- Sessions older than **1 month** that aren't recent work

### How to Archive
1. Identify sessions to archive (keep last 5-10 sessions)
2. Extract old sessions to `.claude/archives/YYYY-MM-sessions-XX-YY.md`
3. Update memory.md to keep only recent sessions + structure
4. Update "Historical Sessions" section with new archive reference
5. Commit both files: `docs: Archive sessions XX-YY, reduce memory.md by N%`

### Archive File Format
```markdown
# CommandCenter - Archived Sessions XX-YY

**Archive Date**: YYYY-MM-DD
**Sessions**: XX-YY (Description of period)
**Period**: YYYY-MM-DD to YYYY-MM-DD

## Archive Contents
- **Session XX**: Brief description
- **Session YY**: Brief description

---

[Full session details...]
```

## 📊 Quick Verification Commands

```bash
# Check commits not yet pushed
git log origin/main..HEAD --oneline

# Check for uncommitted changes
git status --short

# Check current branch
git branch --show-current

# Check memory status
bash .claude/cleanup.sh

# Check memory line count
wc -l .claude/memory.md

# Count sessions in memory
grep -c "^### Session [0-9]\+:" .claude/memory.md

# List background processes
# (Use Claude Code's /bashes command or similar)

# Verify nothing listening on common ports
lsof -ti:3000,5173,8000 2>/dev/null || echo "All ports clear"
```

## 🎯 Success Criteria

Session is ONLY complete when ALL of these are true:

- ✅ memory.md updated with session notes
- ✅ Memory management check performed (via cleanup.sh)
- ✅ Memory archived if needed (>1200 lines or >15 sessions)
- ✅ All changes committed (git status shows "working tree clean")
- ✅ All commits pushed to origin (git status shows "up to date")
- ✅ All background processes killed
- ✅ Cleanup script executed
- ✅ User provided with session summary

---

## 📝 Session Summary Template

Use this template when providing final summary to user:

```
## Session Complete! ✅

**What was accomplished:**
- [Brief bullet points of work completed]

**Commits pushed:**
- `abc1234` - description
- `def5678` - description

**Memory management:**
- Current size: XXX lines (Y sessions, Z archives)
- Status: [OK / Warning / Archived]

**Branch status:**
- Current branch: [branch name]
- Status: ✅ Up to date with origin

**Next actions:**
- [What should be done next session]

You can now safely exit Claude Code.
```

---

**If ANY step fails, STOP and fix it before proceeding to next step.**
