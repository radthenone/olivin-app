"""
Production settings for Olivin project.
"""

import os
import warnings

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
# Bez sekretu backend nie woła rewalidacji katalogu na webie (ADR 0034, #318),
# więc strona produktu pokazuje nową cenę dopiero po wygaśnięciu keszu.
# Tylko ostrzeżenie: route `/api/revalidate` w Next jeszcze nie istnieje —
# wymóg (`ImproperlyConfigured`) wróci razem z nim.
if not os.environ.get("REVALIDATE_SECRET"):
    warnings.warn(
        "REVALIDATE_SECRET nie jest ustawione — rewalidacja katalogu na webie "
        "jest wyłączona.",
        RuntimeWarning,
        stacklevel=1,
    )

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
