"""
Celery configuration.
"""
import os

# Celery
CELERY_BROKER_URL = str(os.environ.get("CELERY_BROKER_URL", "redis://olivin-redis:6379/0"))
CELERY_RESULT_BACKEND = str(os.environ.get("CELERY_RESULT_BACKEND", "redis://olivin-redis:6379/0"))
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Warsaw"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Django celery results
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_CACHE_BACKEND = 'django-cache'
