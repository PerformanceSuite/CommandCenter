"""
Custom Prometheus metrics for Command Center
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from fastapi import FastAPI


# Custom metrics
repository_operations = Counter(
    'commandcenter_repository_operations_total',
    'Total repository operations',
    ['operation', 'status']
)

technology_operations = Counter(
    'commandcenter_technology_operations_total',
    'Total technology operations',
    ['operation', 'status']
)

research_task_duration = Histogram(
    'commandcenter_research_task_duration_seconds',
    'Research task execution duration',
    ['task_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
)

rag_operations = Counter(
    'commandcenter_rag_operations_total',
    'RAG system operations',
    ['operation', 'status']
)

rag_query_duration = Histogram(
    'commandcenter_rag_query_duration_seconds',
    'RAG query execution duration',
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
)

active_research_tasks = Gauge(
    'commandcenter_active_research_tasks',
    'Number of active research tasks'
)

database_connection_pool = Gauge(
    'commandcenter_db_connection_pool_size',
    'Database connection pool size',
    ['state']
)

cache_operations = Counter(
    'commandcenter_cache_operations_total',
    'Cache operations',
    ['operation', 'result']
)

api_key_usage = Counter(
    'commandcenter_api_key_usage_total',
    'API key usage by service',
    ['service', 'endpoint']
)

# Application info
app_info = Info(
    'commandcenter_app',
    'Command Center application information'
)


def setup_custom_metrics(app: FastAPI):
    """
    Setup custom metrics for the application

    Args:
        app: FastAPI application instance
    """
    # Set application info
    app_info.info({
        'version': app.version,
        'title': app.title,
        'environment': 'production'
    })

    # Initialize gauges
    active_research_tasks.set(0)
    database_connection_pool.labels(state='idle').set(0)
    database_connection_pool.labels(state='active').set(0)
    database_connection_pool.labels(state='total').set(0)


# Helper functions for metrics
def track_repository_operation(operation: str, success: bool = True):
    """Track repository operations"""
    status = 'success' if success else 'error'
    repository_operations.labels(operation=operation, status=status).inc()


def track_technology_operation(operation: str, success: bool = True):
    """Track technology operations"""
    status = 'success' if success else 'error'
    technology_operations.labels(operation=operation, status=status).inc()


def track_rag_operation(operation: str, success: bool = True):
    """Track RAG operations"""
    status = 'success' if success else 'error'
    rag_operations.labels(operation=operation, status=status).inc()


def track_cache_operation(operation: str, hit: bool = True):
    """Track cache operations"""
    result = 'hit' if hit else 'miss'
    cache_operations.labels(operation=operation, result=result).inc()


def track_api_key_usage(service: str, endpoint: str):
    """Track API key usage"""
    api_key_usage.labels(service=service, endpoint=endpoint).inc()
