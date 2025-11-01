"""
Custom Prometheus metrics for Command Center
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from fastapi import FastAPI


# Custom metrics
repository_operations = Counter(
    "commandcenter_repository_operations_total",
    "Total repository operations",
    ["operation", "status"],
)

technology_operations = Counter(
    "commandcenter_technology_operations_total",
    "Total technology operations",
    ["operation", "status"],
)

research_task_duration = Histogram(
    "commandcenter_research_task_duration_seconds",
    "Research task execution duration",
    ["task_type"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600],
)

rag_operations = Counter(
    "commandcenter_rag_operations_total",
    "RAG system operations",
    ["operation", "status"],
)

rag_query_duration = Histogram(
    "commandcenter_rag_query_duration_seconds",
    "RAG query execution duration",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)

active_research_tasks = Gauge(
    "commandcenter_active_research_tasks", "Number of active research tasks"
)

database_connection_pool = Gauge(
    "commandcenter_db_connection_pool_size", "Database connection pool size", ["state"]
)

cache_operations = Counter(
    "commandcenter_cache_operations_total", "Cache operations", ["operation", "result"]
)

api_key_usage = Counter(
    "commandcenter_api_key_usage_total",
    "API key usage by service",
    ["service", "endpoint"],
)

# Batch operations metrics
batch_operations = Counter(
    "commandcenter_batch_operations_total",
    "Total batch operations by type and status",
    ["operation_type", "status"],
)

batch_operation_duration = Histogram(
    "commandcenter_batch_operation_duration_seconds",
    "Batch operation execution duration",
    ["operation_type"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600],
)

batch_items_processed = Counter(
    "commandcenter_batch_items_processed_total",
    "Total items processed in batch operations",
    ["operation_type", "status"],
)

batch_active_jobs = Gauge(
    "commandcenter_batch_active_jobs",
    "Number of active batch jobs",
)

# Job metrics
job_operations = Counter(
    "commandcenter_job_operations_total",
    "Total job operations by type and status",
    ["job_type", "status"],
)

job_duration = Histogram(
    "commandcenter_job_duration_seconds",
    "Job execution duration",
    ["job_type"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600, 7200],
)

job_queue_size = Gauge(
    "commandcenter_job_queue_size",
    "Number of jobs in queue by status",
    ["status"],
)

# Application info
app_info = Info("commandcenter_app", "Command Center application information")


def setup_custom_metrics(app: FastAPI):
    """
    Setup custom metrics for the application

    Args:
        app: FastAPI application instance
    """
    # Set application info
    app_info.info(
        {"version": app.version, "title": app.title, "environment": "production"}
    )

    # Initialize gauges
    active_research_tasks.set(0)
    database_connection_pool.labels(state="idle").set(0)
    database_connection_pool.labels(state="active").set(0)
    database_connection_pool.labels(state="total").set(0)


# Helper functions for metrics
def track_repository_operation(operation: str, success: bool = True):
    """Track repository operations"""
    status = "success" if success else "error"
    repository_operations.labels(operation=operation, status=status).inc()


def track_technology_operation(operation: str, success: bool = True):
    """Track technology operations"""
    status = "success" if success else "error"
    technology_operations.labels(operation=operation, status=status).inc()


def track_rag_operation(operation: str, success: bool = True):
    """Track RAG operations"""
    status = "success" if success else "error"
    rag_operations.labels(operation=operation, status=status).inc()


def track_cache_operation(operation: str, hit: bool = True):
    """Track cache operations"""
    result = "hit" if hit else "miss"
    cache_operations.labels(operation=operation, result=result).inc()


def track_api_key_usage(service: str, endpoint: str):
    """Track API key usage"""
    api_key_usage.labels(service=service, endpoint=endpoint).inc()


def track_batch_operation(operation_type: str, success: bool = True):
    """Track batch operations"""
    status = "success" if success else "error"
    batch_operations.labels(operation_type=operation_type, status=status).inc()


def track_batch_items(operation_type: str, count: int, success: bool = True):
    """Track batch items processed"""
    status = "success" if success else "error"
    batch_items_processed.labels(operation_type=operation_type, status=status).inc(
        count
    )


def track_job_operation(job_type: str, success: bool = True):
    """Track job operations"""
    status = "success" if success else "error"
    job_operations.labels(job_type=job_type, status=status).inc()


def update_job_queue_sizes(
    pending: int = 0, running: int = 0, completed: int = 0, failed: int = 0
):
    """Update job queue size gauges"""
    job_queue_size.labels(status="pending").set(pending)
    job_queue_size.labels(status="running").set(running)
    job_queue_size.labels(status="completed").set(completed)
    job_queue_size.labels(status="failed").set(failed)
