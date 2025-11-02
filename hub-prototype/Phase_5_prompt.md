# CommandCenter Hub — Phase 5 Federation + Registry Feed + Metrics

You’re in `/Users/danielconnolly/Projects/CommandCenter/hub-prototype`.

---

## 🧩 1. Extract & install
```bash
tar -xzf CommandCenter-Hub-Phase5-bundle.tar.gz
pnpm add -D tsx
pnpm add nats dotenv
```

---

## 🧰 2. Apply Phase 5 scripts
```bash
pnpm tsx ./scripts/apply-phase5-scripts.ts
```
➡ Expect `✅ Added Phase5 scripts`

---

## 🧭 3. Start NATS (if not running)
```bash
pnpm -C hub nats:up
export NATS_URL=nats://127.0.0.1:4222
```

---

## 🚀 4. Launch federation bridge
```bash
pnpm -C hub federate
```
Console → `🌐 Federation bridge active (mesh.hub.hub-prototype.*)`

---

## 🔁 5. Run registry feed & metrics
```bash
pnpm -C hub registry-feed &
pnpm -C hub metrics &
```

---

## 📡 6. Emit MRKTZR events (via mockBus)
```bash
pnpm -C hub test-events --project mrktzr
```

---

## 📊 7. Observe
| Component | What You See |
|------------|--------------|
| Federation | `↗️ federated mesh.hub.hub-prototype.project.mrktzr.startup` |
| Registry Feed | `🔄 registry update broadcast` |
| Metrics | JSON lines → `snapshots/hub/metrics.log` |

---

## 🧾 8. Validate schema
```bash
npx ajv-cli@5 validate --spec=draft2020 --strict=false \
  -s schemas/registry-feed.schema.json -d snapshots/hub/metrics.log
```

---

## 🧠 9. Run demos
```bash
pnpm -C hub demo-federation
pnpm -C hub demo-registry-feed
pnpm -C hub demo-metrics
```

---

## ✅ 10. Commit snapshot
```bash
git add snapshots/hub/metrics.log
git commit -m "Enable Phase 5 federation, registry feed, and metrics"
```

After execution, your hub will:
- Broadcast local tool/project updates (incl. MRKTZR) over NATS subjects.
- Maintain a live registry feed for cross-hub synchronization.
- Continuously publish metrics for CommandCenter observability.
