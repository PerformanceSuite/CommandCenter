#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
echo "🚀 Deploying Solana module to CommandCenter (local layout assumed)"
echo "• Copy or link adapter into your CommandCenter integrations dir"
echo "• Configure env via config/commandcenter_solana.env"
echo "• Start adapter with:  MESH_BUS_URL=http://localhost:7700/jsonrpc \
    python3 integration/solana_veria_adapter.py"
