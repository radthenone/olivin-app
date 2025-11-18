import os

from pack_logger import configure_logging

"""
Development settings for Olivin project.
"""

DEBUG = True

# Development-specific settings
CORS_ALLOW_ALL_ORIGINS = True

# Allow Android emulator host
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "10.0.2.2",  # Android emulator host
    "*",  # W development pozwól na wszystkie hosty
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging
LOGGING = configure_logging(debug=DEBUG, app_name='olivin')