# Webhook System Documentation

## Overview

CommandCenter provides a comprehensive webhook system for notifying external systems of important events. The webhook system includes:

- **Webhook delivery tracking** - Track every delivery attempt with full history
- **Automatic retry logic** - Exponential backoff for failed deliveries
- **Signature verification** - HMAC-SHA256 signatures for security
- **Event filtering** - Subscribe only to relevant events with wildcard support
- **Payload validation** - Ensure webhook payloads meet requirements
- **Delivery statistics** - Monitor success rates and performance

## Architecture

### Components

1. **WebhookConfig** - Configuration for webhook endpoints
   - Target URL, secret, retry settings
   - Event subscriptions and filtering
   - Delivery statistics (total, successful, failed)

2. **WebhookDelivery** - Individual delivery attempts
   - Tracks status, attempts, timing
   - Stores responses and errors
   - Supports retry scheduling

3. **WebhookService** - Business logic layer
   - Creates and manages deliveries
   - Handles retry logic with exponential backoff
   - Validates payloads and filters events

4. **Webhook Tasks** - Celery background tasks
   - `deliver_webhook` - Attempt delivery
   - `create_and_deliver_webhook` - Create and send
   - `process_pending_deliveries` - Process retries

## API Endpoints

### Webhook Configuration

#### Create Webhook Config
```http
POST /api/v1/webhooks/configs
Content-Type: application/json

{
  "repository_id": 1,
  "webhook_url": "https://example.com/webhook",
  "secret": "your-secret-key",
  "events": ["analysis.complete", "export.*"]
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "repository_id": 1,
  "webhook_url": "https://example.com/webhook",
  "events": ["analysis.complete", "export.*"],
  "active": true,
  "retry_count": 3,
  "retry_delay_seconds": 300,
  "total_deliveries": 0,
  "successful_deliveries": 0,
  "failed_deliveries": 0
}
```

#### List Webhook Configs
```http
GET /api/v1/webhooks/configs?repository_id=1
```

#### Get Webhook Config
```http
GET /api/v1/webhooks/configs/{config_id}
```

#### Update Webhook Config
```http
PATCH /api/v1/webhooks/configs/{config_id}
Content-Type: application/json

{
  "active": false,
  "events": ["analysis.*"]
}
```

#### Delete Webhook Config
```http
DELETE /api/v1/webhooks/configs/{config_id}
```

### Webhook Deliveries

#### Create Webhook Delivery
```http
POST /api/v1/webhooks/deliveries
Content-Type: application/json

{
  "config_id": 1,
  "event_type": "analysis.complete",
  "payload": {
    "event_type": "analysis.complete",
    "timestamp": "2025-10-12T12:00:00Z",
    "repository": "owner/repo",
    "analysis_id": 123,
    "status": "completed"
  }
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "config_id": 1,
  "event_type": "analysis.complete",
  "status": "pending",
  "attempt_number": 1,
  "scheduled_for": "2025-10-12T12:00:00Z"
}
```

#### List Webhook Deliveries
```http
GET /api/v1/webhooks/deliveries?config_id=1&status=delivered&page=1&page_size=50
```

**Query Parameters**:
- `config_id` (optional) - Filter by webhook config
- `event_type` (optional) - Filter by event type
- `status_filter` (optional) - Filter by delivery status
- `page` (default: 1) - Page number
- `page_size` (default: 50) - Items per page

**Response**: `200 OK`
```json
{
  "deliveries": [
    {
      "id": 1,
      "config_id": 1,
      "event_type": "analysis.complete",
      "status": "delivered",
      "http_status_code": 200,
      "attempt_number": 1,
      "duration_ms": 234,
      "attempted_at": "2025-10-12T12:00:01Z",
      "completed_at": "2025-10-12T12:00:01Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

#### Get Webhook Delivery
```http
GET /api/v1/webhooks/deliveries/{delivery_id}
```

#### Retry Failed Delivery
```http
POST /api/v1/webhooks/deliveries/{delivery_id}/retry
```

Manually retry a failed delivery immediately.

**Response**: `202 Accepted`
```json
{
  "status": "scheduled",
  "delivery_id": 1,
  "message": "Delivery scheduled for retry"
}
```

### Statistics

#### Get Webhook Statistics
```http
GET /api/v1/webhooks/statistics?config_id=1
```

**Response**: `200 OK`
```json
{
  "total_configs": 1,
  "total_deliveries": 100,
  "successful_deliveries": 95,
  "failed_deliveries": 5,
  "success_rate": 95.0
}
```

## Event Types

### Analysis Events
- `analysis.started` - Analysis job started
- `analysis.complete` - Analysis completed successfully
- `analysis.failed` - Analysis failed

### Export Events
- `export.started` - Export job started
- `export.complete` - Export completed successfully
- `export.failed` - Export failed

### Batch Events
- `batch.analysis.complete` - Batch analysis completed
- `batch.export.complete` - Batch export completed

### Wildcard Subscriptions
Use wildcards to subscribe to all events in a category:
- `analysis.*` - All analysis events
- `export.*` - All export events
- `*.complete` - All completion events (not supported)

## Webhook Payload Format

All webhook payloads follow this structure:

```json
{
  "event_type": "analysis.complete",
  "timestamp": "2025-10-12T12:00:00Z",
  "project_id": 1,
  "repository": "owner/repo",
  "data": {
    // Event-specific data
  }
}
```

### Example: Analysis Complete
```json
{
  "event_type": "analysis.complete",
  "timestamp": "2025-10-12T12:00:00Z",
  "project_id": 1,
  "repository": "owner/repo",
  "data": {
    "analysis_id": 123,
    "status": "completed",
    "technologies_detected": 15,
    "dependencies_analyzed": 42,
    "duration_seconds": 12.5
  }
}
```

## Security

### Signature Verification

All webhook deliveries include an HMAC-SHA256 signature in the `X-Hub-Signature-256` header.

**Header Format**:
```
X-Hub-Signature-256: sha256=<hex-signature>
```

**Verification (Python)**:
```python
import hmac
import hashlib

def verify_signature(payload_body: bytes, secret: str, signature_header: str) -> bool:
    if not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header[7:]  # Remove 'sha256=' prefix

    mac = hmac.new(secret.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    computed_signature = mac.hexdigest()

    return hmac.compare_digest(computed_signature, expected_signature)
```

**Verification (Node.js)**:
```javascript
const crypto = require('crypto');

function verifySignature(payloadBody, secret, signatureHeader) {
    if (!signatureHeader.startsWith('sha256=')) {
        return false;
    }

    const expectedSignature = signatureHeader.substring(7);
    const computedSignature = crypto
        .createHmac('sha256', secret)
        .update(payloadBody)
        .digest('hex');

    return crypto.timingSafeEqual(
        Buffer.from(expectedSignature),
        Buffer.from(computedSignature)
    );
}
```

### Headers Sent

Every webhook delivery includes these headers:

- `Content-Type: application/json`
- `User-Agent: CommandCenter-Webhook/1.0`
- `X-Webhook-Event: <event-type>`
- `X-Webhook-Delivery-ID: <delivery-id>`
- `X-Hub-Signature-256: sha256=<signature>` (if secret configured)

## Retry Logic

### Exponential Backoff

Failed deliveries are automatically retried with exponential backoff:

| Attempt | Delay Formula | Example (base=300s) |
|---------|---------------|---------------------|
| 1 | base × 2^0 | 300s (5 min) |
| 2 | base × 2^1 | 600s (10 min) |
| 3 | base × 2^2 | 1200s (20 min) |

**Configuration**:
- `retry_count` - Maximum retry attempts (default: 3)
- `retry_delay_seconds` - Base delay in seconds (default: 300)
- `max_delivery_time_seconds` - Maximum time for delivery (default: 3600)

### Retry Status Flow

```
pending → delivering → delivered (success)
                   ↓
                retrying (failure) → delivering → ...
                   ↓
                exhausted (all retries failed)
```

### Manual Retry

You can manually retry failed deliveries:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/deliveries/1/retry
```

## Background Processing

### Celery Tasks

The webhook system uses Celery for background processing:

1. **deliver_webhook** - Attempts webhook delivery
   - Called for each delivery attempt
   - Handles HTTP request and response processing
   - Updates delivery status and schedules retries

2. **create_and_deliver_webhook** - Creates and delivers webhook
   - Convenience task for triggering webhooks
   - Used by other tasks (analysis, export, etc.)

3. **process_pending_deliveries** - Processes retry queue
   - Should run periodically (e.g., every 5 minutes)
   - Picks up scheduled retries
   - Processes pending deliveries

### Scheduled Processing

Add to Celery beat schedule:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'process-pending-webhook-deliveries': {
        'task': 'app.tasks.webhook_tasks.process_pending_deliveries',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'kwargs': {'max_deliveries': 100},
    },
}
```

## Monitoring

### Delivery Statistics

Monitor webhook health with statistics:

```bash
curl http://localhost:8000/api/v1/webhooks/statistics
```

**Key Metrics**:
- `total_deliveries` - Total delivery attempts
- `successful_deliveries` - Successful deliveries (2xx status)
- `failed_deliveries` - Failed deliveries (exhausted retries)
- `success_rate` - Success percentage

### Prometheus Metrics

Webhook metrics are exposed at `/metrics`:

- `commandcenter_webhook_deliveries_total{status}` - Total deliveries by status
- `commandcenter_webhook_delivery_duration_seconds` - Delivery latency histogram
- `commandcenter_webhook_retry_attempts_total` - Total retry attempts

### Logging

Webhook operations are logged with structured logging:

```python
logger.info(
    "Webhook delivery successful",
    extra={
        "delivery_id": delivery.id,
        "config_id": config.id,
        "event_type": event_type,
        "http_status": response.status_code,
        "duration_ms": duration_ms,
    }
)
```

## Best Practices

### Webhook Endpoints

1. **Respond quickly** - Return 2xx within 30 seconds
2. **Process asynchronously** - Queue webhook for processing, return immediately
3. **Idempotency** - Use `X-Webhook-Delivery-ID` to deduplicate
4. **Verify signatures** - Always verify HMAC signature
5. **Handle retries** - Be prepared for duplicate deliveries

### Event Design

1. **Use specific event types** - `analysis.complete` not `event`
2. **Include context** - Add repository, IDs, timestamps
3. **Keep payloads small** - Include IDs, use API for details
4. **Version payloads** - Add version field for compatibility

### Configuration

1. **Use HTTPS** - Always use HTTPS for webhook URLs
2. **Rotate secrets** - Periodically rotate webhook secrets
3. **Monitor statistics** - Set up alerts for high failure rates
4. **Filter events** - Subscribe only to needed events
5. **Set appropriate retries** - Balance reliability vs. latency

## Troubleshooting

### Deliveries Not Received

1. Check webhook config is active:
   ```bash
   curl http://localhost:8000/api/v1/webhooks/configs/1
   ```

2. Verify event subscription:
   - Check `events` field includes the event type
   - Test wildcard matches: `analysis.*` matches `analysis.complete`

3. Check delivery status:
   ```bash
   curl http://localhost:8000/api/v1/webhooks/deliveries?config_id=1&status=failed
   ```

4. Review error messages in delivery records

### High Failure Rate

1. Check target endpoint availability
2. Verify endpoint returns 2xx status codes
3. Check response time (< 30s timeout)
4. Review error messages in failed deliveries
5. Consider increasing `retry_count` or `retry_delay_seconds`

### Signature Verification Failures

1. Ensure secret matches webhook configuration
2. Verify HMAC computation uses raw request body
3. Check signature format: `sha256=<hex>`
4. Use constant-time comparison (`hmac.compare_digest`)

## Code Examples

### Receiving Webhooks (FastAPI)

```python
from fastapi import FastAPI, Request, HTTPException, Header
import hmac
import hashlib

app = FastAPI()

WEBHOOK_SECRET = "your-secret-key"

def verify_signature(body: bytes, signature: str) -> bool:
    if not signature.startswith("sha256="):
        return False

    expected = signature[7:]
    computed = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed, expected)

@app.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str = Header(...)
):
    body = await request.body()

    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    # Process webhook asynchronously
    # task_queue.enqueue(process_webhook, payload)

    return {"status": "received"}
```

### Triggering Webhooks

```python
from app.tasks.webhook_tasks import create_and_deliver_webhook

# Trigger webhook for analysis completion
create_and_deliver_webhook.delay(
    config_id=1,
    project_id=1,
    event_type="analysis.complete",
    payload={
        "event_type": "analysis.complete",
        "timestamp": datetime.utcnow().isoformat(),
        "repository": "owner/repo",
        "data": {
            "analysis_id": 123,
            "status": "completed",
        }
    }
)
```

## Database Schema

### webhook_configs
```sql
CREATE TABLE webhook_configs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    webhook_url VARCHAR(512) NOT NULL,
    secret VARCHAR(512) NOT NULL,
    events JSONB DEFAULT '[]',
    active BOOLEAN DEFAULT TRUE,
    delivery_mode VARCHAR(20) DEFAULT 'async',
    retry_count INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 300,
    max_delivery_time_seconds INTEGER DEFAULT 3600,
    total_deliveries INTEGER DEFAULT 0,
    successful_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0,
    last_delivery_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### webhook_deliveries
```sql
CREATE TABLE webhook_deliveries (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    config_id INTEGER NOT NULL REFERENCES webhook_configs(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    target_url VARCHAR(512) NOT NULL,
    attempt_number INTEGER DEFAULT 1,
    status VARCHAR(20) NOT NULL,
    http_status_code INTEGER,
    response_body TEXT,
    error_message TEXT,
    scheduled_for TIMESTAMP DEFAULT NOW(),
    attempted_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_scheduled ON webhook_deliveries(scheduled_for);
```

## See Also

- [API Documentation](http://localhost:8000/docs)
- [Observability Guide](./OBSERVABILITY.md)
- [Phase 2 Implementation Plan](./planning/PHASE2_REVISED_PLAN.md)
