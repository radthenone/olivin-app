"""`GET /shipping-methods/` na realnym kształcie odpowiedzi (camelCase)."""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.shipping.models import ShippingZone
from tests.factories.shipping import (
    ParcelLockerMethodFactory,
    PickupMethodFactory,
    ShippingMethodFactory,
)


def _url() -> str:
    return reverse("shipping-method-list")


@pytest.mark.django_db
class TestListaMetod:
    def test_anonim_dostaje_metody_z_kosztem(self, api_client: APIClient):
        ShippingMethodFactory(name="Kurier", rate=1990)

        response: Any = api_client.get(_url(), {"order_value": 10000})

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body == [
            {
                "id": body[0]["id"],
                "name": "Kurier",
                "kind": "courier",
                "zone": "PL",
                "cost": {"amount": 1990, "currency": "PLN"},
                "isFree": False,
            }
        ]

    def test_limit_wartosci_odsiewa_paczkomat(self, api_client: APIClient):
        ParcelLockerMethodFactory(name="Paczkomat", max_order_value=500000)
        ShippingMethodFactory(name="Kurier")

        response: Any = api_client.get(_url(), {"order_value": 600000})

        assert [row["name"] for row in response.json()] == ["Kurier"]

    def test_darmowa_dostawa_powyzej_progu(self, api_client: APIClient, settings):
        settings.FREE_SHIPPING_THRESHOLD = 50000
        ShippingMethodFactory(name="Kurier", rate=1990)

        response: Any = api_client.get(_url(), {"order_value": 50000})

        row = response.json()[0]
        assert row["cost"] == {"amount": 0, "currency": "PLN"}
        assert row["isFree"] is True

    def test_odbior_osobisty_wychodzi_przy_kazdej_wartosci(self, api_client: APIClient):
        PickupMethodFactory(name="Odbiór w pracowni")

        response: Any = api_client.get(_url(), {"order_value": 99_000_000})

        assert [row["name"] for row in response.json()] == ["Odbiór w pracowni"]

    def test_strefa_z_parametru(self, api_client: APIClient):
        ShippingMethodFactory(name="Kurier PL", zone=ShippingZone.PL)
        ShippingMethodFactory(name="Kurier UE", zone=ShippingZone.EU)

        response: Any = api_client.get(_url(), {"order_value": 10000, "zone": "EU"})

        assert [row["name"] for row in response.json()] == ["Kurier UE"]

    def test_bez_parametrow_strefa_jest_krajowa(self, api_client: APIClient):
        ShippingMethodFactory(name="Kurier PL", zone=ShippingZone.PL)
        ShippingMethodFactory(name="Kurier UE", zone=ShippingZone.EU)

        response: Any = api_client.get(_url())

        assert [row["name"] for row in response.json()] == ["Kurier PL"]

    def test_lista_nie_jest_stronicowana(self, api_client: APIClient):
        ShippingMethodFactory()

        response: Any = api_client.get(_url())

        assert isinstance(response.json(), list)


@pytest.mark.django_db
class TestNazwyParametrowZKlienta:
    """Schemat ogłasza `orderValue` — wygenerowany klient wysyła to samo.

    Zamianę robi `CamelCaseMiddleWare`; bez niej klient z Orvala pytałby o
    parametr, którego serializer nie czyta, i cicho dostawał pełen cennik.
    """

    def test_camel_case_z_wygenerowanego_klienta_dziala(self, api_client: APIClient):
        ParcelLockerMethodFactory(name="Paczkomat", max_order_value=500000)
        ShippingMethodFactory(name="Kurier")

        response: Any = api_client.get(_url(), {"orderValue": 600000})

        assert [row["name"] for row in response.json()] == ["Kurier"]


@pytest.mark.django_db
class TestWalidacjaParametrow:
    def test_ujemna_wartosc_zamowienia_jest_odrzucona(self, api_client: APIClient):
        response: Any = api_client.get(_url(), {"order_value": -1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "orderValue" in response.json()

    def test_nieznana_strefa_jest_odrzucona(self, api_client: APIClient):
        response: Any = api_client.get(_url(), {"zone": "US"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "zone" in response.json()


@pytest.mark.django_db
class TestBrakMutacji:
    """Metody dostawy prowadzi panel, nie API (ADR 0021)."""

    def test_post_nie_jest_obslugiwany(self, authenticated_client: APIClient):
        response: Any = authenticated_client.post(_url(), {"name": "Kurier"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
