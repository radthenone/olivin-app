"""Zapłata, zdarzenia operatora i zwrot (`CONTEXT.md`, Payment; ADR 0012)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.inventory.models import (
    InventoryItem,
    Reservation,
    ReservationStatus,
    StockMovementReason,
)
from apps.orders.models import OrderStatus
from apps.orders.services import cancel_order
from apps.payments.models import Payment, PaymentStatus, RefundReason, WebhookEvent
from apps.payments.services import (
    PaymentError,
    handle_event,
    request_cancellation,
    start_payment,
)
from core.integrations.payments import EventKind, ProviderEvent
from tests.factories.inventory import ReservationFactory
from tests.payments.helpers import placed_order


def _event(kind: EventKind, intent_id: str, event_id: str = "") -> ProviderEvent:
    return ProviderEvent(
        id=event_id or f"evt_{kind}_{intent_id}",
        kind=kind,
        type=str(kind),
        intent_id=intent_id,
    )


def _available(order) -> int:
    variant = order.items.get().variant
    return InventoryItem.objects.get(variant=variant).available


def _on_hand(order) -> int:
    variant = order.items.get().variant
    return InventoryItem.objects.get(variant=variant).on_hand


def _paid_order(**kwargs):
    order = placed_order(**kwargs)
    started = start_payment(order)
    handle_event(_event(EventKind.PAYMENT_SUCCEEDED, started.payment.intent_id))
    order.refresh_from_db()
    return order, started.payment


@pytest.mark.django_db
class TestStartPayment:
    """Rozpoczęcie zapłaty za zamówienie."""

    def test_intent_for_order_amount(self, fake_payment_provider):
        """Intencja jest na kwotę z zamówienia."""
        order = placed_order(quantity=2)

        started = start_payment(order)

        assert started.client_secret
        assert started.payment.amount == order.total.amount
        assert started.payment.currency == "PLN"
        assert started.payment.status == PaymentStatus.PENDING
        intent = fake_payment_provider.intents[0]
        assert intent["amount"] == order.total.amount
        assert intent["reference"] == order.number

    def test_next_attempt_creates_new_payment(self, fake_payment_provider):
        """Kolejna próba tworzy nową płatność."""
        order = placed_order()

        first = start_payment(order)
        second = start_payment(order)

        assert first.payment.pk != second.payment.pk
        assert first.payment.intent_id != second.payment.intent_id
        assert Payment.objects.filter(order=order).count() == 2
        keys = {intent["idempotency_key"] for intent in fake_payment_provider.intents}
        assert len(keys) == 2

    def test_attempt_renews_reservations_instead_of_duplicating(self):
        """Próba odnawia rezerwacje zamiast ich dublować."""
        order = placed_order(quantity=2, on_hand=5)

        start_payment(order)
        start_payment(order)

        active = Reservation.objects.filter(order=order).filter(
            status=ReservationStatus.ACTIVE
        )
        assert active.count() == 1
        assert active.get().quantity == 2
        assert _available(order) == 3

    def test_expired_reservation_returns_to_full_half_hour(self):
        """Rezerwacja po terminie wraca na pełne pół godziny."""
        order = placed_order()
        Reservation.objects.filter(order=order).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        start_payment(order)

        active = Reservation.objects.filter(order=order).get(
            status=ReservationStatus.ACTIVE
        )
        assert active.expires_at > timezone.now() + timedelta(minutes=29)

    def test_goods_sold_after_expiry_block_payment(self):
        """Towar wykupiony po wygaśnięciu blokuje zapłatę."""
        order = placed_order(quantity=1, on_hand=1)
        reservation = Reservation.objects.filter(order=order).get()
        reservation.expires_at = timezone.now() - timedelta(minutes=1)
        reservation.save()
        ReservationFactory(variant=reservation.variant, quantity=1)

        with pytest.raises(PaymentError) as error:
            start_payment(order)

        assert "items" in error.value.message_dict
        assert not Payment.objects.exists()

    def test_non_pending_order_is_rejected(self):
        """Zamówienie inne niż `pending` jest odrzucane."""
        order = placed_order()
        cancel_order(order)

        with pytest.raises(PaymentError) as error:
            start_payment(order)

        assert "status" in error.value.message_dict

    def test_provider_refusal_leaves_no_payment(self, fake_payment_provider):
        """Odmowa operatora nie zostawia płatności."""
        order = placed_order()
        fake_payment_provider.fail_with = "timeout"

        with pytest.raises(PaymentError) as error:
            start_payment(order)

        assert "payment" in error.value.message_dict
        assert not Payment.objects.exists()


@pytest.mark.django_db
class TestPaymentEvent:
    """Zdarzenie zapłaty od operatora."""

    def test_success_moves_order_to_paid_and_takes_stock(self):
        """Sukces przenosi zamówienie do `paid` i zdejmuje stan."""
        order = placed_order(quantity=2, on_hand=5)
        started = start_payment(order)

        processed = handle_event(
            _event(EventKind.PAYMENT_SUCCEEDED, started.payment.intent_id)
        )

        order.refresh_from_db()
        started.payment.refresh_from_db()
        assert processed is True
        assert order.status == OrderStatus.PAID
        assert started.payment.status == PaymentStatus.SUCCEEDED
        assert (
            Reservation.objects.filter(order=order)
            .filter(status=ReservationStatus.CONSUMED)
            .count()
            == 1
        )
        assert _on_hand(order) == 3
        assert _available(order) == 3

    def test_same_event_twice_changes_nothing(self):
        """To samo zdarzenie drugi raz nic nie zmienia."""
        order = placed_order(quantity=1, on_hand=5)
        started = start_payment(order)
        event = _event(EventKind.PAYMENT_SUCCEEDED, started.payment.intent_id)

        assert handle_event(event) is True
        assert handle_event(event) is False

        assert WebhookEvent.objects.count() == 1
        assert _on_hand(order) == 4

    def test_failure_keeps_order_pending(self):
        """Porażka zostawia zamówienie w `pending`."""
        order = placed_order()
        started = start_payment(order)

        handle_event(_event(EventKind.PAYMENT_FAILED, started.payment.intent_id))

        order.refresh_from_db()
        started.payment.refresh_from_db()
        assert order.status == OrderStatus.PENDING
        assert started.payment.status == PaymentStatus.FAILED
        assert (
            Reservation.objects.filter(order=order)
            .filter(status=ReservationStatus.ACTIVE)
            .count()
            == 1
        )

    def test_success_after_failure_of_same_intent_settles(self):
        """Sukces po porażce tej samej intencji rozlicza zamówienie."""
        order = placed_order()
        started = start_payment(order)
        intent_id = started.payment.intent_id

        handle_event(_event(EventKind.PAYMENT_FAILED, intent_id))
        handle_event(_event(EventKind.PAYMENT_SUCCEEDED, intent_id))

        order.refresh_from_db()
        assert order.status == OrderStatus.PAID

    def test_expired_reservation_takes_goods_again(self):
        """Rezerwacja po terminie bierze towar od nowa."""
        order = placed_order(quantity=1, on_hand=3)
        started = start_payment(order)
        Reservation.objects.filter(order=order).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        handle_event(_event(EventKind.PAYMENT_SUCCEEDED, started.payment.intent_id))

        order.refresh_from_db()
        assert order.status == OrderStatus.PAID
        assert _on_hand(order) == 2

    def test_missing_goods_at_settlement_refunds_money(self, fake_payment_provider):
        """Brak towaru przy rozliczeniu oddaje pieniądze."""
        order = placed_order(quantity=1, on_hand=1)
        started = start_payment(order)
        reservation = Reservation.objects.filter(order=order).get(
            status=ReservationStatus.ACTIVE
        )
        reservation.expires_at = timezone.now() - timedelta(minutes=1)
        reservation.save()
        ReservationFactory(variant=reservation.variant, quantity=1)

        handle_event(_event(EventKind.PAYMENT_SUCCEEDED, started.payment.intent_id))

        order.refresh_from_db()
        started.payment.refresh_from_db()
        assert order.status == OrderStatus.PENDING
        assert started.payment.status == PaymentStatus.REFUNDING
        assert started.payment.refund_reason == RefundReason.OUT_OF_STOCK
        assert _on_hand(order) == 1
        assert fake_payment_provider.refunds[0]["intent_id"] == (
            started.payment.intent_id
        )

        handle_event(_event(EventKind.REFUNDED, started.payment.intent_id))

        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED

    def test_second_payment_for_paid_order_is_refunded(self, fake_payment_provider):
        """Druga wpłata na opłacone zamówienie wraca do klienta."""
        order = placed_order()
        first = start_payment(order)
        second = start_payment(order)

        handle_event(_event(EventKind.PAYMENT_SUCCEEDED, first.payment.intent_id))
        handle_event(_event(EventKind.PAYMENT_SUCCEEDED, second.payment.intent_id))
        handle_event(_event(EventKind.REFUNDED, second.payment.intent_id))

        order.refresh_from_db()
        second.payment.refresh_from_db()
        assert order.status == OrderStatus.PAID
        assert second.payment.status == PaymentStatus.REFUNDED
        assert second.payment.refund_reason == RefundReason.ORDER_CLOSED
        assert _on_hand(order) == 4

    def test_event_of_unknown_intent_is_stored_and_skipped(self):
        """Zdarzenie obcej intencji jest zapisane i pominięte."""
        processed = handle_event(_event(EventKind.PAYMENT_SUCCEEDED, "pi_obca"))

        assert processed is True
        assert WebhookEvent.objects.get().processed_at is not None


@pytest.mark.django_db
class TestCancelPaidOrder:
    """Anulowanie opłaconego zamówienia przez zwrot."""

    def test_refund_at_provider_status_waits_for_event(self, fake_payment_provider):
        """Zwrot idzie do operatora, a status czeka na zdarzenie."""
        order, payment = _paid_order()

        request_cancellation(order)

        order.refresh_from_db()
        payment.refresh_from_db()
        assert order.status == OrderStatus.PAID
        assert payment.status == PaymentStatus.REFUNDING
        assert payment.refund_reason == RefundReason.CANCELLATION
        assert fake_payment_provider.refunds[0]["intent_id"] == payment.intent_id

    def test_refund_event_cancels_and_restores_stock_by_movement(self):
        """Zdarzenie zwrotu anuluje zamówienie i przywraca stan ruchem."""
        order, payment = _paid_order(quantity=2, on_hand=5)
        request_cancellation(order)

        handle_event(_event(EventKind.REFUNDED, payment.intent_id))

        order.refresh_from_db()
        payment.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED
        assert payment.status == PaymentStatus.REFUNDED
        assert _on_hand(order) == 5
        item = InventoryItem.objects.get(variant=order.items.get().variant)
        reasons = list(item.movements.values_list("reason", flat=True))
        assert StockMovementReason.RETURN in reasons

    def test_repeated_refund_event_does_not_duplicate_movement(self):
        """Powtórzone zdarzenie zwrotu nie dubluje ruchu."""
        order, payment = _paid_order(quantity=1, on_hand=5)
        request_cancellation(order)
        event = _event(EventKind.REFUNDED, payment.intent_id, "evt_refund")

        handle_event(event)
        handle_event(_event(EventKind.REFUNDED, payment.intent_id, "evt_refund_2"))

        assert _on_hand(order) == 5

    def test_second_cancellation_during_refund_is_rejected(self):
        """Drugie anulowanie w toku zwrotu jest odrzucane."""
        order, _ = _paid_order()
        request_cancellation(order)

        with pytest.raises(PaymentError):
            request_cancellation(order)

    def test_failed_refund_keeps_order_paid(self):
        """Nieudany zwrot zostawia zamówienie opłacone."""
        order, payment = _paid_order()
        request_cancellation(order)

        handle_event(_event(EventKind.REFUND_FAILED, payment.intent_id))

        order.refresh_from_db()
        payment.refresh_from_db()
        assert order.status == OrderStatus.PAID
        assert payment.status == PaymentStatus.REFUND_FAILED

    def test_rejected_refund_can_be_retried_with_new_key(self, fake_payment_provider):
        """Odrzucony zwrot można zlecić ponownie nowym kluczem."""
        order, payment = _paid_order(quantity=1, on_hand=5)
        request_cancellation(order)
        handle_event(_event(EventKind.REFUND_FAILED, payment.intent_id))

        request_cancellation(order)

        payment.refresh_from_db()
        assert payment.status == PaymentStatus.REFUNDING
        keys = [refund["idempotency_key"] for refund in fake_payment_provider.refunds]
        assert len(keys) == 2
        assert len(set(keys)) == 2

        handle_event(_event(EventKind.REFUNDED, payment.intent_id, "evt_refund_ok"))

        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED
        assert _on_hand(order) == 5

    def test_pending_order_skips_refund(self):
        """Zamówienie `pending` nie idzie przez zwrot."""
        order = placed_order()

        with pytest.raises(PaymentError):
            request_cancellation(order)
