"""API ulubionych: lista, dodanie/usunięcie idempotentne, scalenie listy gościa (#200).

Asercje idą po `response.json()`, nie po `response.data` (patrz
`tests/products/test_views.py`): renderer zamienia klucze na camelCase
dopiero przy renderowaniu.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.favorites.models import Favorite
from apps.products.models import ProductStatus
from tests.factories.favorites import FavoriteFactory
from tests.factories.products import ProductFactory, PublishedProductFactory

FAVORITES_URL = reverse("favorite-list")
FAVORITES_MERGE_URL = reverse("favorite-merge")


def _favorite_detail_url(product_slug: str | None) -> str:
    return reverse("favorite-detail", args=[product_slug])


@pytest.mark.django_db
class TestFavoriteListApi:
    """Lista ulubionych klienta."""

    def test_requires_authentication(self, api_client: APIClient):
        response: Any = api_client.get(FAVORITES_URL)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_lists_only_published_products(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        published = PublishedProductFactory()
        FavoriteFactory(user=user, product=published)
        FavoriteFactory(user=user, product=ProductFactory())  # szkic — poza listą

        response: Any = authenticated_client.get(FAVORITES_URL)

        assert response.status_code == status.HTTP_200_OK
        payload = response.json()["results"]
        assert [item["product"]["slug"] for item in payload] == [published.slug]


@pytest.mark.django_db
class TestFavoriteCreateApi:
    """Dodanie do ulubionych jest idempotentne."""

    def test_creates_favorite(self, authenticated_client: APIClient, user: CustomUser):
        product = PublishedProductFactory()

        response: Any = authenticated_client.post(
            FAVORITES_URL, {"product": product.slug}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Favorite.objects.filter(user=user, product=product).exists()

    def test_repeating_create_does_not_duplicate(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        product = PublishedProductFactory()
        authenticated_client.post(
            FAVORITES_URL, {"product": product.slug}, format="json"
        )

        response: Any = authenticated_client.post(
            FAVORITES_URL, {"product": product.slug}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Favorite.objects.filter(user=user, product=product).count() == 1

    def test_rejects_unpublished_product(self, authenticated_client: APIClient):
        draft = ProductFactory()

        response: Any = authenticated_client.post(
            FAVORITES_URL, {"product": draft.slug}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestFavoriteDestroyApi:
    """Usunięcie z ulubionych jest idempotentne."""

    def test_removes_own_favorite(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        favorite = FavoriteFactory(user=user)

        response: Any = authenticated_client.delete(
            _favorite_detail_url(favorite.product.slug)
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Favorite.objects.filter(pk=favorite.pk).exists()

    def test_removing_missing_favorite_returns_204(
        self, authenticated_client: APIClient
    ):
        product = PublishedProductFactory()

        response: Any = authenticated_client.delete(_favorite_detail_url(product.slug))

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_remove_other_customers_favorite(
        self, authenticated_client: APIClient
    ):
        favorite = FavoriteFactory()

        response: Any = authenticated_client.delete(
            _favorite_detail_url(favorite.product.slug)
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Favorite.objects.filter(pk=favorite.pk).exists()  # cudzy wpis przeżył


@pytest.mark.django_db
class TestFavoriteMergeApi:
    """Scalenie listy gościa z listą konta po zalogowaniu."""

    def test_merges_guest_products_into_account_list(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        existing = PublishedProductFactory()
        FavoriteFactory(user=user, product=existing)
        guest_product = PublishedProductFactory()

        response: Any = authenticated_client.post(
            FAVORITES_MERGE_URL,
            {"products": [guest_product.slug, existing.slug]},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        slugs = {item["product"]["slug"] for item in response.json()}
        assert slugs == {existing.slug, guest_product.slug}

    def test_skips_nonexistent_and_unpublished_slugs(
        self, authenticated_client: APIClient
    ):
        # Produkt cofnięty do szkicu — slug zamrożony z czasu publikacji,
        # ale sam już nie jest widoczny w sklepie.
        unpublished = PublishedProductFactory()
        unpublished.status = ProductStatus.DRAFT
        unpublished.save()

        response: Any = authenticated_client.post(
            FAVORITES_MERGE_URL,
            {"products": [unpublished.slug, "brak-takiego"]},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
