"""API zamówień na realnym kształcie odpowiedzi (camelCase)."""

from __future__ import annotations

from typing import Any

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
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
from tests.factories.orders import (
    CartFactory,
    GuestCartFactory,
    GuestOrderFactory,
    OrderFactory,
)
from tests.factories.products import (
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.shipping import (
    ParcelLockerMethodFactory,
    ShipmentFactory,
    ShippingMethodFactory,
)

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

    def test_order_detail_exposes_delivered_at(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        """Ekran zamówienia dostaje datę doręczenia — od niej liczy terminy zwrotu."""
        order = self._order_for(authenticated_client, user)
        before: Any = authenticated_client.get(_order_url(order.number))
        assert before.json()["deliveredAt"] is None
        for step in (
            OrderStatus.PAID,
            OrderStatus.PACKED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ):
            order.transition_to(step)

        response: Any = authenticated_client.get(_order_url(order.number))

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["deliveredAt"] is not None

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

    def test_gosc_nie_otwiera_zamowienia_zalogowanego_klienta(
        self, api_client: APIClient, user: CustomUser
    ):
        """Adres i numer to klucz do zamówień bez konta, nie do cudzego konta."""
        api_client.force_authenticate(user=user)
        order = self._order_for(api_client, user)
        api_client.force_authenticate(user=None)

        response: Any = api_client.get(_order_url(order.number), {"email": user.email})

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

    def test_anulowanie_wyslanego_jest_odrzucone(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        # Opłacone anuluje się zwrotem (`tests/payments/`); wysłanego klient
        # sam nie anuluje — dalej wyłącznie przez zwrot towaru.
        order = self._order(authenticated_client, user)
        for step in (OrderStatus.PAID, OrderStatus.PACKED, OrderStatus.SHIPPED):
            order.transition_to(step)

        response: Any = authenticated_client.post(_cancel_url(order.number))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.json()

    def test_gosc_nie_anuluje_zamowienia_zalogowanego_klienta(
        self, api_client: APIClient, user: CustomUser
    ):
        api_client.force_authenticate(user=user)
        order = self._order(api_client, user)
        api_client.force_authenticate(user=None)

        response: Any = api_client.post(
            _cancel_url(order.number), {"email": user.email}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING

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


@pytest.mark.django_db
class TestOrderShipments:
    """Przesyłki w szczegółach zamówienia — numer śledzenia bez kwot przewoźnika."""

    def test_detail_lists_shipments_without_declared_value(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        order = OrderFactory(user=user, shipping_method=ParcelLockerMethodFactory())
        ShipmentFactory(
            order=order,
            tracking_number="PL123",
            pickup_point_code="WAW01M",
            declared_value=50000,
        )

        response: Any = authenticated_client.get(_order_url(order.number))

        assert response.status_code == status.HTTP_200_OK
        [shipment] = response.json()["shipments"]
        assert shipment["trackingNumber"] == "PL123"
        assert shipment["pickupPointCode"] == "WAW01M"
        assert shipment["shippingMethodKind"] == "parcel_locker"
        assert shipment["createdAt"]
        assert "declaredValue" not in shipment
        assert "50000" not in response.content.decode()
        # Data doręczenia z #193 zostaje obok przesyłek.
        assert "deliveredAt" in response.json()

    def test_order_without_shipments_has_empty_list(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        order = OrderFactory(user=user)

        response: Any = authenticated_client.get(_order_url(order.number))

        assert response.json()["shipments"] == []

    def test_guest_sees_shipments_with_number_and_email(self, api_client: APIClient):
        order = GuestOrderFactory(email="gosc@test.com")
        ShipmentFactory(order=order, tracking_number="PL999")

        response: Any = api_client.get(
            _order_url(order.number), {"email": "gosc@test.com"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["shipments"][0]["trackingNumber"] == "PL999"

    def test_guest_without_email_does_not_see_shipments(self, api_client: APIClient):
        order = GuestOrderFactory(email="gosc@test.com")
        ShipmentFactory(order=order, tracking_number="PL999")

        response: Any = api_client.get(_order_url(order.number))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "PL999" not in response.content.decode()

    def test_guest_with_wrong_email_does_not_see_shipments(self, api_client: APIClient):
        order = GuestOrderFactory(email="gosc@test.com")
        ShipmentFactory(order=order, tracking_number="PL999")

        response: Any = api_client.get(
            _order_url(order.number), {"email": "ktos.inny@test.com"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "PL999" not in response.content.decode()

    def test_order_list_query_count_does_not_grow_with_shipments(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        ShipmentFactory.create_batch(2, order=OrderFactory(user=user))
        with CaptureQueriesContext(connection) as single:
            authenticated_client.get(_orders_url())

        for _ in range(3):
            ShipmentFactory.create_batch(2, order=OrderFactory(user=user))
        with CaptureQueriesContext(connection) as many:
            response: Any = authenticated_client.get(_orders_url())

        assert len(response.json()["results"]) == 4
        assert len(many) == len(single)
