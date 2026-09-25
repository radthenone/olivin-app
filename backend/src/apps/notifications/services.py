"""Wysyłka powiadomień (`CONTEXT.md`, Notification; ADR 0027)."""

from __future__ import annotations

import logging
from collections import defaultdict
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

logger = logging.getLogger(__name__)

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
    except KeyError as exc:
        # Payload bez wszystkich pól szablonu: zamiast surowych `{placeholder}`
        # w treści, brakujące pola znikają po cichu — powiadomienie ma zostać
        # czytelne, nawet gdy wywołujący zapomni o jednym polu.
        logger.warning(
            "Powiadomienie %r: payload bez pola %s, szablon renderowany częściowo",
            kind,
            exc,
        )
        safe_payload = defaultdict(str, payload)
        return subject_tpl.format_map(safe_payload), body_tpl.format_map(safe_payload)


def _has_marketing_consent(user: CustomUser) -> bool:
    return NotificationPreference.for_user(user).marketing_email


def notify(
    user_or_email: CustomUser | str,
    kind: str,
    payload: dict[str, Any],
    *,
    email: str | None = None,
) -> Notification | None:
    """Zapisuje powiadomienie (dla konta) i wysyła e-mail (`CONTEXT.md`, Notification).

    Transakcyjne rodzaje (`TRANSACTIONAL_KINDS`) docierają zawsze; pozostałe
    (marketingowe) tylko za zgodą `NotificationPreference.marketing_email` —
    świadomie bramkuje ona też zapis rekordu w aplikacji, nie tylko e-mail:
    klient bez zgody nie ma zobaczyć w aplikacji tego, na co się nie zgodził.
    Gość nigdy nie ma zgody, więc marketing do gościa jest zawsze pominięty.
    Gość (samo `user_or_email` jako e-mail) dostaje wyłącznie e-mail — bez
    rekordu, bo nie ma gdzie go pokazać.

    `email` nadpisuje adres wysyłki niezależnie od `user_or_email.email` —
    potrzebne tam, gdzie adres zdarzenia (np. zamówienia) jest niemutowalną
    kopią z chwili złożenia i może różnić się od dzisiejszego e-maila konta
    (`CONTEXT.md`, Account anonymisation). Rekord w aplikacji i tak idzie na
    konto z `user_or_email` — tylko adres wysyłki jest inny.

    Bez idempotencji: każde wywołanie tworzy nowy rekord i kolejkuje nowy
    e-mail. To wywołujący odpowiada za wywołanie raz na realne zdarzenie —
    `issue_document()` woła tylko dla nowo wystawionego dokumentu, sygnał
    zamówienia tylko przy faktycznej zmianie statusu (patrz `orders/signals.py`).
    """
    from apps.accounts.models import CustomUser

    user = user_or_email if isinstance(user_or_email, CustomUser) else None
    recipient_email = email or (
        user.email if user is not None else str(user_or_email)  # type: ignore[missing-attribute]
    )

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

    def _send() -> None:
        try:
            send_notification_email(to=recipient_email, subject=subject, body=message)
        except Exception:
            # Wysyłka nie może zawalić reszty callbacków po commicie (np.
            # wystawienia dokumentu sprzedaży) — powiadomienie jest efektem
            # ubocznym zdarzenia, nie jego warunkiem.
            logger.exception("Nie udało się wysłać e-maila powiadomienia %r", kind)

    transaction.on_commit(_send, robust=True)
    return notification
