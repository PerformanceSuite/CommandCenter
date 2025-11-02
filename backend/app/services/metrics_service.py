"""
Prometheus metrics service for monitoring GitHub operations
"""

from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# GitHub API metrics
github_api_requests_total = Counter(
    "github_api_requests_total",
    "Total number of GitHub API requests",
    ["endpoint", "method", "status"],
)

github_api_request_duration_seconds = Histogram(
    "github_api_request_duration_seconds",
    "GitHub API request duration in seconds",
    ["endpoint", "method"],
)

github_api_rate_limit_remaining = Gauge(
    "github_api_rate_limit_remaining",
    "GitHub API rate limit remaining",
    ["resource_type"],
)

github_api_rate_limit_limit = Gauge(
    "github_api_rate_limit_limit",
    "GitHub API rate limit total",
    ["resource_type"],
)

github_api_errors_total = Counter(
    "github_api_errors_total",
    "Total number of GitHub API errors",
    ["endpoint", "error_type"],
)

# Webhook metrics
webhook_events_received_total = Counter(
    "webhook_events_received_total",
    "Total number of webhook events received",
    ["event_type", "repository"],
)

webhook_events_processed_total = Counter(
    "webhook_events_processed_total",
    "Total number of webhook events processed successfully",
    ["event_type"],
)

webhook_events_failed_total = Counter(
    "webhook_events_failed_total",
    "Total number of webhook events that failed processing",
    ["event_type", "error_type"],
)

webhook_processing_duration_seconds = Histogram(
    "webhook_processing_duration_seconds",
    "Webhook event processing duration in seconds",
    ["event_type"],
)

# Cache metrics
cache_hits_total = Counter("cache_hits_total", "Total number of cache hits", ["cache_type"])

cache_misses_total = Counter("cache_misses_total", "Total number of cache misses", ["cache_type"])

# Repository sync metrics
repository_sync_total = Counter(
    "repository_sync_total",
    "Total number of repository syncs",
    ["repository", "status"],
)

repository_sync_duration_seconds = Histogram(
    "repository_sync_duration_seconds",
    "Repository sync duration in seconds",
    ["repository"],
)


class MetricsService:
    """Service for recording application metrics"""

    @staticmethod
    def record_github_api_request(endpoint: str, method: str, status: str, duration: float):
        """
        Record a GitHub API request

        Args:
            endpoint: API endpoint called
            method: HTTP method
            status: Response status (success/error)
            duration: Request duration in seconds
        """
        github_api_requests_total.labels(endpoint=endpoint, method=method, status=status).inc()

        github_api_request_duration_seconds.labels(endpoint=endpoint, method=method).observe(
            duration
        )

    @staticmethod
    def record_github_api_error(endpoint: str, error_type: str):
        """
        Record a GitHub API error

        Args:
            endpoint: API endpoint that failed
            error_type: Type of error
        """
        github_api_errors_total.labels(endpoint=endpoint, error_type=error_type).inc()

    @staticmethod
    def update_rate_limit_metrics(resource_type: str, remaining: int, limit: int):
        """
        Update rate limit metrics

        Args:
            resource_type: Type of resource (core, search, graphql)
            remaining: Remaining requests
            limit: Total limit
        """
        github_api_rate_limit_remaining.labels(resource_type=resource_type).set(remaining)
        github_api_rate_limit_limit.labels(resource_type=resource_type).set(limit)

    @staticmethod
    def record_webhook_event(event_type: str, repository: str):
        """
        Record a received webhook event

        Args:
            event_type: Type of webhook event
            repository: Repository full name
        """
        webhook_events_received_total.labels(event_type=event_type, repository=repository).inc()

    @staticmethod
    def record_webhook_processed(event_type: str, duration: float):
        """
        Record a successfully processed webhook event

        Args:
            event_type: Type of webhook event
            duration: Processing duration in seconds
        """
        webhook_events_processed_total.labels(event_type=event_type).inc()
        webhook_processing_duration_seconds.labels(event_type=event_type).observe(duration)

    @staticmethod
    def record_webhook_failed(event_type: str, error_type: str):
        """
        Record a failed webhook event

        Args:
            event_type: Type of webhook event
            error_type: Type of error
        """
        webhook_events_failed_total.labels(event_type=event_type, error_type=error_type).inc()

    @staticmethod
    def record_cache_hit(cache_type: str = "github"):
        """
        Record a cache hit

        Args:
            cache_type: Type of cache
        """
        cache_hits_total.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_cache_miss(cache_type: str = "github"):
        """
        Record a cache miss

        Args:
            cache_type: Type of cache
        """
        cache_misses_total.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_repository_sync(repository: str, status: str, duration: float):
        """
        Record a repository sync

        Args:
            repository: Repository full name
            status: Sync status (success/error)
            duration: Sync duration in seconds
        """
        repository_sync_total.labels(repository=repository, status=status).inc()
        repository_sync_duration_seconds.labels(repository=repository).observe(duration)


def track_github_api_call(endpoint: str, method: str = "GET"):
    """
    Decorator to track GitHub API calls with metrics

    Args:
        endpoint: API endpoint being called
        method: HTTP method

    Returns:
        Decorated function
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            error_type = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                MetricsService.record_github_api_error(endpoint, error_type)
                raise
            finally:
                duration = time.time() - start_time
                MetricsService.record_github_api_request(endpoint, method, status, duration)

        return wrapper

    return decorator


# Global metrics service instance
metrics_service = MetricsService()
