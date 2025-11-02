#!/usr/bin/env bash
set -euo pipefail

POLICY=".cc/validation-policy.json"
SCHEMAS="schemas"
FIXTURES="fixtures"

if ! command -v npx >/dev/null; then
  echo "❌ npx not found. Please install Node.js ≥18." >&2
  exit 1
fi
if ! command -v jq >/dev/null; then
  echo "❌ jq not found. Please install jq." >&2
  exit 1
fi

jq -e . "$POLICY" >/dev/null || { echo "Missing $POLICY"; exit 1; }

NOW_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
ENFORCE_DATE="$(jq -r '.enforceOnOrAfter' "$POLICY")"

PHASE_EVENTS="$(jq -r '.phases.events' "$POLICY")"
PHASE_MANIFESTS="$(jq -r '.phases.manifests' "$POLICY")"
PHASE_SNAPSHOTS="$(jq -r '.phases.snapshots' "$POLICY")"

MIN_EVENTS="$(jq -r '.minimums["fixtures.events"]' "$POLICY")"
MIN_MANIFESTS="$(jq -r '.minimums["tools.manifests"]' "$POLICY")"
MIN_SNAPSHOTS="$(jq -r '.minimums["snapshots.files"]' "$POLICY")"

mode_for () {
  local phase="$1"
  if [[ "$NOW_UTC" < "$ENFORCE_DATE" ]]; then
    [[ "$phase" == "events" ]] && echo "enforce" || echo "$PHASE_MANIFESTS"
  else
    echo "enforce"
  fi
}

MODE_EVENTS="enforce"
MODE_MANIFESTS="$(mode_for manifests)"
MODE_SNAPSHOTS="$(mode_for snapshots)"

echo "🕒 Now: $NOW_UTC  |  Enforce on/after: $ENFORCE_DATE"
echo "🔧 Modes → events:$MODE_EVENTS manifests:$MODE_MANIFESTS snapshots:$MODE_SNAPSHOTS"
echo

# 1) Events
EVENT_COUNT=$(ls -1 "$FIXTURES"/*.json 2>/dev/null | wc -l | xargs)
if (( EVENT_COUNT < MIN_EVENTS )); then
  echo "❌ Need at least $MIN_EVENTS event fixtures (have $EVENT_COUNT)."
  exit 1
fi
npx ajv validate -s "$SCHEMAS/event.schema.json" -d "$FIXTURES"/*.json --strict=false --errors=text
echo "✅ Events validated ($EVENT_COUNT files)."
echo

# 2) Manifests
MANIFEST_FILES=( $(ls -1 tools/*/manifest.json 2>/dev/null || true) )
MANIFEST_COUNT=${#MANIFEST_FILES[@]}
if (( MANIFEST_COUNT < MIN_MANIFESTS )); then
  if [[ "$MODE_MANIFESTS" == "enforce" ]]; then
    echo "❌ Need at least $MIN_MANIFESTS tool manifest(s) (have $MANIFEST_COUNT)."
    exit 1
  else
    echo "⚠️  Warning: No tool manifests yet. Will be enforced after $ENFORCE_DATE."
  fi
else
  npx ajv validate -s "$SCHEMAS/manifest.schema.json" -d "tools/*/manifest.json" --strict=false --errors=text
  if grep -R "\"id\": \"REPLACE_ME\"" tools >/dev/null 2>&1 || [[ -d tools/_TEMPLATE_ ]]; then
    if [[ "$MODE_MANIFESTS" == "enforce" ]]; then
      echo "❌ Replace template manifest and remove tools/_TEMPLATE_."
      exit 1
    else
      echo "⚠️  Template manifest present; will fail after $ENFORCE_DATE."
    fi
  else
    echo "✅ Manifests validated ($MANIFEST_COUNT)."
  fi
fi
echo

# 3) Snapshots
SNAPSHOT_COUNT=$(ls -1 snapshots/**/*.json 2>/dev/null | wc -l | xargs || echo 0)
if [[ "$SNAPSHOT_COUNT" == "" ]]; then SNAPSHOT_COUNT=0; fi

if (( SNAPSHOT_COUNT < MIN_SNAPSHOTS )); then
  if [[ "$MODE_SNAPSHOTS" == "enforce" ]]; then
    echo "❌ Need at least $MIN_SNAPSHOTS snapshot JSON (have $SNAPSHOT_COUNT)."
    exit 1
  else
    echo "⚠️  No snapshot JSONs yet. Will be enforced after $ENFORCE_DATE."
  fi
else
  npx ajv validate -s "$SCHEMAS/snapshot.schema.json" -d snapshots/**/*.json --strict=false --errors=text
  echo "✅ Snapshots validated ($SNAPSHOT_COUNT)."
fi

echo
echo "🎉 cc-ci-gate checks complete."
