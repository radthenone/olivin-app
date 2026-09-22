"""API zamówień na realnym kształcie odpowiedzi (camelCase)."""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.consents.models import ConsentKind
from apps.orders.models import Order, OrderStatus
from apps.orders.services.cart import add_item
from tests.factories.consents import (
    ConsentDocumentFactory,
    ConsentFactory,
    GuestConsentFactory,
)
from tests.factories.orders import CartFactory, GuestCartFactory
from tests.factories.products import (
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.shipping import ShippingMethodFactory

TOKEN_HEADER = "HTTP_X_CART_TOKEN"

ADDRESS_PAYLOAD = {
    "recipientName": "Jan Kowalski",
    "street": "Złota 44",
    "city": "Warszawa",
    "postalCode": "00-120",
    "country": "PL",
}


def _orders_url() -> str:
    return reverse("order-list")


def _order_url(number: str) -> str:
    return reverse("order-detail", args=[number])


def _cancel_url(number: str) -> str:
    return reverse("order-cancel", args=[number])


def _variant(**kwargs):
    kwargs.setdefault("product", PublishedProductFactory())
    return ProductVariantFactory(**kwargs)


def _terms_for(user=None, email: str = ""):
    document = ConsentDocumentFactory(kind=ConsentKind.TERMS)
    if user is not None:
        ConsentFactory(user=user, document=document)
    else:
        GuestConsentFactory(email=email, document=document)
    return document


@pytest.mark.django_db
class TestSkladanieZamowienia:
    def test_zalogowany_sklada_zamowienie_z_koszyka(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant(price=100000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()

        response: Any = authenticated_client.post(
            _orders_url(),
            {**ADDRESS_PAYLOAD, "shippingMethod": str(method.pk)},
        )

        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["status"] == "pending"
        assert body["number"]
        assert body["items"][0]["unitPrice"] == {
            "amount": 100000,
            "currency": "PLN",
        }
        assert body["total"]["amount"] == 100000

    def test_gosc_sklada_zamowienie_tokenem_koszyka(self, api_client: APIClient):
        email = "gosc@test.com"
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant(price=10000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()

        response: Any = api_client.post(
            _orders_url(),
            {**ADDRESS_PAYLOAD, "shippingMethod": str(method.pk), "email": email},
            **{TOKEN_HEADER: cart.session_key},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["email"] == email

    def test_bez_koszyka_zamowienie_nie_powstaje(self, api_client: APIClient):
        method = ShippingMethodFactory()

        response: Any = api_client.post(
            _orders_url(),
            {**ADDRESS_PAYLOAD, "shippingMethod": str(method.pk), "email": "a@b.com"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cart" in response.json()

    def test_bez_zgody_na_regulamin_zamowienie_nie_powstaje(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        ConsentDocumentFactory(kind=ConsentKind.TERMS)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()

        response: Any = authenticated_client.post(
            _orders_url(),
            {**ADDRESS_PAYLOAD, "shippingMethod": str(method.pk)},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "terms" in response.json()

    def test_kraj_spoza_unii_jest_odrzucony(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant()
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()

        response: Any = authenticated_client.post(
            _orders_url(),
            {**ADDRESS_PAYLOAD, "country": "US", "shippingMethod": str(method.pk)},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestOdczytZamowien:
    def _order_for(self, client: APIClient, user: CustomUser) -> Order:
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant(price=10000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()
        response: Any = client.post(
            _orders_url(), {**ADDRESS_PAYLOAD, "shippingMethod": str(method.pk)}
        )
        return Order.objects.get(number=response.json()["number"])

    def test_zalogowany_widzi_swoje_zamowienia(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        order = self._order_for(authenticated_client, user)

        response: Any = authenticated_client.get(_orders_url())

        assert response.status_code == status.HTTP_200_OK
        assert [row["number"] for row in response.json()["results"]] == [order.number]

    def test_anonim_nie_dostaje_listy(self, api_client: APIClient):
        response: Any = api_client.get(_orders_url())

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_klient_nie_widzi_cudzego_zamowienia(
        self, api_client: APIClient, user: CustomUser
    ):
        api_client.force_authenticate(user=user)
        order = self._order_for(api_client, user)
        other = CustomUser.objects.create_user(
            email="inny@test.com", password="testpass123!"
        )
        api_client.force_authenticate(user=other)

        response: Any = api_client.get(_order_url(order.number))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_gosc_otwiera_zamowienie_numerem_i_adresem(self, api_client: APIClient):
        email = "gosc@test.com"
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant(price=10000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()
        created: Any = api_client.post(
            _orders_url(),
            {**ADDRESS_PAYLOAD, "shippingMethod": str(method.pk), "email": email},
            **{TOKEN_HEADER: cart.session_key},
        )
        number = created.json()["number"]

        response: Any = api_client.get(_order_url(number), {"email": email})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["number"] == number

    def test_sam_numer_nie_otwiera_zamowienia_goscia(self, api_client: APIClient):
        email = "gosc@test.com"
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant(price=10000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()
        created: Any = api_client.post(
            _orders_url(),
            {**ADDRESS_PAYLOAD, "shippingMethod": str(method.pk), "email": email},
            **{TOKEN_HEADER: cart.session_key},
        )

        response: Any = api_client.get(_order_url(created.json()["number"]))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cudzy_adres_nie_otwiera_zamowienia_goscia(self, api_client: APIClient):
        email = "gosc@test.com"
        _terms_for(email=email)
        cart = GuestCartFactory()
        variant = _variant(price=10000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()
        created: Any = api_client.post(
            _orders_url(),
            {**ADDRESS_PAYLOAD, "shippingMethod": str(method.pk), "email": email},
            **{TOKEN_HEADER: cart.session_key},
        )

        response: Any = api_client.get(
            _order_url(created.json()["number"]), {"email": "ktos.inny@test.com"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAnulowanie:
    def _order(self, client: APIClient, user: CustomUser) -> Order:
        _terms_for(user=user)
        cart = CartFactory(user=user)
        variant = _variant(price=10000)
        stock(variant, 5)
        add_item(cart, variant=variant, quantity=1)
        method = ShippingMethodFactory()
        created: Any = client.post(
            _orders_url(), {**ADDRESS_PAYLOAD, "shippingMethod": str(method.pk)}
        )
        return Order.objects.get(number=created.json()["number"])

    def test_klient_anuluje_zamowienie_pending(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        order = self._order(authenticated_client, user)

        response: Any = authenticated_client.post(_cancel_url(order.number))

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "cancelled"

    def test_anulowanie_oplaconego_jest_odrzucone(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        order = self._order(authenticated_client, user)
        order.transition_to(OrderStatus.PAID)

        response: Any = authenticated_client.post(_cancel_url(order.number))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.json()

    def test_klient_nie_anuluje_cudzego_zamowienia(
        self, api_client: APIClient, user: CustomUser
    ):
        api_client.force_authenticate(user=user)
        order = self._order(api_client, user)
        other = CustomUser.objects.create_user(
            email="inny@test.com", password="testpass123!"
        )
        api_client.force_authenticate(user=other)

        response: Any = api_client.post(_cancel_url(order.number))

        assert response.status_code == status.HTTP_404_NOT_FOUND
