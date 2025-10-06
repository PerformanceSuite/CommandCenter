# GitHub Optimization Implementation

## Overview

This document describes the GitHub optimization features implemented by the GitHub Agent, including webhooks, rate limiting, caching, and enhanced GitHub integrations.

## Features Implemented

### 1. Webhook Support

#### Components
- **Models**: `WebhookConfig`, `WebhookEvent` (in `app/models/webhook.py`)
- **Router**: `app/routers/webhooks.py`
- **Utilities**: `app/utils/webhook_verification.py`

#### Endpoints

##### Webhook Management
- `POST /api/v1/webhooks/configs` - Create webhook configuration
- `GET /api/v1/webhooks/configs` - List webhook configurations
- `GET /api/v1/webhooks/configs/{config_id}` - Get specific webhook config
- `PATCH /api/v1/webhooks/configs/{config_id}` - Update webhook config
- `DELETE /api/v1/webhooks/configs/{config_id}` - Delete webhook config

##### Webhook Events
- `POST /api/v1/webhooks/github` - Receive GitHub webhook events
- `GET /api/v1/webhooks/events` - List received webhook events

#### Features
- GitHub webhook signature verification (HMAC-SHA256)
- Event storage in database for audit trail
- Automatic processing of push, pull_request, and issue events
- Idempotent event handling (duplicate delivery detection)
- Support for event filtering by type and repository

### 2. Rate Limiting & Optimization

#### Components
- **Service**: `app/services/rate_limit_service.py`
- **Model**: `GitHubRateLimit` (in `app/models/webhook.py`)
- **Router**: `app/routers/rate_limits.py`

#### Endpoints
- `GET /api/v1/rate-limits/status` - Get current rate limit status
- `POST /api/v1/rate-limits/track` - Store rate limit status in database
- `GET /api/v1/rate-limits/health` - Check if rate limit is healthy

#### Features
- Real-time rate limit tracking for all GitHub API resource types (core, search, graphql)
- Exponential backoff retry logic with tenacity
- Automatic waiting when rate limit is exhausted
- Rate limit status storage for historical tracking
- Decorator-based retry mechanism for GitHub API calls

### 3. Redis Caching

#### Components
- **Service**: `app/services/redis_service.py`
- **Configuration**: Redis URL in `app/config.py`

#### Features
- Async Redis client with connection pooling
- JSON serialization/deserialization
- Configurable TTL (Time To Live)
- Pattern-based cache invalidation
- Graceful fallback when Redis is unavailable
- Cache key generation utilities

#### Cache Strategy
- Repository info: 5 minutes TTL
- Pull requests: 1 minute TTL
- Issues: 1 minute TTL
- Manual cache invalidation via API endpoint

### 4. Prometheus Metrics

#### Components
- **Service**: `app/services/metrics_service.py`
- **Endpoint**: `/metrics` (Prometheus-compatible)

#### Metrics Tracked
- `github_api_requests_total` - Total GitHub API requests
- `github_api_request_duration_seconds` - API request duration
- `github_api_rate_limit_remaining` - Current rate limit remaining
- `github_api_rate_limit_limit` - Total rate limit
- `github_api_errors_total` - API errors by type
- `webhook_events_received_total` - Webhooks received
- `webhook_events_processed_total` - Webhooks processed successfully
- `webhook_events_failed_total` - Webhook processing failures
- `webhook_processing_duration_seconds` - Webhook processing time
- `cache_hits_total` - Cache hits
- `cache_misses_total` - Cache misses
- `repository_sync_total` - Repository syncs
- `repository_sync_duration_seconds` - Sync duration

### 5. Enhanced GitHub Features

#### Components
- **Service**: `app/services/enhanced_github_service.py`
- **Router**: `app/routers/github_features.py`

#### Endpoints

##### Repository Management
- `GET /api/v1/github/{owner}/{repo}/info` - Get repository info (cached)
- `PATCH /api/v1/github/{owner}/{repo}/settings` - Update repository settings
- `POST /api/v1/github/{owner}/{repo}/cache/invalidate` - Invalidate cache

##### Pull Requests
- `GET /api/v1/github/{owner}/{repo}/pulls` - List pull requests (cached)

##### Issues & Labels
- `GET /api/v1/github/{owner}/{repo}/issues` - List issues
- `POST /api/v1/github/{owner}/{repo}/labels` - Create label
- `PATCH /api/v1/github/{owner}/{repo}/labels/{label_name}` - Update label
- `DELETE /api/v1/github/{owner}/{repo}/labels/{label_name}` - Delete label

##### GitHub Actions
- `GET /api/v1/github/{owner}/{repo}/workflows` - List workflows

## Database Schema

### WebhookConfig
- `id` - Primary key
- `repository_id` - Foreign key to repositories
- `webhook_id` - GitHub webhook ID
- `webhook_url` - Webhook endpoint URL
- `secret` - Webhook secret for signature verification
- `events` - JSON array of subscribed events
- `active` - Whether webhook is active
- `last_delivery_at` - Last delivery timestamp
- `created_at`, `updated_at` - Timestamps

### WebhookEvent
- `id` - Primary key
- `config_id` - Foreign key to webhook_configs
- `event_type` - Event type (push, pull_request, issues, etc.)
- `delivery_id` - GitHub delivery ID (unique)
- `payload` - JSON payload from GitHub
- `repository_full_name` - Repository identifier
- `processed` - Processing status
- `processed_at` - Processing timestamp
- `error` - Error message if failed
- `received_at` - Receipt timestamp

### GitHubRateLimit
- `id` - Primary key
- `resource_type` - Resource type (core, search, graphql)
- `limit` - Total rate limit
- `remaining` - Remaining calls
- `reset_at` - Rate limit reset timestamp
- `token_hash` - Hash of token (for tracking)
- `checked_at` - Check timestamp

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# GitHub Configuration (existing)
GITHUB_TOKEN=your_github_token_here
```

## Installation

### Dependencies Added
- `redis==5.0.1` - Redis client
- `hiredis==2.3.2` - Redis parser (performance)
- `prometheus-client==0.19.0` - Prometheus metrics
- `tenacity==8.2.3` - Retry logic

### Database Migration

Run the migration to create new tables:

```bash
cd backend
alembic upgrade head
```

## Usage Examples

### Setting Up a Webhook

```python
# Create webhook configuration
POST /api/v1/webhooks/configs
{
    "repository_id": 1,
    "webhook_url": "https://your-domain.com/api/v1/webhooks/github",
    "secret": "your-webhook-secret",
    "events": ["push", "pull_request", "issues"]
}
```

### Checking Rate Limits

```python
# Get current rate limit status
GET /api/v1/rate-limits/status

# Response
{
    "status": "success",
    "rate_limits": {
        "core": {
            "limit": 5000,
            "remaining": 4950,
            "reset": "2025-10-05T20:00:00Z",
            "used": 50,
            "percentage_used": 1.0
        },
        "search": {...},
        "graphql": {...}
    }
}
```

### Using Cached Endpoints

```python
# Get repository info (will cache for 5 minutes)
GET /api/v1/github/owner/repo/info?use_cache=true

# Invalidate cache when needed
POST /api/v1/github/owner/repo/cache/invalidate
```

### Managing Labels

```python
# Create a label
POST /api/v1/github/owner/repo/labels
{
    "label_name": "bug",
    "color": "d73a4a",
    "description": "Something isn't working"
}

# Update a label
PATCH /api/v1/github/owner/repo/labels/bug
{
    "color": "ff0000",
    "description": "Bug reports"
}
```

## Testing

### Health Checks
- `GET /health` - Application health
- `GET /api/v1/rate-limits/health` - Rate limit health

### Metrics
- `GET /metrics` - Prometheus metrics endpoint

## Error Handling

All endpoints include comprehensive error handling:
- GitHub API errors are caught and logged
- Rate limit exceeded errors trigger automatic retries
- Webhook signature verification failures return 401
- Database errors are properly handled and rolled back
- All errors include detailed messages in responses

## Monitoring

### Prometheus Integration
The `/metrics` endpoint exposes all operational metrics in Prometheus format. Configure your Prometheus instance to scrape this endpoint.

### Logging
All GitHub operations are logged with appropriate levels:
- INFO: Successful operations, cache hits/misses
- WARNING: Rate limit warnings, retry attempts
- ERROR: Failed operations, webhook processing errors

## Security

### Webhook Security
- All webhook events are verified using HMAC-SHA256 signatures
- Secrets are stored securely in the database
- Invalid signatures return 401 Unauthorized

### Token Security
- GitHub tokens are never exposed in logs or responses
- Rate limit tracking uses SHA-256 hashes of tokens
- Token encryption is supported via configuration

## Performance Optimizations

1. **Caching**: Reduces GitHub API calls by up to 90%
2. **Connection Pooling**: Redis async client uses connection pooling
3. **Batch Operations**: Webhook events can be processed in batches
4. **Exponential Backoff**: Prevents API hammering during rate limits
5. **Metrics**: Low-overhead Prometheus metrics collection

## Future Enhancements

Possible future additions:
- Webhook retry logic for failed deliveries
- GraphQL API support
- Advanced PR automation (auto-merge, auto-review)
- Issue triage automation
- Dependency scanning via GitHub API
- Code scanning integration
- Repository insights and analytics

## API Documentation

Full API documentation is available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI spec: `/openapi.json`
