"""Reguły metody dostawy pilnowane przez model (`CONTEXT.md`, ShippingMethod)."""

from __future__ import annotations

import pytest

from apps.shipping.models import Shipment, ShippingMethodKind
from common.money import Money
from tests.factories.shipping import ShippingMethodFactory


class TestCourierOnly:
    """Wysyłka wyłącznie kurierem (ADR 0036)."""

    def test_only_courier_and_eu_kinds_exist(self):
        """Rodzaje metody dostawy to tylko kurier krajowy i przesyłka do Unii."""
        assert set(ShippingMethodKind.values) == {"courier", "eu"}

    def test_shipment_has_no_pickup_point(self):
        """Przesyłka nie ma kodu punktu odbioru."""
        field_names = {field.name for field in Shipment._meta.get_fields()}

        assert "pickup_point_code" not in field_names


@pytest.mark.django_db
class TestAmounts:
    """Kwoty metody dostawy."""

    def test_rate_is_money_with_currency(self):
        """Stawka wychodzi jako kwota z walutą."""
        method = ShippingMethodFactory(rate=1990, currency="PLN")

        assert method.rate_money == Money(1990, "PLN")

    def test_missing_limit_is_none_not_zero(self):
        """Brak limitu to brak kwoty, a nie zero."""
        without_limit = ShippingMethodFactory(max_order_value=None)
        with_limit = ShippingMethodFactory(max_order_value=500000)

        assert without_limit.max_order_value_money is None
        assert with_limit.max_order_value_money == Money(500000, "PLN")
