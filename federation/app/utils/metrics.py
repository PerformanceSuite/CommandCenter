"""
Prometheus metrics for Federation Service

Tracks:
- Heartbeat message processing (rate, errors, latency)
- Project catalog state (ONLINE/OFFLINE counts)
- Stale checker operations (marked offline count)
- NATS message processing (duration, errors)
"""

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram, Info

# Heartbeat message metrics
heartbeat_messages_total = Counter(
    "federation_heartbeat_messages_total",
    "Total heartbeat messages received from NATS",
    ["project_slug", "status"],  # status: success, error, unknown_project
)

heartbeat_processing_duration = Histogram(
    "federation_heartbeat_processing_duration_seconds",
    "Heartbeat message processing duration",
    ["project_slug"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Project catalog metrics
project_catalog_total = Gauge(
    "federation_project_catalog_total",
    "Number of projects in catalog by status",
    ["status"],  # status: ONLINE, OFFLINE
)

project_catalog_last_updated = Gauge(
    "federation_project_catalog_last_updated_timestamp",
    "Last time project catalog was updated",
    ["project_slug"],
)

# Stale checker metrics
stale_checker_runs_total = Counter(
    "federation_stale_checker_runs_total",
    "Total stale checker runs",
    ["status"],  # status: success, error
)

stale_checker_projects_marked_offline = Counter(
    "federation_stale_checker_projects_marked_offline_total",
    "Total projects marked offline by stale checker",
)

stale_checker_duration = Histogram(
    "federation_stale_checker_duration_seconds",
    "Stale checker execution duration",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# NATS connection metrics
nats_connection_status = Gauge(
    "federation_nats_connection_status",
    "NATS connection status (1=connected, 0=disconnected)",
)

nats_messages_total = Counter(
    "federation_nats_messages_total",
    "Total NATS messages by subject",
    ["subject", "status"],  # status: success, error
)

nats_message_processing_duration = Histogram(
    "federation_nats_message_processing_duration_seconds",
    "NATS message processing duration by subject",
    ["subject"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Application info
federation_info = Info("federation_service", "Federation Service information")


def setup_metrics(app: FastAPI):
    """
    Setup Prometheus metrics for the Federation Service

    Args:
        app: FastAPI application instance
    """
    # Set application info
    federation_info.info({
        "version": app.version,
        "title": app.title,
        "environment": "production",
    })

    # Initialize gauges
    project_catalog_total.labels(status="ONLINE").set(0)
    project_catalog_total.labels(status="OFFLINE").set(0)
    nats_connection_status.set(0)


# Helper functions for tracking metrics

def track_heartbeat_message(project_slug: str, success: bool = True, unknown: bool = False):
    """Track heartbeat message processing"""
    if unknown:
        status = "unknown_project"
    elif success:
        status = "success"
    else:
        status = "error"

    heartbeat_messages_total.labels(project_slug=project_slug, status=status).inc()


def track_stale_checker_run(success: bool = True, projects_marked_offline: int = 0):
    """Track stale checker execution"""
    status = "success" if success else "error"
    stale_checker_runs_total.labels(status=status).inc()

    if projects_marked_offline > 0:
        stale_checker_projects_marked_offline.inc(projects_marked_offline)


def update_project_catalog_counts(online_count: int, offline_count: int):
    """Update project catalog gauge counts"""
    project_catalog_total.labels(status="ONLINE").set(online_count)
    project_catalog_total.labels(status="OFFLINE").set(offline_count)


def update_nats_connection_status(connected: bool):
    """Update NATS connection status gauge"""
    nats_connection_status.set(1 if connected else 0)


def track_nats_message(subject: str, success: bool = True):
    """Track NATS message by subject"""
    status = "success" if success else "error"
    nats_messages_total.labels(subject=subject, status=status).inc()
