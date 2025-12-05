# Shared Infrastructure Plan

- **Orchestration**: Dagger Hub manages tenant-scoped CC & MR instances (ports, volumes, secrets).
- **Message Bus**: NATS (JetStream) for async eventing; HTTP for control plane.
- **Observability**: Prometheus/Grafana with shared labels; OTel traces with W3C headers.
- **SLOs**: freshness <24h (99%); publish success >99.5%; e2e latency <2h (95%) for daily cadence.
