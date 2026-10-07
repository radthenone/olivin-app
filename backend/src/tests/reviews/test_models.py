"""Model opinii: jedna na klienta na produkt, ocena w skali 1-5 (#199)."""

from __future__ import annotations

import pytest
from django.db import IntegrityError, transaction

from apps.reviews.models import Review, ReviewStatus
from tests.factories.accounts import UserFactory
from tests.factories.products import PublishedProductFactory
from tests.factories.reviews import ReviewFactory


@pytest.mark.django_db
class TestReviewModel:
    """Ograniczenia modelu opinii."""

    def test_second_review_of_same_product_by_same_user_is_rejected(self):
        """Baza odrzuca drugą opinię tego samego klienta o tym samym produkcie."""
        product = PublishedProductFactory()
        user = UserFactory()
        ReviewFactory(product=product, user=user)

        with pytest.raises(IntegrityError), transaction.atomic():
            ReviewFactory(product=product, user=user)

    def test_rating_outside_one_to_five_is_rejected(self):
        """Ograniczenie bazy odrzuca ocenę spoza 1-5 przy zapisie programowym."""
        with pytest.raises(IntegrityError), transaction.atomic():
            ReviewFactory(rating=6)

    def test_restart_moderation_sets_pending_status(self):
        """`restart_moderation()` cofa opinię do statusu oczekującego."""
        review = ReviewFactory(status=ReviewStatus.APPROVED)
        review.restart_moderation()
        assert review.status == ReviewStatus.PENDING

    def test_approved_queryset_returns_only_approved(self):
        """`approved()` pomija opinie oczekujące i odrzucone."""
        approved = ReviewFactory(status=ReviewStatus.APPROVED)
        ReviewFactory(status=ReviewStatus.PENDING)
        ReviewFactory(status=ReviewStatus.REJECTED)

        assert list(Review.objects.approved()) == [approved]
