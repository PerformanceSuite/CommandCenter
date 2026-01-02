# ROLLIZR

**Rollup and Consolidation Intelligence**

ROLLIZR identifies fragmented industries and uncovers consolidation opportunities. It's an internal competitive advantage module—intelligence stays in-house to enhance our capabilities.

## Overview

ROLLIZR scans for industries where:
- Many small players exist (fragmentation)
- Consolidation creates value (synergies)
- Opportunities are actionable (timing, access)

This intelligence feeds Wander (exploration seeds), MRKTZR (targets), and Veria (investment theses).

## Strategic Position

Originally conceived as a subscription product for PE firms. **New positioning**: Keep intelligence internal, use it to enhance our own capabilities and take % of profit on deals we facilitate.

Why internal:
- Information asymmetry is the edge
- Sharing reduces value
- Better aligned with "% of profit" model

## Components

### Fragmentation Indexer
Quantifies industry fragmentation:
- Ownership concentration (HHI)
- Number of players by size tier
- Growth rates by segment
- Technology adoption variance

### Opportunity Scanner
Detects acquisition/partnership targets:
- Companies showing stress signals
- Founders approaching retirement
- Technology gaps creating vulnerability
- Regulatory changes forcing consolidation

### Synergy Engine
Analyzes potential combinations:
- Technology stack compatibility
- Customer overlap/expansion
- Supply chain integration
- Team/culture fit signals

### Integration Validator
Simulates post-merger integration:
- System interoperability (ERP, CRM, etc.)
- Process alignment
- Cultural risk factors
- Timeline and cost estimates

## Integration Points

| Module | Integration |
|--------|-------------|
| KnowledgeBeast | Source data, store analyses |
| Wander | Fragmentation as exploration seed |
| MRKTZR | Targets for outreach, deal flow |
| Veria | Investment theses, compliance |
| AI Arena | Validate opportunity hypotheses |

## Data Model

```
Industry
├── id, name, sic_codes[]
├── fragmentation_score (0-1)
├── player_count, top_10_share
├── growth_rate, margin_profile
└── last_analyzed

Opportunity
├── id, industry_id
├── type (acquisition|partnership|rollup)
├── target_companies[]
├── synergy_score, confidence
├── status (detected|researching|active|passed)
├── thesis, risks[]
└── detected_at, updated_at

Company (for targets)
├── id, name, domain, industry_id
├── size_tier, revenue_estimate
├── signals[] (stress, growth, tech_gap)
├── contacts[] (via MRKTZR)
└── last_updated

Synergy Analysis
├── id, opportunity_id
├── companies[]
├── tech_compatibility_score
├── customer_overlap_score
├── integration_complexity
├── estimated_value_creation
└── analysis_date
```

## Actions (VISLZR node)

- scan industry
- view opportunities
- analyze synergy
- create thesis
- track target
- export analysis

## Roadmap

- [ ] Fragmentation Indexer MVP
- [ ] Integration with public company data
- [ ] Opportunity detection rules engine
- [ ] Synergy scoring model
- [ ] MRKTZR integration for outreach
- [ ] Veria integration for compliance
