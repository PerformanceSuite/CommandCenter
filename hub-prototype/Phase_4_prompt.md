# 🧩 CommandCenter Hub — Phase 4 + 4+ Setup

Context:
The bundle `CommandCenter-Hub-Phase4-bundle.tar.gz` is located in this directory.
The goal is to:
1️⃣  Install and configure the NATS Mesh-Bus bridge.
2️⃣  Verify event publishing/subscription.
3️⃣  Apply Phase 4+ upgrades for rotation + temporal replay CLI.

---

## 🧰 1. Extract and prepare
```bash
tar -xzf CommandCenter-Hub-Phase4-bundle.tar.gz
pnpm add -D tsx
pnpm add nats dotenv
```

---

## 🧩 2. Apply Phase 4 scripts
```bash
pnpm tsx ./scripts/apply-phase4-scripts.ts
```

Expected:
`✅ Updated hub/package.json with Phase 4 scripts.`

---

## 🧭 3. Start NATS locally (optional)
```bash
pnpm -C hub nats:up
sleep 3
```

> NATS UI → http://127.0.0.1:8222

---

## ⚙️ 4. Export environment variables
```bash
export NATS_URL=nats://127.0.0.1:4222
export PERSIST_INBOUND=true
```

---

## 🚉 5. Start the Mesh-Bus bridge
```bash
pnpm -C hub nats:bridge
```
Expected:
```
✅ NATS connected: ...
🚉 Bridge active: mockBus -> NATS. Emit local events to publish.
```

---

## 📡 6. In a second terminal, run subscriber demo
```bash
pnpm -C hub nats:subscribe-demo
```
Expected output:
```
👂 Subscribed to hub.>
📥 project veria 2025-... ...
```

---

## 🔁 7. Emit test events
```bash
pnpm -C hub test-events
```
Expected:
- Bridge console → `➡️ published hub.project.veria.startup`
- Subscriber console → `📥 project veria ...`

---

## 🧾 8. Confirm persistence
```bash
tail -n 5 snapshots/hub/events.log | jq .
```

---

## ⚙️ 9. Phase 4+ Enhancements (add now)

**Tasks:**
1. Add **rotation** in `src/hub/eventStreamer.ts`:
   - Create `rotateLogs()` function that moves `events.log` → `events-<timestamp>.log` when file > 5 MB.
   - Called each time after write in `mockBus.emit()`.

2. Add **temporal replay args** to `src/hub/cli.ts`:
   ```bash
   pnpm -C hub events -- --since "2025-11-01T00:00:00Z" --until "2025-11-02T00:00:00Z"
   ```
   Filter lines by `evt.timestamp` within that window.

3. Add script in `hub/package.json`:
   ```json
   "hub:rotate": "tsx ../scripts/rotate-logs.ts"
   ```
   and create `scripts/rotate-logs.ts`:
   ```ts
   import fs from "fs";
   import path from "path";
   const ROOT = path.resolve(process.cwd(), "..");
   const EVENTS_PATH = path.join(ROOT, "snapshots/hub/events.log");
   if (!fs.existsSync(EVENTS_PATH)) process.exit(0);
   const stats = fs.statSync(EVENTS_PATH);
   if (stats.size > 5 * 1024 * 1024) {
     const rotated = `${EVENTS_PATH.replace(".log", "")}-${Date.now()}.log`;
     fs.renameSync(EVENTS_PATH, rotated);
     fs.writeFileSync(EVENTS_PATH, "");
     console.log(`♻️  Rotated to ${rotated}`);
   } else {
     console.log("No rotation needed.");
   }
   ```

4. Run rotation test:
   ```bash
   pnpm -C hub rotate
   ```

5. Test new CLI window filters:
   ```bash
   pnpm -C hub events -- --since "$(date -v-1H -u +%FT%TZ)" --replay-only
   ```

---

## ✅ 10. Verify checklist
| Step | Result |
|------|---------|
| Bridge connects | ✅ |
| Subscriber prints events | ✅ |
| Events persisted | ✅ |
| Rotation works > 5 MB | ✅ |
| Temporal replay filters | ✅ |

---

## 🔮 Next milestone (Phase 5 preview)
- Replace local mockBus entirely with NATS subject emitters.
- Add “Hub Registry Feed” as NATS subject (`hub.registry.update`).
- Integrate with Veria + MRKTZR instances for global correlation tracing.
