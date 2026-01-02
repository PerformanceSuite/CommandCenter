# Real-Time Intelligence Engine

**Status**: Concept
**Created**: 2026-01-02
**Related**: [Wander](./Wander.md), [Veria](./Veria.md)

---

## Overview

The Real-Time Intelligence Engine provides continuous information gathering from diverse sources to feed Wander explorations and Veria decision-making. It transforms raw signals into structured intelligence that autonomous agents can act upon.

---

## Information Sources

### Existing in CommandCenter

| Source | Status | Data Type |
|--------|--------|-----------|
| **Technology Radar** | ✅ Built | Technology tracking, status, domains |
| **Research Hub** | ✅ Built | Research tasks, deep dives, hypotheses |
| **Graph Service** | ✅ Built | Code symbols, dependencies, architecture |
| **KnowledgeBeast** | ✅ Built | Vector embeddings, semantic search |

### To Integrate

| Source | Priority | Data Type | Integration Path |
|--------|----------|-----------|------------------|
| **Prediction Markets** | 🔴 High | Probability signals, market sentiment | Polymarket API |
| **HackerNews** | 🟡 Medium | Tech trends, community sentiment | Algolia API |
| **GitHub Trending** | 🟡 Medium | Emerging projects, star velocity | GitHub API |
| **arXiv** | 🟡 Medium | Research papers, breakthrough signals | arXiv API |
| **SEC Filings** | 🔴 High | Financial disclosures, insider activity | EDGAR API |
| **Social Sentiment** | 🟢 Low | Twitter/X, Reddit, sentiment analysis | Various APIs |
| **News Feeds** | 🟡 Medium | Breaking news, market events | RSS, NewsAPI |

---

## Prediction Markets as Intelligence Source

### Why Prediction Markets?

Prediction markets aggregate distributed knowledge into probability estimates. They're particularly valuable because:

1. **Skin in the game**: Participants bet real money, incentivizing accuracy
2. **Real-time updates**: Prices reflect new information immediately
3. **Quantified uncertainty**: Probabilities, not just sentiment
4. **Contrarian signals**: When markets diverge from consensus, opportunity exists

### Polymarket Integration

**Polymarket** is the leading crypto prediction market with:
- High liquidity on major events
- Clean API access
- Categories: Politics, Crypto, Sports, Finance, Science, Pop Culture

#### Data to Extract

```python
@dataclass
class PredictionMarketSignal:
    market_id: str
    question: str
    current_probability: float
    volume_24h: float
    liquidity: float

    # Derived signals
    probability_change_24h: float
    probability_change_7d: float
    volume_spike: bool  # Volume > 2x average

    # Categories
    domains: List[str]  # Map to Wander domains
    related_entities: List[str]  # Companies, people, technologies

    # Timing
    resolution_date: datetime
    last_updated: datetime
```

#### Signal Processing

1. **Probability Shifts**: Large moves (>10% in 24h) indicate new information
2. **Volume Spikes**: Sudden interest suggests breaking developments
3. **Divergence from Consensus**: When market price differs from pundit consensus
4. **Category Clustering**: Multiple related markets moving together

### Wander Integration

Prediction market signals feed into Wander as:

1. **Locus Seeds**: High-signal markets become exploration starting points
2. **Attractor Signals**: Probability directions suggest where to explore
3. **Validation Source**: Crystal insights can be checked against market prices
4. **Resonance Triggers**: Related markets reinforce pattern detection

```
Polymarket: "Will X company acquire Y?" at 65%
    ↓
Wander seeds: "M&A in [sector]", "X company strategy", "Y company value"
    ↓
Exploration produces crystals about acquisition implications
    ↓
If crystal suggests market is mispriced → Economic action opportunity
```

---

## Prediction Markets as Revenue Mechanism

### Veria Trading Strategy

Beyond using prediction markets for intelligence, Veria can **trade on them** to generate revenue:

#### Strategy 1: Information Arbitrage

When Wander discovers insights that contradict market prices:

```
Wander Crystal: "Regulatory approval for X likely based on pattern match with Y, Z cases"
Current Market: "X regulatory approval" at 35%
    ↓
Evaluate confidence vs. market price
    ↓
If edge exists: Place position
    ↓
Track outcome, update models
```

#### Strategy 2: Cross-Market Arbitrage

Identify related markets with inconsistent prices:

```
Market A: "Company X acquisition" at 70%
Market B: "X stock above $100 by March" at 40%
    ↓
If acquisition would push stock above $100 with >70% probability,
Market B is underpriced
    ↓
Trade the mispricing
```

#### Strategy 3: Event-Driven Research

Commission deep research when:
- High-value markets have uncertain outcomes
- Wander finds domains with information asymmetry
- Research cost < expected value of edge

### Risk Management

| Control | Implementation |
|---------|----------------|
| Position limits | Max % of bankroll per market |
| Confidence thresholds | Only trade when edge > X% |
| Human approval | Require sign-off above $Y |
| Diversification | Max exposure per category |
| Drawdown limits | Pause trading if losses exceed Z |

### Fractal Security Integration

Economic actions (trades) can be encoded as fractals:
- Trade parameters hidden in fractal encoding
- Only authorized trading agent can decode
- Audit trail embedded in visual record
- Human can inspect without full decode

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME INTELLIGENCE ENGINE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    SOURCE CONNECTORS                             ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           ││
│  │  │Polymarket│ │ GitHub   │ │  arXiv   │ │   SEC    │  ...      ││
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           ││
│  └───────┼────────────┼────────────┼────────────┼──────────────────┘│
│          │            │            │            │                    │
│          ▼            ▼            ▼            ▼                    │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    SIGNAL PROCESSOR                              ││
│  │  • Normalize formats                                             ││
│  │  • Extract entities                                              ││
│  │  • Compute embeddings                                            ││
│  │  • Detect anomalies                                              ││
│  │  • Map to domains                                                ││
│  └────────────────────────────┬────────────────────────────────────┘│
│                               │                                      │
│                               ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    SIGNAL STORE                                  ││
│  │  PostgreSQL + pgvector                                           ││
│  │  • Raw signals                                                   ││
│  │  • Processed intelligence                                        ││
│  │  • Historical trends                                             ││
│  └────────────────────────────┬────────────────────────────────────┘│
│                               │                                      │
│          ┌────────────────────┼────────────────────┐                │
│          ▼                    ▼                    ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │    Wander    │    │    Veria     │    │  Tech Radar  │          │
│  │  (discovery) │    │  (trading)   │    │  (tracking)  │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Polymarket Connector (1 week)

- [ ] API integration with Polymarket
- [ ] Signal extraction pipeline
- [ ] Store in PostgreSQL with vectors
- [ ] Basic anomaly detection (volume, price spikes)

### Phase 2: Wander Integration (1 week)

- [ ] Feed signals as Wander seeds
- [ ] Use probabilities in resonance scoring
- [ ] Validate crystals against market prices

### Phase 3: Trading Infrastructure (2 weeks)

- [ ] Wallet integration (Solana or EVM)
- [ ] Position tracking
- [ ] Risk management rules
- [ ] Human approval workflow
- [ ] Fractal encoding for trade proposals

### Phase 4: Additional Sources (ongoing)

- [ ] HackerNews connector
- [ ] GitHub Trending connector
- [ ] arXiv connector
- [ ] SEC EDGAR connector

---

## Revenue Model

### Direct Trading Revenue

```
Expected Value = Σ (Edge × Position Size × Win Rate) - Transaction Costs

Where:
- Edge = (Our Probability - Market Probability) when our P > Market P
- Position Size = f(confidence, bankroll, Kelly criterion)
- Win Rate = Historical accuracy of similar predictions
```

### Indirect Value

1. **Better Wander exploration**: Market signals surface high-value areas
2. **Crystal validation**: Markets provide ground truth for insights
3. **Competitive intelligence**: Track what others are betting on
4. **Early warning**: Price moves precede news

---

## Open Questions

1. **Regulatory considerations**: Is trading on prediction markets legal in target jurisdictions?
2. **Bankroll sizing**: How much capital to allocate initially?
3. **Model evaluation**: How do we measure edge before deploying capital?
4. **Market manipulation risk**: Can large positions move illiquid markets?
5. **API reliability**: What's Polymarket's uptime and rate limits?

---

*This concept connects real-time intelligence gathering with economic action, bridging Wander's discovery with Veria's execution.*
