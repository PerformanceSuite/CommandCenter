# Solana Integration Plan (CommandCenter → Veria)

## 0) Objectives
- Stream authoritative Solana events into the CommandCenter event fabric.
- Normalize into Veria’s compliance schema (entities, obligations, violations, attestations).
- Provide operability: health, latency, and failover across multiple RPCs.

## 1) RPC strategy
- **Start** with a multi‑endpoint pool (e.g., Helius / Triton / Anza / public).
- **Later**: self‑hosted validator/RPC for high‑assurance workloads.
- Health checks: JSON‑RPC echo, `getHealth`, block height drift, slot commitment, p95 latency.

## 2) Adapter (this bundle)
- Consumes WebSocket subscriptions (logs, signatures, account changes).
- Emits canonical events to Mesh‑Bus (subject: `solana.*`).
- Converts commitment to `observed_finality={processed|confirmed|finalized}`.
- Optional: program filters for specific compliance‑relevant programs.

## 3) Agents
- **solana-monitor**: detect latency anomalies, finality stalls, unusual transfer patterns,
  and program‑specific rule violations (configurable).

## 4) Roadmap
- **R1**: Streams + health + baseline rules.
- **R2**: On‑chain attestation programs for RegTech workflows.
- **R3**: Agentic orchestration (AI actors placing/verifying on‑chain escrows) with guardrails.
