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
class TestRozpoczecieZaplaty:
    def test_intencja_na_kwote_z_zamowienia(self, fake_payment_provider):
        order = placed_order(quantity=2)

        started = start_payment(order)

        assert started.client_secret
        assert started.payment.amount == order.total.amount
        assert started.payment.currency == "PLN"
        assert started.payment.status == PaymentStatus.PENDING
        intent = fake_payment_provider.intents[0]
        assert intent["amount"] == order.total.amount
        assert intent["reference"] == order.number

    def test_kolejna_proba_tworzy_nowa_platnosc(self, fake_payment_provider):
        order = placed_order()

        first = start_payment(order)
        second = start_payment(order)

        assert first.payment.pk != second.payment.pk
        assert first.payment.intent_id != second.payment.intent_id
        assert Payment.objects.filter(order=order).count() == 2
        keys = {intent["idempotency_key"] for intent in fake_payment_provider.intents}
        assert len(keys) == 2

    def test_proba_odnawia_rezerwacje_zamiast_ich_dublowac(self):
        order = placed_order(quantity=2, on_hand=5)

        start_payment(order)
        start_payment(order)

        active = Reservation.objects.filter(order=order).filter(
            status=ReservationStatus.ACTIVE
        )
        assert active.count() == 1
        assert active.get().quantity == 2
        assert _available(order) == 3

    def test_rezerwacja_po_terminie_wraca_na_pelne_pol_godziny(self):
        order = placed_order()
        Reservation.objects.filter(order=order).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        start_payment(order)

        active = Reservation.objects.filter(order=order).get(
            status=ReservationStatus.ACTIVE
        )
        assert active.expires_at > timezone.now() + timedelta(minutes=29)

    def test_towar_wykupiony_po_wygasnieciu_blokuje_zaplate(self):
        order = placed_order(quantity=1, on_hand=1)
        reservation = Reservation.objects.filter(order=order).get()
        reservation.expires_at = timezone.now() - timedelta(minutes=1)
        reservation.save()
        ReservationFactory(variant=reservation.variant, quantity=1)

        with pytest.raises(PaymentError) as error:
            start_payment(order)

        assert "items" in error.value.message_dict
        assert not Payment.objects.exists()

    def test_zamowienie_nie_pending_jest_odrzucone(self):
        order = placed_order()
        cancel_order(order)

        with pytest.raises(PaymentError) as error:
            start_payment(order)

        assert "status" in error.value.message_dict

    def test_odmowa_operatora_nie_zostawia_platnosci(self, fake_payment_provider):
        order = placed_order()
        fake_payment_provider.fail_with = "timeout"

        with pytest.raises(PaymentError) as error:
            start_payment(order)

        assert "payment" in error.value.message_dict
        assert not Payment.objects.exists()


@pytest.mark.django_db
class TestZdarzenieZaplaty:
    def test_sukces_przenosi_zamowienie_do_paid_i_zdejmuje_stan(self):
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

    def test_to_samo_zdarzenie_drugi_raz_nic_nie_zmienia(self):
        order = placed_order(quantity=1, on_hand=5)
        started = start_payment(order)
        event = _event(EventKind.PAYMENT_SUCCEEDED, started.payment.intent_id)

        assert handle_event(event) is True
        assert handle_event(event) is False

        assert WebhookEvent.objects.count() == 1
        assert _on_hand(order) == 4

    def test_porazka_zostawia_zamowienie_pending(self):
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

    def test_sukces_po_porazce_tej_samej_intencji_rozlicza(self):
        order = placed_order()
        started = start_payment(order)
        intent_id = started.payment.intent_id

        handle_event(_event(EventKind.PAYMENT_FAILED, intent_id))
        handle_event(_event(EventKind.PAYMENT_SUCCEEDED, intent_id))

        order.refresh_from_db()
        assert order.status == OrderStatus.PAID

    def test_rezerwacja_po_terminie_bierze_towar_od_nowa(self):
        order = placed_order(quantity=1, on_hand=3)
        started = start_payment(order)
        Reservation.objects.filter(order=order).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        handle_event(_event(EventKind.PAYMENT_SUCCEEDED, started.payment.intent_id))

        order.refresh_from_db()
        assert order.status == OrderStatus.PAID
        assert _on_hand(order) == 2

    def test_brak_towaru_przy_rozliczeniu_oddaje_pieniadze(self, fake_payment_provider):
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

    def test_druga_wplata_na_oplacone_zamowienie_wraca(self, fake_payment_provider):
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

    def test_zdarzenie_obcej_intencji_jest_zapisane_i_pominiete(self):
        processed = handle_event(_event(EventKind.PAYMENT_SUCCEEDED, "pi_obca"))

        assert processed is True
        assert WebhookEvent.objects.get().processed_at is not None


@pytest.mark.django_db
class TestAnulowanieOplaconego:
    def test_zwrot_u_operatora_a_status_czeka_na_zdarzenie(self, fake_payment_provider):
        order, payment = _paid_order()

        request_cancellation(order)

        order.refresh_from_db()
        payment.refresh_from_db()
        assert order.status == OrderStatus.PAID
        assert payment.status == PaymentStatus.REFUNDING
        assert payment.refund_reason == RefundReason.CANCELLATION
        assert fake_payment_provider.refunds[0]["intent_id"] == payment.intent_id

    def test_zdarzenie_zwrotu_anuluje_i_przywraca_stan_ruchem(self):
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

    def test_powtorzone_zdarzenie_zwrotu_nie_dubluje_ruchu(self):
        order, payment = _paid_order(quantity=1, on_hand=5)
        request_cancellation(order)
        event = _event(EventKind.REFUNDED, payment.intent_id, "evt_refund")

        handle_event(event)
        handle_event(_event(EventKind.REFUNDED, payment.intent_id, "evt_refund_2"))

        assert _on_hand(order) == 5

    def test_drugie_anulowanie_w_toku_zwrotu_jest_odrzucone(self):
        order, _ = _paid_order()
        request_cancellation(order)

        with pytest.raises(PaymentError):
            request_cancellation(order)

    def test_nieudany_zwrot_zostawia_zamowienie_oplacone(self):
        order, payment = _paid_order()
        request_cancellation(order)

        handle_event(_event(EventKind.REFUND_FAILED, payment.intent_id))

        order.refresh_from_db()
        payment.refresh_from_db()
        assert order.status == OrderStatus.PAID
        assert payment.status == PaymentStatus.REFUND_FAILED

    def test_zamowienie_pending_nie_idzie_przez_zwrot(self):
        order = placed_order()

        with pytest.raises(PaymentError):
            request_cancellation(order)
