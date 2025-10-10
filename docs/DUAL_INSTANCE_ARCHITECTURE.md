# CommandCenter Dual-Instance Architecture

**Version:** 1.0
**Date:** 2025-10-10
**Status:** Active Vision

---

## Overview

CommandCenter operates in **two distinct deployment modes**, each serving different needs:

1. **Global CommandCenter** - Organization-wide portfolio management via web UI
2. **Per-Project CommandCenter** - Project-embedded developer tooling via CLI/MCP/IDE integration

Both instances share the same codebase but are deployed and used differently.

---

## Architecture Vision

```
┌─────────────────────────────────────────────────────────────────┐
│                    GLOBAL COMMANDCENTER                          │
│                                                                  │
│  Web UI: http://commandcenter.company.com (or localhost:3000)  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Single Database (PostgreSQL)                         │      │
│  │  ┌────────────┬────────────┬────────────┬──────────┐ │      │
│  │  │ Project 1  │ Project 2  │ Project 3  │ Project N│ │      │
│  │  │ (Performia)│ (AI-Lab)   │ (Client-X) │ (...)    │ │      │
│  │  └────────────┴────────────┴────────────┴──────────┘ │      │
│  │                                                        │      │
│  │  Project Switcher Dropdown (filter by project_id)    │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  Features:                                                      │
│  - View/manage all projects in one place                       │
│  - Switch between projects via dropdown                        │
│  - Technology Radar (filterable by project)                    │
│  - Research Hub (cross-project view)                           │
│  - Knowledge Base (project-scoped queries)                     │
└─────────────────────────────────────────────────────────────────┘

                              │
                              │ Can deploy instances for
                              │ any project via UI
                              ▼

┌─────────────────────────────────────────────────────────────────┐
│              PER-PROJECT COMMANDCENTER INSTANCES                 │
│                                                                  │
│  Location: .commandcenter/ folder in each project repo         │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │   Performia      │  │   AI-Research    │  │   Client-X   │ │
│  │   ~/performia/   │  │   ~/ai-lab/      │  │   ~/client-x/│ │
│  │                  │  │                  │  │              │ │
│  │  .commandcenter/ │  │  .commandcenter/ │  │ .commandcenter/│
│  │  ├─ config.json  │  │  ├─ config.json  │  │ ├─config.json│ │
│  │  ├─ knowledge/   │  │  ├─ knowledge/   │  │ ├─knowledge/│ │
│  │  ├─ mcp-servers/ │  │  ├─ mcp-servers/ │  │ ├─mcp-servers/│
│  │  └─ .env         │  │  └─ .env         │  │ └─ .env      │ │
│  │                  │  │                  │  │              │ │
│  │  Isolated DB     │  │  Isolated DB     │  │  Isolated DB │ │
│  │  Isolated RAG    │  │  Isolated RAG    │  │  Isolated RAG│ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
│  Access Methods:                                                │
│  - CLI: `commandcenter research create "task"`                 │
│  - MCP: Claude Code/Cursor slash commands                      │
│  - IDE: Native integration via MCP servers                     │
│  - Web UI (optional): localhost:3010, :3020, etc.             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Global CommandCenter

### Purpose
Organization-wide view and management of ALL projects in a single interface.

### Deployment
**Single shared instance** (one deployment for entire organization):
```bash
# Typically deployed on shared server or localhost for solo use
cd ~/commandcenter-global/
docker-compose up -d

# Access at:
# - http://localhost:3000 (local development)
# - http://commandcenter.company.com (production)
```

### Database Structure
- **Single PostgreSQL database** with multi-project support
- `projects` table tracks all projects
- All other tables have `project_id` foreign key for isolation:
  - `repositories` - GitHub repos per project
  - `technologies` - Tech radar entries per project
  - `research_tasks` - Research items per project
  - `knowledge_entries` - RAG documents per project (ChromaDB collection: `project_{id}`)

### User Interface
**Web UI (React)** - Primary interface for global instance
- **Project Switcher Dropdown** (header) - Filter entire UI by project
- **Dashboard** - Overview of selected project
- **Technology Radar** - Visualize tech stack (filterable by project)
- **Research Hub** - Manage research tasks (cross-project view possible)
- **Knowledge Base** - Query documents (scoped to selected project)
- **Projects Page** - CRUD operations on projects
- **Settings** - Add repositories, configure access tokens

### Features
- ✅ Create/manage projects (add new projects to track)
- ✅ Switch between projects via dropdown (filters all views)
- ✅ Technology Radar per project (domain, status, relevance)
- ✅ Research task management (status, priority, tags)
- ✅ Knowledge Base with RAG (upload docs, query with vector/keyword/hybrid search)
- ✅ GitHub repository tracking (sync commits, monitor changes)
- ✅ Per-project data isolation (PostgreSQL + Redis + ChromaDB)

### Use Cases
- **Portfolio Manager**: "View technology adoption across all projects"
- **Team Lead**: "Track research progress for Client-X project"
- **Solo Developer**: "Manage personal R&D across multiple side projects"
- **Organization**: "Deploy CommandCenter instances for any project via UI"

### Current Status
**✅ Fully Implemented** (Phase 1b complete):
- Multi-project database architecture
- Project switcher UI
- Projects CRUD page
- Per-project data isolation (DB, cache, ChromaDB)
- KnowledgeBeast integration with hybrid search

---

## 2. Per-Project CommandCenter

### Purpose
Project-specific developer tooling embedded directly in the codebase.

### Deployment
**One instance per project repository** (embedded in `.commandcenter/` folder):
```bash
# Lives inside each project's repo
~/projects/performia/.commandcenter/
~/projects/ai-research/.commandcenter/
~/projects/client-x/.commandcenter/
```

### Folder Structure
```
.commandcenter/
├── config.json              # Project-specific configuration
├── .env                     # Isolated secrets and API keys
├── knowledge/               # Per-project knowledge base
│   ├── documents/           # Uploaded docs (PDFs, markdown, etc.)
│   └── chroma_db/          # ChromaDB vector storage (isolated)
├── mcp-servers/            # MCP server configurations
│   ├── knowledgebeast/     # RAG MCP server
│   ├── agentflow/          # Agent coordination MCP
│   └── viztrtr/            # UI/UX analysis MCP
├── prompts/                # AgentFlow prompt templates
├── agents/                 # Agent definitions (agents.json)
└── .agent-coordination/    # Multi-agent status tracking
```

### Access Methods

#### 1. CLI Tools (Primary)
```bash
# From project directory
cd ~/projects/performia/

# Research management
commandcenter research create "Investigate JUCE 8.0 migration"
commandcenter research list --status in-progress
commandcenter research update 123 --status completed

# Technology tracking
commandcenter tech add --domain audio --title "JUCE 8.0" --status evaluating
commandcenter tech list --domain audio

# Knowledge base queries
commandcenter ask "How did we implement spatial audio?"
commandcenter knowledge upload ./docs/research-notes.pdf --category research
commandcenter knowledge search "reverb algorithm" --mode hybrid

# Repository tracking
commandcenter repo sync
commandcenter repo status
```

#### 2. MCP Server Integration (IDE)
```bash
# In Claude Code, Cursor, or other MCP-enabled IDE
/research "spatial audio techniques"       # Queries project's knowledge base
/track-tech JUCE 8.0.0                    # Adds to project's tech radar
/ask "how did we implement reverb?"       # RAG search in project docs
/start-workflow feature-development       # Launch AgentFlow workflow
/analyze-ui components/AudioPlayer.tsx    # VIZTRTR UI analysis
```

#### 3. Web UI (Optional)
```bash
# Start project-specific UI (optional)
cd ~/projects/performia/.commandcenter/
docker-compose up -d

# Access at project-specific port
http://localhost:3010  # Performia
http://localhost:3020  # AI-Research
http://localhost:3030  # Client-X
```

### Data Isolation
**Each project instance has completely isolated data:**
- Separate SQLite/PostgreSQL database (per-project)
- Separate ChromaDB collection (no cross-project contamination)
- Separate Redis cache (namespaced by project)
- Separate environment variables and secrets
- Separate GitHub tokens (no cross-repo access)

**Security Benefits:**
- Proprietary research stays within project boundaries
- No risk of data leakage between projects
- Confidential client work remains isolated
- RAG embeddings don't mix (music ≠ AI papers)

### Features (Planned)

#### Phase 2: CLI Foundation
- [ ] `commandcenter` CLI tool (Python/TypeScript)
- [ ] Core commands: research, tech, knowledge, repo
- [ ] Auto-detection of `.commandcenter/` folder
- [ ] Configuration management (config.json, .env)

#### Phase 3: MCP Server Integration
- [ ] KnowledgeBeast MCP server (RAG queries)
- [ ] AgentFlow Coordinator MCP (multi-agent workflows)
- [ ] VIZTRTR MCP (UI/UX analysis)
- [ ] API Manager MCP (multi-provider AI routing)
- [ ] Slash command definitions for IDEs

#### Phase 4: IDE Integration
- [ ] Claude Code integration (slash commands)
- [ ] Cursor integration
- [ ] VS Code extension (optional)
- [ ] Auto-discovery of `.commandcenter/` in workspace

### Use Cases
- **Developer**: "Ask CommandCenter about codebase context while coding"
- **AI Assistant**: "Claude Code queries project knowledge base automatically"
- **Automation**: "CI/CD pipeline updates tech radar on dependency changes"
- **Research**: "Store findings in project-specific knowledge base"

### Current Status
**❌ Not Yet Implemented** (Planned for Phase 2-4):
- CLI tool not built
- MCP servers not deployed
- `.commandcenter/` folder structure not defined
- IDE integration not available

---

## Key Differences Summary

| Aspect | Global Instance | Per-Project Instance |
|--------|-----------------|----------------------|
| **Count** | 1 (shared) | Many (1 per repo) |
| **Purpose** | Portfolio management | Development workflow |
| **Primary Interface** | Web UI (manual) | CLI + MCP + IDE (automated) |
| **Database** | Single shared PostgreSQL | Isolated per project |
| **Scope** | All projects (switchable) | Single project only |
| **Users** | Managers, team leads, solo devs | Developers, AI assistants |
| **Access** | Browser-based | Terminal + IDE integration |
| **Deployment** | Shared server or localhost | Embedded in each repo |
| **Knowledge Base** | Project-scoped queries | Fully isolated RAG |
| **Security** | `project_id` isolation | Complete data separation |

---

## Implementation Roadmap

### Phase 1: Global Instance ✅ COMPLETE
- [x] Multi-project database architecture
- [x] Project CRUD endpoints and UI
- [x] Project switcher dropdown
- [x] Per-project data isolation (DB, cache, ChromaDB)
- [x] KnowledgeBeast integration (hybrid search)
- [x] Technology Radar and Research Hub
- [x] GitHub repository tracking

### Phase 2: Per-Project CLI (Next Priority)
- [ ] Define `.commandcenter/` folder structure
- [ ] Build `commandcenter` CLI tool
- [ ] Implement core commands (research, tech, knowledge, repo)
- [ ] Auto-detection and configuration management
- [ ] Documentation and usage guides

### Phase 3: MCP Server Layer
- [ ] KnowledgeBeast MCP server wrapper
- [ ] AgentFlow Coordinator MCP server
- [ ] VIZTRTR MCP server
- [ ] API Manager MCP (multi-provider routing)
- [ ] MCP server discovery and registration

### Phase 4: IDE Integration
- [ ] Claude Code slash commands
- [ ] Cursor integration
- [ ] Auto-discovery of `.commandcenter/` in workspace
- [ ] Contextual suggestions and auto-completion

### Phase 5: Advanced Features
- [ ] Enhanced Technology Radar features (you mentioned adding more)
- [ ] Enhanced Research Hub features (you mentioned adding more)
- [ ] Cross-instance sync (optional: per-project → global)
- [ ] Collaborative features (team research sharing)

---

## FAQ

### Q: Do I need both instances?
**A:** No, use what fits your workflow:
- **Solo developer managing multiple projects?** → Start with global instance only
- **Team wanting portfolio view?** → Deploy global instance
- **Developer wanting IDE integration?** → Use per-project instance
- **Organization doing both?** → Deploy both (independent)

### Q: Can per-project instances sync to global?
**A:** Not currently implemented, but planned as optional feature:
- Per-project instance can push research/tech to global via API
- Global instance remains source of truth
- Per-project can pull shared technologies from global
- Full sync vs. manual publish (TBD)

### Q: What if I only want CLI tools without isolation?
**A:** You can point CLI tools to global instance:
```bash
# Configure CLI to use global instance
commandcenter config set --instance-url http://localhost:8000
commandcenter config set --project-id 1  # Performia
```

### Q: Can I run multiple per-project instances simultaneously?
**A:** Yes, they are fully isolated:
- Each uses different ports (or no web UI)
- Separate databases and knowledge bases
- No conflicts or data leakage

---

## Next Steps

**Immediate Priorities:**
1. Complete KnowledgeBeast E2E testing (models downloading)
2. Document current global instance capabilities
3. Design `.commandcenter/` folder structure (Phase 2)
4. Build MVP CLI tool for per-project usage
5. Plan MCP server architecture (Phase 3)

**User Feedback Needed:**
- What additional Tech Radar features do you want?
- What additional Research Hub features do you want?
- CLI command syntax preferences?
- MCP slash command naming conventions?

---

**Document Status:** Living document - will be updated as implementation progresses.
