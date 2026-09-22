"""Wybór metod dostawy dla wartości koszyka (`CONTEXT.md`, ShippingMethod)."""

from __future__ import annotations

import pytest

from apps.shipping.models import ShippingZone
from apps.shipping.services import available_methods, free_shipping_threshold
from common.money import Money
from tests.factories.shipping import (
    ParcelLockerMethodFactory,
    PickupMethodFactory,
    ShippingMethodFactory,
)


@pytest.mark.django_db
class TestLimitWartosci:
    """Metoda znika powyżej swojej górnej wartości zamówienia (ADR 0028)."""

    def test_paczkomat_znika_powyzej_swojego_limitu(self):
        ParcelLockerMethodFactory(name="Paczkomat", max_order_value=500000)
        ShippingMethodFactory(name="Kurier", max_order_value=None)

        offers = available_methods(order_value=Money(500001), zone=ShippingZone.PL)

        assert [offer.method.name for offer in offers] == ["Kurier"]

    def test_wartosc_rowna_limitowi_jeszcze_przechodzi(self):
        ParcelLockerMethodFactory(name="Paczkomat", max_order_value=500000)

        offers = available_methods(order_value=Money(500000), zone=ShippingZone.PL)

        assert [offer.method.name for offer in offers] == ["Paczkomat"]

    def test_dwie_metody_kurierskie_z_roznymi_progami(self):
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

    def test_odbior_osobisty_nie_ma_limitu(self):
        PickupMethodFactory(name="Odbiór w pracowni")

        offers = available_methods(order_value=Money(10_000_000), zone=ShippingZone.PL)

        assert [offer.method.name for offer in offers] == ["Odbiór w pracowni"]


@pytest.mark.django_db
class TestStrefaIAktywnosc:
    def test_metoda_z_innej_strefy_nie_wychodzi(self):
        ShippingMethodFactory(name="Kurier PL", zone=ShippingZone.PL)
        ShippingMethodFactory(name="Kurier UE", zone=ShippingZone.EU)

        offers = available_methods(order_value=Money(10000), zone=ShippingZone.EU)

        assert [offer.method.name for offer in offers] == ["Kurier UE"]

    def test_metoda_wylaczona_nie_wychodzi(self):
        ShippingMethodFactory(name="Wygaszony kurier", is_active=False)

        offers = available_methods(order_value=Money(10000), zone=ShippingZone.PL)

        assert offers == []


@pytest.mark.django_db
class TestDarmowaDostawa:
    """Jeden próg dla całego sklepu — ustawienie `FREE_SHIPPING_THRESHOLD`."""

    def test_powyzej_progu_koszt_schodzi_do_zera(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = 50000
        ShippingMethodFactory(name="Kurier", rate=1990)

        offers = available_methods(order_value=Money(50000), zone=ShippingZone.PL)

        assert offers[0].cost == Money(0)

    def test_ponizej_progu_klient_placi_stawke(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = 50000
        ShippingMethodFactory(name="Kurier", rate=1990)

        offers = available_methods(order_value=Money(49999), zone=ShippingZone.PL)

        assert offers[0].cost == Money(1990)

    def test_brak_progu_oznacza_brak_darmowej_dostawy(self, settings):
        settings.FREE_SHIPPING_THRESHOLD = None
        ShippingMethodFactory(name="Kurier", rate=1990)

        offers = available_methods(order_value=Money(10_000_000), zone=ShippingZone.PL)

        assert offers[0].cost == Money(1990)

    def test_prog_nie_dziala_w_obcej_walucie(self, settings):
        """Próg jest złotowy — nie wolno go czytać jako tej samej liczby w euro."""
        settings.FREE_SHIPPING_THRESHOLD = 50000

        assert free_shipping_threshold() == Money(50000, "PLN")


@pytest.mark.django_db
class TestWaluta:
    """Metoda w innej walucie niż koszyk nie jest błędem, tylko ofertą nie do złożenia."""

    def test_metoda_w_obcej_walucie_nie_wychodzi_zamiast_wysadzac_odczyt(self):
        ShippingMethodFactory(name="Kurier EUR", currency="EUR", rate=990)
        ShippingMethodFactory(name="Kurier PLN", currency="PLN", rate=1990)

        offers = available_methods(
            order_value=Money(10000, "PLN"), zone=ShippingZone.PL
        )

        assert [offer.method.name for offer in offers] == ["Kurier PLN"]

    def test_ujemna_wartosc_koszyka_jest_bledem_programu(self):
        with pytest.raises(ValueError):
            available_methods(order_value=Money(-1), zone=ShippingZone.PL)
