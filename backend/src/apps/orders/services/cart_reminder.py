"""Przypomnienie o koszyku (`CONTEXT.md`, CartReminder; #208)."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils import timezone

from apps.inventory.models import available_variants
from apps.notifications.models import NotificationKind
from apps.notifications.newsletter import account_unsubscribe_url
from apps.notifications.services import notify
from apps.orders.models import Cart, CartItem
from apps.products.models import ProductStatus

CART_REMINDER_AFTER = timedelta(hours=24)


def _available_items() -> QuerySet[CartItem]:
    return CartItem.objects.filter(
        variant__in=available_variants().filter(product__status=ProductStatus.PUBLISHED)
    )


def due_carts(now: datetime) -> QuerySet[Cart]:
    """Koszyki do przypomnienia: aktywne konto ze zgodą na którymś kanale, doba ciszy.

    Zgoda na danym kanale (`CONTEXT.md`, CartReminder): wybór wystarczy
    przy `marketing_email` albo `marketing_push`, a `notify()` sam bramkuje
    każdy kanał. `reminded_at IS NULL` znaczy „bez przypomnienia od ostatniej
    zmiany zawartości” — `Cart.touch()` zeruje je przy każdej zmianie pozycji.
    Koszyk bez żadnej dostępnej pozycji odpada już w zapytaniu, żeby nie
    wracał co godzinę. Złożone zamówienie opróżnia koszyk, więc nieopłacone
    zamówienie nie wyzwala przypomnienia.
    """
    return (
        Cart.objects.filter(
            Q(user__notification_preference__marketing_email=True)
            | Q(user__notification_preference__marketing_push=True),
            user__isnull=False,
            user__is_active=True,
            reminded_at__isnull=True,
        )
        .filter(Exists(_available_items().filter(cart=OuterRef("pk"))))
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
def send_cart_reminder(cart_pk: object, *, now: datetime) -> bool:
    """Wysyła przypomnienie przez `notify()` i zapisuje jego moment.

    Koszyk jest blokowany i sprawdzany ponownie, a zablokowany przez inny
    obchód albo zmianę zawartości — pomijany (`skip_locked`): nie będzie
    podwójnej wysyłki ani czekania na cudzą transakcję.
    """
    locked = (
        due_carts(now)
        .select_for_update(skip_locked=True, of=("self",))
        .filter(pk=cart_pk)
        .select_related("user")
        .first()
    )
    if locked is None or locked.user is None:
        return False
    items = list(
        locked.items.select_related(  # type: ignore[missing-attribute]
            "variant", "variant__product", "variant__inventory"
        )
        .prefetch_related("variant__cost_components")
        .order_by("created_at", "id")
    )
    notify(
        locked.user,
        NotificationKind.CART_REMINDER,
        {
            "items": "\n".join(_item_line(item) for item in items),
            "cart_url": settings.CART_URL,
            "preferences_url": settings.NOTIFICATION_PREFERENCES_URL,
            "unsubscribe_url": account_unsubscribe_url(locked.user.pk),
        },
        push_body=f"Pozycje w koszyku: {len(items)}. Wróć, zanim znikną.",
        push_data={"type": NotificationKind.CART_REMINDER.value},
    )
    Cart.objects.filter(pk=locked.pk).update(reminded_at=now)
    return True


def send_cart_reminders(now: datetime | None = None) -> int:
    """Obchód zadania okresowego; zwraca liczbę wysłanych przypomnień."""
    now = now or timezone.now()
    return sum(
        send_cart_reminder(pk, now=now)
        for pk in due_carts(now).values_list("pk", flat=True).iterator()
    )
