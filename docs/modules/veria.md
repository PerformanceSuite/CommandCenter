# Veria

**Financial Intelligence and Prediction Markets**

Veria is CommandCenter's module for financial intelligence gathering, prediction market trading, and economic action. It validates insights through market prices and generates revenue through information arbitrage.

## Overview

Veria combines:
1. **Intelligence Gathering**: Real-time signals from prediction markets, filings, news
2. **Market Validation**: Prices as truth signals for hypotheses
3. **Autonomous Trading**: Economic agents that act on validated insights
4. **Compliance Layer**: Trust and regulatory validation for actions

## Prediction Markets as Intelligence

Prediction markets (Polymarket, etc.) provide:
- Probability-weighted signals on future events
- Real-time updates as information flows
- Quantified uncertainty (not just sentiment)
- Contrarian opportunity detection

Markets validate Wander crystals: if a crystal contradicts market prices, either the crystal is wrong or there's an arbitrage opportunity.

## Trading Strategy

### Revenue Through Information Arbitrage

When Wander crystals or AI Arena validations contradict market prices:
1. Assess confidence differential
2. Size position using Kelly criterion
3. Execute with human approval for large positions
4. Track outcome for model improvement

### Strategy Portfolio

| Strategy | Description | Risk |
|----------|-------------|------|
| Information Arbitrage | Trade when crystals contradict prices | Medium |
| Cross-Market Arbitrage | Exploit price inconsistencies | Low |
| Event-Driven Research | Research high-uncertainty markets | Medium |
| Momentum | Ride probability trends | Low |
| Contrarian | Bet against crowd with evidence | High |

### Risk Management

```
Position Limits:
- Max 5% of bankroll per market
- Max 20% exposure per category
- Max 50% total deployed

Approval Requirements:
- Human approval for positions > $1,000
- Human approval for new categories
- Pause if 20% drawdown in 30 days
```

## Real-Time Intelligence Engine

Continuous signal processing from:

| Source | Signal Type |
|--------|-------------|
| Polymarket | Probability movements, volume |
| HackerNews | Tech sentiment, emerging topics |
| arXiv | Research breakthroughs |
| SEC EDGAR | Filings, insider transactions |
| News APIs | Event detection |

Signals feed Wander (exploration seeds) and trigger AI Arena (validation).

## Integration Points

| Module | Integration |
|--------|-------------|
| Wander | Crystals drive trading hypotheses |
| AI Arena | Validates trading theses |
| KnowledgeBeast | Stores all market data, outcomes |
| MRKTZR | Market intelligence for campaigns |
| ROLLIZR | Investment thesis validation |
| Fractlzr | Encodes trade proposals securely |

## Data Model

```
Market
├── id, platform (polymarket|...)
├── title, description
├── category, tags[]
├── current_price, volume
├── resolution_date, resolved
└── last_updated

Signal
├── id, source, source_id
├── type (price_move|volume_spike|filing|news)
├── content, entities[]
├── importance_score
└── timestamp

Position
├── id, market_id
├── direction (yes|no)
├── size, entry_price
├── thesis, confidence
├── status (open|closed)
├── exit_price, pnl
├── approved_by, approved_at
└── opened_at, closed_at

Trade
├── id, position_id
├── type (open|close|adjust)
├── size, price
├── fees
└── timestamp
```

## Actions (VISLZR node)

- view markets
- scan signals
- create thesis
- open position
- portfolio view
- performance stats

## Compliance

All trading actions go through approval workflow:
- Human checkpoints for significant positions
- Audit trail for all decisions
- Regulatory compliance checks
- Fractlzr encoding for sensitive proposals

## Roadmap

- [x] Real-time intelligence concept
- [ ] Polymarket API integration
- [ ] Signal processing pipeline
- [ ] Trading thesis workflow
- [ ] Position management
- [ ] Human approval gates
- [ ] Performance tracking
