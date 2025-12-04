# MRKTZR Module

**AI Marketing and Partnership Intelligence** module for CommandCenter.

## Overview

MRKTZR automates marketing execution and partnership development through AI-powered agents:

- **Content Generation** - AI-powered social media posts, blog content, video scripts
- **Avatar Management** - AI-powered brand representation
- **Social Media Automation** - Cross-platform scheduling and engagement
- **Analytics** - Performance tracking and optimization

## Architecture

```
mrktzr/
├── src/
│   ├── agents/           # CommandCenter-compatible agents
│   │   └── content-creator/  # Genkit-powered content generation
│   ├── services/         # Business logic
│   ├── models/           # Data models (Zod schemas)
│   ├── api/              # REST endpoints
│   └── core/             # Core AI flows (Genkit)
└── docs/                 # Integration documentation
    ├── 01_STRATEGY/      # Integration concept and improvements
    ├── 02_TECH_BLUEPRINT/# Architecture, APIs, security
    ├── 03_ROADMAP/       # Phase plan and milestones
    ├── 04_AGENTIC_AUTOMATION/  # Agent design
    └── 05_APPENDIX/      # Stack comparison, credits
```

## Integration with CommandCenter

MRKTZR connects to CommandCenter via:

1. **Knowledge API** - Receives topic briefs and research from RAG
2. **Event Bus** - NATS JetStream for async communication
3. **Analytics Feedback** - Returns engagement metrics for learning loop

```
CommandCenter (collect → analyze → synthesize)
     ↓ Topic Briefs
MRKTZR (create → test → publish)
     ↓ Campaigns
Social Platforms
     ↓ Engagement Data
CommandCenter (learning loop)
```

## Quick Start

```bash
cd hub/modules/mrktzr
npm install
npm run dev
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/content` | POST | Generate content from topic |
| `/content/:id` | GET | Get content by ID |
| `/auth/login` | POST | Authenticate user |

## Technology Stack

- **Genkit** - AI orchestration framework
- **Google GenAI** - Gemini models for content generation
- **Express** - REST API server
- **Zod** - Schema validation
- **TypeScript** - Type-safe development

## Documentation

See `docs/` for comprehensive integration documentation:

- [Integration Concept](docs/01_STRATEGY/Integration_Concept.md)
- [Architecture](docs/02_TECH_BLUEPRINT/Integration_Architecture.md)
- [Phase Plan](docs/03_ROADMAP/Phase_Plan.md)
- [Agent Design](docs/04_AGENTIC_AUTOMATION/LLM_Agent_Design.md)

## Status

**Migration Status**: Initial import from standalone MRKTZR project

| Feature | Status |
|---------|--------|
| Content Generation | Prototype |
| Social Scheduling | Planned |
| Analytics | Planned |
| CommandCenter Integration | In Progress |

---

*Part of CommandCenter Hub - AI-Native R&D Management*
