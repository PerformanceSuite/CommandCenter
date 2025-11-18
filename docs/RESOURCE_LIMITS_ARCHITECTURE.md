# Resource Limits Architecture

**Date**: 2025-11-17
**Status**: Recommended Approach
**Context**: Dagger SDK 0.19.4 doesn't expose resource limits API

---

## Problem Statement

The Dagger Python SDK (dagger-io 0.19.4) does not expose container resource limits (CPU, memory) in its public API. We have TODOs in the codebase for setting resource limits that cannot be implemented with the current API.

**Current Code (Not Possible)**:
```python
# backend/app/dagger_modules/commandcenter.py

container = (
    dag.container()
    .from_("postgres:16-alpine")
    # TODO: Resource limits not available in dagger-io 0.19.4
    # .with_cpu_limit(cpus=2.0)
    # .with_memory_limit(memory="2GB")
)
```

---

## Recommended Solution: External Resource Enforcement

**✅ Best Practice**: Enforce resource limits externally at the Dagger Engine level, not within individual container definitions.

### Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Host/Orchestrator Level                   │
│  - Docker daemon limits (--cpus, --memory)          │
│  - Kubernetes resource quotas (requests/limits)     │
│  - VM/EC2 instance sizing                           │
└─────────────────────────────────────────────────────┘
                      ↓ constrains
┌─────────────────────────────────────────────────────┐
│ Layer 2: Dagger Engine Container                   │
│  - docker run dagger-engine --cpus=4 --memory=8g    │
│  - Engine enforces limits on all child containers   │
└─────────────────────────────────────────────────────┘
                      ↓ orchestrates
┌─────────────────────────────────────────────────────┐
│ Layer 3: Application Containers (via Dagger SDK)   │
│  - postgres, redis, backend, frontend containers    │
│  - Inherit limits from Dagger Engine                │
│  - No per-container limits needed in code           │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Options

### Option 1: Docker Daemon Limits (Development)

**For local development**, limit the Dagger Engine container:

```bash
# docker-compose.yml or manual run
docker run -d \
  --name dagger-engine \
  --cpus=4 \
  --memory=8g \
  --memory-swap=8g \
  --privileged \
  -v dagger-engine:/var/lib/dagger \
  registry.dagger.io/engine:v0.19.4
```

**Pros**:
- Simple, works immediately
- No code changes needed
- Easy to adjust per-environment

**Cons**:
- Shared pool (all CommandCenter containers use same limits)
- Less granular control

---

### Option 2: Kubernetes Resource Quotas (Production)

**For production/staging**, use Kubernetes resource management:

```yaml
# dagger-engine-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dagger-engine
spec:
  template:
    spec:
      containers:
      - name: dagger-engine
        image: registry.dagger.io/engine:v0.19.4
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
```

**Additional**: Per-namespace quotas for multi-tenant isolation:

```yaml
# commandcenter-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: commandcenter-quota
  namespace: commandcenter
spec:
  hard:
    requests.cpu: "8"
    requests.memory: "16Gi"
    limits.cpu: "16"
    limits.memory: "32Gi"
```

**Pros**:
- Industry standard for production
- Fine-grained control (requests vs limits)
- Multi-tenant safe (namespace isolation)
- Auto-scaling support

**Cons**:
- Requires Kubernetes infrastructure
- More complex setup

---

### Option 3: cgroups v2 (Host-Level)

**For bare-metal/VM deployments**, use cgroups directly:

```bash
# Create cgroup for Dagger Engine
sudo cgcreate -g cpu,memory:/dagger-engine

# Set limits
echo "400000" > /sys/fs/cgroup/dagger-engine/cpu.max  # 4 CPUs
echo "8G" > /sys/fs/cgroup/dagger-engine/memory.max   # 8GB RAM

# Run Dagger Engine in cgroup
sudo cgexec -g cpu,memory:dagger-engine docker run ...
```

**Pros**:
- Kernel-level enforcement
- No orchestrator needed
- Fine-grained control

**Cons**:
- Requires root/sudo
- Manual setup
- Less portable

---

## Recommended Configuration by Environment

| Environment | Method | CPU Limit | Memory Limit | Notes |
|-------------|--------|-----------|--------------|-------|
| Development (Docker Desktop) | Docker daemon flags | 4 CPUs | 8GB | Simple, adjustable |
| CI/CD | Docker daemon flags | 2 CPUs | 4GB | Fast, isolated per-job |
| Staging (Kubernetes) | Pod resource limits | 4 CPUs | 8GB | Production-like |
| Production (Kubernetes) | Pod resource limits + Quotas | 8 CPUs | 16GB | Auto-scaling enabled |

---

## Why External > Internal

### 1. **Separation of Concerns**
- **Application code** (Python) defines WHAT containers to run
- **Infrastructure** (Docker/K8s) defines HOW MUCH resources they get
- Clean boundary, easier to adjust without code changes

### 2. **Environment Parity**
- Same code runs in dev, staging, prod
- Only infrastructure config changes
- No "if production then..." conditionals

### 3. **SDK Limitations Are Irrelevant**
- Dagger SDK updates won't break our approach
- If `.with_cpu_limit()` is added later, we don't need it
- External limits always work

### 4. **Multi-Tenant Safety**
- Kubernetes namespaces + quotas = true isolation
- One tenant can't exhaust resources for others
- Aligns with CommandCenter's "one instance per project" model

---

## Action Plan

### Immediate (Phase 7)
1. ✅ **Document** this architecture (this file)
2. ✅ **Remove misleading TODOs** from `commandcenter.py`
3. ✅ **Update comments** to reference external limits

```python
# backend/app/dagger_modules/commandcenter.py

container = (
    dag.container()
    .from_("postgres:16-alpine")
    # Resource limits enforced externally via Dagger Engine container.
    # See docs/RESOURCE_LIMITS_ARCHITECTURE.md for details.
)
```

### Near-Term (Hub Production Hardening)
4. Add Dagger Engine resource limits to Hub docker-compose:
   ```yaml
   # hub/docker-compose.yml
   services:
     dagger-engine:
       image: registry.dagger.io/engine:v0.19.4
       deploy:
         resources:
           limits:
             cpus: '4'
             memory: 8G
   ```

### Future (Production Deployment)
5. Create Kubernetes manifests with proper resource quotas
6. Set up monitoring/alerting for resource usage
7. Implement auto-scaling based on load

---

## Verification

To verify resource limits are being enforced:

```bash
# Check Dagger Engine container limits
docker inspect dagger-engine | jq '.[0].HostConfig | {CpuQuota, CpuPeriod, Memory}'

# Monitor actual usage
docker stats dagger-engine

# In Kubernetes
kubectl describe pod dagger-engine-xyz
kubectl top pod dagger-engine-xyz
```

---

## References

- [Dagger Engine Architecture](https://docs.dagger.io/architecture/)
- [Docker Resource Constraints](https://docs.docker.com/config/containers/resource_constraints/)
- [Kubernetes Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)
- [cgroups v2 Documentation](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)

---

## Conclusion

**External resource limits are not a workaround—they're the correct architecture.**

By enforcing limits at the Dagger Engine level (or higher), we achieve:
- ✅ Environment-agnostic code
- ✅ SDK version independence
- ✅ Production-grade multi-tenant isolation
- ✅ Simple, maintainable infrastructure

The TODOs in our code should be removed/updated to reflect this approach.
