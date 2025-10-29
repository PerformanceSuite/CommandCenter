---
name: init-project
description: Initialize project with Universal Session System v2.1
---

When the user types /init-project, perform these actions:

1. Say "🚀 Initializing project with Universal Session System v2.1..."

2. Check if already initialized:
   - Look for `.claude/memory.md`
   - If exists, ask: "Project already initialized. Reinitialize? (will backup existing)"

3. Run the initialization script:
   ```bash
   /Users/danielconnolly/Projects/universal-session-system/init.sh
   ```

4. Show what was created:
   - ✅ 5-document structure (PROJECT, ROADMAP, TECHNICAL, CURRENT_SESSION, memory)
   - ✅ Memory rotation at 500 lines
   - ✅ Smart cleanup for your project type
   - ✅ Repository hygiene checks
   - ✅ Session tracking
   - ✅ Mandatory skills invocation (/start: using-superpowers, context-management)
   - ✅ Cleanup skills invocation (/end: repository-hygiene)

5. Report: "✅ Project initialized! Use /start to begin work and /end to finish."

**USS v2.1 Features:**
- Superpowers integration enforced at every session start
- Context management optimizations (MCP disabling, thinking mode control)
- Repository hygiene enforced at session end
- Memory rotation prevents token overflow
- Smart cleanup adapts to project type
