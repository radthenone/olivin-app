"""Wymiana na ten sam wariant jako rozstrzygnięcie zwrotu (#198, CONTEXT.md).

Zamiast rekompensaty klient może dostać nowy egzemplarz tego samego wariantu:
zamówienie 0 zł, bez płatności, promocji ani kuponu, powiązane ze zgłoszeniem
zwrotu przez pozycję, która je wywołała. Produkt magazynowy wymienia się
przy każdej podstawie, gdy w chwili przyjęcia jest na stanie (inaczej pozycja
rozlicza się jak zwykły zwrot pieniędzy, patrz `services.settlement`).
Produkt na zamówienie wymienia się wyłącznie w ramach reklamacji, przez
ponowne wykonanie: zamówienie idzie prosto w `in_production`, bez sprawdzania
stanu (ADR 0024).
"""

from __future__ import annotations

from django.db import transaction

from apps.inventory.services import ReservationError
from apps.orders.models import (
    ClaimRequest,
    Order,
    OrderItem,
    OrderStatus,
    ReturnRequestItem,
)
from apps.orders.services.order import consume_stock, mark_paid


def can_exchange(item: ReturnRequestItem) -> bool:
    """Czy pozycję da się dziś wymienić na ten sam wariant.

    Sprawdza `order_item.is_made_to_order` — kopię z chwili złożenia
    (ADR 0010), nie bieżącą flagę produktu, która mogła się zmienić.
    """
    if item.claim_request != ClaimRequest.REPLACEMENT:
        return False
    order_item = item.order_item
    if order_item.is_made_to_order:
        return True
    needed = item.quantity * order_item.specimen_count
    return (order_item.variant.available or 0) >= needed


def create_exchange_order(item: ReturnRequestItem) -> Order | None:
    """Zakłada zamówienie 0 zł wymieniające pozycję; `None`, gdy się nie da.

    Wołane z `decide_return_item()` — **przed** ewentualnym „wraca na stan”
    tej samej pozycji, żeby odebrany wadliwy egzemplarz nie podbił dostępności
    na potrzeby własnej wymiany. Adres, dostawa i faktura to kopia źródłowego
    zamówienia; towar i dostawa kosztują 0 — bez promocji ani kuponu
    (kryteria akceptacji #198).

    Własny savepoint: gdy zdjęcie ze stanu padnie na wyścigu o ostatnią sztukę
    (`ReservationError` — stan zniknął między sprawdzeniem a rezerwacją),
    całe założenie zamówienia się cofa i pozycja rozlicza się dalej jak
    zwykły zwrot, zamiast wywrócić decyzję sklepu błędem 500.
    """
    if not can_exchange(item):
        return None
    order_item = item.order_item
    source = order_item.order
    variant = order_item.variant
    is_made_to_order = order_item.is_made_to_order

    try:
        with transaction.atomic():
            exchange_order = Order.objects.create(
                user=source.user,
                email=source.email,
                recipient_name=source.recipient_name,
                street=source.street,
                street2=source.street2,
                city=source.city,
                postal_code=source.postal_code,
                country=source.country,
                shipping_method=source.shipping_method,
                shipping_method_name=source.shipping_method_name,
                shipping_cost=0,
                currency=source.currency,
                exchange_rate=source.exchange_rate,
                exchange_rate_on=source.exchange_rate_on,
                exchange_rate_source=source.exchange_rate_source,
                terms_document=source.terms_document,
                invoice_requested=source.invoice_requested,
            )
            OrderItem.objects.create(
                order=exchange_order,
                variant=variant,
                product_name=order_item.product_name,
                sku=order_item.sku,
                is_made_to_order=is_made_to_order,
                quantity=item.quantity,
                unit_price=0,
                vat_rate=order_item.vat_rate,
                is_vat_exempt=order_item.is_vat_exempt,
                vat_exemption_basis=order_item.vat_exemption_basis,
                engraving_text=order_item.engraving_text,
                engraving_price=0,
                size=order_item.size,
                second_size=order_item.second_size,
                second_engraving_text=order_item.second_engraving_text,
            )
            item.exchange_order = exchange_order
            item.save(update_fields=["exchange_order", "updated_at"])

            # Wariant magazynowy schodzi ze stanu jak przy zwykłej zapłacie
            # kuponem w całości (`services.order.create_order`); produkt na
            # zamówienie nie ma czego zdejmować i idzie prosto w produkcję.
            if not is_made_to_order:
                consume_stock(exchange_order)
            mark_paid(exchange_order)
            if is_made_to_order:
                exchange_order.transition_to(OrderStatus.IN_PRODUCTION)
    except ReservationError:
        item.exchange_order = None
        return None
    return exchange_order
