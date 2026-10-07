"""Przypomnienie o koszyku (`CONTEXT.md`, CartReminder; #208)."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, QuerySet
from django.utils import timezone

from apps.notifications.models import NotificationKind
from apps.notifications.services import notify
from apps.orders.models import Cart, CartItem
from apps.orders.services.cart import cart_items

CART_REMINDER_AFTER = timedelta(hours=24)


def due_carts(now: datetime) -> QuerySet[Cart]:
    """Koszyki do przypomnienia: konto aktywne ze zgodą e-mail, niepuste, doba ciszy.

    `reminded_at IS NULL` znaczy „bez przypomnienia od ostatniej zmiany
    zawartości” — `Cart.touch()` zeruje je przy każdej zmianie pozycji.
    Złożone zamówienie opróżnia koszyk, więc nieopłacone zamówienie nie
    wyzwala przypomnienia.
    """
    return (
        Cart.objects.filter(
            user__isnull=False,
            user__is_active=True,
            user__notification_preference__marketing_email=True,
            reminded_at__isnull=True,
        )
        .filter(Exists(CartItem.objects.filter(cart=OuterRef("pk"))))
        .inactive_since(now - CART_REMINDER_AFTER)
    )


def _is_available(item: CartItem) -> bool:
    return item.variant.product.is_published and item.variant.is_available


def _item_line(item: CartItem) -> str:
    line = (
        f"- {item.variant.product.name} ({item.variant.sku}) × {item.quantity}: "
        f"{item.line_total}"
    )
    return line if _is_available(item) else f"{line} — niedostępne"


@transaction.atomic
def send_cart_reminder(cart: Cart, *, now: datetime) -> bool:
    """Wysyła przypomnienie przez `notify()` i zapisuje jego moment.

    Bez wysyłki, gdy żadna pozycja nie jest dostępna — wtedy też bez
    zapisu, żeby przypomnienie mogło wyjść, gdy towar wróci. Koszyk jest
    blokowany i sprawdzany ponownie: równoległa zmiana zawartości albo
    drugi obchód nie dadzą podwójnej wysyłki.
    """
    locked = due_carts(now).select_for_update(of=("self",)).filter(pk=cart.pk).first()
    if locked is None or locked.user is None:
        return False
    items = list(cart_items(locked))
    if not any(_is_available(item) for item in items):
        return False
    notify(
        locked.user,
        NotificationKind.CART_REMINDER,
        {
            "items": "\n".join(_item_line(item) for item in items),
            "cart_url": settings.CART_URL,
            "preferences_url": settings.NOTIFICATION_PREFERENCES_URL,
        },
    )
    Cart.objects.filter(pk=locked.pk).update(reminded_at=now)
    return True


def send_cart_reminders(now: datetime | None = None) -> int:
    """Obchód zadania okresowego; zwraca liczbę wysłanych przypomnień."""
    now = now or timezone.now()
    return sum(send_cart_reminder(cart, now=now) for cart in due_carts(now))
