"""Kolekcje w API oraz filtr `?collection=` na liście produktów."""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories.categories import CategoryFactory
from tests.factories.collections import CollectionFactory
from tests.factories.products import ProductFactory, PublishedProductFactory


def _get(client: APIClient, url: str, **params: Any) -> tuple[int, Any]:
    response: Any = client.get(url, params or None)
    return response.status_code, response.json()


def _collection_names(client: APIClient) -> list[str]:
    _, body = _get(client, reverse("collection-list"))
    return [row["name"] for row in body["results"]]


def _product_names(client: APIClient, **params: Any) -> list[str]:
    _, body = _get(client, reverse("product-list"), **params)
    return [row["name"] for row in body["results"]]


@pytest.mark.django_db
class TestCollectionListAccess:
    """Kolekcje czyta każdy odwiedzający — bez logowania."""

    def test_anonim_dostaje_liste(self, api_client: APIClient):
        CollectionFactory(name="Winter", products=[PublishedProductFactory()])

        code, _ = _get(api_client, reverse("collection-list"))

        assert code == status.HTTP_200_OK

    def test_pojedyncza_kolekcja_po_slugu(self, api_client: APIClient):
        CollectionFactory(
            name="Winter", slug="winter", products=[PublishedProductFactory()]
        )

        code, body = _get(
            api_client, reverse("collection-detail", kwargs={"slug": "winter"})
        )

        assert code == status.HTTP_200_OK
        assert body["slug"] == "winter"

    def test_nieznany_slug_to_404(self, api_client: APIClient):
        code, _ = _get(
            api_client, reverse("collection-detail", kwargs={"slug": "brak"})
        )

        assert code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
    def test_zapis_jest_niedozwolony(
        self, authenticated_client: APIClient, method: str
    ):
        CollectionFactory(
            name="Winter", slug="winter", products=[PublishedProductFactory()]
        )
        url = (
            reverse("collection-list")
            if method == "post"
            else reverse("collection-detail", kwargs={"slug": "winter"})
        )

        response = getattr(authenticated_client, method)(url, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestOnlyCollectionsWithPublishedProducts:
    """Pusta kampania to dla odwiedzającego ślepy zaułek — nie pokazujemy jej."""

    def test_kolekcja_z_opublikowanym_produktem_jest_widoczna(
        self, api_client: APIClient
    ):
        CollectionFactory(name="Winter", products=[PublishedProductFactory()])

        assert _collection_names(api_client) == ["Winter"]

    def test_kolekcja_bez_produktow_nie_wchodzi_na_liste(self, api_client: APIClient):
        CollectionFactory(name="Pusta")

        assert _collection_names(api_client) == []

    def test_kolekcja_z_samymi_szkicami_nie_wchodzi_na_liste(
        self, api_client: APIClient
    ):
        CollectionFactory(name="Szkicowa", products=[ProductFactory()])

        assert _collection_names(api_client) == []

    def test_kolekcja_z_samymi_szkicami_nie_ma_wlasnego_adresu(
        self, api_client: APIClient
    ):
        CollectionFactory(name="Szkicowa", slug="drafts", products=[ProductFactory()])

        code, _ = _get(
            api_client, reverse("collection-detail", kwargs={"slug": "drafts"})
        )

        assert code == status.HTTP_404_NOT_FOUND

    def test_licznik_pomija_szkice(self, api_client: APIClient):
        CollectionFactory(
            name="Mieszana",
            products=[
                PublishedProductFactory(),
                PublishedProductFactory(),
                ProductFactory(),
            ],
        )

        _, body = _get(api_client, reverse("collection-list"))

        assert body["results"][0]["productCount"] == 2

    def test_produkt_w_dwoch_kolekcjach_nie_mnozy_wierszy(self, api_client: APIClient):
        """Złączenie wiele-do-wielu bez `distinct` zwróciłoby kolekcję tyle
        razy, ile ma pasujących produktów."""
        product = PublishedProductFactory()
        CollectionFactory(name="Winter", products=[product])
        CollectionFactory(name="Gifts", products=[product])

        assert _collection_names(api_client) == ["Gifts", "Winter"]


@pytest.mark.django_db
class TestProductCollectionFilter:
    """`?collection=<slug>` zawęża listę produktów do jednej kampanii."""

    def test_filtr_zwraca_produkty_kolekcji(self, api_client: APIClient):
        rings = CategoryFactory(name="Pierścionki")
        chains = CategoryFactory(name="Łańcuszki")
        ring = PublishedProductFactory(name="Pierścionek", category=rings)
        chain = PublishedProductFactory(name="Łańcuszek", category=chains)
        PublishedProductFactory(name="Poza kolekcją", category=rings)
        CollectionFactory(name="Winter", slug="winter", products=[ring, chain])

        assert sorted(_product_names(api_client, collection="winter")) == [
            "Pierścionek",
            "Łańcuszek",
        ]

    def test_filtr_nie_mnozy_produktu_z_wielu_kolekcji(self, api_client: APIClient):
        product = PublishedProductFactory(name="Pierścionek")
        CollectionFactory(name="Winter", slug="winter", products=[product])
        CollectionFactory(name="Gifts", slug="gifts", products=[product])

        assert _product_names(api_client, collection="winter") == ["Pierścionek"]

    def test_nieznana_kolekcja_daje_pusta_liste(self, api_client: APIClient):
        PublishedProductFactory(name="Pierścionek")

        assert _product_names(api_client, collection="nie-ma") == []

    def test_szkic_w_kolekcji_nie_wchodzi_na_liste(self, api_client: APIClient):
        draft = ProductFactory(name="Szkic")
        published = PublishedProductFactory(name="Widoczny")
        CollectionFactory(name="Winter", slug="winter", products=[draft, published])

        assert _product_names(api_client, collection="winter") == ["Widoczny"]

    def test_filtr_laczy_sie_z_pozostalymi(self, api_client: APIClient):
        from apps.products.models import Material

        gold = PublishedProductFactory(name="Złoty", material=Material.GOLD)
        silver = PublishedProductFactory(name="Srebrny", material=Material.SILVER)
        CollectionFactory(name="Winter", slug="winter", products=[gold, silver])

        found = _product_names(api_client, collection="winter", material=Material.GOLD)

        assert found == ["Złoty"]
