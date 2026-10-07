"""Uprawnienie do opinii: wyłącznie z dostarczonego zamówienia (#199)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint

from apps.orders.models import OrderStatus
from apps.reviews.models import Review, ReviewStatus
from apps.reviews.services import create_review, products_to_review, update_review
from tests.factories.accounts import UserFactory
from tests.factories.orders import OrderFactory, OrderItemFactory
from tests.factories.products import PublishedProductFactory, ProductVariantFactory
from tests.factories.reviews import ReviewFactory


def _delivered_purchase(user, product):
    """Dostarczone zamówienie klienta obejmujące dany produkt."""
    order = OrderFactory(user=user, status=OrderStatus.DELIVERED)
    variant = ProductVariantFactory(product=product)
    OrderItemFactory(order=order, variant=variant)
    return order


@pytest.mark.django_db
class TestCreateReview:
    """Złożenie opinii wymaga dostarczonego zamówienia z produktem."""

    def test_creates_pending_review_for_delivered_purchase(self):
        """Klient z dostarczonym zamówieniem dostaje opinię w moderacji."""
        user = UserFactory()
        product = PublishedProductFactory()
        _delivered_purchase(user, product)

        review = create_review(user=user, product=product, rating=4, comment="Super")

        assert review.status == ReviewStatus.PENDING
        assert review.rating == 4

    def test_rejects_review_without_delivered_order(self):
        """Bez dostarczonego zamówienia z produktem opinia nie powstaje."""
        user = UserFactory()
        product = PublishedProductFactory()

        with pytest.raises(ValidationError):
            create_review(user=user, product=product, rating=5, comment="")

    def test_rejects_second_review_of_same_product(self):
        """Klient ocenia produkt raz — kolejna próba to błąd walidacji."""
        user = UserFactory()
        product = PublishedProductFactory()
        _delivered_purchase(user, product)
        create_review(user=user, product=product, rating=5, comment="")

        with pytest.raises(ValidationError):
            create_review(user=user, product=product, rating=3, comment="")

    def test_race_between_duplicate_check_and_save_becomes_validation_error(self):
        """Wyścig dwóch równoległych żądań: obie kontrole (`exists()` na wejściu
        i `validate_constraints()` w `full_clean()`) przechodzą tuż przed tym, jak
        druga opinia trafia do bazy — `IntegrityError` ma zamienić się w 400,
        nie wywrócić widoku."""
        user = UserFactory()
        product = PublishedProductFactory()
        _delivered_purchase(user, product)
        ReviewFactory(user=user, product=product)  # opinia "drugiego żądania"

        class _AlwaysFalseExists:
            """Atrapa querysetu: udaje, że duplikatu jeszcze nie ma."""

            def exists(self) -> bool:
                return False

        with (
            patch.object(Review.objects, "filter", return_value=_AlwaysFalseExists()),
            patch.object(UniqueConstraint, "validate", return_value=None),
        ):
            with pytest.raises(ValidationError, match="już oceniony"):
                create_review(user=user, product=product, rating=3, comment="")


@pytest.mark.django_db
class TestUpdateReview:
    """Edycja własnej opinii wraca do moderacji."""

    def test_update_changes_content_and_restarts_moderation(self):
        """Edycja zmienia treść i cofa opinię do moderacji."""
        review = ReviewFactory(status=ReviewStatus.APPROVED, rating=5, comment="Ok")

        updated = update_review(review, rating=2, comment="Jednak nie")

        assert updated.rating == 2
        assert updated.comment == "Jednak nie"
        assert updated.status == ReviewStatus.PENDING


@pytest.mark.django_db
class TestProductsToReview:
    """Lista dostarczonych produktów bez wystawionej opinii."""

    def test_lists_delivered_product_without_review(self):
        """Lista zawiera dostarczony produkt bez opinii."""
        user = UserFactory()
        product = PublishedProductFactory()
        _delivered_purchase(user, product)

        assert list(products_to_review(user)) == [product]

    def test_excludes_already_reviewed_product(self):
        """Lista pomija produkt już oceniony."""
        user = UserFactory()
        product = PublishedProductFactory()
        _delivered_purchase(user, product)
        Review.objects.create(user=user, product=product, rating=5)

        assert list(products_to_review(user)) == []

    def test_excludes_product_without_delivered_order(self):
        """Lista pomija produkt bez dostarczonego zamówienia."""
        user = UserFactory()
        PublishedProductFactory()

        assert list(products_to_review(user)) == []
