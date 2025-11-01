#!/usr/bin/env python3
"""
Solana → CommandCenter Adapter
- Streams Solana events and forwards to Mesh-Bus (NATS/HTTP JSON-RPC).
- Reads RPC pool and agent config from ./integration/solana_rpcs_config.json
"""
import asyncio, json, os, sys, time, signal
import websockets
import requests

RPC_CONFIG = os.path.join(os.path.dirname(__file__), "solana_rpcs_config.json")
MESH_BUS_URL = os.environ.get("MESH_BUS_URL", "http://localhost:7700/jsonrpc")
STREAM_PROGRAM_IDS = os.environ.get("STREAM_PROGRAM_IDS", "").split(",") if os.environ.get("STREAM_PROGRAM_IDS") else []

def load_rpcs():
    with open(RPC_CONFIG, "r") as f:
        data = json.load(f)
    return data.get("endpoints", [])

async def subscribe(ws_url, sub_body):
    async with websockets.connect(ws_url, max_queue=None, ping_interval=20) as ws:
        await ws.send(json.dumps(sub_body))
        sub_reply = await ws.recv()
        print("[ws] subscription reply:", sub_reply)
        while True:
            msg = await ws.recv()
            yield json.loads(msg)

def mesh_emit(subject, payload):
    # Generic JSON-RPC emit to Mesh-Bus (replace with NATS client if desired)
    try:
        req = {
            "jsonrpc": "2.0",
            "id": int(time.time()*1000),
            "method": "mesh.emit",
            "params": {"subject": subject, "data": payload},
        }
        requests.post(MESH_BUS_URL, json=req, timeout=3)
    except Exception as e:
        print("[mesh] emit error:", e, file=sys.stderr)

async def stream_loop(rpc):
    ws_url = rpc.get("ws")
    http_url = rpc.get("http")
    if not ws_url or not http_url:
        print("[cfg] missing ws/http in rpc entry:", rpc, file=sys.stderr)
        return

    # Subscribe to logs and account events
    base_logs = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "logsSubscribe",
        "params": [{"mentions": [pid for pid in STREAM_PROGRAM_IDS if pid]}, {"commitment":"confirmed"}],
    }
    base_sig  = {
        "jsonrpc":"2.0",
        "id":2,
        "method":"signatureSubscribe",
        "params":["*","confirmed"]
    }

    try:
        async for event in subscribe(ws_url, base_logs):
            ev = {
                "rpc": http_url,
                "type": "logs",
                "commitment": "confirmed",
                "event": event,
                "ts": time.time()
            }
            mesh_emit("solana.logs", ev)
    except Exception as e:
        print("[ws] stream_loop error:", e, file=sys.stderr)

async def main():
    rpcs = load_rpcs()
    if not rpcs:
        print("[cfg] no RPC endpoints configured")
        sys.exit(1)
    tasks = [asyncio.create_task(stream_loop(rpc)) for rpc in rpcs]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    asyncio.run(main())
