#!/usr/bin/env bash
set -euo pipefail
: "${GOOGLE_API_KEY:?Set GOOGLE_API_KEY}"
MODEL=${MODEL:-gemini-1.5-pro}
PROMPT=${1:-"Hello from curl"}

curl -sS \
  -H 'Content-Type: application/json' \
  -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${GOOGLE_API_KEY}" \
  -d @<(cat <<JSON
{ "contents": [{"role": "user", "parts": [{"text": ${PROMPT@Q}}]}] }
JSON
) | jq
