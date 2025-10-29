# Hub Security Tests

## Overview

Hub security tests validate multi-instance isolation, Dagger orchestration security, and port conflict handling for the CommandCenter Hub.

## Test Structure

### Multi-Instance Isolation (`test_multi_instance_isolation.py`)

**Goal:** Ensure complete isolation between multiple CommandCenter projects.

**Tests (8 total):**
- Project volumes are isolated (no shared Docker volumes) (1)
- Environment variables not leaked between projects (1)
- Database files isolated per project (1)
- Container names unique per project (1)
- Network isolation between projects (1)

**Critical Security Requirements:**
- Each project uses separate Docker volumes
- Secrets never shared between projects
- Database files in isolated directories
- Unique container names prevent conflicts
- Separate networks prevent cross-project access

### Dagger Orchestration Security (`test_dagger_security.py`)

**Goal:** Validate Dagger SDK security practices.

**Tests (5 total):**
- Dagger containers use least privilege (1)
- Secrets not logged or exposed (1)
- Host filesystem access restricted (1)
- Network isolation (1)
- Container resource limits (1)

**Security Principles:**
- Run containers as non-root when possible
- Handle secrets securely (no logs, no env leaks)
- Restrict filesystem mounts to project directory only
- Use isolated networks per project
- Set CPU/memory limits to prevent resource exhaustion

### Port Conflict Handling (`test_port_conflicts.py`)

**Goal:** Prevent and resolve port conflicts.

**Tests (3 total):**
- Detect port conflicts before start (1)
- Suggest alternative ports on conflict (1)
- Prevent multiple instances with same ports (1)

**Conflict Resolution:**
- Scan ports before starting projects
- Suggest alternatives (increment by 10)
- Block simultaneous use of same ports

## Running Hub Security Tests

**All Hub security tests:**
```bash
cd hub/backend
pytest tests/security/ -v
```

**Specific category:**
```bash
pytest tests/security/test_multi_instance_isolation.py -v
```

## Test Count

**Total: 16 tests**
- Multi-instance isolation: 8 tests
- Dagger security: 5 tests
- Port conflicts: 3 tests

## Security Principles

### 1. Data Isolation

Every project must be completely isolated:
- Separate Docker volumes
- Separate database files
- Separate secrets
- No shared configuration

### 2. Network Isolation

Projects cannot access each other's services:
- Unique Docker networks per project
- No cross-project communication
- Port binding only on localhost (or explicit IPs)

### 3. Secret Management

Secrets are project-specific:
- Generated at runtime, not stored
- Never logged or exposed in errors
- Unique per project (no defaults)

### 4. Resource Limits

Prevent resource exhaustion:
- CPU limits per container
- Memory limits per container
- Storage quotas for volumes

## Hub-Specific Security Concerns

### Docker Socket Access

Hub backend requires Docker socket access for Dagger:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

**Risks:**
- Full Docker API access
- Can create/destroy any container
- Potential privilege escalation

**Mitigations:**
- Run Hub backend with minimal permissions
- Validate all project configurations
- Log all Docker operations
- Consider Docker-in-Docker alternative

### Multi-Tenancy

Hub manages multiple isolated projects:
- Each project = separate tenant
- No data leakage between tenants
- Enforce project boundaries strictly

## Best Practices

### Project Configuration Validation

```python
def validate_project_config(config: CommandCenterConfig):
    # Ensure unique project name
    assert config.project_name not in active_projects

    # Ensure ports are available
    assert not is_port_in_use(config.ports.backend)
    assert not is_port_in_use(config.ports.frontend)

    # Ensure secrets are unique
    assert config.secrets["secret_key"] != "default"
```

### Cleanup on Removal

```python
async def remove_project(project_name: str):
    # Stop containers
    await stack.stop()

    # Remove volumes
    await stack.remove_volumes()

    # Remove from registry
    del active_stacks[project_name]
```

### Port Conflict Detection

```python
def find_available_ports(base_port: int, count: int = 4) -> List[int]:
    available = []
    port = base_port

    while len(available) < count:
        if not is_port_in_use(port):
            available.append(port)
        port += 1

    return available
```

## Common Vulnerabilities

### ❌ Shared Volumes

```yaml
volumes:
  shared_data:/data  # DON'T - All projects share this volume
```

### ✅ Isolated Volumes

```yaml
volumes:
  proj_a_data:/data  # ✓ - Unique per project
  proj_b_data:/data  # ✓ - Separate volume
```

### ❌ Hardcoded Secrets

```python
config.secrets = {
    "secret_key": "default-secret-123"  # DON'T - Same for all
}
```

### ✅ Generated Secrets

```python
import secrets

config.secrets = {
    "secret_key": secrets.token_urlsafe(32)  # ✓ - Unique per project
}
```

## Testing Checklist

- [ ] Volumes isolated per project
- [ ] Secrets unique per project
- [ ] Database files separated
- [ ] Container names unique
- [ ] Networks isolated
- [ ] Dagger uses least privilege
- [ ] Secrets not logged
- [ ] Filesystem access restricted
- [ ] Resource limits set
- [ ] Port conflicts detected
- [ ] Alternative ports suggested
- [ ] Multiple instances blocked on same ports
