"""Celery application configuration for Hub background tasks"""
import os
from celery import Celery

# Get Redis URL from environment (default to localhost for development)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'hub',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.orchestration']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

# Optional: Configure task routes
celery_app.conf.task_routes = {
    'app.tasks.orchestration.*': {'queue': 'orchestration'},
}
