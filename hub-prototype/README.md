# CommandCenter — Hub Prototype v1

A lightweight **local-only** hub that discovers tools, simulates a Mesh‑Bus, exposes a minimal web console (Next.js 14 + Tailwind), and ships CLI helpers.

> **Requirements**: Node 20+, PNPM. No external APIs. Local files only.

## Quick Start

```bash
# 1) From this folder
pnpm install

# 2) Start the Hub core (registry, mock-bus, JSON-RPC, audit logging)
pnpm hub:dev

# 3) In another terminal, start the web console
pnpm console:dev

# 4) Discover/refresh tools (rebuild registry)
pnpm hub:refresh

# 5) Useful CLI
pnpm hub:list
pnpm hub:events
pnpm hub:open example-tool
```

The hub persists:
- Tool registry → `snapshots/hub/tool-registry.json`
- Events (JSONL) → `snapshots/hub/events/YYYYMMDD/HH.*.jsonl`
- Audit logs → `snapshots/hub/audit/YYYY/MM/DD/hub.log`

## Layout

```
CommandCenter-Hub-Prototype-v1/
  hub/                     # TypeScript hub core (registry + mock-bus + CLI bindings + JSON-RPC)
  hub-console/             # Next.js 14 console (lists tools, health, and recent events)
  tools/
    example-tool/          # Example tool with manifest.json
  snapshots/
    hub/
      events/              # JSONL event streams per day
      audit/               # Hub audit logs per day
      tool-registry.json   # Built by hub:refresh
  ai/                      # ToolOps stub (reads fixtures/snapshots -> recommendations.json)
  fixtures/                # Reuse Validation‑Seed fixtures here if needed
  .cc/schemas/             # Seed schemas (copy from Validation‑Seed as desired)
```
> Replace `CommandCenter-Hub-Prototype-v1` with the folder name you extracted.

## JSON‑RPC 2.0 Bridge

Hub starts an HTTP JSON‑RPC endpoint on `http://127.0.0.1:5055/rpc`. Methods:
- `bus.publish` → `{{ topic, payload }}` (writes JSONL event; topic must be `tools.<id>.*`)
- `bus.health` → returns uptime & event counters

### cURL example

```bash
curl -s http://127.0.0.1:5055/rpc -H 'content-type: application/json' -d '
{{ "jsonrpc":"2.0","id":1,"method":"bus.publish","params":{{"topic":"tools.example-tool.started","payload":{{"pid":1234}}}} }}'
```

## NATS‑style Topic Namespace (Mock)

Topics are simple dotted strings; subscribe/route by prefix. Events are persisted to JSONL for replay.

## Dagger (stubs)

- Per‑tool `Daggerfile` (example provided).
- Global orchestrator `hub.dagger.yaml` to run `build-all-tools` (stub wired to `hub/bin/build-all-tools.js`).

## AI Assist (ToolOps)

- `ai/ToolOps.ts` reads `fixtures/snapshots` and `snapshots` and emits `ai/recommendations.json` locally.

## Scripts

- `hub:dev` — runs the hub with JSON‑RPC and file watchers
- `hub:refresh` — scans `tools/*/manifest.json` and rebuilds `snapshots/hub/tool-registry.json`
- `hub:list` — prints registered tools
- `hub:open <id>` — opens the tool `web` or `api` endpoint (prints URL; does not launch a browser)
- `hub:events` — tails live event JSONL

---

© 2025 CommandCenter (local prototype).
