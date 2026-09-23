"""Wybór metod dostawy dla wartości koszyka (`CONTEXT.md`, ShippingMethod)."""

from __future__ import annotations

import pytest

from apps.shipping.models import ShippingZone
from apps.shipping.services import (
    available_methods,
    free_shipping_threshold,
    zone_for_country,
)
from common.money import Money
from tests.factories.shipping import (
    ParcelLockerMethodFactory,
    PickupMethodFactory,
    ShippingMethodFactory,
)


@pytest.mark.django_db
class TestValueLimit:
    """Metoda znika powyżej swojej górnej wartości zamówienia (ADR 0028)."""

    def test_parcel_locker_disappears_above_its_limit(self):
        ParcelLockerMethodFactory(name="Paczkomat", max_order_value=500000)
        ShippingMethodFactory(name="Kurier", max_order_value=None)

        offers = available_methods(order_value=Money(500001), zone=ShippingZone.PL)

        assert [offer.method.name for offer in offers] == ["Kurier"]

    def test_value_equal_to_limit_still_passes(self):
        ParcelLockerMethodFactory(name="Paczkomat", max_order_value=500000)

        offers = available_methods(order_value=Money(500000), zone=ShippingZone.PL)

        assert [offer.method.name for offer in offers] == ["Paczkomat"]

    def test_two_courier_methods_with_different_limits(self):
        ShippingMethodFactory(name="Kurier standard", rate=1990, max_order_value=300000)
        ShippingMethodFactory(
            name="Kurier z deklaracją", rate=3490, max_order_value=None
        )

        cheap = available_methods(order_value=Money(200000), zone=ShippingZone.PL)
        expensive = available_methods(order_value=Money(900000), zone=ShippingZone.PL)

        assert {offer.method.name for offer in cheap} == {
            "Kurier standard",
            "Kurier z deklaracją",
        }
        assert [offer.method.name for offer in expensive] == ["Kurier z deklaracją"]

    def test_pickup_has_no_limit(self):
        PickupMethodFactory(name="Odbiór w pracowni")

        offers = available_methods(order_value=Money(10_000_000), zone=ShippingZone.PL)

        assert [offer.method.name for offer in offers] == ["Odbiór w pracowni"]


@pytest.mark.django_db
class TestZoneAndActivity:
    def test_method_from_other_zone_is_excluded(self):
        ShippingMethodFactory(name="Kurier PL", zone=ShippingZone.PL)
        ShippingMethodFactory(name="Kurier UE", zone=ShippingZone.EU)

        offers = available_methods(order_value=Money(10000), zone=ShippingZone.EU)

        assert [offer.method.name for offer in offers] == ["Kurier UE"]

    def test_inactive_method_is_excluded(self):
        ShippingMethodFactory(name="Wygaszony kurier", is_active=False)

        offers = available_methods(order_value=Money(10000), zone=ShippingZone.PL)

        assert offers == []


@pytest.mark.django_db
class TestFreeShipping:
    """Jeden próg dla całego sklepu — ustawienie `FREE_SHIPPING_THRESHOLD`."""

    def test_above_threshold_cost_drops_to_zero(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = 50000
        ShippingMethodFactory(name="Kurier", rate=1990)

        offers = available_methods(order_value=Money(50000), zone=ShippingZone.PL)

        assert offers[0].cost == Money(0)

    def test_below_threshold_customer_pays_rate(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = 50000
        ShippingMethodFactory(name="Kurier", rate=1990)

        offers = available_methods(order_value=Money(49999), zone=ShippingZone.PL)

        assert offers[0].cost == Money(1990)

    def test_no_threshold_means_no_free_shipping(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = None
        ShippingMethodFactory(name="Kurier", rate=1990)

        offers = available_methods(order_value=Money(10_000_000), zone=ShippingZone.PL)

        assert offers[0].cost == Money(1990)

    def test_threshold_ignored_in_foreign_currency(self, settings):
        """Próg jest złotowy — nie wolno go czytać jako tej samej liczby w euro."""
        settings.FREE_SHIPPING_THRESHOLD = 50000

        assert free_shipping_threshold() == Money(50000, "PLN")


@pytest.mark.django_db
class TestCurrency:
    """Metoda w innej walucie niż koszyk nie jest błędem, tylko ofertą nie do złożenia."""

    def test_foreign_currency_method_is_excluded_instead_of_crashing(self):
        ShippingMethodFactory(name="Kurier EUR", currency="EUR", rate=990)
        ShippingMethodFactory(name="Kurier PLN", currency="PLN", rate=1990)

        offers = available_methods(
            order_value=Money(10000, "PLN"), zone=ShippingZone.PL
        )

        assert [offer.method.name for offer in offers] == ["Kurier PLN"]

    def test_negative_cart_value_is_programming_error(self):
        with pytest.raises(ValueError):
            available_methods(order_value=Money(-1), zone=ShippingZone.PL)


class TestZoneForCountry:
    def test_poland_is_domestic_zone(self):
        assert zone_for_country("PL") == ShippingZone.PL

    def test_eu_country_is_eu_zone(self):
        assert zone_for_country("DE") == ShippingZone.EU

    def test_non_eu_country_has_no_zone(self):
        assert zone_for_country("US") is None
