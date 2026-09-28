"""Serwis obserwowanych wariantów (`CONTEXT.md`, Watch; issue #201)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.watches.models import Watch, WatchKind, WatchStatus

if TYPE_CHECKING:
    from apps.accounts.models import CustomUser
    from apps.products.models import ProductVariant

logger = logging.getLogger(__name__)

# Rodzaje powiadomień wysyłane przez `notifications.services.notify`.
# Celowo spoza `TRANSACTIONAL_KINDS` — komunikat jest marketingowy
# i podlega preferencjom (`CONTEXT.md`, Watch, Notification).
WATCH_RESTOCK_KIND = "watch_restock"
WATCH_PRICE_DROP_KIND = "watch_price_drop"


def watches_for(user: CustomUser):  # type: ignore[no-untyped-def]
    """Aktywne obserwowane warianty klienta do listy w API."""
    return (
        Watch.objects.filter(user=user, status=WatchStatus.ACTIVE)
        .select_related("variant", "variant__product")
        .order_by("-created_at", "-id")
    )


def add_watch(*, user: CustomUser, variant: ProductVariant, kind: str) -> Watch:
    """Zapisuje prośbę o jednorazowe powiadomienie.

    Produkt na zamówienie: tylko `price_drop` (nie ma stanu, ADR 0024).
    `price_drop` zapisuje cenę z chwili zapisu (`effective_price` — cena
    ręczna ma pierwszeństwo, promocje się nie liczą). Powtórzenie aktywnej
    prośby jest bezpieczne (idempotentne) — zwraca istniejący wpis.
    """
    if kind not in (WatchKind.RESTOCK, WatchKind.PRICE_DROP):
        raise ValidationError({"kind": "Nieznany rodzaj obserwowania."})
    if kind == WatchKind.RESTOCK and variant.product.is_made_to_order:
        raise ValidationError(
            {"kind": "Produkt na zamówienie można obserwować tylko pod kątem ceny."}
        )

    price_at_watch = None
    currency = variant.currency
    if kind == WatchKind.PRICE_DROP:
        price_at_watch = variant.effective_price.amount

    try:
        with transaction.atomic():
            watch, created = Watch.objects.get_or_create(
                user=user,
                variant=variant,
                kind=kind,
                status=WatchStatus.ACTIVE,
                defaults={
                    "price_at_watch": price_at_watch,
                    "currency": currency,
                },
            )
    except IntegrityError:
        watch = Watch.objects.get(
            user=user, variant=variant, kind=kind, status=WatchStatus.ACTIVE
        )
        created = False
    if created:
        watch.full_clean(exclude=["user", "variant"], validate_unique=False)
    return watch


def remove_watch(*, user: CustomUser, watch_id: str) -> None:
    """Usuwa prośbę klienta; brak dopasowania też jest sukcesem (idempotentne)."""
    Watch.objects.filter(user=user, pk=watch_id).delete()


def _send_watch(watch: Watch, kind: str, payload: dict) -> bool:
    """Wysyła powiadomienie marketingowe i wygasza prośbę.

    Zwraca `True`, gdy wysłano (prośba wygasła), `False` przy braku zgody
    marketingowej — wtedy prośba zostaje aktywna do następnej okazji.
    """
    from apps.notifications.services import notify

    notification = notify(watch.user, kind, payload)
    if notification is None:
        return False
    watch.mark_sent()
    return True


def notify_restock_watches(variant: ProductVariant) -> int:
    """Wyzwalacz powrotu na stan: dostępność z 0 na >0 (issue #201).

    Wołane po każdym zdarzeniu zmieniającym dostępność (ruch magazynowy,
    zwolnienie/wygaśnięcie rezerwacji). Wysyła tylko, gdy wariant jest
    dziś dostępny — prośby powstają przy niedostępnym wariancie, więc
    każde `available > 0` oznacza powrót na stan dla czekających wpisów.
    """
    if variant.product.is_made_to_order:
        return 0
    available = variant.available
    if available is None or available <= 0:
        return 0
    sent = 0
    watches = list(
        Watch.objects.active()
        .filter(variant=variant, kind=WatchKind.RESTOCK)
        .select_related("variant", "variant__product")
    )
    for watch in watches:
        payload = {
            "variant_sku": variant.sku,
            "product_name": variant.product.name,
        }
        try:
            if _send_watch(watch, WATCH_RESTOCK_KIND, payload):
                sent += 1
        except Exception:
            logger.exception("Nie udało się wysłać powiadomienia Watch %s", watch.pk)
    return sent


def notify_price_watches(variant: ProductVariant) -> int:
    """Wyzwalacz spadku ceny: nowa `Price` niższa niż zapisana (issue #201).

    Porównuje bieżącą cenę efektywną (`manual_price` albo `price`) z ceną
    zapisaną przy prośbie. Promocje się nie liczą — nie są częścią `Price`.
    Wołane po przeliczeniu cen (aktywacja `MetalRate`) i po zapisie wariantu.
    """
    current = variant.effective_price.amount
    sent = 0
    watches = list(
        Watch.objects.active()
        .filter(variant=variant, kind=WatchKind.PRICE_DROP)
        .select_related("variant", "variant__product")
    )
    for watch in watches:
        if watch.price_at_watch is None or current >= watch.price_at_watch:
            continue
        payload = {
            "variant_sku": variant.sku,
            "product_name": variant.product.name,
            "old_price": watch.price_at_watch,
            "new_price": current,
        }
        try:
            if _send_watch(watch, WATCH_PRICE_DROP_KIND, payload):
                sent += 1
        except Exception:
            logger.exception("Nie udało się wysłać powiadomienia Watch %s", watch.pk)
    return sent
