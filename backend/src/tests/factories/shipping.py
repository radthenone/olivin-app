from __future__ import annotations

from factory.declarations import Sequence
from factory.django import DjangoModelFactory

from apps.shipping.models import ShippingMethod, ShippingMethodKind, ShippingZone


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


class ParcelLockerMethodFactory(ShippingMethodFactory):
    """Paczkomat: tani, ale z górną wartością zamówienia (ADR 0028)."""

    name = Sequence(lambda n: f"Paczkomat {n}")
    kind = ShippingMethodKind.PARCEL_LOCKER
    rate = 1490
    max_order_value = 500000


class PickupMethodFactory(ShippingMethodFactory):
    """Odbiór osobisty: bez kosztu i bez limitu — towar nie jedzie przewoźnikiem."""

    name = Sequence(lambda n: f"Odbiór osobisty {n}")
    kind = ShippingMethodKind.PICKUP
    rate = 0
    max_order_value = None
