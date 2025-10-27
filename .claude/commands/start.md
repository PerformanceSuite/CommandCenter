---
name: start
description: Start a work session with smart context loading
---

When the user types /start, perform these actions:

**FIRST: Invoke Core Skills** (MANDATORY)
- Use Skill tool to invoke: `using-superpowers`
- Use Skill tool to invoke: `context-management`
- These establish mandatory workflows and optimization practices

**SECOND: Optimize MCP Servers** (AUTOMATIC - Context-Management Strategy 0)
- Read `~/.claude/mcp.json`
- Detect project type from codebase structure
- Autonomously disable unused MCPs:
  - Always disable: `brave-search` (redundant with WebSearch)
  - Backend projects: Disable `puppeteer`, `ide` (unless .ipynb files exist)
  - Use `gh` CLI instead of GitHub MCP tools (saves ~18k tokens/session)
- Write optimized config back to `~/.claude/mcp.json`
- Report: "🔧 MCP Optimization: Disabled X servers (saves ~Xk tokens)"
- Skip if mcp.json doesn't exist or no optimization needed

1. Say "🚀 Starting development session..."

2. **Load Current Context** (not full memory):
   - Read `docs/CURRENT_SESSION.md` if it exists (always < 1000 tokens)
   - If not found, read last 100 lines of `.claude/memory.md`
   - This prevents token overflow issues

3. **Show Project Status**:
   - Display key info from `docs/PROJECT.md` if it exists
   - Otherwise show git status and project structure

4. **Git Status**:
   - Current branch
   - Uncommitted changes (first 10 files)
   - Recent commits (last 3)

5. **Check for TODOs**:
   - Scan codebase for TODO/FIXME comments
   - Show first 5 found

6. **Memory Health Check**:
   - Check `.claude/memory.md` size
   - If > 500 lines, note that rotation will happen on /end
   - Remind about `search-convos` for older history

7. Report: "✅ Session started! Ready to work."

**Key improvements:**
- Reads CURRENT_SESSION.md first (small, current)
- Avoids reading huge memory files
- Shows memory health proactively
