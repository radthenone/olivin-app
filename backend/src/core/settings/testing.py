"""
Testing settings for Olivin project.
"""

import os

# --- Database: SQLite in-memory, bez migracji ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


class DisableMigrations:
    def __contains__(self, item: str) -> bool:
        return True

    def __getitem__(self, item: str) -> None:
        return None


MIGRATION_MODULES = DisableMigrations()

# --- Szybkie hashowanie haseł w testach ---
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# --- Email w pamięci ---
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# --- Cache ---
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# --- Celery ---
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# --- Storage ---
# Dla testów integracyjnych korzystamy z realnej konfiguracji z env/compose.
# Dla testów lokalnych bez infrastruktury zachowujemy bezpieczne fallbacki.
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# Pozwól nadpisać wartości przez env (docker-compose.test.yml). Domyślnie
# fallback do "testing"/"test-bucket" dla testów jednostkowych.
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "testing")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "testing")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME") or (
    os.environ.get("S3_BUCKETS_NAMES", "").split(",")[0].strip() or "test-bucket"
)
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
AWS_S3_USE_SSL = os.environ.get("AWS_S3_USE_SSL", "False").lower() == "true"

# --- DRF ---
REST_FRAMEWORK = {
    **globals().get("REST_FRAMEWORK", {}),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# --- Wyłączone settingsy w testach ---
INSTALLED_APPS = [
    app
    for app in globals().get("INSTALLED_APPS", [])
    if app
    not in (
        "debug_toolbar",
        "silk",
        "django_extensions",
    )
]
