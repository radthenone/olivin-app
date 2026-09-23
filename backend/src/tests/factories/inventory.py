from __future__ import annotations

from factory.declarations import LazyFunction, SubFactory
from factory.django import DjangoModelFactory
from django.utils import timezone

from apps.inventory.models import RESERVATION_TTL, Reservation, ReservationStatus
from tests.factories.products import ProductVariantFactory


class ReservationFactory(DjangoModelFactory):
    """Aktywna rezerwacja wygasająca za pół godziny — jak po rozpoczęciu zapłaty."""

    class Meta:
        model = Reservation

    variant = SubFactory(ProductVariantFactory)
    quantity = 1
    expires_at = LazyFunction(lambda: timezone.now() + RESERVATION_TTL)
    status = ReservationStatus.ACTIVE
