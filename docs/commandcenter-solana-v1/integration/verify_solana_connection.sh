#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="$HERE/solana_rpcs_config.json"

echo "🔍 Verifying Solana RPC connectivity..."
jq -r '.endpoints[] | "\(.name) \(.http) \(.ws)"' "$CFG" | while read -r name http ws; do
  echo "• $name → $http"
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H 'Content-Type: application/json'     --data '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' "$http" || true)
  echo "  HTTP getHealth status: $code"
done
echo "✅ Verification complete"
