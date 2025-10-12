"""
Celery configuration and task initialization for CommandCenter.

This module sets up the Celery app for async job processing including:
- Analysis tasks
- Export tasks
- Webhook delivery tasks
- Scheduled tasks (via Celery Beat)
"""

import os
from celery import Celery
from kombu import Queue, Exchange

# Get configuration from environment
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "commandcenter",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.job_tasks",
        "app.tasks.analysis_tasks",
        "app.tasks.export_tasks",
        "app.tasks.webhook_tasks",
        "app.tasks.scheduled_tasks",
    ],
)

# Configure Celery
celery_app.conf.update(
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_default_queue="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("analysis", Exchange("analysis"), routing_key="analysis"),
        Queue("export", Exchange("export"), routing_key="export"),
        Queue("webhooks", Exchange("webhooks"), routing_key="webhooks"),
    ),

    # Task priorities
    task_queue_max_priority=10,
    task_default_priority=5,

    # Task results
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Store additional metadata

    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit

    # Task retries
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,

    # Beat schedule (for scheduled tasks)
    beat_scheduler="redbeat.RedBeatScheduler",  # Use Redis-backed scheduler
    redbeat_redis_url=CELERY_BROKER_URL,
)

# Import and set beat schedule
try:
    from app.beat_schedule import beat_schedule
    celery_app.conf.beat_schedule = beat_schedule
except ImportError:
    print("Warning: Could not import beat_schedule")
    celery_app.conf.beat_schedule = {}

# Task routing rules
celery_app.conf.task_routes = {
    "app.tasks.analysis_tasks.*": {"queue": "analysis", "priority": 8},
    "app.tasks.export_tasks.*": {"queue": "export", "priority": 5},
    "app.tasks.webhook_tasks.*": {"queue": "webhooks", "priority": 6},
    "app.tasks.scheduled_tasks.*": {"queue": "default", "priority": 7},
}


@celery_app.task(bind=True)
def debug_task(self):
    """
    Debug task for testing Celery setup.

    Usage:
        from app.tasks import debug_task
        result = debug_task.delay()
    """
    return f"Request: {self.request!r}"


# Import task modules to register them with Celery
# Note: Import after celery_app is configured to avoid circular imports
try:
    from app.tasks import job_tasks  # noqa: F401
    from app.tasks import analysis_tasks  # noqa: F401
    from app.tasks import export_tasks  # noqa: F401
    from app.tasks import webhook_tasks  # noqa: F401
    from app.tasks import scheduled_tasks  # noqa: F401
except ImportError as e:
    # Tasks may not exist yet during initial setup
    print(f"Warning: Could not import task modules: {e}")


__all__ = ["celery_app", "debug_task"]
