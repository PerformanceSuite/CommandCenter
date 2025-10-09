#!/usr/bin/env bash
set -euo pipefail
PROMPT=${1:-"Hello from proxy"}

curl -sS http://localhost:4000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer dev_master_key_please_change' \
  -d @<(cat <<JSON
{ "model": "gpt-4o", "messages": [{"role":"user","content": ${PROMPT@Q}}] }
JSON
) | jq -r '.choices[0].message.content'
