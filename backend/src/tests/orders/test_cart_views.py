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
class TestKoszykGoscia:
    def test_pierwsze_dodanie_zwraca_token(self, api_client: APIClient):
        variant = _variant()
        stock(variant, 10)

        response: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 1}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["cartToken"]

    def test_kolejne_zadanie_z_naglowkiem_trafia_w_ten_sam_koszyk(
        self, api_client: APIClient
    ):
        variant = _variant()
        stock(variant, 10)
        created: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 1}
        )
        token = created.json()["cartToken"]

        response: Any = api_client.get(_cart_url(), **{TOKEN_HEADER: token})

        assert response.json()["itemCount"] == 1
        assert Cart.objects.count() == 1

    def test_bez_tokenu_koszyk_jest_pusty_a_nie_nieznaleziony(
        self, api_client: APIClient
    ):
        response: Any = api_client.get(_cart_url())

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["items"] == []
        assert body["itemCount"] == 0
        assert body["cartToken"] is None

    def test_odczyt_pustym_koszykiem_nie_zaklada_wiersza(self, api_client: APIClient):
        api_client.get(_cart_url())

        assert Cart.objects.count() == 0


@pytest.mark.django_db
class TestWidokKoszyka:
    def test_pozycja_ma_cene_aktualna_i_grawer_osobno(self, api_client: APIClient):
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

    def test_podsumowanie_ma_pola_rabatu_i_kuponu(self, api_client: APIClient):
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

    def test_cena_idzie_za_cennikiem_a_nie_za_chwila_dodania(
        self, api_client: APIClient
    ):
        variant = _variant(price=100000)
        stock(variant, 10)
        cart = GuestCartFactory()
        add_item(cart, variant=variant, quantity=1)

        variant.price = 150000
        variant.save()
        response: Any = api_client.get(_cart_url(), **{TOKEN_HEADER: cart.session_key})

        assert response.json()["total"] == {"amount": 150000, "currency": "PLN"}

    def test_klient_nie_widzi_cudzego_koszyka(self, authenticated_client: APIClient):
        other = GuestCartFactory()
        variant = _variant()
        stock(variant, 10)
        add_item(other, variant=variant, quantity=1)

        response: Any = authenticated_client.get(
            _cart_url(), **{TOKEN_HEADER: other.session_key}
        )

        assert response.json()["itemCount"] == 0


@pytest.mark.django_db
class TestZmianaPozycji:
    def test_zmiana_ilosci(self, api_client: APIClient):
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

    def test_usuniecie_pozycji(self, api_client: APIClient):
        variant = _variant()
        stock(variant, 10)
        cart = GuestCartFactory()
        item = add_item(cart, variant=variant, quantity=1)

        response: Any = api_client.delete(
            _item_url(item.pk), **{TOKEN_HEADER: cart.session_key}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["itemCount"] == 0

    def test_pozycja_z_cudzego_koszyka_jest_nieznaleziona(self, api_client: APIClient):
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
class TestWalidacjaDodawania:
    def test_ilosc_ponad_stan_konczy_sie_bledem(self, api_client: APIClient):
        variant = _variant()
        stock(variant, 2)

        response: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 3}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quantity" in response.json()

    def test_ponad_piec_sztuk_konczy_sie_bledem(self, api_client: APIClient):
        variant = _variant()
        stock(variant, 100)

        response: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 6}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_grawer_na_produkcie_bez_grawerunku_konczy_sie_bledem(
        self, api_client: APIClient
    ):
        variant = _variant()
        stock(variant, 10)

        response: Any = api_client.post(
            _items_url(),
            {"variant": str(variant.pk), "quantity": 1, "engravingText": "Ania"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "engravingText" in response.json()

    def test_wariant_szkicu_nie_da_sie_dodac(self, api_client: APIClient):
        """Szkic nie istnieje dla sklepu — także jako identyfikator w żądaniu."""
        variant = ProductVariantFactory()
        stock(variant, 10)

        response: Any = api_client.post(
            _items_url(), {"variant": str(variant.pk), "quantity": 1}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_para_z_wyrobu_na_zamowienie_przechodzi(self, api_client: APIClient):
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
class TestScalanie:
    def test_scalenie_po_zalogowaniu(self, api_client: APIClient, user: CustomUser):
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

    def test_token_po_scaleniu_przestaje_dzialac(
        self, api_client: APIClient, user: CustomUser
    ):
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

    def test_scalanie_wymaga_zalogowania(self, api_client: APIClient):
        guest = GuestCartFactory()

        response: Any = api_client.post(
            _merge_url(), {}, **{TOKEN_HEADER: guest.session_key}
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_scalanie_bez_tokenu_konczy_sie_bledem(
        self, authenticated_client: APIClient
    ):
        response: Any = authenticated_client.post(_merge_url(), {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestKoszykKonta:
    def test_zalogowany_dostaje_koszyk_konta(self, authenticated_client, user):
        variant = _variant()
        stock(variant, 10)
        cart = CartFactory(user=user)
        add_item(cart, variant=variant, quantity=1)

        response: Any = authenticated_client.get(_cart_url())

        assert response.json()["itemCount"] == 1
        assert response.json()["cartToken"] is None
