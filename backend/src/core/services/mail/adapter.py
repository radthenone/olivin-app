from __future__ import annotations

import json
from typing import Any, cast

from allauth.account.adapter import DefaultAccountAdapter
from django.http import RawPostDataException
from django.db import transaction
from django.db.transaction import on_commit

from apps.accounts.services import update_profile_from_signup_data
from core.services.mail.service import MailService
from core.services.mail.tasks import send_email_payloads_task


def get_request_payload(request) -> dict:
    """Zwraca dane requestu także dla headless JSON signup."""
    data = getattr(request, "data", None)
    if data:
        return dict(data)

    post_data = getattr(request, "POST", None)
    if post_data:
        if hasattr(post_data, "dict"):
            return post_data.dict()
        return dict(post_data)

    try:
        body = getattr(request, "body", b"")
    except RawPostDataException:
        return {}

    if not body:
        return {}

    try:
        payload = json.loads(body.decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError):
        return {}

    return payload if isinstance(payload, dict) else {}


class AsyncAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """Zapisuje użytkownika allauth i zakłada powiązany profil."""
        with transaction.atomic():
            saved_user = super().save_user(request, user, form, commit)
            if commit:
                update_profile_from_signup_data(
                    saved_user,
                    get_request_payload(request),
                )
            return saved_user

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

    def populate_username(self, request, user):
        if hasattr(user, "username") and getattr(user, "username") is None:
            pass
        else:
            super().populate_username(request, user)
