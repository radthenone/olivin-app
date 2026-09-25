"""Adapter e-mail dla powiadomień (ADR 0027).

Cienka warstwa nad istniejącą infrastrukturą wysyłki (`core.services.mail`,
używaną dziś przez allauth): powiadomienia dostają własny punkt wejścia pod
`core/integrations/`, żeby nowy kod nie ciągnął zależności z legacy modułu
wprost, ale nie duplikuje kolejkowania ani budowy wiadomości.
"""

from __future__ import annotations

from typing import Any, cast

from django.conf import settings

from core.services.mail.tasks import send_email_payloads_task
from core.services.mail.types import EmailPayload


def send_notification_email(*, to: str, subject: str, body: str) -> None:
    """Kolejkuje e-mail powiadomienia jako zadanie Celery."""
    payload: EmailPayload = {
        "subject": subject,
        "body": body,
        "from_email": settings.DEFAULT_FROM_EMAIL,
        "to": [to],
        "cc": [],
        "bcc": [],
        "reply_to": [],
        "headers": {},
        "alternatives": {},
    }
    task = cast(Any, send_email_payloads_task)
    task.delay([payload])
