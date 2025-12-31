# Session Wrap Command

When context is running low, use this command to preserve session state.

## What to do:

1. **Create a session summary file** at `.claude/sessions/YYYY-MM-DD-HH-MM-summary.md` containing:
   - What was accomplished this session
   - Key decisions made
   - Current state of work
   - Immediate next steps
   - Any open questions or blockers

2. **Stage and commit all changes** with a detailed commit message that includes:
   - Summary of changes
   - Session context (what problem we were solving)
   - Where we left off
   - Next steps in the commit body

3. **Output the resume command** for the user:
   ```
   To resume: claude --continue or start new session and say "review last commit"
   ```

## Commit message format:

```
<type>(<scope>): <summary>

Session: <brief description of what we were working on>

## Accomplished
- <item 1>
- <item 2>

## Decisions Made
- <decision 1>
- <decision 2>

## Next Steps
- <next step 1>
- <next step 2>

## Resume Context
<paragraph explaining where we left off and what to do next>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## On Resume ("review last commit"):

When user says "review last commit" or "continue from last session":
1. Run `git log -1 --format=full` to read the last commit
2. Check for session summary in `.claude/sessions/`
3. Read any referenced files/plans
4. Summarize context back to user and ask how to proceed
