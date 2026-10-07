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

    def test_anonymous_gets_list(self, api_client: APIClient):
        """Anonim dostaje listę kolekcji."""
        CollectionFactory(name="Winter", products=[PublishedProductFactory()])

        code, _ = _get(api_client, reverse("collection-list"))

        assert code == status.HTTP_200_OK

    def test_single_collection_by_slug(self, api_client: APIClient):
        """Pojedyncza kolekcja jest dostępna po slugu."""
        CollectionFactory(
            name="Winter", slug="winter", products=[PublishedProductFactory()]
        )

        code, body = _get(
            api_client, reverse("collection-detail", kwargs={"slug": "winter"})
        )

        assert code == status.HTTP_200_OK
        assert body["slug"] == "winter"

    def test_unknown_slug_is_404(self, api_client: APIClient):
        """Nieznany slug daje 404."""
        code, _ = _get(
            api_client, reverse("collection-detail", kwargs={"slug": "brak"})
        )

        assert code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
    def test_write_is_not_allowed(self, authenticated_client: APIClient, method: str):
        """Zapis przez API jest niedozwolony."""
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

    def test_collection_with_published_product_is_visible(self, api_client: APIClient):
        """Kolekcja z opublikowanym produktem jest widoczna."""
        CollectionFactory(name="Winter", products=[PublishedProductFactory()])

        assert _collection_names(api_client) == ["Winter"]

    def test_collection_without_products_is_not_listed(self, api_client: APIClient):
        """Kolekcja bez produktów nie wchodzi na listę."""
        CollectionFactory(name="Pusta")

        assert _collection_names(api_client) == []

    def test_collection_with_only_drafts_is_not_listed(self, api_client: APIClient):
        """Kolekcja z samymi szkicami nie wchodzi na listę."""
        CollectionFactory(name="Szkicowa", products=[ProductFactory()])

        assert _collection_names(api_client) == []

    def test_collection_with_only_drafts_has_no_detail(self, api_client: APIClient):
        """Kolekcja z samymi szkicami nie ma własnego adresu."""
        CollectionFactory(name="Szkicowa", slug="drafts", products=[ProductFactory()])

        code, _ = _get(
            api_client, reverse("collection-detail", kwargs={"slug": "drafts"})
        )

        assert code == status.HTTP_404_NOT_FOUND

    def test_counter_skips_drafts(self, api_client: APIClient):
        """Licznik produktów pomija szkice."""
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

    def test_product_in_two_collections_does_not_duplicate_rows(
        self, api_client: APIClient
    ):
        """Złączenie wiele-do-wielu bez `distinct` zwróciłoby kolekcję tyle
        razy, ile ma pasujących produktów."""
        product = PublishedProductFactory()
        CollectionFactory(name="Winter", products=[product])
        CollectionFactory(name="Gifts", products=[product])

        assert _collection_names(api_client) == ["Gifts", "Winter"]


@pytest.mark.django_db
class TestProductCollectionFilter:
    """`?collection=<slug>` zawęża listę produktów do jednej kampanii."""

    def test_filter_returns_collection_products(self, api_client: APIClient):
        """Filtr zwraca produkty kolekcji."""
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

    def test_filter_does_not_duplicate_product_in_many_collections(
        self, api_client: APIClient
    ):
        """Filtr nie mnoży produktu należącego do wielu kolekcji."""
        product = PublishedProductFactory(name="Pierścionek")
        CollectionFactory(name="Winter", slug="winter", products=[product])
        CollectionFactory(name="Gifts", slug="gifts", products=[product])

        assert _product_names(api_client, collection="winter") == ["Pierścionek"]

    def test_unknown_collection_gives_empty_list(self, api_client: APIClient):
        """Nieznana kolekcja daje pustą listę."""
        PublishedProductFactory(name="Pierścionek")

        assert _product_names(api_client, collection="nie-ma") == []

    def test_draft_in_collection_is_not_listed(self, api_client: APIClient):
        """Szkic w kolekcji nie wchodzi na listę."""
        draft = ProductFactory(name="Szkic")
        published = PublishedProductFactory(name="Widoczny")
        CollectionFactory(name="Winter", slug="winter", products=[draft, published])

        assert _product_names(api_client, collection="winter") == ["Widoczny"]

    def test_filter_combines_with_others(self, api_client: APIClient):
        """Filtr kolekcji łączy się z pozostałymi filtrami."""
        from apps.products.models import Material

        gold = PublishedProductFactory(name="Złoty", material=Material.GOLD)
        silver = PublishedProductFactory(name="Srebrny", material=Material.SILVER)
        CollectionFactory(name="Winter", slug="winter", products=[gold, silver])

        found = _product_names(api_client, collection="winter", material=Material.GOLD)

        assert found == ["Złoty"]
