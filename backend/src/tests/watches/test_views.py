"""API obserwowanych: dodanie, lista, usunięcie (#201)."""

from __future__ import annotations

from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.watches.models import Watch
from tests.factories.products import MadeToOrderProductFactory, ProductVariantFactory
from tests.factories.watches import WatchFactory

WATCHES_URL = reverse("watch-list")


def _detail_url(watch_id: str) -> str:
    return reverse("watch-detail", args=[watch_id])


@pytest.mark.django_db
class TestWatchListApi:
    def test_requires_authentication(self, api_client: APIClient):
        response: Any = api_client.get(WATCHES_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_lists_only_own_active(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        WatchFactory(user=user)
        WatchFactory()  # cudzy wpis — poza listą

        response: Any = authenticated_client.get(WATCHES_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 1


@pytest.mark.django_db
class TestWatchCreateApi:
    def test_creates_price_drop(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        variant = ProductVariantFactory(price=129900)

        response: Any = authenticated_client.post(
            WATCHES_URL, {"variant": variant.sku, "kind": "price_drop"}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Watch.objects.filter(user=user, variant=variant).count() == 1
        assert response.json()["priceAtWatch"] == variant.effective_price.amount

    def test_rejects_restock_for_made_to_order(self, authenticated_client: APIClient):
        variant = ProductVariantFactory(product=MadeToOrderProductFactory())

        response: Any = authenticated_client.post(
            WATCHES_URL, {"variant": variant.sku, "kind": "restock"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_unknown_kind(self, authenticated_client: APIClient):
        variant = ProductVariantFactory()

        response: Any = authenticated_client.post(
            WATCHES_URL, {"variant": variant.sku, "kind": "promotion"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestWatchDestroyApi:
    def test_removes_own_watch(self, authenticated_client: APIClient, user: CustomUser):
        watch = WatchFactory(user=user)

        response: Any = authenticated_client.delete(_detail_url(str(watch.pk)))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Watch.objects.filter(pk=watch.pk).exists()

    def test_removing_missing_watch_returns_204(self, authenticated_client: APIClient):
        response: Any = authenticated_client.delete(
            _detail_url("00000000-0000-0000-0000-000000000000")
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_remove_other_customers_watch(self, authenticated_client: APIClient):
        watch = WatchFactory()

        response: Any = authenticated_client.delete(_detail_url(str(watch.pk)))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Watch.objects.filter(pk=watch.pk).exists()
