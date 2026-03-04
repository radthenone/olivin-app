"""
Ustawienia bezpieczeństwa i CORS dla Django.

Zawiera konfigurację ALLOWED_HOSTS, CORS oraz ustawienia bezpieczeństwa
wspólne dla wszystkich środowisk.
"""

import os

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


CORS_ALLOW_CREDENTIALS: bool = True
CORS_ALLOW_HEADERS: list[str] = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-api-version",
]
