from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import get_connection

from core.services.mail.service import MailService
from core.services.mail.types import EmailPayload


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_email_payloads_task(self, payloads: list[EmailPayload]) -> int:
    connection = get_connection(backend=settings.ACTUAL_EMAIL_BACKEND)
    messages = [MailService.build(p, connection=connection) for p in payloads]
    return connection.send_messages(messages) or 0
