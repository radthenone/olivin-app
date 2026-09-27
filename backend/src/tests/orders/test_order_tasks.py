"""Zamówienie bez zapłaty przez dobę anuluje się samo (`CONTEXT.md`, Order)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.inventory.models import ReservationStatus
from apps.orders.models import UNPAID_ORDER_TTL, Order, OrderStatus
from apps.orders.tasks import cancel_stale_orders
from tests.factories.inventory import ReservationFactory
from tests.factories.orders import OrderFactory
from tests.factories.products import ProductVariantFactory, stock


def _placed_ago(order: Order, delta: timedelta) -> Order:
    Order.objects.filter(pk=order.pk).update(created_at=timezone.now() - delta)
    return order


@pytest.mark.django_db
class TestAnulowaniaNieoplaconych:
    def test_nieoplacone_po_dobie_jest_anulowane_i_zwalnia_rezerwacje(self):
        order = OrderFactory()
        variant = ProductVariantFactory()
        stock(variant, 5)
        reservation = ReservationFactory(variant=variant, quantity=2, order=order)
        _placed_ago(order, UNPAID_ORDER_TTL + timedelta(minutes=1))

        assert cancel_stale_orders() == 1  # type: ignore[missing-argument]

        order.refresh_from_db()
        reservation.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED
        assert reservation.status == ReservationStatus.RELEASED

    def test_swieze_zamowienie_zostaje(self):
        order = OrderFactory()

        assert cancel_stale_orders() == 0  # type: ignore[missing-argument]

        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING

    def test_oplacone_nie_jest_ruszane(self):
        """Zadanie pilnuje wyłącznie nieopłaconych — opłacone czeka na realizację."""
        order = OrderFactory()
        order.transition_to(OrderStatus.PAID)
        _placed_ago(order, UNPAID_ORDER_TTL * 10)

        assert cancel_stale_orders() == 0  # type: ignore[missing-argument]

        order.refresh_from_db()
        assert order.status == OrderStatus.PAID
