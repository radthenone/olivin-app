"""
Production settings for Olivin project.
"""

import os

from django.core.exceptions import ImproperlyConfigured

DEBUG = False

# Linki z maili muszą wskazywać kanoniczną domenę webu (ADR 0038); domyślny
# `localhost` z `components/email.py` wysłałby klientom martwe linki.
if not os.environ.get("FRONTEND_URL"):
    raise ImproperlyConfigured("FRONTEND_URL jest wymagane w produkcji.")

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HTTPS settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email backend for production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
