---
name: context-management
description: Use proactively throughout sessions to maintain context under 50% capacity (100k tokens) via incremental cleanup, preventing expensive /compact operations
---

# Context Management Skill

**Goal**: Keep context usage under 50% capacity (100k/200k tokens) through continuous, non-disruptive optimization.

## MANDATORY INVOCATION

**This skill is invoked automatically by `/start` command.**

You MUST follow its practices throughout the entire session:
- Thinking mode disabled by default (only enable for complex reasoning)
- Use `gh` CLI instead of GitHub MCP
- Selective file reading with offset/limit
- Filter command outputs with head/tail/grep

**DO NOT SKIP THESE PRACTICES** - they are mandatory, not optional.

## When to Use This Skill

**Proactive (Best):**
- At the start of every session (after /start) - AUTOMATICALLY INVOKED
- After completing major tasks (e.g., file writes, commits)
- Every 10-15 minutes during active development
- Before reading large files or generating long outputs

**Reactive (Fallback):**
- When system reminder shows >80k tokens
- When you notice slower responses
- Before complex tasks that will generate significant output

## Context Monitoring Protocol

### 1. Check Current Usage

When you see system reminders like:
```
Token usage: 115584/200000; 84416 remaining
```

Calculate percentage:
- **Current**: 115584 / 200000 = 58% ⚠️
- **Threshold**: 50% = 100k tokens

### 2. Alert Thresholds

| Usage | Status | Action |
|-------|--------|--------|
| 0-40% | ✅ Healthy | Continue normally |
| 40-50% | 🟡 Caution | Begin incremental cleanup |
| 50-60% | 🟠 Warning | Active cleanup + notifications |
| 60-80% | 🔴 Critical | Aggressive cleanup required |
| 80%+ | 🚨 Emergency | Immediate compaction |

### 3. Communicate Status

When threshold exceeded, inform user:

```
🟡 Context at 45% (90k/200k) - Starting incremental cleanup
🟠 Context at 55% (110k/200k) - Active cleanup in progress
🔴 Context at 65% (130k/200k) - Aggressive cleanup needed
🚨 Context at 85% (170k/200k) - Emergency compaction required
```

## Incremental Cleanup Strategies

### Strategy 0: MCP Server Optimization (Automatic on /start, -15-25k tokens)

**When**: Automatically during `/start` command

**Problem**: MCP servers consume massive context even when unused:
- GitHub MCP: ~18k tokens (26 tools)
- Puppeteer MCP: ~4.7k tokens
- Brave Search MCP: ~1.4k tokens
- IDE MCP: ~1.3k tokens

**Action**: Autonomously disable unused MCPs based on project type

**Workflow**:
1. Read `~/.claude/mcp.json`
2. Detect project type (backend/frontend/fullstack/etc)
3. Identify unused MCPs:
   - **Always disable**: brave-search (redundant with WebSearch)
   - **Backend projects**: Disable puppeteer, ide (unless Jupyter notebooks present)
   - **Frontend projects**: Keep all (may need browser automation)
   - **GitHub**: Always keep enabled (but use `gh` CLI via Bash instead of MCP tools)
4. Comment out unused MCP entries
5. Report optimization results

**Implementation**: Automatically runs during `/start`, reports results like:
```
🔧 MCP Optimization: Disabled 2 unused servers (saves ~6.1k tokens)
  - brave-search: Redundant with WebSearch
  - puppeteer: Not needed for backend work
```

**Note**: Use `gh` CLI via Bash instead of GitHub MCP tools to save an additional ~18k tokens per session (even though GitHub MCP stays enabled for structure).

### Strategy 1: Thinking Suppression (Instant, -20-30%)

**When**: Disable thinking mode by default. Only enable for complex tasks.

**Disable thinking for**:
- Executing clear plans (step-by-step implementation)
- Simple file operations (read, write, edit)
- Running tests or commands
- Code lookups or searches
- Following established patterns

**Enable thinking ONLY for**:
- Brainstorming or design decisions
- Reviewing complex plans for issues
- Debugging ambiguous errors
- Architecture or approach selection
- Trade-off analysis

**Action**: Add at start of response:
```markdown
<thinking_mode>disabled</thinking_mode>
```

**Impact**:
- Reduces token usage by 20-30% immediately
- No quality loss for straightforward tasks
- Re-enable when needed: `<thinking_mode>enabled</thinking_mode>`

**Example**:
```markdown
<thinking_mode>disabled</thinking_mode>

Executing Task 3: Update config file...
```

### Strategy 2: Output Summarization (Fast, -10-15%)

**When**: After completing discrete tasks

**Action**: Instead of showing full tool outputs, summarize:

❌ **Don't** (wasteful):
```
<file contents - 500 lines>
I've read the entire file. Let me now...
```

✅ **Do** (efficient):
```
Read config.py (500 lines) - found 3 relevant sections
Proceeding with update...
```

### Strategy 3: Selective File Reading (Moderate, -15-25%)

**When**: Before reading files

**Actions**:
1. Use `offset` and `limit` parameters when possible
2. Grep/search before full reads
3. Read only changed sections for updates

❌ **Don't**:
```python
Read(file_path="large_file.py")  # Reads entire file
```

✅ **Do**:
```python
Grep(pattern="class MyClass", path="large_file.py")  # Find location first
Read(file_path="large_file.py", offset=100, limit=50)  # Read targeted section
```

### Strategy 4: Tool Output Filtering (Fast, -5-10%)

**When**: Running commands with verbose output

**Actions**:
1. Pipe to `head` or `tail` for previews
2. Use `grep` to filter relevant lines
3. Suppress unnecessary output

❌ **Don't**:
```bash
pytest tests/ -v  # Full verbose output
```

✅ **Do**:
```bash
pytest tests/ -v 2>&1 | grep -E "PASSED|FAILED|ERROR" | head -20
```

### Strategy 5: Memory File Optimization (Moderate, -10-15%)

**When**: At task completion or every 30 minutes

**Actions**:
1. Remove outdated session entries from `.claude/memory.md`
2. Consolidate repetitive information
3. Move details to session logs instead of memory

**Example**:
```markdown
## Session: 2025-10-26 (LATEST)
Work: Completed RAG service rewrite
Next: Dagger integration
Details: See .claude/logs/sessions/2025-10-26_203915.md
```

### Strategy 6: Conversation Pruning (Aggressive, -30-40%)

**When**: Critical threshold (60%+)

**Action**: Suggest to user:
```
🔴 Context at 65% - Recommend conversation pruning:

Option 1: Continue with current task (5-10 min remaining)
Option 2: Complete task, then use /compact to reset context
Option 3: Start new session (save work first)

Current task will complete in ~X messages. Proceed?
```

## Continuous Background Optimization

### Every Response Checklist

Before generating each response:

1. ☐ Check if system reminder shows token usage
2. ☐ If >40%, enable thinking_mode=disabled
3. ☐ Summarize instead of quoting full outputs
4. ☐ Use selective file reading
5. ☐ Filter tool outputs to essentials

### After Each Major Task

After file writes, commits, or task completion:

1. ☐ Note tokens saved via optimization
2. ☐ Update user if crossing threshold
3. ☐ Clean memory file if >300 lines
4. ☐ Compress session logs

## Prevention Best Practices

### File Operations

**Reading**:
- Use Grep before Read to locate sections
- Use offset/limit for large files
- Read only what's needed for the task

**Writing**:
- Don't re-read files you just wrote
- Trust Write/Edit tool success messages
- Avoid unnecessary verification reads

### Tool Selection: Use `gh` CLI Instead of GitHub MCP

**GitHub MCP Cost**: 26 tools × ~700 tokens = ~18k tokens loaded every session

**Alternative**: `gh` CLI via Bash tool (0 token overhead)

✅ **Do** (0 MCP tokens):
```bash
# Create PR
gh pr create --title "feat: Add feature" --body "Description"

# List issues
gh issue list --label bug --state open

# Get PR status
gh pr view 123 --json state,checks

# Create branch
gh repo clone owner/repo && git checkout -b feature

# Merge PR
gh pr merge 123 --squash
```

❌ **Don't** (loads 26 tools, 18k tokens):
```python
mcp__github__create_pull_request(...)  # Wastes tokens
mcp__github__list_issues(...)
mcp__github__get_pull_request_status(...)
```

**When MCP is Better**:
- Rare cases where structured JSON output is critical
- Multi-file operations that `gh` doesn't support well

**Token Savings**: ~18k tokens (9% of budget) per session

### Command Execution

**Bash**:
- Pipe to `head -20` for previews
- Use `grep` to filter output
- Combine related commands (fewer tool calls)

**Tests**:
- Run specific tests, not full suites
- Filter output to failures only
- Use `-q` (quiet) mode when appropriate

### Communication

**Explanations**:
- Be concise but clear
- Use bullet points over paragraphs
- Save detailed docs to files, not responses

**Code Examples**:
- Show diffs, not full files
- Use "..." to indicate omitted sections
- Reference line numbers instead of quoting

## Emergency Compaction Protocol

### When: 80%+ Usage

**Immediate Actions**:

1. **Complete Current Task** (if <5 min):
   ```
   🚨 Context at 85% - Completing current task then compacting
   ```

2. **Save State**:
   - Commit all changes
   - Update memory.md with progress
   - Note next steps clearly

3. **Inform User**:
   ```
   🚨 Emergency: Context at 85% (170k/200k)

   Action: Use /compact to reset conversation

   Progress saved:
   - All changes committed
   - Memory updated with next steps
   - Ready to continue after compaction
   ```

4. **User Decision**:
   - Wait for user to run `/compact`
   - OR continue with extreme caution (thinking disabled, minimal output)

## Context Estimation (When No System Reminder)

**Rough estimates**:
- Average response: ~1-2k tokens
- File read (500 lines): ~3-5k tokens
- Bash output (full): ~2-4k tokens
- Thinking block (long): ~1-3k tokens

**Track mentally**:
- Start of session: ~5-10k (system prompts)
- Every 10 responses: +10-20k
- Each file read: +3-5k
- Each command: +2-4k

**Alert at estimated**:
- 20 responses = ~40-50k (check status)
- 40 responses = ~80-100k (enable cleanup)
- 60 responses = ~120-150k (aggressive cleanup)

## Success Metrics

**Target**: Maintain <50% context throughout session

**Measurements**:
- Check token usage every 10-15 minutes
- Alert user proactively at thresholds
- Optimize without disrupting flow
- Only suggest /compact as last resort

**Good Session**:
- Never exceeded 60%
- Used incremental strategies
- Completed 2+ hours of work
- No forced interruptions

**Excellent Session**:
- Stayed under 50% entire time
- Thinking mode toggled strategically
- Selective reads and filtered outputs
- User didn't notice optimization

## Example Workflow

### Beginning of Session (10k tokens)
```
✅ Context healthy at 5% (10k/200k)
Proceeding with normal operation
```

### After 15 Minutes (45k tokens)
```
✅ Context at 22% (45k/200k) - All good
Continuing with full thinking enabled
```

### After 30 Minutes (85k tokens)
```
🟡 Context at 42% (85k/200k)

Optimization enabled:
- Thinking mode: disabled for routine tasks
- File reading: selective with grep
- Command output: filtered to essentials

Continuing work...
```

### After 45 Minutes (110k tokens)
```
🟠 Context at 55% (110k/200k)

Active cleanup:
- Thinking: disabled except complex tasks
- Memory: pruned old sessions
- Outputs: summaries only

Recommend completing current task (RAG integration)
then starting fresh session. ETA: 10 minutes.
```

### Task Complete (120k tokens)
```
🟠 Context at 60% (120k/200k)

Task complete! Recommend:
1. Commit all work ✅
2. Update memory ✅
3. Start fresh session for next task

Type /end to close this session cleanly.
```

## Anti-Patterns to Avoid

❌ **Don't**:
- Read entire files when you need 10 lines
- Show full bash output when summary works
- Keep thinking enabled for simple tasks
- Quote large sections in responses
- Re-read files you just wrote

✅ **Do**:
- Use grep/search to find, then read selectively
- Filter outputs with head/tail/grep
- Toggle thinking mode based on task complexity
- Reference files by path:line instead of quoting
- Trust tool success without verification

## Integration with Other Skills

**Works with**:
- `verification-before-completion`: Verify efficiently (selective reads)
- `test-driven-development`: Run specific tests, not full suite
- `systematic-debugging`: Use targeted investigation, not broad searches
- `brainstorming`: Disable thinking for idea capture
- `writing-plans`: Save detailed plans to files, not responses

**Complements**:
- USS /end command: Clean session wrap-up
- Memory rotation: Auto-archive when >500 lines
- Session logs: Details in logs, summaries in responses

---

**Remember**: The best context management is invisible to the user. Optimize continuously, alert proactively, and only disrupt when absolutely necessary.
