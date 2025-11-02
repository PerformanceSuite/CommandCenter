# Phase A: Dagger Production Hardening - Implementation Design

**Author**: Claude + Developer
**Date**: 2025-11-02
**Status**: Approved for Implementation
**Related**: `docs/plans/2025-10-29-phase-a-dagger-hardening-plan.md` (detailed task breakdown)
**Dagger SDK Version**: 0.19.4 (upgraded 2025-11-02)

## Executive Summary

This document captures the validated design for implementing Phase A of the Production Foundations work. Phase A transforms the basic CommandCenterStack Dagger orchestration into production-grade container management with full observability, health checks, resource limits, security hardening, and error recovery.

**Implementation Approach**: Sequential Task-by-Task (Plan-Driven)
**Duration**: 3 weeks (10 tasks)
**Methodology**: Test-Driven Development (TDD) throughout

## Context

### Current State
- CommandCenterStack exists in `hub/backend/app/dagger_modules/commandcenter.py`
- Basic container lifecycle (start/stop) works
- No log retrieval, health checks, resource limits, or security hardening
- Dagger SDK just upgraded to 0.19.4 (commit: 12448b9)

### Goals
- Production-grade orchestration with full operational capabilities
- Enable future work (Phase B: Knowledge Ingestion, Phase C: Observability)
- Establish patterns for infrastructure reliability

## Architecture Design

### Overall Structure

```
CommandCenterStack (Enhanced)
├── Core Orchestration (existing ~100 lines)
│   ├── build_postgres/redis/backend/frontend
│   └── start/stop lifecycle
├── Observability Layer (NEW - Week 1) ~150 lines
│   ├── get_logs() - retrieve container logs
│   ├── _service_containers registry - track running containers
│   └── Log API endpoints in Hub
├── Health & Resource Layer (NEW - Week 2) ~200 lines
│   ├── check_*_health() methods (4 services)
│   ├── health_status() aggregation
│   └── ResourceLimits dataclass + application
└── Security & Recovery Layer (NEW - Week 3) ~150 lines
    ├── Non-root user execution
    ├── @with_retry decorator
    └── restart_service() method

Total: ~600 lines (6x current size)
Test growth: 74 → 120+ tests
```

### Design Principles

1. **Test-Driven Development (TDD)**: Every feature starts with a failing test
2. **Incremental Enhancement**: Build on existing code without breaking changes
3. **Dagger SDK Native**: Use SDK 0.19.4 capabilities, not workarounds
4. **Production Patterns**: Industry-standard practices for reliability

## Week 1: Observability Layer (Tasks 1-3)

### Design Decisions

**Service Registry Pattern**:
- Add `_service_containers: dict[str, dagger.Container] = {}` to CommandCenterStack
- Populate in `start()` method after building each container
- Enables log retrieval and health checks to access running containers

**Log Retrieval Strategy**:
```python
async def get_logs(service_name: str, tail: int = 100, follow: bool = False) -> str:
    # Validate service_name in ["postgres", "redis", "backend", "frontend"]
    # Get container from registry
    # Call container.stdout() via Dagger SDK
    # Apply tail limit to prevent memory issues
    # Return log string
```

**API Integration**:
- Hub API endpoint: `GET /api/v1/projects/{id}/logs/{service}?tail=N`
- OrchestrationService.get_project_logs() bridges Hub → Stack
- Validation: service name, project exists, stack running

### Deliverables

- **Task 1**: get_logs() method + unit tests (hub/backend/tests/unit/test_dagger_logs.py)
- **Task 2**: Service registry + _get_service_container() + tests
- **Task 3**: Hub API endpoint + OrchestrationService method + integration tests

### Testing Strategy

- Unit tests: Mock Dagger containers, verify method behavior
- Integration tests: Full API request → log retrieval
- Error cases: Invalid service, container not found, client not initialized

## Week 2: Health & Resource Layer (Tasks 4-5)

### Health Check Design

**Service-Specific Commands**:
- **Postgres**: `pg_isready -U commandcenter` (exit 0 = healthy)
- **Redis**: `redis-cli ping` (output "PONG" = healthy)
- **Backend**: `curl -f http://localhost:8000/health` (HTTP 200 = healthy)
- **Frontend**: `curl -f http://localhost:3000/` (HTTP 200 = healthy)

**Implementation Pattern**:
```python
async def check_postgres_health() -> dict:
    container = self._service_containers.get("postgres")
    if not container:
        return {"healthy": False, "service": "postgres", "error": "Container not found"}

    result = await container.with_exec(["pg_isready", "-U", "commandcenter"]).stdout()
    healthy = "accepting connections" in result

    return {
        "healthy": healthy,
        "service": "postgres",
        "message": result.strip()
    }
```

**Aggregated Health**:
```python
async def health_status() -> dict:
    services = {}
    services["postgres"] = await self.check_postgres_health()
    services["redis"] = await self.check_redis_health()
    services["backend"] = await self.check_backend_health()
    services["frontend"] = await self.check_frontend_health()

    overall_healthy = all(svc["healthy"] for svc in services.values())

    return {
        "overall_healthy": overall_healthy,
        "services": services,
        "timestamp": str(datetime.now())
    }
```

### Resource Limits Design

**ResourceLimits Dataclass**:
```python
@dataclass
class ResourceLimits:
    postgres_cpu: float = 1.0      # 1 full CPU
    postgres_memory_mb: int = 2048 # 2GB RAM
    redis_cpu: float = 0.5         # Half CPU
    redis_memory_mb: int = 512     # 512MB RAM
    backend_cpu: float = 1.0       # 1 full CPU
    backend_memory_mb: int = 1024  # 1GB RAM
    frontend_cpu: float = 0.5      # Half CPU
    frontend_memory_mb: int = 512  # 512MB RAM
```

**Application**:
```python
# In build_postgres():
return (
    self.client.container()
    .from_("postgres:15-alpine")
    # ... other config ...
    .with_resource_limit("cpu", str(limits.postgres_cpu))
    .with_resource_limit("memory", f"{limits.postgres_memory_mb}m")
)
```

**Rationale for Defaults**:
- Postgres: Database needs memory for buffers/cache (2GB reasonable)
- Redis: In-memory cache, lighter workload (512MB sufficient)
- Backend: Python app with FastAPI, moderate memory needs
- Frontend: Nginx serving static assets, minimal resources

### Deliverables

- **Task 4**: Health check methods (4 services) + health_status() + unit tests (hub/backend/tests/unit/test_dagger_health.py)
- **Task 5**: ResourceLimits dataclass + apply to all builds + tests (hub/backend/tests/unit/test_dagger_resources.py)

### Testing Strategy

- Unit tests: Mock container.with_exec(), verify health logic
- Integration tests: Actual health checks against running containers
- Resource tests: Verify limits applied via Dagger SDK

## Week 3: Security & Recovery Layer (Tasks 6-8)

### Security Hardening Design

**Non-Root Execution**:
- Postgres: UID 999 (standard postgres user in Alpine base image)
- Redis: UID 999 (standard redis user in Alpine base image)
- Backend: UID 1000 (non-privileged application user)
- Frontend: UID 1000 (non-privileged application user)

**Implementation**:
```python
class CommandCenterStack:
    POSTGRES_USER_ID = 999
    REDIS_USER_ID = 999
    APP_USER_ID = 1000

    async def build_postgres(self) -> dagger.Container:
        return (
            self.client.container()
            .from_("postgres:15-alpine")
            .with_user(str(self.POSTGRES_USER_ID))  # Early in chain
            # ... rest of config ...
        )
```

**Why Non-Root Matters**:
- Limits blast radius if container is compromised
- Follows principle of least privilege
- Standard security best practice for production containers

### Error Recovery Design

**Retry Decorator with Exponential Backoff**:
```python
def with_retry(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s, 8s
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator

@with_retry(max_retries=3, base_delay=1)
async def start() -> dict:
    # Automatically retries transient failures
    ...
```

**Handles**: Network timeouts, image pull failures, temporary resource unavailability

**Service Restart**:
```python
async def restart_service(service_name: str) -> dict:
    # Validate service name
    # Get appropriate build method (build_postgres, build_redis, etc.)
    # Rebuild container with correct dependencies
    # Update _service_containers registry
    # Restart as service
    # Return success/failure status
```

**API Integration**: `POST /api/v1/projects/{id}/services/{service}/restart`

### Deliverables

- **Task 6**: Non-root execution + security tests (hub/backend/tests/security/test_dagger_security.py)
- **Task 7**: @with_retry decorator + retry behavior tests (hub/backend/tests/unit/test_dagger_retry.py)
- **Task 8**: restart_service() + API endpoint + tests (hub/backend/tests/integration/test_restart_api.py)
- **Task 9**: Documentation updates (DAGGER_ARCHITECTURE.md, SECURITY.md)
- **Task 10**: Full test suite verification + coverage report

### Testing Strategy

- Security tests: Verify with_user() called, no root execution
- Retry tests: Mock failures, verify exponential backoff pattern
- Restart tests: Integration tests for API, verify container rebuilt
- Coverage: Target >90% for all orchestration code

## Documentation & Polish (Tasks 9-10)

### Task 9: Documentation Updates

**DAGGER_ARCHITECTURE.md**:
- Add sections for new features (logs, health, resources, security, recovery)
- Document API endpoints
- Include usage examples
- Architecture diagrams (optional)

**SECURITY.md** (new file):
- Non-root container execution
- Resource limits (prevention of resource exhaustion)
- Network isolation principles
- Secret management best practices
- Security checklist for production deployments

### Task 10: Verification

**Full Test Suite**:
```bash
cd hub/backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

**Coverage Targets**:
- app/dagger_modules/commandcenter.py: >90%
- app/services/orchestration_service.py: >90%
- app/routers/logs.py: >90%
- app/routers/projects.py (restart endpoint): >90%

**Regression Testing**: Ensure no existing functionality broken

## Success Criteria

### Technical Milestones

- ✅ All services have health checks with accurate status reporting
- ✅ Logs retrievable via API for all services (postgres, redis, backend, frontend)
- ✅ Resource limits enforced and configurable per service
- ✅ Security checklist 100% complete (non-root, resource limits documented)
- ✅ Error recovery demonstrated (retry logic works, restart API functional)
- ✅ Test coverage >90% for orchestration code
- ✅ Documentation complete and reviewed (DAGGER_ARCHITECTURE.md, SECURITY.md)
- ✅ All 120+ tests passing
- ✅ No regressions in existing functionality

### Quality Gates

Each task must pass before proceeding to next:
1. Tests written and failing (TDD red phase)
2. Implementation written (TDD green phase)
3. Tests passing (TDD green phase)
4. Code reviewed (self-review or pair review)
5. Committed with descriptive message

## Implementation Plan Reference

Detailed task-by-task implementation steps with exact code examples are in:
**`docs/plans/2025-10-29-phase-a-dagger-hardening-plan.md`**

This design document provides the architectural rationale and design decisions. The implementation plan provides the step-by-step execution guide.

## Next Steps

1. **Design Approval**: ✅ (this document validated)
2. **Worktree Setup**: Create isolated workspace for implementation
3. **Execute Plan**: Use `/superpowers:execute-plan` with the detailed plan
4. **Track Progress**: TodoWrite for each task completion

## Notes

- **Dagger SDK 0.19.4**: Recently upgraded (commit 12448b9), verify API compatibility during implementation
- **TDD Discipline**: Every task follows RED-GREEN-REFACTOR cycle
- **Incremental Commits**: Commit after each task completion, not in batches
- **Documentation**: Update docs in same commit as code changes

---

**Status**: ✅ Design Complete and Approved
**Next Phase**: Worktree Setup → Plan Execution
