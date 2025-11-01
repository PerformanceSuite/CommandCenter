# CommandCenter × Solana — v1

This bundle integrates Solana as the high‑speed **execution layer** within CommandCenter,
routing on‑chain signals into Veria’s compliance and monitoring stack.

## What's inside
- `integration/solana_blueprint.md` — product/architectural positioning
- `integration/solana_integration_plan.md` — end‑to‑end integration steps & roadmap
- `integration/solana_veria_adapter.py` — event bridge to Mesh‑Bus / TaskGraph
- `integration/solana_monitoring_agent.yaml` — baseline agent definition
- `integration/solana_rpcs_config.json` — example multi‑RPC config
- `integration/verify_solana_connection.sh` — RPC health+throughput probe
- `docs/` — overview, architecture diagram, AI convergence, regulatory framework
- `scripts/` — helper scripts to deploy/upgrade
- `config/` — env templates and endpoint lists

## Quickstart
```bash
cd commandcenter-solana-v1
./integration/verify_solana_connection.sh
./scripts/deploy_to_commandcenter.sh
```

## Requirements
- Python 3.10+
- `websockets`, `requests` (for adapter)
- Access to at least one Solana RPC (public or private)
