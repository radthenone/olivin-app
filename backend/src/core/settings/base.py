"""
Base Django settings for Olivin project.

These settings are common to all environments.
"""

import os

from core.envs import load_valid_envs
from core.paths import SRC_DIR

load_valid_envs()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = str(os.environ.get("DJANGO_SECRET_KEY", "secret_key"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get("DJANGO_DEBUG", 1))

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [SRC_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# Django Superuser
DJANGO_SUPERUSER_USERNAME = str(os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin"))
DJANGO_SUPERUSER_EMAIL = str(
    os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
)
DJANGO_SUPERUSER_PASSWORD = str(os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123"))

# ISO standards
COUNTRIES_FIRST = ["PL", "US", "GB", "DE", "FR", "IT", "ES"]
PHONENUMBER_DEFAULT_REGION = "PL"
PHONENUMBER_DEFAULT_FORMAT = "INTERNATIONAL"