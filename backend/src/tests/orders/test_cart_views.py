"""API koszyka na realnym kształcie odpowiedzi (camelCase)."""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.orders.models import Cart
from apps.orders.services import add_item
from apps.products.models import RingSize
from tests.factories.orders import CartFactory, GuestCartFactory
from tests.factories.products import (
    EngravableProductFactory,
    MadeToOrderProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)


def _variant(**kwargs):
    """Wariant, który klient może kupić — produkt opublikowany, nie szkic."""
    kwargs.setdefault("product", PublishedProductFactory())
    return ProductVariantFactory(**kwargs)


TOKEN_HEADER = "HTTP_X_CART_TOKEN"


def _cart_url() -> str:
    return reverse("cart-detail")


def _items_url() -> str:
    return reverse("cart-item-list")


def _item_url(item_id) -> str:
    return reverse("cart-item-detail", args=[item_id])


def _merge_url() -> str:
    return reverse("cart-merge")


@pytest.mark.django_db
class TestGuestCart:
    """Koszyk gościa w API."""

    def test_first_add_returns_token(self, api_client: APIClient):
        """Pierwsze dodanie zwraca token."""
        variant = _variant()
        stock(variant, 10)

        response: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 1}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["cartToken"]

    def test_next_request_with_header_hits_same_cart(self, api_client: APIClient):
        """Kolejne żądanie z nagłówkiem trafia w ten sam koszyk."""
        variant = _variant()
        stock(variant, 10)
        created: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 1}
        )
        token = created.json()["cartToken"]

        response: Any = api_client.get(_cart_url(), **{TOKEN_HEADER: token})

        assert response.json()["itemCount"] == 1
        assert Cart.objects.count() == 1

    def test_without_token_cart_is_empty_not_missing(self, api_client: APIClient):
        """Bez tokenu koszyk jest pusty, a nie nieznaleziony."""
        response: Any = api_client.get(_cart_url())

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["items"] == []
        assert body["itemCount"] == 0
        assert body["cartToken"] is None

    def test_reading_empty_cart_creates_no_row(self, api_client: APIClient):
        """Odczyt pustego koszyka nie zakłada wiersza."""
        api_client.get(_cart_url())

        assert Cart.objects.count() == 0


@pytest.mark.django_db
class TestCartView:
    """Widok koszyka."""

    def test_item_has_current_price_and_separate_engraving(self, api_client: APIClient):
        """Pozycja ma cenę aktualną i grawer osobno."""
        product = EngravableProductFactory(engraving_price=4900)
        variant = ProductVariantFactory(product=product, price=100000)
        stock(variant, 10)
        cart = GuestCartFactory()
        add_item(cart, variant=variant, quantity=2, engraving_text="Ania")

        response: Any = api_client.get(_cart_url(), **{TOKEN_HEADER: cart.session_key})

        body = response.json()
        row = body["items"][0]
        assert row["quantity"] == 2
        assert row["engravingText"] == "Ania"
        assert row["unitPrice"] == {"amount": 100000, "currency": "PLN"}
        assert row["goodsPrice"] == {"amount": 200000, "currency": "PLN"}
        assert row["engravingPrice"] == {"amount": 9800, "currency": "PLN"}
        assert row["lineTotal"] == {"amount": 209800, "currency": "PLN"}
        assert row["variant"]["sku"] == variant.sku

    def test_summary_has_discount_and_coupon_fields(self, api_client: APIClient):
        """Podsumowanie ma pola rabatu i kuponu."""
        variant = _variant(price=100000)
        stock(variant, 10)
        cart = GuestCartFactory()
        add_item(cart, variant=variant, quantity=1)

        response: Any = api_client.get(_cart_url(), **{TOKEN_HEADER: cart.session_key})

        body = response.json()
        assert body["itemCount"] == 1
        assert body["subtotal"] == {"amount": 100000, "currency": "PLN"}
        assert body["discountAmount"] == {"amount": 0, "currency": "PLN"}
        assert body["couponAmount"] == {"amount": 0, "currency": "PLN"}
        assert body["total"] == {"amount": 100000, "currency": "PLN"}

    def test_price_follows_price_list_not_add_time(self, api_client: APIClient):
        """Cena idzie za cennikiem, a nie za chwilą dodania."""
        variant = _variant(price=100000)
        stock(variant, 10)
        cart = GuestCartFactory()
        add_item(cart, variant=variant, quantity=1)

        variant.price = 150000
        variant.save()
        response: Any = api_client.get(_cart_url(), **{TOKEN_HEADER: cart.session_key})

        assert response.json()["total"] == {"amount": 150000, "currency": "PLN"}

    def test_customer_cannot_see_other_cart(self, authenticated_client: APIClient):
        """Klient nie widzi cudzego koszyka."""
        other = GuestCartFactory()
        variant = _variant()
        stock(variant, 10)
        add_item(other, variant=variant, quantity=1)

        response: Any = authenticated_client.get(
            _cart_url(), **{TOKEN_HEADER: other.session_key}
        )

        assert response.json()["itemCount"] == 0


@pytest.mark.django_db
class TestItemChange:
    """Zmiana pozycji koszyka."""

    def test_quantity_change(self, api_client: APIClient):
        """Zmiana ilości pozycji."""
        variant = _variant()
        stock(variant, 10)
        cart = GuestCartFactory()
        item = add_item(cart, variant=variant, quantity=1)

        response: Any = api_client.patch(
            _item_url(item.pk), {"quantity": 3}, **{TOKEN_HEADER: cart.session_key}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["itemCount"] == 1
        item.refresh_from_db()
        assert item.quantity == 3

    def test_item_removal(self, api_client: APIClient):
        """Usunięcie pozycji."""
        variant = _variant()
        stock(variant, 10)
        cart = GuestCartFactory()
        item = add_item(cart, variant=variant, quantity=1)

        response: Any = api_client.delete(
            _item_url(item.pk), **{TOKEN_HEADER: cart.session_key}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["itemCount"] == 0

    def test_item_from_other_cart_is_not_found(self, api_client: APIClient):
        """Pozycja z cudzego koszyka jest nieznaleziona."""
        variant = _variant()
        stock(variant, 10)
        mine = GuestCartFactory()
        theirs = GuestCartFactory()
        item = add_item(theirs, variant=variant, quantity=1)

        response: Any = api_client.delete(
            _item_url(item.pk), **{TOKEN_HEADER: mine.session_key}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAddValidation:
    """Walidacja dodawania do koszyka."""

    def test_quantity_above_stock_fails(self, api_client: APIClient):
        """Ilość ponad stan kończy się błędem."""
        variant = _variant()
        stock(variant, 2)

        response: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 3}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quantity" in response.json()

    def test_more_than_five_fails(self, api_client: APIClient):
        """Ponad pięć sztuk kończy się błędem."""
        variant = _variant()
        stock(variant, 100)

        response: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 6}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_engraving_on_non_engravable_product_fails(self, api_client: APIClient):
        """Grawer na produkcie bez grawerunku kończy się błędem."""
        variant = _variant()
        stock(variant, 10)

        response: Any = api_client.post(
            _items_url(),
            {"variant": str(variant.pk), "quantity": 1, "engravingText": "Ania"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "engravingText" in response.json()

    def test_draft_variant_cannot_be_added(self, api_client: APIClient):
        """Szkic nie istnieje dla sklepu — także jako identyfikator w żądaniu."""
        variant = ProductVariantFactory()
        stock(variant, 10)

        response: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 1}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pair_of_made_to_order_product_passes(self, api_client: APIClient):
        """Para z wyrobu na zamówienie przechodzi."""
        variant = ProductVariantFactory(
            product=MadeToOrderProductFactory(), size=RingSize.S16
        )

        response: Any = api_client.post(
            _items_url(),
            {"variant": str(variant.pk), "quantity": 1, "secondSize": RingSize.S20},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["items"][0]["secondSize"] == "20"


@pytest.mark.django_db
class TestMerge:
    """Scalanie koszyka przez API."""

    def test_merge_after_login(self, api_client: APIClient, user: CustomUser):
        """Scalenie po zalogowaniu."""
        variant = _variant()
        stock(variant, 10)
        guest = GuestCartFactory()
        add_item(guest, variant=variant, quantity=2)
        api_client.force_authenticate(user=user)

        response: Any = api_client.post(
            _merge_url(), {}, **{TOKEN_HEADER: guest.session_key}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["itemCount"] == 1
        assert Cart.objects.filter(user=user).exists() is True
        assert Cart.objects.guest().exists() is False

    def test_token_stops_working_after_merge(
        self, api_client: APIClient, user: CustomUser
    ):
        """Token po scaleniu przestaje działać."""
        variant = _variant()
        stock(variant, 10)
        guest = GuestCartFactory()
        token = guest.session_key
        add_item(guest, variant=variant, quantity=1)
        api_client.force_authenticate(user=user)
        api_client.post(_merge_url(), {}, **{TOKEN_HEADER: token})
        api_client.force_authenticate(user=None)

        response: Any = api_client.get(_cart_url(), **{TOKEN_HEADER: token})

        assert response.json()["itemCount"] == 0

    def test_merge_requires_login(self, api_client: APIClient):
        """Scalanie wymaga zalogowania."""
        guest = GuestCartFactory()

        response: Any = api_client.post(
            _merge_url(), {}, **{TOKEN_HEADER: guest.session_key}
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_merge_without_token_fails(self, authenticated_client: APIClient):
        """Scalanie bez tokenu kończy się błędem."""
        response: Any = authenticated_client.post(_merge_url(), {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAccountCart:
    """Koszyk konta."""

    def test_logged_in_gets_account_cart(self, authenticated_client, user):
        """Zalogowany dostaje koszyk konta."""
        variant = _variant()
        stock(variant, 10)
        cart = CartFactory(user=user)
        add_item(cart, variant=variant, quantity=1)

        response: Any = authenticated_client.get(_cart_url())

        assert response.json()["itemCount"] == 1
        assert response.json()["cartToken"] is None
