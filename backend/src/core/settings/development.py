import os

from pack_logger import configure_logging

from core.settings.components.apps import (
    APPLICATION_APPS,
    DJANGO_APPS,
    THIRD_PARTY_APPS,
)
from core.settings.components.auth import REST_FRAMEWORK
from core.settings.components.middleware import MIDDLEWARE as BASE_MIDDLEWARE

"""
Development settings for Olivin project.
"""

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "10.0.2.2",  # Android emulator host
    "*",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGGING = configure_logging(debug=DEBUG, app_name="olivin")

PACK_LOGGER_EXCLUDED_PATHS = [
    "/admin/",
    "/favicon.ico",
    "/health/",
    "/api/health/",
    "/api/schema/",
    "/api/schema/redoc/",
    "/api/docs/",
    "/api/redoc/",
    "/_allauth/openapi.json",
    "/_allauth/docs/",
    "/_allauth/redoc/",
    "/silk/",
    "/silk/*",
]

DEVELOPMENT_APPS = [
    "drf_spectacular",
    "django_extensions",
    "debug_toolbar",
    "silk",
]

DEVELOPMENT_MIDDLEWARE = [
    "pack_logger.middleware.ApiLoggingMiddleware",
    "silk.middleware.SilkyMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + DEVELOPMENT_APPS + APPLICATION_APPS

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

MIDDLEWARE = BASE_MIDDLEWARE + DEVELOPMENT_MIDDLEWARE

SPECTACULAR_SETTINGS = {
    "TITLE": "olivin-app",
    "DESCRIPTION": "API documentation",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "CAMELIZE_NAMES": False,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
        # "core.utils.allauth_schema_hook.inject_allauth_schema",
    ],
}

HEADLESS_SERVE_SPECIFICATION = True


def silky_intercept_func(request):
    return not any(request.path.startswith(path) for path in PACK_LOGGER_EXCLUDED_PATHS)


SILKY_INTERCEPT_FUNC = silky_intercept_func
