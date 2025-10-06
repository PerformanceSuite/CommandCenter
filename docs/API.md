# Command Center API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`
**API Prefix:** `/api/v1`

## Table of Contents

- [Authentication](#authentication)
- [Common Patterns](#common-patterns)
- [Repositories API](#repositories-api)
- [Technologies API](#technologies-api)
- [Dashboard API](#dashboard-api)
- [Research Tasks API](#research-tasks-api)
- [Knowledge Base API](#knowledge-base-api)
- [Error Responses](#error-responses)
- [Rate Limiting](#rate-limiting)

---

## Authentication

Currently, Command Center API does not require authentication for local development. For production deployments, implement authentication using:

- **JWT Tokens** - Settings configured in `.env` with `SECRET_KEY`
- **GitHub OAuth** - For repository access (coming soon)

### Environment Variables

```bash
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
```

---

## Common Patterns

### Request Headers

```http
Content-Type: application/json
Accept: application/json
```

### Pagination

List endpoints support pagination with query parameters:

```
?skip=0&limit=50
```

- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default varies by endpoint)

### Filtering

Many endpoints support filtering:

```
?domain=audio-dsp&status=integrated
```

### Response Format

Success responses return JSON:

```json
{
  "id": 1,
  "field": "value",
  "created_at": "2025-10-05T12:00:00Z",
  "updated_at": "2025-10-05T12:00:00Z"
}
```

List responses include metadata:

```json
{
  "total": 100,
  "page": 1,
  "page_size": 50,
  "items": [...]
}
```

---

## Repositories API

Manage GitHub repository tracking and synchronization.

### List Repositories

```http
GET /api/v1/repositories
```

**Query Parameters:**
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Maximum results (default: 100)

**Response:** `200 OK`

```json
[
  {
    "id": 1,
    "owner": "performancesuite",
    "name": "performia",
    "full_name": "performancesuite/performia",
    "description": "Music performance system",
    "github_id": 123456789,
    "url": "https://github.com/performancesuite/performia",
    "clone_url": "https://github.com/performancesuite/performia.git",
    "default_branch": "main",
    "is_private": false,
    "last_commit_sha": "abc123...",
    "last_commit_message": "feat: Add new feature",
    "last_commit_author": "developer",
    "last_commit_date": "2025-10-05T10:30:00Z",
    "last_synced_at": "2025-10-05T11:00:00Z",
    "stars": 42,
    "forks": 8,
    "language": "Python",
    "metadata_": {},
    "created_at": "2025-10-01T08:00:00Z",
    "updated_at": "2025-10-05T11:00:00Z"
  }
]
```

**Example:**

```bash
curl http://localhost:8000/api/v1/repositories?limit=10
```

---

### Get Repository

```http
GET /api/v1/repositories/{repository_id}
```

**Path Parameters:**
- `repository_id` (integer, required): Repository ID

**Response:** `200 OK` (same schema as list item)

**Errors:**
- `404 Not Found`: Repository not found

**Example:**

```bash
curl http://localhost:8000/api/v1/repositories/1
```

---

### Create Repository

```http
POST /api/v1/repositories
```

**Request Body:**

```json
{
  "owner": "performancesuite",
  "name": "performia",
  "description": "Music performance system",
  "access_token": "ghp_xxxxxxxxxxxx",
  "is_private": false
}
```

**Field Validation:**
- `owner` (string, required): GitHub username or organization (1-255 chars, alphanumeric with hyphens)
- `name` (string, required): Repository name (1-255 chars, alphanumeric with hyphens)
- `description` (string, optional): Repository description
- `access_token` (string, optional): GitHub personal access token (PAT) in format `ghp_*`, `gho_*`, `ghu_*`, `ghs_*`, or `ghr_*`
- `is_private` (boolean, optional): Whether repository is private (default: false)

**Response:** `201 Created`

```json
{
  "id": 1,
  "owner": "performancesuite",
  "name": "performia",
  "full_name": "performancesuite/performia",
  ...
}
```

**Errors:**
- `400 Bad Request`: Invalid input data
- `409 Conflict`: Repository already exists

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "performancesuite",
    "name": "performia",
    "description": "Music performance system",
    "access_token": "ghp_xxxxxxxxxxxx"
  }'
```

---

### Update Repository

```http
PATCH /api/v1/repositories/{repository_id}
```

**Path Parameters:**
- `repository_id` (integer, required): Repository ID

**Request Body:**

```json
{
  "description": "Updated description",
  "access_token": "ghp_yyyyyyyyyyyy",
  "is_private": true,
  "metadata_": {"custom_field": "value"}
}
```

All fields are optional. Only provided fields will be updated.

**Response:** `200 OK`

**Errors:**
- `404 Not Found`: Repository not found

**Example:**

```bash
curl -X PATCH http://localhost:8000/api/v1/repositories/1 \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated description"}'
```

---

### Delete Repository

```http
DELETE /api/v1/repositories/{repository_id}
```

**Path Parameters:**
- `repository_id` (integer, required): Repository ID

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Repository not found

**Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/repositories/1
```

---

### Sync Repository

Synchronize repository data with GitHub API.

```http
POST /api/v1/repositories/{repository_id}/sync
```

**Path Parameters:**
- `repository_id` (integer, required): Repository ID

**Request Body:**

```json
{
  "force": false
}
```

- `force` (boolean, optional): Force sync even if recently synced (default: false)

**Response:** `200 OK`

```json
{
  "repository_id": 1,
  "synced": true,
  "last_commit_sha": "abc123...",
  "last_commit_message": "feat: Add new feature",
  "last_synced_at": "2025-10-05T12:00:00Z",
  "changes_detected": true
}
```

**Errors:**
- `404 Not Found`: Repository not found
- `500 Internal Server Error`: GitHub API error or network issue

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/repositories/1/sync \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
```

---

## Technologies API

Manage technology tracking, research status, and technology radar.

### List Technologies

```http
GET /api/v1/technologies
```

**Query Parameters:**
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Maximum results (default: 50)
- `domain` (string, optional): Filter by domain (see Technology Domains)
- `status` (string, optional): Filter by status (see Technology Status)
- `search` (string, optional): Search in title, description, or tags

**Response:** `200 OK`

```json
{
  "total": 100,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": 1,
      "title": "JUCE Framework",
      "vendor": "JUCE",
      "domain": "audio-dsp",
      "status": "integrated",
      "relevance_score": 95,
      "priority": 5,
      "description": "C++ framework for audio applications",
      "notes": "Core framework for audio processing",
      "use_cases": "Audio plugins, DAW development",
      "documentation_url": "https://juce.com/docs",
      "repository_url": "https://github.com/juce-framework/JUCE",
      "website_url": "https://juce.com",
      "tags": "audio,c++,framework,dsp",
      "created_at": "2025-10-01T08:00:00Z",
      "updated_at": "2025-10-05T10:00:00Z"
    }
  ]
}
```

**Technology Domains:**
- `audio-dsp`: Audio DSP and signal processing
- `ai-ml`: AI and Machine Learning
- `music-theory`: Music theory and composition
- `performance`: Performance optimization
- `ui-ux`: User interface and experience
- `infrastructure`: Infrastructure and DevOps
- `other`: Other categories

**Technology Status:**
- `discovery`: Initial research phase
- `research`: Active research
- `evaluation`: Testing and evaluation
- `implementation`: Being implemented
- `integrated`: Fully integrated
- `archived`: No longer relevant

**Example:**

```bash
# Get all audio-dsp technologies
curl "http://localhost:8000/api/v1/technologies?domain=audio-dsp"

# Search for "JUCE"
curl "http://localhost:8000/api/v1/technologies?search=JUCE"

# Get integrated technologies
curl "http://localhost:8000/api/v1/technologies?status=integrated"
```

---

### Get Technology

```http
GET /api/v1/technologies/{technology_id}
```

**Path Parameters:**
- `technology_id` (integer, required): Technology ID

**Response:** `200 OK` (same schema as list item)

**Errors:**
- `404 Not Found`: Technology not found

**Example:**

```bash
curl http://localhost:8000/api/v1/technologies/1
```

---

### Create Technology

```http
POST /api/v1/technologies
```

**Request Body:**

```json
{
  "title": "JUCE Framework",
  "vendor": "JUCE",
  "domain": "audio-dsp",
  "status": "integrated",
  "relevance_score": 95,
  "priority": 5,
  "description": "C++ framework for audio applications",
  "notes": "Core framework for audio processing",
  "use_cases": "Audio plugins, DAW development",
  "documentation_url": "https://juce.com/docs",
  "repository_url": "https://github.com/juce-framework/JUCE",
  "website_url": "https://juce.com",
  "tags": "audio,c++,framework,dsp"
}
```

**Required Fields:**
- `title` (string): Technology title (1-255 chars, unique)
- `domain` (string): Technology domain (see domains list)
- `status` (string): Current status (see status list)

**Optional Fields:**
- `vendor` (string): Vendor/creator name
- `relevance_score` (integer): Relevance score 0-100 (default: 50)
- `priority` (integer): Priority 1-5, where 5=highest (default: 3)
- `description` (text): Technology description
- `notes` (text): Internal notes
- `use_cases` (text): Use cases and applications
- `documentation_url` (string): Documentation URL
- `repository_url` (string): Source repository URL
- `website_url` (string): Official website URL
- `tags` (string): Comma-separated tags

**Response:** `201 Created`

**Errors:**
- `400 Bad Request`: Invalid input data
- `409 Conflict`: Technology with same title already exists

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/technologies \
  -H "Content-Type: application/json" \
  -d '{
    "title": "TensorFlow",
    "vendor": "Google",
    "domain": "ai-ml",
    "status": "research",
    "relevance_score": 85,
    "priority": 4
  }'
```

---

### Update Technology

```http
PATCH /api/v1/technologies/{technology_id}
```

**Path Parameters:**
- `technology_id` (integer, required): Technology ID

**Request Body:** All fields optional

```json
{
  "status": "integrated",
  "relevance_score": 98,
  "notes": "Updated implementation notes"
}
```

**Response:** `200 OK`

**Errors:**
- `404 Not Found`: Technology not found

**Example:**

```bash
curl -X PATCH http://localhost:8000/api/v1/technologies/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "integrated", "relevance_score": 98}'
```

---

### Delete Technology

```http
DELETE /api/v1/technologies/{technology_id}
```

**Path Parameters:**
- `technology_id` (integer, required): Technology ID

**Response:** `204 No Content`

**Errors:**
- `404 Not Found`: Technology not found

**Note:** Deleting a technology will cascade delete associated research tasks and knowledge entries.

**Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/technologies/1
```

---

## Dashboard API

Analytics and statistics endpoints for dashboard visualization.

### Get Dashboard Statistics

```http
GET /api/v1/dashboard/stats
```

**Response:** `200 OK`

```json
{
  "repositories": {
    "total": 25
  },
  "technologies": {
    "total": 50,
    "by_status": {
      "discovery": 5,
      "research": 10,
      "evaluation": 8,
      "implementation": 12,
      "integrated": 13,
      "archived": 2
    }
  },
  "research_tasks": {
    "total": 100,
    "by_status": {
      "pending": 20,
      "in_progress": 15,
      "blocked": 3,
      "completed": 60,
      "cancelled": 2
    }
  },
  "knowledge_base": {
    "total_chunks": 5000,
    "categories": {
      "audio": 1500,
      "ai": 2000,
      "infrastructure": 1500
    },
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "db_path": "./docs/knowledge-base/chromadb"
  }
}
```

**Example:**

```bash
curl http://localhost:8000/api/v1/dashboard/stats
```

---

### Get Recent Activity

```http
GET /api/v1/dashboard/recent-activity
```

**Query Parameters:**
- `limit` (integer, optional): Number of items per category (default: 10)

**Response:** `200 OK`

```json
{
  "recent_repositories": [
    {
      "id": 1,
      "full_name": "performancesuite/performia",
      "updated_at": "2025-10-05T10:00:00Z"
    }
  ],
  "recent_technologies": [
    {
      "id": 1,
      "title": "JUCE Framework",
      "status": "integrated",
      "updated_at": "2025-10-05T10:00:00Z"
    }
  ],
  "recent_tasks": [
    {
      "id": 1,
      "title": "Research spatial audio APIs",
      "status": "in_progress",
      "updated_at": "2025-10-05T10:00:00Z"
    }
  ]
}
```

**Example:**

```bash
curl "http://localhost:8000/api/v1/dashboard/recent-activity?limit=5"
```

---

## Research Tasks API

**Note:** Research task endpoints are defined in the models but may not yet have full router implementation. Check `/docs` endpoint for current API availability.

Expected endpoints:
- `GET /api/v1/research-tasks` - List research tasks
- `GET /api/v1/research-tasks/{task_id}` - Get task details
- `POST /api/v1/research-tasks` - Create task
- `PATCH /api/v1/research-tasks/{task_id}` - Update task
- `DELETE /api/v1/research-tasks/{task_id}` - Delete task

---

## Knowledge Base API

**Note:** Knowledge base endpoints leverage the RAG service. Ensure RAG dependencies are installed.

Expected endpoints:
- `POST /api/v1/knowledge/query` - Query knowledge base
- `POST /api/v1/knowledge/add` - Add document to knowledge base
- `GET /api/v1/knowledge/categories` - List categories
- `DELETE /api/v1/knowledge/source/{source}` - Delete by source

### Query Knowledge Base (Expected)

```http
POST /api/v1/knowledge/query
```

**Request Body:**

```json
{
  "query": "What are the latest AI music generation models?",
  "category": "ai",
  "k": 5
}
```

**Response:** `200 OK`

```json
{
  "results": [
    {
      "content": "Document chunk content...",
      "metadata": {
        "source": "ai-research-2025.md",
        "category": "ai"
      },
      "score": 0.85,
      "category": "ai",
      "source": "ai-research-2025.md"
    }
  ]
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PATCH request |
| 201 | Created | Successful POST request |
| 204 | No Content | Successful DELETE request |
| 400 | Bad Request | Invalid input data, validation error |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 500 | Internal Server Error | Server error, external API failure |

### Common Error Examples

**404 Not Found:**
```json
{
  "error": "Not Found",
  "detail": "Repository 999 not found"
}
```

**409 Conflict:**
```json
{
  "error": "Conflict",
  "detail": "Repository performancesuite/performia already exists"
}
```

**400 Bad Request:**
```json
{
  "error": "Validation Error",
  "detail": [
    {
      "loc": ["body", "owner"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

Currently, no rate limiting is enforced in development. For production:

- Implement rate limiting middleware
- Recommended: 100 requests/minute per IP
- GitHub API sync respects GitHub rate limits (5000/hour authenticated)

---

## Interactive API Documentation

Command Center provides interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

Use these interfaces to explore endpoints, test requests, and view detailed schemas.

---

## Health Check

### Health Endpoint

```http
GET /health
```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "app": "Command Center API",
  "version": "1.0.0"
}
```

### Root Endpoint

```http
GET /
```

**Response:** `200 OK`

```json
{
  "app": "Command Center API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

## SDK and Client Libraries

Currently, no official SDK is provided. Use standard HTTP clients:

**Python:**
```python
import requests

response = requests.get("http://localhost:8000/api/v1/repositories")
repositories = response.json()
```

**JavaScript/TypeScript:**
```javascript
const response = await fetch("http://localhost:8000/api/v1/repositories");
const repositories = await response.json();
```

**cURL:**
```bash
curl -X GET http://localhost:8000/api/v1/repositories
```

---

## Changelog

### Version 1.0.0
- Initial API release
- Repositories CRUD and sync endpoints
- Technologies CRUD with filtering
- Dashboard statistics and recent activity
- Health check endpoints
- RAG service integration (optional)

---

## Support

- **Issues:** https://github.com/PerformanceSuite/CommandCenter/issues
- **Documentation:** https://github.com/PerformanceSuite/CommandCenter/tree/main/docs
- **API Docs:** http://localhost:8000/docs
