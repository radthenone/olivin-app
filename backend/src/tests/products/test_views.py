"""Testy katalogu na realnym kształcie odpowiedzi.

Asercje idą po `response.json()`, a nie po `response.data`: renderer zamienia
klucze na camelCase dopiero przy renderowaniu, więc tylko JSON pokazuje to,
co faktycznie dostaje klient.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories.categories import CategoryFactory
from tests.factories.favorites import FavoriteFactory
from tests.factories.products import (
    EngravableProductFactory,
    MadeToOrderProductFactory,
    ProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)


def _get(client: APIClient, url: str, **params: Any) -> tuple[int, Any]:
    response: Any = client.get(url, params or None)
    return response.status_code, response.json()


def _detail(slug: str | None) -> str:
    return reverse("product-detail", kwargs={"slug": slug})


@pytest.mark.django_db
class TestProductListAccess:
    """Katalog czyta każdy odwiedzający — bez logowania."""

    def test_anonymous_gets_list(self, api_client: APIClient):
        """Anonim dostaje listę produktów."""
        PublishedProductFactory()

        code, _ = _get(api_client, reverse("product-list"))

        assert code == status.HTTP_200_OK

    def test_list_is_paginated(self, api_client: APIClient):
        """Lista jest stronicowana."""
        category = CategoryFactory()
        for _ in range(30):
            PublishedProductFactory(category=category)

        _, body = _get(api_client, reverse("product-list"))

        assert body["count"] == 30
        assert len(body["results"]) == 24


@pytest.mark.django_db
class TestDraftsAreInvisible:
    """Szkic nie istnieje dla sklepu pod żadnym adresem."""

    def test_draft_is_not_listed(self, api_client: APIClient):
        """Szkic nie wchodzi na listę."""
        category = CategoryFactory()
        PublishedProductFactory(name="Widoczny", category=category)
        ProductFactory(name="Szkic", category=category)

        _, body = _get(api_client, reverse("product-list"))

        assert [row["name"] for row in body["results"]] == ["Widoczny"]

    def test_draft_detail_is_404(self, api_client: APIClient):
        """Szkic pod własnym adresem daje 404."""
        draft = ProductFactory(name="Szkic")

        code, _ = _get(api_client, _detail(draft.slug))

        assert code == status.HTTP_404_NOT_FOUND

    def test_logged_in_cannot_see_draft_either(self, authenticated_client: APIClient):
        """Zalogowany też nie zobaczy szkicu."""
        draft = ProductFactory(name="Szkic")

        code, _ = _get(authenticated_client, _detail(draft.slug))

        assert code == status.HTTP_404_NOT_FOUND

    def test_published_product_has_detail(self, api_client: APIClient):
        """Opublikowany produkt ma swój adres."""
        product = PublishedProductFactory(name="Gold ring")

        code, body = _get(api_client, _detail(product.slug))

        assert code == status.HTTP_200_OK
        assert body["name"] == "Gold ring"


@pytest.mark.django_db
class TestCheapestVariantOnList:
    """Produkt na liście reprezentuje jego najtańszy wariant (`CONTEXT.md`)."""

    def test_list_shows_cheapest_variant(self, api_client: APIClient):
        """Lista pokazuje najtańszy wariant."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="DROGI", price=200000)
        ProductVariantFactory(product=product, sku="TANI", price=100000)

        _, body = _get(api_client, reverse("product-list"))

        cheapest = body["results"][0]["cheapestVariant"]
        assert cheapest["sku"] == "TANI"
        assert cheapest["price"] == {"amount": 100000, "currency": "PLN"}

    def test_manual_price_counts_for_cheapest(self, api_client: APIClient):
        """Wariant z niższą ceną ręczną jest tańszy, choć wyliczoną ma wyższą."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="WYLICZONY", price=150000)
        ProductVariantFactory(
            product=product, sku="PRZECENIONY", price=200000, manual_price=100000
        )

        _, body = _get(api_client, reverse("product-list"))

        cheapest = body["results"][0]["cheapestVariant"]
        assert cheapest["sku"] == "PRZECENIONY"
        assert cheapest["price"] == {"amount": 100000, "currency": "PLN"}

    def test_product_without_variants_does_not_break_list(self, api_client: APIClient):
        """Produkt bez wariantów nie wywraca listy."""
        PublishedProductFactory(name="Bez wariantów")

        code, body = _get(api_client, reverse("product-list"))

        assert code == status.HTTP_200_OK
        assert body["results"][0]["cheapestVariant"] is None

    def test_list_does_not_show_all_variants(self, api_client: APIClient):
        """Lista nie pokazuje pełnej listy wariantów."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product)

        _, body = _get(api_client, reverse("product-list"))

        assert "variants" not in body["results"][0]


@pytest.mark.django_db
class TestProductDetail:
    """Strona produktu pokazuje wszystkie warianty wraz z traktowaniem podatkowym."""

    def test_detail_returns_all_variants(self, api_client: APIClient):
        """Szczegół zwraca wszystkie warianty."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="A-1", price=100000)
        ProductVariantFactory(product=product, sku="B-2", price=200000)

        _, body = _get(api_client, _detail(product.slug))

        assert [variant["sku"] for variant in body["variants"]] == ["A-1", "B-2"]

    def test_variant_has_own_tax_rate(self, api_client: APIClient):
        """Wariant niesie własną stawkę podatku."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="JEW-1")

        _, body = _get(api_client, _detail(product.slug))

        variant = body["variants"][0]
        assert variant["vatRate"] == "0.2300"
        assert variant["isVatExempt"] is False
        assert variant["vatExemptionBasis"] == ""

    def test_exemption_has_legal_basis_instead_of_rate(self, api_client: APIClient):
        """Zwolnienie nie jest stawką zerową, tylko osobnym bytem (ADR 0013)."""
        product = PublishedProductFactory()
        ProductVariantFactory(vat_exempt=True, product=product, sku="BUL-1")

        _, body = _get(api_client, _detail(product.slug))

        variant = body["variants"][0]
        assert variant["vatRate"] is None
        assert variant["isVatExempt"] is True
        assert variant["vatExemptionBasis"]

    def test_two_variants_of_one_product_can_differ(self, api_client: APIClient):
        """Dwa warianty jednego produktu mogą mieć różne traktowanie."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="A-JEW")
        ProductVariantFactory(vat_exempt=True, product=product, sku="B-BUL")

        _, body = _get(api_client, _detail(product.slug))

        assert [variant["isVatExempt"] for variant in body["variants"]] == [
            False,
            True,
        ]

    def test_made_to_order_product_has_lead_time(self, api_client: APIClient):
        """Produkt na zamówienie niesie czas realizacji."""
        product = MadeToOrderProductFactory(name="Obrączki")

        _, body = _get(api_client, _detail(product.slug))

        assert body["isMadeToOrder"] is True
        assert body["productionTimeDays"] == 21

    def test_stocked_product_has_no_lead_time(self, api_client: APIClient):
        """Produkt magazynowy nie ma czasu realizacji."""
        product = PublishedProductFactory()

        _, body = _get(api_client, _detail(product.slug))

        assert body["isMadeToOrder"] is False
        assert body["productionTimeDays"] is None

    def test_engravable_product_has_engraving_price(self, api_client: APIClient):
        """Koszyk bierze stąd zgodę na grawer i jego cenę (ADR 0018)."""
        product = EngravableProductFactory(name="Sygnet")

        _, body = _get(api_client, _detail(product.slug))

        assert body["isEngravable"] is True
        assert body["engravingPrice"] == {"amount": 4900, "currency": "PLN"}

    def test_non_engravable_product_has_no_engraving_price(self, api_client: APIClient):
        """Produkt bez grawerunku nie ma ceny grawerunku."""
        product = PublishedProductFactory()

        _, body = _get(api_client, _detail(product.slug))

        assert body["isEngravable"] is False
        assert body["engravingPrice"] is None

    def test_list_also_has_engraving(self, api_client: APIClient):
        """Karta produktu na liście ma pokazać „z grawerem” bez wchodzenia
        w szczegół."""
        EngravableProductFactory()

        _, body = _get(api_client, reverse("product-list"))

        assert body["results"][0]["isEngravable"] is True
        assert body["results"][0]["engravingPrice"] == {
            "amount": 4900,
            "currency": "PLN",
        }

    def test_response_hides_status_and_computed_price(self, api_client: APIClient):
        """Odpowiedź nie zdradza statusu ani ceny wyliczonej."""
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, price=129900, manual_price=99900)

        _, body = _get(api_client, _detail(product.slug))

        assert "status" not in body
        assert "manualPrice" not in body["variants"][0]
        assert body["variants"][0]["price"] == {"amount": 99900, "currency": "PLN"}


@pytest.mark.django_db
class TestProductIsReadOnly:
    """Katalog prowadzi panel, nie API (ADR 0021)."""

    @pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
    def test_write_is_not_allowed(self, authenticated_client: APIClient, method: str):
        """Zapis przez API jest niedozwolony."""
        product = PublishedProductFactory()
        url = reverse("product-list") if method == "post" else _detail(product.slug)

        response = getattr(authenticated_client, method)(url, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestQueryBudget:
    """Lista nie może mnożyć zapytań przez liczbę produktów."""

    def test_list_queries_do_not_grow_with_products(
        self, api_client: APIClient, django_assert_max_num_queries
    ):
        """Liczba zapytań listy nie rośnie wraz z liczbą produktów."""
        category = CategoryFactory()
        for index in range(10):
            product = PublishedProductFactory(category=category)
            ProductVariantFactory(product=product, sku=f"A-{index}", price=100000)
            ProductVariantFactory(product=product, sku=f"B-{index}", price=200000)

        # Budżet stały niezależnie od liczby produktów: lista, licznik
        # paginacji, warianty, galerie (produktu oraz wariantów), kamienie,
        # stany magazynowe i tłumaczenia.
        with django_assert_max_num_queries(12):
            api_client.get(reverse("product-list"))


@pytest.mark.django_db
class TestIsFavoriteOnCatalog:
    """Serduszko na liście i karcie produktu (#200) — bez zapytania na produkt."""

    def test_guest_sees_false(self, api_client: APIClient):
        """Gość widzi `false`."""
        PublishedProductFactory()

        status_code, body = _get(api_client, reverse("product-list"))

        assert status_code == status.HTTP_200_OK
        assert body["results"][0]["isFavorite"] is False

    def test_logged_in_sees_own_favorite(self, authenticated_client: APIClient, user):
        """Zalogowany widzi własny ulubiony produkt."""
        product = PublishedProductFactory()
        FavoriteFactory(user=user, product=product)
        other_product = PublishedProductFactory()

        status_code, body = _get(authenticated_client, reverse("product-list"))

        assert status_code == status.HTTP_200_OK
        by_slug = {row["slug"]: row["isFavorite"] for row in body["results"]}
        assert by_slug[product.slug] is True
        assert by_slug[other_product.slug] is False

    def test_product_detail_has_flag_too(self, authenticated_client: APIClient, user):
        """Karta produktu też niesie flagę."""
        product = PublishedProductFactory()
        FavoriteFactory(user=user, product=product)

        status_code, body = _get(authenticated_client, _detail(product.slug))

        assert status_code == status.HTTP_200_OK
        assert body["isFavorite"] is True

    def test_query_budget_does_not_grow_with_products(
        self, authenticated_client: APIClient, django_assert_max_num_queries, user
    ):
        """Budżet zapytań nie rośnie z liczbą produktów."""
        category = CategoryFactory()
        for index in range(10):
            product = PublishedProductFactory(category=category)
            ProductVariantFactory(product=product, sku=f"C-{index}", price=100000)
            if index % 2 == 0:
                FavoriteFactory(user=user, product=product)

        with django_assert_max_num_queries(12):
            authenticated_client.get(reverse("product-list"))
