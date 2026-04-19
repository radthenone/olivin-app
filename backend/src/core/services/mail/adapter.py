from __future__ import annotations

from typing import Any, cast

from allauth.account.adapter import DefaultAccountAdapter
from django.db.transaction import on_commit

from core.services.mail.service import MailService
from core.services.mail.tasks import send_email_payloads_task


class AsyncAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        msg = self.render_mail(template_prefix, email, context)
        payload = MailService.serialize(msg)
        task = cast(Any, send_email_payloads_task)
        on_commit(lambda: task.delay([payload]))

    def clean_username(self, username: str | None, shallow: bool = False) -> str | None:
        """
        Zabezpieczenie dla kont społecznościowych, gdzie username wymuszamy na None.
        Domyślny walidator Allauth wyrzuca TypeError (NoneType ma brak domyślnej długości).
        """
        if username is None:
            return None
        return super().clean_username(username, shallow)
