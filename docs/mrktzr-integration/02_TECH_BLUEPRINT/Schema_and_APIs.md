# Schema & APIs Overview

- **HTTP (OpenAPI)**: `/insights/export` (CC→MR), `/campaigns/intake` (MR intake), `/analytics/intake` (MR→CC metrics).
- **Events (AsyncAPI, NATS)**: `cc.insight.ready`, `mr.campaign.event`, `mr.analytics.metric`.
- **Relational/Vector Models**:
  - CC: `insights`, `embeddings`
  - MR: `campaigns`, `posts`, `metrics`, `personas`
