"""API opinii: własne opinie klienta, „do oceny” i publiczna lista (#199).

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
from apps.orders.models import OrderStatus
from apps.reviews.models import Review, ReviewStatus
from tests.factories.orders import OrderFactory, OrderItemFactory
from tests.factories.products import ProductVariantFactory, PublishedProductFactory
from tests.factories.reviews import ReviewFactory

REVIEWS_URL = reverse("review-list")
TO_REVIEW_URL = reverse("review-to-review")


def _review_detail_url(pk) -> str:
    return reverse("review-detail", args=[pk])


def _product_reviews_url(slug: str | None) -> str:
    return reverse("product-reviews", args=[slug])


def _delivered_purchase(user, product):
    order = OrderFactory(user=user, status=OrderStatus.DELIVERED)
    variant = ProductVariantFactory(product=product)
    OrderItemFactory(order=order, variant=variant)
    return order


@pytest.mark.django_db
class TestReviewCreateApi:
    """Złożenie opinii przez klienta."""

    def test_requires_authentication(self, api_client: APIClient):
        response: Any = api_client.post(
            REVIEWS_URL, {"product": "x", "rating": 5}, format="json"
        )
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_create_review_for_delivered_product(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        product = PublishedProductFactory()
        _delivered_purchase(user, product)

        response: Any = authenticated_client.post(
            REVIEWS_URL,
            {"product": product.slug, "rating": 4, "comment": "Bardzo dobry"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == ReviewStatus.PENDING
        assert Review.objects.filter(user=user, product=product).exists()

    def test_rejects_review_without_delivered_order(
        self, authenticated_client: APIClient
    ):
        product = PublishedProductFactory()

        response: Any = authenticated_client.post(
            REVIEWS_URL, {"product": product.slug, "rating": 5}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_second_review_of_same_product(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        product = PublishedProductFactory()
        _delivered_purchase(user, product)
        ReviewFactory(user=user, product=product)

        response: Any = authenticated_client.post(
            REVIEWS_URL, {"product": product.slug, "rating": 5}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestReviewUpdateApi:
    """Edycja własnej opinii przywraca moderację."""

    def test_update_own_review_restarts_moderation(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        review = ReviewFactory(user=user, status=ReviewStatus.APPROVED, rating=5)

        response: Any = authenticated_client.patch(
            _review_detail_url(review.pk),
            {"rating": 1, "comment": "Zmieniam zdanie"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        review.refresh_from_db()
        assert review.status == ReviewStatus.PENDING
        assert review.rating == 1

    def test_cannot_update_other_customers_review(
        self, authenticated_client: APIClient
    ):
        review = ReviewFactory()

        response: Any = authenticated_client.patch(
            _review_detail_url(review.pk), {"rating": 1}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestReviewListApi:
    """Lista własnych opinii klienta, niezależnie od statusu."""

    def test_list_returns_only_own_reviews_any_status(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        mine = ReviewFactory(user=user, status=ReviewStatus.PENDING)
        ReviewFactory()

        response: Any = authenticated_client.get(REVIEWS_URL)

        ids = [row["id"] for row in response.json()["results"]]
        assert ids == [str(mine.pk)]


@pytest.mark.django_db
class TestToReviewApi:
    """Produkty z dostarczonych zamówień, których klient nie ocenił."""

    def test_lists_delivered_products_without_review(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        product = PublishedProductFactory()
        _delivered_purchase(user, product)

        response: Any = authenticated_client.get(TO_REVIEW_URL)

        slugs = [row["slug"] for row in response.json()]
        assert slugs == [product.slug]

    def test_query_count_does_not_grow_with_product_count(
        self,
        authenticated_client: APIClient,
        user: CustomUser,
        django_assert_num_queries,
    ):
        """Tłumaczenia nazwy są prefetchowane — bez tego każdy produkt dobijałby bazę."""
        one_product = PublishedProductFactory()
        _delivered_purchase(user, one_product)
        with django_assert_num_queries(2):
            authenticated_client.get(TO_REVIEW_URL)

        for _ in range(3):
            _delivered_purchase(user, PublishedProductFactory())
        with django_assert_num_queries(2):
            authenticated_client.get(TO_REVIEW_URL)

    def test_excludes_already_reviewed_product(
        self, authenticated_client: APIClient, user: CustomUser
    ):
        product = PublishedProductFactory()
        _delivered_purchase(user, product)
        ReviewFactory(user=user, product=product)

        response: Any = authenticated_client.get(TO_REVIEW_URL)

        assert response.json() == []


@pytest.mark.django_db
class TestProductReviewsPublicApi:
    """Publiczna, paginowana lista opinii opublikowanych produktu."""

    def test_returns_only_approved_reviews_signed_with_username(
        self, api_client: APIClient
    ):
        product = PublishedProductFactory()
        approved = ReviewFactory(
            product=product, status=ReviewStatus.APPROVED, comment="Super"
        )
        ReviewFactory(product=product, status=ReviewStatus.PENDING)
        ReviewFactory(product=product, status=ReviewStatus.REJECTED)

        response: Any = api_client.get(_product_reviews_url(product.slug))

        assert response.status_code == status.HTTP_200_OK
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["username"] == approved.user.username
        assert results[0]["comment"] == "Super"

    def test_does_not_require_authentication(self, api_client: APIClient):
        product = PublishedProductFactory()
        response: Any = api_client.get(_product_reviews_url(product.slug))
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProductAverageRating:
    """Średnia ocen opublikowanych w API produktu (lista i karta)."""

    def test_average_rating_counts_only_approved_reviews(self, api_client: APIClient):
        product = PublishedProductFactory()
        ProductVariantFactory(product=product)
        ReviewFactory(product=product, status=ReviewStatus.APPROVED, rating=4)
        ReviewFactory(product=product, status=ReviewStatus.APPROVED, rating=2)
        ReviewFactory(product=product, status=ReviewStatus.PENDING, rating=1)

        list_response: Any = api_client.get(reverse("product-list"))
        detail_response: Any = api_client.get(
            reverse("product-detail", args=[product.slug])
        )

        list_data = list_response.json()
        detail_data = detail_response.json()
        [row] = [item for item in list_data["results"] if item["slug"] == product.slug]
        assert row["averageRating"] == 3.0
        assert detail_data["averageRating"] == 3.0
        assert "reviewCount" not in row

    def test_average_rating_is_null_without_approved_reviews(
        self, api_client: APIClient
    ):
        product = PublishedProductFactory()
        ProductVariantFactory(product=product)

        response: Any = api_client.get(reverse("product-detail", args=[product.slug]))

        assert response.json()["averageRating"] is None
