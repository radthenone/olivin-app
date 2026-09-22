from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.orders.models import GUEST_CART_TTL_DAYS, Cart


@shared_task
def purge_stale_guest_carts() -> int:
    """Kasuje koszyki gości bez aktywności przez 30 dni (ADR 0030).

    Tylko gości: koszyk konta należy do klienta, który może wrócić po roku
    i ma prawo zastać to, co zostawił. Koszyk gościa jest dostępny wyłącznie
    przez token, więc po miesiącu ciszy nie ma już komu go pokazać.
    """
    cutoff = timezone.now() - timedelta(days=GUEST_CART_TTL_DAYS)
    deleted, _ = Cart.objects.guest().inactive_since(cutoff).delete()
    return deleted
