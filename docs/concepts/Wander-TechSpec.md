# Wander Technical Specification

**Status**: Design Complete
**Created**: 2026-01-02
**Parent**: [Wander Concept](./Wander.md)

This document contains detailed technical specifications for implementing Wander.

---

## Database Schema

### Tables

```sql
-- Core session tracking
CREATE TABLE wander_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, paused, completed, abandoned

    -- Configuration
    seed_concept TEXT NOT NULL,
    seed_embedding vector(1536),
    attractor TEXT,
    attractor_embedding vector(1536),

    -- Constraints
    allowed_domains TEXT[],
    forbidden_domains TEXT[],
    fence_embeddings vector(1536)[], -- Convex hull anchors
    max_drift_distance FLOAT DEFAULT 0.8,
    max_steps INTEGER DEFAULT 1000,

    -- Budget
    cloud_budget_cents INTEGER DEFAULT 500,
    cloud_spent_cents INTEGER DEFAULT 0,
    local_calls INTEGER DEFAULT 0,
    cloud_calls INTEGER DEFAULT 0,

    -- Tuning
    temperature FLOAT DEFAULT 0.7,
    human_checkpoint_frequency INTEGER DEFAULT 50, -- Steps between required human checks

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_step_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_status CHECK (status IN ('active', 'paused', 'completed', 'abandoned'))
);

-- Points in idea space
CREATE TABLE wander_loci (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES wander_sessions(id) ON DELETE CASCADE,

    concept TEXT NOT NULL,
    embedding vector(1536) NOT NULL,

    source_type VARCHAR(50) NOT NULL, -- SEED, ADJACENT, BRIDGED, SERENDIPITOUS
    domains TEXT[] NOT NULL DEFAULT '{}',
    abstraction_level FLOAT DEFAULT 0.5,

    -- Scores
    novelty_score FLOAT DEFAULT 0.5,
    interestingness FLOAT DEFAULT 0.5,
    actionability FLOAT DEFAULT 0.0,
    uncertainty FLOAT DEFAULT 0.5,

    -- Visit tracking
    visit_count INTEGER DEFAULT 0,
    first_encountered TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_visited TIMESTAMP WITH TIME ZONE,

    -- Connections (stored as JSONB for flexibility)
    adjacent_to JSONB DEFAULT '[]', -- [{locus_id, distance, strength}]
    bridges_to JSONB DEFAULT '[]',  -- [{locus_id, bridge_type, strength}]
    contradicts JSONB DEFAULT '[]', -- [{locus_id, tension_description}]

    CONSTRAINT valid_source_type CHECK (source_type IN ('SEED', 'ADJACENT', 'BRIDGED', 'SERENDIPITOUS'))
);

CREATE INDEX idx_loci_session ON wander_loci(session_id);
CREATE INDEX idx_loci_embedding ON wander_loci USING ivfflat (embedding vector_cosine_ops);

-- Exploration path
CREATE TABLE wander_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES wander_sessions(id) ON DELETE CASCADE,

    step_number INTEGER NOT NULL,
    from_locus_id UUID REFERENCES wander_loci(id),
    to_locus_id UUID NOT NULL REFERENCES wander_loci(id),

    -- Selection info
    adjacencies_considered INTEGER,
    selection_scores JSONB, -- {interestingness, novelty, bridge_potential, uncertainty}
    selection_reason TEXT,

    -- Resource tracking
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_cents INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(session_id, step_number)
);

CREATE INDEX idx_traces_session ON wander_traces(session_id, step_number);

-- What emerges from dwelling at a locus
CREATE TABLE wander_residues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES wander_sessions(id) ON DELETE CASCADE,
    trace_id UUID NOT NULL REFERENCES wander_traces(id) ON DELETE CASCADE,

    from_locus_id UUID REFERENCES wander_loci(id),
    to_locus_id UUID NOT NULL REFERENCES wander_loci(id),

    -- Dwelling outputs
    connection TEXT,
    tension TEXT,
    bridge TEXT,
    surprise TEXT,
    possibility TEXT,

    -- Extracted themes
    themes TEXT[] DEFAULT '{}',
    themes_embedding vector(1536),

    -- Scores
    interestingness FLOAT,
    actionability FLOAT,

    -- Model info
    model_used VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_residues_session ON wander_residues(session_id);
CREATE INDEX idx_residues_themes_embedding ON wander_residues USING ivfflat (themes_embedding vector_cosine_ops);

-- Recurring patterns
CREATE TABLE wander_resonances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES wander_sessions(id) ON DELETE CASCADE, -- NULL for cross-session
    project_id UUID NOT NULL REFERENCES projects(id),

    themes TEXT[] NOT NULL,
    embedding vector(1536) NOT NULL,

    occurrences INTEGER DEFAULT 1,
    strength FLOAT DEFAULT 1.0,
    status VARCHAR(50) DEFAULT 'candidate', -- candidate, confirmed, invalidated

    supporting_residue_ids UUID[] DEFAULT '{}',

    -- Decay tracking
    last_reinforced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    decay_rate FLOAT DEFAULT 0.1, -- 10% daily

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_resonance_status CHECK (status IN ('candidate', 'confirmed', 'invalidated'))
);

CREATE INDEX idx_resonances_project ON wander_resonances(project_id);
CREATE INDEX idx_resonances_embedding ON wander_resonances USING ivfflat (embedding vector_cosine_ops);

-- Validated insights
CREATE TABLE wander_crystals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES wander_sessions(id) ON DELETE SET NULL,
    project_id UUID NOT NULL REFERENCES projects(id),

    insight TEXT NOT NULL,
    embedding vector(1536) NOT NULL,

    confidence FLOAT NOT NULL,
    actionability FLOAT NOT NULL,
    domains TEXT[] NOT NULL,

    source_resonance_id UUID REFERENCES wander_resonances(id),
    source_locus_id UUID REFERENCES wander_loci(id),
    supporting_evidence JSONB DEFAULT '[]', -- [{type, id, summary}]

    status VARCHAR(50) DEFAULT 'active', -- active, acted_upon, invalidated, archived

    -- Validation
    validated_by VARCHAR(100), -- model or 'human'
    validation_notes TEXT,
    human_approved BOOLEAN DEFAULT FALSE,
    human_approved_at TIMESTAMP WITH TIME ZONE,
    human_approved_by VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_crystal_status CHECK (status IN ('active', 'acted_upon', 'invalidated', 'archived'))
);

CREATE INDEX idx_crystals_project ON wander_crystals(project_id);
CREATE INDEX idx_crystals_embedding ON wander_crystals USING ivfflat (embedding vector_cosine_ops);

-- Compressed warm memory
CREATE TABLE wander_warm_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES wander_sessions(id) ON DELETE CASCADE,

    cluster_type VARCHAR(50) NOT NULL, -- theme_cluster, failed_path, summary
    content JSONB NOT NULL,
    embedding vector(1536),

    strength FLOAT DEFAULT 1.0,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE -- For decay
);

CREATE INDEX idx_warm_memory_session ON wander_warm_memory(session_id);
```

---

## Memory Interaction Architecture: Recursive Language Model Pattern

Wander uses the **Recursive Language Model (RLM)** pattern for memory interaction. Instead of injecting context directly into LLM attention windows (where it degrades via "context rot"), we store context as variables in a persistent REPL environment that the LLM can query programmatically.

### Why RLM?

| Problem | Traditional Approach | RLM Approach |
|---------|---------------------|---------------|
| Context rot | Quality degrades as context grows | Context never enters attention |
| Context limits | Hard cap at 128K-272K tokens | Effectively unlimited (10M+ tested) |
| Token efficiency | Pay for entire context every call | Only load what's needed |
| Memory management | Manual summarization/truncation | LLM decides what to access |
| Auditability | Opaque attention patterns | Explicit code shows access patterns |

**Research basis**: [Recursive Language Models](https://arxiv.org/abs/2512.24601) (Zhang, Kraska, Khattab - Dec 2025)
- GPT-5-mini + RLM outperformed GPT-5 direct by 110% on 132K token tasks
- Successfully handled 10M+ token contexts (100x beyond model window)
- 2-3K tokens/query vs 95K+ for direct context injection

### Core Architecture

```
Traditional:
[272K tokens of context] + [query] → LLM → answer
         ↓ context rot, token limits

RLM Pattern:
[query] → LLM → writes code → REPL executes → result
                    ↓              ↑
              llm_query()    context stored
              (sub-LLM)      as variable
```

### REPL Environment Design

```python
class WanderREPL:
    """Persistent REPL environment for Wander sessions."""

    def __init__(self, session: WanderSession):
        self.globals = {
            # Core context - stored as variables, NOT in LLM context
            'hot_memory': [],      # Recent loci (list of dicts)
            'warm_memory': [],     # Compressed clusters
            'resonances': {},      # Pattern tracker
            'trace': [],           # Exploration path
            'current_locus': None,

            # Query functions available to dweller
            'embed': self._embed,
            'query_similar': self._query_similar,
            'query_by_domain': self._query_by_domain,
            'get_locus': self._get_locus,
            'get_neighbors': self._get_neighbors,
            'llm_query': self._llm_query,  # Spawn sub-LLM

            # Standard library access
            're': re,
            'json': json,
            'math': math,
        }
        self.session = session

    async def _llm_query(self, prompt: str, context: str = "") -> str:
        """Spawn a sub-LLM to process a chunk of context.

        This is the key recursive primitive. The dweller LLM can call
        this to analyze chunks without loading them into its own context.
        """
        # Use smaller/cheaper model for sub-queries
        response = await self.session.sub_llm.complete(
            system="You are a helpful assistant analyzing a chunk of context.",
            prompt=f"{prompt}\n\nContext:\n{context}" if context else prompt,
            max_tokens=2000
        )
        return response

    async def _query_similar(self, embedding: List[float], k: int = 10) -> List[dict]:
        """Find k most similar loci by embedding distance."""
        return await self.session.vector_store.query(
            embedding=embedding,
            k=k,
            filter={'session_id': self.session.id}
        )

    async def _query_by_domain(self, domain: str, limit: int = 20) -> List[dict]:
        """Get loci in a specific domain."""
        return [l for l in self.globals['hot_memory']
                if domain in l.get('domains', [])]

    def execute(self, code: str) -> dict:
        """Execute Python code in the REPL environment."""
        try:
            # Capture stdout for print() statements
            stdout_capture = io.StringIO()
            with redirect_stdout(stdout_capture):
                exec(code, self.globals)

            return {
                'success': True,
                'stdout': stdout_capture.getvalue()[:10000],  # Truncate
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': stdout_capture.getvalue()[:10000],
                'error': str(e)
            }
```

### Dweller System Prompt (RLM-Style)

```python
RLM_DWELLER_SYSTEM_PROMPT = """
You are a Wander dweller exploring idea space. You have access to a REPL
environment with the session's memory stored as variables.

AVAILABLE VARIABLES:
- hot_memory: {hot_count} recent loci (list of dicts with 'concept', 'embedding', 'domains')
- warm_memory: {warm_count} compressed theme clusters
- resonances: {resonance_count} detected patterns
- trace: {trace_count} steps taken so far
- current_locus: Your current position in idea space

AVAILABLE FUNCTIONS:
- embed(text) -> List[float]: Get embedding for text
- query_similar(embedding, k=10) -> List[dict]: Find similar loci
- query_by_domain(domain, limit=20) -> List[dict]: Get loci by domain
- get_locus(id) -> dict: Get full locus details
- get_neighbors(locus_id) -> List[dict]: Get connected loci
- llm_query(prompt, context="") -> str: Spawn sub-LLM to analyze context

IMPORTANT: Do NOT try to print or analyze large amounts of memory directly.
Instead, use query functions to find relevant items, then use llm_query()
to analyze specific chunks.

EXAMPLE - Finding connections:
```repl
# Find loci related to current concept
similar = query_similar(current_locus['embedding'], k=5)
for locus in similar:
    analysis = llm_query(
        f"How does '{locus['concept']}' connect to '{current_locus['concept']}'?",
        context=json.dumps(locus)
    )
    print(f"{locus['concept']}: {analysis}")
```

EXAMPLE - Analyzing patterns across memory:
```repl
# Check resonances for relevant patterns
relevant_themes = [r for r in resonances.values()
                   if any(t in current_locus['domains'] for t in r['themes'])]

if relevant_themes:
    pattern_analysis = llm_query(
        "What patterns emerge from these resonances?",
        context=json.dumps(relevant_themes[:5])
    )
    print(pattern_analysis)
```

When you want to execute code, wrap it in triple backticks with 'repl':
```repl
# Your Python code here
```

When ready to provide your dwelling output, use FINAL():
FINAL({"connection": "...", "tension": "...", ...})
"""
```

### Sub-LLM Strategy

The dweller (root LLM) orchestrates; sub-LLMs do focused analysis:

| Role | Model | Use Case |
|------|-------|----------|
| Root dweller | Claude Sonnet / GPT-5 | Orchestration, code generation, final synthesis |
| Sub-LLM (cheap) | Claude Haiku / GPT-5-mini | Chunk analysis, classification, extraction |
| Sub-LLM (semantic) | Local Llama 3.2 | Theme extraction, similarity judgments |
| Crystallizer | Claude Opus | High-stakes insight validation |

### Memory Access Patterns

The RLM approach enables these patterns that would be impossible with direct context:

**1. Selective Loading**
```python
# Instead of: load all 50K loci into context
# Do: query for relevant subset
relevant = query_similar(current_locus['embedding'], k=20)
analysis = llm_query("Find the most interesting connection", json.dumps(relevant))
```

**2. Iterative Exploration**
```python
# Process large memory in chunks
for i in range(0, len(hot_memory), 100):
    chunk = hot_memory[i:i+100]
    themes = llm_query("Extract main themes", json.dumps(chunk))
    theme_buffer.append(themes)

# Synthesize
final = llm_query("What patterns emerge?", json.dumps(theme_buffer))
```

**3. Recursive Decomposition**
```python
# Break complex analysis into sub-problems
domains = list(set(d for l in hot_memory for d in l['domains']))
for domain in domains:
    domain_loci = query_by_domain(domain)
    domain_analysis = llm_query(f"Key insights in {domain}?", json.dumps(domain_loci))
    domain_buffer[domain] = domain_analysis

# Cross-domain synthesis
bridges = llm_query("What bridges exist between domains?", json.dumps(domain_buffer))
```

**4. Answer Verification**
```python
# Use sub-LLM to verify findings
candidate_insight = "Financial regulation patterns mirror..."
verification = llm_query(
    f"Does this insight hold? '{candidate_insight}'",
    context=json.dumps(supporting_evidence)
)
```

### Implementation References

- **Paper**: [arXiv:2512.24601](https://arxiv.org/abs/2512.24601) - Recursive Language Models
- **Reference impl**: [github.com/ysz/recursive-llm](https://github.com/ysz/recursive-llm)
- **Prime Intellect environments**: [primeintellect.ai/blog/rlm](https://www.primeintellect.ai/blog/rlm)

### Integration with Wander Memory Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    WANDER RLM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DWELLER (Root LLM)                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Receives: query + REPL environment description            │ │
│  │  Produces: Python code to explore memory                   │ │
│  │  Can call: llm_query() for sub-analysis                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  REPL ENVIRONMENT                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Variables (context stored here, NOT in LLM):              │ │
│  │  ├── hot_memory[]      ← Recent loci (full detail)         │ │
│  │  ├── warm_memory[]     ← Compressed clusters               │ │
│  │  ├── resonances{}      ← Pattern tracker                   │ │
│  │  ├── trace[]           ← Exploration path                  │ │
│  │  └── current_locus     ← Current position                  │ │
│  │                                                             │ │
│  │  Functions:                                                 │ │
│  │  ├── query_similar()   ← Vector search                     │ │
│  │  ├── query_by_domain() ← Filter by domain                  │ │
│  │  ├── get_neighbors()   ← Graph traversal                   │ │
│  │  └── llm_query()       ← Spawn sub-LLM                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  BACKING STORES (never loaded fully into LLM context)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  PostgreSQL  │  │  pgvector    │  │  Redis       │           │
│  │  (loci,      │  │  (embeddings,│  │  (hot cache, │           │
│  │   traces)    │  │   similarity)│  │   sessions)  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Session Management

```
POST   /api/v1/wander/sessions
       Create new wander session
       Body: { name, seed_concept, attractor?, allowed_domains?, forbidden_domains?,
               max_steps?, cloud_budget_cents?, temperature? }

GET    /api/v1/wander/sessions/{session_id}
       Get session details

GET    /api/v1/wander/sessions
       List sessions (with pagination)
       Query: ?project_id=&status=&limit=&offset=

PATCH  /api/v1/wander/sessions/{session_id}
       Update session (name, status, constraints)

DELETE /api/v1/wander/sessions/{session_id}
       Delete session and all associated data
```

### Wander Control

```
POST   /api/v1/wander/sessions/{session_id}/step
       Execute single wander step
       Returns: { step_number, from_locus, to_locus, residue, resonances_detected }

POST   /api/v1/wander/sessions/{session_id}/wander
       Execute multiple steps
       Body: { n_steps: 10 }
       Returns: { steps_completed, crystals_formed, stopped_reason? }

POST   /api/v1/wander/sessions/{session_id}/pause
       Pause active session

POST   /api/v1/wander/sessions/{session_id}/resume
       Resume paused session

POST   /api/v1/wander/sessions/{session_id}/stop
       Stop session (marks as completed)
```

### Memory Inspection

```
GET    /api/v1/wander/sessions/{session_id}/loci
       List all loci in session
       Query: ?visited=true&min_interestingness=0.5

GET    /api/v1/wander/sessions/{session_id}/loci/{locus_id}
       Get locus details with connections

GET    /api/v1/wander/sessions/{session_id}/trace
       Get full exploration trace

GET    /api/v1/wander/sessions/{session_id}/resonances
       Get resonances for session

GET    /api/v1/wander/sessions/{session_id}/crystals
       Get crystals formed in session
```

### Cross-Session Queries

```
GET    /api/v1/wander/crystals
       Get all crystals across sessions
       Query: ?project_id=&status=active&min_confidence=0.7

GET    /api/v1/wander/resonances
       Get global resonances
       Query: ?project_id=&status=confirmed

POST   /api/v1/wander/search
       Semantic search across all wander data
       Body: { query, types: ['locus', 'crystal', 'resonance'], limit }
```

### Manual Intervention

```
POST   /api/v1/wander/sessions/{session_id}/inject
       Inject a locus to guide exploration
       Body: { concept, force_visit: true }

POST   /api/v1/wander/sessions/{session_id}/fence
       Add embedding to fence (expand or contract)
       Body: { concept, action: 'include' | 'exclude' }

POST   /api/v1/wander/sessions/{session_id}/crystallize
       Force crystallization attempt at current locus
```

### MCP Tools (for Claude Code)

```python
# Tool definitions for agent use
tools = [
    {
        "name": "wander_create_session",
        "description": "Start a new wander exploration session",
        "parameters": {
            "name": "string",
            "seed_concept": "string",
            "attractor": "string (optional)",
            "allowed_domains": "string[] (optional)"
        }
    },
    {
        "name": "wander_step",
        "description": "Take one exploration step in a wander session",
        "parameters": {
            "session_id": "string"
        }
    },
    {
        "name": "wander_run",
        "description": "Run multiple wander steps",
        "parameters": {
            "session_id": "string",
            "n_steps": "integer (default 10)"
        }
    },
    {
        "name": "wander_get_insights",
        "description": "Get crystals and resonances from a session",
        "parameters": {
            "session_id": "string",
            "min_confidence": "float (default 0.7)"
        }
    },
    {
        "name": "wander_inject",
        "description": "Inject a concept to guide exploration",
        "parameters": {
            "session_id": "string",
            "concept": "string"
        }
    }
]
```

---

## Wander Step Algorithm

```python
async def wander_step(session: WanderSession) -> WanderStepResult:
    """Execute one step of the wander loop."""

    current_locus = get_current_locus(session)

    # 1. Generate adjacencies using multiple strategies
    adjacencies = []
    adjacencies += await distance_band_sample(current_locus, session)
    adjacencies += await cross_domain_bridge(current_locus, session)
    adjacencies += await analogical_reason(current_locus, session)
    adjacencies += await seek_tensions(current_locus, session)

    # 2. Filter by scope constraints
    adjacencies = [a for a in adjacencies if passes_scope_check(a, session)]

    # 3. Rank by composite score
    for adj in adjacencies:
        adj.score = (
            0.3 * adj.interestingness +
            0.3 * adj.novelty +
            0.2 * adj.bridge_potential +
            0.2 * adj.uncertainty
        )

    adjacencies.sort(key=lambda a: a.score, reverse=True)

    # 4. Select next via softmax sampling
    next_locus = softmax_select(adjacencies, temperature=session.temperature)

    # 5. Dwell: reflect on the encounter
    use_cloud = should_use_cloud(current_locus, next_locus, session)
    residue = await dwell(current_locus, next_locus, use_cloud, session)

    # 6. Check for resonance
    resonances = await check_resonances(residue, session)
    for resonance in resonances:
        await reinforce_resonance(resonance)

    # 7. Maybe crystallize
    if should_crystallize(next_locus, resonances, session):
        crystal = await crystallize(next_locus, resonances, session)
        if crystal:
            await emit_event('wander.crystal.formed', crystal)

    # 8. Update state
    trace = create_trace(session, current_locus, next_locus, residue)
    session.current_locus_id = next_locus.id
    session.step_count += 1

    # 9. Compress hot→warm if needed
    if len(get_hot_memory(session)) > HOT_MEMORY_LIMIT:
        await compress_to_warm(session)

    # 10. Emit event
    await emit_event('wander.step.completed', {
        'session_id': session.id,
        'step_number': session.step_count,
        'from_locus': current_locus,
        'to_locus': next_locus,
        'resonances_detected': len(resonances)
    })

    return WanderStepResult(
        step_number=session.step_count,
        from_locus=current_locus,
        to_locus=next_locus,
        residue=residue,
        resonances=resonances
    )
```

---

## Dweller Prompt Structure

> **Note**: The prompt below is for simple/direct dwelling. For production use with
> large memory, use the RLM-style prompt from the "Memory Interaction Architecture"
> section, which enables programmatic memory access via REPL.

```python
# Simple dwelling prompt (for small context / testing)
SIMPLE_DWELLING_PROMPT = """You are dwelling at a point in idea space, reflecting on an encounter between two concepts.

CURRENT LOCUS:
{current_concept}
- Domains: {current_domains}
- Abstraction level: {current_abstraction}

ENCOUNTERED LOCUS:
{next_concept}
- Domains: {next_domains}
- Abstraction level: {next_abstraction}

RECENT THEMES FROM THIS SESSION:
{recent_themes}

ACTIVE RESONANCES (patterns we've seen before):
{active_resonances}

Reflect on this encounter. For each question, provide a concise response (1-2 sentences):

1. CONNECTION: What links these two concepts? What do they share?
2. TENSION: Where do they conflict or create productive friction?
3. BRIDGE: What crosses domains here? What translation is possible?
4. SURPRISE: What's unexpected about this juxtaposition?
5. POSSIBILITY: What new concept or insight might emerge from this encounter?

Also extract:
- THEMES: List 3-5 thematic keywords
- INTERESTINGNESS: Rate 0.0-1.0 how interesting this encounter is
- ACTIONABILITY: Rate 0.0-1.0 how actionable insights here might be

Respond in JSON format:
{
  "connection": "...",
  "tension": "...",
  "bridge": "...",
  "surprise": "...",
  "possibility": "...",
  "themes": ["...", "..."],
  "interestingness": 0.X,
  "actionability": 0.X
}"""
```

---

## Framework Integration Analysis

### Tier 0: Core Pattern (Implement First)

| Pattern | Source | Use For |
|---------|--------|---------||
| **RLM (Recursive Language Model)** | [arXiv:2512.24601](https://arxiv.org/abs/2512.24601) | Memory interaction, context management, sub-LLM orchestration |

RLM is not a framework to integrate - it's the **core architectural pattern** for how Wander interacts with memory. See "Memory Interaction Architecture" section above.

### Tier 1: Most Relevant (Consider Forking/Integrating)

| Framework | License | Stars | Use For |
|-----------|---------|-------|---------|
| **Letta (MemGPT)** | Apache 2.0 | ~12k | Memory infrastructure foundation |
| **Mem0** | Apache 2.0 | ~24k | Graph-based memory relationships |
| **A-MEM** | Research | N/A | Zettelkasten-inspired memory evolution |

**Letta** provides:
- Tiered memory (core + archival)
- Context virtualization
- Stateful agent primitives
- Good fit for HOT/WARM/COLD architecture

**Mem0** provides:
- Universal memory layer
- Graph-based representations
- Production persistence
- Good fit for resonance/connection tracking

### Tier 2: Useful Components

| Framework | Use Case |
|-----------|----------|
| **LangGraph** | Stateful orchestration, computational graphs |
| **CrewAI** | Multi-agent role-playing if we need synthesis agents |
| **BabyAGI** | Lightweight task-planning patterns |

### Tier 3: Research Inspiration

| Paper/Project | Key Idea |
|--------------|----------|
| **CreativeDC** (Dec 2025) | Divergent-convergent scaffolding |
| **SAGE** | Self-evolving agents with reflective memory |
| **Agent Workflow Memory** | Procedural memory for multi-step workflows |
| **ExACT** | Reflective-MCTS for exploratory learning |

---

## Visual Encoding for Session Archives

### Token Comparison

| Format | Size | Use Case |
|--------|------|----------|
| Full JSON | 10,000-50,000 tokens | Database storage only |
| Compressed text | 500-2,000 tokens | LLM context injection |
| Image 1024×1024 | 1,000-2,000 tokens | Human review + vision LLM |
| Image 512×512 | 300-600 tokens | Compact visual summary |
| Session embedding | 1 vector | Similarity search |

### Standard Plot Encoding

UMAP projection of session:
- **Position**: Semantic similarity (UMAP from embeddings)
- **Color**: Domain (categorical palette)
- **Size**: Visit count / importance
- **Path**: Trace of exploration
- **Stars**: Crystal locations
- **Halos**: Resonance clusters

Vision models CAN interpret this format.

### Fractal Encoding (Experimental)

See [Fractal Security Concept](./FractalSecurity.md) for full specification.

---

## NATS Event Subjects

```
wander.session.created     # New session started
wander.session.paused      # Session paused
wander.session.resumed     # Session resumed
wander.session.completed   # Session finished

wander.step.started        # About to take step
wander.step.completed      # Step finished with results

wander.adjacencies.found   # Adjacencies generated (for visualization)
wander.locus.visited       # Locus visited

wander.resonance.detected  # New resonance candidate
wander.resonance.strengthened  # Existing resonance reinforced
wander.resonance.confirmed # Resonance graduated to confirmed

wander.crystal.formed      # New crystal created
wander.crystal.validated   # Crystal passed validation

wander.fence.approached    # Near fence boundary (warning)
wander.circuit.tripped     # Circuit breaker activated
wander.budget.low          # Budget running low (warning)
```

---

*This specification provides implementation details for the Wander system. See [Wander.md](./Wander.md) for concept overview.*
