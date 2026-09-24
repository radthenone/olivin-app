"""Wysyłka powiadomień (`CONTEXT.md`, Notification; ADR 0027)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.notifications.models import (
    TRANSACTIONAL_KINDS,
    Notification,
    NotificationPreference,
)
from core.integrations.notifications.mail import send_notification_email

if TYPE_CHECKING:
    from apps.accounts.models import CustomUser

# Treść krótkich transakcyjnych e-maili; klucz to `NotificationKind`.
_TEMPLATES: dict[str, tuple[str, str]] = {
    "order_status_changed": (
        "Zmiana statusu zamówienia {order_number}",
        "Zamówienie {order_number} ma teraz status: {status_label}.",
    ),
    "order_paid": (
        "Zamówienie {order_number} opłacone",
        "Dziękujemy — zamówienie {order_number} zostało opłacone.",
    ),
    "document_ready": (
        "Dokument do zamówienia {order_number} gotowy",
        "Dokument {document_kind} do zamówienia {order_number} jest gotowy.",
    ),
}


def _render(kind: str, payload: dict[str, Any]) -> tuple[str, str]:
    subject_tpl, body_tpl = _TEMPLATES.get(kind, (kind, kind))
    try:
        return subject_tpl.format(**payload), body_tpl.format(**payload)
    except KeyError:
        # Payload bez wszystkich pól szablonu — treść zamiast wyjątku.
        return subject_tpl, body_tpl


def _has_marketing_consent(user: CustomUser) -> bool:
    return NotificationPreference.for_user(user).marketing_email


def notify(
    user_or_email: CustomUser | str, kind: str, payload: dict[str, Any]
) -> Notification | None:
    """Zapisuje powiadomienie (dla konta) i wysyła e-mail (`CONTEXT.md`, Notification).

    Transakcyjne rodzaje (`TRANSACTIONAL_KINDS`) docierają zawsze; pozostałe
    (marketingowe) tylko za zgodą `NotificationPreference.marketing_email` —
    gość nigdy jej nie ma, więc marketing do gościa jest zawsze pominięty.
    Gość dostaje wyłącznie e-mail — bez rekordu, bo nie ma gdzie go pokazać.
    """
    from apps.accounts.models import CustomUser

    user = user_or_email if isinstance(user_or_email, CustomUser) else None
    email = user.email if user is not None else str(user_or_email)  # type: ignore[missing-attribute]

    if kind not in TRANSACTIONAL_KINDS and not (
        user is not None and _has_marketing_consent(user)
    ):
        return None

    subject, message = _render(kind, payload)

    notification: Notification | None = None
    if user is not None:
        notification = Notification.objects.create(
            user=user, kind=kind, message=message, data=payload
        )

    transaction.on_commit(
        lambda: send_notification_email(to=email, subject=subject, body=message)
    )
    return notification
