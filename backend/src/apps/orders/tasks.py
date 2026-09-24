from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.orders.models import GUEST_CART_TTL_DAYS, UNPAID_ORDER_TTL, Cart, Order
from apps.orders.services.document import issue_documents
from apps.orders.services.order import expire_unpaid_orders


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


@shared_task
def cancel_stale_orders() -> int:
    """Anuluje zamówienia bez zapłaty przez dobę (`CONTEXT.md`, Order).

    Zwalnia przy tym rezerwacje: zamówienie, które nie zostanie opłacone,
    nie może w nieskończoność trzymać towaru poza sprzedażą. Rezerwacje
    i tak wygasają po pół godziny — to zadanie domyka samo zamówienie.
    """
    return expire_unpaid_orders(older_than=timezone.now() - UNPAID_ORDER_TTL)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def issue_sales_documents(order_id: str) -> list[str]:
    """Wystawia dokumenty sprzedaży po opłaceniu zamówienia (ADR 0026).

    Ponowne uruchomienie — powtórka zadania, drugie zdarzenie od operatora —
    zwraca dokumenty już wystawione zamiast nadawać nowe numery. Dlatego
    zadanie wolno ponawiać po awarii bucketa czy renderu: bez ponowienia
    opłacone zamówienie zostałoby bez dokumentu na zawsze.
    """
    order = Order.objects.get(pk=order_id)
    return [document.reference for document in issue_documents(order)]
