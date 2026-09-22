from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import ReservationStatus
from apps.inventory.services import (
    ReservationError,
    consume,
    release,
    reserve,
    restock,
)
from apps.orders.models import Order, OrderStatus
from apps.payments.models import Payment, PaymentStatus, RefundReason, WebhookEvent
from core.integrations.payments import (
    EventKind,
    PaymentProviderError,
    ProviderEvent,
    get_provider,
)


class PaymentError(ValidationError):
    """Odmowa rozpoczęcia zapłaty albo zwrotu, którą klient widzi jako 400."""


@dataclass(frozen=True, slots=True)
class StartedPayment:
    """Wynik rozpoczęcia zapłaty: próba po stronie sklepu i sekret dla klienta."""

    payment: Payment
    client_secret: str


@transaction.atomic
def start_payment(order: Order) -> StartedPayment:
    """Zakłada intencję płatniczą na kwotę zamówienia (ADR 0012).

    Każde wywołanie to nowa próba — nieudana zostaje jako ślad. Rezerwacje
    są odnawiane, bo trzymają stan 30 minut od **rozpoczęcia zapłaty**
    (`CONTEXT.md`, Reservation), a nie od złożenia zamówienia: klient
    wracający po nieudanej próbie ma dostać pełne pół godziny.
    """
    # Blokada wiersza szereguje równoległe próby tego samego zamówienia —
    # bez niej obie policzyłyby ten sam numer próby.
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != OrderStatus.PENDING:
        raise PaymentError(
            {
                "status": (
                    "Zapłacić można wyłącznie zamówienie oczekujące na zapłatę; "
                    f"to jest „{order.get_status_display()}”."  # type: ignore[missing-attribute]
                )
            }
        )

    total = order.total
    if total.amount <= 0:
        raise PaymentError({"total": "Zamówienie nie ma kwoty do zapłaty."})

    _renew_reservations(order)

    attempt = order.payments.count() + 1  # type: ignore[missing-attribute]
    try:
        intent = get_provider().create_intent(
            amount=total.amount,
            currency=total.currency,
            reference=order.number,
            idempotency_key=f"order-{order.number}-payment-{attempt}",
        )
    except PaymentProviderError as error:
        raise PaymentError(
            {"payment": "Operator płatności nie odpowiedział — spróbuj ponownie."}
        ) from error

    payment = Payment.objects.create(
        order=order,
        intent_id=intent.id,
        amount=total.amount,
        currency=total.currency,
    )
    return StartedPayment(payment=payment, client_secret=intent.client_secret)


@transaction.atomic
def request_cancellation(order: Order) -> Payment:
    """Anulowanie opłaconego zamówienia: zwrot u operatora.

    Zamówienie **nie** przechodzi tu do `cancelled` — robi to zdarzenie
    zwrotu, bo dopiero ono potwierdza, że pieniądze wróciły do klienta.
    """
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != OrderStatus.PAID:
        raise PaymentError(
            {"status": "Zwrot przy anulowaniu dotyczy wyłącznie zamówienia opłaconego."}
        )
    payments = order.payments.select_for_update()  # type: ignore[missing-attribute]
    if payments.filter(
        status=PaymentStatus.REFUNDING, refund_reason=RefundReason.CANCELLATION
    ).exists():
        raise PaymentError({"status": "Zwrot za to zamówienie jest już w toku."})
    payment = payments.filter(status=PaymentStatus.SUCCEEDED).first()
    if payment is None:
        raise PaymentError({"payment": "Zamówienie nie ma zapłaty do zwrotu."})

    try:
        _refund(payment, RefundReason.CANCELLATION)
    except PaymentProviderError as error:
        raise PaymentError(
            {"payment": "Operator płatności nie przyjął zwrotu — spróbuj ponownie."}
        ) from error
    return payment


@transaction.atomic
def handle_event(event: ProviderEvent) -> bool:
    """Przetwarza zdarzenie operatora dokładnie raz; `False` przy powtórce.

    Zapis zdarzenia i jego skutki idą w jednej transakcji: jeśli skutek
    się nie powiedzie, znika też zapis, operator ponawia dostarczenie
    i zdarzenie przechodzi od nowa. Zdarzenie bez znanej płatności zostaje
    zapisane i pominięte — to intencja założona poza sklepem.
    """
    stored, _ = WebhookEvent.objects.get_or_create(
        event_id=event.id,
        defaults={"kind": event.type, "payload": event.payload},
    )
    stored = WebhookEvent.objects.select_for_update().get(pk=stored.pk)
    if stored.processed_at is not None:
        return False

    payment = (
        Payment.objects.select_for_update().filter(intent_id=event.intent_id).first()
        if event.intent_id
        else None
    )
    if payment is not None:
        _apply(event.kind, payment)

    stored.processed_at = timezone.now()
    stored.save(update_fields=["processed_at", "updated_at"])
    return True


def _apply(kind: EventKind, payment: Payment) -> None:
    if kind == EventKind.PAYMENT_SUCCEEDED:
        _settle(payment)
    elif kind == EventKind.PAYMENT_FAILED:
        # Porażka po sukcesie to spóźnione zdarzenie, nie zmiana zdania.
        if payment.status == PaymentStatus.PENDING:
            _set_status(payment, PaymentStatus.FAILED)
    elif kind == EventKind.REFUNDED:
        _complete_refund(payment)
    elif kind == EventKind.REFUND_FAILED:
        _set_status(payment, PaymentStatus.REFUND_FAILED)


def _settle(payment: Payment) -> None:
    """Zapłata doszła do skutku: zamówienie `paid`, towar schodzi ze stanu.

    Intencja nieudana może jeszcze zostać opłacona tą samą intencją, więc
    rozlicza się także z `failed`. Zamówienie, które nie czeka już na
    zapłatę (opłacone inną próbą, anulowane po terminie), oddaje pieniądze —
    sklep nie zatrzymuje wpłaty, za którą nic nie wyśle.
    """
    if payment.status not in (PaymentStatus.PENDING, PaymentStatus.FAILED):
        return
    _set_status(payment, PaymentStatus.SUCCEEDED)

    order = Order.objects.select_for_update().get(pk=payment.order_id)  # type: ignore[missing-attribute]
    if order.status != OrderStatus.PENDING:
        _refund(payment, RefundReason.ORDER_CLOSED)
        return

    try:
        # Punkt zapisu: rozliczenie części pozycji przed odmową przy
        # kolejnej musi się cofnąć, zanim pieniądze pójdą z powrotem.
        with transaction.atomic():
            _consume_stock(order)
    except ReservationError:
        _refund(payment, RefundReason.OUT_OF_STOCK)
        return

    order.transition_to(OrderStatus.PAID)


def _complete_refund(payment: Payment) -> None:
    """Pieniądze wróciły do klienta — teraz dopiero zamówienie się zamyka."""
    if payment.status == PaymentStatus.REFUNDED:
        return
    _set_status(payment, PaymentStatus.REFUNDED)

    order = Order.objects.select_for_update().get(pk=payment.order_id)  # type: ignore[missing-attribute]
    if payment.refund_reason == RefundReason.CANCELLATION:
        if not order.can_transition_to(OrderStatus.CANCELLED):
            return
        for reservation in order.reservations.filter(  # type: ignore[missing-attribute]
            status=ReservationStatus.CONSUMED
        ):
            restock(reservation, note=f"Anulowanie zamówienia {order.number}")
        order.transition_to(OrderStatus.CANCELLED)
    elif payment.refund_reason == RefundReason.OUT_OF_STOCK:
        if order.status != OrderStatus.PENDING:
            return
        _release_active(order)
        order.transition_to(OrderStatus.CANCELLED)


def _refund(payment: Payment, reason: str) -> None:
    refund_id = get_provider().refund(
        payment.intent_id, idempotency_key=f"refund-{payment.intent_id}"
    )
    payment.status = PaymentStatus.REFUNDING
    payment.refund_reason = reason
    payment.refund_id = refund_id
    payment.save(update_fields=["status", "refund_reason", "refund_id", "updated_at"])


def _set_status(payment: Payment, status: str) -> None:
    payment.status = status
    payment.save(update_fields=["status", "updated_at"])


def _needed_stock(order: Order) -> Counter[int]:
    """Ilości do zdjęcia ze stanu według wariantu; wyrób na zamówienie pomija."""
    needed: Counter[int] = Counter()
    for item in order.items.all():  # type: ignore[missing-attribute]
        if not item.is_made_to_order:
            needed[item.variant_id] += item.quantity * item.specimen_count  # type: ignore[missing-attribute]
    return needed


def _release_active(order: Order) -> None:
    for reservation in order.reservations.filter(  # type: ignore[missing-attribute]
        status=ReservationStatus.ACTIVE
    ):
        release(reservation)


def _renew_reservations(order: Order) -> None:
    """Zwalnia rezerwacje zamówienia i zakłada je od nowa na pełny czas.

    W jednej transakcji: własne zwolnione sztuki wracają do puli, z której
    zaraz bierze nowa rezerwacja, więc klient nie traci ich na rzecz innego.
    Odmowa znaczy, że po wygaśnięciu ktoś kupił towar — wtedy zapłaty nie
    zaczynamy.
    """
    _release_active(order)
    items = order.items.select_related("variant__product")  # type: ignore[missing-attribute]
    for item in items:
        try:
            reserve(item.variant, item.quantity * item.specimen_count, order=order)
        except ReservationError as error:
            raise PaymentError({"items": str(error)}) from error


def _consume_stock(order: Order) -> None:
    """Rozlicza rezerwacje ruchem sprzedaży.

    Rezerwacja wygasła, zanim zdarzenie doszło (np. długie uwierzytelnienie
    u banku) — próbujemy wziąć towar od nowa. Jeśli już go nie ma,
    `ReservationError` wychodzi na zewnątrz i pieniądze wracają.
    """
    needed = _needed_stock(order)
    for reservation in order.reservations.filter(  # type: ignore[missing-attribute]
        status=ReservationStatus.ACTIVE
    ).select_related("variant__product"):
        if reservation.is_active:
            consume(reservation)
            needed[reservation.variant_id] -= reservation.quantity
        else:
            release(reservation)

    variants = {
        item.variant_id: item.variant  # type: ignore[missing-attribute]
        for item in order.items.select_related("variant__product")  # type: ignore[missing-attribute]
    }
    for variant_id, quantity in needed.items():
        if quantity > 0:
            reservation = reserve(variants[variant_id], quantity, order=order)
            if reservation is not None:
                consume(reservation)
