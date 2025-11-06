# Phase 6: Health & Service Discovery Implementation Plan

## Overview
Phase 6 focuses on implementing comprehensive health checking and service discovery for the CommandCenter Hub. This will enable federation capabilities and provide real-time monitoring of all services across multiple CommandCenter instances.

## Timeline
**Duration**: Weeks 6-8 (3 weeks)
**Start Date**: 2025-11-05

## Key Deliverables

### 1. Enhanced Service Model (Week 6)
- Extend existing models to support health tracking
- Add service metadata and health check configuration
- Implement service registry pattern

### 2. Health Check Worker (Week 6-7)
- Async health probing for all services
- Configurable health check intervals
- Smart retry logic with exponential backoff
- Health status persistence

### 3. Health Summary Publisher (Week 7)
- Periodic health summaries via NATS
- Aggregated health metrics
- Federation-ready health broadcasts
- Real-time status updates

### 4. Federation Dashboard (Week 7-8)
- Service discovery registry
- Cross-hub health monitoring
- Visual health indicators
- Service dependency mapping

## Implementation Tasks

### Week 6: Service Model & Health Infrastructure

#### Task 6.1: Create Service Model
- [ ] Create `hub/backend/app/models/service.py`
- [ ] Add Service model with health fields
- [ ] Create migration for services table
- [ ] Add relationship to Project model

#### Task 6.2: Health Check Infrastructure
- [ ] Create `hub/backend/app/services/health_service.py`
- [ ] Implement health probe methods (HTTP, TCP, Redis, PostgreSQL)
- [ ] Add configurable timeout and retry logic
- [ ] Create health status enum and transitions

#### Task 6.3: Service Registration
- [ ] Auto-register services on project start
- [ ] Update OrchestrationService to track services
- [ ] Add service lifecycle events
- [ ] Implement service deregistration on stop

### Week 7: Health Monitoring & Publishing

#### Task 7.1: Health Check Worker
- [ ] Create `hub/backend/app/workers/health_worker.py`
- [ ] Implement async health check loop
- [ ] Add intelligent scheduling (stagger checks)
- [ ] Store health history in database

#### Task 7.2: Health Summary Publisher
- [ ] Create health aggregation logic
- [ ] Implement NATS publisher for health summaries
- [ ] Add hub.global.health topic
- [ ] Include service metadata in summaries

#### Task 7.3: Health API Endpoints
- [ ] GET /api/services - List all services
- [ ] GET /api/services/{id}/health - Service health details
- [ ] GET /api/projects/{id}/health - Project health summary
- [ ] WebSocket /ws/health - Real-time health updates

### Week 8: Federation & Dashboard

#### Task 8.1: Service Discovery Registry
- [ ] Create `hub/backend/app/services/discovery_service.py`
- [ ] Implement service registration protocol
- [ ] Add service metadata and capabilities
- [ ] Create service query interface

#### Task 8.2: Federation Dashboard API
- [ ] GET /api/federation/hubs - List discovered hubs
- [ ] GET /api/federation/services - Global service registry
- [ ] POST /api/federation/register - Hub registration
- [ ] WebSocket /ws/federation - Federation events

#### Task 8.3: Health Monitoring UI
- [ ] Create ServiceHealthCard component
- [ ] Add real-time health indicators
- [ ] Implement service dependency graph
- [ ] Add health history charts

#### Task 8.4: Testing & Documentation
- [ ] Unit tests for health service
- [ ] Integration tests for health worker
- [ ] WebSocket health stream tests
- [ ] Update API documentation

## Technical Details

### Service Model Schema
```python
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String, nullable=False)  # postgres, redis, backend, frontend
    service_type = Column(String)  # database, cache, api, web

    # Health Configuration
    health_url = Column(String)  # HTTP health endpoint
    health_method = Column(String, default="http")  # http, tcp, exec
    health_interval = Column(Integer, default=30)  # seconds
    health_timeout = Column(Integer, default=5)  # seconds
    health_retries = Column(Integer, default=3)

    # Health Status
    health_status = Column(Enum("up", "down", "degraded", "unknown"))
    last_health_check = Column(DateTime)
    consecutive_failures = Column(Integer, default=0)
    health_details = Column(JSON)  # latency, errors, version, etc.

    # Service Info
    version = Column(String)
    port = Column(Integer)
    container_id = Column(String)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="services")
    health_history = relationship("HealthCheck", back_populates="service")
```

### Health Check Types

1. **HTTP Health Checks**
   - GET request to health endpoint
   - Check status code (200-299 = healthy)
   - Measure response time
   - Parse JSON response for details

2. **TCP Health Checks**
   - Attempt TCP connection
   - Check if port is listening
   - Measure connection time

3. **Database Health Checks**
   - PostgreSQL: pg_isready command
   - Redis: PING command
   - Check connection and response time

4. **Container Health Checks**
   - Docker/Dagger exec health commands
   - Check container status
   - Monitor resource usage

### Health Status Transitions
```
unknown -> up: First successful check
up -> degraded: Response time > threshold
up -> down: Check failures > retry limit
degraded -> up: Response time normal
degraded -> down: Check failures > retry limit
down -> up: Successful check
```

### NATS Event Topics
```
hub.{hub_id}.health.{service_name} - Individual service health
hub.{hub_id}.health.summary - Hub health summary
hub.global.health - Global health broadcast
hub.{hub_id}.service.registered - Service registration
hub.{hub_id}.service.deregistered - Service removal
```

### Health Summary Format
```json
{
  "hub_id": "hub-main",
  "timestamp": "2025-11-05T10:00:00Z",
  "overall_status": "healthy",
  "services": [
    {
      "name": "postgres",
      "type": "database",
      "status": "up",
      "latency_ms": 5,
      "version": "16.0",
      "uptime_seconds": 3600
    },
    {
      "name": "backend",
      "type": "api",
      "status": "up",
      "latency_ms": 12,
      "endpoints_healthy": 15,
      "endpoints_total": 15
    }
  ],
  "projects": [
    {
      "id": 1,
      "name": "commandcenter",
      "status": "running",
      "health": "healthy",
      "service_count": 4
    }
  ]
}
```

## Success Criteria

### Week 6
- [ ] Service model created and migrated
- [ ] Health check infrastructure operational
- [ ] Services auto-registered on project start
- [ ] Basic health probing functional

### Week 7
- [ ] Health worker running continuously
- [ ] Health summaries published to NATS
- [ ] Health API endpoints functional
- [ ] WebSocket health updates streaming

### Week 8
- [ ] Service discovery registry complete
- [ ] Federation dashboard showing all hubs
- [ ] Real-time health monitoring UI
- [ ] All tests passing (>90% coverage)

## Dependencies

### Required Services
- NATS with JetStream (from Phase 1-4)
- PostgreSQL for persistence
- Redis for caching
- WebSocket support

### Python Packages
```
httpx>=0.24.0  # Async HTTP client
asyncio>=3.11  # Async/await support
nats-py>=2.6.0  # NATS client
```

### Frontend Components
- React 18 with TypeScript
- WebSocket client
- Chart.js for health graphs
- Tailwind CSS for styling

## Testing Strategy

### Unit Tests
- Service model CRUD operations
- Health check probe methods
- Health status transitions
- Service registration logic

### Integration Tests
- End-to-end health checking
- NATS event publishing
- WebSocket streaming
- Federation discovery

### Performance Tests
- Health check concurrency
- WebSocket connection limits
- Database query optimization
- NATS throughput

## Risk Mitigation

### Risk: Health checks overwhelm services
**Mitigation**: Implement rate limiting, staggered checks, and circuit breakers

### Risk: False positives/negatives
**Mitigation**: Multiple retry attempts, gradual degradation, historical analysis

### Risk: Network partitions
**Mitigation**: Local caching, graceful degradation, eventual consistency

### Risk: Resource exhaustion
**Mitigation**: Connection pooling, timeout enforcement, resource limits

## Next Steps

After Phase 6 completion:
1. Phase 7: Graph Service Implementation (Weeks 9-12)
2. Phase 8: VISLZR Frontend (Weeks 13-16)
3. Phase 9: Federation & Cross-Project Intelligence (Weeks 17-20)

## Notes

- Build on existing health.py router
- Leverage Dagger for container health
- Use existing NATS infrastructure from Phase 1-4
- Maintain backward compatibility with current Project model
- Consider prometheus metrics export for future
