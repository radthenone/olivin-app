"""
Database configuration.
"""
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": str(os.environ.get("POSTGRES_DB", "postgres")),
        "USER": str(os.environ.get("POSTGRES_USER", "postgres")),
        "PASSWORD": str(os.environ.get("POSTGRES_PASSWORD", "postgres")),
        "HOST": str(os.environ.get("POSTGRES_HOST", "localhost")),
        "PORT": int(os.environ.get("POSTGRES_PORT", 5433)),
    }
}
