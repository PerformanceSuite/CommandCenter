#!/bin/bash
cd /Users/danielconnolly/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows
/Users/danielconnolly/.local/bin/uv run obox https://github.com/dconnolly-slalom/CommandCenter \
  --prompt "Add docstring to create_app function in backend/app/main.py. Commit and push." \
  --branch main \
  --model sonnet \
  --max-turns 30
