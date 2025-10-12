# Memory Management Guidelines for Claude Code

**Last Updated**: 2025-10-12

This document provides guidelines for maintaining `.claude/memory.md` at an optimal size for Claude Code sessions.

---

## 🎯 Goals

1. **Keep memory.md under 800 lines** for fast context loading
2. **Maintain last 5-10 sessions** for recent context
3. **Archive older sessions** monthly to preserve history
4. **Automate detection** of when archiving is needed

---

## 📐 Memory Size Thresholds

| Lines | Status | Action |
|-------|--------|--------|
| 0-500 | ✅ Optimal | No action needed |
| 501-800 | ✅ Good | Monitor size |
| 801-1000 | ⚠️ Warning | Consider archiving at next session |
| 1001-2000 | ⚠️ Large | Archive recommended |
| 2000+ | 🚨 Critical | Archive immediately |

---

## 🤖 Automated Checks (cleanup.sh)

The `cleanup.sh` script now includes automatic memory monitoring:

```bash
# Run at end of every session
bash .claude/cleanup.sh
```

**What it checks:**
- Current memory.md line count
- Number of sessions in memory
- Compares against threshold (800 lines)
- Shows statistics and warnings

**Example output:**
```
📊 Memory Statistics:
  • memory.md: 439 lines
  • Sessions in memory: 5
  • Archive files: 1
  ✅ Memory file size OK (439/800 lines)
```

---

## 📋 Manual Archiving Process (When Needed)

### When to Archive

Archive when **ANY** of these conditions are met:
- memory.md exceeds **800 lines**
- More than **10 sessions** in memory.md
- Sessions older than **1 month**
- cleanup.sh shows warning/alert

### How to Archive

**Step 1: Identify sessions to archive**
```bash
# Count sessions
grep "^### Session [0-9]\+:" .claude/memory.md | wc -l

# View session numbers
grep "^### Session [0-9]\+:" .claude/memory.md | head -20
```

**Step 2: Determine cutoff**
- Keep **last 5 sessions** (at minimum)
- Keep **current sprint work** (sessions from current month)
- Archive everything else

**Step 3: Extract sessions to archive**
```bash
# Example: Archive Sessions 1-25, keep 26-current
# Find line number where Session 26 starts
grep -n "^### Session 26:" .claude/memory.md

# Extract lines 1-[line_number-1] to archive
sed -n '1,[line_number]p' .claude/memory.md > .claude/archives/YYYY-MM-sessions.md
```

**Step 4: Create new memory.md**
```bash
# Extract recent sessions + static content
# Keep: Header, Project Overview, Architecture, Recent Sessions
```

**Step 5: Verify and commit**
```bash
# Check sizes
wc -l .claude/memory.md .claude/archives/*.md

# Commit
git add .claude/
git commit -m "docs: Archive sessions [X-Y] - memory optimization"
```

---

## 📝 /end-session Integration

When running `/end-session`, Claude should:

### 1. Check Memory Size
```bash
CURRENT_LINES=$(wc -l < .claude/memory.md)
if [ $CURRENT_LINES -gt 800 ]; then
    echo "⚠️ Memory file has $CURRENT_LINES lines (threshold: 800)"
    echo "Consider archiving old sessions"
fi
```

### 2. Update Memory Rules

**When documenting sessions, follow these rules:**

**DO** ✅:
- Keep session summaries concise (50-100 lines per session)
- Focus on deliverables, not implementation details
- Use bullet points instead of paragraphs
- Link to detailed logs/commits instead of embedding full output
- Remove redundant "Testing/Verification" sections
- Consolidate similar sessions

**DON'T** ❌:
- Include full file contents in session logs
- Repeat the same information across multiple sessions
- Keep detailed troubleshooting steps (once resolved)
- Document every single command executed
- Maintain duplicate architecture descriptions

**Example - GOOD Session Entry:**
```markdown
### Session 28: Observability Implementation ✅
**Date**: 2025-10-12
**Status**: COMPLETE - 4h actual vs 5h budgeted

**Deliverables:**
- Health check endpoints (3 services)
- Structured JSON logging
- Prometheus metrics (5 new metrics)

**Files Created (3 files, 450 LOC):**
- backend/app/routers/health.py
- backend/app/utils/logging_config.py
- backend/app/utils/metrics.py

**Commit:** `abc1234` - feat: Add observability infrastructure
```

**Example - BAD Session Entry (Too Verbose):**
```markdown
### Session 28: Observability Implementation ✅
**Date**: 2025-10-12

First I read the health.py file:
[300 lines of file content]

Then I tested the endpoint:
[50 lines of curl output]

Then I found an error:
[100 lines of error logs]

Then I fixed it by:
[200 lines of implementation details]

[Repeat for each file...]
```

### 3. Archive Trigger Logic

```python
def should_archive_memory():
    """Determine if archiving is needed."""
    lines = count_lines(".claude/memory.md")
    sessions = count_sessions(".claude/memory.md")

    if lines > 1000:
        return True, "Critical: >1000 lines"
    elif lines > 800:
        return True, "Warning: >800 lines"
    elif sessions > 10:
        return True, f"Too many sessions: {sessions}"
    else:
        return False, f"OK ({lines} lines, {sessions} sessions)"
```

### 4. Archiving During /end-session

**When cleanup.sh shows alert:**
```
⚠️ ALERT: memory.md exceeds recommended size
    Archive needed at next /end-session
```

**Claude should:**
1. Identify oldest sessions (beyond last 5)
2. Extract to `.claude/archives/YYYY-MM-sessions.md`
3. Restructure memory.md keeping only recent sessions
4. Add header to archive file
5. Commit both files with descriptive message

---

## 🏗️ Memory.md Structure (Template)

To maintain optimal size, memory.md should follow this structure:

```markdown
# CommandCenter - Claude Code Memory

**Last Updated**: YYYY-MM-DD

---

## 🎯 START HERE - Next Session Quick Reference
[~50 lines - immediate priorities]

## 📊 Project Overview
[~50 lines - tech stack, architecture summary]

## 🏗️ Current Status - Recent Sessions
[~200 lines - last 5 sessions only, concise format]

## 📋 Phase/Sprint Progress Tracker
[~50 lines - visual roadmap]

## 🏛️ Architecture Reference
[~100 lines - diagrams, key patterns]

## 🔧 Configuration & Setup
[~50 lines - quick commands]

## 🐛 Common Issues & Solutions
[~50 lines - top 5 problems]

## 📚 Technical Debt & Improvements
[~50 lines - prioritized list]

## 🔗 Historical Sessions
[~20 lines - links to archives]

## 📖 Additional Resources
[~30 lines - docs, references]

---
TOTAL: ~700 lines maximum
```

---

## 📊 Monthly Maintenance Checklist

**First session of each month:**

- [ ] Run `cleanup.sh` and review statistics
- [ ] Check if memory.md > 800 lines
- [ ] Count sessions in memory (should be ≤10)
- [ ] Archive previous month's sessions if needed
- [ ] Verify archive file has header
- [ ] Commit archive changes
- [ ] Update "Last Archived" date in this document

**Last Archived**: Never (first archive created 2025-10-12)

---

## 🔍 Monitoring Commands

**Quick checks:**
```bash
# Line count
wc -l .claude/memory.md

# Session count
grep -c "^### Session [0-9]\+:" .claude/memory.md

# Size in KB
du -h .claude/memory.md

# Archive count
ls -1 .claude/archives/*.md | wc -l

# Full report
bash .claude/cleanup.sh
```

---

## 🚨 Emergency Reset (Last Resort)

If memory.md becomes unmanageable (>5000 lines), perform emergency reset:

```bash
# Backup current state
cp .claude/memory.md .claude/archives/$(date +%Y-%m-%d)-emergency-backup.md

# Extract ONLY last 2 sessions
grep -n "^### Session" .claude/memory.md | tail -2
# Note line numbers

# Create minimal memory.md with structure + last 2 sessions
# Use the template above
```

**Only use this if:**
- File exceeds 5000 lines
- Normal archiving would take too long
- Immediate session start is critical

---

## 📈 Success Metrics

**Healthy memory.md:**
- ✅ 400-800 lines consistently
- ✅ 5-10 sessions in memory
- ✅ Archives created monthly
- ✅ No cleanup.sh warnings
- ✅ Fast Claude Code session starts (<5 seconds)

**Unhealthy memory.md:**
- ❌ >1000 lines regularly
- ❌ >15 sessions accumulated
- ❌ No archives created
- ❌ Cleanup.sh shows alerts
- ❌ Slow session starts (>10 seconds)

---

## 🤝 Best Practices

1. **Archive proactively** - Don't wait for alerts
2. **Keep recent context** - Last 5 sessions minimum
3. **Concise session logs** - Focus on deliverables, not details
4. **Run cleanup.sh** - After every session
5. **Monthly review** - Check memory health first session of month
6. **Link, don't embed** - Reference commits/PRs instead of full details
7. **Consolidate duplicates** - Remove repeated information
8. **Trust archives** - Historical details are preserved

---

## 📚 Related Documents

- `.claude/cleanup.sh` - Automated monitoring script
- `.claude/archives/` - Historical session archives
- `CLAUDE.md` - Project-specific Claude Code instructions

---

**Remember**: Memory management is about **quality over quantity**. A well-maintained 500-line memory.md is far more valuable than a 3,000-line file that's impossible to navigate.
