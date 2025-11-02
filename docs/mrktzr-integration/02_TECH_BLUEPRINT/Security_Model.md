# Security Model

- **Isolation**: per-tenant encryption keys; distinct Postgres schemas; separate Docker volumes.
- **Auth**: Mutual mTLS between CC↔MR; OAuth2 client credentials for control plane (scoped per tenant).
- **Secrets**: SOPS- or Vault-managed; ephemeral runtime injection via Dagger.
- **SSRF/XSS**: re-use CommandCenter protections; content moderation guardrails before publish.
- **Idempotency**: `Idempotency-Key` header; store request hashes for 24h.
