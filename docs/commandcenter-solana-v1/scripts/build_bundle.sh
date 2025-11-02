#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="commandcenter-solana-v1.bundle.tar.gz"
echo "📦 Building $OUT ..."
tar -czf "$OUT" -C "$ROOT" .
echo "✅ Wrote $OUT"
