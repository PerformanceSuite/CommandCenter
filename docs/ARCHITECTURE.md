# Command Center Architecture

This document provides a comprehensive overview of Command Center's system architecture, design patterns, and implementation details.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Layers](#architecture-layers)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Data Layer](#data-layer)
- [RAG Pipeline](#rag-pipeline)
- [Security Model](#security-model)
- [Service Layer Patterns](#service-layer-patterns)
- [API Design](#api-design)
- [Deployment Architecture](#deployment-architecture)
- [Scalability Considerations](#scalability-considerations)
- [Future Architecture](#future-architecture)

---

## System Overview

Command Center is a full-stack application designed for R&D management and knowledge base operations. It follows a modern three-tier architecture with clear separation of concerns.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│              Browser/Client Layer                    │
│         React SPA (TypeScript + Vite)               │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────┐
│            Application Layer (FastAPI)               │
│  ┌──────────┬──────────┬──────────┬──────────┐     │
│  │  Routers │ Services │ Schemas  │  Models  │     │
│  └──────────┴──────────┴──────────┴──────────┘     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                Data Layer                            │
│  ┌──────────┬──────────┬──────────────────────┐    │
│  │PostgreSQL│  Redis   │  ChromaDB (Vectors)  │    │
│  └──────────┴──────────┴──────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- **Framework:** FastAPI 0.104+ (Python 3.11+)
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Async Runtime:** asyncio + uvicorn
- **HTTP Client:** httpx (async)

**Frontend:**
- **Framework:** React 18
- **Language:** TypeScript 5
- **Build Tool:** Vite 5
- **Styling:** Tailwind CSS 3
- **State Management:** React Context + hooks
- **HTTP Client:** fetch API

**Data Layer:**
- **Primary DB:** PostgreSQL 16
- **Cache:** Redis 7
- **Vector Store:** ChromaDB
- **Embeddings:** sentence-transformers (local, no API costs)

**Infrastructure:**
- **Containerization:** Docker + Docker Compose
- **Reverse Proxy:** Traefik (optional)
- **Process Manager:** uvicorn (production: gunicorn)

---

## Architecture Layers

### 1. Presentation Layer (Frontend)

**Responsibility:** User interface and user experience

**Components:**
- **Pages:** Top-level route components
- **Components:** Reusable UI elements
- **Services:** API communication layer
- **Hooks:** Custom React hooks for state/logic
- **Types:** TypeScript type definitions

**Design Patterns:**
- Component composition
- Custom hooks for reusability
- Service layer abstraction
- Type-safe API contracts

### 2. Application Layer (Backend)

**Responsibility:** Business logic and API endpoints

**Components:**
- **Routers:** API endpoint definitions
- **Services:** Business logic implementation
- **Schemas:** Request/response validation
- **Models:** Database models
- **Utils:** Helper functions

**Design Patterns:**
- Service layer pattern
- Repository pattern (via ORM)
- Dependency injection
- Async/await for I/O

### 3. Data Layer

**Responsibility:** Data persistence and retrieval

**Components:**
- **PostgreSQL:** Relational data
- **Redis:** Caching and sessions
- **ChromaDB:** Vector embeddings for RAG

---

## Backend Architecture

### Directory Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   └── env.py                  # Migration configuration
├── app/
│   ├── models/                 # SQLAlchemy models
│   │   ├── repository.py       # Repository model
│   │   ├── technology.py       # Technology model
│   │   ├── research_task.py    # Research task model
│   │   └── knowledge_entry.py  # Knowledge entry model
│   ├── routers/                # API endpoints
│   │   ├── repositories.py     # Repository endpoints
│   │   ├── technologies.py     # Technology endpoints
│   │   └── dashboard.py        # Dashboard endpoints
│   ├── schemas/                # Pydantic schemas
│   │   ├── repository.py       # Repository schemas
│   │   ├── technology.py       # Technology schemas
│   │   └── research.py         # Research task schemas
│   ├── services/               # Business logic
│   │   ├── github_service.py   # GitHub integration
│   │   └── rag_service.py      # RAG/knowledge base
│   ├── utils/                  # Utilities
│   │   ├── encryption.py       # Token encryption
│   │   └── validators.py       # Custom validators
│   ├── config.py               # Configuration management
│   ├── database.py             # Database setup
│   └── main.py                 # Application entry point
├── tests/                      # Test suite
└── requirements.txt            # Python dependencies
```

### Core Patterns

#### 1. Service Layer Pattern

Services encapsulate business logic and external integrations:

```python
class GitHubService:
    """GitHub API integration service"""

    def __init__(self, access_token: Optional[str] = None):
        self.token = access_token or settings.github_token
        self.github = Github(self.token)

    async def sync_repository(self, owner: str, name: str) -> Dict:
        """Sync repository with GitHub API"""
        repo = self.github.get_repo(f"{owner}/{name}")
        # Business logic here
        return sync_info
```

**Benefits:**
- Separation of concerns
- Testable business logic
- Reusable across routers
- External API abstraction

#### 2. Dependency Injection

FastAPI's dependency injection for database sessions, services, and authentication:

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency"""
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/repositories")
async def list_repositories(
    db: AsyncSession = Depends(get_db)
) -> List[Repository]:
    # Use db session
    pass
```

**Benefits:**
- Clean separation of concerns
- Easy testing with mocks
- Lifecycle management
- Request-scoped resources

#### 3. Async/Await Pattern

All I/O operations use async/await for concurrency:

```python
@router.post("/{repository_id}/sync")
async def sync_repository(
    repository_id: int,
    db: AsyncSession = Depends(get_db)
) -> RepositorySyncResponse:
    # Async database query
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repository = result.scalar_one_or_none()

    # Async external API call
    github_service = GitHubService(repository.access_token)
    sync_info = await github_service.sync_repository(...)

    return sync_info
```

**Benefits:**
- High concurrency
- Efficient I/O handling
- Better resource utilization
- Non-blocking operations

#### 4. Schema Validation

Pydantic schemas for request/response validation:

```python
class RepositoryCreate(BaseModel):
    """Schema for creating a repository"""
    owner: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    @field_validator('owner', 'name')
    @classmethod
    def validate_github_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$', v):
            raise ValueError('Invalid GitHub name format')
        return v
```

**Benefits:**
- Automatic validation
- Clear API contracts
- Type safety
- Documentation generation

---

## Frontend Architecture

### Directory Structure

```
frontend/
├── src/
│   ├── components/             # Reusable components
│   │   ├── common/             # Common UI components
│   │   ├── repositories/       # Repository components
│   │   ├── technologies/       # Technology components
│   │   └── dashboard/          # Dashboard components
│   ├── pages/                  # Page components
│   │   ├── Dashboard.tsx       # Dashboard page
│   │   ├── Repositories.tsx    # Repositories page
│   │   └── Technologies.tsx    # Technologies page
│   ├── services/               # API service layer
│   │   ├── api.ts              # Base API client
│   │   ├── repositories.ts     # Repository API
│   │   └── technologies.ts     # Technology API
│   ├── hooks/                  # Custom React hooks
│   │   ├── useRepositories.ts  # Repository data hook
│   │   └── useTechnologies.ts  # Technology data hook
│   ├── types/                  # TypeScript types
│   │   ├── repository.ts       # Repository types
│   │   └── technology.ts       # Technology types
│   ├── utils/                  # Utility functions
│   ├── App.tsx                 # Main application
│   └── main.tsx                # Entry point
└── tests/                      # Test suite
```

### Core Patterns

#### 1. Component Composition

Breaking UI into reusable components:

```typescript
// RepositoryCard.tsx
interface RepositoryCardProps {
  repository: Repository;
  onSync: (id: number) => Promise<void>;
}

export const RepositoryCard: React.FC<RepositoryCardProps> = ({
  repository,
  onSync,
}) => {
  return (
    <Card>
      <CardHeader title={repository.full_name} />
      <CardBody description={repository.description} />
      <CardActions onSync={() => onSync(repository.id)} />
    </Card>
  );
};
```

#### 2. Custom Hooks

Encapsulating data fetching and state management:

```typescript
// useRepositories.ts
export const useRepositories = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRepositories = async () => {
      const data = await repositoryService.getAll();
      setRepositories(data);
      setLoading(false);
    };
    fetchRepositories();
  }, []);

  const sync = async (id: number) => {
    await repositoryService.sync(id);
    // Refresh data
  };

  return { repositories, loading, sync };
};
```

#### 3. Service Layer

Abstracting API calls:

```typescript
// services/repositories.ts
class RepositoryService {
  private baseUrl = '/api/v1/repositories';

  async getAll(): Promise<Repository[]> {
    const response = await fetch(this.baseUrl);
    return response.json();
  }

  async sync(id: number): Promise<SyncResponse> {
    const response = await fetch(`${this.baseUrl}/${id}/sync`, {
      method: 'POST',
    });
    return response.json();
  }
}

export const repositoryService = new RepositoryService();
```

---

## Data Layer

### Database Schema

#### Entity Relationship Diagram

```
┌─────────────────┐
│  Repository     │
├─────────────────┤
│ id (PK)         │───┐
│ owner           │   │
│ name            │   │
│ full_name       │   │
│ access_token    │   │
│ ...             │   │
└─────────────────┘   │
                      │
                      │  ┌─────────────────┐
                      ├──│ ResearchTask    │
                      │  ├─────────────────┤
                      │  │ id (PK)         │
┌─────────────────┐   │  │ repository_id   │──┐
│  Technology     │   │  │ technology_id   │  │
├─────────────────┤   │  │ title           │  │
│ id (PK)         │───┤  │ status          │  │
│ title           │   │  │ ...             │  │
│ domain          │   │  └─────────────────┘  │
│ status          │   │                       │
│ ...             │   │                       │
└─────────────────┘   │  ┌─────────────────┐  │
                      │  │ KnowledgeEntry  │  │
                      └──┤─────────────────┤──┘
                         │ id (PK)         │
                         │ technology_id   │
                         │ task_id         │
                         │ content         │
                         │ ...             │
                         └─────────────────┘
```

#### Key Models

**Repository:**
- Tracks GitHub repositories
- Stores encrypted access tokens
- Maintains sync metadata
- Links to research tasks

**Technology:**
- Technology radar entries
- Domain categorization
- Status tracking (discovery → integrated)
- Priority and relevance scoring

**ResearchTask:**
- Research activities
- Links to technologies and repositories
- Status tracking (pending → completed)
- Document uploads and findings

**KnowledgeEntry:**
- RAG knowledge base entries
- Links to technologies and tasks
- Metadata for vector search

### Database Patterns

#### 1. SQLAlchemy 2.0 Async

```python
class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))

    # Relationships
    research_tasks: Mapped[list["ResearchTask"]] = relationship(
        "ResearchTask",
        back_populates="repository",
        cascade="all, delete-orphan"
    )
```

#### 2. Migrations with Alembic

```python
# alembic/versions/xxx_add_repositories.py
def upgrade():
    op.create_table(
        'repositories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(512), nullable=False, unique=True),
        # ... more columns
    )
```

#### 3. Encrypted Tokens

```python
# utils/encryption.py
class TokenEncryption:
    """Encrypt/decrypt GitHub tokens"""

    def encrypt(self, token: str) -> str:
        """Encrypt token using Fernet"""
        f = Fernet(settings.SECRET_KEY.encode())
        return f.encrypt(token.encode()).decode()

    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt token"""
        f = Fernet(settings.SECRET_KEY.encode())
        return f.decrypt(encrypted_token.encode()).decode()
```

---

## RAG Pipeline

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Document Ingestion                      │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │  PDF   │  │Markdown│  │  DOCX  │  │  TXT   │   │
│  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘   │
└──────┼───────────┼───────────┼───────────┼─────────┘
       │           │           │           │
       └───────────┴───────────┴───────────┘
                       │
       ┌───────────────▼───────────────┐
       │      Docling Processing       │
       │  (Document Understanding)     │
       └───────────────┬───────────────┘
                       │
       ┌───────────────▼───────────────┐
       │       Text Chunking           │
       │  (RecursiveCharacterSplitter) │
       └───────────────┬───────────────┘
                       │
       ┌───────────────▼───────────────┐
       │    Embedding Generation       │
       │  (sentence-transformers)      │
       └───────────────┬───────────────┘
                       │
       ┌───────────────▼───────────────┐
       │    Vector Store (ChromaDB)    │
       └───────────────────────────────┘
                       │
       ┌───────────────▼───────────────┐
       │    Similarity Search          │
       │  (Query → Top-K Results)      │
       └───────────────────────────────┘
```

### Components

#### 1. Document Processing (Docling)

```python
# Docling handles complex document structures
# - Tables, images, headers, sections
# - Multi-column layouts
# - PDF parsing with OCR fallback
```

#### 2. Embedding Model

```python
# Local embedding model (no API costs)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
# Model specs:
# - 384 dimensions
# - ~22 million parameters
# - ~90MB disk space
# - Fast inference on CPU
```

#### 3. Vector Store (ChromaDB)

```python
vectorstore = Chroma(
    collection_name="performia_docs",
    embedding_function=embeddings,
    persist_directory="./chromadb"
)

# Features:
# - Local, no external service
# - Metadata filtering
# - Similarity search
# - Persistent storage
```

#### 4. Query Pipeline

```python
async def query(question: str, k: int = 5) -> List[Dict]:
    """Query knowledge base"""
    results = vectorstore.similarity_search_with_score(
        question,
        k=k
    )

    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": float(score)
        }
        for doc, score in results
    ]
```

### RAG Service Integration

The RAG service integrates with the main application:

```python
class RAGService:
    """Service for RAG operations"""

    async def query(self, question: str, category: Optional[str] = None):
        """Query with optional category filtering"""
        filter_dict = {"category": category} if category else None
        return self.vectorstore.similarity_search(question, filter=filter_dict)

    async def add_document(self, content: str, metadata: Dict):
        """Add document to knowledge base"""
        chunks = self.text_splitter.split_text(content)
        self.vectorstore.add_texts(texts=chunks, metadatas=[metadata] * len(chunks))

    async def get_statistics(self):
        """Get knowledge base stats"""
        results = self.vectorstore.get()
        return {
            "total_chunks": len(results["ids"]),
            "categories": self._count_categories(results["metadatas"])
        }
```

---

## Security Model

### Data Isolation

**Critical:** Each project instance must be isolated.

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    environment:
      COMPOSE_PROJECT_NAME: project-a-commandcenter  # Unique per project
    volumes:
      - project-a-postgres-data:/var/lib/postgresql/data  # Isolated data
```

**Enforcement:**
- Separate Docker networks per project
- Isolated volume mounts
- Per-project database instances
- No shared containers

### Token Encryption

GitHub tokens are encrypted at rest:

```python
# Storage
encrypted_token = encrypt_token(github_token)
repository.access_token = encrypted_token

# Retrieval
github_token = decrypt_token(repository.access_token)
github_service = GitHubService(access_token=github_token)
```

**Encryption Details:**
- Algorithm: Fernet (symmetric encryption)
- Key: Derived from `SECRET_KEY` in `.env`
- Storage: PostgreSQL (encrypted column)
- Transmission: HTTPS only

### Environment Variables

Sensitive configuration in `.env`:

```bash
# Security
SECRET_KEY=your-secret-key-here        # 32+ random characters
ENCRYPT_TOKENS=true                    # Always true in production

# Database
DATABASE_URL=postgresql://...          # Connection string
DB_PASSWORD=strong-password            # Strong password

# API Keys (optional)
ANTHROPIC_API_KEY=sk-...               # For LLM features
OPENAI_API_KEY=sk-...                  # For LLM features

# GitHub
GITHUB_TOKEN=ghp_...                   # Per-repository tokens preferred
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Whitelist only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production:** Restrict `cors_origins` to specific domains.

---

## Service Layer Patterns

### 1. GitHub Integration

**Purpose:** Abstract GitHub API interactions

**Responsibilities:**
- Repository synchronization
- Commit tracking
- Authentication
- Rate limit handling

**Implementation:**
```python
class GitHubService:
    def __init__(self, access_token: Optional[str] = None):
        self.github = Github(access_token)

    async def sync_repository(self, owner: str, name: str):
        """Sync repository metadata and commits"""
        repo = self.github.get_repo(f"{owner}/{name}")
        # Fetch latest commits, stats, etc.
        return sync_info
```

### 2. RAG Service

**Purpose:** Knowledge base operations

**Responsibilities:**
- Document ingestion
- Vector search
- Embedding generation
- Statistics and analytics

**Implementation:**
```python
class RAGService:
    def __init__(self, db_path: str):
        self.embeddings = HuggingFaceEmbeddings(...)
        self.vectorstore = Chroma(...)

    async def query(self, question: str, k: int = 5):
        """Semantic search"""
        return self.vectorstore.similarity_search(question, k=k)
```

---

## API Design

### RESTful Principles

- **Resources:** Nouns (repositories, technologies)
- **HTTP Methods:** GET, POST, PATCH, DELETE
- **Status Codes:** Semantic (200, 201, 404, 409, 500)
- **Versioning:** `/api/v1/`
- **Pagination:** `?skip=0&limit=50`
- **Filtering:** `?domain=audio-dsp&status=integrated`

### Response Patterns

**Single Resource:**
```json
{
  "id": 1,
  "field": "value",
  "created_at": "2025-10-05T12:00:00Z"
}
```

**List with Pagination:**
```json
{
  "total": 100,
  "page": 1,
  "page_size": 50,
  "items": [...]
}
```

**Error:**
```json
{
  "error": "Error type",
  "detail": "Detailed message"
}
```

---

## Deployment Architecture

### Development

```
┌─────────────────┐
│   Developer     │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Docker  │
    │ Compose │
    └────┬────┘
         │
    ┌────▼────┬─────────┬─────────┐
    │Frontend │ Backend │Database │
    │  :3000  │  :8000  │  :5432  │
    └─────────┴─────────┴─────────┘
```

### Production (Traefik)

```
┌──────────────────┐
│   Internet       │
└────────┬─────────┘
         │
    ┌────▼────┐
    │ Traefik │  (Port 80/443)
    │ Reverse │
    │  Proxy  │
    └────┬────┘
         │
    ┌────┴────────────────────┐
    │                         │
┌───▼────┐             ┌──────▼──┐
│Frontend│             │ Backend │
│ :3000  │             │  :8000  │
└────────┘             └─────┬───┘
                             │
                    ┌────────▼────────┐
                    │   PostgreSQL    │
                    │     Redis       │
                    │    ChromaDB     │
                    └─────────────────┘
```

### Zero-Conflict Deployment

Using Traefik for subdomain routing:

```yaml
# docker-compose.traefik.yml
services:
  frontend:
    labels:
      - "traefik.http.routers.project-a-frontend.rule=Host(`project-a.localhost`)"

  backend:
    labels:
      - "traefik.http.routers.project-a-backend.rule=Host(`api.project-a.localhost`)"
```

Access:
- Frontend: `http://project-a.localhost`
- Backend: `http://api.project-a.localhost`

---

## Scalability Considerations

### Current Architecture Limits

- **Database:** PostgreSQL can handle millions of records
- **Vector Store:** ChromaDB suitable for 100K-1M documents
- **Concurrent Users:** 100-1000 (single instance)

### Scaling Strategies

**Horizontal Scaling:**
```
Load Balancer
    │
    ├─── Backend Instance 1
    ├─── Backend Instance 2
    └─── Backend Instance 3
         │
    PostgreSQL (with read replicas)
```

**Caching Layer:**
```
Backend ──► Redis Cache ──► PostgreSQL
```

**Background Jobs:**
```
FastAPI ──► Celery Workers ──► Redis Queue
                │
         ┌──────┴──────┐
    Worker 1      Worker 2
```

### Performance Optimization

**Database:**
- Indexes on frequently queried columns
- Connection pooling
- Query optimization
- Materialized views for analytics

**API:**
- Response caching (Redis)
- Pagination for lists
- Async I/O for external APIs
- CDN for static assets

**RAG:**
- Batch embedding generation
- Vector index optimization
- Metadata filtering
- Result caching

---

## Future Architecture

### Planned Enhancements

**Authentication & Authorization:**
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ JWT Token
┌──────▼──────┐
│  Auth Middleware  │
│  (JWT Verify)     │
└──────┬──────┘
       │
┌──────▼──────┐
│   Backend   │
└─────────────┘
```

**Microservices (Future):**
```
┌──────────────┐
│  API Gateway │
└──────┬───────┘
       │
   ┌───┴────────────────┬─────────────┐
   │                    │             │
┌──▼──────┐   ┌─────────▼──┐   ┌──────▼─────┐
│Repository│   │ Technology │   │    RAG     │
│ Service  │   │  Service   │   │  Service   │
└──────────┘   └────────────┘   └────────────┘
```

**Real-time Updates:**
```
┌─────────┐
│ WebSocket│
│  Server  │
└────┬─────┘
     │
┌────▼─────────────────┐
│  Event Bus (Redis)   │
└──────────────────────┘
```

**Machine Learning:**
```
┌─────────────────┐
│  ML Pipeline    │
│  (Technology    │
│   Clustering)   │
└────┬────────────┘
     │
┌────▼────────────┐
│  Feature Store  │
└─────────────────┘
```

---

## Design Principles

1. **Separation of Concerns:** Each layer has clear responsibilities
2. **Async First:** All I/O operations are non-blocking
3. **Type Safety:** Strong typing in Python (type hints) and TypeScript
4. **API First:** Backend exposes clean REST API for any client
5. **Data Isolation:** Each project instance is completely isolated
6. **Security by Default:** Encryption, validation, secure defaults
7. **Observability:** Logging, health checks, metrics
8. **Extensibility:** Plugin architecture for integrations
9. **Performance:** Caching, pagination, efficient queries
10. **Developer Experience:** Clear documentation, easy setup

---

## Documentation References

- [API Documentation](./API.md) - Complete API reference
- [Configuration Guide](./CONFIGURATION.md) - Environment setup
- [Data Isolation](./DATA_ISOLATION.md) - Multi-project security
- [Docling Setup](./DOCLING_SETUP.md) - RAG document processing
- [Contributing Guide](./CONTRIBUTING.md) - Development guidelines

---

**Architecture Version:** 1.0.0
**Last Updated:** 2025-10-05
