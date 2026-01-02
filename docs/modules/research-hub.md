# Research Hub

**R&D Task Management**

Research Hub tracks research activities, technology evaluations, and findings. It's the structured counterpart to Wander's unstructured exploration.

## Overview

Research Hub manages:
- Research tasks and projects
- Technology evaluations (radar)
- Document uploads and findings
- Team coordination

## Technology Radar

Track technologies through lifecycle stages:

```
DISCOVER → RESEARCH → EVALUATE → IMPLEMENT → INTEGRATED
```

| Stage | Meaning |
|-------|---------|
| Discover | Heard about it, might be relevant |
| Research | Actively learning, gathering info |
| Evaluate | Testing, POC, benchmarking |
| Implement | Building with it, rolling out |
| Integrated | Part of standard stack |

## Research Tasks

Structured research with:
- Clear objectives
- Document attachments
- Findings and conclusions
- Links to hypotheses (AI Arena)

## Integration Points

| Module | Integration |
|--------|-------------|
| KnowledgeBeast | Findings stored and searchable |
| AI Arena | Tasks can spawn validation hypotheses |
| Wander | Structured findings seed exploration |
| VISLZR | Visualize research status, dependencies |

## API

```
GET  /api/v1/research-tasks
POST /api/v1/research-tasks
GET  /api/v1/research-tasks/{id}
PUT  /api/v1/research-tasks/{id}

GET  /api/v1/technologies
POST /api/v1/technologies
PUT  /api/v1/technologies/{id}/stage
```

## Data Model

```
ResearchTask
├── id, title, description
├── status (backlog|active|blocked|complete)
├── priority, due_date
├── documents[]
├── findings[]
├── hypothesis_ids[] (linked AI Arena)
└── created_at, updated_at

Technology
├── id, name, description
├── category, tags[]
├── stage (discover|research|evaluate|implement|integrated)
├── evaluation_notes
├── research_task_ids[]
└── last_evaluated

Finding
├── id, task_id
├── content, evidence[]
├── confidence
└── created_at
```

## Actions (VISLZR node)

- view radar
- create task
- update stage
- add finding
- link hypothesis

## Status

✅ **Working** - Core CRUD operational, UI in main frontend
