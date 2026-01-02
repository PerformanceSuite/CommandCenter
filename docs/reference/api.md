# API Reference

**Base URL**: `http://localhost:8000/api/v1`

**Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)

## Authentication

Most endpoints require authentication via JWT token:

```
Authorization: Bearer <token>
```

Get a token via `/api/v1/auth/login`.

## Core Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness check |
| GET | `/health/ready` | Readiness check with dependencies |

### Hypotheses (AI Arena)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/hypotheses` | List hypotheses |
| POST | `/hypotheses` | Create hypothesis |
| GET | `/hypotheses/{id}` | Get hypothesis details |
| POST | `/hypotheses/{id}/validate` | Start validation |
| GET | `/hypotheses/{id}/debate` | Get debate results |
| GET | `/hypotheses/stats` | Dashboard statistics |
| GET | `/hypotheses/costs` | LLM cost tracking |

### Knowledge

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/knowledge/search` | Semantic search |
| POST | `/knowledge/ingest` | Ingest document |
| POST | `/knowledge/ask` | RAG query |

### Research Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/research-tasks` | List tasks |
| POST | `/research-tasks` | Create task |
| GET | `/research-tasks/{id}` | Get task details |
| PUT | `/research-tasks/{id}` | Update task |

### Technologies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/technologies` | List technologies |
| POST | `/technologies` | Add technology |
| PUT | `/technologies/{id}` | Update technology |
| PUT | `/technologies/{id}/stage` | Update radar stage |

### Repositories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/repositories` | List repositories |
| POST | `/repositories/sync` | Sync from GitHub |
| GET | `/repositories/{id}` | Get repository details |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/settings/providers` | List AI providers |
| POST | `/settings/providers` | Add provider |
| PUT | `/settings/providers/{id}` | Update provider |
| GET | `/settings/models` | List available models |

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs` | List background jobs |
| GET | `/jobs/{id}` | Get job status |
| DELETE | `/jobs/{id}` | Cancel job |

## Response Format

All responses follow this structure:

```json
{
  "data": { ... },
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

Error responses:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": { ... }
  }
}
```

## Pagination

List endpoints support pagination:

```
GET /hypotheses?page=1&per_page=20
```

## Filtering

Most list endpoints support filtering:

```
GET /hypotheses?status=validated&confidence_min=0.8
GET /technologies?stage=evaluate
GET /research-tasks?status=active
```

## WebSocket Events

Real-time updates via Server-Sent Events:

```
GET /events/stream
```

Event types:
- `hypothesis.created`
- `hypothesis.validated`
- `job.started`
- `job.completed`
- `job.failed`
