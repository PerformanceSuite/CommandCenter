#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SNAP_DIR="$ROOT_DIR/snapshots/hub"
EVENTS_PATH="$SNAP_DIR/events.log"

echo "📁 Verifying hub snapshot directories..."
mkdir -p "$SNAP_DIR"
touch "$EVENTS_PATH"

if [ -d "$SNAP_DIR" ] && [ -f "$EVENTS_PATH" ]; then
  echo "✅ Snapshot directories verified: $SNAP_DIR"
else
  echo "❌ Failed to verify snapshot directory."
  exit 1
fi
