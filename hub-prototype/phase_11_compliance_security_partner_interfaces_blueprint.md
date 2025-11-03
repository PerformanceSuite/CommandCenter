# Phase 11 — Compliance, Security & Partner Interfaces Blueprint

**Objective:** Integrate Veria’s compliance and security frameworks directly into CommandCenter instances, enabling continuous compliance validation, partner access portals, and verifiable attestations. This phase transforms each project instance into a compliance-aware environment with external transparency capabilities.

---

## 0) Overview

Phase 11 expands CommandCenter’s internal automation (Phase 10) to include:
- **Compliance Engine**: a rules-based audit and attestation system derived from Veria.
- **Security Dashboard**: aggregated visibility of all audit and vulnerability data.
- **Partner Interface**: external, role-based API and dashboard for auditors and partners.
- **Continuous Attestation**: cryptographically signed compliance states stored immutably.

The meta-hub can optionally expose read-only partner views across projects.

---

## 1) Compliance Engine

### 1.1 Rule Model (Prisma)
- `ComplianceRule(id, projectId, name, framework[MiCA|DAC8|SEC|GDPR|SOC2], category, description, queryJson, severity, weight)`
- `ComplianceResult(id, ruleId, targetEntity, targetId, status[pass|warn|fail], detailsJson, evaluatedAt)`
- `Attestation(id, projectId, summary, hash, signer, createdAt, proofUrl)`

### 1.2 Rules Execution
- Rules defined in YAML or JSON logic syntax under `/compliance/rules/`.
- Execution agent (`compliance-checker`) runs rules against the project’s Graph-Service and Audit data.
- Example YAML:
```yaml
name: schema_version_consistency
framework: MiCA
query:
  entity: Service
  condition: version == latest
severity: medium
weight: 0.2
```

### 1.3 Attestation Generation
- After each compliance run, results are summarized and hashed (SHA-256).
- Attestation file generated (`attestation.json`) with signer signature (PGP or keypair from Vault).
- Uploaded to Veria registry or IPFS.

---

## 2) Security Dashboard

### 2.1 Data Sources
- `Audit` table (security, license, code review kinds)
- `ComplianceResult` (mapped by severity)
- `HealthSample` (infrastructure health)

### 2.2 Aggregations
- Critical vulnerability count
- Compliance pass ratio
- Time since last attestation
- Audit trend graph (7d)

### 2.3 VISLZR Security View
- New tab: **Security & Compliance**
- Panels:
  - Risk Overview (heatmap)
  - Compliance Frameworks (MiCA, SOC2, etc.)
  - Open Vulnerabilities (grouped by severity)
  - Attestation Status (timestamp + signature)
- Quick actions:
  - Run Compliance Sweep
  - Generate Attestation
  - Export Partner Report

---

## 3) Partner Interface

### 3.1 API Gateway (PartnerHub)
Hosted by each project instance (Fastify service):
- `GET /api/partner/summary` → returns aggregated compliance + audit data.
- `GET /api/partner/attestations` → list of attestations + proof URLs.
- `GET /api/partner/audit/:id` → view specific audit report (sanitized).

### 3.2 Access Control
- Roles: `Partner`, `Auditor`, `Viewer`.
- Auth methods: OIDC or API key.
- Row-level filtering (each partner sees only permitted categories).

### 3.3 Partner Dashboard (optional lightweight VISLZR front)
- Hosted at `/partner/` route.
- Read-only visualization with summary panels + links to attestations.

---

## 4) Integration with Veria

### 4.1 Data Sync
- Compliance Engine imports Veria frameworks via Veria’s `registry.json`.
- Periodically syncs definitions (`frameworks/MiCA.json`, `frameworks/DAC8.json`).

### 4.2 Veria Attestation Upload
- When configured, completed attestations are uploaded to Veria’s registry:
  - REST endpoint: `POST /veria/api/attestations`
  - Payload: `{ project, hash, summary, signer, proofUrl }`
  - Response includes permanent registry ID.

### 4.3 Shared Agents
- `veria-compliance` agent (Phase 10 registry) extends local compliance-checker with external validation.
- Can compare local vs. Veria registry states.

---

## 5) Continuous Compliance Workflows

### 5.1 Example Workflow (Phase 10 DAG)
```yaml
name: continuous-compliance
trigger:
  on: [audit.result.completed]
  filters:
    kind: security
nodes:
  - id: run_compliance
    agent: compliance-checker
    action: runRules
  - id: generate_attestation
    agent: attestor
    action: signAttestation
    dependsOn: [run_compliance]
  - id: upload_veria
    agent: veria-compliance
    action: uploadRegistry
    dependsOn: [generate_attestation]
```

### 5.2 Scheduling
- Default: nightly compliance sweep at 02:00 local time.
- Manual trigger via VISLZR or CLI.

---

## 6) CLI Tools

Add to `package.json`:
```json
{
  "scripts": {
    "compliance:run": "tsx ./scripts/compliance/run.ts",
    "compliance:attest": "tsx ./scripts/compliance/attest.ts",
    "partner:serve": "tsx ./services/partner/server.ts",
    "partner:test": "tsx ./scripts/partner/test.ts"
  }
}
```

---

## 7) Security & Data Handling
- Attestations and compliance results stored in read-only snapshot directories.
- Sensitive data redacted before partner publication.
- All API endpoints protected by auth middleware.
- Attestation signatures generated by per-project keypair stored in Vault.
- Logs hashed + timestamped for tamper evidence.

---

## 8) Observability
- Compliance run metrics (rules executed, pass%, fail%) → Prometheus.
- Partner API access logs + response times.
- OTel traces for rule evaluation and attestation generation.
- Grafana dashboard: Compliance Trend, Attestation History, Framework Coverage.

---

## 9) Implementation Steps

### 9.1 Backend
1. Add Prisma models (ComplianceRule, ComplianceResult, Attestation).
2. Implement compliance-checker agent and attestor agent.
3. Build PartnerHub API (Fastify routes).
4. Integrate Veria registry sync + upload.

### 9.2 Frontend (VISLZR)
1. Add **Security & Compliance Tab**.
2. Implement visual components for frameworks, rules, and attestation badges.
3. Add quick actions (Run Sweep, Generate Attestation).
4. Optional: `/partner/` read-only dashboard.

### 9.3 Testing
- Run compliance sweep → validate rule results.
- Generate attestation → verify signature + hash.
- Partner API → returns sanitized results.
- VISLZR tab → renders KPIs correctly.

---

## 10) Acceptance Criteria

- Compliance rules execute successfully and record `ComplianceResult` entries.
- Attestations generated, signed, and optionally uploaded to Veria.
- Partner API exposes read-only, sanitized summaries.
- VISLZR displays real-time compliance and audit KPIs.
- Continuous compliance workflow executes automatically.

---

## 11) Deliverables Checklist
- [ ] Prisma models + migrations
- [ ] Compliance-checker + Attestor agents
- [ ] PartnerHub API service
- [ ] VISLZR Security & Compliance tab
- [ ] CLI commands
- [ ] Veria integration scripts
- [ ] Grafana dashboards
- [ ] `/docs/phase11-compliance.md`

---

> Phase 11 establishes CommandCenter as a compliance-aware platform with transparent, partner-accessible attestation workflows — integrating Veria’s regulatory intelligence and enabling external trust by design.
