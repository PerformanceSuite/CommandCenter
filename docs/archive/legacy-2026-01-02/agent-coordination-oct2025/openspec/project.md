# Project Context: CommandCenter MCP Development

## Purpose
CommandCenter is an R&D management and knowledge base system. **Current Goal**: Build Model Context Protocol (MCP) infrastructure to enable `commandcenter analyze ~/Projects/performia --launch-agents` workflow for automated project analysis and research task generation.

## Tech Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Database**: PostgreSQL 15, Redis
- **AI/ML**: ChromaDB, LangChain, HuggingFaceEmbeddings
- **Infrastructure**: Docker Compose, GitHub Actions
- **Testing**: pytest (backend), Vitest (frontend)

## Project Conventions

### Code Style
- **Python**: Black formatter (line length 100), Flake8 linter, type hints required
- **TypeScript**: ESLint + Prettier, strict mode enabled
- **Imports**: Absolute imports preferred (`from app.services import ...`)
- **Naming**: snake_case (Python), camelCase (TypeScript), PascalCase (classes/components)

### Architecture Patterns
- **Service Layer Pattern**: Routers → Services → Models → Schemas
- **Async-first**: All database operations use async/await
- **Dependency Injection**: FastAPI dependencies for database sessions
- **Error Handling**: Custom exceptions, FastAPI exception handlers
- **Configuration**: Pydantic Settings for environment variables

### Testing Strategy
- **Coverage Target**: 80%+ for new code
- **Test Structure**: `tests/unit/`, `tests/integration/`, `tests/e2e/`
- **Fixtures**: pytest fixtures for database, API client
- **Mocking**: `pytest-mock` for external dependencies
- **CI**: All tests must pass before merge

### Git Workflow
- **Branch Strategy**: Feature branches from `main` (git worktrees for parallel agents)
- **Commit Convention**: `type(scope): description` (feat, fix, docs, refactor, test, chore)
- **PR Process**: 10/10 review score required, all tests passing, squash merge
- **Agent Branches**: `agent/{agent-name}` pattern for parallel development

## Domain Context

### MCP (Model Context Protocol)
- Protocol for AI assistants to expose capabilities (resources, tools, prompts)
- JSON-RPC 2.0 based communication
- Enable IDE integration (Claude Code, Cursor, etc.)
- CommandCenter will expose project analysis and research orchestration via MCP

### Current Phase: Phase 1 - Foundation Infrastructure
Three parallel agents building:
1. **MCP Core** - JSON-RPC protocol, server, provider interfaces
2. **Project Analyzer** - Language parsers, tech detection, dependency analysis
3. **CLI Interface** - Click-based commands for `commandcenter analyze`

### Multi-Agent Coordination
- **Git Worktrees**: Each agent in `.agent-worktrees/{agent-name}/`
- **OpenSpec**: Spec-driven development with delta-based change tracking
- **Checkpoint Execution**: 2-hour sprints with coordinator review
- **File-Based Coordination**: STATUS.json, COMMUNICATION.md for agent sync

## Important Constraints

### Security
- **Data Isolation**: Each CommandCenter instance for single project only
- **Token Encryption**: Repository access tokens encrypted at rest
- **No Hardcoded Secrets**: All sensitive data via environment variables
- **API Rate Limiting**: GitHub API calls must respect rate limits

### Performance
- **Async Operations**: All I/O operations must be async
- **Database Connection Pooling**: Max 20 connections per instance
- **RAG Query Limits**: Max 10 documents per query
- **CLI Response Time**: Commands should complete in <5 seconds

### Compatibility
- **Python Version**: Must work with Python 3.11+
- **Node Version**: Frontend requires Node 20+
- **Database**: PostgreSQL 15+ required for JSON operations
- **Docker**: Compose V2 required

## External Dependencies

### APIs
- **GitHub API**: Repository access, commit tracking (requires PAT)
- **Anthropic API** (optional): Claude models for AI features
- **OpenAI API** (optional): Alternative LLM provider

### Services
- **PostgreSQL**: Primary database
- **Redis**: Caching and session storage
- **ChromaDB**: Vector storage for RAG
- **Docker**: Container runtime

### Libraries
- **PyGithub**: GitHub API wrapper
- **LangChain**: RAG framework
- **Click**: CLI framework (will be used for `commandcenter` CLI)
- **Pydantic**: Data validation and settings
- **SQLAlchemy**: ORM

## Checkpoint Workflow

### Coordination Files
- **`STATUS.json`**: Real-time agent progress tracking
- **`COMMUNICATION.md`**: Async message board for agent questions
- **`openspec/changes/`**: OpenSpec change proposals per checkpoint
- **`feedback/`**: Coordinator feedback for agents

### Agent Responsibilities
- Work in isolated git worktrees
- Implement against OpenSpec change proposals
- Update STATUS.json after each commit
- Post blockers to COMMUNICATION.md
- Use stubs for dependencies not yet available
- Write tests alongside implementation
- Self-review before marking checkpoint complete

### Coordinator Responsibilities (Claude)
- Review STATUS.json after each checkpoint
- Run integration tests on merged branches
- Generate feedback reports for each agent
- Detect and resolve conflicts early
- Update COMMUNICATION.md with coordination decisions
- Validate OpenSpec changes
- Approve checkpoint completion

## Multi-Agent Success Criteria

### Checkpoint Success
- ✅ All agents report progress ≥ target (40%, 80%, 100%)
- ✅ Tests passing for completed deliverables
- ✅ No merge conflicts (or resolved automatically)
- ✅ Integration tests pass
- ✅ OpenSpec validation passes (`openspec validate --strict`)
- ✅ STATUS.json shows no critical blockers

### Phase Success
- ✅ All checkpoints complete
- ✅ Full test suite passes (131/131 tests target)
- ✅ End-to-end workflow works
- ✅ Code quality: linters pass, types check
- ✅ All OpenSpec changes archived
- ✅ No "STUB" markers in final code
- ✅ Documentation complete

### Project Success
- ✅ `commandcenter analyze ~/Projects/test-project` works
- ✅ Detects technologies correctly
- ✅ Outputs analysis results
- ✅ All 3 agents' code merged to main
- ✅ Ready for Phase 2 (MCP server implementations)
