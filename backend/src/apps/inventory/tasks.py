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
    """
    return Reservation.objects.expired().update(status=ReservationStatus.RELEASED)
