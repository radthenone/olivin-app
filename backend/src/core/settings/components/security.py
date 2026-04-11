"""
Ustawienia bezpieczeństwa i CORS dla Django.

Zawiera konfigurację ALLOWED_HOSTS, CORS oraz ustawienia bezpieczeństwa
wspólne dla wszystkich środowisk.
"""

import os

from corsheaders.defaults import default_headers

ALLOWED_HOSTS: list[str] = list(
    str(os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,10.0.2.2")).split(
        ","
    )
)

CORS_ALLOWED_ORIGINS: list[str] = list(
    os.environ.get(
        "FRONTEND_URLS",
        "http://localhost:8081,http://127.0.0.1:8081,http://10.0.2.2:8081",
    ).split(",")
)


# Wymagane, gdy frontend (SPA) jest na innym origin niż backend i używasz
# sesji cookie + CSRF.
CSRF_TRUSTED_ORIGINS: list[str] = list(
    os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:8081,http://127.0.0.1:8081,http://10.0.2.2:8081",
    ).split(","),
)


CORS_ALLOW_CREDENTIALS: bool = True
CORS_ALLOW_HEADERS: list[str] = [
    *default_headers,
    "x-api-version",
    "x-csrftoken",
]

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
