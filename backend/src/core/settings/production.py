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
# Nagłówek one-click wypisu (RFC 8058) musi wskazywać publiczny adres HTTPS API.
# `http` odpada: RFC 8058 wymaga HTTPS, a `SECURE_SSL_REDIRECT` dałby 301 na POST.
if not os.environ.get("BACKEND_URL", "").startswith("https://"):
    raise ImproperlyConfigured("BACKEND_URL (https://) jest wymagane w produkcji.")
# Bez sekretu web nie przyjmie rewalidacji, a strona produktu pokazywałaby
# do wygaśnięcia keszu inną cenę niż kasa (ADR 0034, #318).
if not os.environ.get("REVALIDATE_SECRET"):
    raise ImproperlyConfigured("REVALIDATE_SECRET jest wymagane w produkcji.")

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
