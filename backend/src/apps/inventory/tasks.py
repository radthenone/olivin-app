from __future__ import annotations

from celery import shared_task

from apps.inventory.models import Reservation, ReservationStatus


@shared_task
def expire_reservations() -> int:
    """Oznacza przeterminowane rezerwacje jako zwolnione (`CONTEXT.md`, Reservation).

    Sprzątanie, nie przywracanie stanu: dostępność liczy wyłącznie
    rezerwacje nieprzeterminowane, więc towar wraca do sprzedaży dokładnie
    w chwili wygaśnięcia, niezależnie od tego, kiedy przejdzie ten obchód.
    Zadanie porządkuje statusy, żeby panel i historia mówiły prawdę.
    Po sprzątnięciu budzi obserwowane warianty — wygasła rezerwacja to
    powrót na stan dla czekających próśb (issue #201).
    """
    expired_ids = list(
        Reservation.objects.expired().values_list("variant_id", flat=True).distinct()
    )
    updated = Reservation.objects.expired().update(status=ReservationStatus.RELEASED)
    if expired_ids:
        try:
            from apps.products.models import ProductVariant
            from apps.watches.services import notify_restock_watches

            for variant in ProductVariant.objects.select_related("product").filter(
                pk__in=set(expired_ids)
            ):
                notify_restock_watches(variant)
        except Exception:  # pragma: no cover - powiadomienie nie psuje sprzątania
            import logging

            logging.getLogger(__name__).exception("Watch restock check failed")
    return updated
