# Command Center API Documentation

**Version:** 2.0.0 (Phase 2)
**Base URL:** `http://localhost:8000`
**API Prefix:** `/api/v1`

## Table of Contents

- [Authentication](#authentication)
- [Common Patterns](#common-patterns)
- [Core APIs](#core-apis)
  - [Repositories API](#repositories-api)
  - [Technologies API](#technologies-api)
  - [Dashboard API](#dashboard-api)
  - [Research Tasks API](#research-tasks-api)
  - [Knowledge Base API](#knowledge-base-api)
- [Phase 2 APIs](#phase-2-apis)
  - [Jobs API](#jobs-api) - Async task management
  - [Export API](#export-api) - Multi-format exports
  - [Webhooks API](#webhooks-api) - Event notifications
  - [Schedules API](#schedules-api) - Recurring tasks
  - [Batch API](#batch-api) - Bulk operations
  - [MCP API](#mcp-api) - Model Context Protocol
- [Error Responses](#error-responses)
- [Rate Limiting](#rate-limiting)
- [WebSocket Endpoints](#websocket-endpoints)

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

## Core APIs

### Repositories API

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

## Phase 2 APIs

### Jobs API

The Jobs API enables async task management with Celery integration, progress tracking, and real-time updates via WebSocket.

**Features:**
- Create and dispatch async jobs
- Real-time progress updates
- Job cancellation
- Statistics and monitoring
- WebSocket support for live progress

**Job Types:**
- `analysis` - Repository analysis
- `export` - Data export
- `import` - Data import
- `webhook_delivery` - Webhook delivery
- `batch_analysis` - Batch repository analysis
- `scheduled_task` - Scheduled task execution

**Job Status:**
- `pending` - Created but not yet dispatched
- `running` - Currently executing
- `completed` - Successfully completed
- `failed` - Failed with error
- `cancelled` - Cancelled by user

#### List Jobs

```http
GET /api/v1/jobs
```

**Query Parameters:**
- `project_id` (optional): Filter by project
- `status_filter` (optional): Filter by status
- `job_type` (optional): Filter by job type
- `skip` (default: 0): Pagination offset
- `limit` (default: 100, max: 1000): Results per page

**Response:** `200 OK`

```json
{
  "jobs": [
    {
      "id": 123,
      "project_id": 1,
      "job_type": "analysis",
      "status": "completed",
      "progress": 100,
      "current_step": "Analysis complete",
      "result": {"technologies_detected": 15},
      "created_by": "user@example.com",
      "celery_task_id": "a1b2c3d4-...",
      "created_at": "2025-10-12T10:00:00Z",
      "started_at": "2025-10-12T10:00:05Z",
      "completed_at": "2025-10-12T10:02:30Z",
      "is_terminal": true
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

**Example:**

```bash
curl "http://localhost:8000/api/v1/jobs?status_filter=running"
```

---

#### Create Job

```http
POST /api/v1/jobs
```

**Request Body:**

```json
{
  "project_id": 1,
  "job_type": "analysis",
  "parameters": {
    "repository_id": 42,
    "analysis_type": "full"
  },
  "created_by": "user@example.com",
  "tags": {
    "priority": "high",
    "department": "engineering"
  }
}
```

**Response:** `201 Created`

---

#### Get Job

```http
GET /api/v1/jobs/{job_id}
```

**Response:** `200 OK`

---

#### Dispatch Job

```http
POST /api/v1/jobs/{job_id}/dispatch
```

Submits a pending job to Celery for async execution.

**Query Parameters:**
- `delay_seconds` (optional, 0-3600): Delay before execution

**Response:** `200 OK` with updated job including `celery_task_id`

---

#### Cancel Job

```http
POST /api/v1/jobs/{job_id}/cancel
```

Cancels a running or pending job and revokes the Celery task.

**Response:** `200 OK`

---

#### Get Job Progress

```http
GET /api/v1/jobs/{job_id}/progress
```

Returns detailed progress information including Celery task status.

**Response:** `200 OK`

```json
{
  "job_id": 123,
  "status": "running",
  "progress": 45,
  "current_step": "Analyzing dependencies",
  "celery_task_id": "a1b2c3d4-...",
  "celery_status": "STARTED",
  "is_terminal": false
}
```

---

#### List Active Jobs

```http
GET /api/v1/jobs/active/list
```

Returns all pending or running jobs.

**Response:** `200 OK`

---

#### Get Job Statistics

```http
GET /api/v1/jobs/statistics/summary
```

Returns aggregated statistics including total jobs, jobs by status, success rate, and average duration.

**Query Parameters:**
- `project_id` (optional): Filter by project

**Response:** `200 OK`

```json
{
  "total_jobs": 250,
  "jobs_by_status": {
    "pending": 5,
    "running": 3,
    "completed": 230,
    "failed": 10,
    "cancelled": 2
  },
  "success_rate": 95.8,
  "average_duration_seconds": 145.6
}
```

---

### Export API

The Export API provides multi-format analysis exports including SARIF, HTML, CSV, Excel, and JSON.

**Supported Formats:**
- **SARIF** - Static Analysis Results Interchange Format (GitHub Code Scanning compatible)
- **HTML** - Self-contained interactive reports with charts
- **CSV** - Spreadsheet-friendly data (multiple types)
- **Excel** - Multi-sheet workbooks with formatting
- **JSON** - Raw analysis data

**Rate Limiting:** 10 requests/minute for individual exports, 5 requests/minute for batch operations.

#### Export to SARIF

```http
GET /api/v1/export/{analysis_id}/sarif
```

Exports analysis to SARIF 2.1.0 format for GitHub Code Scanning, GitLab SAST, Azure DevOps, and IDE integration.

**Response:** `200 OK` (application/json)

---

#### Export to HTML

```http
GET /api/v1/export/{analysis_id}/html
```

Generates self-contained HTML report with:
- Interactive charts (Chart.js)
- Dark/light mode toggle
- Responsive design
- Print-friendly styles

**Response:** `200 OK` (text/html)

---

#### Export to CSV

```http
GET /api/v1/export/{analysis_id}/csv
```

**Query Parameters:**
- `export_type` (required): Type of CSV data
  - `combined` - All data in one file
  - `technologies` - Detected technologies
  - `dependencies` - Dependencies analysis
  - `metrics` - Code metrics
  - `gaps` - Research gaps

**Response:** `200 OK` (text/csv)

---

#### Export to Excel

```http
GET /api/v1/export/{analysis_id}/excel
```

Generates multi-sheet Excel workbook with formatting.

**Requires:** openpyxl library installed

**Response:** `200 OK` (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

---

#### Export to JSON

```http
GET /api/v1/export/{analysis_id}/json
```

**Query Parameters:**
- `pretty` (default: true): Pretty-print JSON

**Response:** `200 OK` (application/json)

---

#### Get Available Formats

```http
GET /api/v1/export/formats
```

Returns list of available export formats with descriptions, use cases, and rate limits.

**Response:** `200 OK`

---

#### Batch Export

```http
POST /api/v1/export/batch
```

Export multiple analyses in batch. Returns a job ID for tracking.

**Request Body:**

```json
{
  "analysis_ids": [1, 2, 3],
  "format": "sarif"
}
```

**Response:** `202 Accepted` with job information

---

### Webhooks API

The Webhooks API enables event notifications to external systems with automatic retry logic, signature verification, and delivery tracking.

**Features:**
- HMAC-SHA256 signature verification
- Exponential backoff retry logic
- Event filtering with wildcards
- Delivery statistics and monitoring
- Manual retry capability

**For complete documentation, see:** [WEBHOOKS.md](./WEBHOOKS.md)

#### Quick Example

```bash
# Create webhook configuration
curl -X POST http://localhost:8000/api/v1/webhooks/configs \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": 1,
    "webhook_url": "https://example.com/webhook",
    "secret": "your-secret-key",
    "events": ["analysis.complete", "export.*"]
  }'
```

**Common Endpoints:**
- `POST /api/v1/webhooks/configs` - Create webhook
- `GET /api/v1/webhooks/configs` - List webhooks
- `POST /api/v1/webhooks/deliveries` - Create delivery
- `GET /api/v1/webhooks/deliveries` - List deliveries
- `POST /api/v1/webhooks/deliveries/{id}/retry` - Retry failed delivery
- `GET /api/v1/webhooks/statistics` - Get statistics

---

### Schedules API

The Schedules API enables automated recurring task execution with timezone support, cron expressions, and health monitoring.

**Features:**
- 6 frequency types (once, hourly, daily, weekly, monthly, cron)
- IANA timezone support
- Execution windows (start_time/end_time)
- Health monitoring
- Manual execution
- Celery Beat integration

**For complete documentation, see:** [SCHEDULING.md](./SCHEDULING.md)

#### Quick Example

```bash
# Create daily schedule
curl -X POST http://localhost:8000/api/v1/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "name": "Daily Analysis",
    "task_type": "analysis",
    "frequency": "daily",
    "timezone": "America/New_York",
    "task_parameters": {
      "repository_id": 42
    }
  }'
```

**Common Endpoints:**
- `POST /api/v1/schedules` - Create schedule
- `GET /api/v1/schedules` - List schedules
- `POST /api/v1/schedules/{id}/execute` - Execute manually
- `POST /api/v1/schedules/{id}/enable` - Enable schedule
- `POST /api/v1/schedules/{id}/disable` - Disable schedule
- `GET /api/v1/schedules/statistics/summary` - Get statistics
- `GET /api/v1/schedules/due/list` - List due schedules

---

### Batch API

The Batch API enables bulk operations for analysis, export, and import across multiple repositories or projects.

**Operations:**
- Batch repository analysis
- Batch data export
- Batch data import

**Endpoints:**
- `POST /api/v1/batch/analyze` - Batch analyze repositories
- `POST /api/v1/batch/export` - Batch export data
- `POST /api/v1/batch/import` - Batch import data

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/batch/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "repository_ids": [1, 2, 3, 4, 5]
  }'
```

**Response:** `202 Accepted` with job ID for tracking

---

### MCP API

The Model Context Protocol (MCP) API provides structured AI assistant access to CommandCenter resources, tools, and prompts.

**Features:**
- 14 resource types (projects, technologies, repos, jobs, schedules)
- 10 actionable tools (CRUD operations)
- 7 prompt templates for AI guidance
- Context management for stateful sessions
- Authentication and rate limiting

**Endpoints:**
- `GET /mcp/resources` - List available resources
- `GET /mcp/resources/{uri}` - Get specific resource
- `POST /mcp/tools/{name}` - Invoke tool
- `GET /mcp/prompts` - List available prompts
- `GET /mcp/prompts/{name}` - Get prompt template

**Example:**

```bash
# List available resources
curl http://localhost:8000/mcp/resources

# Invoke tool
curl -X POST http://localhost:8000/mcp/tools/list_projects \
  -H "Content-Type: application/json" \
  -d '{}'
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

## WebSocket Endpoints

Command Center provides WebSocket support for real-time job progress updates.

### Job Progress WebSocket

```
ws://localhost:8000/api/v1/jobs/ws/{job_id}
```

Connects to a specific job for real-time progress updates.

**Message Types:**

1. **connected** - Initial connection confirmation
```json
{
  "type": "connected",
  "job_id": 123,
  "status": "running",
  "progress": 0,
  "current_step": "Starting analysis"
}
```

2. **progress** - Periodic progress updates
```json
{
  "type": "progress",
  "job_id": 123,
  "status": "running",
  "progress": 45,
  "current_step": "Analyzing dependencies",
  "is_terminal": false
}
```

3. **completed** - Job completion
```json
{
  "type": "completed",
  "job_id": 123,
  "status": "completed",
  "result": {"technologies_detected": 15},
  "error": null
}
```

**Example Client (JavaScript):**

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/jobs/ws/123');

ws.onopen = () => {
  console.log('Connected to job 123');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Job ${data.job_id}: ${data.progress}% - ${data.current_step}`);

  if (data.type === 'completed') {
    console.log('Job completed!', data.result);
    ws.close();
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

**Connection Lifecycle:**
1. Client connects to `/api/v1/jobs/ws/{job_id}`
2. Server verifies job exists
3. Server sends initial `connected` message
4. Server sends `progress` updates every 1 second
5. Server sends `completed` message when job finishes
6. Connection automatically closes

**Error Codes:**
- `1008` - Job not found
- `1011` - Internal server error

---

## Changelog

### Version 2.0.0 (Phase 2) - 2025-10-12
- **Jobs API**: Async task management with Celery integration
- **Export API**: Multi-format exports (SARIF, HTML, CSV, Excel, JSON)
- **Webhooks API**: Event notifications with retry logic
- **Schedules API**: Recurring task execution with Celery Beat
- **Batch API**: Bulk operations for analysis/export/import
- **MCP API**: Model Context Protocol integration
- **WebSocket Support**: Real-time job progress updates
- **Rate Limiting**: Per-endpoint rate limits
- **Enhanced Documentation**: Comprehensive Phase 2 API docs

### Version 1.0.0 - 2025-10-05
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
- **Webhooks Guide:** [WEBHOOKS.md](./WEBHOOKS.md)
- **Scheduling Guide:** [SCHEDULING.md](./SCHEDULING.md)
- **Observability:** [OBSERVABILITY.md](./OBSERVABILITY.md)
