"""Reguły metody dostawy pilnowane przez model (`CONTEXT.md`, ShippingMethod)."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.shipping.models import ShippingMethod, ShippingMethodKind
from common.money import Money
from tests.factories.shipping import ParcelLockerMethodFactory, ShippingMethodFactory


@pytest.mark.django_db
class TestPickup:
    """Odbiór osobisty."""

    def test_pickup_with_limit_is_rejected(self):
        """Odbiór osobisty z limitem wartości jest odrzucany."""
        with pytest.raises(ValidationError) as error:
            ShippingMethodFactory(
                kind=ShippingMethodKind.PICKUP, max_order_value=100000
            )

        assert "max_order_value" in error.value.message_dict

    def test_database_constraint_catches_unvalidated_save(self):
        """Ograniczenie w bazie łapie zapis z pominięciem walidacji."""
        method = ShippingMethodFactory(kind=ShippingMethodKind.PARCEL_LOCKER)

        with pytest.raises(IntegrityError):
            ShippingMethod.objects.filter(pk=method.pk).update(
                kind=ShippingMethodKind.PICKUP, max_order_value=100000
            )


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
        with_limit = ParcelLockerMethodFactory(max_order_value=500000)

        assert without_limit.max_order_value_money is None
        assert with_limit.max_order_value_money == Money(500000, "PLN")
