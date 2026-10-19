from __future__ import annotations

from factory.declarations import Sequence, SubFactory
from factory.django import DjangoModelFactory

from apps.shipping.models import (
    Shipment,
    ShippingMethod,
    ShippingMethodKind,
    ShippingZone,
)


class ShippingMethodFactory(DjangoModelFactory):
    """Kurier krajowy bez limitu wartości — najprostsza metoda, jaka istnieje."""

    class Meta:
        model = ShippingMethod

    name = Sequence(lambda n: f"Kurier {n}")
    kind = ShippingMethodKind.COURIER
    zone = ShippingZone.PL
    rate = 1990
    currency = "PLN"
    max_order_value = None
    is_active = True


class ShipmentFactory(DjangoModelFactory):
    """Przesyłka wpisana ręcznie w panelu, jeszcze przed nadaniem (ADR 0027)."""

    class Meta:
        model = Shipment

    # Ścieżka tekstowa, bo `tests.factories.orders` sam importuje ten moduł.
    order = SubFactory("tests.factories.orders.OrderFactory")
    tracking_number = ""
    declared_value = 25000
    currency = "PLN"
