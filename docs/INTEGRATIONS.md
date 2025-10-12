# External Integrations Guide

**CommandCenter External Integrations** - Connect your R&D workflow with GitHub and extend with custom integrations.

---

## Table of Contents

1. [Overview](#overview)
2. [GitHub Integration](#github-integration)
3. [GitHub Action](#github-action)
4. [Custom Integrations](#custom-integrations)
5. [API Reference](#api-reference)
6. [Troubleshooting](#troubleshooting)

---

## Overview

CommandCenter provides a flexible integration framework that allows you to:

- **Sync GitHub Issues** with Research Tasks (bidirectional)
- **Automate PR analysis** via GitHub Actions
- **Handle webhooks** from external services
- **Extend** with custom integrations using base classes

### Available Integrations

| Integration | Status | Features |
|------------|--------|----------|
| **GitHub** | ✅ Implemented | Issues sync, PR analysis, webhooks, Projects |
| **Custom** | ✅ Framework | Base classes for building your own |

---

## GitHub Integration

### Features

1. **Issues ↔ Research Tasks Sync**
   - GitHub Issues automatically create Research Tasks
   - Research Tasks can create GitHub Issues
   - Bidirectional status updates
   - Priority mapping from labels

2. **Webhook Support**
   - Issues events (opened, closed, edited)
   - Pull Request events (opened, synchronize)
   - Push events (default branch only)

3. **GitHub Projects** (partial)
   - List projects
   - Columns support via GraphQL (planned)

### Setup

#### 1. Create GitHub Personal Access Token

```bash
# Required scopes:
# - repo (full control)
# - read:org
# - admin:repo_hook

# Navigate to: https://github.com/settings/tokens/new
# Generate token and save securely
```

#### 2. Configure Integration

```python
# Via CommandCenter API or UI
POST /api/v1/integrations

{
  "project_id": 1,
  "name": "GitHub: my-org",
  "integration_type": "github",
  "auth_type": "token",
  "access_token": "ghp_...",  # Will be encrypted
  "config": {
    "webhook_secret": "your_webhook_secret",  # Generate with: openssl rand -hex 32
    "default_labels": ["commandcenter"],
    "auto_sync": true
  }
}
```

#### 3. Configure Webhook (Optional)

Set up webhook in your GitHub repository:

1. Go to **Settings → Webhooks → Add webhook**
2. **Payload URL**: `https://your-commandcenter.com/api/v1/integrations/github/webhook`
3. **Content type**: `application/json`
4. **Secret**: Use the `webhook_secret` from step 2
5. **Events**: Select `Issues`, `Pull requests`, `Pushes`

### Usage Examples

#### Sync Issue to Task

```python
# Automatic via webhook when issue is created/updated

# Or manual via API
POST /api/v1/integrations/{integration_id}/sync/issue-to-task

{
  "issue_number": 123,
  "repository": {
    "owner": "my-org",
    "name": "my-repo"
  }
}
```

#### Create Issue from Task

```python
POST /api/v1/integrations/{integration_id}/sync/task-to-issue

{
  "task_id": 456,
  "repository": {
    "owner": "my-org",
    "name": "my-repo"
  }
}

# Response:
{
  "issue_number": 124,
  "url": "https://github.com/my-org/my-repo/issues/124",
  "action": "created"
}
```

### Priority Mapping

GitHub labels automatically map to task priorities:

| GitHub Label | Task Priority |
|--------------|---------------|
| `priority: high`, `critical`, `urgent` | `high` |
| `priority: low` | `low` |
| Other labels | `medium` (default) |

### Status Mapping

| GitHub Issue State | Task Status |
|-------------------|-------------|
| `open` | `todo` |
| `closed` | `done` |

---

## GitHub Action

### Overview

Automate repository analysis on Pull Requests using CommandCenter's GitHub Action.

**Location**: `.github/actions/commandcenter-analyze/`

### Quick Start

```yaml
# .github/workflows/pr-analysis.yml
name: PR Analysis

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run CommandCenter Analysis
        uses: ./.github/actions/commandcenter-analyze
        with:
          commandcenter-url: ${{ secrets.COMMANDCENTER_URL }}
          api-token: ${{ secrets.COMMANDCENTER_TOKEN }}
          project-id: ${{ secrets.COMMANDCENTER_PROJECT_ID }}
```

### Configuration

#### Required Secrets

Add these to your GitHub repository secrets:

```bash
# COMMANDCENTER_URL
https://your-commandcenter-instance.com

# COMMANDCENTER_TOKEN
# Generate via: CommandCenter UI → Settings → API Tokens
# Required scopes: jobs:create, jobs:read

# COMMANDCENTER_PROJECT_ID
1  # Your project ID from CommandCenter
```

#### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `commandcenter-url` | CommandCenter API URL | Yes | - |
| `api-token` | API authentication token | Yes | - |
| `project-id` | CommandCenter project ID | Yes | - |
| `repository-id` | Specific repo ID | No | Auto-detect |
| `analysis-depth` | `quick`, `standard`, `comprehensive` | No | `standard` |
| `post-comment` | Post results to PR | No | `true` |
| `fail-on-errors` | Fail on critical issues | No | `false` |

#### Outputs

| Output | Description |
|--------|-------------|
| `job-id` | CommandCenter job ID |
| `status` | `completed`, `failed`, `timeout` |
| `summary` | Analysis summary text |

### Advanced Workflows

#### Quality Gates

```yaml
- name: Analyze with Quality Gates
  uses: ./.github/actions/commandcenter-analyze
  with:
    commandcenter-url: ${{ secrets.COMMANDCENTER_URL }}
    api-token: ${{ secrets.COMMANDCENTER_TOKEN }}
    project-id: ${{ secrets.COMMANDCENTER_PROJECT_ID }}
    analysis-depth: comprehensive
    fail-on-errors: 'true'  # Block PR if critical issues found
```

#### Scheduled Analysis

```yaml
# .github/workflows/daily-analysis.yml
name: Daily Analysis

on:
  schedule:
    - cron: '0 9 * * 1-5'  # Weekdays at 9 AM

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Full Analysis
        uses: ./.github/actions/commandcenter-analyze
        with:
          commandcenter-url: ${{ secrets.COMMANDCENTER_URL }}
          api-token: ${{ secrets.COMMANDCENTER_TOKEN }}
          project-id: ${{ secrets.COMMANDCENTER_PROJECT_ID }}
          analysis-depth: comprehensive
          post-comment: 'false'  # No PR to comment on
```

#### Multi-Repository Matrix

```yaml
jobs:
  analyze:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        repo: [backend, frontend, infrastructure]
    steps:
      - uses: actions/checkout@v4
        with:
          repository: my-org/${{ matrix.repo }}

      - name: Analyze ${{ matrix.repo }}
        uses: ./.github/actions/commandcenter-analyze
        with:
          commandcenter-url: ${{ secrets.COMMANDCENTER_URL }}
          api-token: ${{ secrets.COMMANDCENTER_TOKEN }}
          project-id: ${{ secrets.COMMANDCENTER_PROJECT_ID }}
```

---

## Custom Integrations

### Creating Custom Integrations

Use the base integration framework to build your own integrations.

#### 1. Extend BaseIntegration

```python
# app/integrations/custom.py
from app.integrations.base import BaseIntegration, IntegrationError
from typing import Dict, Any

class CustomIntegration(BaseIntegration):
    """Custom integration implementation."""

    def __init__(self, integration_id: int, db: AsyncSession):
        super().__init__(
            integration_id=integration_id,
            db=db,
            integration_type="custom",
        )

    async def test_connection(self) -> bool:
        """Test if connection is working."""
        try:
            token = await self.get_access_token()
            # Make test API call
            # ...
            await self.record_success()
            return True
        except Exception as e:
            await self.record_error(str(e))
            raise IntegrationError(f"Connection test failed: {e}")

    async def get_display_name(self) -> str:
        """Get display name."""
        return "Custom Integration"

    async def sync_data(self) -> Dict[str, Any]:
        """Custom sync logic."""
        # Implement your sync logic
        pass
```

#### 2. Add Webhook Support

```python
from app.integrations.base import WebhookIntegration

class CustomWebhookIntegration(WebhookIntegration):
    """Custom integration with webhook support."""

    async def handle_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle webhook events."""
        if event_type == "data.updated":
            return await self._handle_data_update(payload)
        return {"status": "ignored"}

    def get_webhook_secret(self) -> str:
        """Get webhook secret from config."""
        integration = self._integration
        return integration.config.get("webhook_secret", "")

    async def _handle_data_update(self, payload: Dict[str, Any]):
        """Handle data update event."""
        # Your logic here
        await self.record_success()
        return {"status": "processed"}
```

#### 3. Add OAuth Support

```python
from app.integrations.base import OAuthIntegration

class CustomOAuthIntegration(OAuthIntegration):
    """Custom OAuth integration."""

    def get_oauth_authorize_url(self, state: str, redirect_uri: str) -> str:
        """Get OAuth authorization URL."""
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "read write",
        }
        return f"https://api.service.com/oauth/authorize?{urlencode(params)}"

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.service.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                }
            )
            response.raise_for_status()
            return response.json()
```

### Base Class Features

All integrations inherit these features:

- **Token Management**: Encrypted storage, automatic refresh
- **Health Monitoring**: Success/error tracking, auto-disable on failures
- **Rate Limiting**: Track and respect API rate limits
- **Webhook Verification**: HMAC-SHA256 signature verification
- **Error Recovery**: Exponential backoff, retry logic

---

## API Reference

### Integration Endpoints

```python
# List integrations
GET /api/v1/integrations?project_id=1

# Create integration
POST /api/v1/integrations
{
  "project_id": 1,
  "name": "GitHub Integration",
  "integration_type": "github",
  "auth_type": "token",
  "access_token": "ghp_..."
}

# Get integration
GET /api/v1/integrations/{id}

# Update integration
PATCH /api/v1/integrations/{id}
{
  "enabled": false
}

# Delete integration
DELETE /api/v1/integrations/{id}

# Test connection
POST /api/v1/integrations/{id}/test

# Get health status
GET /api/v1/integrations/{id}/health
```

### GitHub-Specific Endpoints

```python
# Sync issue to task
POST /api/v1/integrations/{id}/github/sync/issue-to-task
{
  "issue_number": 123,
  "repository": {"owner": "org", "name": "repo"}
}

# Sync task to issue
POST /api/v1/integrations/{id}/github/sync/task-to-issue
{
  "task_id": 456,
  "repository": {"owner": "org", "name": "repo"}
}

# List projects
GET /api/v1/integrations/{id}/github/projects?owner=org&repo=repo

# Handle webhook (called by GitHub)
POST /api/v1/integrations/github/webhook
X-Hub-Signature-256: sha256=...
X-GitHub-Event: issues
{...}
```

---

## Troubleshooting

### GitHub Integration Issues

#### Issue: Webhook signature verification fails

**Symptoms**: Webhook events rejected with 401 Unauthorized

**Solution**:
```bash
# Verify webhook secret matches
# In GitHub: Settings → Webhooks → Edit → Secret
# In CommandCenter: integration.config.webhook_secret

# Test signature generation:
echo -n '{"test": "payload"}' | openssl dgst -sha256 -hmac "your_secret"
```

#### Issue: Issues not syncing to tasks

**Symptoms**: GitHub issues created but no tasks appear

**Solution**:
1. Check webhook is configured for "Issues" events
2. Verify integration is enabled: `GET /api/v1/integrations/{id}`
3. Check integration health: `GET /api/v1/integrations/{id}/health`
4. Review logs for errors

#### Issue: Token expired

**Symptoms**: API calls fail with 401 Unauthorized

**Solution**:
```python
# GitHub Personal Access Tokens don't expire automatically
# Check token is still valid:
curl -H "Authorization: token ghp_..." https://api.github.com/user

# If invalid, generate new token and update integration:
PATCH /api/v1/integrations/{id}
{
  "access_token": "ghp_new_token"
}
```

### GitHub Action Issues

#### Issue: Action times out

**Solution**: Reduce analysis depth or increase timeout

```yaml
with:
  analysis-depth: quick  # Instead of comprehensive
```

#### Issue: PR comments not posted

**Solution**: Check workflow permissions

```yaml
permissions:
  contents: read
  pull-requests: write  # Required for comments
```

#### Issue: Analysis job fails

**Solution**: Check CommandCenter API accessibility

```yaml
- name: Test API
  run: |
    curl -f ${{ secrets.COMMANDCENTER_URL }}/api/v1/health \
      -H "Authorization: Bearer ${{ secrets.COMMANDCENTER_TOKEN }}"
```

### Custom Integration Issues

#### Issue: Integration disabled after errors

**Symptoms**: `enabled: false`, `status: error`

**Solution**:
```python
# Integrations auto-disable after 5 consecutive errors
# Fix the underlying issue, then re-enable:

PATCH /api/v1/integrations/{id}
{
  "enabled": true,
  "status": "active"
}

# Check health before re-enabling:
POST /api/v1/integrations/{id}/test
```

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("app.integrations").setLevel(logging.DEBUG)
```

Check integration health:

```bash
curl http://localhost:8000/api/v1/integrations/1/health | jq
```

Monitor error counts:

```python
GET /api/v1/integrations/{id}

{
  "error_count": 0,
  "success_count": 142,
  "success_rate": 100.0,
  "last_error": null
}
```

---

## Additional Resources

- **GitHub Action README**: `.github/actions/commandcenter-analyze/README.md`
- **API Documentation**: `http://localhost:8000/docs`
- **Integration Model**: `backend/app/models/integration.py`
- **Base Classes**: `backend/app/integrations/base.py`
- **GitHub Integration**: `backend/app/integrations/github_integration.py`

---

**Last Updated**: 2025-10-12
**Version**: 1.0.0
**Author**: CommandCenter Development Team
