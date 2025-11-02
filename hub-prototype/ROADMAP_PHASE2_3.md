# CommandCenter Hub — Phases 2 & 3
**Event Origin · Correlation Tracking · Event Streamer · Mesh Replay Service**

## 🎯 Objectives
1. **Phase 2** — Add `origin` + `correlationId` to events, persist & replay.
2. **Phase 3** — Add live `EventStreamer` + replay service compatible with Mesh‑Bus.

---

## 🚀 Getting Started (Codex‑friendly)
```bash
cd /Users/danielconnolly/Projects/CommandCenter/hub-prototype
# Extract bundle contents into hub-prototype/
tar -xzf CommandCenter-Hub-Phase2-3-bundle.tar.gz

# Ensure snapshots folder + events.log exist
pnpm -C hub verify || pnpm hub:verify || bash ./scripts/verify-snapshots.sh

# Apply scripts into hub/package.json (adds hub:verify, hub:test-events, hub:stream-demo, hub:replay-demo)
pnpm tsx ./scripts/apply-scripts.ts

# Emit a couple events and verify persistence
pnpm -C hub test-events || pnpm hub:test-events

# Stream live (Phase 3 demo)
pnpm -C hub stream-demo || pnpm hub:stream-demo

# Replay recent (Phase 3 demo)
pnpm -C hub replay-demo || pnpm hub:replay-demo

# Filtered event view via CLI (overwrites or complements existing hub/src/cli.ts)
pnpm -C hub events -- --project veria
pnpm -C hub events -- --tool graph-service
```

> If `pnpm -C hub <script>` doesn’t work on your machine, try running the right‑side command (after `||`) or execute the script directly with `tsx`/`node` from the repository root.

---

## 🧩 Phase 2 Implementation
- `src/hub/mockBus.ts` → origin metadata & correlationId
- Events persist under `snapshots/hub/events.log`
- `schemas/event.schema.json` (draft2020)
- CLI filters: `--project` or `--tool`

### Validate schema
```bash
npx ajv-cli@5 validate --spec=draft2020 --strict=false   -s schemas/event.schema.json -d "fixtures/*.json"
```

> Note: `ajv` may warn about `"format": "uuid"`; this is safe to ignore unless you add a custom format validator.

---

## ⚙️ Phase 3 — Event Streamer + Mesh Replay Service
### Goals
- Real‑time subscriptions to append‑only `events.log`
- Temporal replay by time range
- Parity with future Mesh‑Bus (NATS) via adapter

### Components
| File | Purpose |
|------|---------|
| `src/hub/eventStreamer.ts` | Watches `events.log` and emits `'event'` for new lines |
| `scripts/stream-demo.ts`   | Demonstrates live stream usage |
| `scripts/replay-demo.ts`   | Demonstrates replay by time range |
| `src/hub/cli.ts`           | Filtered replay and tailing (backward‑compatible) |

### Future hooks
- Plug into NATS or real Mesh‑Bus via adapter layer
- `hub:replay --since <timestamp>` / `--until`
- Log rotation & retention policy (size‑ and time‑based)

---

## 🧰 Scripts Auto‑Install
Run once to auto‑insert scripts into `hub/package.json`:
```bash
pnpm tsx ./scripts/apply-scripts.ts
```

Scripts inserted (idempotent):
```json
{
  "hub:verify": "bash ../scripts/verify-snapshots.sh",
  "hub:test-events": "tsx ../scripts/test-events.ts",
  "hub:stream-demo": "tsx ../scripts/stream-demo.ts",
  "hub:replay-demo": "tsx ../scripts/replay-demo.ts"
}
```

---

## ✅ Validation Checklist
| Step | Command | Expected |
|------|---------|----------|
| Verify dirs | `pnpm -C hub verify` or `pnpm hub:verify` | `events.log` exists |
| Emit events | `pnpm -C hub test-events` | JSON appended |
| Stream live | `pnpm -C hub stream-demo` | live feed printed |
| Replay recent | `pnpm -C hub replay-demo` | prints recent events |
| Filter view | `pnpm -C hub events -- --project veria` | subset displayed |

---

## 🧭 Notes
- This bundle is **minimal‑deps** and consistent with the Phase‑1 prototype.
- `src/hub/cli.ts` here is drop‑in; if you have a customized CLI already, merge the filter logic.
