"""
Celery configuration.
"""

import os
from datetime import timedelta

from celery.schedules import crontab, schedule

# Celery
CELERY_BROKER_URL = str(
    os.environ.get("CELERY_BROKER_URL", "redis://olivin-redis:6379/0")
)
CELERY_RESULT_BACKEND = str(
    os.environ.get("CELERY_RESULT_BACKEND", "redis://olivin-redis:6379/0")
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Warsaw"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Django celery results
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_SERIALIZER = "json"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_IMPORTS = (
    "core.services.mail.tasks",
    "core.services.allauth.tasks",
)

CELERY_BEAT_SCHEDULE = {
    "cleanup-stale-unverified-users": {
        "task": "core.services.allauth.tasks.cleanup_stale_unverified_users",
        "schedule": schedule(run_every=timedelta(days=1)), # 1 day
    },
}
