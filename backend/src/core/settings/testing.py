"""
Testing settings for Olivin project.
"""

import os

# --- Database: SQLite in-memory, bez migracji ---
# `TEST_DATABASE=postgres` zostawia Postgresa z `components/database.py` —
# dla testów blokad wierszy, których SQLite nie odtworzy (`select_for_update`
# jest tam bez skutku, a zapis blokuje całą bazę).
if os.environ.get("TEST_DATABASE") != "postgres":
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
# `ACTUAL_EMAIL_BACKEND` to backend, którego `send_email_payloads_task`
# używa naprawdę (`components/email.py`) — bez nadpisania zadanie łączyłoby
# się z prawdziwym SMTP nawet w testach.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
ACTUAL_EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# --- Kurs walut bez sieci ---
EXCHANGE_RATE_PROVIDER = "core.integrations.exchange_rate.fake.FakeExchangeRateProvider"

# --- Push donikąd w testach (nadpisywany atrapą w testach push) ---
PUSH_PROVIDER = "core.integrations.push.noop.NoopPushProvider"

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
# Testy integracyjne korzystają z realnego S3 z compose; testy jednostkowe
# z mocka w `tests/conftest.py`. Nazwy bucketów biorą się z ADR 0025
# (`core/storage/buckets.py`), więc nie ma ich tutaj.
#
# Endpoint celowo NIE pochodzi z `AWS_S3_ENDPOINT_URL`: ta zmienna na maszynie
# dewelopera wskazuje hosta z compose (Taskfile dotenv), a pola plików
# (`FileField(storage=...)`) wiążą magazyn przy imporcie — wyciekły adres
# kończyłby w mocku prawdziwym połączeniem. Jednostki zawsze widzą `None`
# (moto), integracja w dockerze dostaje adres przez `TEST_S3_ENDPOINT_URL`
# z `docker-compose.test.yml`.
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "testing")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "testing")
AWS_S3_ENDPOINT_URL = os.environ.get("TEST_S3_ENDPOINT_URL")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
AWS_S3_ADDRESSING_STYLE = os.environ.get("AWS_S3_ADDRESSING_STYLE", "path")
AWS_S3_URL_PROTOCOL = os.environ.get("AWS_S3_URL_PROTOCOL", "http:")
AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN", "localhost")
S3_PUBLIC_BASE_URL = os.environ.get("S3_PUBLIC_BASE_URL", "")

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
