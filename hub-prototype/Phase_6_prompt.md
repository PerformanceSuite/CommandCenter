CommandCenter Hub Phase 6 (Mesh-Service + Heartbeat)**

 **CommandCenter Hub — Phase 6: Mesh-Service Integration + Hub Discovery Heartbeat**.

Your task is to install, link, and validate the Phase 6 bundle in the local prototype at:
`/Users/danielconnolly/Projects/CommandCenter/hub-prototype`

---

#### Steps to perform

```bash
# 1️⃣  Enter the CommandCenter hub prototype directory
cd /Users/danielconnolly/Projects/CommandCenter/hub-prototype

# 2️⃣  Unpack the Phase 6 bundle
tar -xzf CommandCenter-Hub-Phase6-bundle.tar.gz

# 3️⃣  Merge new folders (src/, scripts/, schemas/, docs/) into repo root
# (If your package.json lives under hub/, keep bundle at root; the script detects this automatically)

# 4️⃣  Apply Phase 6 scripts & dependencies
pnpm tsx ./scripts/apply-phase6-scripts.ts
pnpm install

# 5️⃣  Start the heartbeat publisher (presence + health)
export HUB_ID=local-hub
export NATS_URL="nats://127.0.0.1:4222"
pnpm hub:heartbeat
```

Then open two more terminals in the same directory:

```bash
# Terminal 2 — watch live presence
pnpm hub:presence

# Terminal 3 — watch health summaries
pnpm hub:health
```

---

#### Validation checklist

✅ Presence messages appear on `hub.presence.<hubId>` every ~3 s
✅ Health summaries appear on `hub.health.<hubId>` every ~15 s
✅ If you restart NATS (`brew services restart nats` or your method), both publishers recover automatically
✅ `hub:presence` shows active hubs and prunes stale ones after ~12 s

---

*(Optional)* To validate schema integrity with AJV once presence/health fixtures are captured:

```bash
npx ajv-cli@5 validate --spec=draft2020 -s schemas/presence.schema.json -d fixtures/presence*.json
npx ajv-cli@5 validate --spec=draft2020 -s schemas/health.schema.json -d fixtures/health*.json
```

---
