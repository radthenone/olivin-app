"""Wyzwalacze obserwowanych (`CONTEXT.md`, Watch; issue #201).

Zdarzeniowo, nie cyklicznie (`.ai/project.md`): ruch magazynowy i zapis
wariantu budzą czekające prośby. Ścieżki zbiorcze (`bulk_update` w
przeliczeniu cen, hurtowe zwalnianie rezerwacji) omijają sygnały — tam
wołane są wprost funkcje z `apps.watches.services`.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.inventory.models import Reservation, ReservationStatus, StockMovement
from apps.products.models import ProductVariant


@receiver(post_save, sender=StockMovement, dispatch_uid="watches_restock_on_movement")
def _restock_on_movement(
    sender, instance: StockMovement, created: bool, **kwargs
) -> None:
    """Ruch zmienia stan z ruchów — sprawdza powrót na stan po commicie."""
    if not created:
        return
    variant_id = instance.item.variant_id  # type: ignore[missing-attribute]

    def _check() -> None:
        from apps.products.models import ProductVariant
        from apps.watches.services import notify_restock_watches

        variant = (
            ProductVariant.objects.select_related("product")
            .filter(pk=variant_id)
            .first()
        )
        if variant is not None:
            notify_restock_watches(variant)

    transaction.on_commit(_check, robust=True)


@receiver(post_save, sender=Reservation, dispatch_uid="watches_restock_on_release")
def _restock_on_reservation(
    sender, instance: Reservation, created: bool, **kwargs
) -> None:
    """Zwolnienie rezerwacji wraca do dostępności bez ruchu — też budzi Watch."""
    if created or instance.status != ReservationStatus.RELEASED:
        return
    variant_id = instance.variant_id  # type: ignore[missing-attribute]

    def _check() -> None:
        from apps.products.models import ProductVariant
        from apps.watches.services import notify_restock_watches

        variant = (
            ProductVariant.objects.select_related("product")
            .filter(pk=variant_id)
            .first()
        )
        if variant is not None:
            notify_restock_watches(variant)

    transaction.on_commit(_check, robust=True)


@receiver(
    post_save, sender=ProductVariant, dispatch_uid="watches_price_on_variant_save"
)
def _price_on_variant_save(
    sender, instance: ProductVariant, created: bool, **kwargs
) -> None:
    """Zapis wariantu (np. cena ręczna z panelu) — sprawdza spadek ceny po commicie."""
    if created:
        return

    def _check() -> None:
        from apps.watches.services import notify_price_watches

        fresh = (
            ProductVariant.objects.select_related("product")
            .filter(pk=instance.pk)
            .first()
        )
        if fresh is not None:
            notify_price_watches(fresh)

    transaction.on_commit(_check, robust=True)
