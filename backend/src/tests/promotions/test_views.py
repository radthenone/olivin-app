"""API promocji i kodu w koszyku na realnym kształcie odpowiedzi (camelCase)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Cart
from apps.products.services.metal_rate import activate_rate
from tests.factories.products import (
    MetalRateFactory,
    ProductVariantFactory,
    PublishedProductFactory,
    stock,
)
from tests.factories.promotions import PromotionFactory

TOKEN_HEADER = "HTTP_X_CART_TOKEN"


def _guest_cart_token(client: APIClient) -> str:
    variant = ProductVariantFactory(product=PublishedProductFactory(), price=100000)
    stock(variant, 5)
    response: Any = client.post(
        reverse("cart-item-list"), {"variant": str(variant.pk), "quantity": 1}
    )
    return response.json()["cartToken"]


@pytest.mark.django_db
class TestPromotionList:
    """`GET /promotions/` pokazuje każdemu aktywne promocje bez kodu."""

    def test_lists_only_active_promotions_without_code(self, api_client: APIClient):
        """Promocja kodowa, przeszła i przyszła nie trafiają na listę."""
        PromotionFactory(name="Jesień")
        PromotionFactory(name="Tajna", code="SEKRET")
        PromotionFactory(name="Minęła", ends_at=timezone.now() - timedelta(hours=1))
        PromotionFactory(name="Będzie", starts_at=timezone.now() + timedelta(days=1))

        response: Any = api_client.get(reverse("promotion-list"))

        assert response.status_code == status.HTTP_200_OK
        assert [row["name"] for row in response.json()["results"]] == ["Jesień"]

    def test_row_shape(self, api_client: APIClient):
        """Wiersz ma rodzaj, wartość, zakres i próg koszyka jako kwotę."""
        PromotionFactory(value=15, min_cart_value=50000)

        row = api_client.get(reverse("promotion-list")).json()["results"][0]  # type: ignore[attr-defined]

        assert row["kind"] == "percent"
        assert row["value"] == 15
        assert row["wholeCatalog"] is True
        assert row["minCartValue"] == {"amount": 50000, "currency": "PLN"}
        assert "code" not in row


@pytest.mark.django_db
class TestCartPromotionCode:
    """`POST /cart/promotion-code/` i rabat w podsumowaniu koszyka."""

    @pytest.fixture(autouse=True)
    def _active_rate(self):
        activate_rate(MetalRateFactory(price_per_gram=10000))

    def test_code_activates_promotion_in_guest_cart(self, api_client: APIClient):
        """Kod wpisany małymi literami działa i obniża sumę koszyka."""
        token = _guest_cart_token(api_client)
        PromotionFactory(code="LATO", value=10)

        response: Any = api_client.post(
            reverse("cart-promotion-code"), {"code": "lato"}, HTTP_X_CART_TOKEN=token
        )

        body = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert body["promotionCode"] == "LATO"
        assert body["discountAmount"] == {"amount": 10000, "currency": "PLN"}
        assert body["total"] == {"amount": 90000, "currency": "PLN"}

    def test_unknown_code_is_400(self, api_client: APIClient):
        """Nieznany kod to 400 z polem `code`."""
        token = _guest_cart_token(api_client)

        response: Any = api_client.post(
            reverse("cart-promotion-code"), {"code": "NIEMA"}, HTTP_X_CART_TOKEN=token
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.json()

    def test_rejected_code_leaves_no_guest_cart(self, api_client: APIClient):
        """Odrzucony kod bez tokenu nie zakłada pustego koszyka gościa."""
        response: Any = api_client.post(
            reverse("cart-promotion-code"), {"code": "NIEMA"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Cart.objects.exists()

    def test_cart_shows_automatic_promotion(self, api_client: APIClient):
        """Promocja bez kodu obniża sumę koszyka bez żadnej akcji klienta."""
        token = _guest_cart_token(api_client)
        PromotionFactory(value=25)

        body = api_client.get(reverse("cart-detail"), HTTP_X_CART_TOKEN=token).json()  # type: ignore[attr-defined]

        assert body["subtotal"]["amount"] == 100000
        assert body["discountAmount"]["amount"] == 25000
        assert body["total"]["amount"] == 75000
        assert body["promotionCode"] is None
