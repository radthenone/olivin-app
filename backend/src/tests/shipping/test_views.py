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
class TestMethodList:
    """Lista metod dostawy."""

    def test_anonymous_gets_methods_with_cost(self, api_client: APIClient):
        """Anonim dostaje metody z kosztem."""
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

    def test_value_limit_filters_out_parcel_locker(self, api_client: APIClient):
        """Limit wartości odsiewa paczkomat."""
        ParcelLockerMethodFactory(name="Paczkomat", max_order_value=500000)
        ShippingMethodFactory(name="Kurier")

        response: Any = api_client.get(_url(), {"order_value": 600000})

        assert [row["name"] for row in response.json()] == ["Kurier"]

    def test_free_shipping_above_threshold(self, api_client: APIClient, settings):
        """Darmowa dostawa powyżej progu."""
        settings.FREE_SHIPPING_THRESHOLD = 50000
        ShippingMethodFactory(name="Kurier", rate=1990)

        response: Any = api_client.get(_url(), {"order_value": 50000})

        row = response.json()[0]
        assert row["cost"] == {"amount": 0, "currency": "PLN"}
        assert row["isFree"] is True

    def test_pickup_is_listed_for_any_value(self, api_client: APIClient):
        """Odbiór osobisty wychodzi przy każdej wartości."""
        PickupMethodFactory(name="Odbiór w pracowni")

        response: Any = api_client.get(_url(), {"order_value": 99_000_000})

        assert [row["name"] for row in response.json()] == ["Odbiór w pracowni"]

    def test_zone_from_parameter(self, api_client: APIClient):
        """Strefa pochodzi z parametru."""
        ShippingMethodFactory(name="Kurier PL", zone=ShippingZone.PL)
        ShippingMethodFactory(name="Kurier UE", zone=ShippingZone.EU)

        response: Any = api_client.get(_url(), {"order_value": 10000, "zone": "EU"})

        assert [row["name"] for row in response.json()] == ["Kurier UE"]

    def test_without_params_zone_is_domestic(self, api_client: APIClient):
        """Bez parametrów strefa jest krajowa."""
        ShippingMethodFactory(name="Kurier PL", zone=ShippingZone.PL)
        ShippingMethodFactory(name="Kurier UE", zone=ShippingZone.EU)

        response: Any = api_client.get(_url())

        assert [row["name"] for row in response.json()] == ["Kurier PL"]

    def test_pickup_is_free_below_threshold(self, api_client: APIClient, settings):
        """Odbiór osobisty jest darmowy poniżej progu."""
        settings.FREE_SHIPPING_THRESHOLD = 50000
        PickupMethodFactory(name="Odbiór w pracowni")

        response: Any = api_client.get(_url(), {"order_value": 1000})

        assert response.json()[0]["isFree"] is True

    def test_foreign_currency_method_does_not_break_read(self, api_client: APIClient):
        """Publiczny odczyt nie może paść przez jeden wiersz wpisany w panelu."""
        ShippingMethodFactory(name="Kurier EUR", currency="EUR")

        response: Any = api_client.get(_url(), {"order_value": 10000})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_is_not_paginated(self, api_client: APIClient):
        """Lista nie jest stronicowana."""
        ShippingMethodFactory()

        response: Any = api_client.get(_url())

        assert isinstance(response.json(), list)


@pytest.mark.django_db
class TestParameterNamesFromClient:
    """Schemat ogłasza `orderValue` — wygenerowany klient wysyła to samo.

    Zamianę robi `CamelCaseMiddleWare`; bez niej klient z Orvala pytałby o
    parametr, którego serializer nie czyta, i cicho dostawał pełen cennik.
    """

    def test_camel_case_from_generated_client_works(self, api_client: APIClient):
        """camelCase z wygenerowanego klienta działa."""
        ParcelLockerMethodFactory(name="Paczkomat", max_order_value=500000)
        ShippingMethodFactory(name="Kurier")

        response: Any = api_client.get(_url(), {"orderValue": 600000})

        assert [row["name"] for row in response.json()] == ["Kurier"]


@pytest.mark.django_db
class TestParameterValidation:
    """Walidacja parametrów listy metod."""

    def test_negative_order_value_is_rejected(self, api_client: APIClient):
        """Ujemna wartość zamówienia jest odrzucana."""
        response: Any = api_client.get(_url(), {"order_value": -1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "orderValue" in response.json()

    def test_unknown_zone_is_rejected(self, api_client: APIClient):
        """Nieznana strefa jest odrzucana."""
        response: Any = api_client.get(_url(), {"zone": "US"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "zone" in response.json()


@pytest.mark.django_db
class TestNoMutations:
    """Metody dostawy prowadzi panel, nie API (ADR 0021)."""

    def test_post_is_not_supported(self, authenticated_client: APIClient):
        """POST nie jest obsługiwany."""
        response: Any = authenticated_client.post(_url(), {"name": "Kurier"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
