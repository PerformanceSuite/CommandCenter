# 🧩 CommandCenter Hub — Phase 2 & 3 Setup & Validation

Context:
You are inside `/Users/danielconnolly/Projects/CommandCenter/hub-prototype`.
The bundle `CommandCenter-Hub-Phase2-3-bundle.tar.gz` has been extracted here.
The goal is to finalize Phase 2 (Event Origin + Correlation Tracking) and Phase 3 (Event Streamer + Mesh Replay Service).

---

## 🪄 Tasks for Codex

1. **Install `tsx` locally**
   ```bash
   pnpm add -D tsx
   ```

2. **Apply the Phase 2-3 scripts into `hub/package.json`**
   ```bash
   pnpm tsx ./scripts/apply-scripts.ts
   ```

3. **Verify snapshot directory & create `events.log`**
   ```bash
   pnpm -C hub verify || pnpm hub:verify || bash ./scripts/verify-snapshots.sh
   ```

4. **Emit test events (Phase 2 validation)**
   ```bash
   pnpm -C hub test-events || pnpm hub:test-events
   ```

5. **Inspect persisted log**
   ```bash
   cat snapshots/hub/events.log | jq .
   ```

6. **Run live stream demo (Phase 3 validation)**
   ```bash
   pnpm -C hub stream-demo || pnpm hub:stream-demo
   ```

7. **Run replay demo (Phase 3 temporal replay)**
   ```bash
   pnpm -C hub replay-demo || pnpm hub:replay-demo
   ```

8. **Run CLI filter checks (back-compatibility)**
   ```bash
   pnpm -C hub events -- --project veria
   pnpm -C hub events -- --tool graph-service
   ```

9. **Confirm expected outputs**
   - `✅ Snapshot directories verified`
   - JSON events appended under `snapshots/hub/events.log`
   - “📡 live: …” appears from `stream-demo`
   - “⏮ replay: …” from `replay-demo`
   - Filtered events visible with CLI

10. **Commit snapshot verification**
    ```bash
    git add snapshots/hub/events.log
    git commit -m "Add Phase2-3 event persistence and streamer validation"
    ```

---

## 🎯 Goal
After completing all steps, you should have:
- Working origin + correlation IDs
- Persistent `events.log`
- Functional live event stream
- Replay by timestamp
- CLI filters for `--project` / `--tool`

Once this is confirmed, proceed to **Phase 4 — Mesh-Bus Adapter + NATS Bridge** (integration with CommandCenter Mesh Bus).

---

✅ *Codex should execute each command sequentially, verify results at each stage, and ensure no missing dependencies before moving to Phase 4.*
