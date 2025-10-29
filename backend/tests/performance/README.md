# Performance Tests

## Overview

Performance tests establish baseline metrics and detect performance regressions in API endpoints, database queries, and RAG search.

## Test Structure

### N+1 Query Detection (`test_n_plus_one_queries.py`)

**Goal:** Prevent N+1 query anti-pattern.

**Tests (5 total):**
- Technologies list uses joins (no N+1) (1)
- Technology detail loads relationships efficiently (1)
- Research tasks list uses joins (1)
- Repositories list with technologies (many-to-many) (1)
- Knowledge base query (1)

**N+1 Pattern:**
```python
# ❌ N+1 PROBLEM
technologies = db.query(Technology).all()  # 1 query
for tech in technologies:
    tech.repositories  # N queries (one per technology)
```

**Solution:**
```python
# ✅ FIX with eager loading
technologies = db.query(Technology).options(
    joinedload(Technology.repositories)
).all()  # 1-2 queries total
```

### API Endpoint Benchmarks (`test_api_benchmarks.py`)

**Goal:** Establish response time baselines.

**Tests (3 total):**
- Technology list < 300ms (1)
- Repository detail < 500ms (1)
- Research list with pagination < 300ms (1)

**Thresholds:**
- **List endpoints**: 300ms
- **Detail endpoints**: 500ms
- **Bulk operations**: 1500ms
- **RAG search**: 1500ms

### Database Stress Tests (`test_database_stress.py`)

**Goal:** Validate database performance under load.

**Tests (3 total):**
- Bulk create 100 technologies < 1500ms (1)
- 10 concurrent read queries < 1000ms (1)
- 50 rapid connections (connection pool) (1)

**Stress Levels:**
- **Bulk create**: 100 records
- **Concurrent reads**: 10 simultaneous
- **Connection pool**: 50 rapid connections

### RAG Performance (`test_rag_performance.py`)

**Goal:** Validate knowledge base search performance.

**Tests (2 total):**
- Single RAG query < 1500ms (1)
- 5 concurrent RAG queries < 3000ms (1)

**RAG Components:**
- Vector similarity search (pgvector)
- Keyword search
- Reciprocal Rank Fusion
- HuggingFace embeddings

## Running Performance Tests

**All performance tests:**
```bash
cd backend
pytest tests/performance/ -v -s
```

**Specific category:**
```bash
pytest tests/performance/test_n_plus_one_queries.py -v
```

**With performance output:**
```bash
pytest tests/performance/ -v -s --durations=10
```

**In Docker:**
```bash
make test-performance
```

## Test Count

**Total: 13 tests**
- N+1 query detection: 5 tests
- API benchmarks: 3 tests
- Database stress: 3 tests
- RAG performance: 2 tests

## Performance Baselines

### API Response Times (Target)

| Endpoint | Threshold | Notes |
|----------|-----------|-------|
| GET /technologies | 300ms | List with filtering |
| GET /technologies/{id} | 500ms | Detail with relationships |
| GET /repositories | 300ms | List with pagination |
| GET /research | 300ms | List with filtering |
| POST /knowledge/query | 1500ms | RAG search |

### Database Operations (Target)

| Operation | Threshold | Scale |
|-----------|-----------|-------|
| Bulk create | 1500ms | 100 records |
| Concurrent reads | 1000ms | 10 simultaneous |
| Connection pool | No errors | 50 connections |

### Query Efficiency

| Query Type | Max Queries | Notes |
|------------|-------------|-------|
| List endpoint | ≤3 | Main query + joins |
| Detail endpoint | ≤2 | Record + relationships |
| Many-to-many | ≤3 | Association + both tables |

## Performance Optimization Tips

### 1. Database Indexing

**Index foreign keys:**
```sql
CREATE INDEX idx_technologies_project_id ON technologies(project_id);
CREATE INDEX idx_repositories_project_id ON repositories(project_id);
```

**Index frequently filtered columns:**
```sql
CREATE INDEX idx_technologies_domain ON technologies(domain);
CREATE INDEX idx_research_status ON research_tasks(status);
```

### 2. Eager Loading Relationships

**Use `joinedload` for one-to-many:**
```python
technologies = session.query(Technology).options(
    joinedload(Technology.repositories)
).all()
```

**Use `selectinload` for collections:**
```python
repositories = session.query(Repository).options(
    selectinload(Repository.technologies)
).all()
```

### 3. Pagination

**Always paginate list endpoints:**
```python
@app.get("/technologies")
async def list_technologies(page: int = 1, per_page: int = 50):
    offset = (page - 1) * per_page
    technologies = session.query(Technology).offset(offset).limit(per_page).all()
    return technologies
```

### 4. Query Result Caching

**Cache expensive queries:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_technology_stats(project_id: int):
    return session.query(Technology).filter(
        Technology.project_id == project_id
    ).count()
```

### 5. Database Connection Pooling

**Configure pool size:**
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Concurrent connections
    max_overflow=10,  # Extra connections under load
    pool_pre_ping=True  # Verify connections
)
```

## Monitoring Performance

### Using pytest-benchmark

```bash
pip install pytest-benchmark
```

```python
def test_technology_list_benchmark(benchmark, client, auth_headers):
    def run_query():
        return client.get("/api/v1/technologies", headers=auth_headers)

    result = benchmark(run_query)
    assert result.status_code == 200
```

### Using query counter

```python
def test_check_queries(query_counter, client, auth_headers):
    query_counter.clear()

    response = client.get("/api/v1/technologies", headers=auth_headers)

    print(f"Executed {len(query_counter)} queries:")
    for query in query_counter:
        print(f"  - {query['statement'][:100]}...")
```

### Profiling Slow Endpoints

```python
import cProfile
import pstats

def test_profile_endpoint(client, auth_headers):
    profiler = cProfile.Profile()
    profiler.enable()

    response = client.get("/api/v1/technologies", headers=auth_headers)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 slowest functions
```

## Common Performance Issues

### Issue 1: N+1 Queries

**Symptom:** Endpoint slow with many records
**Detection:** Query counter shows N queries
**Fix:** Add eager loading

### Issue 2: Missing Indexes

**Symptom:** Slow list queries with filtering
**Detection:** Database EXPLAIN shows sequential scans
**Fix:** Add indexes on filtered columns

### Issue 3: Large Result Sets

**Symptom:** Endpoint times out with full dataset
**Detection:** No pagination, returns 1000+ records
**Fix:** Add pagination

### Issue 4: Slow RAG Queries

**Symptom:** Knowledge base search takes >2s
**Detection:** Embedding generation or vector search slow
**Fix:** Cache embeddings, optimize pgvector index

## Performance Regression Detection

**Run performance tests in CI:**
```yaml
# .github/workflows/performance.yml
- name: Run performance tests
  run: pytest tests/performance/ -v --benchmark-autosave

- name: Compare with baseline
  run: pytest-benchmark compare
```

**Fail CI if regression:**
```python
def test_no_regression(benchmark_results):
    baseline = load_baseline()
    current = benchmark_results

    for endpoint, time in current.items():
        assert time < baseline[endpoint] * 1.2, (
            f"{endpoint} regressed by >20%"
        )
```

## Next Steps

1. **Establish production baselines:**
   - Run tests against production-like data volumes
   - Document actual performance metrics
   - Set realistic thresholds

2. **Add more coverage:**
   - File upload performance
   - Bulk delete operations
   - Complex aggregation queries
   - WebSocket connection stress

3. **Optimize slow endpoints:**
   - Profile with cProfile
   - Add database indexes
   - Implement caching
   - Optimize queries

4. **Continuous monitoring:**
   - Add performance tests to CI
   - Track metrics over time
   - Alert on regressions
