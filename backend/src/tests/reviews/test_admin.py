"""Panel opinii: akceptacja, odrzucenie i usunięcie (#199)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.reviews.models import Review, ReviewStatus
from tests.factories.reviews import ReviewFactory


@pytest.mark.django_db
class TestReviewAdminActions:
    """Akcje zbiorcze zmieniające status moderacji."""

    def test_approve_action_publishes_selected_reviews(self, admin_client):
        """Akcja akceptacji publikuje zaznaczone opinie."""
        review = ReviewFactory(status=ReviewStatus.PENDING)

        admin_client.post(
            reverse("admin:reviews_review_changelist"),
            {"action": "approve", "_selected_action": [str(review.pk)]},
        )

        review.refresh_from_db()
        assert review.status == ReviewStatus.APPROVED

    def test_reject_action_rejects_selected_reviews(self, admin_client):
        """Akcja odrzucenia odrzuca zaznaczone opinie."""
        review = ReviewFactory(status=ReviewStatus.PENDING)

        admin_client.post(
            reverse("admin:reviews_review_changelist"),
            {"action": "reject", "_selected_action": [str(review.pk)]},
        )

        review.refresh_from_db()
        assert review.status == ReviewStatus.REJECTED

    def test_delete_removes_review(self, admin_client):
        """Usunięcie w panelu kasuje opinię."""
        review = ReviewFactory()

        admin_client.post(
            reverse("admin:reviews_review_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": [str(review.pk)],
            },
        )
        admin_client.post(
            reverse("admin:reviews_review_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": [str(review.pk)],
                "post": "yes",
            },
        )

        assert not Review.objects.filter(pk=review.pk).exists()
