# Wander: Long-Running Exploratory Agent for Idea Discovery

**Status**: Design Complete
**Created**: 2026-01-02
**Last Updated**: 2026-01-02

---

## Executive Summary

Wander is a **divergent exploration system** that autonomously traverses idea space to discover novel concepts, patterns, and opportunities. Unlike convergent agents that seek specific answers, Wander explores with purpose but without predetermined targets.

The system produces three outputs:
- **Encounters**: Unexpected juxtapositions between concepts
- **Resonances**: Patterns that recur across explorations
- **Crystals**: Validated insights that survive scrutiny

---

## Philosophy

### What is a Wander?

A wander is **purposefully undirected** exploration:
- **Random**: Pick any point in space (bad)
- **Purposefully undirected**: Pick points that are *interesting* without knowing *why* yet (good)

Every wander has:
- A **SEED** (starting point)
- An **ATTRACTOR** (vague sense of what we're looking for)
- NO **TARGET** (no specific answer sought)

### Core Principles

1. **Divergent by design** - Exploration, not exploitation
2. **Productive distance** - Find connections that are close enough to relate, far enough to be non-obvious
3. **Memory as metabolism** - Ideas flow through layers, transform, decay, or crystallize
4. **Decouple useful from wandering** - Usefulness is a post-filter, not exploration criteria
5. **Rhythm over continuous** - Rest cycles, not constant generation

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WANDER SYSTEM                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      VISLZR MIND MAP                            │ │
│  │  Real-time visualization of exploration as force-directed      │ │
│  │  graph. Nodes drift, connect, pulse with resonance.            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              ▲                                       │
│                              │ WebSocket (NATS events)              │
│                              │                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      WANDER ENGINE                              │ │
│  │                                                                  │ │
│  │  Adjacency     Dweller      Resonance     Crystallizer          │ │
│  │   Finder   →   (LLM)    →   Tracker   →                         │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  MEMORY LAYERS: HOT → WARM → COLD → COMPOST              │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  SCOPE & VERIFICATION: Fences, Constraints, Breakers     │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    ECONOMIC ACTION LAYER                        │ │
│  │  Crystal → Evaluate → Fractal Encode → Execute (with wallet)   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Memory Architecture

### Four-Layer Memory System

| Layer | Purpose | Storage | Lifespan | Size |
|-------|---------|---------|----------|------|
| **HOT** | Working context | In-memory | Current session | ~10-50 items |
| **WARM** | Recent themes | SQLite/Postgres | Days-weeks | ~100-500 clusters |
| **COLD** | Crystallized insights | Postgres + vectors | Permanent | ~50-200 crystals |
| **COMPOST** | Decayed but queryable | Vector store only | Forever (passive) | Unbounded |

### Memory Flow

```
New encounter
      ↓
  HOT MEMORY (full detail)
      ↓ (compress on overflow)
  WARM MEMORY (theme clusters)
      ↓ (graduate on strength)
  COLD MEMORY (validated insights)

      OR

      ↓ (decay below threshold)
  COMPOST (mulch for future)
```

---

## Core Data Models

### Locus (Point in Idea Space)

```python
@dataclass
class Locus:
    id: str
    concept: str                      # Natural language description
    embedding: np.ndarray             # Vector representation

    source_type: SourceType           # SEED | ADJACENT | BRIDGED | SERENDIPITOUS
    domains: List[str]                # Which domains this touches
    abstraction_level: float          # 0.0 = concrete, 1.0 = abstract

    novelty_score: float
    interestingness: float
    actionability: float
    uncertainty: float

    visit_count: int
    first_encountered: datetime
    last_visited: datetime
```

### Residue (What Emerges from Dwelling)

```python
@dataclass
class Residue:
    encounter: Tuple[str, str]        # (from_locus_id, to_locus_id)

    connection: str                   # What links these concepts?
    tension: str                      # Where do they conflict?
    bridge: str                       # What crosses domains?
    surprise: str                     # What's unexpected?
    possibility: str                  # What new concept might emerge?

    themes: List[str]
    themes_embedding: np.ndarray
    interestingness: float
    actionability: float
```

### Resonance (Recurring Pattern)

```python
@dataclass
class Resonance:
    id: str
    themes: List[str]
    embedding: np.ndarray

    occurrences: int
    strength: float                   # Decays over time
    status: ResonanceStatus           # CANDIDATE | CONFIRMED | INVALIDATED

    supporting_residue_ids: List[str]
```

### Crystal (Validated Insight)

```python
@dataclass
class Crystal:
    id: str
    insight: str
    embedding: np.ndarray

    confidence: float
    actionability: float
    domains: List[str]

    source_resonance_id: str
    supporting_evidence: List[str]
    status: CrystalStatus             # ACTIVE | ACTED_UPON | INVALIDATED
```

---

## Adjacency Finding Strategies

The core challenge: Find concepts that are **productively distant** - close enough to connect, far enough to be non-obvious.

### Strategy 1: Distance Band Sampling
- Query vectors in 0.3-0.7 cosine distance range
- Too close (<0.3) = same idea, different words
- Too far (>0.7) = probably unrelated noise

### Strategy 2: Cross-Domain Bridging
- Maintain separate embedding spaces per domain
- Find concepts that appear in multiple domains
- These are natural bridge points

### Strategy 3: Analogical Reasoning
- Given known relationships (A→B via R), find where locus might have similar relationship
- "X is to Y as A is to ?"

### Strategy 4: Tension/Contradiction Seeking
- Find concepts in productive conflict
- Not random opposites, but meaningful dialectic

---

## Scope & Verification

Constraints that compound at every layer:

### Layer 0: Session Creation
- Allowed/forbidden domains
- Seed concepts (anchors)
- Max drift distance
- Embedding fence (convex hull)
- Resource budgets

### Layer 1: Every Step
- Is proposed locus within fence?
- Is it in allowed domain?
- Are resources remaining?

### Layer 2: Adjacency Generation
- Pre-filter candidates before consideration

### Layer 3: Dwelling Output
- Verify LLM output for safety
- Check for PII, hallucination

### Layer 4: Crystallization Gate
- Minimum strength threshold
- Human approval (optional)

### Layer 5: Circuit Breakers
- Budget exhausted → STOP
- Loop detected → STOP
- Drift exceeded → STOP

---

## Model Strategy

### Local Models (80% of operations)
- **Embeddings**: nomic-embed-text or all-MiniLM-L6-v2
- **Generation**: Llama 3.2 3B, Mistral 7B, Qwen 2.5 7B
- **Use for**: Routine dwellings, theme extraction, compression

### Cloud Models (20% of operations)
- **Primary**: Claude Sonnet 4
- **Heavy**: Claude Opus 4.5 (crystallization only)
- **Use for**: High-value dwellings, bridging, crystallization

### Decision Logic
```python
use_cloud = (
    bridge_score > 0.7 OR
    resonance_proximity > 0.8 OR
    is_crystallization_candidate
) AND (
    session.cloud_budget > estimated_cost
)
```

---

## Fractal Security Layer (Experimental)

A novel access control mechanism where sensitive information (especially for economic agents with wallet privileges) is encoded as fractal images. Only agents with matching decoder training can extract meaning.

### Properties
- **Key is capability**: Can't steal a token, would need to steal entire model
- **Degradable access**: Partial training = partial comprehension
- **Prompt injection resistant**: Visual format mismatch detectable
- **Audit trail**: Fractal itself is the record

### Use Cases
- Economic action proposals
- Wallet operation instructions
- Sensitive strategy data

---

## VISLZR Integration

Real-time mind map visualization using ReactFlow:

### Node Types
- **LocusNode**: Standard exploration point (circle)
- **CrystalNode**: Hardened insight (diamond)
- **FractalNode**: Security-encoded data (square with image)

### Edge Types
- **Path**: Taken exploration route (solid)
- **Adjacency**: Potential next step (dashed)
- **Bridge**: Cross-domain connection (double)
- **Resonance**: Pattern connection (wavy, animated)

### Interactions
- **Observe**: Watch wander unfold
- **Steer**: Click to guide, drag to hint
- **Analyze**: Select, compare, trace paths
- **Go Deeper**: Spawn focused sub-wander

---

## Build Sequence

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| **0** | Mind Map Foundation | ReactFlow component, mock data, controls |
| **1** | Foundation | Database schema, data models, KB integration |
| **2** | Adjacency Finding | Distance band, bridging, ranking |
| **3** | Wander Loop | Step execution, trace, local LLM dweller |
| **4** | Resonance & Crystallization | Pattern detection, decay, validation |
| **5** | Constraints & Verification | Fences, breakers, checkpoints |
| **6** | VISLZR Integration | Wire to NATS, real-time updates |
| **7** | Persistence & Archival | Multi-format save, visual encoding |
| **8** | Fractal Security | Encoder/decoder, economic layer |

---

## First Use Case: Meta-Wander for Veria

The first wander session explores:
> "What business domains would be valuable for an autonomous economic agent to operate in?"

**Seed concepts**: Financial services, information asymmetry, intelligence tooling, Veria capabilities, CommandCenter infrastructure

**Attractor**: "Economic opportunity in financial intelligence with tractable solutions given our existing assets"

**Expected outputs**: Candidate domains, market gaps, competitive landscape, first actionable opportunity

---

## References

### Frameworks to Integrate
- **Letta (MemGPT)**: Tiered memory management - github.com/letta-ai/letta
- **Mem0**: Graph-based memory - github.com/mem0ai/mem0
- **LangGraph**: Stateful orchestration - github.com/langchain-ai/langgraph

### Research
- A-MEM: Zettelkasten-inspired agent memory
- CreativeDC: Divergent-convergent scaffolding
- SAGE: Self-evolving agents with reflective memory
- Memory in the Age of AI Agents (survey)

---

*This concept document serves as the authoritative reference for the Wander system design.*
