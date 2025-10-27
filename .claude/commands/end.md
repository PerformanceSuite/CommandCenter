---
name: end
description: End work session with complete cleanup and documentation
---

When the user types /end, perform these actions:

**FIRST: Invoke Repository Hygiene Skill** (MANDATORY)
- Use Skill tool to invoke: `repository-hygiene`
- This ensures proper cleanup practices are followed
- WAIT for skill to load before proceeding

1. **Session Timestamp**:
   - Say "🏁 Ending development session at [timestamp]..."
   - Note session duration if /start was used

2. **Run Smart Cleanup**:
   - Execute `.claude/cleanup.sh` if it exists
   - Clean project-specific artifacts based on detected type:
     - Node: node_modules/.cache, .next, dist
     - Python: __pycache__, .pytest_cache, *.pyc
     - Rust: target/debug, target/release
     - Go: go build cache
   - Remove OS artifacts (.DS_Store, Thumbs.db, *~)
   - Report what was cleaned

3. **Repository Hygiene Audit**:
   ```
   =================== Repository Hygiene Check ===================
   ```
   - Check for debug statements:
     - JavaScript/TypeScript: console.log, console.debug, debugger
     - Python: print() statements, breakpoint()
     - Go: fmt.Println in non-main files
   - Scan for potential secrets:
     - Patterns: api_key, password, token, secret, private_key
     - AWS/GCP/Azure credentials
   - Verify .env files are gitignored
   - Find TODOs without issue numbers
   - Check for uncommitted changes
   - Report all findings in a structured format

4. **Memory Management with Rotation**:
   - Check `.claude/memory.md` size
   - If > 2000 lines:
     - Archive to `.claude/memory_archive_[date].md`
     - Keep last 500 lines in active memory
   - Add session summary with:
     ```
     ## Session: [date and time]
     **Duration**: [if available]
     **Branch**: [current git branch]

     ### Work Completed:
     - [bullet points]

     ### Key Decisions:
     - [if any]

     ### Blockers/Issues:
     - [if any]

     ### Next Steps:
     - [priorities for next session]
     ```

5. **Create Session Log**:
   - Save to `.claude/logs/sessions/[timestamp].md`
   - Include full hygiene report, git status, work summary

6. **Update Core Documentation** (if docs exist):
   - Update `docs/PROJECT.md` status section
   - Clear `docs/CURRENT_SESSION.md`
   - Update progress in `docs/ROADMAP.md` if applicable

7. **Git Status Summary**:
   ```
   =================== Git Status ===================
   Branch: [branch name]
   Modified: [count] files
   Untracked: [count] files
   Uncommitted changes: [list main files]
   ```

8. **Final Session Report**:
   ```
   =================== Session Summary ===================
   Duration: [time]
   Files Modified: [count]
   Lines Added/Removed: +[added] -[removed]

   Hygiene Score: [✅ Clean | ⚠️ Warnings | ❌ Critical]
   - Debug statements: [count or ✓]
   - Potential secrets: [count or ✓]
   - TODOs without issues: [count or ✓]

   Token Usage: [estimate] / 200k
   Memory Size: [lines] lines

   Next Priorities:
   1. [from memory/notes]
   2. [from memory/notes]
   ```

9. **Cleanup Complete**:
   - Report: "✅ Session ended successfully! Repository is [CLEAN/HAS WARNINGS]"
   - If warnings exist: "Run `git status` to review uncommitted changes"
   - Suggest: "Next session: Use /start to begin"

Note: This command consolidates ALL cleanup functionality into one place. No need for separate bash scripts or multiple cleanup systems.
