# KnowledgeBeast

**Vector Store, RAG, and Knowledge Graph**

KnowledgeBeast is CommandCenter's unified knowledge layer. Everything learned, discovered, or ingested lives here and is queryable by both humans and agents.

## Overview

KnowledgeBeast combines:
- **Vector Store**: Semantic search via pgvector
- **Knowledge Graph**: Relationships between entities
- **RAG Pipeline**: Retrieval-augmented generation for queries
- **Ingestion**: Multi-source content processing

## Capabilities

### Semantic Search
Query by meaning, not just keywords:
```
"What do we know about prediction market accuracy?"
→ Returns relevant chunks from ingested docs, crystals, research
```

### Knowledge Graph
Entities and relationships:
```
[Contact: Alice] --works_at--> [Organization: Acme Corp]
[Crystal: PM-accuracy] --validates--> [Hypothesis: markets-beat-polls]
[Document: SEC-filing] --mentions--> [Organization: Acme Corp]
```

### Multi-Source Ingestion

| Source | Method |
|--------|--------|
| Documents | Upload, parse, chunk, embed |
| RSS Feeds | Subscribe, auto-ingest |
| Webhooks | Receive events, extract knowledge |
| File Watchers | Monitor directories |
| Crystals | Auto-ingested from Wander |
| CRM Data | Contacts, orgs, interactions from MRKTZR |

### Queryable by Agents
Agents can query KnowledgeBeast via MCP tools:
```python
# Agent querying knowledge
results = knowledge_beast.search("rollup opportunities in HVAC")
for r in results:
    print(r.content, r.relevance_score)
```

## Integration Points

Every module reads from and writes to KnowledgeBeast:

| Module | Reads | Writes |
|--------|-------|--------|
| Wander | Exploration source | Crystals |
| AI Arena | Evidence for debates | Validated hypotheses |
| MRKTZR | Contact/org intelligence | CRM data, interactions |
| ROLLIZR | Company data | Opportunity analyses |
| Veria | Market intelligence | Trading outcomes |
| Research Hub | Research history | Findings |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      KNOWLEDGEBEAST                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Ingestion  │  │   Storage   │  │   Query     │             │
│  │  Pipeline   │  │             │  │   Engine    │             │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤             │
│  │ • Parse     │  │ • Vectors   │  │ • Semantic  │             │
│  │ • Chunk     │  │   (pgvector)│  │ • Graph     │             │
│  │ • Embed     │  │ • Graph     │  │ • Hybrid    │             │
│  │ • Extract   │  │   (postgres)│  │ • Filters   │             │
│  │   entities  │  │ • Metadata  │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## API

```
POST /api/v1/knowledge/ingest
GET  /api/v1/knowledge/search?q=...
GET  /api/v1/knowledge/entity/{id}
GET  /api/v1/knowledge/graph?entity_id=...
POST /api/v1/knowledge/ask  (RAG query)
```

## Data Model

```
Document
├── id, source, source_id
├── title, content, content_hash
├── metadata{}
├── chunks[]
└── ingested_at

Chunk
├── id, document_id
├── content, embedding (vector)
├── position, token_count
└── entities[] (extracted)

Entity
├── id, type (person|org|concept|...)
├── name, aliases[]
├── properties{}
└── relationships[]

Relationship
├── id, from_entity_id, to_entity_id
├── type (works_at|mentions|validates|...)
├── properties{}
└── source_chunk_id
```

## Actions (VISLZR node)

- search
- ingest document
- view entity
- explore graph
- recent ingestions
- statistics

## Status

✅ **Working** - Core RAG operational, graph partially implemented
