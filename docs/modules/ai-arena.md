# AI Arena

**Multi-Model Debate and Validation**

AI Arena tests hypotheses through structured multi-model debate. It's CommandCenter's primary VALIDATE mechanism.

## Overview

When you need to validate an idea, hypothesis, or approach, AI Arena pits multiple AI models against each other in structured debate. The result: consensus, dissent, or actionable uncertainty.

## How It Works

1. **Submit Hypothesis**: A claim to validate
2. **Debate Rounds**: Models argue for/against with evidence
3. **Chairman Synthesis**: Neutral model synthesizes positions
4. **Consensus Check**: Agreement level determines outcome
5. **Crystal Output**: Validated insight or identified uncertainty

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI ARENA                                 │
│                                                                 │
│  Hypothesis: "Prediction markets outperform polls for elections"│
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                     │
│  │ Claude  │    │ Gemini  │    │  GPT-4  │                     │
│  │  FOR    │    │ AGAINST │    │ ANALYST │                     │
│  └────┬────┘    └────┬────┘    └────┬────┘                     │
│       │              │              │                           │
│       └──────────────┼──────────────┘                           │
│                      ▼                                          │
│               ┌──────────┐                                      │
│               │ Chairman │                                      │
│               │Synthesis │                                      │
│               └────┬─────┘                                      │
│                    ▼                                            │
│  Result: 78% consensus FOR with caveats about sample size       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Roles

| Role | Purpose | Default Model |
|------|---------|---------------|
| Analyst | Research and evidence gathering | Claude |
| Researcher | Deep dive on specific aspects | Gemini |
| Strategist | Implications and applications | GPT-4 |
| Critic | Devil's advocate, weaknesses | Claude |
| Chairman | Neutral synthesis | Claude |

## Integration Points

| Module | Integration |
|--------|-------------|
| Wander | Crystal candidates validated here |
| KnowledgeBeast | Evidence retrieved for debates |
| Veria | Market prices as validation signal |
| Prompt Improver | Winning argument patterns improve prompts |

## API

```
POST /api/v1/hypotheses
POST /api/v1/hypotheses/{id}/validate
GET  /api/v1/hypotheses/{id}/debate
GET  /api/v1/hypotheses/stats
GET  /api/v1/hypotheses/costs
```

## Data Model

```
Hypothesis
├── id, title, description
├── status (draft|validating|validated|rejected)
├── confidence_score (0-1)
├── created_at, validated_at
└── debates[]

Debate
├── id, hypothesis_id
├── rounds[]
├── chairman_synthesis
├── consensus_level
└── total_cost

Round
├── id, debate_id, round_number
├── responses[] (per model)
└── evidence_cited[]

Response
├── id, round_id
├── model, role
├── position (for|against|neutral)
├── argument, evidence[]
├── tokens, cost
└── timestamp
```

## Actions (VISLZR node)

- create hypothesis
- validate
- view debate
- cost analysis
- export results

## Status

✅ **Working** - Full debate flow operational with Claude, Gemini, GPT-4
