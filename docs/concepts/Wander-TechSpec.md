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

```python
DWELLING_PROMPT = """You are dwelling at a point in idea space, reflecting on an encounter between two concepts.

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
