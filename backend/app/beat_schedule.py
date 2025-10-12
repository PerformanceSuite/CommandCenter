"""
Celery Beat schedule configuration for periodic tasks.

This module defines the schedule for recurring tasks that should be
executed automatically by Celery Beat.
"""

from celery.schedules import crontab

# Beat schedule for periodic tasks
beat_schedule = {
    # Schedule dispatcher - runs every minute to check for due schedules
    "dispatch-due-schedules": {
        "task": "app.tasks.scheduled_tasks.dispatch_due_schedules",
        "schedule": 60.0,  # Every 60 seconds
        "options": {
            "expires": 50,  # Task expires after 50 seconds (before next run)
        },
    },
    # Schedule cleanup - runs daily at 2 AM UTC to disable expired schedules
    "cleanup-expired-schedules": {
        "task": "app.tasks.scheduled_tasks.cleanup_expired_schedules",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2:00 AM UTC
        "options": {
            "expires": 3600,  # Task expires after 1 hour
        },
    },
    # Schedule health monitoring - runs every 5 minutes
    "monitor-schedule-health": {
        "task": "app.tasks.scheduled_tasks.monitor_schedule_health",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
        "options": {
            "expires": 240,  # Task expires after 4 minutes
        },
    },
}
