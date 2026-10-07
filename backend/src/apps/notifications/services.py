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
    PushDevice,
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
    "return_request_status_changed": (
        "Zgłoszenie zwrotu do zamówienia {order_number}",
        "Zgłoszenie zwrotu do zamówienia {order_number} ma teraz stan: {status_label}.",
    ),
    "return_settled": (
        "Rozliczenie zwrotu do zamówienia {order_number}",
        "Zwrot do zamówienia {order_number} rozliczony na {compensation_amount}: "
        "{compensation_form}.",
    ),
    "watch_restock": (
        "Wariant {variant_sku} wrócił na stan",
        "Obserwowany wariant {variant_sku} ({product_name}) jest znowu dostępny.",
    ),
    "watch_price_drop": (
        "Cena wariantu {variant_sku} spadła",
        "Obserwowany wariant {variant_sku} ({product_name}) stanieje: "
        "było {old_price}, jest {new_price}.",
    ),
    "cart_reminder": (
        "W koszyku czekają na Ciebie wyroby",
        "W Twoim koszyku zostały wyroby — ceny i dostępność na dziś:\n"
        "{items}\n\n"
        "Wróć do koszyka: {cart_url}\n\n"
        "Nie chcesz takich wiadomości? Zmień zgody: {preferences_url}\n"
        "Wypisz się: {unsubscribe_url}",
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


def _has_marketing_push_consent(user: CustomUser) -> bool:
    return NotificationPreference.for_user(user).marketing_push


def _should_send_push(user: CustomUser | None, kind: str) -> bool:
    """Czy push dla tego rodzaju i klienta (issue #202).

    Transakcyjne zawsze; marketingowe tylko za zgodą `marketing_push`.
    Gość nigdy — nie ma urządzeń.
    """
    if user is None:
        return False
    if kind in TRANSACTIONAL_KINDS:
        return True
    return _has_marketing_push_consent(user)


def register_push_device(*, user: CustomUser, token: str, platform: str) -> PushDevice:
    """Rejestruje urządzenie push; powtórzenie odświeża właściciela i czas.

    Token jest globalnie unikalny: to samo urządzenie po wylogowaniu
    i zalogowaniu na inne konto przechodzi na nowe konto — stąd
    `update_or_create` po tokenie, nie po parze (konto, token). Wyścig
    dwóch równoległych rejestracji rozstrzyga ograniczenie unikalności.
    """
    from django.db import IntegrityError
    from django.utils import timezone

    from apps.notifications.models import PushDevice

    token = token.strip()
    try:
        device, _ = PushDevice.objects.update_or_create(
            token=token,
            defaults={
                "user": user,
                "platform": platform,
                "last_used_at": timezone.now(),
            },
        )
    except IntegrityError:
        device = PushDevice.objects.get(token=token)
        device.user = user  # type: ignore[assignment]
        device.platform = platform
        device.last_used_at = timezone.now()
        device.save(update_fields=["user", "platform", "last_used_at", "updated_at"])
    return device


def unregister_push_device(*, user: CustomUser, token: str) -> None:
    """Wyrejestrowuje urządzenie; brak dopasowania też jest sukcesem."""
    PushDevice.objects.filter(user=user, token=token.strip()).delete()


def notify(
    user_or_email: CustomUser | str,
    kind: str,
    payload: dict[str, Any],
    *,
    email: str | None = None,
    push_body: str | None = None,
    push_data: dict[str, Any] | None = None,
) -> Notification | None:
    """Zapisuje powiadomienie (dla konta) i wysyła e-mail (`CONTEXT.md`, Notification).

    Kanał push (issue #202) jest kolejkowany jako zadanie Celery po commicie:
    transakcyjne zawsze, marketingowe tylko za zgodą `marketing_push`.
    Błąd pusha nie blokuje e-maila ani rekordu.

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

    `push_body` i `push_data` zastępują w pushu treść e-maila i payload —
    dla komunikatów, których pełna treść jest za długa na powiadomienie
    (np. przypomnienie o koszyku z listą pozycji).

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

    subject, message = _render(kind, payload)

    # Push jest niezależnym kanałem z własną zgodą (`marketing_push`):
    # kolejkowanie przed bramką e-mailową, żeby marketing z samym `push`
    # (bez `marketing_email`) też doszedł. Transakcyjne zawsze, gość nigdy.
    def _send_push() -> None:
        if not _should_send_push(user, kind):
            return
        try:
            from typing import Any, cast

            from apps.notifications.tasks import send_push_notification

            assert user is not None
            # `cast(Any, ...)` jak w `send_notification_email`: pyrefly
            # widzi w udekorowanym zadaniu Celery `list[str]`, nie callable.
            task = cast(Any, send_push_notification)
            task.delay(
                user_id=str(user.pk),
                title=subject,
                body=push_body if push_body is not None else message,
                data=push_data if push_data is not None else payload,
            )
        except Exception:
            # Push nie blokuje pozostałych kanałów — błąd kolejkowania
            # kończy się logiem, nie wyjątkiem z callbacku po commicie.
            logger.exception("Nie udało się zakolejkować pusha %r", kind)

    transaction.on_commit(_send_push, robust=True)

    if kind not in TRANSACTIONAL_KINDS and not (
        user is not None and _has_marketing_consent(user)
    ):
        return None

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
