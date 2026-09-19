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
from tests.factories.products import (
    MadeToOrderProductFactory,
    ProductFactory,
    ProductVariantFactory,
    PublishedProductFactory,
)


def _get(client: APIClient, url: str, **params: Any) -> tuple[int, Any]:
    response: Any = client.get(url, params or None)
    return response.status_code, response.json()


def _detail(slug: str) -> str:
    return reverse("product-detail", kwargs={"slug": slug})


@pytest.mark.django_db
class TestProductListAccess:
    """Katalog czyta każdy odwiedzający — bez logowania."""

    def test_anonim_dostaje_liste(self, api_client: APIClient):
        PublishedProductFactory()

        code, _ = _get(api_client, reverse("product-list"))

        assert code == status.HTTP_200_OK

    def test_lista_jest_stronicowana(self, api_client: APIClient):
        category = CategoryFactory()
        for _ in range(30):
            PublishedProductFactory(category=category)

        _, body = _get(api_client, reverse("product-list"))

        assert body["count"] == 30
        assert len(body["results"]) == 24


@pytest.mark.django_db
class TestDraftsAreInvisible:
    """Szkic nie istnieje dla sklepu pod żadnym adresem."""

    def test_szkic_nie_wchodzi_na_liste(self, api_client: APIClient):
        category = CategoryFactory()
        PublishedProductFactory(name="Widoczny", category=category)
        ProductFactory(name="Szkic", category=category)

        _, body = _get(api_client, reverse("product-list"))

        assert [row["name"] for row in body["results"]] == ["Widoczny"]

    def test_szkic_pod_wlasnym_adresem_to_404(self, api_client: APIClient):
        draft = ProductFactory(name="Szkic")

        code, _ = _get(api_client, _detail(draft.slug))

        assert code == status.HTTP_404_NOT_FOUND

    def test_zalogowany_tez_nie_zobaczy_szkicu(self, authenticated_client: APIClient):
        draft = ProductFactory(name="Szkic")

        code, _ = _get(authenticated_client, _detail(draft.slug))

        assert code == status.HTTP_404_NOT_FOUND

    def test_opublikowany_produkt_ma_swoj_adres(self, api_client: APIClient):
        product = PublishedProductFactory(name="Gold ring")

        code, body = _get(api_client, _detail(product.slug))

        assert code == status.HTTP_200_OK
        assert body["name"] == "Gold ring"


@pytest.mark.django_db
class TestCheapestVariantOnList:
    """Produkt na liście reprezentuje jego najtańszy wariant (`CONTEXT.md`)."""

    def test_lista_pokazuje_najtanszy_wariant(self, api_client: APIClient):
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="DROGI", price=200000)
        ProductVariantFactory(product=product, sku="TANI", price=100000)

        _, body = _get(api_client, reverse("product-list"))

        cheapest = body["results"][0]["cheapestVariant"]
        assert cheapest["sku"] == "TANI"
        assert cheapest["price"] == {"amount": 100000, "currency": "PLN"}

    def test_cena_reczna_liczy_sie_przy_wyborze_najtanszego(
        self, api_client: APIClient
    ):
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

    def test_produkt_bez_wariantow_nie_wywraca_listy(self, api_client: APIClient):
        PublishedProductFactory(name="Bez wariantów")

        code, body = _get(api_client, reverse("product-list"))

        assert code == status.HTTP_200_OK
        assert body["results"][0]["cheapestVariant"] is None

    def test_lista_nie_pokazuje_pelnej_listy_wariantow(self, api_client: APIClient):
        product = PublishedProductFactory()
        ProductVariantFactory(product=product)

        _, body = _get(api_client, reverse("product-list"))

        assert "variants" not in body["results"][0]


@pytest.mark.django_db
class TestProductDetail:
    """Strona produktu pokazuje wszystkie warianty wraz z traktowaniem podatkowym."""

    def test_szczegol_zwraca_wszystkie_warianty(self, api_client: APIClient):
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="A-1", price=100000)
        ProductVariantFactory(product=product, sku="B-2", price=200000)

        _, body = _get(api_client, _detail(product.slug))

        assert [variant["sku"] for variant in body["variants"]] == ["A-1", "B-2"]

    def test_wariant_niesie_wlasna_stawke_podatku(self, api_client: APIClient):
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="JEW-1")

        _, body = _get(api_client, _detail(product.slug))

        variant = body["variants"][0]
        assert variant["vatRate"] == "0.2300"
        assert variant["isVatExempt"] is False
        assert variant["vatExemptionBasis"] == ""

    def test_zwolnienie_niesie_podstawe_prawna_zamiast_stawki(
        self, api_client: APIClient
    ):
        """Zwolnienie nie jest stawką zerową, tylko osobnym bytem (ADR 0013)."""
        product = PublishedProductFactory()
        ProductVariantFactory(vat_exempt=True, product=product, sku="BUL-1")

        _, body = _get(api_client, _detail(product.slug))

        variant = body["variants"][0]
        assert variant["vatRate"] is None
        assert variant["isVatExempt"] is True
        assert variant["vatExemptionBasis"]

    def test_dwa_warianty_jednego_produktu_moga_miec_rozne_traktowanie(
        self, api_client: APIClient
    ):
        product = PublishedProductFactory()
        ProductVariantFactory(product=product, sku="A-JEW")
        ProductVariantFactory(vat_exempt=True, product=product, sku="B-BUL")

        _, body = _get(api_client, _detail(product.slug))

        assert [variant["isVatExempt"] for variant in body["variants"]] == [
            False,
            True,
        ]

    def test_produkt_na_zamowienie_niesie_czas_realizacji(self, api_client: APIClient):
        product = MadeToOrderProductFactory(name="Obrączki")

        _, body = _get(api_client, _detail(product.slug))

        assert body["isMadeToOrder"] is True
        assert body["productionTimeDays"] == 21

    def test_produkt_magazynowy_nie_ma_czasu_realizacji(self, api_client: APIClient):
        product = PublishedProductFactory()

        _, body = _get(api_client, _detail(product.slug))

        assert body["isMadeToOrder"] is False
        assert body["productionTimeDays"] is None

    def test_odpowiedz_nie_zdradza_statusu_ani_ceny_wyliczonej(
        self, api_client: APIClient
    ):
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
    def test_zapis_jest_niedozwolony(
        self, authenticated_client: APIClient, method: str
    ):
        product = PublishedProductFactory()
        url = reverse("product-list") if method == "post" else _detail(product.slug)

        response = getattr(authenticated_client, method)(url, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestQueryBudget:
    """Lista nie może mnożyć zapytań przez liczbę produktów."""

    def test_lista_nie_rosnie_wraz_z_liczba_produktow(
        self, api_client: APIClient, django_assert_max_num_queries
    ):
        category = CategoryFactory()
        for index in range(10):
            product = PublishedProductFactory(category=category)
            ProductVariantFactory(product=product, sku=f"A-{index}", price=100000)
            ProductVariantFactory(product=product, sku=f"B-{index}", price=200000)

        with django_assert_max_num_queries(4):
            api_client.get(reverse("product-list"))
