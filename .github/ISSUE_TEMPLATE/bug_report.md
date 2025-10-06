---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## Screenshots

If applicable, add screenshots to help explain your problem.

## Environment

**Desktop/Server:**
- OS: [e.g., macOS 13.0, Ubuntu 22.04, Windows 11]
- Browser: [e.g., Chrome 120, Firefox 121, Safari 17]
- Version: [e.g., 1.0.0]

**Docker:**
- Docker version: [e.g., 24.0.0]
- Docker Compose version: [e.g., 2.20.0]

**Deployment:**
- Deployment type: [e.g., Docker Compose, Traefik]
- Environment: [e.g., Development, Production]

## Logs

Please include relevant logs:

```
# Backend logs
docker compose logs backend

# Frontend logs
docker compose logs frontend

# Database logs
docker compose logs postgres
```

## Configuration

Please share relevant configuration (remove sensitive data):

```bash
# .env settings (REMOVE SECRETS!)
COMPOSE_PROJECT_NAME=...
BACKEND_PORT=...
```

## Additional Context

Add any other context about the problem here.

## Possible Solution

If you have a suggestion for fixing the bug, please describe it here.

## Checklist

- [ ] I have searched existing issues to ensure this is not a duplicate
- [ ] I have included all relevant information above
- [ ] I have removed all sensitive data (passwords, tokens, etc.)
- [ ] I have included logs and error messages
- [ ] I have specified my environment details
