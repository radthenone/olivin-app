"""Reguły metody dostawy pilnowane przez model (`CONTEXT.md`, ShippingMethod)."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.shipping.models import ShippingMethod, ShippingMethodKind
from common.money import Money
from tests.factories.shipping import ParcelLockerMethodFactory, ShippingMethodFactory


@pytest.mark.django_db
class TestOdbiorOsobisty:
    def test_odbior_z_limitem_jest_odrzucony(self):
        with pytest.raises(ValidationError) as error:
            ShippingMethodFactory(
                kind=ShippingMethodKind.PICKUP, max_order_value=100000
            )

        assert "max_order_value" in error.value.message_dict

    def test_ograniczenie_w_bazie_lapie_zapis_z_pominieciem_walidacji(self):
        method = ShippingMethodFactory(kind=ShippingMethodKind.PARCEL_LOCKER)

        with pytest.raises(IntegrityError):
            ShippingMethod.objects.filter(pk=method.pk).update(
                kind=ShippingMethodKind.PICKUP, max_order_value=100000
            )


@pytest.mark.django_db
class TestKwoty:
    def test_stawka_wychodzi_jako_kwota_z_waluta(self):
        method = ShippingMethodFactory(rate=1990, currency="PLN")

        assert method.rate_money == Money(1990, "PLN")

    def test_brak_limitu_to_brak_kwoty_a_nie_zero(self):
        without_limit = ShippingMethodFactory(max_order_value=None)
        with_limit = ParcelLockerMethodFactory(max_order_value=500000)

        assert without_limit.max_order_value_money is None
        assert with_limit.max_order_value_money == Money(500000, "PLN")
